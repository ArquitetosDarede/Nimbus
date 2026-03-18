"""
Notion Cache Layer

Fetches and indexes ALL accessible Notion content locally using SQLite with FTS5.
Acts as a local read-only mirror of the Notion workspace.

behaviour:
  - On startup: checks if cache is stale (TTL exceeded).  If stale, kicks off a
    background thread that paginates through every Notion page/database and stores
    the full text in SQLite.
  - Agents use the local cache instead of making live API calls during generation.
  - The background thread respects Notion rate limits (≤ 3 req/s).

Storage:
  - SQLite file at .nimbus_cache/notion.db (relative to CWD / workspace root).
  - Configurable via env var NIMBUS_NOTION_CACHE_PATH.

TTL:
  - Default 6 hours.  Configurable via NIMBUS_NOTION_CACHE_TTL_HOURS.
"""

import json
import logging
import os
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional

try:
    from notion_client import Client as _NotionClient  # type: ignore[import]

    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_DEFAULT_CACHE_DIR = os.path.join(
    os.path.dirname(  # src/tools/ → src/ → project root
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ),
    ".nimbus_cache",
)
_DEFAULT_CACHE_PATH = os.path.join(_DEFAULT_CACHE_DIR, "notion.db")

_DEFAULT_TTL_SECONDS = int(os.getenv("NIMBUS_NOTION_CACHE_TTL_HOURS", "6")) * 3600

# Stay comfortably under the 3 req/s Notion average limit.
_REQUEST_DELAY = 0.38  # seconds between API calls


# ---------------------------------------------------------------------------
# NotionCacheLayer
# ---------------------------------------------------------------------------


class NotionCacheLayer:
    """
    Local SQLite cache that mirrors the entire Notion workspace.

    Public API
    ----------
    start_sync_if_needed()      Kick off background sync when cache is stale.
    force_full_sync()           Block until a full sync finishes (use sparingly).
    search(query, limit)        FTS5 full-text search.  Returns list of dicts.
    get_page(page_id)           Retrieve one cached page by ID.
    get_all_formatted(max_chars)Return all content as a prompt-ready string.
    page_count()                Number of cached pages.
    is_ready()                  True once at least one full sync has completed.
    last_synced_at()            Unix timestamp of the last completed full sync.
    """

    def __init__(self, cache_path: Optional[str] = None) -> None:
        self.cache_path: str = cache_path or os.getenv(
            "NIMBUS_NOTION_CACHE_PATH", _DEFAULT_CACHE_PATH
        )
        self._lock = threading.Lock()
        self._db: Optional[sqlite3.Connection] = None
        self._client: Any = None
        self._ready = False
        self._error: Optional[str] = None
        self._sync_thread: Optional[threading.Thread] = None

        if not _SDK_AVAILABLE:
            self._error = (
                "notion-client SDK not installed.  "
                "Run: pip install notion-client"
            )
            logger.warning("[NotionCache] %s", self._error)
            return

        token = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
        if not token:
            self._error = "NOTION_API_KEY not set.  Notion cache is disabled."
            logger.warning("[NotionCache] %s", self._error)
            return

        self._client = _NotionClient(auth=token)
        self._init_db()

        # If there is already a valid cache on disk, mark as ready immediately.
        if not self.is_stale():
            self._ready = True
            logger.info(
                "[NotionCache] Found fresh cache (%d pages).  Ready.",
                self.page_count(),
            )

    # ------------------------------------------------------------------
    # DB initialisation
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        conn = self._connect()
        conn.executescript(
            """
            PRAGMA journal_mode=WAL;

            CREATE TABLE IF NOT EXISTS notion_pages (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL DEFAULT '',
                url         TEXT NOT NULL DEFAULT '',
                object_type TEXT NOT NULL DEFAULT 'page',
                parent_id   TEXT NOT NULL DEFAULT '',
                parent_type TEXT NOT NULL DEFAULT 'workspace',
                last_edited TEXT NOT NULL DEFAULT '',
                full_text   TEXT NOT NULL DEFAULT '',
                props_json  TEXT NOT NULL DEFAULT '{}',
                indexed_at  REAL NOT NULL DEFAULT 0
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS notion_fts USING fts5(
                page_id UNINDEXED,
                title,
                full_text,
                tokenize = "unicode61"
            );

            CREATE TABLE IF NOT EXISTS sync_log (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_type    TEXT NOT NULL,
                started_at   REAL NOT NULL,
                completed_at REAL,
                pages_synced INTEGER DEFAULT 0,
                errors_count INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS sync_items (
                sync_id     INTEGER NOT NULL,
                item_index  INTEGER NOT NULL,
                item_id     TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                last_edited TEXT NOT NULL DEFAULT '',
                status      TEXT NOT NULL DEFAULT 'pending',
                updated_at  REAL NOT NULL DEFAULT 0,
                PRIMARY KEY (sync_id, item_id)
            );

            CREATE INDEX IF NOT EXISTS idx_sync_items_status
            ON sync_items (sync_id, status, item_index);

            CREATE TABLE IF NOT EXISTS sync_state (
                sync_id      INTEGER PRIMARY KEY,
                phase        TEXT NOT NULL DEFAULT 'enumerating',
                next_cursor  TEXT NOT NULL DEFAULT '',
                page_number  INTEGER NOT NULL DEFAULT 0,
                updated_at   REAL NOT NULL DEFAULT 0
            );
            """
        )
        conn.commit()
        logger.info("[NotionCache] DB initialised at: %s", self.cache_path)

    def _connect(self) -> sqlite3.Connection:
        """Return the cached SQLite connection (opens once per instance)."""
        if self._db is None:
            self._db = sqlite3.connect(self.cache_path, check_same_thread=False)
            self._db.row_factory = sqlite3.Row
        return self._db

    # ------------------------------------------------------------------
    # Staleness / TTL
    # ------------------------------------------------------------------

    def is_stale(self) -> bool:
        """Return True when the cache needs a full refresh."""
        if self._db is None:
            return True
        conn = self._connect()
        row = conn.execute(
            "SELECT completed_at FROM sync_log "
            "WHERE sync_type='full' AND completed_at IS NOT NULL "
            "ORDER BY completed_at DESC LIMIT 1"
        ).fetchone()
        if not row:
            return True
        return (time.time() - float(row["completed_at"])) > _DEFAULT_TTL_SECONDS

    def last_synced_at(self) -> Optional[float]:
        if self._db is None:
            return None
        conn = self._connect()
        row = conn.execute(
            "SELECT completed_at FROM sync_log "
            "WHERE sync_type='full' AND completed_at IS NOT NULL "
            "ORDER BY completed_at DESC LIMIT 1"
        ).fetchone()
        return float(row["completed_at"]) if row else None

    # ------------------------------------------------------------------
    # Sync entry points
    # ------------------------------------------------------------------

    def start_sync_if_needed(self) -> None:
        """
        If the cache is stale (or empty) start a daemon background sync thread.
        Returns immediately — the sync runs in the background.
        """
        if self._client is None:
            return
        if self.is_stale():
            logger.info("[NotionCache] Cache is stale — starting background full sync.")
            t = threading.Thread(target=self._run_full_sync, daemon=True, name="notion-sync")
            self._sync_thread = t
            t.start()
        else:
            logger.info(
                "[NotionCache] Cache is fresh (%d pages).  No sync needed.",
                self.page_count(),
            )

    def force_full_sync(self) -> Dict[str, Any]:
        """Blocking full sync.  Returns a summary dict."""
        if self._client is None:
            return {"error": self._error or "No Notion client available"}
        return self._run_full_sync()

    # ------------------------------------------------------------------
    # Core sync logic
    # ------------------------------------------------------------------

    def _run_full_sync(self) -> Dict[str, Any]:
        """Enumerate + ingest every accessible Notion item.  Thread-safe."""
        if self._client is None:
            return {"error": self._error}

        started = time.time()
        sync_id, items, resumed = self._prepare_sync_run(started)
        total = len(items)
        pages_synced = 0
        pages_skipped = 0
        errors = 0

        try:
            if resumed:
                logger.info("[NotionCache] Resuming sync %d with %d pending items.", sync_id, total)
            else:
                logger.info("[NotionCache] Found %d items to sync.", total)

            for idx, item in enumerate(items, 1):
                item_id = item["id"].replace("-", "")
                try:
                    if self._should_refresh_item(item):
                        self._ingest_item(item)
                        pages_synced += 1
                        self._mark_sync_item_status(sync_id, item_id, "done")
                    else:
                        self._mark_item_revalidated(item_id)
                        self._mark_sync_item_status(sync_id, item_id, "skipped")
                        pages_skipped += 1
                except Exception as exc:
                    self._mark_sync_item_status(sync_id, item_id, "pending")
                    logger.warning(
                        "[NotionCache] Failed to ingest %s: %s",
                        item.get("id", "?"),
                        exc,
                    )
                    errors += 1

                if idx % 20 == 0 or idx == total:
                    elapsed = time.time() - started
                    rate = idx / elapsed if elapsed > 0 else 0.0
                    remaining_items = max(total - idx, 0)
                    eta_seconds = int(remaining_items / rate) if rate > 0 else 0
                    percentage = (idx / total * 100.0) if total else 100.0
                    logger.info(
                        "[NotionCache] Processed %d / %d (%.1f%%) | synced=%d | skipped=%d | elapsed=%s | eta=%s | current='%s'",
                        idx,
                        total,
                        percentage,
                        pages_synced,
                        pages_skipped,
                        self._format_duration(int(elapsed)),
                        self._format_duration(eta_seconds),
                        self._extract_title(item)[:60],
                    )

                time.sleep(_REQUEST_DELAY)

        except Exception as exc:
            logger.error("[NotionCache] Full sync aborted: %s", exc)
            errors += 1

        completed = time.time()
        conn = self._connect()
        total_done = self._count_sync_items(sync_id, "done")
        total_skipped = self._count_sync_items(sync_id, "skipped")
        if errors == 0:
            self._delete_items_not_in_sync(sync_id)
        conn.execute(
            "UPDATE sync_log SET completed_at=?, pages_synced=?, errors_count=? WHERE id=?",
            (completed, total_done, errors, sync_id),
        )
        conn.commit()
        if errors == 0:
            self._set_sync_state(sync_id, "complete", "", 0)
            self._cleanup_old_sync_rows(sync_id)
        self._ready = True

        summary = {
            "pages_synced": total_done,
            "pages_skipped": total_skipped,
            "errors": errors,
            "resumed": resumed,
            "duration_seconds": round(completed - started, 1),
        }
        logger.info("[NotionCache] Full sync complete: %s", summary)
        return summary

    def _enumerate_all_items(
        self,
        sync_id: Optional[int] = None,
        start_cursor: Optional[str] = None,
        start_page_number: int = 0,
        clear_existing: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Use the Notion search endpoint with pagination and optionally persist
        the worklist incrementally for resume support.
        """
        items: List[Dict[str, Any]] = []
        cursor = start_cursor
        page_number = start_page_number

        if sync_id is not None and clear_existing:
            conn = self._connect()
            conn.execute("DELETE FROM sync_items WHERE sync_id = ?", (sync_id,))
            conn.commit()

        next_item_index = self._next_sync_item_index(sync_id) if sync_id is not None else 1

        while True:
            params: Dict[str, Any] = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor

            result = self._client.search(**params)
            time.sleep(_REQUEST_DELAY)

            batch = result.get("results", [])
            items.extend(batch)
            page_number += 1
            logger.info(
                "[NotionCache] Enumeration page %d: +%d items (total=%d)",
                page_number,
                len(batch),
                len(items),
            )

            next_cursor = result.get("next_cursor") or ""
            if sync_id is not None and batch:
                next_item_index = self._append_sync_items(sync_id, batch, next_item_index)
                self._set_sync_state(sync_id, "enumerating", next_cursor, page_number)

            if not result.get("has_more") or not next_cursor:
                break
            cursor = next_cursor

        if sync_id is not None:
            self._set_sync_state(sync_id, "ingesting", "", page_number)

        return items

    def _prepare_sync_run(self, started_at: float) -> tuple[int, List[Dict[str, Any]], bool]:
        """Resume an incomplete sync if present, otherwise start a new full run."""
        conn = self._connect()
        row = conn.execute(
            "SELECT id FROM sync_log WHERE sync_type='full' AND completed_at IS NULL ORDER BY started_at DESC LIMIT 1"
        ).fetchone()

        if row:
            sync_id = int(row["id"])
            state = self._get_sync_state(sync_id)
            if state and state.get("phase") == "enumerating":
                logger.info(
                    "[NotionCache] Resuming enumeration for sync %d from page %d.",
                    sync_id,
                    int(state.get("page_number", 0)),
                )
                self._enumerate_all_items(
                    sync_id=sync_id,
                    start_cursor=(state.get("next_cursor") or None),
                    start_page_number=int(state.get("page_number", 0)),
                    clear_existing=False,
                )
            items = self._load_sync_items(sync_id, statuses=("pending",))
            if items:
                return sync_id, items, True
            conn.execute("DELETE FROM sync_items WHERE sync_id = ?", (sync_id,))
            conn.execute("DELETE FROM sync_state WHERE sync_id = ?", (sync_id,))
            conn.commit()

        sync_id = conn.execute(
            "INSERT INTO sync_log (sync_type, started_at) VALUES ('full', ?)",
            (started_at,),
        ).lastrowid
        conn.commit()

        self._set_sync_state(int(sync_id), "enumerating", "", 0)
        self._enumerate_all_items(sync_id=int(sync_id), clear_existing=True)
        items = self._load_sync_items(int(sync_id), statuses=("pending",))
        return int(sync_id), items, False

    def _append_sync_items(self, sync_id: int, items: List[Dict[str, Any]], start_index: int) -> int:
        """Append enumerated items to the persisted worklist."""
        conn = self._connect()
        rows = [
            (
                sync_id,
                idx,
                item["id"].replace("-", ""),
                json.dumps(item, ensure_ascii=False),
                str(item.get("last_edited_time", "")),
                "pending",
                time.time(),
            )
            for idx, item in enumerate(items, start_index)
            if isinstance(item, dict) and item.get("id")
        ]
        if rows:
            conn.executemany(
                """
                INSERT OR REPLACE INTO sync_items
                    (sync_id, item_index, item_id, payload_json, last_edited, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            conn.commit()
        return start_index + len(rows)

    def _next_sync_item_index(self, sync_id: Optional[int]) -> int:
        """Return the next stable item index for incremental enumeration persistence."""
        if sync_id is None:
            return 1
        conn = self._connect()
        row = conn.execute(
            "SELECT COALESCE(MAX(item_index), 0) AS max_idx FROM sync_items WHERE sync_id = ?",
            (sync_id,),
        ).fetchone()
        return int(row["max_idx"]) + 1 if row else 1

    def _load_sync_items(self, sync_id: int, statuses: tuple[str, ...] = ("pending",)) -> List[Dict[str, Any]]:
        """Load persisted sync work items from SQLite in stable processing order."""
        conn = self._connect()
        placeholders = ", ".join("?" for _ in statuses)
        query = (
            "SELECT payload_json FROM sync_items WHERE sync_id = ? "
            f"AND status IN ({placeholders}) ORDER BY item_index"
        )
        rows = conn.execute(query, (sync_id, *statuses)).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def _mark_sync_item_status(self, sync_id: int, item_id: str, status: str) -> None:
        """Persist per-item processing state for resume support."""
        conn = self._connect()
        conn.execute(
            "UPDATE sync_items SET status = ?, updated_at = ? WHERE sync_id = ? AND item_id = ?",
            (status, time.time(), sync_id, item_id),
        )
        conn.commit()

    def _should_refresh_item(self, item: Dict[str, Any]) -> bool:
        """Return True when the local cache is missing or stale for this item."""
        item_id = item["id"].replace("-", "")
        notion_last_edited = str(item.get("last_edited_time", ""))
        conn = self._connect()
        row = conn.execute(
            "SELECT last_edited FROM notion_pages WHERE id = ?",
            (item_id,),
        ).fetchone()
        if not row:
            return True
        return str(row["last_edited"] or "") != notion_last_edited

    def _mark_item_revalidated(self, item_id: str) -> None:
        """Update indexed_at when an unchanged item is revalidated during sync."""
        conn = self._connect()
        conn.execute(
            "UPDATE notion_pages SET indexed_at = ? WHERE id = ?",
            (time.time(), item_id),
        )
        conn.commit()

    def _delete_items_not_in_sync(self, sync_id: int) -> None:
        """Remove local cache rows for pages no longer returned by Notion search."""
        conn = self._connect()
        conn.execute(
            "DELETE FROM notion_pages WHERE id NOT IN (SELECT item_id FROM sync_items WHERE sync_id = ?)",
            (sync_id,),
        )
        conn.execute(
            "DELETE FROM notion_fts WHERE page_id NOT IN (SELECT id FROM notion_pages)"
        )
        conn.commit()

    def _cleanup_old_sync_rows(self, keep_sync_id: int) -> None:
        """Keep sync metadata bounded after a successful run."""
        conn = self._connect()
        conn.execute("DELETE FROM sync_items WHERE sync_id != ?", (keep_sync_id,))
        conn.execute("DELETE FROM sync_state WHERE sync_id != ?", (keep_sync_id,))
        conn.execute(
            "DELETE FROM sync_log WHERE id != ? AND completed_at IS NOT NULL",
            (keep_sync_id,),
        )
        conn.commit()

    def _count_sync_items(self, sync_id: int, status: str) -> int:
        """Count persisted work items by status for the current sync."""
        conn = self._connect()
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM sync_items WHERE sync_id = ? AND status = ?",
            (sync_id, status),
        ).fetchone()
        return int(row["n"]) if row else 0

    def _get_sync_state(self, sync_id: int) -> Optional[Dict[str, Any]]:
        """Return persisted state for the current sync execution."""
        conn = self._connect()
        row = conn.execute(
            "SELECT phase, next_cursor, page_number FROM sync_state WHERE sync_id = ?",
            (sync_id,),
        ).fetchone()
        return dict(row) if row else None

    def _set_sync_state(self, sync_id: int, phase: str, next_cursor: str, page_number: int) -> None:
        """Persist the current enumeration/ingestion checkpoint."""
        conn = self._connect()
        conn.execute(
            """
            INSERT INTO sync_state (sync_id, phase, next_cursor, page_number, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(sync_id) DO UPDATE SET
                phase = excluded.phase,
                next_cursor = excluded.next_cursor,
                page_number = excluded.page_number,
                updated_at = excluded.updated_at
            """,
            (sync_id, phase, next_cursor, page_number, time.time()),
        )
        conn.commit()

    def _ingest_item(self, item: Dict[str, Any]) -> None:
        """Fetch full content for one Notion page/database and store it."""
        obj_type = item.get("object", "page")
        item_id = item["id"].replace("-", "")
        title = self._extract_title(item)
        url = item.get("url", "")
        last_edited = item.get("last_edited_time", "")

        parent = item.get("parent", {})
        parent_type = parent.get("type", "workspace")
        parent_id = (
            parent.get(f"{parent_type}_id")
            or parent.get("database_id")
            or parent.get("page_id")
            or ""
        )

        if obj_type == "page":
            full_text = self._fetch_page_text(item_id)
            props_json = json.dumps(
                self._flatten_properties(item.get("properties", {}))
            )
        elif obj_type == "database":
            full_text = self._fetch_database_text(item_id, title)
            props_json = json.dumps(
                {"schema": list(item.get("properties", {}).keys())}
            )
        else:
            full_text = title
            props_json = "{}"

        with self._lock:
            conn = self._connect()
            # Upsert into main table.
            conn.execute(
                """
                INSERT INTO notion_pages
                    (id, title, url, object_type, parent_id, parent_type,
                     last_edited, full_text, props_json, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    url=excluded.url,
                    last_edited=excluded.last_edited,
                    full_text=excluded.full_text,
                    props_json=excluded.props_json,
                    indexed_at=excluded.indexed_at
                """,
                (
                    item_id, title, url, obj_type,
                    parent_id, parent_type, last_edited,
                    full_text, props_json, time.time(),
                ),
            )
            # Keep FTS in sync: delete stale entry then re-insert.
            conn.execute("DELETE FROM notion_fts WHERE page_id = ?", (item_id,))
            conn.execute(
                "INSERT INTO notion_fts (page_id, title, full_text) VALUES (?, ?, ?)",
                (item_id, title, full_text),
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Content fetchers
    # ------------------------------------------------------------------

    def _fetch_page_text(
        self, page_id: str, depth: int = 0, max_depth: int = 3
    ) -> str:
        """Recursively fetch and format all block content for a page."""
        if depth > max_depth:
            return ""

        parts: List[str] = []
        cursor: Optional[str] = None

        while True:
            params: Dict[str, Any] = {"block_id": page_id, "page_size": 100}
            if cursor:
                params["start_cursor"] = cursor

            result = self._client.blocks.children.list(**params)
            time.sleep(_REQUEST_DELAY)

            for block in result.get("results", []):
                line = self._format_block(block)
                if line:
                    parts.append(line)

                # Recurse into nested blocks.
                if block.get("has_children") and depth < max_depth:
                    child_text = self._fetch_page_text(
                        block["id"].replace("-", ""), depth + 1, max_depth
                    )
                    if child_text:
                        indent = "  " * (depth + 1)
                        parts.append(
                            "\n".join(
                                f"{indent}{l}" for l in child_text.splitlines()
                            )
                        )

            if not result.get("has_more") or not result.get("next_cursor"):
                break
            cursor = result["next_cursor"]
            time.sleep(_REQUEST_DELAY)

        return "\n".join(parts)

    def _fetch_database_text(self, db_id: str, db_title: str) -> str:
        """Fetch all rows from a database (properties + row page content)."""
        parts: List[str] = [f"## Database: {db_title}"]
        cursor: Optional[str] = None

        while True:
            params: Dict[str, Any] = {"database_id": db_id, "page_size": 100}
            if cursor:
                params["start_cursor"] = cursor

            result = self._client.databases.query(**params)
            time.sleep(_REQUEST_DELAY)

            for row in result.get("results", []):
                row_title = self._extract_title(row)
                row_props = self._flatten_properties(row.get("properties", {}))
                prop_text = "; ".join(
                    f"{k}: {v}" for k, v in row_props.items() if v
                )
                parts.append(f"### {row_title}")
                if prop_text:
                    parts.append(prop_text)
                # Fetch the page content of each row.
                try:
                    row_id = row["id"].replace("-", "")
                    row_content = self._fetch_page_text(row_id)
                    if row_content:
                        parts.append(row_content)
                except Exception:
                    pass

            if not result.get("has_more") or not result.get("next_cursor"):
                break
            cursor = result["next_cursor"]
            time.sleep(_REQUEST_DELAY)

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Public query API
    # ------------------------------------------------------------------

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        FTS5 full-text search across all cached pages.

        Returns a list of dicts with keys: id, title, url, object_type,
        last_edited, snippet.
        """
        if not self._ready or self._db is None:
            return []

        conn = self._connect()
        # Escape FTS5 special chars to avoid query syntax errors.
        safe_q = query.replace('"', '""')
        try:
            rows = conn.execute(
                """
                SELECT p.id, p.title, p.url, p.object_type, p.last_edited,
                       snippet(notion_fts, 2, '[', ']', '...', 32) AS snippet
                FROM   notion_fts f
                JOIN   notion_pages p ON p.id = f.page_id
                WHERE  notion_fts MATCH ?
                ORDER  BY rank
                LIMIT  ?
                """,
                (safe_q, limit),
            ).fetchall()
        except sqlite3.OperationalError as exc:
            logger.warning("[NotionCache] FTS search error: %s", exc)
            return []

        return [dict(r) for r in rows]

    def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Return one cached page by ID (hyphens optional)."""
        if self._db is None:
            return None
        normalized = page_id.replace("-", "")
        conn = self._connect()
        row = conn.execute(
            "SELECT id, title, url, object_type, full_text, props_json, last_edited "
            "FROM notion_pages WHERE id = ?",
            (normalized,),
        ).fetchone()
        return dict(row) if row else None

    def get_all_formatted(self, max_chars: int = 80_000) -> str:
        """
        Return ALL cached content as a single formatted string, ready for
        injection into an LLM prompt.  Truncates at max_chars.
        """
        if self._db is None or not self._ready:
            return ""

        conn = self._connect()
        rows = conn.execute(
            "SELECT title, object_type, url, full_text "
            "FROM notion_pages ORDER BY object_type, title"
        ).fetchall()

        parts: List[str] = []
        total_chars = 0
        remaining = len(rows)

        for row in rows:
            remaining -= 1
            chunk = (
                f"=== {row['object_type'].upper()}: {row['title']} ===\n"
                f"{row['full_text']}\n"
            )
            if total_chars + len(chunk) > max_chars:
                parts.append(
                    f"... [{remaining + 1} more page(s) omitted — "
                    f"use search to query them]"
                )
                break
            parts.append(chunk)
            total_chars += len(chunk)

        return "\n".join(parts)

    def get_all_as_dict(self) -> Dict[str, Dict[str, str]]:
        """
        Return all cached pages as a dict compatible with the orchestrator's
        notion_cache state shape: {page_id: {"title": ..., "text": ...}}.
        """
        if self._db is None or not self._ready:
            return {}

        conn = self._connect()
        rows = conn.execute(
            "SELECT id, title, full_text FROM notion_pages ORDER BY title"
        ).fetchall()

        return {
            row["id"]: {"title": row["title"], "text": row["full_text"]}
            for row in rows
        }

    def page_count(self) -> int:
        if self._db is None:
            return 0
        row = self._connect().execute(
            "SELECT COUNT(*) AS n FROM notion_pages"
        ).fetchone()
        return int(row["n"]) if row else 0

    def is_ready(self) -> bool:
        return self._ready

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_duration(total_seconds: int) -> str:
        """Format seconds as HH:MM:SS for progress logs."""
        hours, remainder = divmod(max(total_seconds, 0), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @staticmethod
    def _extract_title(item: Dict[str, Any]) -> str:
        # Pages: top-level "title" array.
        top = item.get("title")
        if isinstance(top, list):
            return "".join(t.get("plain_text", "") for t in top) or "Untitled"

        # Pages/databases with a "properties" dict that has a "title" prop.
        for _k, v in item.get("properties", {}).items():
            if isinstance(v, dict) and v.get("type") == "title":
                rich = v.get("title", [])
                return "".join(t.get("plain_text", "") for t in rich) or "Untitled"

        return "Untitled"

    @staticmethod
    def _flatten_properties(props: Dict[str, Any]) -> Dict[str, str]:
        """Convert Notion property objects to plain {name: value_str} dict."""
        out: Dict[str, str] = {}
        for name, prop in props.items():
            ptype = prop.get("type", "")
            try:
                if ptype == "title":
                    out[name] = "".join(
                        t.get("plain_text", "") for t in prop.get("title", [])
                    )
                elif ptype == "rich_text":
                    out[name] = "".join(
                        t.get("plain_text", "") for t in prop.get("rich_text", [])
                    )
                elif ptype == "select":
                    out[name] = (prop.get("select") or {}).get("name", "")
                elif ptype == "multi_select":
                    out[name] = ", ".join(
                        o.get("name", "") for o in prop.get("multi_select", [])
                    )
                elif ptype == "number":
                    val = prop.get("number")
                    out[name] = str(val) if val is not None else ""
                elif ptype == "checkbox":
                    out[name] = str(prop.get("checkbox", ""))
                elif ptype == "date":
                    out[name] = (prop.get("date") or {}).get("start", "")
                elif ptype == "url":
                    out[name] = prop.get("url") or ""
                elif ptype == "email":
                    out[name] = prop.get("email") or ""
                elif ptype == "phone_number":
                    out[name] = prop.get("phone_number") or ""
                elif ptype == "status":
                    out[name] = (prop.get("status") or {}).get("name", "")
                elif ptype == "people":
                    out[name] = ", ".join(
                        p.get("name", "")
                        for p in prop.get("people", [])
                        if isinstance(p, dict)
                    )
            except Exception:
                pass
        return {k: v for k, v in out.items() if v}

    @staticmethod
    def _format_block(block: Dict[str, Any]) -> str:
        """Convert a single Notion block to a Markdown-ish text line."""
        btype = block.get("type", "")
        data = block.get(btype, {})
        rich = data.get("rich_text", [])
        text = "".join(t.get("plain_text", "") for t in rich)

        mapping = {
            "paragraph": text,
            "heading_1": f"# {text}",
            "heading_2": f"## {text}",
            "heading_3": f"### {text}",
            "bulleted_list_item": f"- {text}",
            "numbered_list_item": f"1. {text}",
            "to_do": f"[{'x' if data.get('checked') else ' '}] {text}",
            "quote": f"> {text}",
            "toggle": f"▶ {text}",
            "divider": "---",
            "child_page": f"[Page: {data.get('title', '')}]",
            "child_database": f"[Database: {data.get('title', '')}]",
        }

        if btype in mapping:
            return mapping[btype]

        if btype == "callout":
            emoji = (data.get("icon") or {}).get("emoji", "")
            return f"{emoji} {text}".strip()

        if btype == "code":
            lang = data.get("language", "")
            return f"```{lang}\n{text}\n```"

        if btype == "table_row":
            cells = data.get("cells", [])
            cell_texts = [
                "".join(t.get("plain_text", "") for t in cell)
                for cell in cells
            ]
            return " | ".join(cell_texts)

        if btype in ("image", "file", "pdf", "video", "audio"):
            caption = "".join(
                t.get("plain_text", "") for t in data.get("caption", [])
            )
            return f"[{btype}: {caption}]" if caption else f"[{btype}]"

        return text  # fallback


# ---------------------------------------------------------------------------
# Singleton helpers
# ---------------------------------------------------------------------------

_cache_layer: Optional[NotionCacheLayer] = None


def get_notion_cache_layer(
    cache_path: Optional[str] = None,
) -> NotionCacheLayer:
    """Return the global NotionCacheLayer instance, creating it if needed."""
    global _cache_layer
    if _cache_layer is None:
        _cache_layer = NotionCacheLayer(cache_path)
    return _cache_layer

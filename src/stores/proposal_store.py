"""
ProposalStore — Repository pattern for durable proposal and workflow state storage.

Current implementation: FileProposalStore (local JSON files).
Future: DynamoProposalStore for AWS DynamoDB.
"""

import json
import logging
import os
import re
import unicodedata
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_HTML_COMMENT_RE = re.compile(r"<!--.*?(?:-->|-+\u2192)", re.DOTALL)
_TEMPLATE_TAG_RE = re.compile(r"</?exemplo>", re.IGNORECASE)


class ProposalStore(ABC):
    """Abstract interface for proposal persistence."""

    @abstractmethod
    def save_analysis(self, session_id: str, data: Dict[str, Any]) -> str:
        """Persist analysis result. Returns storage key."""

    @abstractmethod
    def load_analysis(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load analysis result for session."""

    @abstractmethod
    def save_architecture(self, session_id: str, data: Dict[str, Any]) -> str:
        """Persist architecture contract. Returns storage key."""

    @abstractmethod
    def load_architecture(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load architecture contract for session."""

    @abstractmethod
    def save_proposal(self, session_id: str, data: Dict[str, Any]) -> str:
        """Persist final proposal. Returns file path or storage key."""

    @abstractmethod
    def load_proposal(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load proposal for session."""

    @abstractmethod
    def save_workflow_state(self, session_id: str, data: Dict[str, Any]) -> str:
        """Persist full workflow state snapshot."""

    @abstractmethod
    def load_workflow_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load workflow state for session."""

    @abstractmethod
    def append_audit(self, session_id: str, event: str, data: Dict[str, Any]) -> None:
        """Append an audit log entry."""


def _safe_filename(raw: str) -> str:
    """Normalize a string for safe filesystem usage."""
    normalized = unicodedata.normalize("NFKD", str(raw or ""))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = re.sub(r"\s+", "_", ascii_text.strip())
    ascii_text = re.sub(r"[^A-Za-z0-9_\-]", "", ascii_text)
    return ascii_text or "unknown"


class FileProposalStore(ProposalStore):
    """File-based implementation — stores JSON per session in a local directory."""

    def __init__(self, base_dir: str | None = None):
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
        self.sessions_dir = self.base_dir / ".nimbus_sessions"
        self.proposals_dir = self.base_dir / "propostas"
        self.audit_dir = self.base_dir / ".nimbus_audit"

    def _session_dir(self, session_id: str) -> Path:
        d = self.sessions_dir / _safe_filename(session_id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _write_json(self, path: Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def _read_json(self, path: Path) -> Optional[Dict[str, Any]]:
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_analysis(self, session_id: str, data: Dict[str, Any]) -> str:
        path = self._session_dir(session_id) / "analysis.json"
        self._write_json(path, data)
        logger.info("[FileProposalStore] Analysis saved: %s", path)
        return str(path)

    def load_analysis(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._read_json(self._session_dir(session_id) / "analysis.json")

    def save_architecture(self, session_id: str, data: Dict[str, Any]) -> str:
        path = self._session_dir(session_id) / "architecture.json"
        self._write_json(path, data)
        logger.info("[FileProposalStore] Architecture saved: %s", path)
        return str(path)

    def load_architecture(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._read_json(self._session_dir(session_id) / "architecture.json")

    def save_proposal(self, session_id: str, data: Dict[str, Any]) -> str:
        self.proposals_dir.mkdir(parents=True, exist_ok=True)

        metadata = data.get("metadata", {}) if isinstance(data, dict) else {}
        raw_client = metadata.get("client") or data.get("title") or "Cliente"
        client_slug = _safe_filename(raw_client)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = self.proposals_dir / f"nimbus-{client_slug}-{timestamp}.md"

        with open(filename, "w", encoding="utf-8") as f:
            heading = str(data.get("title") or "Proposta Tecnica").strip()
            f.write(f"{heading}\n")
            f.write("=" * 70 + "\n\n")
            if metadata.get("client"):
                f.write(f"Cliente: {metadata['client']}\n")
            f.write(f"Data: {datetime.now().strftime('%d/%m/%Y')}\n\n")

            for section in data.get("sections", []):
                if isinstance(section, dict):
                    title = section.get('title', 'Sem titulo')
                    content = section.get('content', '')
                    # Strip HTML/XML comment tags (template markers)
                    content = _HTML_COMMENT_RE.sub('', content)
                    # Strip template XML tags like <exemplo>, </exemplo>
                    content = _TEMPLATE_TAG_RE.sub('', content)
                    # Clean up blank lines left behind
                    content = re.sub(r'\n{3,}', '\n\n', content).strip()
                    f.write(f"## {title}\n\n")
                    f.write(f"{content}\n\n")

        # Also save structured JSON for re-processing
        json_path = self._session_dir(session_id) / "proposal.json"
        self._write_json(json_path, data)

        logger.info("[FileProposalStore] Proposal saved: %s", filename)
        return str(filename)

    def load_proposal(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._read_json(self._session_dir(session_id) / "proposal.json")

    def save_workflow_state(self, session_id: str, data: Dict[str, Any]) -> str:
        path = self._session_dir(session_id) / "workflow_state.json"
        self._write_json(path, data)
        return str(path)

    def load_workflow_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._read_json(self._session_dir(session_id) / "workflow_state.json")

    def append_audit(self, session_id: str, event: str, data: Dict[str, Any]) -> None:
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        path = self.audit_dir / "chat_audit.jsonl"
        entry = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "data": data,
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

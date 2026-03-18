"""
Orchestrator Agent - Coordinates the workflow between all specialized agents.
"""

import os
import hashlib
import random
import time
import logging
import re
import unicodedata
from datetime import datetime
from typing import Any, Dict, Callable

from strands import Agent
from strands.models import OpenAIModel

from .analysis_agent import AnalysisAgent
from .chat_policy_agent import ChatPolicyAgent
from .conversion_agent import ConversionAgent
from .generation_agent import GenerationAgent
from .questionnaire_agent import QuestionnaireAgent
from .review_agent import ReviewAgent
from .security_agent import SecurityAgent

ORCHESTRATOR_PROMPT = """
You are the Orchestrator Agent that coordinates specialized proposal agents.
Keep workflow state consistent, handle failures gracefully, and provide clear status.
"""

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """Coordinates analysis, questionnaire, generation, security, and conversion flows."""

    def __init__(self, notion_mcp_client=None, notion_cache_layer=None):
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.min_call_interval_seconds = float(os.getenv("NIMBUS_MIN_CALL_INTERVAL_SECONDS", "2.5"))
        self.max_rate_limit_retries = int(os.getenv("NIMBUS_RATE_LIMIT_RETRIES", "2"))
        self.base_backoff_seconds = float(os.getenv("NIMBUS_BACKOFF_BASE_SECONDS", "3.0"))
        self.enable_security_scan = os.getenv("NIMBUS_ENABLE_SECURITY_SCAN", "false").lower() == "true"
        self.review_score_threshold = float(os.getenv("NIMBUS_REVIEW_SCORE_THRESHOLD", "8.0"))
        self.max_review_regeneration = int(os.getenv("NIMBUS_MAX_REVIEW_REGENERATION", "1"))
        self._last_llm_call_at = 0.0

        # Local Notion cache layer (SQLite mirror of the full workspace).
        self.notion_cache_layer = notion_cache_layer

        use_notion_tools = os.getenv("NIMBUS_ENABLE_NOTION_TOOLS", "false").lower() == "true"
        notion_client_for_agents = notion_mcp_client if use_notion_tools else None

        self.analysis_agent = AnalysisAgent(notion_mcp_client=notion_client_for_agents)
        self.chat_policy_agent = ChatPolicyAgent()
        self.questionnaire_agent = QuestionnaireAgent()
        self.generation_agent = GenerationAgent(notion_mcp_client=notion_client_for_agents)
        self.review_agent = ReviewAgent()
        self.security_agent = SecurityAgent()
        self.conversion_agent = ConversionAgent()

        self.agent = Agent(
            model=OpenAIModel(
                model_id="gpt-4o",
                params={
                    "temperature": 0.2,
                    "max_tokens": 1024,
                },
            ),
            system_prompt=ORCHESTRATOR_PROMPT,
            tools=[],
            callback_handler=None,
        )

        self.state: Dict[str, Any] = {
            "current_step": "init",
            "analysis_result": None,
            "questionnaire": None,
            "user_answers": None,
            "generated_proposal": None,
            "security_scan": None,
            "final_output": None,
            "history": [],
            "notion_cache": {},
            "analysis_cache": {},
            "questionnaire_cache": {},
            "proposal_cache": {},
            "security_cache": {},
            "final_output_cache": {},
        }

    def _log_step(self, step: str, data: Any = None) -> None:
        self.state["history"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "step": step,
                "data": data,
            }
        )
        self.state["current_step"] = step
        logger.info("[Orchestrator] %s", step)

    def _populate_notion_cache_from_layer(self) -> None:
        """
        Load all cached Notion pages from the local SQLite layer into
        self.state["notion_cache"] so that _format_notion_cache() and
        _extract_required_fields_from_notion_cache() have content to work with.
        """
        if self.notion_cache_layer is None:
            return
        if not self.notion_cache_layer.is_ready():
            logger.info("[Orchestrator] Notion cache layer not ready yet — skipping injection.")
            return
        pages = self.notion_cache_layer.get_all_as_dict()
        if pages:
            self.state["notion_cache"].update(pages)
            logger.info(
                "[Orchestrator] Loaded %d pages from Notion cache layer.", len(pages)
            )

    def _build_cache_wait_response(self, reason: str) -> Dict[str, Any]:
        """Return a standardized response when Notion cache is mandatory but unavailable."""
        status = "Aguardando sincronizacao do cache do Notion"
        message = (
            "Ainda estou sincronizando o cache do Notion. "
            "Por favor, aguarde alguns instantes e tente novamente."
        )
        details = {
            "reason": reason,
            "cache_layer_available": self.notion_cache_layer is not None,
            "cache_ready": bool(self.notion_cache_layer and self.notion_cache_layer.is_ready()),
            "cached_pages": int(self.notion_cache_layer.page_count()) if self.notion_cache_layer else 0,
        }
        return {
            "success": False,
            "requires_input": False,
            "waiting_for_cache": True,
            "status": status,
            "assistant_message": message,
            "cache_status": details,
            "workflow_state": self.get_workflow_state(),
        }

    def _ensure_notion_cache_ready(self) -> Dict[str, Any] | None:
        """
        Enforce strict cache usage.

        Returns:
            None when cache is ready and populated.
            Error payload dict when cache is unavailable/not ready/empty.
        """
        if self.notion_cache_layer is None:
            return self._build_cache_wait_response("cache_layer_unavailable")

        # Always trigger sync attempt before checking readiness.
        try:
            self.notion_cache_layer.start_sync_if_needed()
        except Exception:
            logger.exception("[Orchestrator] Failed to trigger Notion cache sync")

        if not self.notion_cache_layer.is_ready():
            return self._build_cache_wait_response("cache_sync_in_progress")

        if int(self.notion_cache_layer.page_count()) <= 0:
            return self._build_cache_wait_response("cache_empty")

        self._populate_notion_cache_from_layer()
        if not self.state.get("notion_cache"):
            return self._build_cache_wait_response("cache_not_loaded_into_orchestrator")

        return None

    def analyze_requirements(self, input_text: str, input_type: str = "text") -> Dict[str, Any]:
        """Analyze requirements only after strict Notion cache availability checks."""
        gate = self._ensure_notion_cache_ready()
        if isinstance(gate, dict):
            return gate

        cache_str = self._compact_text(self._format_notion_cache())
        return self.analysis_agent.analyze(input_text, input_type=input_type, notion_cache=cache_str)

    def _format_notion_cache(self) -> str:
        fragments = []
        for page_id, info in self.state.get("notion_cache", {}).items():
            title = info.get("title", "(no title)") if isinstance(info, dict) else "(invalid)"
            text = info.get("text", "") if isinstance(info, dict) else ""
            fragments.append(f"--- Notion Page: {title} ({page_id}) ---\n{text}\n")
        return "\n".join(fragments)

    def _throttle_next_call(self) -> None:
        """Apply proactive pacing between model calls to reduce 429 bursts."""
        now = time.monotonic()
        wait_for = self.min_call_interval_seconds - (now - self._last_llm_call_at)
        if wait_for > 0:
            time.sleep(wait_for)
        self._last_llm_call_at = time.monotonic()

    def _is_rate_limit_error(self, exc: Exception) -> bool:
        """Best-effort detection for provider 429 errors."""
        msg = str(exc).lower()
        return "429" in msg or "rate limit" in msg or "too many requests" in msg

    def _run_with_rate_limit_control(self, step_name: str, fn: Callable[..., Any], *args, **kwargs) -> Any:
        """Run a callable with pacing and bounded exponential backoff on 429."""
        attempts = self.max_rate_limit_retries + 1
        for attempt in range(1, attempts + 1):
            try:
                self._throttle_next_call()
                return fn(*args, **kwargs)
            except Exception as e:
                if not self._is_rate_limit_error(e) or attempt == attempts:
                    raise
                delay = self.base_backoff_seconds * (2 ** (attempt - 1))
                jitter = random.uniform(0.0, 0.8)
                sleep_for = delay + jitter
                self._log_step("rate_limited_retry", {
                    "step": step_name,
                    "attempt": attempt,
                    "sleep_seconds": round(sleep_for, 2),
                })
                time.sleep(sleep_for)

    def _hash_text(self, text: str) -> str:
        """Create stable hash for cache keys."""
        value = text if isinstance(text, str) else str(text)
        return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()

    def _hash_obj(self, payload: Any) -> str:
        """Create stable hash for serializable payloads."""
        stable = str(payload)
        try:
            import json

            stable = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
        except Exception:
            pass
        return self._hash_text(stable)

    def _compact_text(self, text: str, max_chars: int = 6000) -> str:
        """Bound prompt size to reduce token pressure and avoid rate limits."""
        if not isinstance(text, str):
            return ""
        clean = text.strip()
        if len(clean) <= max_chars:
            return clean
        return clean[:max_chars] + "\n\n[cache truncated for token control]"

    def _field_input_hint(
        self,
        field_name: str,
        description: str = "",
        notion_guidance: Dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """Build field hints using Notion evidence first, without domain hardcoding."""
        guidance = notion_guidance if isinstance(notion_guidance, dict) else {}
        field_hints = guidance.get("field_hints", {}) if isinstance(guidance, dict) else {}
        field_key = str(field_name or "").strip()

        expected = "Siga o formato e o nivel de detalhe definidos no template do Notion para este campo."
        example = ""
        if isinstance(field_hints, dict):
            field_info = field_hints.get(field_key, {})
            if isinstance(field_info, dict):
                snippets = field_info.get("snippets", [])
                if isinstance(snippets, list) and snippets:
                    first = str(snippets[0]).strip()
                    if first:
                        expected = f"Baseie a resposta no padrao observado: {first[:220]}"
                examples = field_info.get("examples", [])
                if isinstance(examples, list) and examples:
                    example = str(examples[0]).strip()[:220]

        if not example:
            desc = str(description or "").strip()
            if desc:
                example = f"Responder especificamente sobre: {desc[:180]}"

        return {
            "expectedFormat": expected,
            "exampleAnswer": example,
        }

    def _build_questionnaire_from_gaps(self, data_gaps: list[dict[str, Any]]) -> Dict[str, Any]:
        """Generate questionnaire from context and evidence retrieved from Notion cache."""
        user_input_hint = ""
        history = self.state.get("history", [])
        if isinstance(history, list) and history:
            last = history[-1]
            if isinstance(last, dict) and isinstance(last.get("data"), dict):
                user_input_hint = str(last.get("data", {}).get("user_input", ""))

        notion_guidance = self._extract_notion_guidance_for_chat(user_input_hint, data_gaps)
        evidence_context = {
            "queries": notion_guidance.get("query_pack", [])[:20] if isinstance(notion_guidance, dict) else [],
            "pages": [
                {
                    "page_id": item.get("page_id"),
                    "title": item.get("title"),
                    "matched_queries": item.get("matched_queries", []),
                }
                for item in (notion_guidance.get("matched_pages", [])[:10] if isinstance(notion_guidance, dict) else [])
                if isinstance(item, dict)
            ],
        }

        dynamic = self.chat_policy_agent.build_questionnaire(
            user_input=user_input_hint,
            data_gaps=data_gaps,
            notion_guidance=notion_guidance,
        )

        if isinstance(dynamic, dict) and isinstance(dynamic.get("questions"), list) and dynamic.get("questions"):
            # Normalize fields expected by server response format.
            questions = []
            for idx, q in enumerate(dynamic.get("questions", []), start=1):
                if not isinstance(q, dict):
                    continue
                text = str(q.get("text", "")).strip()
                field = str(q.get("field", "")).strip()
                description = str(q.get("reason", "")).strip()
                hint = self._field_input_hint(field, description, notion_guidance)
                questions.append(
                    {
                        "id": str(q.get("id") or f"q{idx}"),
                        "field": field,
                        "text": text or f"Poderia detalhar o campo '{field}'?",
                        "type": "text",
                        "required": bool(q.get("required", True)),
                        "priority": str(q.get("priority", "important")),
                        "helpText": description or "Informacao necessaria para elevar a qualidade da proposta.",
                        "expectedFormat": str(q.get("expectedFormat") or hint.get("expectedFormat", "texto objetivo")),
                        "exampleAnswer": str(q.get("exampleAnswer") or hint.get("exampleAnswer", "")),
                        "evidence": q.get("evidence", []),
                        "options": [],
                        "validation": q.get("validation", {"minLength": 3, "maxLength": 2000, "pattern": ".+"}),
                    }
                )
            if questions:
                return {
                    "id": str(dynamic.get("id") or f"questionnaire_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                    "questions": questions,
                    "estimatedTime": int(dynamic.get("estimatedTime") or max(5, len(questions) * 2)),
                    "notion_context": evidence_context,
                }

        # Safe fallback to deterministic generation if LLM output is invalid.
        questions = []
        for idx, gap in enumerate(data_gaps, start=1):
            field = gap.get("field", f"campo_{idx}") if isinstance(gap, dict) else f"campo_{idx}"
            description = ""
            if isinstance(gap, dict):
                description = str(gap.get("description", "")).strip()
            hint = self._field_input_hint(str(field), description, notion_guidance)
            question_text = f"Poderia detalhar o campo '{field}'?"
            if description:
                question_text = f"{question_text} Contexto: {description}"
            example = hint.get("exampleAnswer", "")
            if example:
                question_text = f"{question_text} Exemplo: {example}"
            questions.append(
                {
                    "id": f"q{idx}",
                    "field": str(field),
                    "text": question_text,
                    "type": "text",
                    "required": bool(gap.get("required", True)) if isinstance(gap, dict) else True,
                    "priority": "critical" if isinstance(gap, dict) and gap.get("required", True) else "important",
                    "helpText": (
                        "Responder com dados objetivos para continuidade da proposta. "
                        f"Formato esperado: {hint.get('expectedFormat', 'texto objetivo')}."
                    ),
                    "expectedFormat": hint.get("expectedFormat", "texto objetivo"),
                    "exampleAnswer": hint.get("exampleAnswer", ""),
                    "options": [],
                    "validation": {"minLength": 3, "maxLength": 2000, "pattern": ".+"},
                }
            )
        return {
            "id": f"questionnaire_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "questions": questions,
            "estimatedTime": max(5, len(questions) * 2),
            "notion_context": evidence_context,
        }

    def _extract_notion_guidance_for_chat(
        self,
        user_input: str,
        data_gaps: list[dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build context guidance by querying cache with terms from input and required fields."""
        query_pack = self._build_notion_query_pack(user_input, data_gaps)
        matches = self._search_notion_cache_by_queries(query_pack, per_query_limit=6)

        pages: dict[str, dict[str, Any]] = {}
        for row in matches:
            page_id = str(row.get("page_id", "")).strip()
            if not page_id:
                continue
            entry = pages.get(page_id)
            if not isinstance(entry, dict):
                entry = {
                    "page_id": page_id,
                    "title": row.get("title", ""),
                    "snippets": [],
                    "matched_queries": [],
                    "match_count": 0,
                }
                pages[page_id] = entry
            snippet = str(row.get("snippet", "")).strip()
            query = str(row.get("query", "")).strip()
            if snippet and snippet not in entry["snippets"]:
                entry["snippets"].append(snippet)
            if query and query not in entry["matched_queries"]:
                entry["matched_queries"].append(query)
            entry["match_count"] = int(entry.get("match_count", 0)) + 1

        matched_pages = sorted(
            pages.values(),
            key=lambda item: int(item.get("match_count", 0)),
            reverse=True,
        )[:20]

        field_hints: dict[str, dict[str, Any]] = {}
        for gap in data_gaps:
            if not isinstance(gap, dict):
                continue
            field = str(gap.get("field", "")).strip()
            if not field:
                continue
            field_tokens = self._field_tokens(field)
            snippets: list[str] = []
            examples: list[str] = []
            for page in matched_pages:
                for snippet in page.get("snippets", []):
                    snippet_text = str(snippet)
                    low = snippet_text.lower()
                    if any(token in low for token in field_tokens):
                        if snippet_text not in snippets:
                            snippets.append(snippet_text[:260])
                        if "exemplo" in low or "example" in low:
                            examples.append(snippet_text[:220])
                    if len(snippets) >= 3 and len(examples) >= 2:
                        break
                if len(snippets) >= 3 and len(examples) >= 2:
                    break
            field_hints[field] = {
                "snippets": snippets,
                "examples": examples,
            }

        return {
            "query_pack": query_pack,
            "matched_pages": matched_pages,
            "field_hints": field_hints,
        }

    def _field_tokens(self, field_path: str) -> list[str]:
        """Tokenize a field path into lower-case search hints."""
        raw = str(field_path or "").strip()
        if not raw:
            return []
        parts = [p for p in raw.split(".") if p]
        leaf = parts[-1] if parts else raw
        leaf_spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", leaf)
        tokens = re.findall(r"[a-z0-9]{3,}", leaf_spaced.lower())
        full = raw.lower()
        out = [full, leaf.lower()]
        out.extend(tokens)
        return [t for t in dict.fromkeys(out) if t]

    def _build_notion_query_pack(self, user_input: str, data_gaps: list[dict[str, Any]]) -> list[str]:
        """Prepare cache queries from user context and required field metadata."""
        queries: list[str] = []

        user_tokens = re.findall(r"[a-z0-9_\-]{4,}", self._normalize_for_search(str(user_input or "")))
        for token in user_tokens[:10]:
            queries.append(token)

        for field_path, label in self._required_fields():
            queries.append(str(field_path).strip())
            normalized_label = self._normalize_for_search(str(label).strip())
            if normalized_label:
                queries.append(normalized_label)

        for gap in data_gaps:
            if not isinstance(gap, dict):
                continue
            field = str(gap.get("field", "")).strip()
            description = str(gap.get("description", "")).strip()
            if field:
                queries.append(field)
                queries.append(f"{field} required")
                for token in self._field_tokens(field):
                    if len(token) >= 4:
                        queries.append(token)
            normalized_desc = self._normalize_for_search(description)
            for token in re.findall(r"[a-z0-9_\-]{4,}", normalized_desc)[:6]:
                queries.append(token)

        # keep deterministic order and uniqueness
        return [q for q in dict.fromkeys(q.strip() for q in queries) if q]

    def _normalize_for_search(self, text: str) -> str:
        """Normalize text for stable query tokens (remove accents, lowercase)."""
        value = unicodedata.normalize("NFKD", str(text or ""))
        ascii_text = value.encode("ascii", "ignore").decode("ascii")
        return ascii_text.lower()

    def _search_notion_cache_by_queries(self, queries: list[str], per_query_limit: int = 5) -> list[dict[str, Any]]:
        """Search local Notion cache for each query and return normalized rows."""
        results: list[dict[str, Any]] = []

        layer = self.notion_cache_layer
        if layer is not None and layer.is_ready():
            for query in queries:
                try:
                    hits = layer.search(query, limit=per_query_limit)
                except Exception:
                    logger.exception("[Orchestrator] Cache query failed: %s", query)
                    hits = []
                for hit in hits:
                    if not isinstance(hit, dict):
                        continue
                    results.append(
                        {
                            "query": query,
                            "page_id": str(hit.get("id", "")).strip(),
                            "title": str(hit.get("title", "")).strip(),
                            "snippet": str(hit.get("snippet", "")).strip(),
                        }
                    )
            return results

        cache = self.state.get("notion_cache", {})
        if not isinstance(cache, dict):
            return results

        # Fallback when cache layer search is unavailable: naive text search on loaded cache.
        for query in queries:
            q = query.lower().strip()
            if not q:
                continue
            matched = 0
            for page_id, info in cache.items():
                if matched >= per_query_limit:
                    break
                if not isinstance(info, dict):
                    continue
                title = str(info.get("title", ""))
                text = str(info.get("text", ""))
                blob = f"{title}\n{text}".lower()
                pos = blob.find(q)
                if pos < 0:
                    continue
                start = max(0, pos - 80)
                end = min(len(text), start + 260)
                snippet = text[start:end] if text else title
                results.append(
                    {
                        "query": query,
                        "page_id": str(page_id),
                        "title": title,
                        "snippet": snippet,
                    }
                )
                matched += 1

        return results

    def _extract_required_fields_from_notion_cache(self) -> list[tuple[str, str]]:
        """Extract required fields strictly from explicit Notion template signals."""
        template_text = self._get_template_text_from_notion_cache()
        if not template_text:
            return []

        text_blob = template_text
        if not text_blob.strip():
            return []

        required_markers = ("obrigat", "required", "mandat")
        field_candidates: list[str] = []

        json_pair_patterns = [
            r'"field"\s*:\s*"([^"\n]+)"[\s\S]{0,220}?"required"\s*:\s*true',
            r'"required"\s*:\s*true[\s\S]{0,220}?"field"\s*:\s*"([^"\n]+)"',
            r"'field'\s*:\s*'([^'\n]+)'[\s\S]{0,220}?'required'\s*:\s*true",
            r"'required'\s*:\s*true[\s\S]{0,220}?'field'\s*:\s*'([^'\n]+)'",
        ]
        for pattern in json_pair_patterns:
            for match in re.finditer(pattern, text_blob, flags=re.IGNORECASE):
                candidate = str(match.group(1)).strip()
                if candidate:
                    field_candidates.append(candidate)

        field_after_label = re.compile(
            r"(?:campo|field)\s*[:=\-]\s*`?([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*)`?",
            re.IGNORECASE,
        )
        required_then_field = re.compile(
            r"(?:obrigat\w*|required|mandat\w*)[\s\S]{0,120}?(?:campo|field)\s*[:=\-]\s*`?([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*)`?",
            re.IGNORECASE,
        )

        for raw_line in text_blob.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            by_label = field_after_label.search(line)
            if by_label and any(marker in line.lower() for marker in required_markers):
                field_candidates.append(by_label.group(1).strip())

        for match in required_then_field.finditer(text_blob):
            candidate = str(match.group(1)).strip()
            if candidate:
                field_candidates.append(candidate)

        seen: set[str] = set()
        extracted: list[tuple[str, str]] = []
        for raw in field_candidates:
            normalized = raw.strip().strip("`\"' ")
            if not normalized:
                continue
            if len(normalized) < 2:
                continue
            if not re.match(r"^[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*$", normalized):
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            extracted.append((normalized, self._humanize_field_label(normalized)))

        return extracted

    def _get_template_text_from_notion_cache(self) -> str:
        """Return template text only from a page explicitly identified as proposal template."""
        cache = self.state.get("notion_cache", {})
        if not isinstance(cache, dict) or not cache:
            return ""

        for value in cache.values():
            if not isinstance(value, dict):
                continue
            title = str(value.get("title", "")).strip().lower()
            if "template" in title and "proposta" in title:
                return str(value.get("text", ""))
        return ""

    def _humanize_field_label(self, field_name: str) -> str:
        """Build a readable label from a field path without hardcoded domain fields."""
        parts = [p for p in str(field_name).split(".") if p]
        leaf = parts[-1] if parts else str(field_name)
        leaf = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", leaf)
        leaf = leaf.replace("_", " ").replace("-", " ").strip()
        if not leaf:
            return str(field_name)
        return leaf[0].upper() + leaf[1:]

    def _required_fields(self) -> list[tuple[str, str]]:
        """Return only Notion-inferred required fields with stable ordering."""
        merged: list[tuple[str, str]] = []
        seen: set[str] = set()

        for field_path, label in self._extract_required_fields_from_notion_cache():
            if field_path in seen:
                continue
            seen.add(field_path)
            merged.append((field_path, label))
        return merged

    def _extract_template_sections_from_notion_cache(self, template_text: str | None = None) -> list[str]:
        """Extract template section order from top-level markdown headings in template text."""
        if not isinstance(template_text, str):
            template_text = self._get_template_text_from_notion_cache()
        if not template_text:
            return []

        sections: list[str] = []
        seen: set[str] = set()
        for raw_line in template_text.splitlines():
            line = str(raw_line).strip()
            if not line:
                continue

            heading = re.match(r"^(#{1,6})\s+(.+)$", line)
            if not heading:
                continue

            level = len(heading.group(1))
            # Keep only document section headings; subsection headings belong to body content.
            if level > 2:
                continue

            candidate = heading.group(2).strip(" -:\t")

            if len(candidate) < 4:
                continue
            low = candidate.lower()
            if "exemplo" in low or "observa" in low or "instru" in low:
                continue

            key = low
            if key in seen:
                continue
            seen.add(key)
            sections.append(candidate)

        return sections

    def _get_nested(self, obj: Dict[str, Any], path: str) -> Any:
        current: Any = obj
        for key in path.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current

    def _set_nested(self, obj: Dict[str, Any], path: str, value: Any) -> None:
        keys = path.split(".")
        current = obj
        for key in keys[:-1]:
            next_val = current.get(key)
            if not isinstance(next_val, dict):
                next_val = {}
                current[key] = next_val
            current = next_val
        current[keys[-1]] = value

    def _merge_user_answers(self, analysis_data: Dict[str, Any], user_answers: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user-provided answers into analysis data."""
        merged = dict(analysis_data)
        if not isinstance(user_answers, dict):
            return merged

        for path, _label in self._required_fields():
            flat_key = path.replace(".", "_")
            value = None

            if path in user_answers:
                value = user_answers.get(path)
            elif flat_key in user_answers:
                value = user_answers.get(flat_key)
            elif path.startswith("clientInfo.") and isinstance(user_answers.get("clientInfo"), dict):
                sub_key = path.split(".", 1)[1]
                value = user_answers["clientInfo"].get(sub_key)

            if isinstance(value, str):
                value = value.strip()
            if value not in (None, ""):
                self._set_nested(merged, path, value)

        # Also merge generic answers (quality-gap mode may use non-template field names).
        for key, value in user_answers.items():
            if not isinstance(key, str):
                continue
            normalized_key = key.strip()
            if not normalized_key:
                continue
            if isinstance(value, str):
                value = value.strip()
            if value in (None, ""):
                continue
            self._set_nested(merged, normalized_key, value)

        return merged

    def _normalize_analysis_aliases(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map top-level aliases to required nested paths based on Notion-required fields."""
        if not isinstance(analysis_data, dict):
            return {}

        normalized = dict(analysis_data)
        for target_path, _label in self._required_fields():
            if "." not in target_path:
                continue
            source_key = target_path.split(".")[-1]
            current_val = self._get_nested(normalized, target_path)
            if current_val not in (None, ""):
                continue
            source_val = normalized.get(source_key)
            if isinstance(source_val, str):
                source_val = source_val.strip()
            if source_val not in (None, ""):
                self._set_nested(normalized, target_path, source_val)

        return normalized

    def _collect_required_gaps(self, analysis_data: Dict[str, Any]) -> list[dict[str, Any]]:
        """Build gaps list strictly from Notion-required fields."""
        gaps: list[dict[str, Any]] = []
        required_pairs = self._required_fields()
        existing = analysis_data.get("dataGaps", []) if isinstance(analysis_data, dict) else []

        if not required_pairs:
            return gaps

        required_set = {field for field, _label in required_pairs}
        existing_by_field: dict[str, dict[str, Any]] = {}

        if isinstance(existing, list):
            for item in existing:
                if isinstance(item, dict) and item.get("field"):
                    field_name = str(item.get("field", "")).strip()
                    if field_name in required_set:
                        existing_by_field[field_name] = item

        for field_path, label in required_pairs:
            value = self._get_nested(analysis_data, field_path)
            missing = value is None or (isinstance(value, str) and not value.strip())
            if missing:
                base_item = existing_by_field.get(field_path, {})
                description = str(base_item.get("description", "")).strip()
                suggested = base_item.get("suggestedQuestions", [])
                if not isinstance(suggested, list) or not suggested:
                    suggested = [f"Informe: {label}"]
                gaps.append(
                    {
                        "field": field_path,
                        "description": description or f"{label} é obrigatório no template do Notion.",
                        "required": True,
                        "suggestedQuestions": suggested,
                    }
                )
        return gaps

    def generate_proposal(self, user_input: str, user_answers: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Generate a complete proposal flow result from raw user input."""
        if not isinstance(user_input, str) or not user_input.strip():
            return {
                "success": False,
                "error": "user_input must be a non-empty string",
                "workflow_state": self.get_workflow_state(),
                "status": "Erro na geracao da proposta",
            }

        try:
            self._log_step("workflow_started", {"user_input": user_input[:120]})

            # Strict cache gate: never continue proposal workflow without Notion cache.
            gate = self._ensure_notion_cache_ready()
            if isinstance(gate, dict):
                self._log_step("workflow_waiting_cache", gate.get("cache_status"))
                return gate

            input_key = self._hash_text(user_input.strip())
            cached_output = self.state["final_output_cache"].get(input_key)
            if isinstance(cached_output, dict):
                self._log_step("workflow_completed_from_cache", {"input_hash": input_key[:12]})
                return dict(cached_output)

            cache_str = self._compact_text(self._format_notion_cache())

            self._log_step("analysis_started")
            analysis_t0 = time.perf_counter()
            analysis_result = self.state["analysis_cache"].get(input_key)
            if not isinstance(analysis_result, dict):
                analysis_result = self._run_with_rate_limit_control(
                    "analysis",
                    self.analysis_agent.analyze,
                    user_input,
                    input_type="natural_language",
                    notion_cache=cache_str,
                )
                self.state["analysis_cache"][input_key] = analysis_result
            self.state["analysis_result"] = analysis_result

            # Fail fast if analysis did not succeed; do not continue to generation.
            if isinstance(analysis_result, dict):
                if analysis_result.get("status") == "analysis_failed" or analysis_result.get("error"):
                    err = analysis_result.get("error", "analysis_failed")
                    raise RuntimeError(f"analysis_failed: {err}")

            analysis_data = analysis_result.get("analysis", {}) if isinstance(analysis_result, dict) else {}
            if not isinstance(analysis_data, dict):
                analysis_data = {"raw_analysis": str(analysis_data)}

            analysis_data = self._normalize_analysis_aliases(analysis_data)

            if isinstance(user_answers, dict) and user_answers:
                analysis_data = self._merge_user_answers(analysis_data, user_answers)
                analysis_data = self._normalize_analysis_aliases(analysis_data)

            self._log_step("analysis_completed", {"duration_ms": int((time.perf_counter() - analysis_t0) * 1000)})

            data_gaps = self._collect_required_gaps(analysis_data)

            if data_gaps:
                self._log_step("questionnaire_started", {"gaps": len(data_gaps)})
                gaps_key = self._hash_obj(data_gaps)
                questionnaire = self.state["questionnaire_cache"].get(gaps_key)
                if not isinstance(questionnaire, dict):
                    questionnaire = self._build_questionnaire_from_gaps(data_gaps)
                    self.state["questionnaire_cache"][gaps_key] = questionnaire
                self.state["questionnaire"] = questionnaire
                self._log_step("questionnaire_completed")
                return {
                    "success": False,
                    "requires_input": True,
                    "status": "Informações obrigatórias pendentes para gerar proposta",
                    "required_fields_source": "notion",
                    "questionnaire": questionnaire,
                    "pending_fields": [
                        item.get("field") for item in data_gaps if isinstance(item, dict) and item.get("field")
                    ],
                    "input_examples": {
                        str(item.get("field")): self._field_input_hint(
                            str(item.get("field")),
                            str(item.get("description", "")),
                        )
                        for item in data_gaps
                        if isinstance(item, dict) and item.get("field")
                    },
                    "workflow_state": self.get_workflow_state(),
                }

            self._log_step("generation_started")
            generation_t0 = time.perf_counter()
            template_text = self._get_template_text_from_notion_cache()
            if not isinstance(template_text, str) or not template_text.strip():
                self._log_step("template_text_not_found_in_cache")
                return {
                    "success": False,
                    "requires_input": False,
                    "status": "Template de proposta nao encontrado no cache do Notion",
                    "error": "template_text_not_found_in_cache",
                    "workflow_state": self.get_workflow_state(),
                }

            template_sections = self._extract_template_sections_from_notion_cache(template_text)
            if not template_sections:
                self._log_step("template_sections_not_found_in_cache")
                return {
                    "success": False,
                    "requires_input": False,
                    "status": "Template do Notion sem seções explícitas (modo estrito)",
                    "error": "template_sections_not_found_in_cache",
                    "workflow_state": self.get_workflow_state(),
                }

            generation_context = {
                "analysis": analysis_data,
                "data_gaps": data_gaps,
                "user_input": user_input,
                "questionnaire": self.state.get("questionnaire"),
                "notion_cache": cache_str,
                "template_text": template_text,
                "template_sections": template_sections,
            }
            generation_key = self._hash_obj(generation_context)
            proposal_sections = self.state["proposal_cache"].get(generation_key)
            if not isinstance(proposal_sections, list):
                proposal_sections = self._run_with_rate_limit_control(
                    "generation",
                    self.generation_agent.generate_full_proposal,
                    generation_context,
                    notion_cache=cache_str,
                )
                self.state["proposal_cache"][generation_key] = proposal_sections

            if (
                isinstance(proposal_sections, list)
                and proposal_sections
                and isinstance(proposal_sections[0], dict)
                and proposal_sections[0].get("status") == "generation_failed"
            ):
                raise RuntimeError(str(proposal_sections[0].get("error", "generation_failed")))

            proposal = {
                "title": analysis_data.get("clientInfo", {}).get("projectName", "Proposta Tecnica"),
                "sections": proposal_sections,
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "client": analysis_data.get("clientInfo", {}).get("companyName"),
                    "technologies": analysis_data.get("technologies", []),
                    "template_sections": template_sections,
                },
            }

            validation = self.generation_agent.validate_proposal(proposal, expected_sections=template_sections)
            review_result = self._run_with_rate_limit_control(
                "review",
                self.review_agent.review_proposal,
                proposal,
                template_sections,
                cache_str,
                analysis_data,
            )

            if isinstance(review_result, dict):
                review_score = float(review_result.get("score", 0.0) or 0.0)
                needs_regen = (review_score < self.review_score_threshold) or not validation.get("valid", False)
            else:
                review_score = 0.0
                needs_regen = True

            regen_attempt = 0
            while needs_regen and regen_attempt < self.max_review_regeneration:
                regen_attempt += 1
                self._log_step(
                    "review_regeneration_started",
                    {
                        "attempt": regen_attempt,
                        "review_score": review_score,
                        "validation_errors": len(validation.get("errors", [])),
                    },
                )

                review_actions = review_result.get("actions", []) if isinstance(review_result, dict) else []
                review_feedback = "\n".join(str(item) for item in review_actions if isinstance(item, str))

                generation_context_retry = dict(generation_context)
                generation_context_retry["review_feedback"] = review_feedback
                retry_key = self._hash_obj(generation_context_retry)

                proposal_sections_retry = self.state["proposal_cache"].get(retry_key)
                if not isinstance(proposal_sections_retry, list):
                    proposal_sections_retry = self._run_with_rate_limit_control(
                        "generation_retry",
                        self.generation_agent.generate_full_proposal,
                        generation_context_retry,
                        notion_cache=cache_str,
                    )
                    self.state["proposal_cache"][retry_key] = proposal_sections_retry

                proposal = {
                    "title": analysis_data.get("clientInfo", {}).get("projectName", "Proposta Tecnica"),
                    "sections": proposal_sections_retry,
                    "metadata": {
                        "created": datetime.now().isoformat(),
                        "client": analysis_data.get("clientInfo", {}).get("companyName"),
                        "technologies": analysis_data.get("technologies", []),
                        "template_sections": template_sections,
                        "review_regeneration_attempt": regen_attempt,
                    },
                }

                validation = self.generation_agent.validate_proposal(proposal, expected_sections=template_sections)
                review_result = self._run_with_rate_limit_control(
                    "review_retry",
                    self.review_agent.review_proposal,
                    proposal,
                    template_sections,
                    cache_str,
                    analysis_data,
                )
                review_score = float(review_result.get("score", 0.0) or 0.0) if isinstance(review_result, dict) else 0.0
                needs_regen = (review_score < self.review_score_threshold) or not validation.get("valid", False)

                self._log_step(
                    "review_regeneration_completed",
                    {
                        "attempt": regen_attempt,
                        "review_score": review_score,
                        "validation_valid": bool(validation.get("valid", False)),
                    },
                )

            self.state["generated_proposal"] = proposal
            self._log_step(
                "generation_completed",
                {
                    "sections_count": len(proposal.get("sections", [])),
                    "duration_ms": int((time.perf_counter() - generation_t0) * 1000),
                    "review_score": review_score,
                },
            )

            security_result: Dict[str, Any] = {
                "overallRisk": "not_scanned",
                "findings": [],
                "summary": {
                    "totalFindings": 0,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                },
            }
            if self.enable_security_scan:
                self._log_step("security_scan_started")
                security_t0 = time.perf_counter()
                proposal_key = self._hash_obj(proposal)
                security_result = self.state["security_cache"].get(proposal_key)
                if not isinstance(security_result, dict):
                    security_result = self._run_with_rate_limit_control(
                        "security",
                        self.security_agent.scan_proposal,
                        proposal,
                    )
                    self.state["security_cache"][proposal_key] = security_result
                self.state["security_scan"] = security_result
                self._log_step(
                    "security_scan_completed",
                    {
                        "risk_level": security_result.get("overallRisk", "unknown"),
                        "duration_ms": int((time.perf_counter() - security_t0) * 1000),
                    },
                )
            else:
                self._log_step("security_scan_skipped", {"reason": "NIMBUS_ENABLE_SECURITY_SCAN=false"})

            self._log_step("finalization_started")
            output_path = self._save_proposal_to_file(proposal)

            final_output = {
                "success": True,
                "proposal": proposal,
                "review": {
                    "score_threshold": self.review_score_threshold,
                    "result": review_result,
                    "validation": validation,
                    "regeneration_attempts": regen_attempt,
                    "passed": not needs_regen,
                },
                "security_assessment": security_result,
                "workflow_state": self.get_workflow_state(),
                "status": "Proposta gerada com sucesso",
                "output_file": output_path,
            }
            self.state["final_output"] = final_output
            self.state["final_output_cache"][input_key] = final_output
            self._log_step("workflow_completed", {"status": "success"})
            return final_output
        except Exception as e:
            self._log_step("workflow_error", {"error": str(e)})
            return {
                "success": False,
                "error": f"Erro durante workflow: {e}",
                "workflow_state": self.get_workflow_state(),
                "status": "Erro na geracao da proposta",
            }

    def generate_proposal_with_security(self, user_input: str) -> Dict[str, Any]:
        """Generate proposal and include security findings in response."""
        result = self.generate_proposal(user_input)
        if result.get("success"):
            security = result.get("security_assessment", {})
            critical_findings = [
                finding
                for finding in security.get("findings", [])
                if isinstance(finding, dict) and finding.get("severity") == "critical"
            ]
            if critical_findings:
                result["requires_review"] = True
                result["critical_findings"] = critical_findings
                result["status"] = "Proposta gerada com achados criticos de seguranca"
        return result

    def convert_proposal(self, target_format: str = "word", proposal: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Prepare an existing proposal for conversion into word/pdf."""
        candidate_proposal = proposal if isinstance(proposal, dict) and proposal else self.state.get("generated_proposal")
        if not isinstance(candidate_proposal, dict) or not candidate_proposal:
            return {"success": False, "error": "Nenhuma proposta foi gerada ainda"}

        self._log_step(f"conversion_started_{target_format}")
        try:
            conversion_result = self.conversion_agent.prepare_for_conversion(candidate_proposal, target_format)
            self._log_step(f"conversion_completed_{target_format}")
            return {
                "success": True,
                "format": target_format,
                "conversion_metadata": conversion_result,
                "status": f"Proposta preparada para conversao para {target_format.upper()}",
            }
        except Exception as e:
            self._log_step(f"conversion_error_{target_format}", {"error": str(e)})
            return {
                "success": False,
                "error": str(e),
                "status": f"Erro na conversao para {target_format}",
            }

    def _save_proposal_to_file(self, proposal: Dict[str, Any]) -> str:
        """Save proposal text output into propostas/nimbus-Nome_do_Cliente-timestamp.md."""
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        dirname = os.path.join(base, "propostas")
        os.makedirs(dirname, exist_ok=True)

        metadata = proposal.get("metadata", {}) if isinstance(proposal, dict) else {}
        raw_client = metadata.get("client") or proposal.get("title") or "Cliente"
        normalized_client = unicodedata.normalize("NFKD", str(raw_client))
        normalized_client = normalized_client.encode("ascii", "ignore").decode("ascii")
        normalized_client = re.sub(r"\s+", "_", normalized_client.strip())
        normalized_client = re.sub(r"[^A-Za-z0-9_\-]", "", normalized_client)
        if not normalized_client:
            normalized_client = "Cliente"

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(dirname, f"nimbus-{normalized_client}-{timestamp}.md")

        try:
            with open(filename, "w", encoding="utf-8") as file:
                heading = str(proposal.get("title") or "Proposta Tecnica").strip()
                file.write(f"{heading}\n")
                file.write("=" * 70 + "\n\n")

                if metadata.get("client"):
                    file.write(f"Cliente: {metadata['client']}\n")
                if metadata.get("created"):
                    file.write(f"Data: {metadata['created']}\n")

                file.write("\n")
                for section in proposal.get("sections", []):
                    if isinstance(section, dict):
                        file.write(f"## {section.get('title', 'Sem titulo')}\n\n")
                        file.write(f"{section.get('content', '')}\n\n")
            logger.info("[Orchestrator] Proposta salva em: %s", filename)
        except Exception as e:
            logger.exception("[Orchestrator] Erro ao salvar proposta")

        return filename

    def get_workflow_state(self) -> Dict[str, Any]:
        """Return a lightweight workflow status summary."""
        return {
            "current_step": self.state.get("current_step"),
            "analysis_complete": self.state.get("analysis_result") is not None,
            "proposal_generated": self.state.get("generated_proposal") is not None,
            "security_scanned": self.state.get("security_scan") is not None,
            "history": self.state.get("history", []),
        }

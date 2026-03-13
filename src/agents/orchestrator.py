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
from .conversion_agent import ConversionAgent
from .generation_agent import GenerationAgent
from .questionnaire_agent import QuestionnaireAgent
from .security_agent import SecurityAgent

ORCHESTRATOR_PROMPT = """
You are the Orchestrator Agent that coordinates specialized proposal agents.
Keep workflow state consistent, handle failures gracefully, and provide clear status.
"""

logger = logging.getLogger(__name__)


DEFAULT_REQUIRED_FIELDS: list[tuple[str, str]] = [
    ("clientInfo.companyName", "Nome do cliente"),
    ("clientInfo.contactPerson", "Pessoa de contato"),
    ("clientInfo.contactEmail", "Email de contato"),
    ("clientInfo.contactPhone", "Telefone de contato"),
    ("timeline", "Prazo/timeline do projeto"),
    ("budget", "Orcamento do projeto"),
]

NOTION_REQUIRED_FIELD_HINTS: list[tuple[str, str, tuple[str, ...]]] = [
    (
        "clientInfo.companyName",
        "Nome do cliente",
        ("nome do cliente", "cliente", "razao social", "empresa"),
    ),
    (
        "clientInfo.contactPerson",
        "Pessoa de contato",
        ("pessoa de contato", "contato principal", "responsavel", "stakeholder"),
    ),
    (
        "clientInfo.contactEmail",
        "Email de contato",
        ("email", "e-mail", "correio eletronico"),
    ),
    (
        "clientInfo.contactPhone",
        "Telefone de contato",
        ("telefone", "celular", "whatsapp", "fone"),
    ),
    (
        "timeline",
        "Prazo/timeline do projeto",
        ("timeline", "prazo", "cronograma", "deadline"),
    ),
    (
        "budget",
        "Orcamento do projeto",
        ("orcamento", "budget", "valor", "investimento"),
    ),
    (
        "objetivos",
        "Objetivos do projeto",
        ("objetivo", "metas", "resultado esperado", "escopo"),
    ),
    (
        "clientInfo.segment",
        "Segmento do cliente",
        ("segmento", "setor", "industria", "nicho"),
    ),
]


class OrchestratorAgent:
    """Coordinates analysis, questionnaire, generation, security, and conversion flows."""

    def __init__(self, notion_mcp_client=None):
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.min_call_interval_seconds = float(os.getenv("NIMBUS_MIN_CALL_INTERVAL_SECONDS", "2.5"))
        self.max_rate_limit_retries = int(os.getenv("NIMBUS_RATE_LIMIT_RETRIES", "2"))
        self.base_backoff_seconds = float(os.getenv("NIMBUS_BACKOFF_BASE_SECONDS", "3.0"))
        self.enable_security_scan = os.getenv("NIMBUS_ENABLE_SECURITY_SCAN", "false").lower() == "true"
        self._last_llm_call_at = 0.0

        use_notion_tools = os.getenv("NIMBUS_ENABLE_NOTION_TOOLS", "false").lower() == "true"
        notion_client_for_agents = notion_mcp_client if use_notion_tools else None

        self.analysis_agent = AnalysisAgent(notion_mcp_client=notion_client_for_agents)
        self.questionnaire_agent = QuestionnaireAgent()
        self.generation_agent = GenerationAgent(notion_mcp_client=notion_client_for_agents)
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

    def _field_input_hint(self, field_name: str, description: str = "") -> dict[str, str]:
        """Return expected format and example answer for a missing field."""
        normalized = (field_name or "").strip()
        lowered = normalized.lower()
        lowered_compact = lowered.replace(" ", "").replace("_", "")
        desc_lower = (description or "").lower()

        if normalized == "clientInfo.contactPhone" or lowered.endswith("contactphone"):
            return {
                "expectedFormat": "Telefone em formato internacional ou nacional com DDD",
                "exampleAnswer": "+55 11 99999-9999",
            }
        if normalized == "clientInfo.contactEmail" or lowered.endswith("contactemail"):
            return {
                "expectedFormat": "Email corporativo valido",
                "exampleAnswer": "joao@empresa.com",
            }
        if normalized == "clientInfo.contactPerson" or lowered.endswith("contactperson"):
            return {
                "expectedFormat": "Nome completo do responsavel principal",
                "exampleAnswer": "Joao da Silva",
            }
        if normalized == "timeline":
            return {
                "expectedFormat": "Duracao com unidade de tempo",
                "exampleAnswer": "6 semanas",
            }
        if normalized == "budget":
            return {
                "expectedFormat": "Valor estimado com moeda",
                "exampleAnswer": "R$ 50 mil",
            }
        if lowered_compact == "technicalrequirements":
            return {
                "expectedFormat": "Resumo tecnico com capacidade, SO, dependencias e excecoes",
                "exampleAnswer": (
                    "50 VMs (32 GB RAM, 16 vCPU), Windows Server 2019; "
                    "3 VMs SQL Server 2019; migracao em ondas com janela noturna."
                ),
            }
        if "vm" in lowered or "infraestrutura" in desc_lower or "technical" in desc_lower:
            return {
                "expectedFormat": "Resumo tecnico objetivo com numeros e tecnologias",
                "exampleAnswer": (
                    "50 VMs Windows Server 2019, 32 GB RAM e 16 vCPU; "
                    "3 SQL Server 2019; armazenamento em blocos com backup diario."
                ),
            }
        if "security" in lowered or "compliance" in lowered or "seguranca" in desc_lower:
            return {
                "expectedFormat": "Controles tecnicos e requisitos normativos",
                "exampleAnswer": (
                    "Criptografia em repouso e transito, MFA para administradores, "
                    "CloudTrail com retencao de 12 meses e aderencia a LGPD."
                ),
            }
        return {
            "expectedFormat": "Resposta objetiva e especifica do campo solicitado",
            "exampleAnswer": "Fornecer valor direto, com numeros e contexto quando aplicavel.",
        }

    def _build_questionnaire_from_gaps(self, data_gaps: list[dict[str, Any]]) -> Dict[str, Any]:
        """Generate questionnaire deterministically to avoid an extra model call."""
        questions = []
        for idx, gap in enumerate(data_gaps, start=1):
            field = gap.get("field", f"campo_{idx}") if isinstance(gap, dict) else f"campo_{idx}"
            description = ""
            if isinstance(gap, dict):
                description = str(gap.get("description", "")).strip()
            hint = self._field_input_hint(str(field), description)
            question_text = f"Poderia detalhar o campo '{field}'?"
            if description:
                question_text = f"{question_text} Contexto: {description}"
            example = hint.get("exampleAnswer", "")
            if example:
                question_text = f"{question_text} Exemplo: {example}"
            questions.append(
                {
                    "id": f"q{idx}",
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
        }

    def _extract_required_fields_from_notion_cache(self) -> list[tuple[str, str]]:
        """Infer likely required fields from Notion cache text using keyword hints."""
        cache = self.state.get("notion_cache", {})
        if not isinstance(cache, dict) or not cache:
            return []

        fragments: list[str] = []
        for value in cache.values():
            if isinstance(value, dict):
                title = str(value.get("title", ""))
                text = str(value.get("text", ""))
                fragments.append(f"{title}\n{text}")
            elif isinstance(value, str):
                fragments.append(value)

        text_blob = "\n".join(fragments).lower()
        if not text_blob.strip():
            return []

        detected: list[tuple[str, str]] = []
        for field_path, label, hints in NOTION_REQUIRED_FIELD_HINTS:
            if any(hint in text_blob for hint in hints):
                detected.append((field_path, label))
        return detected

    def _required_fields(self) -> list[tuple[str, str]]:
        """Return baseline + Notion-inferred required fields with stable ordering."""
        merged: list[tuple[str, str]] = []
        seen: set[str] = set()

        for field_path, label in DEFAULT_REQUIRED_FIELDS + self._extract_required_fields_from_notion_cache():
            if field_path in seen:
                continue
            seen.add(field_path)
            merged.append((field_path, label))
        return merged

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

        return merged

    def _normalize_analysis_aliases(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map common top-level aliases to required nested paths."""
        if not isinstance(analysis_data, dict):
            return {}

        normalized = dict(analysis_data)
        alias_map: list[tuple[str, str]] = [
            ("contactPhone", "clientInfo.contactPhone"),
            ("phone", "clientInfo.contactPhone"),
            ("telefone", "clientInfo.contactPhone"),
            ("contactEmail", "clientInfo.contactEmail"),
            ("email", "clientInfo.contactEmail"),
            ("contactPerson", "clientInfo.contactPerson"),
            ("responsavel", "clientInfo.contactPerson"),
            ("companyName", "clientInfo.companyName"),
            ("clientName", "clientInfo.companyName"),
        ]

        for source_key, target_path in alias_map:
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
        """Build required gaps list for interactive questionnaire."""
        gaps: list[dict[str, Any]] = []
        existing = analysis_data.get("dataGaps", []) if isinstance(analysis_data, dict) else []
        existing_fields = set()
        alias_to_required = {
            "contactPhone": "clientInfo.contactPhone",
            "phone": "clientInfo.contactPhone",
            "telefone": "clientInfo.contactPhone",
            "contactEmail": "clientInfo.contactEmail",
            "email": "clientInfo.contactEmail",
            "contactPerson": "clientInfo.contactPerson",
            "responsavel": "clientInfo.contactPerson",
            "companyName": "clientInfo.companyName",
            "clientName": "clientInfo.companyName",
        }
        if isinstance(existing, list):
            for item in existing:
                if isinstance(item, dict) and item.get("field"):
                    field_name = str(item["field"])
                    normalized_field = alias_to_required.get(field_name, field_name)
                    existing_fields.add(normalized_field)

        for field_path, label in self._required_fields():
            value = self._get_nested(analysis_data, field_path)
            missing = value is None or (isinstance(value, str) and not value.strip())
            if missing:
                normalized_field = field_path
                if normalized_field in existing_fields:
                    continue
                gaps.append(
                    {
                        "field": normalized_field,
                        "description": f"{label} é obrigatório para gerar proposta completa.",
                        "required": True,
                        "suggestedQuestions": [f"Informe: {label}"],
                    }
                )

        if isinstance(existing, list):
            for item in existing:
                if isinstance(item, dict):
                    field_name = str(item.get("field", "")).strip()
                    if not field_name:
                        gaps.append(item)
                        continue

                    normalized_field = alias_to_required.get(field_name, field_name)
                    current_value = self._get_nested(analysis_data, normalized_field)
                    if current_value is not None and (not isinstance(current_value, str) or current_value.strip()):
                        continue

                    clone = dict(item)
                    clone["field"] = normalized_field
                    if not any(isinstance(g, dict) and g.get("field") == normalized_field for g in gaps):
                        gaps.append(clone)
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
                    "required_fields_source": "notion+default" if self.state.get("notion_cache") else "default",
                    "questionnaire": questionnaire,
                    "missing_fields": [
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
            generation_context = {
                "analysis": analysis_data,
                "data_gaps": data_gaps,
                "user_input": user_input,
                "questionnaire": self.state.get("questionnaire"),
                "notion_cache": cache_str,
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
                },
            }
            self.state["generated_proposal"] = proposal
            self._log_step(
                "generation_completed",
                {
                    "sections_count": len(proposal_sections),
                    "duration_ms": int((time.perf_counter() - generation_t0) * 1000),
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
                file.write("PROPOSTA TECNICA - MIGRACAO PARA AWS\n")
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

"""
Orchestrator Agent v2 — Coordinates the new proposal generation workflow.

New workflow:
  Analysis → Architecture contract → Security pre-gen → Non-blocking gaps →
  Relevance map → Generation (WriterAgent per section) → Coherence check →
  Selective regen → SCORE evaluation → Final save

Key changes from v1:
- No required_fields concept — gaps are non-blocking
- Architecture contract is the single source of truth
- NotionRelevanceMapper provides per-section Notion content (no truncation)
- CoherenceAgent replaces _post_process_sections
- ScoreEvaluatorAgent replaces ReviewAgent
- FileProposalStore for durable persistence
"""

import json
import logging
import os
import random
import time
import traceback
from datetime import datetime
from typing import Any, Callable, Dict

from strands import Agent
from strands.models import OpenAIModel

from .analysis_agent import AnalysisAgent
from .architecture_agent import ArchitectureAgent
from .coherence_agent import CoherenceAgent
from .conversion_agent import ConversionAgent
from .generation_agent import GenerationAgent
from .notion_relevance_mapper import NotionRelevanceMapper
from .score_evaluator_agent import ScoreEvaluatorAgent
from stores.proposal_store import FileProposalStore

ORCHESTRATOR_PROMPT = """
You are the Orchestrator Agent that coordinates specialized proposal agents.
Keep workflow state consistent, handle failures gracefully, and provide clear status.
"""

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """Coordinates analysis, architecture, generation, coherence, and evaluation flows."""

    def __init__(self, notion_cache_layer=None, aws_mcp_client=None, aws_knowledge_mcp_client=None):
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.min_call_interval_seconds = float(os.getenv("NIMBUS_MIN_CALL_INTERVAL_SECONDS", "2.5"))
        self.max_rate_limit_retries = int(os.getenv("NIMBUS_RATE_LIMIT_RETRIES", "2"))
        self.base_backoff_seconds = float(os.getenv("NIMBUS_BACKOFF_BASE_SECONDS", "3.0"))
        self.review_score_threshold = float(os.getenv("NIMBUS_REVIEW_SCORE_THRESHOLD", "8.0"))
        self.max_coherence_passes = int(os.getenv("NIMBUS_MAX_COHERENCE_PASSES", "2"))
        self.max_score_regeneration = int(os.getenv("NIMBUS_MAX_SCORE_REGENERATION", "1"))
        self._last_llm_call_at = 0.0

        self.notion_cache_layer = notion_cache_layer

        # Agents
        self.analysis_agent = AnalysisAgent()
        self.architecture_agent = ArchitectureAgent(aws_mcp_client=aws_mcp_client, aws_knowledge_mcp_client=aws_knowledge_mcp_client)
        self.relevance_mapper = NotionRelevanceMapper()
        self.generation_agent = GenerationAgent()
        self.coherence_agent = CoherenceAgent()
        self.score_evaluator = ScoreEvaluatorAgent()
        self.conversion_agent = ConversionAgent()

        # Store
        self.store = FileProposalStore()

        self.agent = Agent(
            model=OpenAIModel(
                model_id="gpt-4o",
                params={"temperature": 0.2, "max_tokens": 1024},
            ),
            system_prompt=ORCHESTRATOR_PROMPT,
            tools=[],
            callback_handler=None,
        )

        self.state: Dict[str, Any] = {
            "current_step": "init",
            "analysis_result": None,
            "architecture_contract": None,
            "security_eval": None,
            "generated_proposal": None,
            "coherence_result": None,
            "score_result": None,
            "final_output": None,
            "history": [],
            "notion_cache": {},
        }

    # -------------------------------------------------------------------------
    # Logging / rate-limit helpers
    # -------------------------------------------------------------------------

    def _log_step(self, step: str, data: Any = None) -> None:
        self.state["history"].append({
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "data": data,
        })
        self.state["current_step"] = step
        logger.info("[Orchestrator] %s", step)

    def _throttle_next_call(self) -> None:
        now = time.monotonic()
        wait_for = self.min_call_interval_seconds - (now - self._last_llm_call_at)
        if wait_for > 0:
            time.sleep(wait_for)
        self._last_llm_call_at = time.monotonic()

    def _is_rate_limit_error(self, exc: Exception) -> bool:
        msg = str(exc).lower()
        return "429" in msg or "rate limit" in msg or "too many requests" in msg

    def _run_with_rate_limit_control(self, step_name: str, fn: Callable[..., Any], *args, **kwargs) -> Any:
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
                    "step": step_name, "attempt": attempt, "sleep_seconds": round(sleep_for, 2),
                })
                time.sleep(sleep_for)

    # -------------------------------------------------------------------------
    # Notion cache helpers
    # -------------------------------------------------------------------------

    def _populate_notion_cache_from_layer(self) -> None:
        if self.notion_cache_layer is None:
            return
        if not self.notion_cache_layer.is_ready():
            logger.info("[Orchestrator] Notion cache layer not ready yet — skipping injection.")
            return
        pages = self.notion_cache_layer.get_all_as_dict()
        if pages:
            self.state["notion_cache"].update(pages)
            logger.info("[Orchestrator] Loaded %d pages from Notion cache layer.", len(pages))

    def _build_cache_wait_response(self, reason: str) -> Dict[str, Any]:
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
        if self.notion_cache_layer is None:
            return self._build_cache_wait_response("cache_layer_unavailable")
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

    def _get_template_text_from_notion_cache(self) -> str:
        # Busca o template de proposta pelo page_id fornecido
        TEMPLATE_PAGE_ID = "32c78f568aaf803bb459f32a6d69b97d"
        cache = self.state.get("notion_cache", {})
        if not isinstance(cache, dict) or not cache:
            return ""
        # Busca pelo page_id exato
        page = cache.get(TEMPLATE_PAGE_ID)
        if page and isinstance(page, dict):
            return str(page.get("text", ""))
        # Fallback: busca pelo título
        for value in cache.values():
            if not isinstance(value, dict):
                continue
            title = str(value.get("title", "")).strip().lower()
            if "template" in title and "proposta" in title:
                return str(value.get("text", ""))
        return ""

    def _extract_template_sections(self, template_text: str | None = None) -> list[str]:
        """Extract template section order from top-level markdown headings.
        
        No arbitrary filters — keeps all #/## headings as sections.
        """
        import re
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
            heading = re.match(r"^(#{1,2})\s+(.+)$", line)
            if not heading:
                continue
            candidate = heading.group(2).strip(" -:\t")
            if len(candidate) < 2:
                continue
            key = candidate.lower()
            if key in seen:
                continue
            seen.add(key)
            sections.append(candidate)
        return sections

    def _get_score_page_content(self) -> str:
        """Find the SCORE - Consulting page in the Notion cache."""
        cache = self.state.get("notion_cache", {})
        if not isinstance(cache, dict):
            return ""
        for value in cache.values():
            if not isinstance(value, dict):
                continue
            title = str(value.get("title", "")).strip().lower()
            if "score" in title and "consulting" in title:
                return str(value.get("text", ""))
        return ""

    def _format_notion_cache_summary(self) -> str:
        """Brief summary of Notion cache for analysis context."""
        fragments = []
        for page_id, info in self.state.get("notion_cache", {}).items():
            title = info.get("title", "(no title)") if isinstance(info, dict) else "(invalid)"
            text = info.get("text", "") if isinstance(info, dict) else ""
            fragments.append(f"--- Notion Page: {title} ({page_id}) ---\n{text}\n")
        full = "\n".join(fragments)
        # Provide a reasonable amount for analysis (not the full 6000 truncation)
        if len(full) > 12000:
            return full[:12000] + "\n\n[...remainder omitted for analysis context]"
        return full

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def analyze_requirements(self, input_text: str, input_type: str = "text") -> Dict[str, Any]:
        gate = self._ensure_notion_cache_ready()
        if isinstance(gate, dict):
            return gate
        cache_str = self._format_notion_cache_summary()
        return self.analysis_agent.analyze(input_text, input_type=input_type, notion_cache=cache_str)

    def generate_proposal(self, user_input: str, session_id: str | None = None) -> Dict[str, Any]:
        """Generate a complete proposal using the new multi-agent workflow."""
        if not isinstance(user_input, str) or not user_input.strip():
            return {
                "success": False,
                "error": "user_input must be a non-empty string",
                "workflow_state": self.get_workflow_state(),
                "status": "Erro na geracao da proposta",
            }

        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            self._log_step("workflow_started", {"user_input": user_input[:120], "session_id": session_id})

            # ---- Notion cache gate ----
            gate = self._ensure_notion_cache_ready()
            if isinstance(gate, dict):
                self._log_step("workflow_waiting_cache", gate.get("cache_status"))
                return gate

            notion_cache = self.state.get("notion_cache", {})

            # ---- 1. Analysis ----
            self._log_step("analysis_started")
            t0 = time.perf_counter()
            cache_str = self._format_notion_cache_summary()
            analysis_result = self._run_with_rate_limit_control(
                "analysis",
                self.analysis_agent.analyze,
                user_input,
                input_type="natural_language",
                notion_cache=cache_str,
            )
            if isinstance(analysis_result, dict) and (
                analysis_result.get("status") == "analysis_failed" or analysis_result.get("error")
            ):
                raise RuntimeError(f"analysis_failed: {analysis_result.get('error', 'unknown')}")

            analysis_data = analysis_result.get("analysis", {}) if isinstance(analysis_result, dict) else {}
            if not isinstance(analysis_data, dict):
                analysis_data = {"raw_analysis": str(analysis_data)}

            self.state["analysis_result"] = analysis_result
            self.store.save_analysis(session_id, analysis_result)
            self._log_step("analysis_completed", {"duration_ms": int((time.perf_counter() - t0) * 1000)})

            # ---- 2. Architecture contract ----
            self._log_step("architecture_started")
            t0 = time.perf_counter()
            architecture = self._run_with_rate_limit_control(
                "architecture",
                self.architecture_agent.generate_architecture,
                analysis_data,
                user_input,
                cache_str[:8000],
            )
            if architecture.get("error"):
                raise RuntimeError(f"architecture_failed: {architecture.get('error')}")

            self.state["architecture_contract"] = architecture
            self.store.save_architecture(session_id, architecture)
            self._log_step("architecture_completed", {
                "services": len(architecture.get("services", [])),
                "gaps": len(architecture.get("data_gaps", [])),
                "duration_ms": int((time.perf_counter() - t0) * 1000),
            })

            # ---- 3. Security pre-gen evaluation ----
            self._log_step("security_pregen_started")
            t0 = time.perf_counter()
            security_eval = self._run_with_rate_limit_control(
                "security_pregen",
                self.architecture_agent.evaluate_security,
                architecture,
                user_input,
            )
            self.state["security_eval"] = security_eval

            # Merge security gaps into architecture contract for writer visibility
            security_gaps = security_eval.get("security_gaps", [])
            if isinstance(security_gaps, list):
                all_gaps = architecture.get("data_gaps", []) + security_gaps
                architecture["data_gaps"] = all_gaps

            self.store.append_audit(session_id, "security_pregen", {
                "overall_risk": security_eval.get("overall_risk", "unknown"),
                "findings_count": len(security_eval.get("findings", [])),
            })
            self._log_step("security_pregen_completed", {
                "risk": security_eval.get("overall_risk", "unknown"),
                "duration_ms": int((time.perf_counter() - t0) * 1000),
            })

            # ---- 4. Template extraction ----
            template_text = self._get_template_text_from_notion_cache()
            if not template_text:
                return {
                    "success": False,
                    "status": "Template de proposta nao encontrado no cache do Notion",
                    "error": "template_not_found",
                    "workflow_state": self.get_workflow_state(),
                }

            template_sections = self._extract_template_sections(template_text)
            if not template_sections:
                return {
                    "success": False,
                    "status": "Template do Notion sem seções explícitas",
                    "error": "template_sections_not_found",
                    "workflow_state": self.get_workflow_state(),
                }

            # ---- 5. Relevance mapping ----
            self._log_step("relevance_mapping_started")
            t0 = time.perf_counter()
            raw_relevance_map = self._run_with_rate_limit_control(
                "relevance_mapping",
                self.relevance_mapper.build_relevance_map,
                template_sections,
                notion_cache,
                user_input[:500],
            )
            # Resolve page IDs to full content per section
            relevance_content: Dict[str, str] = {}
            for section in template_sections:
                relevance_content[section] = self.relevance_mapper.get_relevant_content(
                    section, raw_relevance_map, notion_cache,
                )
            self._log_step("relevance_mapping_completed", {
                "duration_ms": int((time.perf_counter() - t0) * 1000),
            })

            # ---- 6. Generation ----
            self._log_step("generation_started")
            t0 = time.perf_counter()
            generation_context = {
                "analysis": analysis_data,
                "user_input": user_input,
                "template_text": template_text,
                "template_sections": template_sections,
            }
            proposal_sections = self._run_with_rate_limit_control(
                "generation",
                self.generation_agent.generate_full_proposal,
                generation_context,
                relevance_content,
                architecture,
            )
            self._log_step("generation_completed", {
                "sections": len(proposal_sections),
                "duration_ms": int((time.perf_counter() - t0) * 1000),
            })

            # ---- 7. Coherence check + selective regen ----
            self._log_step("coherence_check_started")
            for coherence_pass in range(1, self.max_coherence_passes + 1):
                coherence_result = self._run_with_rate_limit_control(
                    f"coherence_pass_{coherence_pass}",
                    self.coherence_agent.check_coherence,
                    proposal_sections,
                    architecture,
                    template_sections,
                )
                self.state["coherence_result"] = coherence_result

                if coherence_result.get("coherent", True):
                    self._log_step("coherence_passed", {"pass": coherence_pass})
                    break

                issues = coherence_result.get("issues", [])
                if not issues:
                    break

                self._log_step("coherence_regen", {"pass": coherence_pass, "issues": len(issues)})

                # Deduplicate issues by section index — consolidate feedback
                regen_by_idx: Dict[int, list] = {}
                for issue in issues:
                    if not isinstance(issue, dict):
                        continue
                    target_title = str(issue.get("section_title", "")).strip()
                    correction = str(issue.get("correction_context", "")).strip()
                    if not target_title or not correction:
                        continue
                    for idx, section in enumerate(proposal_sections):
                        if not isinstance(section, dict):
                            continue
                        if target_title.lower() in str(section.get("title", "")).lower():
                            regen_by_idx.setdefault(idx, []).append(correction)
                            break

                # Regenerate each affected section once with consolidated feedback
                for idx, corrections in regen_by_idx.items():
                    section = proposal_sections[idx]
                    target_title = str(section.get("title", "")).strip()
                    merged_feedback = "\n".join(f"- {c}" for c in corrections)
                    regen_context = dict(generation_context)
                    regen_context["review_feedback"] = merged_feedback
                    new_content = self._run_with_rate_limit_control(
                        "coherence_regen_section",
                        self.generation_agent.writer.generate_section,
                        section_title=target_title,
                        context=regen_context,
                        template_fragment=self.generation_agent._extract_template_fragment(
                            template_text, target_title
                        ),
                        architecture_contract=json.dumps(architecture, ensure_ascii=False, indent=2),
                        relevant_notion_content=relevance_content.get(target_title, ""),
                        existing_sections_summary=self.generation_agent._summarize_existing_sections(
                            proposal_sections
                        ),
                        review_feedback=merged_feedback,
                    )
                    if new_content:
                        proposal_sections[idx]["content"] = str(new_content).strip()

            # ---- 8. SCORE evaluation ----
            self._log_step("score_evaluation_started")
            t0 = time.perf_counter()
            structural = ScoreEvaluatorAgent.validate_structure(proposal_sections, template_sections)

            score_page = self._get_score_page_content()
            score_result = {"score": 0.0, "passed": False, "summary": "SCORE page not found", "issues": []}
            if score_page:
                score_result = self._run_with_rate_limit_control(
                    "score_evaluation",
                    self.score_evaluator.evaluate,
                    proposal_sections,
                    score_page,
                    architecture,
                    template_sections,
                )

            self.state["score_result"] = score_result
            score_val = float(score_result.get("score", 0.0) or 0.0)
            score_passed = bool(score_result.get("passed", False)) and structural.get("valid", False)

            # Selective regen based on SCORE feedback
            regen_done = 0
            if not score_passed:
                score_issues = score_result.get("issues", [])
                # Deduplicate score issues by section index
                score_regen_by_idx: Dict[int, list] = {}
                if isinstance(score_issues, list):
                    for issue in score_issues:
                        if not isinstance(issue, dict):
                            continue
                        if str(issue.get("severity", "")).lower() not in ("critical", "major"):
                            continue
                        target_title = str(issue.get("section_title", "")).strip()
                        guidance = str(issue.get("correction_guidance", "")).strip()
                        if not target_title or not guidance:
                            continue
                        for idx, section in enumerate(proposal_sections):
                            if not isinstance(section, dict):
                                continue
                            if target_title.lower() in str(section.get("title", "")).lower():
                                score_regen_by_idx.setdefault(idx, []).append(guidance)
                                break

                for idx, guidances in score_regen_by_idx.items():
                    if regen_done >= self.max_score_regeneration:
                        break
                    section = proposal_sections[idx]
                    target_title = str(section.get("title", "")).strip()
                    merged_guidance = "\n".join(f"- {g}" for g in guidances)
                    regen_context = dict(generation_context)
                    regen_context["review_feedback"] = merged_guidance
                    new_content = self._run_with_rate_limit_control(
                        "score_regen_section",
                        self.generation_agent.writer.generate_section,
                        section_title=target_title,
                        context=regen_context,
                        template_fragment=self.generation_agent._extract_template_fragment(
                            template_text, target_title
                        ),
                        architecture_contract=json.dumps(architecture, ensure_ascii=False, indent=2),
                        relevant_notion_content=relevance_content.get(target_title, ""),
                        existing_sections_summary=self.generation_agent._summarize_existing_sections(
                            proposal_sections
                        ),
                        review_feedback=merged_guidance,
                    )
                    if new_content:
                        proposal_sections[idx]["content"] = str(new_content).strip()
                        regen_done += 1

            self._log_step("score_evaluation_completed", {
                "score": score_val,
                "passed": score_passed,
                "structural_valid": structural.get("valid", False),
                "regen_done": regen_done,
                "duration_ms": int((time.perf_counter() - t0) * 1000),
            })

            # ---- 9. Assemble and save ----
            self._log_step("finalization_started")
            proposal = {
                "title": analysis_data.get("clientInfo", {}).get("projectName", "Proposta Tecnica")
                    if isinstance(analysis_data.get("clientInfo"), dict)
                    else "Proposta Tecnica",
                "sections": proposal_sections,
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "client": analysis_data.get("clientInfo", {}).get("companyName")
                        if isinstance(analysis_data.get("clientInfo"), dict)
                        else None,
                    "technologies": analysis_data.get("technologies", []),
                    "template_sections": template_sections,
                    "architecture_summary": architecture.get("solution_summary", ""),
                    "security_risk": security_eval.get("overall_risk", "unknown"),
                    "score": score_val,
                    "score_passed": score_passed,
                    "data_gaps": architecture.get("data_gaps", []),
                    "assumptions": architecture.get("assumptions", []),
                },
            }

            self.state["generated_proposal"] = proposal
            output_path = self.store.save_proposal(session_id, proposal)

            self.store.append_audit(session_id, "workflow_completed", {
                "sections_count": len(proposal_sections),
                "score": score_val,
                "score_passed": score_passed,
                "output_file": output_path,
            })

            final_output = {
                "success": True,
                "proposal": proposal,
                "architecture_contract": architecture,
                "security_evaluation": security_eval,
                "coherence": coherence_result,
                "review": {
                    "score": score_val,
                    "passed": score_passed,
                    "structural": structural,
                    "score_result": score_result,
                    "regeneration_attempts": regen_done,
                },
                "data_gaps": architecture.get("data_gaps", []),
                "workflow_state": self.get_workflow_state(),
                "status": "Proposta gerada com sucesso",
                "output_file": output_path,
                "session_id": session_id,
            }
            self.state["final_output"] = final_output
            self._log_step("workflow_completed", {"status": "success", "score": score_val})
            return final_output

        except Exception as e:
            logger.error("[Orchestrator] workflow_error: %s", e)
            traceback.print_exc()
            self._log_step("workflow_error", {"error": str(e)})
            return {
                "success": False,
                "error": f"Erro durante workflow: {e}",
                "workflow_state": self.get_workflow_state(),
                "status": "Erro na geracao da proposta",
                "session_id": session_id,
            }

    def convert_proposal(self, target_format: str = "word", proposal: Dict[str, Any] | None = None) -> Dict[str, Any]:
        candidate = proposal if isinstance(proposal, dict) and proposal else self.state.get("generated_proposal")
        if not isinstance(candidate, dict) or not candidate:
            return {"success": False, "error": "Nenhuma proposta foi gerada ainda"}

        self._log_step(f"conversion_started_{target_format}")
        try:
            result = self.conversion_agent.prepare_for_conversion(candidate, target_format)
            self._log_step(f"conversion_completed_{target_format}")
            return {
                "success": True,
                "format": target_format,
                "conversion_metadata": result,
                "status": f"Proposta preparada para conversao para {target_format.upper()}",
            }
        except Exception as e:
            self._log_step(f"conversion_error_{target_format}", {"error": str(e)})
            return {"success": False, "error": str(e), "status": f"Erro na conversao para {target_format}"}

    def get_workflow_state(self) -> Dict[str, Any]:
        return {
            "current_step": self.state.get("current_step"),
            "analysis_complete": self.state.get("analysis_result") is not None,
            "architecture_complete": self.state.get("architecture_contract") is not None,
            "proposal_generated": self.state.get("generated_proposal") is not None,
            "coherence_checked": self.state.get("coherence_result") is not None,
            "score_evaluated": self.state.get("score_result") is not None,
            "history": self.state.get("history", []),
        }

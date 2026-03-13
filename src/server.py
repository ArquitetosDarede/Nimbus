"""
Propostas MCP Server

Exposes proposal generation agents through MCP protocol via OrchestratorAgent.
The orchestrator coordinates all specialized agents and exposes their functionality.
"""

import asyncio
import json
import logging
import os
import re
from typing import Any, List
from datetime import datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from agents.orchestrator import OrchestratorAgent
from agents.interaction_agent import InteractionAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nimbus")

# Initialize Notion MCP Client for agents
try:
    from tools.notion_strands_tools import create_notion_mcp_client
    logger.info("Creating Notion MCP client for orchestrator...")
    notion_mcp_client = create_notion_mcp_client()
    logger.info("✅ Notion MCP client created successfully")
except Exception as e:
    logger.error(f"❌ Failed to create Notion MCP client: {e}")
    logger.info("Orchestrator will run without Notion integration")
    notion_mcp_client = None

# Initialize the Orchestrator Agent with all specialized sub-agents
try:
    logger.info("Initializing OrchestratorAgent with specialized sub-agents...")
    orchestrator = OrchestratorAgent(notion_mcp_client=notion_mcp_client)
    logger.info("✅ OrchestratorAgent initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize OrchestratorAgent: {e}")
    raise

try:
    logger.info("Initializing InteractionAgent for natural-language questionnaire answers...")
    interaction_agent = InteractionAgent()
    logger.info("✅ InteractionAgent initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize InteractionAgent: {e}")
    raise

# Session storage
sessions = {}
proposals = {}

STRICT_HUMAN_LOOP = os.getenv("NIMBUS_STRICT_HUMAN_LOOP", "true").lower() == "true"

FIELD_ALIAS_MAP = {
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

# Create MCP server
app = Server("nimbus")


def _normalize_field_name(field_name: str) -> str:
    if not isinstance(field_name, str):
        return ""
    trimmed = field_name.strip()
    return FIELD_ALIAS_MAP.get(trimmed, trimmed)


def _normalized_field_set(values: list[Any] | None) -> set[str]:
    out: set[str] = set()
    for item in values or []:
        if isinstance(item, str):
            normalized = _normalize_field_name(item)
            if normalized:
                out.add(normalized)
    return out


def _session_open_required_fields(session: dict[str, Any]) -> set[str]:
    values = session.get("required_fields_open", [])
    return _normalized_field_set(values if isinstance(values, list) else [])


def _session_user_provided_fields(session: dict[str, Any]) -> set[str]:
    values = session.get("user_provided_fields", [])
    return _normalized_field_set(values if isinstance(values, list) else [])


def _append_audit(session: dict[str, Any], event: str, data: dict[str, Any]) -> None:
    audit = session.get("audit", [])
    if not isinstance(audit, list):
        audit = []
    audit.append({
        "timestamp": datetime.now().isoformat(),
        "event": event,
        "data": data,
    })
    session["audit"] = audit


def _build_questionnaire_message(result: dict[str, Any]) -> str:
    """Create a human-friendly follow-up message for pending required fields."""
    missing = result.get("missing_fields", []) if isinstance(result, dict) else []
    questionnaire = result.get("questionnaire", {}) if isinstance(result, dict) else {}
    questions = questionnaire.get("questions", []) if isinstance(questionnaire, dict) else []
    input_examples = result.get("input_examples", {}) if isinstance(result, dict) else {}

    def friendly_label(field_name: str) -> str:
        mapping = {
            "clientInfo.companyName": "nome do cliente",
            "clientInfo.contactPerson": "nome da pessoa de contato",
            "clientInfo.contactEmail": "email de contato do cliente",
            "clientInfo.contactPhone": "telefone de contato do cliente",
            "timeline": "prazo do projeto",
            "budget": "orcamento estimado do projeto",
            "Technical Requirements": "requisitos tecnicos",
        }
        return mapping.get(field_name, field_name)

    header = "Preciso de algumas informacoes obrigatorias para continuar a proposta."
    if not questions:
        if missing:
            if len(missing) == 1 and isinstance(missing[0], str):
                field = missing[0]
                ex = ""
                if isinstance(input_examples, dict) and isinstance(input_examples.get(field), dict):
                    ex = str(input_examples[field].get("exampleAnswer", "")).strip()
                line = f"Poderia detalhar o {friendly_label(field)}?"
                if ex:
                    line = f"{line} Exemplo: {ex}"
                return f"{header} {line}"
            listed = ", ".join(friendly_label(str(item)) for item in missing)
            return f"{header} Campos pendentes: {listed}."
        return header

    segments = [header]
    if len(questions) == 1 and isinstance(questions[0], dict):
        q = questions[0]
        text = str(q.get("text", "")).strip()
        field = _extract_field_from_question_text(text)
        if field:
            ex = str(q.get("exampleAnswer", "")).strip()
            line = f"Poderia detalhar o {friendly_label(field)}?"
            if ex:
                line = f"{line} Exemplo: {ex}"
            segments.append(line)
        elif text:
            segments.append(text)
    else:
        for q in questions[:8]:
            if isinstance(q, dict) and q.get("text"):
                clean_text = str(q.get("text", "")).replace("\n", " ").strip()
                clean_text = clean_text.lstrip("- ").strip()
                if clean_text:
                    segments.append(clean_text)
    segments.append("Responda em linguagem natural; eu extraio os campos automaticamente.")
    return " ".join(seg for seg in segments if seg).strip()


def _extract_field_from_question_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    match = re.search(r"campo\s+'([^']+)'", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def _filter_questionnaire_to_unresolved(questionnaire: dict[str, Any], unresolved_fields: list[str]) -> dict[str, Any]:
    if not isinstance(questionnaire, dict):
        return questionnaire
    unresolved_set = _normalized_field_set(unresolved_fields)
    if not unresolved_set:
        return questionnaire

    questions = questionnaire.get("questions", [])
    if not isinstance(questions, list):
        return questionnaire

    filtered = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        field_name = ""
        if isinstance(q.get("field"), str):
            field_name = q.get("field", "")
        elif isinstance(q.get("text"), str):
            field_name = _extract_field_from_question_text(q.get("text", ""))
        normalized = _normalize_field_name(field_name)
        if normalized and normalized in unresolved_set:
            filtered.append(q)

    clone = dict(questionnaire)
    if filtered:
        clone["questions"] = filtered
        clone["estimatedTime"] = max(5, len(filtered) * 2)
    return clone


def _build_partial_followup_message(parsed_result: dict[str, Any], unresolved_fields: list[str]) -> str:
    answers = parsed_result.get("answers", {}) if isinstance(parsed_result, dict) else {}
    resolved_fields = [k for k in answers.keys()] if isinstance(answers, dict) else []

    lines: list[str] = []
    if resolved_fields:
        pretty = ", ".join(resolved_fields)
        lines.append(f"Perfeito, já entendi: {pretty}.")

    if unresolved_fields:
        listed = ", ".join(unresolved_fields)
        lines.append(f"Agora falta apenas: {listed}.")
        lines.append("Pode responder só esse complemento em linguagem natural.")
    else:
        lines.append("Recebi os dados pendentes desta etapa.")

    return " ".join(lines).strip()


def _build_general_assistant_message(tool_name: str, payload: dict[str, Any]) -> str:
    """Create a concise human-facing summary for any Nimbus tool response."""
    status = str(payload.get("status", "")).strip()
    success = bool(payload.get("success"))
    requires_input = bool(payload.get("requires_input"))

    if requires_input:
        return _build_questionnaire_message(payload)

    if tool_name == "generate_proposal":
        if success:
            output_file = payload.get("output_file")
            if output_file:
                return f"Proposta gerada com sucesso. Arquivo salvo em: {output_file}."
            return "Proposta gerada com sucesso."
        return status or "Nao consegui gerar a proposta nesta tentativa."

    if tool_name == "answer_questionnaire":
        if success:
            return "Perfeito, consegui aplicar suas respostas e concluir a proposta."
        return status or "Ainda faltam informacoes para concluir."

    if tool_name == "analyze_requirements":
        return "Analise concluida. Posso seguir para gerar a proposta quando voce confirmar."

    if tool_name == "scan_security":
        risk = payload.get("overallRisk") or payload.get("risk") or "desconhecido"
        return f"Varredura de seguranca concluida. Nivel de risco: {risk}."

    if tool_name == "prepare_conversion":
        fmt = payload.get("format", "arquivo")
        return f"Preparacao de conversao concluida para {fmt}."

    if tool_name == "get_workflow_status":
        step = payload.get("current_step", "desconhecido")
        return f"Status atual do workflow: {step}."

    return status or "Operacao concluida."


def _strict_guard_block_message(session_id: str, missing_fields: list[Any]) -> dict[str, Any]:
    return {
        "success": False,
        "requires_input": True,
        "status": "Fluxo bloqueado por politica de interacao humana obrigatoria",
        "missing_fields": missing_fields,
        "session_id": session_id,
        "assistant_message": (
            "Para esta sessao, so posso avancar com resposta natural do usuario via continue_interaction "
            "ou answer_questionnaire.answer_text."
        ),
        "policy": {
            "strict_human_loop": True,
            "reason": "pending_required_fields_must_come_from_user_message",
        },
    }


def _latest_pending_session_id() -> str | None:
    """Return the latest session id that is waiting for user input."""
    latest_id = None
    latest_ts = ""
    for sid, data in sessions.items():
        if not isinstance(data, dict):
            continue
        if not bool(data.get("requires_input")):
            continue
        created = str(data.get("created_at", ""))
        if created >= latest_ts:
            latest_ts = created
            latest_id = sid
    return latest_id


def _compact_chat_payload(payload: dict[str, Any], session_id: str | None = None) -> dict[str, Any]:
    """Return a concise chat-friendly payload instead of full workflow JSON."""
    compact: dict[str, Any] = {
        "success": bool(payload.get("success")),
        "requires_input": bool(payload.get("requires_input")),
        "status": payload.get("status", ""),
        "assistant_message": payload.get("assistant_message", ""),
    }
    if session_id:
        compact["session_id"] = session_id

    if payload.get("requires_input"):
        if isinstance(payload.get("missing_fields"), list):
            compact["missing_fields"] = payload.get("missing_fields", [])
        if isinstance(payload.get("input_examples"), dict):
            compact["input_examples"] = payload.get("input_examples", {})
        if isinstance(payload.get("questionnaire"), dict):
            q = payload.get("questionnaire", {})
            questions = q.get("questions", []) if isinstance(q.get("questions"), list) else []
            compact["questions"] = [
                {
                    "id": item.get("id"),
                    "text": item.get("text"),
                    "expectedFormat": item.get("expectedFormat"),
                    "exampleAnswer": item.get("exampleAnswer"),
                }
                for item in questions
                if isinstance(item, dict)
            ]

    if payload.get("success"):
        if payload.get("output_file"):
            compact["output_file"] = payload.get("output_file")
        if payload.get("proposal_id"):
            compact["proposal_id"] = payload.get("proposal_id")

    # Keep parsing info minimal and only when present.
    if isinstance(payload.get("answer_parsing"), dict):
        parsed = payload.get("answer_parsing", {})
        compact["answer_parsing"] = {
            "status": parsed.get("status"),
            "confidence": parsed.get("confidence"),
            "notes": parsed.get("notes", []),
        }

    return compact


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available proposal generation tools via orchestrator"""
    return [
        Tool(
            name="generate_proposal",
            description="Generate a complete technical architecture proposal with analysis, questionnaire, generation, and security scan - all orchestrated",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_input": {
                        "type": "string",
                        "description": "Natural language request for proposal generation"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID for tracking"
                    }
                },
                "required": ["user_input"]
            }
        ),
        Tool(
            name="analyze_requirements",
            description="Analyze client input and extract requirements (via orchestrator's analysis sub-agent)",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_text": {
                        "type": "string",
                        "description": "Client input text to analyze"
                    },
                    "input_type": {
                        "type": "string",
                        "description": "Type of input: text, transcript, email",
                        "default": "text"
                    }
                },
                "required": ["input_text"]
            }
        ),
        Tool(
            name="scan_security",
            description="Scan an existing proposal for security vulnerabilities and compliance issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "proposal": {
                        "type": "object",
                        "description": "Proposal to scan for security issues"
                    }
                },
                "required": ["proposal"]
            }
        ),
        Tool(
            name="prepare_conversion",
            description="Prepare existing proposal for format conversion (Word/PDF)",
            inputSchema={
                "type": "object",
                "properties": {
                    "proposal": {
                        "type": "object",
                        "description": "Proposal to prepare for conversion"
                    },
                    "target_format": {
                        "type": "string",
                        "description": "Target format: word or pdf"
                    }
                },
                "required": ["proposal", "target_format"]
            }
        ),
        Tool(
            name="get_workflow_status",
            description="Get the current workflow status",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="answer_questionnaire",
            description="Continue proposal generation from natural-language user answers (human <> nimbus)",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID returned by generate_proposal"
                    },
                    "answer_text": {
                        "type": "string",
                        "description": "Natural-language user answer with one or more missing fields"
                    },
                    "answers": {
                        "type": "object",
                        "description": "Optional pre-structured answers (kept for backward compatibility)"
                    }
                },
                "required": ["session_id"],
                "anyOf": [
                    {"required": ["answer_text"]},
                    {"required": ["answers"]}
                ]
            }
        ),
        Tool(
            name="continue_interaction",
            description="Unified conversational continuation point for any pending Nimbus interaction (human <> nimbus)",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID returned by generate_proposal"
                    },
                    "user_message": {
                        "type": "string",
                        "description": "Natural-language user message to continue the session"
                    }
                },
                "required": ["session_id", "user_message"]
            }
        ),
        Tool(
            name="nimbus_chat",
            description="Single entrypoint for Nimbus messages: auto-routes to new proposal or pending interaction without assistant-side interpretation",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "User message, typically starting with 'Nimbus ...'"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional explicit session id; if omitted, server uses latest pending session or creates a new one"
                    }
                },
                "required": ["message"]
            }
        )
    ]



@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls via OrchestratorAgent"""
    try:
        if name == "generate_proposal":
            user_input = arguments["user_input"]
            session_id = arguments.get("session_id", f"session_{datetime.now().timestamp()}")

            if STRICT_HUMAN_LOOP and session_id in sessions:
                prev = sessions[session_id]
                if bool(prev.get("requires_input")):
                    missing_fields = prev.get("result", {}).get("missing_fields", []) if isinstance(prev.get("result"), dict) else []
                    blocked = _strict_guard_block_message(session_id, missing_fields)
                    _append_audit(prev, "blocked_generate_during_pending", {"missing_fields": missing_fields})
                    return [TextContent(type="text", text=json.dumps(blocked, indent=2, ensure_ascii=False, default=str))]
            
            logger.info(f"[Orchestrator] Starting proposal generation: {session_id}")
            
            # Delegate to orchestrator - it handles the entire workflow
            result = await asyncio.to_thread(
                orchestrator.generate_proposal,
                user_input
            )

            if result.get("requires_input"):
                result["assistant_message"] = _build_questionnaire_message(result)
            else:
                result["assistant_message"] = _build_general_assistant_message("generate_proposal", result)
            
            # Store in session
            sessions[session_id] = {
                "session_id": session_id,
                "user_input": user_input,
                "result": result,
                "status": result.get("status"),
                "requires_input": bool(result.get("requires_input")),
                "last_tool": "generate_proposal",
                "collected_answers": {},
                "required_fields_open": sorted(_normalized_field_set(result.get("missing_fields", []))),
                "user_provided_fields": [],
                "strict_human_loop": STRICT_HUMAN_LOOP,
                "audit": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "event": "session_created",
                        "data": {
                            "source": "user_input",
                            "requires_input": bool(result.get("requires_input")),
                            "missing_fields": result.get("missing_fields", []),
                        },
                    }
                ],
                "created_at": datetime.now().isoformat()
            }
            
            # Store proposal if generated
            if result.get("success") and result.get("proposal"):
                proposal_id = f"proposal_{datetime.now().timestamp()}"
                proposals[proposal_id] = result["proposal"]
                result["proposal_id"] = proposal_id
            
            logger.info(f"[Orchestrator] Proposal generation completed: {result.get('status')}")
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False, default=str)
            )]

        elif name == "answer_questionnaire":
            session_id = arguments["session_id"]
            answer_text = arguments.get("answer_text", "")
            answers = arguments.get("answers", {})

            if session_id not in sessions:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": f"Sessão não encontrada: {session_id}",
                    }, ensure_ascii=False)
                )]

            user_input = sessions[session_id].get("user_input")
            if not isinstance(user_input, str) or not user_input.strip():
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": "Sessão inválida: user_input ausente",
                    }, ensure_ascii=False)
                )]

            logger.info(f"[Orchestrator] Continuing proposal generation with answers: {session_id}")
            strict_session = bool(sessions[session_id].get("strict_human_loop", STRICT_HUMAN_LOOP))

            previous_result = sessions[session_id].get("result", {})
            missing_fields = previous_result.get("missing_fields", []) if isinstance(previous_result, dict) else []
            questionnaire = previous_result.get("questionnaire", {}) if isinstance(previous_result, dict) else {}

            if strict_session and (not isinstance(answer_text, str) or not answer_text.strip()):
                blocked = _strict_guard_block_message(session_id, missing_fields)
                _append_audit(sessions[session_id], "blocked_non_natural_answer", {"tool": "answer_questionnaire"})
                return [TextContent(type="text", text=json.dumps(blocked, indent=2, ensure_ascii=False, default=str))]

            parsed_result = {
                "answers": {},
                "unresolved_fields": missing_fields,
                "status": "skipped",
            }
            if isinstance(answer_text, str) and answer_text.strip():
                parsed_result = await asyncio.to_thread(
                    interaction_agent.extract_answers,
                    answer_text,
                    missing_fields,
                    questionnaire,
                )

            merged_answers = {}
            parsed_answers = parsed_result.get("answers", {}) if isinstance(parsed_result, dict) else {}
            if isinstance(parsed_answers, dict):
                merged_answers.update(parsed_answers)
            if isinstance(answers, dict) and not strict_session:
                merged_answers.update(answers)

            if not merged_answers:
                unresolved = parsed_result.get("unresolved_fields", missing_fields) if isinstance(parsed_result, dict) else missing_fields
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "requires_input": True,
                        "status": "Resposta recebida, mas sem dados extraíveis para os campos pendentes",
                        "missing_fields": unresolved,
                        "assistant_message": "Nao consegui extrair os campos pendentes da sua resposta. Pode responder novamente em linguagem natural com os dados solicitados?",
                        "answer_parsing": parsed_result,
                    }, indent=2, ensure_ascii=False, default=str)
                )]

            cumulative_answers = sessions[session_id].get("collected_answers", {})
            if not isinstance(cumulative_answers, dict):
                cumulative_answers = {}
            cumulative_answers.update(merged_answers)
            sessions[session_id]["collected_answers"] = cumulative_answers

            result = await asyncio.to_thread(
                orchestrator.generate_proposal,
                user_input,
                cumulative_answers,
            )

            result["answer_parsing"] = parsed_result
            result["applied_answers"] = merged_answers

            provided_fields_now = _normalized_field_set(list(merged_answers.keys()))
            user_fields = _session_user_provided_fields(sessions[session_id])
            user_fields.update(provided_fields_now)
            sessions[session_id]["user_provided_fields"] = sorted(user_fields)

            open_fields = _session_open_required_fields(sessions[session_id])
            open_fields.update(_normalized_field_set(result.get("missing_fields", [])))
            open_fields.difference_update(provided_fields_now)
            sessions[session_id]["required_fields_open"] = sorted(open_fields)

            _append_audit(
                sessions[session_id],
                "user_answer_applied",
                {
                    "tool": "answer_questionnaire",
                    "provided_fields": sorted(provided_fields_now),
                    "remaining_fields": sorted(open_fields),
                    "source": "user_message",
                },
            )

            if strict_session and result.get("success") and open_fields:
                result = _strict_guard_block_message(session_id, sorted(open_fields))
                _append_audit(
                    sessions[session_id],
                    "blocked_finalize_open_required_fields",
                    {"remaining_fields": sorted(open_fields)},
                )

            unresolved = parsed_result.get("unresolved_fields", []) if isinstance(parsed_result, dict) else []
            if unresolved:
                unresolved_norm = sorted(_normalized_field_set(unresolved))
                result["missing_fields"] = unresolved_norm
                if isinstance(result.get("questionnaire"), dict):
                    result["questionnaire"] = _filter_questionnaire_to_unresolved(result["questionnaire"], unresolved_norm)
                result["assistant_message"] = _build_partial_followup_message(parsed_result, unresolved_norm)
            elif result.get("requires_input"):
                result["assistant_message"] = _build_partial_followup_message(parsed_result, result.get("missing_fields", []))

            if result.get("requires_input"):
                result.setdefault("assistant_message", _build_questionnaire_message(result))
            else:
                result["assistant_message"] = _build_general_assistant_message("answer_questionnaire", result)

            sessions[session_id]["result"] = result
            sessions[session_id]["status"] = result.get("status")
            sessions[session_id]["requires_input"] = bool(result.get("requires_input"))
            sessions[session_id]["last_tool"] = "answer_questionnaire"

            if result.get("success") and result.get("proposal"):
                proposal_id = f"proposal_{datetime.now().timestamp()}"
                proposals[proposal_id] = result["proposal"]
                result["proposal_id"] = proposal_id

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False, default=str)
            )]
        
        elif name == "analyze_requirements":
            input_text = arguments["input_text"]
            input_type = arguments.get("input_type", "text")
            
            logger.info("[Orchestrator] Analyzing requirements via analysis sub-agent")
            
            # Use orchestrator's analysis agent directly
            result = await asyncio.to_thread(
                orchestrator.analysis_agent.analyze,
                input_text,
                input_type
            )
            if isinstance(result, dict):
                result["assistant_message"] = _build_general_assistant_message("analyze_requirements", result)
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False, default=str)
            )]
        
        elif name == "scan_security":
            proposal = arguments["proposal"]
            
            logger.info("[Orchestrator] Scanning security via security sub-agent")
            
            # Use orchestrator's security agent directly
            scan_result = await asyncio.to_thread(
                orchestrator.security_agent.scan_proposal,
                proposal
            )
            if isinstance(scan_result, dict):
                scan_result["assistant_message"] = _build_general_assistant_message("scan_security", scan_result)
            
            return [TextContent(
                type="text",
                text=json.dumps(scan_result, indent=2, ensure_ascii=False, default=str)
            )]
        
        elif name == "prepare_conversion":
            proposal = arguments["proposal"]
            target_format = arguments["target_format"]
            
            logger.info(f"[Orchestrator] Preparing conversion to {target_format}")
            
            # Use orchestrator's conversion agent directly
            conversion_result = await asyncio.to_thread(
                orchestrator.convert_proposal,
                target_format,
                proposal,
            )
            if isinstance(conversion_result, dict):
                conversion_result["assistant_message"] = _build_general_assistant_message("prepare_conversion", conversion_result)
            
            return [TextContent(
                type="text",
                text=json.dumps(conversion_result, indent=2, ensure_ascii=False, default=str)
            )]
        
        elif name == "get_workflow_status":
            logger.info("[Orchestrator] Fetching workflow status")
            
            status = orchestrator.get_workflow_state()
            if isinstance(status, dict):
                status["assistant_message"] = _build_general_assistant_message("get_workflow_status", status)
            
            return [TextContent(
                type="text",
                text=json.dumps(status, indent=2, ensure_ascii=False, default=str)
            )]

        elif name == "continue_interaction":
            session_id = arguments["session_id"]
            user_message = arguments["user_message"]

            if session_id not in sessions:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": f"Sessao nao encontrada: {session_id}",
                        "assistant_message": "Nao encontrei essa sessao. Pode iniciar novamente com generate_proposal.",
                    }, ensure_ascii=False)
                )]

            if not isinstance(user_message, str) or not user_message.strip():
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "assistant_message": "Recebi sua mensagem vazia. Pode responder com os dados em linguagem natural?",
                    }, ensure_ascii=False)
                )]

            previous = sessions[session_id].get("result", {})
            requires_input = bool(previous.get("requires_input")) if isinstance(previous, dict) else False

            if requires_input:
                missing_fields = previous.get("missing_fields", []) if isinstance(previous, dict) else []
                questionnaire = previous.get("questionnaire", {}) if isinstance(previous, dict) else {}
                parsed_result = await asyncio.to_thread(
                    interaction_agent.extract_answers,
                    user_message,
                    missing_fields,
                    questionnaire,
                )
                parsed_answers = parsed_result.get("answers", {}) if isinstance(parsed_result, dict) else {}

                if not isinstance(parsed_answers, dict) or not parsed_answers:
                    response = {
                        "success": False,
                        "requires_input": True,
                        "status": "Resposta recebida, mas sem dados extraiveis para os campos pendentes",
                        "missing_fields": parsed_result.get("unresolved_fields", missing_fields) if isinstance(parsed_result, dict) else missing_fields,
                        "answer_parsing": parsed_result,
                        "assistant_message": "Nao consegui extrair os campos pendentes da sua resposta. Pode responder novamente com os dados solicitados?",
                    }
                    sessions[session_id]["result"] = response
                    sessions[session_id]["status"] = response.get("status")
                    sessions[session_id]["requires_input"] = True
                    sessions[session_id]["last_tool"] = "continue_interaction"
                    _append_audit(sessions[session_id], "user_answer_not_extracted", {"missing_fields": missing_fields})
                    return [TextContent(type="text", text=json.dumps(response, indent=2, ensure_ascii=False, default=str))]

                user_input = sessions[session_id].get("user_input")
                cumulative_answers = sessions[session_id].get("collected_answers", {})
                if not isinstance(cumulative_answers, dict):
                    cumulative_answers = {}
                cumulative_answers.update(parsed_answers)
                sessions[session_id]["collected_answers"] = cumulative_answers

                result = await asyncio.to_thread(
                    orchestrator.generate_proposal,
                    user_input,
                    cumulative_answers,
                )
                result["answer_parsing"] = parsed_result
                result["applied_answers"] = parsed_answers

                provided_fields_now = _normalized_field_set(list(parsed_answers.keys()))
                user_fields = _session_user_provided_fields(sessions[session_id])
                user_fields.update(provided_fields_now)
                sessions[session_id]["user_provided_fields"] = sorted(user_fields)

                open_fields = _session_open_required_fields(sessions[session_id])
                open_fields.update(_normalized_field_set(result.get("missing_fields", [])))
                open_fields.difference_update(provided_fields_now)
                sessions[session_id]["required_fields_open"] = sorted(open_fields)

                _append_audit(
                    sessions[session_id],
                    "user_answer_applied",
                    {
                        "tool": "continue_interaction",
                        "provided_fields": sorted(provided_fields_now),
                        "remaining_fields": sorted(open_fields),
                        "source": "user_message",
                    },
                )

                strict_session = bool(sessions[session_id].get("strict_human_loop", STRICT_HUMAN_LOOP))
                if strict_session and result.get("success") and open_fields:
                    result = _strict_guard_block_message(session_id, sorted(open_fields))
                    _append_audit(
                        sessions[session_id],
                        "blocked_finalize_open_required_fields",
                        {"remaining_fields": sorted(open_fields)},
                    )

                unresolved = parsed_result.get("unresolved_fields", []) if isinstance(parsed_result, dict) else []
                if unresolved:
                    unresolved_norm = sorted(_normalized_field_set(unresolved))
                    result["missing_fields"] = unresolved_norm
                    if isinstance(result.get("questionnaire"), dict):
                        result["questionnaire"] = _filter_questionnaire_to_unresolved(result["questionnaire"], unresolved_norm)
                    result["assistant_message"] = _build_partial_followup_message(parsed_result, unresolved_norm)
                elif result.get("requires_input"):
                    result["assistant_message"] = _build_partial_followup_message(parsed_result, result.get("missing_fields", []))

                if result.get("requires_input"):
                    result.setdefault("assistant_message", _build_questionnaire_message(result))
                else:
                    result["assistant_message"] = _build_general_assistant_message("answer_questionnaire", result)

                sessions[session_id]["result"] = result
                sessions[session_id]["status"] = result.get("status")
                sessions[session_id]["requires_input"] = bool(result.get("requires_input"))
                sessions[session_id]["last_tool"] = "continue_interaction"
                return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False, default=str))]

            response = {
                "success": True,
                "status": "Sessao sem pendencias de perguntas",
                "assistant_message": "No momento nao ha perguntas pendentes nesta sessao. Se quiser, eu inicio uma nova proposta.",
            }
            sessions[session_id]["last_tool"] = "continue_interaction"
            return [TextContent(type="text", text=json.dumps(response, indent=2, ensure_ascii=False, default=str))]

        elif name == "nimbus_chat":
            raw_message = arguments["message"]
            explicit_session_id = arguments.get("session_id")

            if not isinstance(raw_message, str) or not raw_message.strip():
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "assistant_message": "Mensagem vazia. Envie uma mensagem iniciando com 'Nimbus ...'.",
                    }, ensure_ascii=False)
                )]

            # Strip invocation prefix if present, but keep full text when not present.
            msg = raw_message.strip()
            lowered = msg.lower()
            if lowered.startswith("nimbus"):
                msg = msg[6:].lstrip(" :,-") or raw_message.strip()

            target_session_id = explicit_session_id if isinstance(explicit_session_id, str) and explicit_session_id.strip() else None
            if not target_session_id:
                target_session_id = _latest_pending_session_id()

            if target_session_id and target_session_id in sessions and bool(sessions[target_session_id].get("requires_input")):
                # Route as continuation of pending human<>nimbus dialogue.
                nested_args = {"session_id": target_session_id, "user_message": msg}
                nested_response = await call_tool("continue_interaction", nested_args)
                try:
                    if nested_response and isinstance(nested_response[0], TextContent):
                        raw = json.loads(nested_response[0].text)
                        compact = _compact_chat_payload(raw if isinstance(raw, dict) else {}, target_session_id)
                        text = str(compact.get("assistant_message", "")).strip() or str(compact.get("status", "")).strip()
                        if not text:
                            text = "Resposta recebida."
                        return [TextContent(type="text", text=text)]
                except Exception:
                    pass
                return nested_response

            # No pending session: start a new proposal generation using this message.
            new_session_id = explicit_session_id if isinstance(explicit_session_id, str) and explicit_session_id.strip() else f"session_{datetime.now().timestamp()}"
            nested_args = {"session_id": new_session_id, "user_input": msg}
            nested_response = await call_tool("generate_proposal", nested_args)
            try:
                if nested_response and isinstance(nested_response[0], TextContent):
                    raw = json.loads(nested_response[0].text)
                    compact = _compact_chat_payload(raw if isinstance(raw, dict) else {}, new_session_id)
                    text = str(compact.get("assistant_message", "")).strip() or str(compact.get("status", "")).strip()
                    if not text:
                        text = "Resposta recebida."
                    return [TextContent(type="text", text=text)]
            except Exception:
                pass
            return nested_response
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"[Orchestrator] Error calling tool {name}: {e}")
        import traceback
        traceback.print_exc()
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "assistant_message": "Ocorreu um erro ao processar sua solicitacao. Pode tentar novamente em linguagem natural?",
            }, ensure_ascii=False)
        )]


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

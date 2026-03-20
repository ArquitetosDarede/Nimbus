"""
Nimbus

Exposes proposal generation agents through MCP protocol via OrchestratorAgent v2.
The orchestrator coordinates all specialized agents and exposes their functionality.
"""

import asyncio
import json
import logging
import os
import re
from typing import Any, List
from datetime import datetime
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from agents.orchestrator_v2 import OrchestratorAgent
from agents.interaction_agent import InteractionAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nimbus")

# Initialize optional AWS Documentation MCP Client
aws_mcp_client = None
try:
    from tools.aws_docs_mcp_client import create_aws_docs_mcp_client
    logger.info("Creating AWS Documentation MCP client...")
    aws_mcp_client = create_aws_docs_mcp_client()
    if aws_mcp_client:
        logger.info("✅ AWS Documentation MCP client created successfully")
    else:
        logger.info("ℹ️ AWS Documentation MCP client not available (npx not found or server not installed)")
except Exception as e:
    logger.warning(f"⚠️ Failed to create AWS Documentation MCP client: {e}")

# Initialize the Notion Cache Layer (local SQLite mirror of the entire workspace)
notion_cache_layer = None
try:
    from tools.notion_cache_layer import get_notion_cache_layer
    logger.info("Initialising Notion cache layer...")
    notion_cache_layer = get_notion_cache_layer()
    notion_cache_layer.start_sync_if_needed()
    logger.info("✅ Notion cache layer ready (sync running in background if needed)")
except Exception as e:
    logger.error(f"❌ Failed to initialise Notion cache layer: {e}")

# Initialize the Orchestrator Agent with new v2 architecture
try:
    logger.info("Initializing OrchestratorAgent v2 with specialized sub-agents...")
    orchestrator = OrchestratorAgent(
        notion_cache_layer=notion_cache_layer,
        aws_mcp_client=aws_mcp_client,
    )
    logger.info("✅ OrchestratorAgent v2 initialized successfully")
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

AUDIT_LOG_PATH = os.getenv("NIMBUS_AUDIT_LOG_PATH", ".nimbus_audit/chat_audit.jsonl")

# Create MCP server
app = Server("nimbus")


def _normalize_field_name(field_name: str) -> str:
    if not isinstance(field_name, str):
        return ""
    return field_name.strip()


def _friendly_label(field_name: str) -> str:
    raw = _normalize_field_name(field_name)
    if not raw:
        return "campo"
    leaf = raw.split(".")[-1]
    leaf = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", leaf)
    leaf = leaf.replace("_", " ").replace("-", " ").strip()
    return leaf.lower() if leaf else raw


def _append_audit(session: dict[str, Any], event: str, data: dict[str, Any]) -> None:
    audit = session.get("audit", [])
    if not isinstance(audit, list):
        audit = []
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event,
        "data": data,
    }
    audit.append(entry)
    session["audit"] = audit

    session_id = str(session.get("session_id", "")).strip() or "unknown"
    _persist_audit_entry(session_id, entry)


def _persist_audit_entry(session_id: str, entry: dict[str, Any]) -> None:
    """Append one durable audit record in JSONL for traceability."""
    try:
        path = Path(AUDIT_LOG_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {"session_id": session_id, **entry}
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception:
        logger.exception("[Audit] Failed to persist audit entry")


def _build_general_assistant_message(tool_name: str, payload: dict[str, Any]) -> str:
    """Create a concise human-facing summary for any Nimbus tool response."""
    status = str(payload.get("status", "")).strip()
    success = bool(payload.get("success"))
    waiting_for_cache = bool(payload.get("waiting_for_cache"))

    if waiting_for_cache:
        explicit = str(payload.get("assistant_message", "")).strip()
        return explicit if explicit else "Ainda estou sincronizando o cache do Notion. Por favor, aguarde e tente novamente."

    if tool_name == "generate_proposal":
        if success:
            score = payload.get("review", {}).get("score", 0) if isinstance(payload.get("review"), dict) else 0
            output_file = payload.get("output_file")
            gaps = payload.get("data_gaps", [])
            parts = [f"Proposta gerada com sucesso (SCORE: {score:.1f})."]
            if output_file:
                parts.append(f"Arquivo: {output_file}")
            if isinstance(gaps, list) and gaps:
                parts.append(f"{len(gaps)} lacuna(s) de dados identificada(s) (não bloqueantes).")
            return " ".join(parts)
        return status or "Nao consegui gerar a proposta nesta tentativa."

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


def _compact_chat_payload(payload: dict[str, Any], session_id: str | None = None) -> dict[str, Any]:
    """Return a concise chat-friendly payload."""
    compact: dict[str, Any] = {
        "success": bool(payload.get("success")),
        "status": payload.get("status", ""),
        "assistant_message": payload.get("assistant_message", ""),
    }
    if session_id:
        compact["session_id"] = session_id
    if payload.get("success"):
        if payload.get("output_file"):
            compact["output_file"] = payload.get("output_file")
        review = payload.get("review")
        if isinstance(review, dict):
            compact["score"] = review.get("score", 0)
        gaps = payload.get("data_gaps", [])
        if isinstance(gaps, list) and gaps:
            compact["data_gaps_count"] = len(gaps)
    return compact


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


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available proposal generation tools via orchestrator"""
    return [
        Tool(
            name="generate_proposal",
            description="Generate a complete technical architecture proposal with analysis, architecture contract, generation, coherence check, and SCORE evaluation",
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

            logger.info(f"[Orchestrator] Starting proposal generation: {session_id}")

            result = await asyncio.to_thread(
                orchestrator.generate_proposal,
                user_input,
                session_id,
            )

            result["assistant_message"] = _build_general_assistant_message("generate_proposal", result)

            # Store in session
            sessions[session_id] = {
                "session_id": session_id,
                "user_input": user_input,
                "result": result,
                "status": result.get("status"),
                "requires_input": False,
                "last_tool": "generate_proposal",
                "audit": [],
                "created_at": datetime.now().isoformat(),
            }
            _append_audit(
                sessions[session_id],
                "session_created",
                {
                    "source": "user_input",
                    "success": bool(result.get("success")),
                    "data_gaps": len(result.get("data_gaps", [])),
                },
            )

            # Record user input in audit
            _append_audit(
                sessions[session_id],
                "user_input_recorded",
                {"user_input": user_input},
            )

            if result.get("success") and result.get("proposal"):
                proposal_id = f"proposal_{datetime.now().timestamp()}"
                proposals[proposal_id] = result["proposal"]
                result["proposal_id"] = proposal_id

            logger.info(f"[Orchestrator] Proposal generation completed: {result.get('status')}")

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False, default=str)
            )]

        elif name == "analyze_requirements":
            input_text = arguments["input_text"]
            input_type = arguments.get("input_type", "text")

            logger.info("[Orchestrator] Analyzing requirements via analysis sub-agent")

            result = await asyncio.to_thread(
                orchestrator.analyze_requirements,
                input_text,
                input_type,
            )
            if isinstance(result, dict):
                result["assistant_message"] = _build_general_assistant_message("analyze_requirements", result)

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False, default=str)
            )]

        elif name == "scan_security":
            proposal = arguments["proposal"]

            logger.info("[Orchestrator] Scanning security via architecture agent")

            scan_result = await asyncio.to_thread(
                orchestrator.architecture_agent.evaluate_security,
                proposal,
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

            # Record user response in audit
            _append_audit(
                sessions[session_id],
                "user_response_recorded",
                {"user_message": user_message},
            )

            # In v2, gaps are non-blocking so we don't have pending required fields.
            # continue_interaction is used for follow-up questions or regeneration requests.
            previous = sessions[session_id].get("result", {})
            data_gaps = previous.get("data_gaps", []) if isinstance(previous, dict) else []

            # Re-generate with additional context from user message
            user_input = sessions[session_id].get("user_input", "")
            enriched_input = f"{user_input}\n\nInformações adicionais do usuário:\n{user_message}"

            result = await asyncio.to_thread(
                orchestrator.generate_proposal,
                enriched_input,
                session_id,
            )

            result["assistant_message"] = _build_general_assistant_message("generate_proposal", result)
            sessions[session_id]["result"] = result
            sessions[session_id]["status"] = result.get("status")
            sessions[session_id]["last_tool"] = "continue_interaction"

            if result.get("success") and result.get("proposal"):
                proposal_id = f"proposal_{datetime.now().timestamp()}"
                proposals[proposal_id] = result["proposal"]
                result["proposal_id"] = proposal_id

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False, default=str)
            )]

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

            msg = raw_message.strip()
            lowered = msg.lower()
            if lowered.startswith("nimbus"):
                msg = msg[6:].lstrip(" :,-") or raw_message.strip()

            target_session_id = explicit_session_id if isinstance(explicit_session_id, str) and explicit_session_id.strip() else None

            # Check for existing session that might benefit from follow-up
            if not target_session_id:
                target_session_id = _latest_pending_session_id()

            if target_session_id and target_session_id in sessions:
                # Route as continuation of existing session
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

            # No pending session: start a new proposal generation
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

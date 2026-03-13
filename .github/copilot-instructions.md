# Nimbus Routing Guardrails

When a user message starts with `Nimbus` (case-insensitive), treat it as a strict pass-through command to Nimbus MCP.

## Mandatory behavior

1. Do not answer the content directly.
2. Do not summarize, reformulate, or ask your own follow-up questions before routing.
3. Immediately call the MCP tool `mcp_nimbus_chat` with:
   - `message`: the full user message
   - `session_id`: if a known active session is available; otherwise omit it
4. Return Nimbus response to the user as-is (or minimal relay), without adding your own interpretation.
5. If Nimbus requests missing fields, relay that request verbatim and wait for user reply.

## Non-Nimbus messages

For messages that do not start with `Nimbus`, follow normal assistant behavior.

## Safety

If tool call fails, state only that routing failed and ask user to retry the same `Nimbus ...` message.

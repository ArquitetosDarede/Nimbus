"""
AWS Knowledge MCP Client

Creates a Strands MCPClient for the AWS Knowledge MCP Server.
Provides access to comprehensive AWS knowledge including documentation, best practices,
architectural guidance, Agent SOPs, and regional availability information.

Used by ArchitectureAgent and other agents to query AWS best practices and guidance.

Key Features:
- Real-time access to latest AWS documentation
- Best practices and architectural guidance
- Agent SOPs (step-by-step procedures for complex workflows)
- CDK, CloudFormation, and Amplify documentation
- Regional availability information
- What's New posts and blog content
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_aws_knowledge_client = None


def create_aws_knowledge_mcp_client() -> Optional[object]:
    """
    Create AWS Knowledge MCP client using Strands integration.

    Provides access to:
    - AWS documentation (latest, real-time)
    - Best practices and Well-Architected guidance
    - Architectural references and solutions
    - Agent SOPs (step-by-step workflows for AI agents)
    - CDK, CloudFormation, and Amplify frameworks
    - Regional availability of AWS services
    - Troubleshooting guides and error solutions
    - What's New posts and announcements

    Requires the awslabs.aws-knowledge-mcp-server PyPI package (run via uvx).
    The client exposes tools for AWS knowledge access and planning.

    Returns:
        MCPClient instance or None if unavailable.
    """
    global _aws_knowledge_client

    try:
        from strands.tools.mcp import MCPClient
        from mcp.client.stdio import stdio_client, StdioServerParameters

        server_params = StdioServerParameters(
            command="uvx",
            args=["awslabs.aws-knowledge-mcp-server@latest"],
            env={
                "PATH": os.environ.get("PATH", ""),
            },
        )

        def transport_callable():
            return stdio_client(server_params)

        client = MCPClient(
            transport_callable=transport_callable,
            startup_timeout=30,
            prefix="aws_knowledge_",
        )

        _aws_knowledge_client = client
        logger.info("[AWSKnowledgeMCP] AWS Knowledge MCP client created.")
        return client

    except BaseException as e:
        logger.warning("[AWSKnowledgeMCP] AWS Knowledge MCP server is not available: %s", e)
        logger.warning(
            "[AWSKnowledgeMCP] Architecture agent will work without AWS Knowledge "
            "(SOPs, best practices, documentation)."
        )
        return None

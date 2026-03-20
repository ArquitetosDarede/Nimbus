"""
AWS Documentation MCP Client

Creates a Strands MCPClient for the AWS Documentation MCP Server.
Used by ArchitectureAgent to query AWS best practices and service documentation.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_aws_docs_client = None


def create_aws_docs_mcp_client() -> Optional[object]:
    """
    Create AWS Documentation MCP client using Strands integration.

    Requires the awslabs.aws-documentation-mcp-server PyPI package (run via uvx).
    The client exposes tools for searching and reading AWS documentation.

    Returns:
        MCPClient instance or None if unavailable.
    """
    global _aws_docs_client

    try:
        from strands.tools.mcp import MCPClient
        from mcp.client.stdio import stdio_client, StdioServerParameters

        server_params = StdioServerParameters(
            command="uvx",
            args=["awslabs.aws-documentation-mcp-server@latest"],
            env={
                "PATH": os.environ.get("PATH", ""),
            },
        )

        def transport_callable():
            return stdio_client(server_params)

        client = MCPClient(
            transport_callable=transport_callable,
            startup_timeout=30,
            prefix="aws_docs_",
        )

        _aws_docs_client = client
        logger.info("[AWSDocsMCP] AWS Documentation MCP client created.")
        return client

    except BaseException as e:
        logger.warning("[AWSDocsMCP] AWS Documentation MCP server is not available: %s", e)
        logger.warning("[AWSDocsMCP] Architecture agent will work without AWS docs.")
        return None

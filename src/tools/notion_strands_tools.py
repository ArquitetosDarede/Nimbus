"""
Notion Tools using Strands MCP Integration

This module provides Notion access through Strands' native MCP integration.
Uses MCPClient to connect to Notion MCP server and expose tools to agents.

IMPORTANT: According to Strands documentation, MCPClient should be passed
directly to Agent constructor for automatic lifecycle management.
"""

import os
import logging
from typing import Callable
from strands.tools.mcp import MCPClient
from mcp.client.stdio import stdio_client, StdioServerParameters

logger = logging.getLogger(__name__)

# Global MCP client instance
_notion_mcp_client: MCPClient | None = None


def create_notion_transport() -> Callable:
    """
    Create transport callable for Notion MCP server.
    
    Returns:
        Callable that returns async context manager for MCP transport
    """
    # Server parameters - using official Notion MCP server package
    # NOTE: The package expects NOTION_TOKEN, not NOTION_API_KEY
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@notionhq/notion-mcp-server"],
        env={
            "NOTION_TOKEN": os.getenv("NOTION_API_KEY", "")  # Use NOTION_API_KEY from env but pass as NOTION_TOKEN
        }
    )
    
    # Return callable that creates the transport
    def transport_callable():
        return stdio_client(server_params)
    
    return transport_callable


def create_notion_mcp_client() -> MCPClient:
    """
    Create Notion MCP client using Strands integration.
    
    This creates an MCPClient that can be passed directly to Agent constructor.
    The Agent will handle the lifecycle automatically (connection, tool loading, cleanup).
    
    This is the RECOMMENDED approach according to Strands documentation:
    https://strandsagents.com/docs/user-guide/concepts/tools/mcp-tools/
    
    OPTIMIZATION: Uses tool_filters to limit which Notion tools are loaded,
    reducing context size and avoiding OpenAI rate limits.
    
    Returns:
        MCPClient instance ready to be passed to Agent
    """
    global _notion_mcp_client
    
    try:
        # Create transport callable
        transport = create_notion_transport()
        
        # Create MCP client with tool filters to reduce context size
        # Only load essential search and query tools
        import re
        client = MCPClient(
            transport_callable=transport,
            startup_timeout=30,
            prefix="notion_",  # Prefix tools with "notion_"
            tool_filters={
                "allowed": [
                    re.compile(r".*search.*"),      # Allow search tools
                    re.compile(r".*query.*"),       # Allow query tools
                    re.compile(r".*retrieve.*")     # Allow retrieve tools
                ],
                "rejected": [
                    re.compile(r".*create.*"),      # Reject create tools (not needed for reading)
                    re.compile(r".*update.*"),      # Reject update tools
                    re.compile(r".*delete.*"),      # Reject delete tools
                    re.compile(r".*move.*"),        # Reject move tools
                    re.compile(r".*append.*")       # Reject append tools
                ]
            }
        )
        
        logger.info("✅ Created Notion MCP client with filtered tools (search, query, retrieve only)")
        logger.info("   This reduces context size and avoids OpenAI rate limits")
        
        # Store client reference
        _notion_mcp_client = client
        
        return client
            
    except Exception as e:
        logger.error(f"❌ Failed to create Notion MCP client: {e}")
        logger.exception("Full traceback:")
        raise


def cleanup_notion_mcp_client():
    """
    Cleanup Notion MCP client resources.
    
    Call this when shutting down the application.
    Note: If using managed integration (passing MCPClient to Agent),
    cleanup is handled automatically.
    """
    global _notion_mcp_client
    
    if _notion_mcp_client is not None:
        try:
            _notion_mcp_client.stop(None, None, None)
            logger.info("Notion MCP client stopped")
        except:
            pass
        finally:
            _notion_mcp_client = None

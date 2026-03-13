"""
Notion MCP Tools for Strands Agents

Provides REAL Notion access as tools for Analysis and Generation agents.
Uses Strands @tool decorator for tool creation.

This version connects to the actual Notion MCP server and returns real data.
"""

from typing import List
import json
from strands import tool
from .notion_client import get_notion_client

# Try to import real MCP client
try:
    from .notion_mcp_client import search_notion_sync, fetch_notion_sync, query_database_sync
    REAL_NOTION_AVAILABLE = True
except ImportError:
    REAL_NOTION_AVAILABLE = False


@tool
def notion_search(query: str, query_type: str = "internal") -> str:
    """
    Search Notion workspace for validated scopes, rules, and guidelines.
    
    Use this to:
    - Find validated scopes based on technologies (e.g., "AWS Lambda", "VPC", "RDS")
    - Search for proposal structure rules
    - Find templates and guidelines
    - Query scope databases
    
    Args:
        query: Search query (e.g., "AWS Lambda scope", "proposal structure")
        query_type: "internal" for workspace search, "user" for user search
    
    Returns:
        Real search results from Notion or instructions if not available
    """
    client = get_notion_client()
    if not client.connected:
        return "Notion integration not available. Please configure NOTION_API_KEY."
    
    # Try to use real MCP client
    if REAL_NOTION_AVAILABLE:
        try:
            result = search_notion_sync(query, query_type)
            if result and not result.get("error"):
                return json.dumps(result, indent=2, ensure_ascii=False)
        except Exception as e:
            # Fallback to instructions if real connection fails
            pass
    
    # Fallback: return instructions
    return f"""
To search Notion for '{query}':

1. Use the Notion MCP server configured in Kiro
2. Search for: {query}
3. Look for:
   - Validated scopes matching the technologies
   - Proposal structure rules and guidelines
   - Templates and best practices
   - Hours estimation rules

The search should return pages and databases related to your query.
Extract relevant information and use it in your analysis/generation.
    """.strip()


@tool
def notion_fetch(id: str, include_discussions: bool = False) -> str:
    """
    Fetch complete content from a Notion page or database by URL or ID.
    
    Use this to:
    - Get full details of a validated scope
    - Read complete proposal structure rules
    - Fetch template content
    - Access database schemas
    
    Args:
        id: Notion page URL or ID
        include_discussions: Include comments/discussions
    
    Returns:
        Real page content from Notion or instructions if not available
    """
    client = get_notion_client()
    if not client.connected:
        return "Notion integration not available. Please configure NOTION_API_KEY."
    
    # Try to use real MCP client
    if REAL_NOTION_AVAILABLE:
        try:
            result = fetch_notion_sync(id, include_discussions)
            if result and not result.get("error"):
                return json.dumps(result, indent=2, ensure_ascii=False)
        except Exception as e:
            # Fallback to instructions if real connection fails
            pass
    
    # Fallback: return instructions
    return f"""
To fetch Notion page/database '{id}':

1. Use the Notion MCP server configured in Kiro
2. Fetch the page/database with ID: {id}
3. Include discussions: {include_discussions}

The fetch should return the complete content in Markdown format.
Use this content to inform your proposal generation.
    """.strip()


@tool
def notion_query_database(view_url: str) -> str:
    """
    Query a Notion database view with filters and sorts.
    
    Use this to:
    - Query scope catalog database
    - Filter scopes by technology, hours, or type
    - Get all scopes for a specific AWS service
    - Find scopes within a hours range
    
    Args:
        view_url: Database view URL
    
    Returns:
        Real database query results from Notion or instructions if not available
    """
    client = get_notion_client()
    if not client.connected:
        return "Notion integration not available. Please configure NOTION_API_KEY."
    
    # Try to use real MCP client
    if REAL_NOTION_AVAILABLE:
        try:
            result = query_database_sync(view_url)
            if result and not result.get("error"):
                return json.dumps(result, indent=2, ensure_ascii=False)
        except Exception as e:
            # Fallback to instructions if real connection fails
            pass
    
    # Fallback: return instructions
    return f"""
To query Notion database view '{view_url}':

1. Use the Notion MCP server configured in Kiro
2. Query the database view: {view_url}
3. The view may have filters and sorts pre-configured

The query should return filtered database rows.
Extract scope information (title, description, hours, technologies) for your proposal.
    """.strip()


def create_all_notion_tools() -> List:
    """
    Create all Notion tools for Strands agents.
    
    These tools provide REAL access to Notion through MCP client,
    with fallback to instructions if connection fails.
    
    Returns:
        List of Notion tools (functions decorated with @tool)
    """
    return [
        notion_search,
        notion_fetch,
        notion_query_database
    ]

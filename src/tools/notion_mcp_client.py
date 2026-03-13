"""
Notion SDK Client

Direct connection to Notion API using the official Python SDK.
No MCP server layer needed - simpler, faster, and more reliable.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

try:
    from notion_client import Client as NotionClient
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    logging.warning("Notion SDK not available. Install with: pip install notion-client")

logger = logging.getLogger(__name__)

# Thread pool for async wrappers
_thread_pool = ThreadPoolExecutor(max_workers=3)


class NotionMCPClient:
    """
    Client for connecting directly to Notion API using the official SDK.
    
    This is a simpler alternative to the MCP server approach:
    - Direct HTTP calls to Notion API
    - No subprocess management needed
    - Better error handling and logging
    - Faster performance
    """
    
    def __init__(self):
        if not SDK_AVAILABLE:
            logger.warning("Notion SDK not installed. Install with: pip install notion-client")
            self.client = None
            self.connected = False
            return
        
        # Get token from environment
        notion_token = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
        
        if not notion_token:
            logger.warning("NOTION_API_KEY or NOTION_TOKEN environment variable not set")
            self.client = None
            self.connected = False
            return
        
        try:
            # Initialize Notion client
            self.client = NotionClient(auth=notion_token)
            
            # Verify connection by fetching user info
            user_info = self.client.users.me()
            self.connected = True
            user_name = user_info.get("name", "Unknown")
            logger.info(f"✅ Connected to Notion as: {user_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Notion: {e}")
            self.client = None
            self.connected = False
    
    async def search(self, query: str, query_type: str = "internal") -> Dict[str, Any]:
        """
        Search Notion workspace.
        
        Args:
            query: Search query
            query_type: Type of search (internal, user)
        
        Returns:
            Search results from Notion
        """
        if not self.connected or not self.client:
            return {"error": "Not connected to Notion", "results": []}
        
        try:
            # Run search in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                _thread_pool,
                lambda: self.client.search(query=query, page_size=10)
            )
            
            # Format results
            items = result.get("results", [])
            formatted_items = []
            
            for item in items:
                formatted_item = {
                    "id": item["id"],
                    "object": item.get("object", "unknown"),
                    "title": self._extract_title(item),
                    "url": item.get("url", ""),
                    "last_edited_time": item.get("last_edited_time", "")
                }
                formatted_items.append(formatted_item)
            
            return {
                "query": query,
                "results": formatted_items,
                "total": len(formatted_items)
            }
            
        except Exception as e:
            logger.error(f"Notion search failed: {e}")
            return {"error": str(e), "results": []}
    
    async def fetch(self, page_id: str, include_discussions: bool = False) -> Dict[str, Any]:
        """
        Fetch Notion page or database content.
        
        Args:
            page_id: Notion page or database ID/URL
            include_discussions: Include comments/discussions (not implemented yet)
        
        Returns:
            Page content and metadata from Notion
        """
        if not self.connected or not self.client:
            return {"error": "Not connected to Notion", "content": ""}
        
        try:
            # Normalize page ID (remove hyphens for API)
            normalized_id = page_id.replace("-", "")
            
            # Run fetch in thread pool
            loop = asyncio.get_event_loop()
            page = await loop.run_in_executor(
                _thread_pool,
                lambda: self.client.pages.retrieve(normalized_id)
            )
            
            # Extract content
            title = self._extract_title(page)
            properties = page.get("properties", {})
            
            # Get page blocks (actual content)
            blocks = await loop.run_in_executor(
                _thread_pool,
                lambda: self.client.blocks.children.list(normalized_id)
            )
            
            # Format block content
            block_content = self._format_blocks(blocks.get("results", []))
            
            return {
                "id": page["id"],
                "title": title,
                "content": block_content,
                "properties": list(properties.keys()),
                "url": page.get("url", ""),
                "last_edited_time": page.get("last_edited_time", "")
            }
            
        except Exception as e:
            logger.error(f"Notion fetch failed: {e}")
            return {"error": str(e), "content": ""}
    
    async def query_database(self, view_url: str) -> Dict[str, Any]:
        """
        Query Notion database.
        
        Args:
            view_url: Database view URL or database ID
        
        Returns:
            Database query results
        """
        if not self.connected or not self.client:
            return {"error": "Not connected to Notion", "rows": []}
        
        try:
            # Extract database ID from URL or use directly if it's an ID
            db_id = self._extract_db_id(view_url)
            
            # Run query in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                _thread_pool,
                lambda: self.client.databases.query(db_id, page_size=100)
            )
            
            # Format rows
            rows = []
            for item in result.get("results", []):
                rows.append({
                    "id": item["id"],
                    "url": item.get("url", ""),
                    "properties": item.get("properties", {}),
                    "last_edited_time": item.get("last_edited_time", "")
                })
            
            return {
                "database_id": db_id,
                "rows": rows,
                "total": len(rows)
            }
            
        except Exception as e:
            logger.error(f"Notion database query failed: {e}")
            return {"error": str(e), "rows": []}
    
    def _extract_title(self, item: Dict[str, Any]) -> str:
        """Extract title from Notion page or database."""
        # Try direct title field (pages)
        if "title" in item:
            title_blocks = item.get("title", [])
            if title_blocks:
                return title_blocks[0].get("plain_text", "Untitled")
        
        # Try title from properties (databases)
        if "properties" in item:
            for prop_name, prop_val in item.get("properties", {}).items():
                if prop_val.get("type") == "title":
                    return prop_name
        
        return "Untitled"
    
    def _extract_db_id(self, url_or_id: str) -> str:
        """Extract database ID from URL or use as-is if it's already an ID."""
        # If it's a URL, extract ID
        if "notion.so" in url_or_id:
            # Extract ID from URL (typically the last part)
            parts = url_or_id.replace("https://", "").replace("http://", "").split("/")
            for part in reversed(parts):
                if len(part) >= 32:  # Notion IDs are at least 32 chars
                    return part.replace("-", "")
        
        # Otherwise assume it's already an ID, normalize it
        return url_or_id.replace("-", "").lower()
    
    def _format_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """Format Notion blocks into readable text."""
        content_parts = []
        
        for block in blocks:
            block_type = block.get("type", "")
            block_data = block.get(block_type, {})
            
            if block_type == "paragraph":
                text = self._extract_text(block_data.get("rich_text", []))
                if text:
                    content_parts.append(text)
            
            elif block_type == "heading_1":
                text = self._extract_text(block_data.get("rich_text", []))
                if text:
                    content_parts.append(f"# {text}")
            
            elif block_type == "heading_2":
                text = self._extract_text(block_data.get("rich_text", []))
                if text:
                    content_parts.append(f"## {text}")
            
            elif block_type == "heading_3":
                text = self._extract_text(block_data.get("rich_text", []))
                if text:
                    content_parts.append(f"### {text}")
            
            elif block_type == "bulleted_list_item":
                text = self._extract_text(block_data.get("rich_text", []))
                if text:
                    content_parts.append(f"- {text}")
            
            elif block_type == "numbered_list_item":
                text = self._extract_text(block_data.get("rich_text", []))
                if text:
                    content_parts.append(f"• {text}")
            
            elif block_type == "code":
                text = self._extract_text(block_data.get("rich_text", []))
                language = block_data.get("language", "")
                if text:
                    content_parts.append(f"```{language}\n{text}\n```")
        
        return "\n".join(content_parts)
    
    def _extract_text(self, rich_text_array: List[Dict[str, Any]]) -> str:
        """Extract plain text from Notion rich text array."""
        text_parts = []
        for rich_text in rich_text_array:
            text_parts.append(rich_text.get("plain_text", ""))
        return "".join(text_parts)


# Singleton instance
_notion_client: Optional[NotionMCPClient] = None


def get_notion_mcp_client() -> NotionMCPClient:
    """Get singleton Notion MCP client instance."""
    global _notion_client
    if _notion_client is None:
        _notion_client = NotionMCPClient()
    return _notion_client


# Synchronous wrappers for use in Strands agents
def search_notion_sync(query: str, query_type: str = "internal") -> Dict[str, Any]:
    """
    Synchronous wrapper for Notion search.
    
    This can be called from Strands agents which run in sync context.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    client = get_notion_mcp_client()
    return loop.run_until_complete(client.search(query, query_type))


def fetch_notion_sync(page_id: str, include_discussions: bool = False) -> Dict[str, Any]:
    """
    Synchronous wrapper for Notion fetch.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    client = get_notion_mcp_client()
    return loop.run_until_complete(client.fetch(page_id, include_discussions))


def query_database_sync(view_url: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for Notion database query.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    client = get_notion_mcp_client()
    return loop.run_until_complete(client.query_database(view_url))


def create_notion_mcp_client() -> NotionMCPClient:
    """
    Backward-compatible factory kept for legacy imports.

    Returns the SDK-backed singleton client instance.
    """
    return get_notion_mcp_client()

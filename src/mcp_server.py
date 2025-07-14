#!/usr/bin/env python3
"""
MCP (Model Context Protocol) server for Gemini Context Extraction
Provides AI agents with structured access to Gemini conversation data.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

# MCP imports
try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource, Tool, TextContent, ImageContent, EmbeddedResource,
        CallToolRequest, CallToolResult, GetResourceRequest, GetResourceResult,
        ListResourcesRequest, ListResourcesResult,
        ListToolsRequest, ListToolsResult
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("⚠️ MCP not available. Install with: pip install mcp")

from .config import get_config
from .enhanced_gemini_extractor import EnhancedGeminiExtractor
from .conversation_analyzer import ConversationAnalyzer
from .search_based_extractor import SearchBasedExtractor

class GeminiMCPServer:
    """MCP server for Gemini conversation extraction and analysis."""
    
    def __init__(self):
        self.config = get_config()
        self.server = Server("gemini-context-extractor")
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up MCP handlers."""
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available conversation resources."""
            resources = []
            extracts_dir = Path(self.config.extraction.output_dir)
            
            # List structured conversations
            for json_file in extracts_dir.glob("structured_*.json"):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    resources.append(Resource(
                        uri=f"gemini://conversation/{json_file.stem}",
                        name=data.get("title", json_file.stem),
                        description=f"Conversation with {data.get('message_count', 0)} messages",
                        mimeType="application/json"
                    ))
                except Exception as e:
                    logging.warning(f"Error reading {json_file}: {e}")
            
            # Add analysis resources
            for analysis_file in extracts_dir.glob("conversation_analysis_*.json"):
                resources.append(Resource(
                    uri=f"gemini://analysis/{analysis_file.stem}",
                    name=f"Analysis: {analysis_file.stem}",
                    description="Conversation analysis and insights",
                    mimeType="application/json"
                ))
            
            return resources
        
        @self.server.get_resource()
        async def get_resource(uri: str) -> GetResourceResult:
            """Get a specific conversation or analysis resource."""
            if uri.startswith("gemini://conversation/"):
                conversation_id = uri.replace("gemini://conversation/", "")
                return await self._get_conversation_resource(conversation_id)
            elif uri.startswith("gemini://analysis/"):
                analysis_id = uri.replace("gemini://analysis/", "")
                return await self._get_analysis_resource(analysis_id)
            else:
                raise ValueError(f"Unknown resource URI: {uri}")
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="extract_conversation",
                    description="Extract a Gemini conversation from URL",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "Gemini conversation URL"
                            },
                            "title": {
                                "type": "string",
                                "description": "Optional conversation title"
                            }
                        },
                        "required": ["url"]
                    }
                ),
                Tool(
                    name="search_conversations",
                    description="Search for conversations by query",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="analyze_conversations",
                    description="Analyze all extracted conversations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_details": {
                                "type": "boolean",
                                "description": "Include detailed analysis",
                                "default": True
                            }
                        }
                    }
                ),
                Tool(
                    name="get_conversation_summary",
                    description="Get summary of a specific conversation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "conversation_id": {
                                "type": "string",
                                "description": "Conversation ID or filename"
                            }
                        },
                        "required": ["conversation_id"]
                    }
                ),
                Tool(
                    name="list_conversations",
                    description="List all available conversations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_metadata": {
                                "type": "boolean",
                                "description": "Include conversation metadata",
                                "default": True
                            }
                        }
                    }
                ),
                Tool(
                    name="search_conversation_content",
                    description="Search within conversation content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "conversation_id": {
                                "type": "string",
                                "description": "Optional specific conversation ID"
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            try:
                if name == "extract_conversation":
                    return await self._extract_conversation_tool(arguments)
                elif name == "search_conversations":
                    return await self._search_conversations_tool(arguments)
                elif name == "analyze_conversations":
                    return await self._analyze_conversations_tool(arguments)
                elif name == "get_conversation_summary":
                    return await self._get_conversation_summary_tool(arguments)
                elif name == "list_conversations":
                    return await self._list_conversations_tool(arguments)
                elif name == "search_conversation_content":
                    return await self._search_conversation_content_tool(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
    
    async def _get_conversation_resource(self, conversation_id: str) -> GetResourceResult:
        """Get conversation resource."""
        extracts_dir = Path(self.config.extraction.output_dir)
        json_file = extracts_dir / f"{conversation_id}.json"
        
        if not json_file.exists():
            raise FileNotFoundError(f"Conversation not found: {conversation_id}")
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        return GetResourceResult(
            contents=[TextContent(
                type="text",
                text=json.dumps(data, indent=2)
            )]
        )
    
    async def _get_analysis_resource(self, analysis_id: str) -> GetResourceResult:
        """Get analysis resource."""
        extracts_dir = Path(self.config.extraction.output_dir)
        analysis_file = extracts_dir / f"{analysis_id}.json"
        
        if not analysis_file.exists():
            raise FileNotFoundError(f"Analysis not found: {analysis_id}")
        
        with open(analysis_file, 'r') as f:
            data = json.load(f)
        
        return GetResourceResult(
            contents=[TextContent(
                type="text",
                text=json.dumps(data, indent=2)
            )]
        )
    
    async def _extract_conversation_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Extract conversation tool."""
        url = arguments["url"]
        title = arguments.get("title", "")
        
        extractor = EnhancedGeminiExtractor(
            cdp_port=self.config.browser.cdp_port,
            output_dir=self.config.extraction.output_dir
        )
        
        result = await extractor.extract_conversation_with_structure(url, title)
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"✅ Conversation extracted successfully!\n\n"
                     f"📄 **Title**: {result.get('title', 'Unknown')}\n"
                     f"💬 **Messages**: {result.get('message_count', 0)}\n"
                     f"📁 **Files**: {', '.join(result.get('files', []))}\n\n"
                     f"**Result**: {json.dumps(result, indent=2)}"
            )]
        )
    
    async def _search_conversations_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Search conversations tool."""
        query = arguments["query"]
        limit = arguments.get("limit", 10)
        
        extractor = SearchBasedExtractor(
            cdp_port=self.config.browser.cdp_port,
            output_dir=self.config.extraction.output_dir
        )
        
        result = await extractor.search_conversations(query, limit)
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"🔍 Search results for '{query}':\n\n{json.dumps(result, indent=2)}"
            )]
        )
    
    async def _analyze_conversations_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Analyze conversations tool."""
        include_details = arguments.get("include_details", True)
        
        analyzer = ConversationAnalyzer(self.config.extraction.output_dir)
        summary, analyses = analyzer.analyze_all_conversations()
        
        if include_details:
            result = {"summary": summary, "detailed_analyses": analyses}
        else:
            result = {"summary": summary}
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"📊 Conversation Analysis:\n\n{json.dumps(result, indent=2)}"
            )]
        )
    
    async def _get_conversation_summary_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get conversation summary tool."""
        conversation_id = arguments["conversation_id"]
        
        extracts_dir = Path(self.config.extraction.output_dir)
        json_file = extracts_dir / f"structured_{conversation_id}.json"
        
        if not json_file.exists():
            # Try without structured_ prefix
            json_file = extracts_dir / f"{conversation_id}.json"
        
        if not json_file.exists():
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"❌ Conversation not found: {conversation_id}"
                )],
                isError=True
            )
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        summary = {
            "title": data.get("title", "Unknown"),
            "url": data.get("url", ""),
            "message_count": data.get("message_count", 0),
            "extracted_at": data.get("extracted_at", ""),
            "messages_preview": data.get("messages", [])[:3]  # First 3 messages
        }
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"📄 Conversation Summary:\n\n{json.dumps(summary, indent=2)}"
            )]
        )
    
    async def _list_conversations_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """List conversations tool."""
        include_metadata = arguments.get("include_metadata", True)
        
        extracts_dir = Path(self.config.extraction.output_dir)
        conversations = []
        
        for json_file in extracts_dir.glob("structured_*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                conv_info = {
                    "id": json_file.stem,
                    "title": data.get("title", "Unknown"),
                    "message_count": data.get("message_count", 0)
                }
                
                if include_metadata:
                    conv_info.update({
                        "url": data.get("url", ""),
                        "extracted_at": data.get("extracted_at", ""),
                        "file": str(json_file)
                    })
                
                conversations.append(conv_info)
            except Exception as e:
                logging.warning(f"Error reading {json_file}: {e}")
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"📚 Available Conversations ({len(conversations)}):\n\n{json.dumps(conversations, indent=2)}"
            )]
        )
    
    async def _search_conversation_content_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Search conversation content tool."""
        query = arguments["query"]
        conversation_id = arguments.get("conversation_id")
        
        extracts_dir = Path(self.config.extraction.output_dir)
        results = []
        
        # Determine which files to search
        if conversation_id:
            json_files = [extracts_dir / f"structured_{conversation_id}.json"]
        else:
            json_files = list(extracts_dir.glob("structured_*.json"))
        
        for json_file in json_files:
            if not json_file.exists():
                continue
            
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                # Search in messages
                matching_messages = []
                for msg in data.get("messages", []):
                    if query.lower() in msg.get("content", "").lower():
                        matching_messages.append({
                            "id": msg.get("id", ""),
                            "sender": msg.get("sender", ""),
                            "content_preview": msg.get("content", "")[:200] + "..."
                        })
                
                if matching_messages:
                    results.append({
                        "conversation": data.get("title", json_file.stem),
                        "matches": len(matching_messages),
                        "messages": matching_messages[:5]  # Limit to 5 matches per conversation
                    })
            
            except Exception as e:
                logging.warning(f"Error searching {json_file}: {e}")
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"🔍 Content search results for '{query}':\n\n{json.dumps(results, indent=2)}"
            )]
        )

async def main():
    """Run the MCP server."""
    if not MCP_AVAILABLE:
        print("❌ MCP not available. Install with: pip install mcp")
        return
    
    server_instance = GeminiMCPServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="gemini-context-extractor",
                server_version="1.0.0",
                capabilities=server_instance.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())

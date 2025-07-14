#!/usr/bin/env python3
"""
FastAPI HTTP MCP Server for Gemini Context Extraction
Uses FastAPI with SSE (Server-Sent Events) for MCP protocol over HTTP.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

# FastAPI imports
try:
    from fastapi import FastAPI, Request
    from fastapi.responses import StreamingResponse
    from fastapi.middleware.cors import CORSMiddleware
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("⚠️ FastAPI not available. Install with: pip install fastapi uvicorn")

# MCP imports
try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.sse import SseServerTransport
    from mcp.types import (
        Resource, Tool, TextContent, CallToolResult,
        GetResourceResult, ListResourcesResult, ListToolsResult
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("⚠️ MCP not available. Install with: pip install mcp")

from .config import get_config
from .enhanced_gemini_extractor import EnhancedGeminiExtractor
from .conversation_analyzer import ConversationAnalyzer

class GeminiFastAPIMCPServer:
    """FastAPI-based HTTP MCP server for Gemini conversation extraction."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI is required. Install with: pip install fastapi uvicorn")
        
        if not MCP_AVAILABLE:
            raise ImportError("MCP is required. Install with: pip install mcp")
        
        self.config = get_config()
        self.host = host
        self.port = port
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Gemini Context Extractor MCP Server",
            description="HTTP MCP server for Gemini conversation extraction and analysis",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Create MCP server
        self.mcp_server = Server("gemini-context-extractor")
        
        # Setup MCP handlers
        self.setup_mcp_handlers()
        
        # Setup FastAPI routes
        self.setup_routes()
        
        # Create SSE server
        self.sse_app = self.create_sse_server()
        
        # Mount SSE server
        self.app.mount("/mcp", self.sse_app)
    
    def create_sse_server(self):
        """Create a Starlette app that handles SSE connections."""
        transport = SseServerTransport("/messages/")
        
        async def handle_sse(request):
            """Handle SSE connections for MCP."""
            async with transport.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await self.mcp_server.run(
                    streams[0], streams[1], 
                    InitializationOptions(
                        server_name="gemini-context-extractor",
                        server_version="1.0.0",
                        capabilities=self.mcp_server.get_capabilities()
                    )
                )
        
        # Create Starlette routes for SSE and message handling
        routes = [
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=transport.handle_post_message),
        ]
        
        return Starlette(routes=routes)
    
    def setup_mcp_handlers(self):
        """Setup MCP protocol handlers."""
        
        @self.mcp_server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="extract_conversation",
                    description="Extract a Gemini conversation from URL",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "Gemini conversation URL"},
                            "title": {"type": "string", "description": "Optional conversation title"}
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
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "description": "Max results", "default": 10}
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
                            "include_details": {"type": "boolean", "default": True}
                        }
                    }
                ),
                Tool(
                    name="list_conversations",
                    description="List all available conversations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_metadata": {"type": "boolean", "default": True}
                        }
                    }
                ),
                Tool(
                    name="get_conversation_details",
                    description="Get detailed information about a specific conversation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "conversation_id": {"type": "string", "description": "Conversation ID"}
                        },
                        "required": ["conversation_id"]
                    }
                )
            ]
        
        @self.mcp_server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            try:
                if name == "extract_conversation":
                    return await self._extract_conversation_tool(arguments)
                elif name == "search_conversations":
                    return await self._search_conversations_tool(arguments)
                elif name == "analyze_conversations":
                    return await self._analyze_conversations_tool(arguments)
                elif name == "list_conversations":
                    return await self._list_conversations_tool(arguments)
                elif name == "get_conversation_details":
                    return await self._get_conversation_details_tool(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
    
    async def _extract_conversation_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Extract conversation tool implementation."""
        url = arguments["url"]
        title = arguments.get("title", "")
        
        try:
            extractor = EnhancedGeminiExtractor(
                cdp_port=self.config.browser.cdp_port,
                output_dir=self.config.extraction.output_dir
            )
            
            result = await extractor.extract_conversation_with_structure(url, title)
            
            response = {
                "success": True,
                "message": "Conversation extracted successfully",
                "data": result
            }
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(response, indent=2))]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error extracting conversation: {str(e)}")],
                isError=True
            )
    
    async def _search_conversations_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Search conversations tool implementation."""
        query = arguments["query"]
        limit = arguments.get("limit", 10)
        
        try:
            extracts_dir = Path(self.config.extraction.output_dir)
            results = []
            
            for json_file in extracts_dir.glob("structured_*.json"):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    # Simple text search
                    title = data.get("title", "")
                    messages = data.get("messages", [])
                    
                    matches = False
                    if query.lower() in title.lower():
                        matches = True
                    else:
                        for msg in messages:
                            if query.lower() in msg.get("content", "").lower():
                                matches = True
                                break
                    
                    if matches:
                        results.append({
                            "title": title,
                            "url": data.get("url", ""),
                            "message_count": data.get("message_count", 0),
                            "file": str(json_file),
                            "extracted_at": data.get("extracted_at", "")
                        })
                    
                    if len(results) >= limit:
                        break
                
                except Exception as e:
                    logging.warning(f"Error reading {json_file}: {e}")
            
            response = {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results)
            }
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(response, indent=2))]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error searching conversations: {str(e)}")],
                isError=True
            )
    
    async def _analyze_conversations_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Analyze conversations tool implementation."""
        include_details = arguments.get("include_details", True)
        
        try:
            analyzer = ConversationAnalyzer(self.config.extraction.output_dir)
            summary, analyses = analyzer.analyze_all_conversations()
            
            result = {"summary": summary}
            if include_details:
                result["detailed_analyses"] = analyses
            
            response = {
                "success": True,
                "message": "Analysis completed successfully",
                "data": result
            }
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(response, indent=2))]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error analyzing conversations: {str(e)}")],
                isError=True
            )
    
    async def _list_conversations_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """List conversations tool implementation."""
        include_metadata = arguments.get("include_metadata", True)
        
        try:
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
            
            response = {
                "success": True,
                "conversations": conversations,
                "count": len(conversations)
            }
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(response, indent=2))]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error listing conversations: {str(e)}")],
                isError=True
            )
    
    async def _get_conversation_details_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get conversation details tool implementation."""
        conversation_id = arguments["conversation_id"]
        
        try:
            extracts_dir = Path(self.config.extraction.output_dir)
            json_file = extracts_dir / f"{conversation_id}.json"
            
            if not json_file.exists():
                json_file = extracts_dir / f"structured_{conversation_id}.json"
            
            if not json_file.exists():
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Conversation not found: {conversation_id}")],
                    isError=True
                )
            
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            response = {
                "success": True,
                "conversation": data
            }
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(response, indent=2))]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error getting conversation details: {str(e)}")],
                isError=True
            )
    
    def setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/")
        async def root():
            """Health check endpoint."""
            return {
                "service": "Gemini Context Extractor MCP Server",
                "version": "1.0.0",
                "status": "running",
                "mcp_endpoint": f"http://{self.host}:{self.port}/mcp/sse",
                "health_endpoint": f"http://{self.host}:{self.port}/health",
                "tools": ["extract_conversation", "search_conversations", "analyze_conversations", "list_conversations", "get_conversation_details"]
            }
        
        @self.app.get("/health")
        async def health():
            """Detailed health check."""
            return {
                "status": "healthy",
                "mcp_server": "gemini-context-extractor",
                "config": {
                    "browser": {
                        "cdp_port": self.config.browser.cdp_port,
                        "user_data_dir": self.config.browser.user_data_dir
                    },
                    "extraction": {
                        "output_dir": self.config.extraction.output_dir,
                        "use_markitdown": self.config.extraction.use_markitdown
                    }
                }
            }
    
    def run(self):
        """Run the FastAPI HTTP MCP server."""
        print(f"🚀 Starting Gemini FastAPI MCP Server...")
        print(f"📍 Server URL: http://{self.host}:{self.port}")
        print(f"🔌 MCP SSE Endpoint: http://{self.host}:{self.port}/mcp/sse")
        print(f"🏥 Health Check: http://{self.host}:{self.port}/health")
        print(f"🔧 Tools: extract_conversation, search_conversations, analyze_conversations, list_conversations, get_conversation_details")
        
        uvicorn.run(self.app, host=self.host, port=self.port)

async def main():
    """Main entry point for FastAPI HTTP MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gemini FastAPI HTTP MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    
    server = GeminiFastAPIMCPServer(host=args.host, port=args.port)
    server.run()

if __name__ == "__main__":
    asyncio.run(main())

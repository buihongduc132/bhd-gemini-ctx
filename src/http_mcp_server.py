#!/usr/bin/env python3
"""
HTTP MCP Server for Gemini Context Extraction
Provides AI agents with HTTP-based access to Gemini conversation data using FastAPI and SSE.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

# FastAPI imports
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import StreamingResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("⚠️ FastAPI not available. Install with: pip install fastapi uvicorn")

# MCP imports with FastMCP
try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    print("⚠️ FastMCP not available. Install with: pip install fastmcp")

from .config import get_config
from .enhanced_gemini_extractor import EnhancedGeminiExtractor
from .conversation_analyzer import ConversationAnalyzer

class GeminiHTTPMCPServer:
    """HTTP MCP server for Gemini conversation extraction and analysis."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI is required for HTTP MCP server. Install with: pip install fastapi uvicorn")
        
        if not FASTMCP_AVAILABLE:
            raise ImportError("FastMCP is required for HTTP MCP server. Install with: pip install fastmcp")
        
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
        
        # Create FastMCP instance
        self.mcp = FastMCP("gemini-context-extractor")
        
        # Setup MCP tools
        self.setup_mcp_tools()
        
        # Setup FastAPI routes
        self.setup_routes()
    
    def setup_mcp_tools(self):
        """Setup MCP tools for AI agents."""
        
        @self.mcp.tool()
        async def extract_conversation(url: str, title: str = "") -> Dict[str, Any]:
            """Extract a Gemini conversation from URL with structured parsing."""
            try:
                extractor = EnhancedGeminiExtractor(
                    cdp_port=self.config.browser.cdp_port,
                    output_dir=self.config.extraction.output_dir
                )
                
                result = await extractor.extract_conversation_with_structure(url, title)
                
                return {
                    "success": True,
                    "message": "Conversation extracted successfully",
                    "data": result
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to extract conversation"
                }
        
        @self.mcp.tool()
        async def search_conversations(query: str, limit: int = 10) -> Dict[str, Any]:
            """Search for conversations by query."""
            try:
                # For now, search in extracted conversations
                extracts_dir = Path(self.config.extraction.output_dir)
                results = []
                
                for json_file in extracts_dir.glob("structured_*.json"):
                    try:
                        with open(json_file, 'r') as f:
                            data = json.load(f)
                        
                        # Simple text search in title and messages
                        title = data.get("title", "")
                        messages = data.get("messages", [])
                        
                        # Check if query matches title or any message content
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
                
                return {
                    "success": True,
                    "query": query,
                    "results": results,
                    "count": len(results)
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to search conversations"
                }
        
        @self.mcp.tool()
        async def analyze_conversations(include_details: bool = True) -> Dict[str, Any]:
            """Analyze all extracted conversations and provide insights."""
            try:
                analyzer = ConversationAnalyzer(self.config.extraction.output_dir)
                summary, analyses = analyzer.analyze_all_conversations()
                
                result = {"summary": summary}
                if include_details:
                    result["detailed_analyses"] = analyses
                
                return {
                    "success": True,
                    "message": "Analysis completed successfully",
                    "data": result
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to analyze conversations"
                }
        
        @self.mcp.tool()
        async def list_conversations(include_metadata: bool = True) -> Dict[str, Any]:
            """List all available conversations."""
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
                
                return {
                    "success": True,
                    "conversations": conversations,
                    "count": len(conversations)
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to list conversations"
                }
        
        @self.mcp.tool()
        async def get_conversation_details(conversation_id: str) -> Dict[str, Any]:
            """Get detailed information about a specific conversation."""
            try:
                extracts_dir = Path(self.config.extraction.output_dir)
                json_file = extracts_dir / f"{conversation_id}.json"
                
                if not json_file.exists():
                    # Try with structured_ prefix
                    json_file = extracts_dir / f"structured_{conversation_id}.json"
                
                if not json_file.exists():
                    return {
                        "success": False,
                        "error": "Conversation not found",
                        "message": f"No conversation found with ID: {conversation_id}"
                    }
                
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                return {
                    "success": True,
                    "conversation": data
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to get conversation details"
                }
    
    def setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/")
        async def root():
            """Health check endpoint."""
            return {
                "service": "Gemini Context Extractor MCP Server",
                "version": "1.0.0",
                "status": "running",
                "mcp_endpoint": "/mcp",
                "tools_count": len(self.mcp._tools),
                "config": {
                    "cdp_port": self.config.browser.cdp_port,
                    "output_dir": self.config.extraction.output_dir
                }
            }
        
        @self.app.get("/health")
        async def health():
            """Detailed health check."""
            return {
                "status": "healthy",
                "mcp_tools": list(self.mcp._tools.keys()),
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
        
        # Mount MCP server at /mcp endpoint
        @self.app.get("/mcp")
        async def mcp_endpoint():
            """MCP SSE endpoint for AI agents."""
            # This will be handled by FastMCP's built-in SSE support
            return {"message": "MCP endpoint - use SSE connection"}
    
    async def run(self):
        """Run the HTTP MCP server."""
        print(f"🚀 Starting Gemini HTTP MCP Server...")
        print(f"📍 Server URL: http://{self.host}:{self.port}")
        print(f"🔌 MCP Endpoint: http://{self.host}:{self.port}/mcp")
        print(f"🏥 Health Check: http://{self.host}:{self.port}/health")
        print(f"🔧 Tools Available: {len(self.mcp._tools)}")
        
        # Run FastMCP with HTTP transport
        await self.mcp.run(
            transport="http",
            host=self.host,
            port=self.port,
            path="/mcp"
        )

async def main():
    """Main entry point for HTTP MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gemini HTTP MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    
    server = GeminiHTTPMCPServer(host=args.host, port=args.port)
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())

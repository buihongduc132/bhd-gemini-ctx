#!/usr/bin/env python3
"""
Simple HTTP MCP Server for Gemini Context Extraction
A lightweight HTTP API that provides MCP-like functionality without complex dependencies.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

# FastAPI imports
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("⚠️ FastAPI not available. Install with: pip install fastapi uvicorn")

from .config import get_config
from .enhanced_gemini_extractor import EnhancedGeminiExtractor
from .conversation_analyzer import ConversationAnalyzer

# Pydantic models for request/response
class ExtractRequest(BaseModel):
    url: str
    title: str = ""

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class AnalyzeRequest(BaseModel):
    include_details: bool = True

class ListRequest(BaseModel):
    include_metadata: bool = True

class ConversationDetailsRequest(BaseModel):
    conversation_id: str

class ToolCallRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any]

class SimpleHTTPMCPServer:
    """Simple HTTP MCP server for Gemini conversation extraction."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI is required. Install with: pip install fastapi uvicorn")
        
        self.config = get_config()
        self.host = host
        self.port = port
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Gemini Context Extractor HTTP API",
            description="HTTP API for Gemini conversation extraction and analysis",
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
        
        # Setup routes
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/")
        async def root():
            """API information endpoint."""
            return {
                "service": "Gemini Context Extractor HTTP API",
                "version": "1.0.0",
                "status": "running",
                "endpoints": {
                    "extract": "POST /extract",
                    "search": "POST /search", 
                    "analyze": "POST /analyze",
                    "list": "POST /list",
                    "details": "POST /details",
                    "tool_call": "POST /tool",
                    "health": "GET /health"
                },
                "config": {
                    "cdp_port": self.config.browser.cdp_port,
                    "output_dir": self.config.extraction.output_dir
                }
            }
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": "gemini-context-extractor",
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
        
        @self.app.post("/extract")
        async def extract_conversation(request: ExtractRequest):
            """Extract a conversation from URL."""
            try:
                extractor = EnhancedGeminiExtractor(
                    cdp_port=self.config.browser.cdp_port,
                    output_dir=self.config.extraction.output_dir
                )
                
                result = await extractor.extract_conversation_with_structure(
                    request.url, request.title
                )
                
                return {
                    "success": True,
                    "message": "Conversation extracted successfully",
                    "data": result
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/search")
        async def search_conversations(request: SearchRequest):
            """Search for conversations by query."""
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
                        relevance_score = 0
                        
                        # Check title match
                        if request.query.lower() in title.lower():
                            matches = True
                            relevance_score += 0.5
                        
                        # Check message content
                        message_matches = 0
                        for msg in messages:
                            if request.query.lower() in msg.get("content", "").lower():
                                matches = True
                                message_matches += 1
                        
                        if message_matches > 0:
                            relevance_score += min(message_matches * 0.1, 0.5)
                        
                        if matches:
                            results.append({
                                "title": title,
                                "url": data.get("url", ""),
                                "message_count": data.get("message_count", 0),
                                "file": str(json_file),
                                "extracted_at": data.get("extracted_at", ""),
                                "relevance_score": round(relevance_score, 2),
                                "message_matches": message_matches
                            })
                        
                        if len(results) >= request.limit:
                            break
                    
                    except Exception as e:
                        logging.warning(f"Error reading {json_file}: {e}")
                
                # Sort by relevance score
                results.sort(key=lambda x: x["relevance_score"], reverse=True)
                
                return {
                    "success": True,
                    "query": request.query,
                    "results": results,
                    "count": len(results)
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/analyze")
        async def analyze_conversations(request: AnalyzeRequest):
            """Analyze all extracted conversations."""
            try:
                analyzer = ConversationAnalyzer(self.config.extraction.output_dir)
                summary, analyses = analyzer.analyze_all_conversations()
                
                result = {"summary": summary}
                if request.include_details:
                    result["detailed_analyses"] = analyses
                
                return {
                    "success": True,
                    "message": "Analysis completed successfully",
                    "data": result
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/list")
        async def list_conversations(request: ListRequest):
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
                        
                        if request.include_metadata:
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
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/details")
        async def get_conversation_details(request: ConversationDetailsRequest):
            """Get detailed information about a specific conversation."""
            try:
                extracts_dir = Path(self.config.extraction.output_dir)
                json_file = extracts_dir / f"{request.conversation_id}.json"
                
                if not json_file.exists():
                    json_file = extracts_dir / f"structured_{request.conversation_id}.json"
                
                if not json_file.exists():
                    raise HTTPException(status_code=404, detail=f"Conversation not found: {request.conversation_id}")
                
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                return {
                    "success": True,
                    "conversation": data
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/tool")
        async def call_tool(request: ToolCallRequest):
            """Generic tool call endpoint for MCP-like functionality."""
            try:
                tool = request.tool
                args = request.arguments
                
                if tool == "extract_conversation":
                    extract_req = ExtractRequest(**args)
                    return await extract_conversation(extract_req)
                elif tool == "search_conversations":
                    search_req = SearchRequest(**args)
                    return await search_conversations(search_req)
                elif tool == "analyze_conversations":
                    analyze_req = AnalyzeRequest(**args)
                    return await analyze_conversations(analyze_req)
                elif tool == "list_conversations":
                    list_req = ListRequest(**args)
                    return await list_conversations(list_req)
                elif tool == "get_conversation_details":
                    details_req = ConversationDetailsRequest(**args)
                    return await get_conversation_details(details_req)
                else:
                    raise HTTPException(status_code=400, detail=f"Unknown tool: {tool}")
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    def run(self):
        """Run the HTTP server."""
        print(f"🚀 Starting Gemini HTTP API Server...")
        print(f"📍 Server URL: http://{self.host}:{self.port}")
        print(f"🏥 Health Check: http://{self.host}:{self.port}/health")
        print(f"📖 API Docs: http://{self.host}:{self.port}/docs")
        print(f"🔧 Endpoints: /extract, /search, /analyze, /list, /details, /tool")

        uvicorn.run(self.app, host=self.host, port=self.port)

def main():
    """Main entry point for HTTP server."""
    import argparse

    parser = argparse.ArgumentParser(description="Gemini Simple HTTP API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")

    args = parser.parse_args()

    server = SimpleHTTPMCPServer(host=args.host, port=args.port)
    server.run()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
CLI interface for Gemini Context Extraction
Provides command-line access to all extraction and analysis features.
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from typing import Optional, List

from .config import get_config, save_config, create_default_config, print_config, GeminiConfig
from .enhanced_gemini_extractor import EnhancedGeminiExtractor
from .conversation_analyzer import ConversationAnalyzer
from .search_based_extractor import SearchBasedExtractor

class GeminiCLI:
    """Command-line interface for Gemini extraction tools."""
    
    def __init__(self):
        self.config = get_config()
    
    async def extract_conversation(self, url: str, title: str = "") -> dict:
        """Extract a single conversation."""
        extractor = EnhancedGeminiExtractor(
            cdp_port=self.config.browser.cdp_port,
            output_dir=self.config.extraction.output_dir
        )
        
        result = await extractor.extract_conversation_with_structure(url, title)
        return result
    
    async def search_conversations(self, query: str, limit: int = 10) -> dict:
        """Search for conversations."""
        extractor = SearchBasedExtractor(
            cdp_port=self.config.browser.cdp_port,
            output_dir=self.config.extraction.output_dir
        )
        
        result = await extractor.search_conversations(query, limit)
        return result
    
    def analyze_conversations(self, output_format: str = "text") -> dict:
        """Analyze all extracted conversations."""
        analyzer = ConversationAnalyzer(self.config.extraction.output_dir)
        summary, analyses = analyzer.analyze_all_conversations()
        
        if output_format == "json":
            return {"summary": summary, "analyses": analyses}
        elif output_format == "text":
            analyzer.print_summary_report(summary)
            return summary
        
        return summary
    
    def list_conversations(self) -> List[dict]:
        """List all extracted conversations."""
        extracts_dir = Path(self.config.extraction.output_dir)
        conversations = []
        
        for json_file in extracts_dir.glob("structured_*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    conversations.append({
                        "file": str(json_file),
                        "title": data.get("title", "Unknown"),
                        "url": data.get("url", ""),
                        "message_count": data.get("message_count", 0),
                        "extracted_at": data.get("extracted_at", "")
                    })
            except Exception as e:
                print(f"⚠️ Error reading {json_file}: {e}")
        
        return conversations
    
    def configure(self, **kwargs) -> None:
        """Update configuration."""
        # Update browser config
        for key, value in kwargs.items():
            if hasattr(self.config.browser, key):
                setattr(self.config.browser, key, value)
            elif hasattr(self.config.extraction, key):
                setattr(self.config.extraction, key, value)
        
        save_config(self.config)
        print("✅ Configuration updated")

def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Gemini Context Extraction CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract a specific conversation
  gemini-cli extract https://gemini.google.com/app/abc123 --title "My Conversation"
  
  # Search for conversations about memory
  gemini-cli search "memory" --limit 5
  
  # Analyze all conversations
  gemini-cli analyze --format json
  
  # List all extracted conversations
  gemini-cli list
  
  # Configure browser settings
  gemini-cli config --cdp-port 9223 --user-data-dir /path/to/profile
  
  # Show current configuration
  gemini-cli config --show
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract a conversation')
    extract_parser.add_argument('url', help='Conversation URL')
    extract_parser.add_argument('--title', '-t', default='', help='Conversation title')
    extract_parser.add_argument('--format', '-f', choices=['json', 'markdown', 'html'], 
                               default='json', help='Output format')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search conversations')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', '-l', type=int, default=10, help='Max results')
    search_parser.add_argument('--extract', '-e', action='store_true', 
                              help='Extract found conversations')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze conversations')
    analyze_parser.add_argument('--format', '-f', choices=['json', 'text'], 
                               default='text', help='Output format')
    analyze_parser.add_argument('--file', help='Analyze specific conversation file')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List extracted conversations')
    list_parser.add_argument('--format', '-f', choices=['json', 'table'], 
                            default='table', help='Output format')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_parser.add_argument('--show', action='store_true', help='Show current config')
    config_parser.add_argument('--create-default', action='store_true',
                              help='Create default config file')
    config_parser.add_argument('--cdp-port', type=int, help='Chrome CDP port')
    config_parser.add_argument('--user-data-dir', help='Chrome user data directory')
    config_parser.add_argument('--headless', action='store_true', help='Enable headless mode')
    config_parser.add_argument('--output-dir', help='Output directory')
    config_parser.add_argument('--timeout', type=int, help='Browser timeout (ms)')

    # HTTP MCP Server command
    http_mcp_parser = subparsers.add_parser('http-mcp', help='Start HTTP MCP server')
    http_mcp_parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    http_mcp_parser.add_argument('--port', type=int, default=8000, help='Port to bind to')

    return parser

async def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = GeminiCLI()
    
    try:
        if args.command == 'extract':
            print(f"🔄 Extracting conversation: {args.url}")
            result = await cli.extract_conversation(args.url, args.title)
            
            if args.format == 'json':
                print(json.dumps(result, indent=2))
            else:
                print(f"✅ Extraction complete: {result}")
        
        elif args.command == 'search':
            print(f"🔍 Searching for: {args.query}")
            result = await cli.search_conversations(args.query, args.limit)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'analyze':
            print("📊 Analyzing conversations...")
            result = cli.analyze_conversations(args.format)
            
            if args.format == 'json':
                print(json.dumps(result, indent=2))
        
        elif args.command == 'list':
            conversations = cli.list_conversations()
            
            if args.format == 'json':
                print(json.dumps(conversations, indent=2))
            else:
                print("\n📚 Extracted Conversations:")
                print("=" * 80)
                for conv in conversations:
                    print(f"📄 {conv['title']}")
                    print(f"   Messages: {conv['message_count']}")
                    print(f"   File: {conv['file']}")
                    print(f"   Extracted: {conv['extracted_at']}")
                    print()
        
        elif args.command == 'config':
            if args.show:
                print_config()
            elif args.create_default:
                create_default_config()
            else:
                # Update configuration
                config_updates = {}
                if args.cdp_port:
                    config_updates['cdp_port'] = args.cdp_port
                if args.user_data_dir:
                    config_updates['user_data_dir'] = args.user_data_dir
                if args.headless:
                    config_updates['headless'] = args.headless
                if args.output_dir:
                    config_updates['output_dir'] = args.output_dir
                if args.timeout:
                    config_updates['timeout'] = args.timeout

                if config_updates:
                    cli.configure(**config_updates)
                else:
                    print_config()

        elif args.command == 'http-mcp':
            print(f"🚀 Starting HTTP API Server on {args.host}:{args.port}")
            try:
                from .simple_http_mcp import SimpleHTTPMCPServer
                server = SimpleHTTPMCPServer(host=args.host, port=args.port)
                server.run()
            except ImportError as e:
                print(f"❌ Error: {e}")
                print("💡 Install FastAPI dependencies: pip install fastapi uvicorn")
            except Exception as e:
                print(f"❌ Error starting HTTP API server: {e}")
    
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def cli_entry_point():
    """Entry point for CLI script."""
    asyncio.run(main())

if __name__ == "__main__":
    cli_entry_point()

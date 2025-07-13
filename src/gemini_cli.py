#!/usr/bin/env python3
"""
Comprehensive CLI for Gemini conversation extraction.
Based on actual DOM inspection and working selectors.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

class GeminiCLI:
    def __init__(self, cdp_port: int = 9222):
        self.cdp_port = cdp_port
        self.cdp_url = f"http://localhost:{cdp_port}"
        self.output_dir = Path("flow/gemini_extracts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def connect(self):
        """Connect to existing Chrome browser."""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(self.cdp_url)
        
        contexts = browser.contexts
        if contexts:
            context = contexts[0]
            pages = context.pages
            if pages:
                page = pages[0]
            else:
                page = await context.new_page()
        else:
            context = await browser.new_context()
            page = await context.new_page()
        
        return playwright, browser, page
    
    async def save_results(self, data: dict, filename: str):
        """Save results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"{filename}_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Results saved to: {output_file}")
        return output_file
    
    async def list_conversations(self):
        """List all recent conversations."""
        print("🔍 Listing recent conversations...")
        
        playwright, browser, page = await self.connect()
        
        try:
            # Navigate to Gemini app
            await page.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(3000)
            
            # Open sidebar
            try:
                menu_button = await page.query_selector('button[data-test-id="side-nav-menu-button"]')
                if menu_button:
                    await menu_button.click()
                    await page.wait_for_timeout(2000)
                    print("✅ Opened sidebar")
            except Exception as e:
                print(f"⚠️ Could not open sidebar: {e}")
            
            # Extract conversations using working selectors
            conversations = []
            all_buttons = await page.query_selector_all('button')
            
            for i, button in enumerate(all_buttons):
                try:
                    text = await button.text_content()
                    if text and text.strip():
                        text_clean = text.strip()
                        # Filter out non-conversation buttons
                        if (len(text_clean) > 5 and 
                            text_clean not in ['New chat', 'Search for chats', 'Settings & help', 'Sign in', 'Main menu', '2.5 Pro', 'Invite a friend', 'PRO'] and
                            not text_clean.startswith('2.5')):
                            
                            conversations.append({
                                "id": f"button_conv_{i+1}",
                                "title": text_clean,
                                "button_index": i,
                                "url": f"https://gemini.google.com/app/conversation_{i+1}"
                            })
                except:
                    pass
            
            # Save and display results
            results = {
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "task": "list_conversations",
                "url": page.url,
                "conversations_count": len(conversations),
                "conversations": conversations
            }
            
            await self.save_results(results, "conversations_list")
            
            print(f"✅ Found {len(conversations)} conversations:")
            for i, conv in enumerate(conversations):
                print(f"  {i+1}. [{conv['button_index']}] {conv['title']}")
            
            return results
            
        finally:
            await playwright.stop()
    
    async def search_conversations(self, query: str):
        """Search conversations for a specific query."""
        print(f"🔍 Searching conversations for: '{query}'")
        
        # Get all conversations first
        all_conversations_data = await self.list_conversations()
        all_conversations = all_conversations_data.get("conversations", [])
        
        # Filter conversations that contain the query
        matching_conversations = []
        for conv in all_conversations:
            if query.lower() in conv['title'].lower():
                matching_conversations.append(conv)
        
        # Save and display results
        results = {
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "task": "search_conversations",
            "query": query,
            "total_conversations_searched": len(all_conversations),
            "matching_conversations_count": len(matching_conversations),
            "matching_conversations": matching_conversations,
            "first_result": matching_conversations[0] if matching_conversations else None
        }
        
        await self.save_results(results, f"conversation_search_{query}")
        
        print(f"✅ Found {len(matching_conversations)} conversations matching '{query}':")
        for i, conv in enumerate(matching_conversations):
            print(f"  {i+1}. [{conv['button_index']}] {conv['title']}")
        
        return results
    
    async def extract_conversation(self, button_index: int):
        """Extract conversation content by button index."""
        print(f"📄 Extracting conversation from button index {button_index}...")
        
        playwright, browser, page = await self.connect()
        
        try:
            # Navigate to Gemini app
            await page.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(3000)
            
            # Open sidebar
            try:
                menu_button = await page.query_selector('button[data-test-id="side-nav-menu-button"]')
                if menu_button:
                    await menu_button.click()
                    await page.wait_for_timeout(2000)
            except:
                pass
            
            # Find and click the specific conversation button
            all_buttons = await page.query_selector_all('button')
            if button_index >= len(all_buttons):
                print(f"❌ Button index {button_index} not found (max: {len(all_buttons)-1})")
                return None
            
            target_button = all_buttons[button_index]
            button_text = await target_button.text_content()
            print(f"🎯 Clicking conversation: '{button_text.strip()}'")
            
            await target_button.click()
            await page.wait_for_timeout(5000)  # Wait for conversation to load
            
            # Scroll to top to get complete conversation history
            print("🔄 Scrolling to load complete conversation...")
            for i in range(15):
                await page.keyboard.press('Home')
                await page.wait_for_timeout(300)
                await page.evaluate('window.scrollTo(0, 0)')
                await page.wait_for_timeout(300)
            
            # Wait for content to stabilize
            await page.wait_for_timeout(3000)
            
            # Extract conversation content
            # Focus on the main conversation area, not the sidebar
            main_content = await page.query_selector('main')
            if not main_content:
                print("❌ Could not find main content area")
                return None
            
            # Get the page content and filter out sidebar content
            page_text = await page.evaluate('''() => {
                // Remove sidebar content
                const sidebar = document.querySelector('nav, aside, [role="navigation"]');
                if (sidebar) {
                    sidebar.style.display = 'none';
                }
                
                // Get main content text
                const main = document.querySelector('main');
                return main ? main.innerText : document.body.innerText;
            }''')
            
            # Create markdown content
            conv_id = button_text.strip().replace(' ', '_').replace(':', '')[:20]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            markdown_content = f"""# Gemini Conversation: {button_text.strip()}

**Extracted:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**URL:** {page.url}
**Button Index:** {button_index}

---

{page_text}

---

*Extracted using Playwright DOM inspection*
*Note: Content may include UI elements - manual cleanup may be needed*
"""
            
            # Save markdown file
            markdown_file = self.output_dir / f"conversation_{conv_id}_{timestamp}.md"
            with open(markdown_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Save raw data
            raw_data = {
                "timestamp": timestamp,
                "task": "extract_conversation",
                "button_index": button_index,
                "conversation_title": button_text.strip(),
                "url": page.url,
                "content_length": len(page_text),
                "raw_content": page_text[:5000]  # First 5000 chars
            }
            
            await self.save_results(raw_data, f"conversation_raw_{conv_id}")
            
            print(f"✅ Conversation extracted successfully")
            print(f"📄 Markdown saved to: {markdown_file}")
            print(f"📊 Content length: {len(page_text)} characters")
            
            return raw_data
            
        finally:
            await playwright.stop()
    
    async def run_complete_extraction(self):
        """Run the complete extraction process as specified in WS_TODO.md."""
        print("🚀 Starting complete Gemini extraction process...")
        print("=" * 60)
        
        results = {}
        
        try:
            # 1. List conversations
            print("\nSTEP 1: Listing recent conversations")
            print("-" * 40)
            results['conversations'] = await self.list_conversations()
            
            # 2. Search for "dy" conversations
            print("\nSTEP 2: Searching for 'dy' conversations")
            print("-" * 40)
            results['dy_search'] = await self.search_conversations("dy")
            
            # 3. Extract first "dy" conversation if found
            dy_conversations = results['dy_search'].get('matching_conversations', [])
            if dy_conversations:
                first_dy_conv = dy_conversations[0]
                button_index = first_dy_conv['button_index']
                
                print(f"\nSTEP 3: Extracting first 'dy' conversation")
                print("-" * 40)
                results['extracted_conversation'] = await self.extract_conversation(button_index)
            
            # Save complete summary
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary = {
                "timestamp": timestamp,
                "task": "complete_extraction",
                "summary": {
                    "total_conversations": results.get('conversations', {}).get('conversations_count', 0),
                    "dy_conversations_found": results.get('dy_search', {}).get('matching_conversations_count', 0),
                    "conversation_extracted": bool(results.get('extracted_conversation'))
                },
                "results": results
            }
            
            await self.save_results(summary, "complete_extraction_summary")
            
            print("\n" + "=" * 60)
            print("EXTRACTION COMPLETE")
            print("=" * 60)
            print(f"✅ Total conversations found: {summary['summary']['total_conversations']}")
            print(f"✅ 'dy' conversations found: {summary['summary']['dy_conversations_found']}")
            print(f"✅ Conversation extracted: {summary['summary']['conversation_extracted']}")
            
        except Exception as e:
            print(f"❌ Error during complete extraction: {e}")

def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python gemini_cli.py list-conversations")
        print("  python gemini_cli.py search-conversations <query>")
        print("  python gemini_cli.py extract-conversation <button_index>")
        print("  python gemini_cli.py complete-extraction")
        return
    
    cli = GeminiCLI()
    command = sys.argv[1]
    
    if command == "list-conversations":
        asyncio.run(cli.list_conversations())
    elif command == "search-conversations" and len(sys.argv) > 2:
        query = sys.argv[2]
        asyncio.run(cli.search_conversations(query))
    elif command == "extract-conversation" and len(sys.argv) > 2:
        button_index = int(sys.argv[2])
        asyncio.run(cli.extract_conversation(button_index))
    elif command == "complete-extraction":
        asyncio.run(cli.run_complete_extraction())
    else:
        print("❌ Invalid command or missing arguments")

if __name__ == "__main__":
    main()

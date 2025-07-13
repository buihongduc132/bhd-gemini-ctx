#!/usr/bin/env python3
"""
Final Gemini Extractor - Correctly distinguishes gems vs conversations and includes search functionality.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False

class FinalGeminiExtractor:
    def __init__(self, cdp_port: int = 9222):
        self.cdp_port = cdp_port
        self.cdp_url = f"http://localhost:{cdp_port}"
        self.output_dir = Path("flow/gemini_extracts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.markitdown = MarkItDown() if MARKITDOWN_AVAILABLE else None
    
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
    
    async def wait_for_network_stability(self, page, timeout=30000):
        """Wait for network to be stable."""
        print("⏳ Waiting for network stability...")
        try:
            await page.wait_for_load_state('networkidle', timeout=timeout)
            print("✅ Network is stable")
        except Exception as e:
            print(f"⚠️ Network stability timeout: {e}")
        await page.wait_for_timeout(2000)
    
    async def get_gems_list(self):
        """Get list of gems (custom apps)."""
        print("💎 Getting gems list...")
        
        playwright, browser, page = await self.connect()
        
        try:
            # Navigate to Gemini app
            await page.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=15000)
            await self.wait_for_network_stability(page)
            
            # Open sidebar
            try:
                menu_button = await page.query_selector('button[data-test-id="side-nav-menu-button"]')
                if menu_button:
                    await menu_button.click()
                    await page.wait_for_timeout(2000)
                    await self.wait_for_network_stability(page, timeout=10000)
            except Exception as e:
                print(f"⚠️ Error opening sidebar: {e}")
            
            # Look for gems (items with colons, custom apps)
            gems = []
            all_buttons = await page.query_selector_all('button')
            
            for i, button in enumerate(all_buttons):
                try:
                    text = await button.text_content()
                    if text and text.strip():
                        text_clean = text.strip()
                        
                        # Gems typically have colons and are custom apps
                        if (len(text_clean) > 5 and 
                            ':' in text_clean and
                            text_clean not in ['New chat', 'Search for chats', 'Settings & help'] and
                            not text_clean.startswith('2.5')):
                            
                            gems.append({
                                "index": len(gems) + 1,
                                "button_index": i,
                                "title": text_clean,
                                "type": "gem"
                            })
                except:
                    continue
            
            print(f"✅ Found {len(gems)} gems:")
            for gem in gems:
                print(f"  {gem['index']}. [{gem['button_index']}] {gem['title']}")
            
            return gems
            
        finally:
            await playwright.stop()
    
    async def get_recent_conversations(self):
        """Get actual recent conversations (not gems)."""
        print("💬 Getting recent conversations...")
        
        playwright, browser, page = await self.connect()
        
        try:
            # Navigate to Gemini app
            await page.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=15000)
            await self.wait_for_network_stability(page)
            
            # Open sidebar
            try:
                menu_button = await page.query_selector('button[data-test-id="side-nav-menu-button"]')
                if menu_button:
                    await menu_button.click()
                    await page.wait_for_timeout(2000)
                    await self.wait_for_network_stability(page, timeout=10000)
            except Exception as e:
                print(f"⚠️ Error opening sidebar: {e}")
            
            # Look for actual conversations (not gems)
            conversations = []
            all_buttons = await page.query_selector_all('button')
            
            for i, button in enumerate(all_buttons):
                try:
                    text = await button.text_content()
                    if text and text.strip():
                        text_clean = text.strip()
                        
                        # Conversations are typically:
                        # - Don't have colons (gems have colons)
                        # - Are not UI elements
                        # - Have substantial text
                        if (len(text_clean) > 10 and 
                            ':' not in text_clean and  # No colons = not a gem
                            text_clean not in ['New chat', 'Search for chats', 'Settings & help', 'Sign in', 'Main menu', '2.5 Pro', 'Invite a friend', 'PRO', 'Gemini', 'Try Gemini Advanced'] and
                            not text_clean.startswith('2.5') and
                            not text_clean.startswith('Gemini')):
                            
                            conversations.append({
                                "index": len(conversations) + 1,
                                "button_index": i,
                                "title": text_clean,
                                "type": "conversation"
                            })
                except:
                    continue
            
            print(f"✅ Found {len(conversations)} recent conversations:")
            for conv in conversations:
                print(f"  {conv['index']}. [{conv['button_index']}] {conv['title']}")
            
            return conversations
            
        finally:
            await playwright.stop()
    
    async def search_conversations(self, query: str):
        """Search for conversations using the search page."""
        print(f"🔍 Searching conversations for: '{query}'")
        
        playwright, browser, page = await self.connect()
        
        try:
            # Navigate to search page
            print("📍 Navigating to search page...")
            await page.goto("https://gemini.google.com/search", wait_until="domcontentloaded", timeout=15000)
            await self.wait_for_network_stability(page)
            
            # Find search input and enter query
            search_input = await page.query_selector('input[type="text"], input[placeholder*="search"], textarea')
            if search_input:
                print(f"🔍 Entering search query: '{query}'")
                await search_input.fill(query)
                await page.keyboard.press('Enter')
                await self.wait_for_network_stability(page)
            else:
                print("❌ Could not find search input")
                return []
            
            # Extract search results
            search_results = []
            
            # Look for conversation results with various selectors
            result_selectors = [
                '[data-testid*="result"]',
                '.search-result',
                '.conversation-result',
                'article',
                'div[role="button"]',
                'a[href*="conversation"]',
                'button'
            ]
            
            for selector in result_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"Found {len(elements)} elements with selector: {selector}")
                        
                        for i, element in enumerate(elements):
                            try:
                                text = await element.text_content()
                                href = await element.get_attribute('href')
                                
                                if text and len(text.strip()) > 20:
                                    search_results.append({
                                        "index": i + 1,
                                        "title": text.strip()[:200],
                                        "url": href or "N/A",
                                        "selector": selector
                                    })
                            except:
                                continue
                        
                        if search_results:
                            break
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
            
            print(f"✅ Found {len(search_results)} search results:")
            for result in search_results[:10]:  # Show first 10
                print(f"  {result['index']}. {result['title'][:100]}...")
            
            return search_results
            
        finally:
            await playwright.stop()
    
    async def extract_conversation_content(self, button_index: int, source_type: str = "recent"):
        """Extract conversation content, filtering out suggestions."""
        print(f"📄 Extracting conversation from button index {button_index} ({source_type})...")
        
        playwright, browser, page = await self.connect()
        
        try:
            if source_type == "recent":
                # Navigate to main app for recent conversations
                await page.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=15000)
                await self.wait_for_network_stability(page)
                
                # Open sidebar
                try:
                    menu_button = await page.query_selector('button[data-test-id="side-nav-menu-button"]')
                    if menu_button:
                        await menu_button.click()
                        await page.wait_for_timeout(2000)
                        await self.wait_for_network_stability(page, timeout=10000)
                except Exception as e:
                    print(f"⚠️ Error opening sidebar: {e}")
                
                # Click the conversation
                all_buttons = await page.query_selector_all('button')
                if button_index >= len(all_buttons):
                    print(f"❌ Button index {button_index} not found")
                    return None
                
                target_button = all_buttons[button_index]
                button_text = await target_button.text_content()
                print(f"🎯 Clicking: '{button_text.strip()}'")
                
                await target_button.click(force=True)
                await page.wait_for_timeout(5000)
                await self.wait_for_network_stability(page, timeout=20000)
            
            # Scroll to get complete history
            print("🔄 Scrolling to load complete conversation...")
            for i in range(20):
                await page.keyboard.press('Home')
                await page.wait_for_timeout(200)
            await self.wait_for_network_stability(page, timeout=15000)
            
            # Extract conversation content, filtering out suggestions
            print("📄 Extracting conversation content (filtering suggestions)...")
            conversation_html = await page.evaluate('''() => {
                const main = document.querySelector('main');
                if (!main) return null;
                
                // Look for actual conversation messages
                const messageSelectors = [
                    '[data-message-id]',
                    'article',
                    '.message',
                    '[role="article"]',
                    '.conversation-turn'
                ];
                
                let messageElements = [];
                for (const selector of messageSelectors) {
                    const elements = main.querySelectorAll(selector);
                    if (elements.length > 0) {
                        messageElements = Array.from(elements);
                        break;
                    }
                }
                
                // Filter out suggestion prompts and UI elements
                const filteredElements = [];
                messageElements.forEach(element => {
                    const text = element.textContent || '';
                    
                    // Skip if it's a suggestion prompt
                    if (text.includes('Compare teachings') || 
                        text.includes('Analyze consequences') ||
                        text.includes('Illustrate Python') ||
                        text.includes('Simulate a virtual') ||
                        text.includes('Hello, Duc') ||
                        text.length < 20) {
                        return;
                    }
                    
                    filteredElements.push(element);
                });
                
                // If we have filtered elements, use them
                if (filteredElements.length > 0) {
                    let content = '';
                    filteredElements.forEach((element, index) => {
                        content += `<div class="message-${index}">${element.outerHTML}</div>`;
                    });
                    return content;
                }
                
                // Otherwise, get all content but filter text
                return main.outerHTML;
            }''')
            
            if not conversation_html or len(conversation_html.strip()) < 50:
                print("⚠️ Limited content, getting full page...")
                conversation_html = await page.evaluate('''() => {
                    const main = document.querySelector('main');
                    return main ? main.innerHTML : document.body.innerHTML;
                }''')
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            conv_id = f"conversation_{button_index}_{source_type}"
            
            # Save raw HTML
            html_file = self.output_dir / f"final_{conv_id}_{timestamp}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Final Extraction: {source_type} {button_index}</title>
</head>
<body>
    <h1>Final Gemini Extraction</h1>
    <p><strong>Extracted:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>URL:</strong> {page.url}</p>
    <p><strong>Source:</strong> {source_type}</p>
    <p><strong>Content Length:</strong> {len(conversation_html)} characters</p>
    <hr>
    {conversation_html}
</body>
</html>""")
            
            print(f"✅ Final extraction saved to: {html_file}")
            print(f"📊 Content length: {len(conversation_html)} characters")
            
            # Convert to markdown
            if self.markitdown and len(conversation_html) > 100:
                try:
                    result = self.markitdown.convert(str(html_file))
                    
                    # Clean the markdown content
                    cleaned_content = self._clean_markdown_content(result.text_content)
                    
                    markdown_file = self.output_dir / f"final_{conv_id}_{timestamp}.md"
                    with open(markdown_file, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    print(f"✅ Cleaned markdown saved to: {markdown_file}")
                except Exception as e:
                    print(f"⚠️ Markdown conversion error: {e}")
            
            return {
                "source_type": source_type,
                "button_index": button_index,
                "url": page.url,
                "html_file": str(html_file),
                "content_length": len(conversation_html),
                "timestamp": timestamp
            }
            
        finally:
            await playwright.stop()
    
    def _clean_markdown_content(self, content: str) -> str:
        """Clean markdown content by removing suggestions and UI elements."""
        lines = content.split('\n')
        cleaned_lines = []
        
        # Add header
        cleaned_lines.extend([
            f"# Gemini Conversation Extract",
            "",
            f"**Extracted:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            ""
        ])
        
        # Filter content
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and suggestions
            if not line:
                continue
            
            # Skip suggestion prompts
            if any(suggestion in line for suggestion in [
                'Compare teachings', 'Analyze consequences', 'Illustrate Python',
                'Simulate a virtual', 'Hello, Duc'
            ]):
                continue
            
            # Skip UI elements
            if any(ui in line.lower() for ui in [
                'menu', 'button', 'search', 'settings', 'gemini', 'new chat'
            ]):
                continue
            
            # Add meaningful content
            if len(line) > 10:
                cleaned_lines.append(line)
        
        cleaned_lines.extend([
            "",
            "---",
            "",
            "*Extracted with suggestion filtering*"
        ])
        
        return '\n'.join(cleaned_lines)

async def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python final_gemini_extractor.py list-gems")
        print("  python final_gemini_extractor.py list-conversations")
        print("  python final_gemini_extractor.py search <query>")
        print("  python final_gemini_extractor.py extract-recent <button_index>")
        return
    
    extractor = FinalGeminiExtractor()
    command = sys.argv[1]
    
    if command == "list-gems":
        await extractor.get_gems_list()
    elif command == "list-conversations":
        await extractor.get_recent_conversations()
    elif command == "search" and len(sys.argv) > 2:
        query = sys.argv[2]
        await extractor.search_conversations(query)
    elif command == "extract-recent" and len(sys.argv) > 2:
        button_index = int(sys.argv[2])
        await extractor.extract_conversation_content(button_index, "recent")
    else:
        print("❌ Invalid command or missing arguments")

if __name__ == "__main__":
    asyncio.run(main())

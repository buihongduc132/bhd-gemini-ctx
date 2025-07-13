#!/usr/bin/env python3
"""
Improved Gemini Conversation Extractor with proper network waiting and content loading.
Addresses the issues with dynamic content loading and network stability.
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

class ImprovedGeminiExtractor:
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
        """Wait for network to be stable (no requests for 2 seconds)."""
        print("⏳ Waiting for network stability...")
        
        try:
            # Wait for network to be idle (no requests for 2 seconds)
            await page.wait_for_load_state('networkidle', timeout=timeout)
            print("✅ Network is stable")
        except Exception as e:
            print(f"⚠️ Network stability timeout: {e}")
        
        # Additional wait for any WebSocket or dynamic content
        await page.wait_for_timeout(3000)
    
    async def get_conversations_list(self):
        """Get list of available conversations with proper waiting."""
        print("🔍 Getting conversations list...")
        
        playwright, browser, page = await self.connect()
        
        try:
            # Navigate to Gemini app
            print("📍 Navigating to Gemini app...")
            await page.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=15000)
            
            # Wait for network stability
            await self.wait_for_network_stability(page)
            
            # Open sidebar
            print("📂 Opening sidebar...")
            try:
                menu_button = await page.query_selector('button[data-test-id="side-nav-menu-button"]')
                if menu_button:
                    await menu_button.click()
                    await page.wait_for_timeout(2000)
                    # Wait for sidebar content to load
                    await self.wait_for_network_stability(page, timeout=10000)
            except Exception as e:
                print(f"⚠️ Error opening sidebar: {e}")
            
            # Extract conversations with better filtering
            conversations = []
            all_buttons = await page.query_selector_all('button')
            
            print(f"🔍 Found {len(all_buttons)} total buttons, filtering for conversations...")
            
            for i, button in enumerate(all_buttons):
                try:
                    text = await button.text_content()
                    if text and text.strip():
                        text_clean = text.strip()
                        
                        # More specific filtering for conversation buttons
                        if (len(text_clean) > 5 and 
                            text_clean not in ['New chat', 'Search for chats', 'Settings & help', 'Sign in', 'Main menu', '2.5 Pro', 'Invite a friend', 'PRO', 'Gemini', 'Try Gemini Advanced'] and
                            not text_clean.startswith('2.5') and
                            not text_clean.startswith('Gemini') and
                            ':' in text_clean):  # Conversations often have colons
                            
                            conversations.append({
                                "index": len(conversations) + 1,
                                "button_index": i,
                                "title": text_clean,
                                "url": f"https://gemini.google.com/app/conversation_{i}"
                            })
                except Exception as e:
                    continue
            
            print(f"✅ Found {len(conversations)} conversations:")
            for conv in conversations:
                print(f"  {conv['index']}. [{conv['button_index']}] {conv['title']}")
            
            return conversations
            
        finally:
            await playwright.stop()
    
    async def count_gems(self):
        """Count how many gems are visible."""
        print("💎 Counting gems...")
        
        playwright, browser, page = await self.connect()
        
        try:
            # Navigate to gems page
            print("📍 Navigating to gems page...")
            await page.goto("https://gemini.google.com/gems", wait_until="domcontentloaded", timeout=15000)
            
            # Wait for network stability
            await self.wait_for_network_stability(page)
            
            # Look for gem elements with various selectors
            gem_selectors = [
                '[data-testid*="gem"]',
                '.gem-card',
                '.gem-item',
                'article',
                '.card',
                '[role="button"]:has-text("gem")',
                'div[data-gem-id]'
            ]
            
            total_gems = 0
            gems_found = []
            
            for selector in gem_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"Found {len(elements)} elements with selector: {selector}")
                        
                        for i, element in enumerate(elements):
                            try:
                                text = await element.text_content()
                                if text and len(text.strip()) > 5:
                                    gems_found.append({
                                        "index": i + 1,
                                        "title": text.strip()[:100],
                                        "selector": selector
                                    })
                            except:
                                continue
                        
                        total_gems = len(gems_found)
                        break
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
            
            print(f"✅ Found {total_gems} gems total")
            for gem in gems_found[:10]:  # Show first 10
                print(f"  {gem['index']}. {gem['title']}")
            
            return {
                "total_gems": total_gems,
                "gems": gems_found,
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
            }
            
        finally:
            await playwright.stop()
    
    async def extract_conversation_properly(self, button_index: int):
        """Extract conversation with proper waiting for content to load."""
        print(f"📄 Extracting conversation from button index {button_index}...")
        
        playwright, browser, page = await self.connect()
        
        try:
            # Navigate to Gemini app
            print("📍 Navigating to Gemini app...")
            await page.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=15000)
            
            # Wait for initial network stability
            await self.wait_for_network_stability(page)
            
            # Open sidebar
            print("📂 Opening sidebar...")
            try:
                menu_button = await page.query_selector('button[data-test-id="side-nav-menu-button"]')
                if menu_button:
                    await menu_button.click()
                    await page.wait_for_timeout(2000)
                    await self.wait_for_network_stability(page, timeout=10000)
            except Exception as e:
                print(f"⚠️ Error opening sidebar: {e}")
            
            # Find and click the conversation
            all_buttons = await page.query_selector_all('button')
            if button_index >= len(all_buttons):
                print(f"❌ Button index {button_index} not found (max: {len(all_buttons)-1})")
                return None
            
            target_button = all_buttons[button_index]
            button_text = await target_button.text_content()
            print(f"🎯 Clicking conversation: '{button_text.strip()}'")
            
            # Click the conversation button
            await target_button.click(force=True)
            print("⏳ Waiting for conversation to load...")
            
            # Wait longer for conversation content to load
            await page.wait_for_timeout(5000)
            
            # Wait for network stability after clicking
            await self.wait_for_network_stability(page, timeout=20000)
            
            # Try to wait for message elements to appear
            print("🔍 Looking for message elements...")
            message_selectors = [
                '[data-message-id]',
                'article',
                '.message',
                '[role="article"]',
                '.conversation-turn',
                '.chat-message',
                '[data-testid*="message"]'
            ]
            
            messages_found = False
            for selector in message_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=10000)
                    elements = await page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        print(f"✅ Found {len(elements)} message elements with selector: {selector}")
                        messages_found = True
                        break
                except:
                    continue
            
            if not messages_found:
                print("⚠️ No message elements found, extracting available content...")
            
            # Scroll to top to get complete history
            print("🔄 Scrolling to load complete conversation...")
            for i in range(20):
                await page.keyboard.press('Home')
                await page.wait_for_timeout(200)
                await page.evaluate('window.scrollTo(0, 0)')
                await page.wait_for_timeout(200)
            
            # Wait for any additional content to load after scrolling
            await self.wait_for_network_stability(page, timeout=15000)
            
            # Extract conversation content with safer approach
            print("📄 Extracting conversation content...")
            conversation_html = await page.evaluate('''() => {
                // Find main content area
                const main = document.querySelector('main');
                if (!main) return null;

                // Try to find conversation messages with multiple strategies
                let messageElements = [];

                // Strategy 1: Look for message containers
                const messageSelectors = [
                    '[data-message-id]',
                    'article',
                    '.message',
                    '[role="article"]',
                    '.conversation-turn',
                    '.chat-message',
                    '[data-testid*="message"]',
                    'div[data-test-id*="message"]'
                ];

                for (const selector of messageSelectors) {
                    const elements = main.querySelectorAll(selector);
                    if (elements.length > 0) {
                        messageElements = Array.from(elements);
                        console.log(`Found ${elements.length} elements with selector: ${selector}`);
                        break;
                    }
                }

                // Strategy 2: If no specific message elements, look for content blocks
                if (messageElements.length === 0) {
                    // Look for divs with substantial text content
                    const allDivs = main.querySelectorAll('div');
                    messageElements = Array.from(allDivs).filter(div => {
                        const text = div.textContent || '';
                        return text.trim().length > 50 &&
                               !div.querySelector('button') &&
                               !div.querySelector('nav');
                    });
                    console.log(`Found ${messageElements.length} content divs`);
                }

                // Strategy 3: Get all text content if nothing else works
                if (messageElements.length === 0) {
                    console.log('No message elements found, returning main innerHTML');
                    return main.outerHTML;
                }

                // Extract content safely using outerHTML
                let extractedContent = '';
                messageElements.forEach((element, index) => {
                    extractedContent += `<div class="message-${index}">${element.outerHTML}</div>`;
                });

                return extractedContent || main.outerHTML;
            }''')
            
            if not conversation_html or len(conversation_html.strip()) < 100:
                print("⚠️ Limited content extracted, getting full page content...")
                conversation_html = await page.evaluate('''() => {
                    const main = document.querySelector('main');
                    return main ? main.innerHTML : document.body.innerHTML;
                }''')
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            conv_id = button_text.strip().replace(' ', '_').replace(':', '')[:20]
            
            # Save raw HTML
            html_file = self.output_dir / f"conversation_improved_{conv_id}_{timestamp}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Improved Extraction: {button_text.strip()}</title>
</head>
<body>
    <h1>Improved Gemini Conversation: {button_text.strip()}</h1>
    <p><strong>Extracted:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>URL:</strong> {page.url}</p>
    <p><strong>Content Length:</strong> {len(conversation_html)} characters</p>
    <hr>
    {conversation_html}
</body>
</html>""")
            
            print(f"✅ Improved extraction saved to: {html_file}")
            print(f"📊 Content length: {len(conversation_html)} characters")
            
            # Convert to markdown if markitdown available
            if self.markitdown and len(conversation_html) > 100:
                try:
                    result = self.markitdown.convert(str(html_file))
                    markdown_file = self.output_dir / f"conversation_improved_{conv_id}_{timestamp}.md"
                    with open(markdown_file, 'w', encoding='utf-8') as f:
                        f.write(result.text_content)
                    print(f"✅ Markdown saved to: {markdown_file}")
                except Exception as e:
                    print(f"⚠️ Markdown conversion error: {e}")
            
            return {
                "conversation_title": button_text.strip(),
                "button_index": button_index,
                "url": page.url,
                "html_file": str(html_file),
                "content_length": len(conversation_html),
                "timestamp": timestamp,
                "extraction_method": "improved_with_network_waiting"
            }
            
        finally:
            await playwright.stop()

async def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python improved_conversation_extractor.py list")
        print("  python improved_conversation_extractor.py count-gems")
        print("  python improved_conversation_extractor.py extract <button_index>")
        return
    
    extractor = ImprovedGeminiExtractor()
    command = sys.argv[1]
    
    if command == "list":
        await extractor.get_conversations_list()
    elif command == "count-gems":
        result = await extractor.count_gems()
        print(f"\n📊 Summary: {result['total_gems']} gems found")
    elif command == "extract" and len(sys.argv) > 2:
        button_index = int(sys.argv[2])
        await extractor.extract_conversation_properly(button_index)
    else:
        print("❌ Invalid command or missing arguments")

if __name__ == "__main__":
    asyncio.run(main())

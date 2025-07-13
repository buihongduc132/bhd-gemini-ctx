#!/usr/bin/env python3
"""
Enhanced Gemini Conversation Extractor with markitdown integration.
Extracts detailed conversation content using DOM inspection and converts to high-quality markdown.
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
    print("⚠️ markitdown not available. Install with: pip install markitdown")

class EnhancedGeminiExtractor:
    def __init__(self, cdp_port: int = 9222):
        self.cdp_port = cdp_port
        self.cdp_url = f"http://localhost:{cdp_port}"
        self.output_dir = Path("flow/gemini_extracts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize markitdown if available
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
    
    async def get_conversations_list(self):
        """Get list of available conversations."""
        print("🔍 Getting conversations list...")
        
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
            
            # Extract conversations
            conversations = []
            all_buttons = await page.query_selector_all('button')
            
            for i, button in enumerate(all_buttons):
                try:
                    text = await button.text_content()
                    if text and text.strip():
                        text_clean = text.strip()
                        if (len(text_clean) > 5 and 
                            text_clean not in ['New chat', 'Search for chats', 'Settings & help', 'Sign in', 'Main menu', '2.5 Pro', 'Invite a friend', 'PRO'] and
                            not text_clean.startswith('2.5')):
                            
                            conversations.append({
                                "index": len(conversations) + 1,
                                "button_index": i,
                                "title": text_clean,
                                "url": f"https://gemini.google.com/app/conversation_{i}"
                            })
                except:
                    pass
            
            print(f"✅ Found {len(conversations)} conversations:")
            for conv in conversations:
                print(f"  {conv['index']}. [{conv['button_index']}] {conv['title']}")
            
            return conversations
            
        finally:
            await playwright.stop()
    
    async def extract_conversation_html(self, button_index: int):
        """Extract raw HTML content from a conversation."""
        print(f"📄 Extracting HTML from conversation at button index {button_index}...")
        
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
            
            # Find and click the conversation
            all_buttons = await page.query_selector_all('button')
            if button_index >= len(all_buttons):
                print(f"❌ Button index {button_index} not found (max: {len(all_buttons)-1})")
                return None
            
            target_button = all_buttons[button_index]
            button_text = await target_button.text_content()
            print(f"🎯 Opening conversation: '{button_text.strip()}'")
            
            # Click with force to handle overlays
            await target_button.click(force=True)
            await page.wait_for_timeout(5000)
            
            # Scroll to top to load complete history
            print("🔄 Scrolling to load complete conversation...")
            for i in range(20):
                await page.keyboard.press('Home')
                await page.wait_for_timeout(200)
                await page.evaluate('window.scrollTo(0, 0)')
                await page.wait_for_timeout(200)
            
            # Wait for content to stabilize
            await page.wait_for_timeout(3000)
            
            # Wait for conversation messages to load
            print("⏳ Waiting for conversation messages to load...")
            await page.wait_for_timeout(5000)

            # Try to find and wait for message elements
            try:
                await page.wait_for_selector('div[data-message-id], article, .message, [role="article"]', timeout=10000)
            except:
                print("⚠️ No message elements found, extracting available content...")

            # Extract the main conversation content with better selectors
            conversation_html = await page.evaluate('''() => {
                // Hide sidebar and other UI elements
                const sidebar = document.querySelector('nav, aside, [role="navigation"]');
                if (sidebar) sidebar.style.display = 'none';

                // Find the main conversation container
                const main = document.querySelector('main');
                if (!main) return null;

                // Look for various possible conversation containers
                let conversationContainer = null;

                // Try different selectors for conversation content
                const selectors = [
                    '[data-message-id]',
                    'article',
                    '.message',
                    '[role="article"]',
                    '.conversation-turn',
                    '.chat-message',
                    '[data-testid*="message"]',
                    '.conversation-content',
                    '.messages-container'
                ];

                for (const selector of selectors) {
                    const elements = main.querySelectorAll(selector);
                    if (elements.length > 0) {
                        // Create a container with all message elements
                        const container = document.createElement('div');
                        container.className = 'extracted-conversation';
                        elements.forEach(el => container.appendChild(el.cloneNode(true)));
                        return container.innerHTML;
                    }
                }

                // If no specific message elements found, get all content from main
                // but try to filter out navigation and UI elements
                const allContent = main.cloneNode(true);

                // Remove navigation and UI elements
                const elementsToRemove = allContent.querySelectorAll(
                    'nav, aside, button, .menu, .toolbar, .header, .footer, [role="navigation"], [role="banner"]'
                );
                elementsToRemove.forEach(el => el.remove());

                return allContent.innerHTML;
            }''')
            
            if not conversation_html:
                print("❌ Could not extract conversation HTML")
                return None
            
            # Save raw HTML
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            conv_id = button_text.strip().replace(' ', '_').replace(':', '')[:20]
            
            html_file = self.output_dir / f"conversation_raw_{conv_id}_{timestamp}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Gemini Conversation: {button_text.strip()}</title>
</head>
<body>
    <h1>Gemini Conversation: {button_text.strip()}</h1>
    <p><strong>Extracted:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>URL:</strong> {page.url}</p>
    <hr>
    {conversation_html}
</body>
</html>""")
            
            print(f"✅ Raw HTML saved to: {html_file}")
            
            # Convert to markdown using markitdown if available
            if self.markitdown:
                print("🔄 Converting to markdown using markitdown...")
                try:
                    result = self.markitdown.convert(str(html_file))
                    markdown_content = result.text_content
                    
                    markdown_file = self.output_dir / f"conversation_{conv_id}_{timestamp}.md"
                    with open(markdown_file, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)
                    
                    print(f"✅ Markdown saved to: {markdown_file}")
                    
                    # Also save a cleaned version
                    cleaned_content = self._clean_markdown(markdown_content, button_text.strip())
                    cleaned_file = self.output_dir / f"conversation_cleaned_{conv_id}_{timestamp}.md"
                    with open(cleaned_file, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    
                    print(f"✅ Cleaned markdown saved to: {cleaned_file}")
                    
                except Exception as e:
                    print(f"⚠️ Error converting with markitdown: {e}")
            
            return {
                "conversation_title": button_text.strip(),
                "button_index": button_index,
                "url": page.url,
                "html_file": str(html_file),
                "html_length": len(conversation_html),
                "timestamp": timestamp
            }
            
        finally:
            await playwright.stop()
    
    def _clean_markdown(self, markdown_content: str, title: str) -> str:
        """Clean and format the markdown content."""
        lines = markdown_content.split('\n')
        cleaned_lines = []
        
        # Add header
        cleaned_lines.extend([
            f"# {title}",
            "",
            f"**Extracted:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Source:** Gemini Conversation",
            "",
            "---",
            ""
        ])
        
        # Process content lines
        in_conversation = False
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and navigation elements
            if not line or line in ['Gemini', 'New chat', 'Search for chats', 'Settings & help']:
                continue
            
            # Skip obvious UI elements
            if any(ui_element in line.lower() for ui_element in ['menu', 'button', 'search', 'settings']):
                continue
            
            # Add the line
            cleaned_lines.append(line)
        
        # Add footer
        cleaned_lines.extend([
            "",
            "---",
            "",
            "*Extracted using enhanced Gemini conversation extractor with markitdown*"
        ])
        
        return '\n'.join(cleaned_lines)
    
    async def extract_multiple_conversations(self, indices: list):
        """Extract multiple conversations by their indices."""
        print(f"📄 Extracting {len(indices)} conversations...")
        
        results = []
        for i, index in enumerate(indices):
            print(f"\n--- Extracting conversation {i+1}/{len(indices)} ---")
            result = await self.extract_conversation_html(index)
            if result:
                results.append(result)
            
            # Small delay between extractions
            await asyncio.sleep(2)
        
        # Save summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary = {
            "timestamp": timestamp,
            "task": "extract_multiple_conversations",
            "total_requested": len(indices),
            "successfully_extracted": len(results),
            "results": results
        }
        
        summary_file = self.output_dir / f"extraction_summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Extraction complete. Summary saved to: {summary_file}")
        return results

async def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python enhanced_conversation_extractor.py list")
        print("  python enhanced_conversation_extractor.py extract <button_index>")
        print("  python enhanced_conversation_extractor.py extract-multiple <index1,index2,index3>")
        return
    
    extractor = EnhancedGeminiExtractor()
    command = sys.argv[1]
    
    if command == "list":
        await extractor.get_conversations_list()
    elif command == "extract" and len(sys.argv) > 2:
        button_index = int(sys.argv[2])
        await extractor.extract_conversation_html(button_index)
    elif command == "extract-multiple" and len(sys.argv) > 2:
        indices = [int(x.strip()) for x in sys.argv[2].split(',')]
        await extractor.extract_multiple_conversations(indices)
    else:
        print("❌ Invalid command or missing arguments")

if __name__ == "__main__":
    asyncio.run(main())

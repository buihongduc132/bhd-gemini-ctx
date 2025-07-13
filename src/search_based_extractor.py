#!/usr/bin/env python3
"""
Search-based Gemini Extractor - Uses the search page to find and extract real conversations.
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

class SearchBasedExtractor:
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
    
    async def show_all_conversations_in_search(self):
        """Go to search page and show all conversations listed there."""
        print("🔍 Going to search page to show all conversations...")
        
        playwright, browser, page = await self.connect()
        
        try:
            # Navigate to search page
            print("📍 Navigating to https://gemini.google.com/search")
            await page.goto("https://gemini.google.com/search", wait_until="domcontentloaded", timeout=15000)
            await self.wait_for_network_stability(page)
            
            # Look for conversation elements on the search page
            print("🔍 Looking for conversation elements...")
            
            # Try different selectors to find conversation items
            conversation_selectors = [
                'a[href*="/app/"]',
                'a[href*="conversation"]', 
                'div[data-conversation-id]',
                '[role="button"][href]',
                'a[href*="/chat/"]',
                '.conversation-item',
                '.search-result a',
                'a[href*="/c/"]'
            ]
            
            all_conversations = []
            
            for selector in conversation_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"Found {len(elements)} elements with selector: {selector}")
                        
                        for i, element in enumerate(elements):
                            try:
                                href = await element.get_attribute('href')
                                text = await element.text_content()
                                
                                if href and text and len(text.strip()) > 10:
                                    all_conversations.append({
                                        "index": len(all_conversations) + 1,
                                        "title": text.strip()[:200],
                                        "url": href,
                                        "selector": selector
                                    })
                            except:
                                continue
                        
                        if all_conversations:
                            break
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
            
            # If no specific conversation links, look for any clickable items with text
            if not all_conversations:
                print("🔍 Looking for any clickable conversation items...")
                generic_elements = await page.query_selector_all('div[role="button"], button, a')
                
                for i, element in enumerate(generic_elements):
                    try:
                        text = await element.text_content()
                        href = await element.get_attribute('href')
                        
                        if text and len(text.strip()) > 20 and len(text.strip()) < 200:
                            # Skip obvious UI elements
                            if not any(skip in text.lower() for skip in ['search', 'menu', 'settings', 'sign in', 'new chat']):
                                all_conversations.append({
                                    "index": len(all_conversations) + 1,
                                    "title": text.strip(),
                                    "url": href or "No URL",
                                    "element_index": i
                                })
                    except:
                        continue
            
            print(f"\n✅ Found {len(all_conversations)} conversations on search page:")
            for conv in all_conversations[:20]:  # Show first 20
                print(f"  {conv['index']}. {conv['title']}")
                if conv.get('url') and conv['url'] != "No URL":
                    print(f"      URL: {conv['url']}")
            
            # Save the list
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = self.output_dir / f"search_conversations_all_{timestamp}.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": timestamp,
                    "total_conversations": len(all_conversations),
                    "conversations": all_conversations
                }, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 Full list saved to: {results_file}")
            return all_conversations
            
        finally:
            await playwright.stop()
    
    async def search_and_filter_conversations(self, query: str):
        """Search for conversations with a specific query."""
        print(f"🔍 Searching and filtering conversations for: '{query}'")
        
        playwright, browser, page = await self.connect()
        
        try:
            # Navigate to search page
            print("📍 Navigating to https://gemini.google.com/search")
            await page.goto("https://gemini.google.com/search", wait_until="domcontentloaded", timeout=15000)
            await self.wait_for_network_stability(page)
            
            # Find search input and enter query
            print(f"🔍 Entering search query: '{query}'")
            search_selectors = [
                'input[type="text"]',
                'input[placeholder*="search"]',
                'input[placeholder*="Search"]',
                'textarea',
                '[role="searchbox"]',
                '.search-input'
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await page.query_selector(selector)
                    if search_input:
                        print(f"Found search input with selector: {selector}")
                        break
                except:
                    continue
            
            if search_input:
                await search_input.fill(query)
                await page.keyboard.press('Enter')
                await self.wait_for_network_stability(page)
            else:
                print("❌ Could not find search input")
                return []
            
            # Extract filtered results
            print("🔍 Extracting filtered conversation results...")
            filtered_conversations = []
            
            # Look for conversation results
            result_selectors = [
                'a[href*="/app/"]',
                'a[href*="conversation"]',
                'div[role="button"]',
                '.search-result',
                'a[href*="/c/"]'
            ]
            
            for selector in result_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"Found {len(elements)} filtered results with selector: {selector}")
                        
                        for i, element in enumerate(elements):
                            try:
                                text = await element.text_content()
                                href = await element.get_attribute('href')
                                
                                if text and len(text.strip()) > 10:
                                    filtered_conversations.append({
                                        "index": len(filtered_conversations) + 1,
                                        "title": text.strip()[:200],
                                        "url": href or "No URL",
                                        "selector": selector,
                                        "element_index": i
                                    })
                            except:
                                continue
                        
                        if filtered_conversations:
                            break
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
            
            print(f"\n✅ Found {len(filtered_conversations)} filtered conversations:")
            for conv in filtered_conversations[:15]:  # Show first 15
                print(f"  {conv['index']}. {conv['title']}")
                if conv.get('url') and conv['url'] != "No URL":
                    print(f"      URL: {conv['url']}")
            
            # Save filtered results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = self.output_dir / f"search_conversations_filtered_{query}_{timestamp}.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": timestamp,
                    "query": query,
                    "total_filtered": len(filtered_conversations),
                    "conversations": filtered_conversations
                }, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 Filtered results saved to: {results_file}")
            return filtered_conversations
            
        finally:
            await playwright.stop()
    
    async def extract_conversation_by_clicking(self, element_index: int, title: str = ""):
        """Click on a conversation element from search page and extract the content."""
        print(f"📄 Extracting conversation: {title}")
        print(f"🔗 Element index: {element_index}")

        playwright, browser, page = await self.connect()

        try:
            # Navigate to search page first
            print("📍 Navigating to search page...")
            await page.goto("https://gemini.google.com/search", wait_until="domcontentloaded", timeout=15000)
            await self.wait_for_network_stability(page)

            # Find the conversation element and click it
            print(f"🎯 Looking for conversation element at index {element_index}...")
            conversation_elements = await page.query_selector_all('div[role="button"]')

            if element_index < len(conversation_elements):
                target_element = conversation_elements[element_index]
                element_text = await target_element.text_content()
                print(f"🎯 Clicking on: '{element_text.strip()}'")

                await target_element.click()
                await self.wait_for_network_stability(page, timeout=20000)
            else:
                print(f"❌ Element index {element_index} not found")
                return None
            
            # Scroll to top to get complete history
            print("🔄 Scrolling to load complete conversation...")
            for i in range(15):
                await page.keyboard.press('Home')
                await page.wait_for_timeout(300)
            
            await self.wait_for_network_stability(page, timeout=15000)
            
            # Extract the main conversation content
            print("📄 Extracting conversation content from main section...")
            conversation_html = await page.evaluate('''() => {
                // Find the main conversation area
                const main = document.querySelector('main');
                if (!main) return null;
                
                // Look for conversation messages
                const messageSelectors = [
                    '[data-message-id]',
                    'article',
                    '.message',
                    '[role="article"]',
                    '.conversation-turn',
                    '.chat-message'
                ];
                
                let messageElements = [];
                for (const selector of messageSelectors) {
                    const elements = main.querySelectorAll(selector);
                    if (elements.length > 0) {
                        messageElements = Array.from(elements);
                        console.log(`Found ${elements.length} messages with selector: ${selector}`);
                        break;
                    }
                }
                
                // If we found message elements, extract them
                if (messageElements.length > 0) {
                    let content = '';
                    messageElements.forEach((element, index) => {
                        content += `<div class="message-${index}">${element.outerHTML}</div>\\n`;
                    });
                    return content;
                }
                
                // Otherwise get the main content
                return main.innerHTML;
            }''')
            
            if not conversation_html or len(conversation_html.strip()) < 100:
                print("⚠️ Limited content, getting full page...")
                conversation_html = await page.evaluate('''() => {
                    return document.body.innerHTML;
                }''')
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
            
            # Save raw HTML
            html_file = self.output_dir / f"conversation_extracted_{safe_title}_{timestamp}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Extracted Conversation: {title}</title>
</head>
<body>
    <h1>Gemini Conversation: {title}</h1>
    <p><strong>Extracted:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>URL:</strong> {page.url}</p>
    <p><strong>Content Length:</strong> {len(conversation_html)} characters</p>
    <hr>
    {conversation_html}
</body>
</html>""")
            
            print(f"✅ Raw HTML saved to: {html_file}")
            print(f"📊 Content length: {len(conversation_html)} characters")
            
            # Convert to markdown
            if self.markitdown and len(conversation_html) > 100:
                try:
                    result = self.markitdown.convert(str(html_file))
                    
                    # Clean markdown
                    cleaned_content = f"""# {title}

**Extracted:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**URL:** {page.url}
**Content Length:** {len(conversation_html)} characters

---

{result.text_content}

---

*Extracted from Gemini conversation via search*
"""
                    
                    markdown_file = self.output_dir / f"conversation_extracted_{safe_title}_{timestamp}.md"
                    with open(markdown_file, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    
                    print(f"✅ Markdown saved to: {markdown_file}")
                    
                    return {
                        "title": title,
                        "url": page.url,
                        "html_file": str(html_file),
                        "markdown_file": str(markdown_file),
                        "content_length": len(conversation_html),
                        "timestamp": timestamp
                    }
                    
                except Exception as e:
                    print(f"⚠️ Markdown conversion error: {e}")
            
            return {
                "title": title,
                "url": page.url,
                "html_file": str(html_file),
                "content_length": len(conversation_html),
                "timestamp": timestamp
            }
            
        finally:
            await playwright.stop()

async def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python search_based_extractor.py show-all")
        print("  python search_based_extractor.py search <query>")
        print("  python search_based_extractor.py extract <conversation_url> <title>")
        print("  python search_based_extractor.py full-flow <search_query>")
        return
    
    extractor = SearchBasedExtractor()
    command = sys.argv[1]
    
    if command == "show-all":
        await extractor.show_all_conversations_in_search()
    elif command == "search" and len(sys.argv) > 2:
        query = sys.argv[2]
        await extractor.search_and_filter_conversations(query)
    elif command == "extract" and len(sys.argv) > 3:
        element_index = int(sys.argv[2])
        title = sys.argv[3] if len(sys.argv) > 3 else "Conversation"
        await extractor.extract_conversation_by_clicking(element_index, title)
    elif command == "full-flow" and len(sys.argv) > 2:
        query = sys.argv[2]
        print("🚀 Running full extraction flow...")
        
        # 1. Show all conversations
        print("\n=== STEP 1: Show all conversations ===")
        all_convs = await extractor.show_all_conversations_in_search()
        
        # 2. Search and filter
        print(f"\n=== STEP 2: Search for '{query}' ===")
        filtered_convs = await extractor.search_and_filter_conversations(query)
        
        # 3. Extract first 2 conversations by clicking on them
        print(f"\n=== STEP 3: Extract first 2 conversations ===")
        extracted = 0
        for conv in filtered_convs:
            if extracted >= 2:
                break
            if conv.get('element_index') is not None:
                print(f"\n--- Extracting conversation {extracted + 1}: {conv['title']} ---")
                await extractor.extract_conversation_by_clicking(conv['element_index'], conv['title'])
                extracted += 1
        
        print(f"\n✅ Full flow complete! Extracted {extracted} conversations.")
    else:
        print("❌ Invalid command or missing arguments")

if __name__ == "__main__":
    asyncio.run(main())

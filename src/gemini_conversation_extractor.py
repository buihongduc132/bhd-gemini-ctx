#!/usr/bin/env python3
"""
Gemini Conversation Extractor using Playwright

This script connects to an existing Chrome browser instance and extracts
conversation content from Google Gemini, converting it to markdown format.

Features:
- Connect to existing Chrome instance via CDP
- List and search gems
- List recent conversations
- Search conversations
- Extract full conversation content as markdown
- Scroll to get complete conversation history
"""

import asyncio
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from playwright.async_api import async_playwright, Browser, Page
from markdownify import markdownify as md

class GeminiConversationExtractor:
    def __init__(self, cdp_port: int = 9222):
        """Initialize the extractor with CDP connection."""
        self.cdp_port = cdp_port
        self.cdp_url = f"http://localhost:{cdp_port}"
        self.browser = None
        self.page = None
        self.playwright = None

        # Create output directory
        self.output_dir = Path("flow/gemini_extracts")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def connect_to_browser(self):
        """Connect to the existing Chrome browser instance."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)

            # Get the first available context and page
            contexts = self.browser.contexts
            if contexts:
                context = contexts[0]
                pages = context.pages
                if pages:
                    self.page = pages[0]
                else:
                    self.page = await context.new_page()
            else:
                context = await self.browser.new_context()
                self.page = await context.new_page()

            print(f"✅ Connected to Chrome browser at {self.cdp_url}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to browser: {e}")
            return False

    async def close_browser(self):
        """Close the browser connection."""
        if self.playwright:
            await self.playwright.stop()
    
    async def list_gems(self) -> Dict:
        """List all available gems."""
        print("🔍 Listing gems...")

        try:
            # Navigate to gems page with more robust loading
            print("📍 Navigating to gems page...")
            try:
                await self.page.goto("https://gemini.google.com/gems/view", wait_until="domcontentloaded", timeout=15000)
            except:
                # Fallback: try with load event
                await self.page.goto("https://gemini.google.com/gems/view", wait_until="load", timeout=10000)

            await self.page.wait_for_timeout(5000)  # Wait for dynamic content

            # Look for gem elements - try multiple selectors
            gems = []

            # Try different possible selectors for gems
            gem_selectors = [
                '[data-testid*="gem"]',
                '.gem-card',
                '.gem-item',
                '[role="button"]:has-text("Gem")',
                'article',
                '.card',
                '[data-gem-id]'
            ]

            gem_elements = []
            for selector in gem_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        gem_elements = elements
                        print(f"Found {len(elements)} elements with selector: {selector}")
                        break
                except:
                    continue

            # If no specific gem elements found, look for any clickable items
            if not gem_elements:
                # Look for any cards or items that might be gems
                potential_selectors = [
                    'div[role="button"]',
                    '.MuiCard-root',
                    '.card',
                    'article',
                    'div:has(h3)',
                    'div:has(h2)'
                ]

                for selector in potential_selectors:
                    try:
                        elements = await self.page.query_selector_all(selector)
                        if elements:
                            # Filter elements that might be gems (have text content)
                            filtered_elements = []
                            for element in elements:
                                text = await element.text_content()
                                if text and len(text.strip()) > 10:  # Has meaningful content
                                    filtered_elements.append(element)

                            if filtered_elements:
                                gem_elements = filtered_elements[:20]  # Limit to first 20
                                print(f"Found {len(gem_elements)} potential gem elements with selector: {selector}")
                                break
                    except:
                        continue

            # Extract gem information
            for i, element in enumerate(gem_elements):
                try:
                    # Get text content
                    text_content = await element.text_content()
                    if not text_content or len(text_content.strip()) < 5:
                        continue

                    # Try to get href if it's a link
                    href = None
                    try:
                        href = await element.get_attribute('href')
                        if not href:
                            # Look for a link inside the element
                            link = await element.query_selector('a')
                            if link:
                                href = await link.get_attribute('href')
                    except:
                        pass

                    # Extract title and description
                    title = ""
                    description = ""

                    # Try to find title in h1, h2, h3, or strong tags
                    for tag in ['h1', 'h2', 'h3', 'h4', 'strong', '.title']:
                        try:
                            title_element = await element.query_selector(tag)
                            if title_element:
                                title = await title_element.text_content()
                                break
                        except:
                            continue

                    # If no title found, use first line of text
                    if not title:
                        lines = text_content.strip().split('\n')
                        title = lines[0][:100] if lines else f"Gem {i+1}"

                    # Use remaining text as description
                    if len(text_content.strip()) > len(title):
                        description = text_content.replace(title, '').strip()[:200]

                    gem_data = {
                        "id": f"gem_{i+1}",
                        "title": title.strip(),
                        "description": description.strip() if description else "No description available",
                        "url": href if href else f"https://gemini.google.com/gems/view#{i+1}",
                        "raw_text": text_content.strip()[:300]  # First 300 chars for debugging
                    }

                    gems.append(gem_data)

                except Exception as e:
                    print(f"Error extracting gem {i}: {e}")
                    continue

            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"gems_list_{timestamp}.json"

            gems_data = {
                "timestamp": timestamp,
                "task": "list_gems",
                "url": "https://gemini.google.com/gems/view",
                "gems_count": len(gems),
                "gems": gems,
                "page_title": await self.page.title(),
                "extraction_method": "playwright_dom"
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(gems_data, f, indent=2, ensure_ascii=False)

            print(f"✅ Found {len(gems)} gems, saved to {output_file}")
            return gems_data

        except Exception as e:
            print(f"❌ Error listing gems: {e}")
            return {"error": str(e), "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")}
    
    async def search_gems(self, query: str) -> Dict:
        """Search for gems with a specific query."""
        print(f"🔍 Searching gems for: {query}")

        try:
            # First get all gems
            all_gems_data = await self.list_gems()
            all_gems = all_gems_data.get("gems", [])

            # Filter gems that contain the query
            matching_gems = []
            for gem in all_gems:
                gem_text = f"{gem.get('title', '')} {gem.get('description', '')} {gem.get('raw_text', '')}".lower()
                if query.lower() in gem_text:
                    matching_gems.append(gem)

            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"gems_search_{query}_{timestamp}.json"

            search_data = {
                "timestamp": timestamp,
                "task": "search_gems",
                "query": query,
                "url": "https://gemini.google.com/gems/view",
                "total_gems_searched": len(all_gems),
                "matching_gems_count": len(matching_gems),
                "matching_gems": matching_gems,
                "first_result": matching_gems[0] if matching_gems else None,
                "extraction_method": "playwright_dom_filter"
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(search_data, f, indent=2, ensure_ascii=False)

            print(f"✅ Found {len(matching_gems)} gems matching '{query}', saved to {output_file}")
            return search_data

        except Exception as e:
            print(f"❌ Error searching gems: {e}")
            return {"error": str(e), "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")}
    
    async def list_recent_conversations(self) -> Dict:
        """List recent conversations from the home page."""
        print("🔍 Listing recent conversations...")

        try:
            # Navigate to Gemini home page with more robust loading
            print("📍 Navigating to Gemini home page...")
            try:
                await self.page.goto("https://gemini.google.com", wait_until="domcontentloaded", timeout=15000)
            except:
                # Fallback: try with load event
                await self.page.goto("https://gemini.google.com", wait_until="load", timeout=10000)

            await self.page.wait_for_timeout(5000)  # Wait for dynamic content

            conversations = []

            # Look for conversation elements in sidebar
            conversation_selectors = [
                '[data-testid*="conversation"]',
                '[data-testid*="chat"]',
                '.conversation-item',
                '.chat-item',
                'nav a',
                'aside a',
                '.sidebar a',
                '[role="button"]:has-text("conversation")',
                'div[role="button"]'
            ]

            conversation_elements = []
            for selector in conversation_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        # Filter elements that look like conversations
                        filtered_elements = []
                        for element in elements:
                            text = await element.text_content()
                            href = await element.get_attribute('href')

                            # Check if it looks like a conversation
                            if (text and len(text.strip()) > 5 and
                                (href and '/app/' in href) or
                                any(word in text.lower() for word in ['conversation', 'chat', 'discuss'])):
                                filtered_elements.append(element)

                        if filtered_elements:
                            conversation_elements = filtered_elements
                            print(f"Found {len(filtered_elements)} conversation elements with selector: {selector}")
                            break
                except:
                    continue

            # If no specific conversation elements found, look for links in sidebar
            if not conversation_elements:
                try:
                    # Look for sidebar or navigation area
                    sidebar_selectors = ['nav', 'aside', '.sidebar', '[role="navigation"]']
                    for sidebar_selector in sidebar_selectors:
                        sidebar = await self.page.query_selector(sidebar_selector)
                        if sidebar:
                            links = await sidebar.query_selector_all('a')
                            for link in links:
                                href = await link.get_attribute('href')
                                text = await link.text_content()
                                if href and '/app/' in href and text and len(text.strip()) > 3:
                                    conversation_elements.append(link)

                            if conversation_elements:
                                print(f"Found {len(conversation_elements)} conversation links in sidebar")
                                break
                except:
                    pass

            # Extract conversation information
            for i, element in enumerate(conversation_elements[:20]):  # Limit to first 20
                try:
                    text_content = await element.text_content()
                    href = await element.get_attribute('href')

                    if not text_content or len(text_content.strip()) < 3:
                        continue

                    # Clean up the text
                    title = text_content.strip()[:100]

                    # Extract conversation ID from URL
                    conv_id = ""
                    if href and '/app/' in href:
                        conv_id = href.split('/app/')[-1].split('?')[0].split('#')[0]

                    conversation_data = {
                        "id": conv_id or f"conv_{i+1}",
                        "title": title,
                        "url": href if href else f"https://gemini.google.com/app/unknown_{i+1}",
                        "raw_text": text_content.strip()
                    }

                    conversations.append(conversation_data)

                except Exception as e:
                    print(f"Error extracting conversation {i}: {e}")
                    continue

            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"recent_conversations_{timestamp}.json"

            conversations_data = {
                "timestamp": timestamp,
                "task": "list_recent_conversations",
                "url": "https://gemini.google.com",
                "conversations_count": len(conversations),
                "conversations": conversations,
                "page_title": await self.page.title(),
                "extraction_method": "playwright_dom"
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(conversations_data, f, indent=2, ensure_ascii=False)

            print(f"✅ Found {len(conversations)} recent conversations, saved to {output_file}")
            return conversations_data

        except Exception as e:
            print(f"❌ Error listing recent conversations: {e}")
            return {"error": str(e), "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")}
    
    async def search_conversations(self, query: str) -> Dict:
        """Search for conversations with a specific query."""
        print(f"🔍 Searching conversations for: {query}")

        try:
            # Navigate to search page with more robust loading
            print("📍 Navigating to search page...")
            try:
                await self.page.goto("https://gemini.google.com/search", wait_until="domcontentloaded", timeout=15000)
            except:
                # Fallback: try with load event
                await self.page.goto("https://gemini.google.com/search", wait_until="load", timeout=10000)

            await self.page.wait_for_timeout(3000)

            # Look for search input
            search_input = None
            search_selectors = [
                'input[type="search"]',
                'input[placeholder*="search"]',
                'input[placeholder*="Search"]',
                'textarea[placeholder*="search"]',
                'input[data-testid*="search"]',
                '.search-input',
                '#search',
                'input'
            ]

            for selector in search_selectors:
                try:
                    search_input = await self.page.query_selector(selector)
                    if search_input:
                        # Check if it's visible and enabled
                        is_visible = await search_input.is_visible()
                        is_enabled = await search_input.is_enabled()
                        if is_visible and is_enabled:
                            print(f"Found search input with selector: {selector}")
                            break
                        else:
                            search_input = None
                except:
                    continue

            if not search_input:
                print("❌ Could not find search input")
                # Try to search in recent conversations instead
                recent_data = await self.list_recent_conversations()
                conversations = recent_data.get("conversations", [])

                # Filter conversations that contain the query
                matching_conversations = []
                for conv in conversations:
                    conv_text = f"{conv.get('title', '')} {conv.get('raw_text', '')}".lower()
                    if query.lower() in conv_text:
                        matching_conversations.append(conv)

                search_data = {
                    "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                    "task": "search_conversations",
                    "query": query,
                    "url": "https://gemini.google.com/search",
                    "search_method": "fallback_to_recent_conversations",
                    "total_conversations_searched": len(conversations),
                    "matching_conversations_count": len(matching_conversations),
                    "matching_conversations": matching_conversations,
                    "first_result": matching_conversations[0] if matching_conversations else None
                }

                output_file = self.output_dir / f"conversation_search_{query}_{search_data['timestamp']}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(search_data, f, indent=2, ensure_ascii=False)

                print(f"✅ Found {len(matching_conversations)} conversations matching '{query}' (fallback method)")
                return search_data

            # Perform search
            await search_input.fill(query)
            await search_input.press('Enter')

            # Wait for search results
            await self.page.wait_for_timeout(3000)

            # Look for search results
            search_results = []
            result_selectors = [
                '.search-result',
                '.result-item',
                '[data-testid*="result"]',
                '.conversation-result',
                'article',
                '.card',
                'div[role="button"]'
            ]

            result_elements = []
            for selector in result_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        # Filter elements that look like search results
                        filtered_elements = []
                        for element in elements:
                            text = await element.text_content()
                            if text and len(text.strip()) > 10:
                                filtered_elements.append(element)

                        if filtered_elements:
                            result_elements = filtered_elements
                            print(f"Found {len(filtered_elements)} search result elements")
                            break
                except:
                    continue

            # Extract search results
            for i, element in enumerate(result_elements[:10]):  # Limit to first 10
                try:
                    text_content = await element.text_content()
                    href = await element.get_attribute('href')

                    if not text_content or len(text_content.strip()) < 5:
                        continue

                    # Try to find a link inside if no href
                    if not href:
                        link = await element.query_selector('a')
                        if link:
                            href = await link.get_attribute('href')

                    # Extract title (first line or heading)
                    title = ""
                    for tag in ['h1', 'h2', 'h3', 'h4', 'strong']:
                        try:
                            title_element = await element.query_selector(tag)
                            if title_element:
                                title = await title_element.text_content()
                                break
                        except:
                            continue

                    if not title:
                        lines = text_content.strip().split('\n')
                        title = lines[0][:100] if lines else f"Result {i+1}"

                    # Use remaining text as preview
                    preview = text_content.replace(title, '').strip()[:200]

                    result_data = {
                        "id": f"search_result_{i+1}",
                        "title": title.strip(),
                        "preview": preview,
                        "url": href if href else "",
                        "raw_text": text_content.strip()[:300]
                    }

                    search_results.append(result_data)

                except Exception as e:
                    print(f"Error extracting search result {i}: {e}")
                    continue

            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"conversation_search_{query}_{timestamp}.json"

            search_data = {
                "timestamp": timestamp,
                "task": "search_conversations",
                "query": query,
                "url": "https://gemini.google.com/search",
                "search_method": "direct_search",
                "results_count": len(search_results),
                "search_results": search_results,
                "first_result": search_results[0] if search_results else None,
                "page_title": await self.page.title(),
                "extraction_method": "playwright_dom"
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(search_data, f, indent=2, ensure_ascii=False)

            print(f"✅ Found {len(search_results)} search results for '{query}', saved to {output_file}")
            return search_data

        except Exception as e:
            print(f"❌ Error searching conversations: {e}")
            return {"error": str(e), "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")}

    async def extract_conversation_content(self, conversation_url: str) -> Dict:
        """Extract full conversation content from a specific URL."""
        print(f"📄 Extracting conversation content from: {conversation_url}")

        try:
            # Navigate to conversation with more robust loading
            print(f"📍 Navigating to conversation: {conversation_url}")
            try:
                await self.page.goto(conversation_url, wait_until="domcontentloaded", timeout=15000)
            except:
                # Fallback: try with load event
                await self.page.goto(conversation_url, wait_until="load", timeout=10000)

            await self.page.wait_for_timeout(5000)

            # Scroll to top to load all messages
            print("🔄 Scrolling to load complete conversation history...")

            # Scroll to the very top multiple times to ensure all content is loaded
            for i in range(10):
                await self.page.keyboard.press('Home')
                await self.page.wait_for_timeout(500)

                # Also try scrolling up
                await self.page.evaluate('window.scrollTo(0, 0)')
                await self.page.wait_for_timeout(500)

                # Check if we can scroll up more
                scroll_position = await self.page.evaluate('window.pageYOffset')
                if scroll_position == 0:
                    # Try a few more times to be sure
                    for _ in range(3):
                        await self.page.keyboard.press('PageUp')
                        await self.page.wait_for_timeout(300)

            # Wait for content to stabilize
            await self.page.wait_for_timeout(2000)

            # Look for conversation messages
            messages = []

            # Try different selectors for message elements
            message_selectors = [
                '[data-testid*="message"]',
                '[data-testid*="chat"]',
                '.message',
                '.chat-message',
                '.conversation-turn',
                'article',
                '.user-message',
                '.ai-message',
                'div[role="article"]',
                'div[data-message-id]'
            ]

            message_elements = []
            for selector in message_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements and len(elements) > 1:  # Should have multiple messages
                        message_elements = elements
                        print(f"Found {len(elements)} message elements with selector: {selector}")
                        break
                except:
                    continue

            # If no specific message elements found, look for any content blocks
            if not message_elements:
                try:
                    # Look for main content area
                    main_selectors = ['main', '.main-content', '.conversation', '.chat-container']
                    for main_selector in main_selectors:
                        main_element = await self.page.query_selector(main_selector)
                        if main_element:
                            # Look for any div elements that might contain messages
                            divs = await main_element.query_selector_all('div')
                            # Filter divs that have substantial text content
                            for div in divs:
                                text = await div.text_content()
                                if text and len(text.strip()) > 20:
                                    message_elements.append(div)

                            if message_elements:
                                print(f"Found {len(message_elements)} potential message elements in main content")
                                break
                except:
                    pass

            # Extract message content
            for i, element in enumerate(message_elements):
                try:
                    text_content = await element.text_content()
                    if not text_content or len(text_content.strip()) < 10:
                        continue

                    # Try to determine if it's user or AI message
                    message_type = "unknown"

                    # Look for indicators in the element or its parents
                    element_html = await element.inner_html()
                    element_classes = await element.get_attribute('class') or ""

                    if any(indicator in element_html.lower() or indicator in element_classes.lower()
                           for indicator in ['user', 'human', 'you']):
                        message_type = "user"
                    elif any(indicator in element_html.lower() or indicator in element_classes.lower()
                             for indicator in ['ai', 'assistant', 'gemini', 'bot']):
                        message_type = "ai"
                    else:
                        # Try to guess based on content patterns
                        if text_content.strip().endswith('?') or len(text_content.strip()) < 100:
                            message_type = "user"
                        else:
                            message_type = "ai"

                    # Look for timestamps
                    timestamp_text = ""
                    try:
                        timestamp_element = await element.query_selector('[data-testid*="timestamp"], .timestamp, time')
                        if timestamp_element:
                            timestamp_text = await timestamp_element.text_content()
                    except:
                        pass

                    message_data = {
                        "index": i,
                        "type": message_type,
                        "content": text_content.strip(),
                        "timestamp": timestamp_text.strip() if timestamp_text else "",
                        "html": element_html[:500] if len(element_html) < 500 else element_html[:500] + "..."
                    }

                    messages.append(message_data)

                except Exception as e:
                    print(f"Error extracting message {i}: {e}")
                    continue

            # Convert to markdown
            markdown_content = self._convert_messages_to_markdown(messages, conversation_url)

            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            conv_id = conversation_url.split('/')[-1] if '/' in conversation_url else "unknown"

            # Save raw data
            raw_file = self.output_dir / f"conversation_raw_{conv_id}_{timestamp}.json"
            raw_data = {
                "timestamp": timestamp,
                "task": "extract_conversation_content",
                "url": conversation_url,
                "messages_count": len(messages),
                "messages": messages,
                "page_title": await self.page.title(),
                "extraction_method": "playwright_dom_with_scrolling"
            }

            with open(raw_file, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, indent=2, ensure_ascii=False)

            # Save markdown
            markdown_file = self.output_dir / f"conversation_{conv_id}_{timestamp}.md"
            with open(markdown_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print(f"✅ Extracted {len(messages)} messages, saved to {raw_file} and {markdown_file}")
            return raw_data

        except Exception as e:
            print(f"❌ Error extracting conversation content: {e}")
            return {"error": str(e), "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")}

    def _convert_messages_to_markdown(self, messages: List[Dict], url: str) -> str:
        """Convert extracted messages to markdown format."""
        markdown_lines = [
            "# Gemini Conversation",
            "",
            f"**URL:** {url}",
            f"**Extracted:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Messages:** {len(messages)}",
            "",
            "---",
            ""
        ]

        for message in messages:
            message_type = message.get('type', 'unknown')
            content = message.get('content', '')
            timestamp = message.get('timestamp', '')

            # Add message header
            if message_type == 'user':
                header = "## 👤 User"
            elif message_type == 'ai':
                header = "## 🤖 Gemini"
            else:
                header = f"## Message {message.get('index', 0) + 1}"

            if timestamp:
                header += f" _{timestamp}_"

            markdown_lines.append(header)
            markdown_lines.append("")
            markdown_lines.append(content)
            markdown_lines.append("")

        markdown_lines.append("---")
        markdown_lines.append("")
        markdown_lines.append("*Extracted using Playwright DOM manipulation*")

        return "\n".join(markdown_lines)

    async def run_complete_extraction(self):
        """Run the complete extraction process as specified in WS_TODO.md."""
        print("🚀 Starting complete Gemini extraction process...")

        # Connect to browser
        if not await self.connect_to_browser():
            return

        results = {}

        try:
            # 1. List gems
            print("\n" + "="*50)
            print("STEP 1: Listing gems")
            print("="*50)
            results['gems_list'] = await self.list_gems()

            # 2. Search for "memory" gems
            print("\n" + "="*50)
            print("STEP 2: Searching for 'memory' gems")
            print("="*50)
            results['memory_gems'] = await self.search_gems("memory")

            # 3. List recent conversations
            print("\n" + "="*50)
            print("STEP 3: Listing recent conversations")
            print("="*50)
            results['recent_conversations'] = await self.list_recent_conversations()

            # 4. Search for "dy" conversations
            print("\n" + "="*50)
            print("STEP 4: Searching for 'dy' conversations")
            print("="*50)
            results['dy_conversations'] = await self.search_conversations("dy")

            # 5. Extract first conversation content if available
            first_conversation_url = None

            # Try to get first conversation from recent conversations
            recent_convs = results.get('recent_conversations', {}).get('conversations', [])
            if recent_convs:
                first_conversation_url = recent_convs[0].get('url')

            # Or try from dy search results
            if not first_conversation_url:
                dy_results = results.get('dy_conversations', {}).get('search_results', [])
                if dy_results:
                    first_conversation_url = dy_results[0].get('url')

            if first_conversation_url and first_conversation_url.startswith('http'):
                print("\n" + "="*50)
                print("STEP 5: Extracting first conversation content")
                print("="*50)
                results['first_conversation_content'] = await self.extract_conversation_content(first_conversation_url)

            # Save summary
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_file = self.output_dir / f"extraction_summary_{timestamp}.json"

            summary_data = {
                "timestamp": timestamp,
                "extraction_type": "complete_gemini_extraction",
                "tasks_completed": list(results.keys()),
                "summary": {
                    "gems_found": results.get('gems_list', {}).get('gems_count', 0),
                    "memory_gems_found": results.get('memory_gems', {}).get('matching_gems_count', 0),
                    "recent_conversations": results.get('recent_conversations', {}).get('conversations_count', 0),
                    "dy_conversations_found": results.get('dy_conversations', {}).get('results_count', 0),
                    "first_conversation_extracted": bool(results.get('first_conversation_content'))
                },
                "results": results
            }

            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)

            print(f"\n✅ Complete extraction summary saved to {summary_file}")

            # Print summary
            print("\n" + "="*50)
            print("EXTRACTION SUMMARY")
            print("="*50)
            print(f"Gems found: {summary_data['summary']['gems_found']}")
            print(f"Memory gems found: {summary_data['summary']['memory_gems_found']}")
            print(f"Recent conversations: {summary_data['summary']['recent_conversations']}")
            print(f"DY conversations found: {summary_data['summary']['dy_conversations_found']}")
            print(f"First conversation extracted: {summary_data['summary']['first_conversation_extracted']}")

        except Exception as e:
            print(f"❌ Error during extraction: {e}")

        finally:
            await self.close_browser()

    async def extract_specific_conversation(self, url: str):
        """Extract a specific conversation by URL."""
        if not await self.connect_to_browser():
            return

        try:
            result = await self.extract_conversation_content(url)
            return result
        except Exception as e:
            print(f"❌ Error extracting conversation: {e}")
        finally:
            await self.close_browser()


async def main():
    """Main function to run the extractor."""
    extractor = GeminiConversationExtractor()

    # Run the complete extraction as specified in WS_TODO.md
    await extractor.run_complete_extraction()


if __name__ == "__main__":
    asyncio.run(main())

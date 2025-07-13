#!/usr/bin/env python3
"""
Extract the IOC conversation using the search page discovery method
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False
    print("⚠️ markitdown not available. Install with: pip install markitdown")

async def extract_ioc_conversation():
    """Extract the IOC conversation specifically."""
    print("🎯 Extracting IOC conversation...")
    
    playwright = await async_playwright().start()
    
    try:
        # Connect to existing Chrome browser
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
        
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
        
        # Navigate directly to the IOC conversation
        # From the JSON, we know it's at conversation_15 or we can try the app URL
        print("🔍 Navigating directly to IOC conversation...")

        # Try different possible URLs for the IOC conversation
        possible_urls = [
            "https://gemini.google.com/app",  # Start with main app to find the conversation
        ]

        conversation_found = False
        for url in possible_urls:
            try:
                print(f"🔍 Trying URL: {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)

                # Wait for network stability
                print("⏳ Waiting for network stability...")
                try:
                    await page.wait_for_load_state('networkidle', timeout=30000)
                    print("✅ Network is stable")
                except Exception as e:
                    print(f"⚠️ Network stability timeout: {e}")

                # Additional wait for dynamic content
                await page.wait_for_timeout(3000)

                # Check if we're on a conversation page or need to find it
                current_url = page.url
                print(f"📍 Current URL: {current_url}")

                if "conversation_15" in current_url or "app/" in current_url:
                    # We might be on the conversation page
                    conversation_found = True
                    break
                elif url.endswith("/app"):
                    # We're on the main app, look for "Repo as IOC" in sidebar
                    print("🔍 Looking for 'Repo as IOC' conversation in sidebar...")

                    # First try to open the sidebar if it's collapsed
                    try:
                        sidebar_button = await page.query_selector('[data-test-id="side-nav-menu-button"]')
                        if sidebar_button:
                            print("🔄 Opening sidebar...")
                            await sidebar_button.click(force=True)
                            await page.wait_for_timeout(2000)
                    except:
                        print("⚠️ Could not open sidebar")

                    # Look for conversation elements in sidebar
                    conversation_elements = await page.query_selector_all('[data-test-id="conversation"]')

                    for element in conversation_elements:
                        try:
                            text = await element.text_content()
                            if text and ('Repo as IOC' in text or 'IOC' in text):
                                print(f"✅ Found IOC conversation: {text.strip()}")
                                # Scroll to element first
                                await element.scroll_into_view_if_needed()
                                await page.wait_for_timeout(1000)
                                await element.click(force=True)
                                # Wait for navigation
                                await page.wait_for_timeout(3000)
                                conversation_found = True
                                break
                        except Exception as e:
                            print(f"⚠️ Error clicking conversation element: {e}")
                            continue

                    # If not found in conversation elements, try buttons
                    if not conversation_found:
                        buttons = await page.query_selector_all('button')

                        for button in buttons:
                            try:
                                text = await button.text_content()
                                if text and ('Repo as IOC' in text or 'IOC' in text):
                                    print(f"✅ Found IOC conversation button: {text.strip()}")
                                    # Scroll to button first
                                    await button.scroll_into_view_if_needed()
                                    await page.wait_for_timeout(1000)
                                    await button.click(force=True)
                                    # Wait for navigation
                                    await page.wait_for_timeout(3000)
                                    conversation_found = True
                                    break
                            except Exception as e:
                                print(f"⚠️ Error clicking button: {e}")
                                continue

                    if conversation_found:
                        print(f"📍 Navigated to conversation, current URL: {page.url}")
                        break

            except Exception as e:
                print(f"⚠️ Error with URL {url}: {e}")
                continue

        if not conversation_found:
            print("❌ IOC conversation not found")
            return None
        
        # Wait for navigation and content loading
        print("⏳ Waiting for conversation to load...")
        try:
            await page.wait_for_load_state('networkidle', timeout=10000)
        except:
            print("⚠️ Network timeout, proceeding anyway...")
        await page.wait_for_timeout(5000)
        
        # Scroll to load complete history
        print("🔄 Loading complete conversation history...")
        for i in range(15):
            await page.keyboard.press('Home')
            await page.wait_for_timeout(200)
            await page.evaluate('window.scrollTo(0, 0)')
            await page.wait_for_timeout(200)
        
        try:
            await page.wait_for_load_state('networkidle', timeout=5000)
        except:
            print("⚠️ Network timeout during scroll, proceeding...")
        
        # Extract conversation content
        print("📄 Extracting conversation content...")
        
        conversation_html = await page.evaluate('''() => {
            // Look for the main conversation content area, not the sidebar
            const chatWindow = document.querySelector('chat-window-content');
            const chatHistory = document.querySelector('#chat-history');
            const conversationContainer = document.querySelector('.chat-history-scroll-container');

            // Try different selectors for the conversation content
            let contentElement = chatWindow || chatHistory || conversationContainer;

            if (contentElement) {
                console.log('Found conversation content area');
                return contentElement.outerHTML;
            }

            // Fallback: look for message elements specifically
            const messageSelectors = [
                '[data-message-id]',
                'article',
                '.message',
                '[role="article"]',
                '.conversation-turn',
                '.chat-message',
                '.response-container'
            ];

            let messageElements = [];
            for (const selector of messageSelectors) {
                const elements = document.querySelectorAll(selector);
                if (elements.length > 0) {
                    messageElements = Array.from(elements);
                    console.log(`Found ${elements.length} messages with selector: ${selector}`);
                    break;
                }
            }

            if (messageElements.length > 0) {
                let content = '';
                messageElements.forEach((element, index) => {
                    content += `<div class="message-${index}">${element.outerHTML}</div>\\n`;
                });
                return content;
            }

            // Last resort: get the main content but try to filter out sidebar
            const main = document.querySelector('main');
            if (main) {
                // Try to find the content area within main
                const contentArea = main.querySelector('.main-content, .content-container, .chat-container');
                if (contentArea) {
                    console.log('Found main content area');
                    return contentArea.outerHTML;
                }
                console.log('Using full main content as fallback');
                return main.outerHTML;
            }

            return 'No content found';
        }''')
        
        if not conversation_html or len(conversation_html.strip()) < 100:
            print("⚠️ Limited content extracted, trying fallback...")
            conversation_html = await page.evaluate('''() => {
                const main = document.querySelector('main');
                return main ? main.innerHTML : document.body.innerHTML;
            }''')
        
        # Save the conversation
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw HTML
        html_file = Path(f"gemini_extracts/ioc_conversation_{timestamp}.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>IOC Conversation</title>
</head>
<body>
    <h1>IOC Conversation</h1>
    <p><strong>Extracted:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>URL:</strong> {page.url}</p>
    <p><strong>Content Length:</strong> {len(conversation_html)} characters</p>
    <hr>
    {conversation_html}
</body>
</html>""")
        
        print(f"✅ Raw HTML saved to: {html_file}")
        
        # Convert to markdown if available
        if MARKITDOWN_AVAILABLE:
            try:
                print("🔄 Converting to markdown using markitdown...")
                markitdown = MarkItDown()
                result = markitdown.convert(str(html_file))
                
                # Clean and format markdown
                cleaned_content = f"""# IOC Conversation

**Extracted:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**URL:** {page.url}  
**Content Length:** {len(conversation_html)} characters

---

{result.text_content}

---

*Extracted from Gemini IOC conversation using search page method with markitdown conversion*
"""
                
                markdown_file = Path(f"gemini_extracts/ioc_conversation_{timestamp}.md")
                with open(markdown_file, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                
                print(f"✅ Markdown saved to: {markdown_file}")
                
                # Also print the content to console
                print("\n" + "="*80)
                print("IOC CONVERSATION CONTENT:")
                print("="*80)
                print(cleaned_content)
                print("="*80)
                
                return str(markdown_file)
                
            except Exception as e:
                print(f"⚠️ Markdown conversion error: {e}")
        else:
            print("⚠️ markitdown not available, skipping markdown conversion")
        
        return str(html_file)
        
    except Exception as e:
        print(f"❌ Error extracting IOC conversation: {e}")
        return None
    finally:
        await playwright.stop()

if __name__ == "__main__":
    result = asyncio.run(extract_ioc_conversation())
    if result:
        print(f"\n🎉 IOC conversation extracted successfully: {result}")
    else:
        print("\n❌ Failed to extract IOC conversation")

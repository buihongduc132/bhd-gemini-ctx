#!/usr/bin/env python3
"""
Page inspector tool to examine the actual DOM structure of Gemini pages.
This will help us identify the correct selectors to use.
"""

import asyncio
import json
from playwright.async_api import async_playwright

async def inspect_current_page():
    """Inspect the current page structure."""
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
        
        # Get the current page
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
        
        print(f"Current URL: {page.url}")
        print(f"Page Title: {await page.title()}")
        print("=" * 60)
        
        # Get page content
        content = await page.content()
        
        # Look for common elements
        print("🔍 Looking for common elements...")
        
        # Check for authentication status
        sign_in_elements = await page.query_selector_all('text="Sign in"')
        if sign_in_elements:
            print("❌ Not authenticated - Sign in required")
        else:
            print("✅ Appears to be authenticated")
        
        # Look for navigation elements
        nav_elements = await page.query_selector_all('nav')
        print(f"Found {len(nav_elements)} nav elements")
        
        # Look for sidebar elements
        sidebar_selectors = ['aside', '[role="navigation"]', '.sidebar']
        for selector in sidebar_selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"Found {len(elements)} elements with selector: {selector}")
        
        # Look for main content
        main_elements = await page.query_selector_all('main')
        print(f"Found {len(main_elements)} main elements")
        
        # Look for buttons and links
        buttons = await page.query_selector_all('button')
        links = await page.query_selector_all('a')
        print(f"Found {len(buttons)} buttons and {len(links)} links")
        
        # Look for specific Gemini elements
        gemini_selectors = [
            '[data-testid*="gem"]',
            '[data-testid*="conversation"]',
            '[data-testid*="chat"]',
            '.gem-card',
            '.conversation-item'
        ]
        
        print("\n🔍 Looking for Gemini-specific elements...")
        for selector in gemini_selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"Found {len(elements)} elements with selector: {selector}")
                # Get text content of first few elements
                for i, element in enumerate(elements[:3]):
                    try:
                        text = await element.text_content()
                        if text:
                            print(f"  Element {i+1}: {text[:100]}")
                    except:
                        pass
        
        # Save page structure for analysis
        page_info = {
            "url": page.url,
            "title": await page.title(),
            "timestamp": "now",
            "element_counts": {
                "nav": len(nav_elements),
                "main": len(main_elements),
                "buttons": len(buttons),
                "links": len(links)
            }
        }
        
        with open("flow/page_inspection.json", "w") as f:
            json.dump(page_info, f, indent=2)
        
        print(f"\n📄 Page inspection saved to flow/page_inspection.json")
        
        await playwright.stop()
        
    except Exception as e:
        print(f"❌ Error inspecting page: {e}")

async def navigate_and_inspect(url: str):
    """Navigate to a specific URL and inspect it."""
    try:
        playwright = await async_playwright().start()
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
        
        print(f"📍 Navigating to: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(3000)
        
        print(f"✅ Loaded: {await page.title()}")
        print(f"URL: {page.url}")
        
        # Take a screenshot for visual inspection
        screenshot_path = f"flow/screenshot_{url.replace('/', '_').replace(':', '')}.png"
        await page.screenshot(path=screenshot_path)
        print(f"📸 Screenshot saved to: {screenshot_path}")
        
        # Get all visible text elements
        all_text_elements = await page.query_selector_all('*')
        visible_texts = []
        
        for element in all_text_elements[:50]:  # Limit to first 50 elements
            try:
                if await element.is_visible():
                    text = await element.text_content()
                    if text and len(text.strip()) > 5:
                        tag_name = await element.evaluate('el => el.tagName')
                        class_name = await element.get_attribute('class') or ''
                        visible_texts.append({
                            "tag": tag_name.lower(),
                            "class": class_name,
                            "text": text.strip()[:100]
                        })
            except:
                continue
        
        print(f"\n📝 Found {len(visible_texts)} visible text elements:")
        for i, item in enumerate(visible_texts[:10]):  # Show first 10
            print(f"  {i+1}. <{item['tag']}> {item['text']}")
        
        await playwright.stop()
        
    except Exception as e:
        print(f"❌ Error navigating and inspecting: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
        asyncio.run(navigate_and_inspect(url))
    else:
        asyncio.run(inspect_current_page())

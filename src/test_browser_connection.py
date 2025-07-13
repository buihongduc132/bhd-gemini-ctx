#!/usr/bin/env python3
"""
Test script to verify Playwright connection to existing Chrome instance.
"""

import asyncio
from playwright.async_api import async_playwright

async def test_connection():
    """Test connection to Chrome browser."""
    print("🔍 Testing Playwright connection...")

    try:
        # Connect to existing Chrome instance
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
        print("✅ Connected to Chrome browser")

        # Get or create a page
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

        print("✅ Page ready")

        # Navigate to Gemini
        print("🚀 Navigating to Gemini...")
        try:
            await page.goto("https://gemini.google.com", wait_until="domcontentloaded", timeout=10000)
            title = await page.title()
            print(f"✅ Page loaded: {title}")
        except Exception as nav_error:
            print(f"⚠️ Navigation timeout, but connection works: {nav_error}")
            # Still consider this a success since we connected to the browser

        # Clean up
        await playwright.stop()

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    if success:
        print("\n🎉 Playwright connection is working correctly!")
        print("You can now run: python gemini_conversation_extractor.py")
    else:
        print("\n💡 Make sure Chrome is running with:")
        print("google-chrome --remote-debugging-port=9222 --user-data-dir=/home/bhd/ChromeProfiles/default --no-first-run &")

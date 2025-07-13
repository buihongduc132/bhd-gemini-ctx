#!/usr/bin/env python3
"""
API server for Gemini conversation extraction.
Provides REST endpoints for all extraction functions.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from playwright.async_api import async_playwright

app = FastAPI(title="Gemini Extractor API", version="1.0.0")

class GeminiExtractorAPI:
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
    
    async def list_conversations(self) -> Dict:
        """List recent conversations."""
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
                                "id": f"button_conv_{i+1}",
                                "title": text_clean,
                                "button_index": i,
                                "url": f"https://gemini.google.com/app/conversation_{i+1}"
                            })
                except:
                    pass
            
            return {
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "task": "list_conversations",
                "url": page.url,
                "conversations_count": len(conversations),
                "conversations": conversations
            }
            
        finally:
            await playwright.stop()
    
    async def search_conversations(self, query: str) -> Dict:
        """Search conversations for a query."""
        all_conversations_data = await self.list_conversations()
        all_conversations = all_conversations_data.get("conversations", [])
        
        # Filter conversations
        matching_conversations = []
        for conv in all_conversations:
            if query.lower() in conv['title'].lower():
                matching_conversations.append(conv)
        
        return {
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "task": "search_conversations",
            "query": query,
            "total_conversations_searched": len(all_conversations),
            "matching_conversations_count": len(matching_conversations),
            "matching_conversations": matching_conversations,
            "first_result": matching_conversations[0] if matching_conversations else None
        }
    
    async def extract_conversation(self, button_index: int) -> Dict:
        """Extract conversation content by button index."""
        playwright, browser, page = await self.connect()
        
        try:
            # Navigate and open sidebar
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
            
            # Click the specific conversation button
            all_buttons = await page.query_selector_all('button')
            if button_index >= len(all_buttons):
                raise HTTPException(status_code=404, detail=f"Button index {button_index} not found")
            
            target_button = all_buttons[button_index]
            button_text = await target_button.text_content()
            
            await target_button.click()
            await page.wait_for_timeout(3000)
            
            # Scroll to top for complete history
            for i in range(10):
                await page.keyboard.press('Home')
                await page.wait_for_timeout(500)
                await page.evaluate('window.scrollTo(0, 0)')
                await page.wait_for_timeout(500)
            
            # Extract messages (simplified for API)
            messages = []
            main_element = await page.query_selector('main')
            if main_element:
                text_divs = await main_element.query_selector_all('div')
                for i, div in enumerate(text_divs[:50]):
                    try:
                        text = await div.text_content()
                        if text and len(text.strip()) > 20:
                            messages.append({
                                "index": i,
                                "content": text.strip()[:500],  # Limit content length
                                "length": len(text.strip())
                            })
                    except:
                        continue
            
            return {
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "task": "extract_conversation",
                "button_index": button_index,
                "conversation_title": button_text.strip(),
                "url": page.url,
                "messages_count": len(messages),
                "messages": messages[:10]  # Return only first 10 messages for API
            }
            
        finally:
            await playwright.stop()

# Initialize extractor
extractor = GeminiExtractorAPI()

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Gemini Extractor API", "version": "1.0.0"}

@app.get("/conversations")
async def get_conversations():
    """List all recent conversations."""
    try:
        result = await extractor.list_conversations()
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations/search/{query}")
async def search_conversations_endpoint(query: str):
    """Search conversations for a specific query."""
    try:
        result = await extractor.search_conversations(query)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations/extract/{button_index}")
async def extract_conversation_endpoint(button_index: int):
    """Extract conversation content by button index."""
    try:
        result = await extractor.extract_conversation(button_index)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
        await playwright.stop()
        return {"status": "healthy", "chrome_connected": True}
    except Exception as e:
        return {"status": "unhealthy", "chrome_connected": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

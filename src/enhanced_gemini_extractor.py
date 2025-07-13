#!/usr/bin/env python3
"""
Enhanced Gemini Conversation Extractor for WS_TODO2
Extracts conversations with proper message structure, sender identification, and timestamps.
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

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
        self.output_dir = Path("gemini_extracts")
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
    
    def parse_conversation_structure(self, html_content):
        """Parse HTML to extract structured conversation data."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find conversation containers
        conversation_containers = soup.find_all('div', class_='conversation-container')
        
        messages = []
        for container in conversation_containers:
            message_id = container.get('id', '')
            
            # Look for user queries
            user_query = container.find('user-query')
            if user_query:
                query_text = self.extract_user_message(user_query)
                if query_text:
                    messages.append({
                        'id': message_id,
                        'sender': 'user',
                        'content': query_text,
                        'timestamp': self.extract_timestamp(container),
                        'type': 'user_message'
                    })
            
            # Look for model responses
            model_response = container.find('model-response')
            if model_response:
                response_content = self.extract_model_response(model_response)
                if response_content:
                    messages.append({
                        'id': message_id,
                        'sender': 'assistant',
                        'content': response_content,
                        'timestamp': self.extract_timestamp(container),
                        'type': 'assistant_message'
                    })
        
        return messages
    
    def extract_user_message(self, user_query_element):
        """Extract user message content."""
        query_texts = []
        
        # Look for query text elements
        query_elements = user_query_element.find_all('p', class_='query-text-line')
        for element in query_elements:
            text = element.get_text(strip=True)
            if text and text not in ['', '\n']:
                query_texts.append(text)
        
        return '\n'.join(query_texts) if query_texts else None
    
    def extract_model_response(self, model_response_element):
        """Extract model response content."""
        # Look for message content
        message_content = model_response_element.find('message-content')
        if not message_content:
            return None
        
        # Extract markdown content
        markdown_div = message_content.find('div', class_='markdown')
        if markdown_div:
            # Clean up the content
            content = self.clean_response_content(markdown_div)
            return content
        
        return None
    
    def clean_response_content(self, markdown_element):
        """Clean and format response content."""
        # Remove script tags and other unwanted elements
        for script in markdown_element.find_all(['script', 'style']):
            script.decompose()

        # Convert to markdown-like format while preserving structure
        content = self.html_to_markdown(markdown_element)

        return content

    def html_to_markdown(self, element):
        """Convert HTML element to markdown format."""
        if MARKITDOWN_AVAILABLE and self.markitdown:
            try:
                # Create a temporary HTML file
                temp_html = f"<html><body>{str(element)}</body></html>"
                temp_file = self.output_dir / "temp_conversion.html"

                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(temp_html)

                # Convert using markitdown
                result = self.markitdown.convert(str(temp_file))

                # Clean up temp file
                temp_file.unlink()

                return result.text_content.strip()
            except Exception as e:
                print(f"⚠️ Markitdown conversion failed: {e}")

        # Fallback: simple HTML to text conversion
        content = str(element)
        content = re.sub(r'<[^>]+>', '', content)  # Remove HTML tags
        content = re.sub(r'\s+', ' ', content)     # Normalize whitespace
        content = content.strip()

        return content
    
    def extract_timestamp(self, container):
        """Extract timestamp from message container."""
        # Look for timestamp indicators in the HTML
        timestamp_selectors = [
            'time',
            '[data-timestamp]',
            '.timestamp',
            '.message-time',
            '[datetime]'
        ]

        for selector in timestamp_selectors:
            timestamp_elem = container.find(selector)
            if timestamp_elem:
                # Try to get datetime attribute
                timestamp = timestamp_elem.get('datetime') or timestamp_elem.get('data-timestamp')
                if timestamp:
                    try:
                        # Parse and return ISO format
                        parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        return parsed_time.isoformat()
                    except:
                        pass

                # Try to parse text content
                text_content = timestamp_elem.get_text(strip=True)
                if text_content:
                    try:
                        # Try common timestamp formats
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%m/%d/%Y %H:%M']:
                            try:
                                parsed_time = datetime.strptime(text_content, fmt)
                                return parsed_time.isoformat()
                            except:
                                continue
                    except:
                        pass

        # Fallback: use current time
        return datetime.now().isoformat()
    
    async def extract_conversation_with_structure(self, conversation_url, title=""):
        """Extract conversation with proper message structure."""
        print(f"📄 Extracting structured conversation: {title}")
        
        playwright, browser, page = await self.connect()
        
        try:
            # Navigate to conversation
            await page.goto(conversation_url, wait_until="domcontentloaded", timeout=15000)
            
            # Wait for content to load
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
            except:
                print("⚠️ Network timeout, proceeding...")
            
            await page.wait_for_timeout(5000)
            
            # Scroll to load complete history
            print("🔄 Loading complete conversation history...")
            for i in range(15):
                await page.keyboard.press('Home')
                await page.wait_for_timeout(200)
            
            # Extract raw HTML
            conversation_html = await page.evaluate('''() => {
                const chatHistory = document.querySelector('#chat-history');
                if (chatHistory) {
                    return chatHistory.outerHTML;
                }
                
                const main = document.querySelector('main');
                return main ? main.outerHTML : document.body.outerHTML;
            }''')
            
            # Parse conversation structure
            messages = self.parse_conversation_structure(conversation_html)
            
            # Save structured data
            result = await self.save_structured_conversation(
                conversation_html, messages, title, page.url
            )
            
            return result
            
        except Exception as e:
            print(f"❌ Error extracting conversation: {e}")
            return None
        finally:
            await playwright.stop()
    
    async def save_structured_conversation(self, html_content, messages, title, url):
        """Save conversation in multiple structured formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
        
        # Save raw HTML
        html_file = self.output_dir / f"structured_{safe_title}_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Structured Gemini Conversation: {title}</title>
</head>
<body>
    <h1>{title}</h1>
    <p><strong>Extracted:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>URL:</strong> {url}</p>
    <p><strong>Messages:</strong> {len(messages)}</p>
    <hr>
    {html_content}
</body>
</html>""")
        
        # Save structured JSON
        json_file = self.output_dir / f"structured_{safe_title}_{timestamp}.json"
        structured_data = {
            "title": title,
            "url": url,
            "extracted_at": datetime.now().isoformat(),
            "message_count": len(messages),
            "messages": messages
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
        
        # Create structured markdown
        markdown_content = self.create_structured_markdown(structured_data)
        
        markdown_file = self.output_dir / f"structured_{safe_title}_{timestamp}.md"
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ Structured files saved:")
        print(f"  - HTML: {html_file}")
        print(f"  - JSON: {json_file}")
        print(f"  - Markdown: {markdown_file}")
        
        return {
            "html_file": str(html_file),
            "json_file": str(json_file),
            "markdown_file": str(markdown_file),
            "message_count": len(messages)
        }
    
    def create_structured_markdown(self, structured_data):
        """Create well-formatted markdown from structured data."""
        md_content = f"""# {structured_data['title']}

**Extracted:** {structured_data['extracted_at']}  
**URL:** {structured_data['url']}  
**Messages:** {structured_data['message_count']}

---

"""
        
        for i, message in enumerate(structured_data['messages']):
            sender_icon = "👤" if message['sender'] == 'user' else "🤖"
            sender_name = "User" if message['sender'] == 'user' else "Assistant"
            
            md_content += f"""## {sender_icon} {sender_name} (Message {i+1})

**ID:** {message['id']}  
**Timestamp:** {message['timestamp']}  
**Type:** {message['type']}

{message['content']}

---

"""
        
        md_content += f"""
*Extracted using Enhanced Gemini Extractor with structured message parsing*
"""
        
        return md_content

# Usage functions
async def extract_ioc_structured():
    """Extract IOC conversation with structure."""
    extractor = EnhancedGeminiExtractor()
    
    # Use the known IOC conversation URL
    ioc_url = "https://gemini.google.com/app/868452c61789e8d8"
    
    result = await extractor.extract_conversation_with_structure(
        ioc_url, "Repo as IOC - Structured"
    )
    
    if result:
        print(f"\n🎉 Structured extraction complete!")
        print(f"Messages extracted: {result['message_count']}")
        return result
    else:
        print("\n❌ Structured extraction failed")
        return None

if __name__ == "__main__":
    asyncio.run(extract_ioc_structured())

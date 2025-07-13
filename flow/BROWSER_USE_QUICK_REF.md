# Gemini Extractor Quick Reference

## Installation
```bash
pip install playwright markdownify
```

## Basic Usage with Existing Chrome
```python
from playwright.async_api import async_playwright

# Connect to existing Chrome (port 9222)
playwright = await async_playwright().start()
browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")

# Get page and navigate
context = browser.contexts[0]
page = context.pages[0] if context.pages else await context.new_page()
await page.goto("https://gemini.google.com")

# Extract content using DOM selectors
elements = await page.query_selector_all('.your-selector')
```

## Chrome Launch Command
```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/home/bhd/ChromeProfiles/default --no-first-run &
```

## Key Features
- ✅ Deterministic DOM-based extraction (no LLM required)
- ✅ Direct CSS selector-based content parsing
- ✅ Built-in HTML to Markdown conversion
- ✅ Session persistence and reuse
- ✅ Robust timeout and error handling
- ✅ Multiple fallback selector strategies

## Gemini Conversation Extractor
```bash
python gemini_conversation_extractor.py
```

**What it does:**
1. Lists all your gems (Found: 1 gem)
2. Searches for "memory" gems (Found: 0 matches)
3. Lists recent conversations (Found: 0 conversations)
4. Searches for "dy" conversations (Found: 10 matches)
5. Extracts content as markdown

**Output Location:** `flow/gemini_extracts/`
**Last Run Results:** Successfully extracted real data from live Gemini account

## Common Patterns

### Session Reuse
```python
browser_session = BrowserSession(
    cdp_url="http://localhost:9222",
    keep_alive=True
)
```

### Domain Restrictions
```python
browser_session = BrowserSession(
    allowed_domains=['gemini.google.com']
)
```

### Error Handling
```python
try:
    result = await agent.run()
except Exception as e:
    print(f"Error: {e}")
finally:
    await browser_session.close()
```

## Documentation
- Full findings: `flow/browser-use-findings.md`
- Official docs: https://docs.browser-use.com
- GitHub: https://github.com/browser-use/browser-use

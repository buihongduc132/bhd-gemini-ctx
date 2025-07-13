# Network Handling and Dynamic Content Loading

## Overview

This document explains the critical importance of proper network handling when extracting Gemini conversations. Gemini uses dynamic loading, WebSockets, and Angular components that require specific timing strategies.

## Why Network Handling is Critical

### Gemini's Dynamic Architecture
- **Angular Framework**: Components load asynchronously
- **WebSocket Communication**: Real-time content updates
- **Lazy Loading**: Content loads as needed
- **Dynamic DOM**: Elements appear after network requests

### Problems Without Proper Waiting
```python
# ❌ WRONG - Will get incomplete content
await page.goto(url)
content = await page.query_selector('main').inner_html()
# Result: Empty or partial content
```

```python
# ✅ CORRECT - Wait for stability
await page.goto(url, wait_until="domcontentloaded")
await page.wait_for_load_state('networkidle')
await page.wait_for_timeout(3000)
content = await page.query_selector('main').inner_html()
# Result: Complete conversation content
```

## Network Stability Strategies

### 1. Basic Load State Waiting
```python
async def basic_network_wait(page, url):
    # Navigate with proper wait condition
    await page.goto(url, wait_until="domcontentloaded", timeout=15000)
    
    # Wait for network to be idle (no requests for 500ms)
    await page.wait_for_load_state('networkidle', timeout=30000)
    
    print("✅ Basic network stability achieved")
```

**Load States:**
- `domcontentloaded`: DOM is ready, but resources may still load
- `load`: All resources loaded (images, CSS, JS)
- `networkidle`: No network requests for 500ms (recommended)

### 2. Enhanced Stability Waiting
```python
async def enhanced_network_wait(page, timeout=30000):
    """Enhanced network waiting with multiple strategies."""
    print("⏳ Waiting for network stability...")
    
    try:
        # Primary: Wait for network idle
        await page.wait_for_load_state('networkidle', timeout=timeout)
        print("✅ Network idle achieved")
        
        # Secondary: Additional wait for dynamic content
        await page.wait_for_timeout(2000)
        print("✅ Dynamic content buffer complete")
        
        # Tertiary: Wait for specific elements if needed
        try:
            await page.wait_for_selector('main', timeout=5000)
            print("✅ Main content area loaded")
        except:
            print("⚠️ Main selector timeout, proceeding...")
            
    except Exception as e:
        print(f"⚠️ Network stability timeout: {e}")
        # Fallback: Minimum wait
        await page.wait_for_timeout(5000)
```

### 3. WebSocket-Aware Waiting
```python
async def websocket_aware_wait(page):
    """Wait for WebSocket connections to stabilize."""
    
    # Monitor WebSocket activity
    websocket_count = await page.evaluate('''() => {
        return window.performance.getEntriesByType('resource')
            .filter(r => r.name.includes('ws://') || r.name.includes('wss://'))
            .length;
    }''')
    
    if websocket_count > 0:
        print(f"🔌 Detected {websocket_count} WebSocket connections")
        # Extra wait for WebSocket data
        await page.wait_for_timeout(5000)
    
    # Check for ongoing network activity
    active_requests = await page.evaluate('''() => {
        return window.performance.getEntriesByType('resource')
            .filter(r => r.responseEnd === 0)  // Still loading
            .length;
    }''')
    
    if active_requests > 0:
        print(f"📡 {active_requests} requests still active, waiting...")
        await page.wait_for_timeout(3000)
```

## Page-Specific Network Patterns

### 1. Search Page Loading
```python
async def wait_for_search_page(page):
    """Specific waiting strategy for search page."""
    await page.goto("https://gemini.google.com/search", 
                   wait_until="domcontentloaded", timeout=15000)
    
    # Wait for conversation list to load
    await page.wait_for_load_state('networkidle', timeout=20000)
    
    # Additional wait for conversation elements
    try:
        await page.wait_for_function('''() => {
            const conversations = document.querySelectorAll('generic');
            return conversations.length > 5;  // Expect multiple conversations
        }''', timeout=10000)
        print("✅ Conversation list loaded")
    except:
        print("⚠️ Conversation list timeout")
    
    await page.wait_for_timeout(2000)
```

### 2. Conversation Page Loading
```python
async def wait_for_conversation_page(page, conversation_url):
    """Specific waiting strategy for individual conversations."""
    await page.goto(conversation_url, 
                   wait_until="domcontentloaded", timeout=15000)
    
    # Wait for initial load
    await page.wait_for_load_state('networkidle', timeout=20000)
    
    # Wait for conversation content to appear
    try:
        await page.wait_for_function('''() => {
            const main = document.querySelector('main');
            if (!main) return false;
            
            const text = main.textContent || '';
            return text.length > 100;  // Expect substantial content
        }''', timeout=15000)
        print("✅ Conversation content loaded")
    except:
        print("⚠️ Conversation content timeout")
    
    # Extra wait for complete rendering
    await page.wait_for_timeout(3000)
```

### 3. Post-Click Navigation
```python
async def wait_after_click(page, element):
    """Wait for navigation after clicking conversation."""
    # Get current URL before click
    current_url = page.url
    
    # Click element
    await element.click()
    
    # Wait for URL change (navigation)
    try:
        await page.wait_for_function(f'''() => {{
            return window.location.href !== "{current_url}";
        }}''', timeout=10000)
        print("✅ Navigation detected")
    except:
        print("⚠️ No navigation detected")
    
    # Wait for new page to load
    await page.wait_for_load_state('networkidle', timeout=20000)
    await page.wait_for_timeout(3000)
```

## Scroll-Based Content Loading

### Complete History Loading
```python
async def load_complete_conversation_history(page):
    """Scroll to ensure complete conversation history loads."""
    print("🔄 Loading complete conversation history...")
    
    # Scroll to top multiple times
    for i in range(15):
        await page.keyboard.press('Home')
        await page.wait_for_timeout(200)
        
        # Also use JavaScript scroll
        await page.evaluate('window.scrollTo(0, 0)')
        await page.wait_for_timeout(200)
    
    # Wait for any additional content to load
    await page.wait_for_load_state('networkidle', timeout=15000)
    
    # Verify content stability
    initial_length = await page.evaluate('document.body.textContent.length')
    await page.wait_for_timeout(2000)
    final_length = await page.evaluate('document.body.textContent.length')
    
    if abs(final_length - initial_length) > 100:
        print("⚠️ Content still changing, additional wait...")
        await page.wait_for_timeout(3000)
    
    print("✅ Conversation history loading complete")
```

### Progressive Loading Detection
```python
async def detect_progressive_loading(page):
    """Detect if content is still loading progressively."""
    
    # Take content snapshots
    snapshots = []
    for i in range(3):
        content_length = await page.evaluate('document.body.textContent.length')
        snapshots.append(content_length)
        await page.wait_for_timeout(1000)
    
    # Check if content is still growing
    if snapshots[2] > snapshots[1] > snapshots[0]:
        print("📈 Progressive loading detected, extended wait...")
        await page.wait_for_timeout(5000)
        return True
    
    return False
```

## Error Handling and Timeouts

### Timeout Management
```python
async def robust_network_wait(page, max_timeout=60000):
    """Robust network waiting with fallback strategies."""
    start_time = time.time()
    
    try:
        # Primary strategy
        await page.wait_for_load_state('networkidle', timeout=max_timeout // 2)
        
    except TimeoutError:
        elapsed = (time.time() - start_time) * 1000
        remaining = max_timeout - elapsed
        
        if remaining > 5000:
            print(f"⚠️ Network idle timeout, trying load state...")
            try:
                await page.wait_for_load_state('load', timeout=remaining)
            except TimeoutError:
                print(f"⚠️ Load state timeout, using minimum wait...")
                await page.wait_for_timeout(5000)
        else:
            print(f"⚠️ Maximum timeout reached, proceeding...")
```

### Network Error Recovery
```python
async def handle_network_errors(page, url, max_retries=3):
    """Handle network errors with retry logic."""
    
    for attempt in range(max_retries):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_load_state('networkidle', timeout=30000)
            return True
            
        except Exception as e:
            print(f"❌ Network error (attempt {attempt + 1}): {e}")
            
            if attempt < max_retries - 1:
                print(f"🔄 Retrying in {(attempt + 1) * 2} seconds...")
                await page.wait_for_timeout((attempt + 1) * 2000)
            else:
                print(f"❌ Max retries reached, failing...")
                return False
```

## Performance Monitoring

### Network Activity Monitoring
```python
async def monitor_network_activity(page):
    """Monitor ongoing network activity."""
    
    network_info = await page.evaluate('''() => {
        const resources = performance.getEntriesByType('resource');
        const recent = resources.filter(r => 
            (performance.now() - r.startTime) < 5000  // Last 5 seconds
        );
        
        return {
            total_requests: resources.length,
            recent_requests: recent.length,
            active_requests: resources.filter(r => r.responseEnd === 0).length,
            websockets: resources.filter(r => 
                r.name.includes('ws://') || r.name.includes('wss://')
            ).length
        };
    }''')
    
    print(f"📊 Network Activity: {network_info}")
    return network_info
```

### Content Stability Verification
```python
async def verify_content_stability(page, stability_duration=3000):
    """Verify content has stabilized."""
    
    print("🔍 Verifying content stability...")
    
    # Take initial snapshot
    initial_content = await page.evaluate('document.body.textContent.length')
    
    # Wait and check again
    await page.wait_for_timeout(stability_duration)
    final_content = await page.evaluate('document.body.textContent.length')
    
    difference = abs(final_content - initial_content)
    
    if difference < 50:  # Minimal change threshold
        print("✅ Content is stable")
        return True
    else:
        print(f"⚠️ Content changed by {difference} characters")
        return False
```

## Best Practices Summary

### Do's ✅
- Always use `wait_for_load_state('networkidle')`
- Add buffer time after network idle (2-3 seconds)
- Scroll to load complete conversation history
- Monitor WebSocket activity for dynamic content
- Use progressive loading detection
- Implement retry logic for network errors

### Don'ts ❌
- Don't rely only on `domcontentloaded`
- Don't skip additional timeout after network idle
- Don't assume content is complete without verification
- Don't ignore WebSocket connections
- Don't proceed without minimum stability checks

---

**Next Step:** After understanding network handling, proceed to [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for the complete working implementation.

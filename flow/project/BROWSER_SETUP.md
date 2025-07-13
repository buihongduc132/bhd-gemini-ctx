# Browser Setup for Gemini Extraction

## Overview

This document details the exact browser configuration required for Gemini conversation extraction. The setup enables remote debugging and maintains authentication state.

## Chrome Browser Configuration

### 1. Start Chrome with Remote Debugging

**Command:**
```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/home/bhd/ChromeProfiles/default --no-first-run &
```

**Parameter Breakdown:**
- `--remote-debugging-port=9222`: Enables Chrome DevTools Protocol on port 9222
- `--user-data-dir=/home/bhd/ChromeProfiles/default`: Uses dedicated profile directory
- `--no-first-run`: Skips first-run setup dialogs
- `&`: Runs in background

### 2. Verify Chrome Debug Connection

**Test Connection:**
```bash
curl http://localhost:9222/json/version
```

**Expected Response:**
```json
{
   "Browser": "Chrome/120.0.6099.109",
   "Protocol-Version": "1.3",
   "User-Agent": "Mozilla/5.0...",
   "V8-Version": "12.0.267.8",
   "WebKit-Version": "537.36",
   "webSocketDebuggerUrl": "ws://localhost:9222/devtools/browser/..."
}
```

### 3. Authentication Requirements

**Manual Steps:**
1. Open Chrome browser (should auto-open with debug flags)
2. Navigate to https://gemini.google.com
3. Sign in with Google account if not already authenticated
4. Verify access to conversations and search page

**Verification:**
- Can access https://gemini.google.com/search
- Can see conversation list
- Can click on conversations and view content

## Profile Directory Structure

**Recommended Setup:**
```
/home/bhd/ChromeProfiles/
└── default/
    ├── Default/
    │   ├── Cookies
    │   ├── Local Storage/
    │   └── Session Storage/
    └── First Run
```

**Benefits:**
- Persistent authentication
- Saved preferences (dark/light theme)
- Extension state preservation
- Consistent session across restarts

## Troubleshooting

### Common Issues

**1. Port Already in Use**
```bash
# Check what's using port 9222
lsof -i :9222

# Kill existing Chrome processes
pkill -f "chrome.*remote-debugging-port"
```

**2. Authentication Lost**
```bash
# Restart Chrome with same profile
google-chrome --remote-debugging-port=9222 --user-data-dir=/home/bhd/ChromeProfiles/default --no-first-run &
```

**3. Profile Corruption**
```bash
# Backup and reset profile if needed
mv /home/bhd/ChromeProfiles/default /home/bhd/ChromeProfiles/default.bak
mkdir -p /home/bhd/ChromeProfiles/default
# Re-authenticate manually
```

### Validation Steps

**1. Check Chrome Process:**
```bash
ps aux | grep chrome | grep remote-debugging-port
```

**2. Test CDP Connection:**
```bash
curl http://localhost:9222/json/list
```

**3. Verify Gemini Access:**
- Open http://localhost:9222 in another browser
- Navigate to Gemini tab
- Confirm authentication status

## Security Considerations

**Important Notes:**
- Remote debugging exposes browser control to localhost
- Only run on trusted networks
- Use dedicated profile for automation
- Don't expose port 9222 externally

**Best Practices:**
- Use dedicated Chrome profile for automation
- Regularly backup profile directory
- Monitor for unauthorized access
- Close debug session when not needed

## Alternative Configurations

### Headless Mode (Not Recommended)
```bash
# Headless mode - authentication issues
google-chrome --headless --remote-debugging-port=9222 --user-data-dir=/home/bhd/ChromeProfiles/default
```

**Issues with Headless:**
- Google authentication may fail
- Some dynamic content doesn't load
- Harder to debug issues visually

### Docker Setup (Advanced)
```dockerfile
# Example Docker setup (requires X11 forwarding)
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y google-chrome-stable
CMD ["google-chrome", "--remote-debugging-port=9222", "--no-sandbox", "--disable-dev-shm-usage"]
```

## Integration with Python

**Connection Test:**
```python
from playwright.async_api import async_playwright

async def test_connection():
    playwright = await async_playwright().start()
    try:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
        contexts = browser.contexts
        print(f"Connected! Found {len(contexts)} contexts")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
    finally:
        await playwright.stop()
```

## Environment Variables

**Optional Configuration:**
```bash
export CHROME_DEBUG_PORT=9222
export CHROME_PROFILE_DIR=/home/bhd/ChromeProfiles/default
export GEMINI_BASE_URL=https://gemini.google.com
```

**Usage in Scripts:**
```python
import os
CDP_PORT = int(os.getenv('CHROME_DEBUG_PORT', 9222))
PROFILE_DIR = os.getenv('CHROME_PROFILE_DIR', '/home/bhd/ChromeProfiles/default')
```

---

**Next Step:** Once browser is properly configured, proceed to [DOM_INSPECTION.md](DOM_INSPECTION.md) to learn how to inspect Gemini's page structure.

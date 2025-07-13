# Gemini UI Structure Documentation

**Generated:** 2025-07-13 18:50  
**Purpose:** Comprehensive UI structure reference for automation and extraction

## 🎯 Overview

This document provides detailed information about Google Gemini's UI structure, selectors, and navigation patterns based on extensive browser automation and extraction work.

## 🏗️ Main Page Structure

### Base URLs
- **Main App**: `https://gemini.google.com/app`
- **Specific Conversation**: `https://gemini.google.com/app/{conversation_id}`
- **Gems**: `https://gemini.google.com/gem/{gem_id}`
- **Search**: `https://gemini.google.com/search`
- **Gems View**: `https://gemini.google.com/gems/view`

### Page Layout
```
┌─────────────────────────────────────────────────────────┐
│ Top Bar (Logo, Mode Switcher, Actions)                 │
├─────────────────────────────────────────────────────────┤
│ Sidebar │ Main Content Area                             │
│         │                                               │
│ - Menu  │ - Chat History Container                      │
│ - Gems  │ - Conversation Messages                       │
│ - Recent│ - Input Area                                  │
│ - Search│                                               │
└─────────────────────────────────────────────────────────┘
```

## 🔍 Key Selectors & Elements

### Navigation & Menu
```css
/* Main menu button */
[data-test-id="side-nav-menu-button"]
.main-menu-button

/* Sidebar container */
.side-nav-menu-button
mat-sidenav-container

/* Search navigation */
search-nav-bar
.search-nav-bar-container
```

### Sidebar Elements
```css
/* Gems section */
bot-list
.bots-list-container
[data-test-id="item"]
.bot-item

/* Recent conversations */
conversations-list
[data-test-id="conversation"]
.conversation
.conversation-title

/* Conversation pin status */
.conversation-pin-icon
.ng-star-inserted
```

### Main Content Area
```css
/* Chat window */
chat-window
chat-window-content
.chat-container

/* Chat history */
#chat-history
.chat-history-scroll-container
[data-test-id="chat-history-container"]

/* Conversation containers */
.conversation-container
.message-actions-hover-boundary
```

### Message Structure
```css
/* User messages */
user-query
.user-query-container
.user-query-bubble-container
.query-content
.query-text
.query-text-line

/* Assistant responses */
model-response
response-container
.response-container
.presented-response-container
message-content
.markdown
.model-response-text
```

### Message Metadata
```css
/* Message IDs (in container attributes) */
.conversation-container[id="message_id"]

/* Response containers with tracking */
response-container[jslog*="BardVeMetadataKey"]

/* Message content areas */
#message-content-id-r_{message_id}
#model-response-message-content{message_id}
```

## 🎨 UI Components

### Avatars & Icons
```css
/* Gemini avatar */
bard-avatar
.bard-avatar
.avatar-component
.avatar_primary_animation

/* User profile */
.profile-picture
```

### Controls & Buttons
```css
/* TTS controls */
tts-control
.tts-button
[aria-label="Listen"]

/* More options */
[data-test-id="more-menu-button"]
.more-button

/* Copy buttons */
.copy-button
[aria-label="Copy code"]

/* Expand buttons */
.expand-button
[aria-label="Expand"]
```

### Code Blocks
```css
/* Code containers */
code-block
.code-block
.formatted-code-block-internal-container
.code-container
[data-test-id="code-content"]

/* Code decoration */
.code-block-decoration
.header-formatted
```

## 🔄 Dynamic Loading Patterns

### Network Stability
- Pages use dynamic loading with Angular components
- Wait for `networkidle` state: `page.wait_for_load_state('networkidle')`
- Common timeout: 10-30 seconds
- Fallback: Proceed after timeout with warning

### Conversation Loading
```javascript
// Wait for conversation to load
await page.wait_for_selector('#chat-history', { timeout: 15000 });

// Scroll to load complete history
for (let i = 0; i < 15; i++) {
    await page.keyboard.press('Home');
    await page.wait_for_timeout(200);
}
```

### Content Extraction
```javascript
// Extract main conversation content
const chatHistory = document.querySelector('#chat-history');
const conversationContainers = document.querySelectorAll('.conversation-container');
```

## 📱 Mobile vs Desktop

### Responsive Classes
```css
/* Mobile indicators */
.is-mobile
.mobile
.ng-star-inserted

/* Desktop specific */
.desktop
.with-pill-ui
```

### Mobile-Specific Elements
```css
/* Mobile controls */
.mobile-controls
.sidebard-mobile-menu-item

/* Mobile conversation layout */
.conversation.ng-tns-c1226462257-11.mobile
```

## 🔍 Search Functionality

### Search Page Structure
```css
/* Search input */
.search-input
.search-bar

/* Search results */
.search-results
.conversation-search-result

/* Filters */
.search-filters
.filter-options
```

### Search Result Items
```css
/* Individual results */
.search-result-item
.conversation-preview
.result-title
.result-snippet
```

## 💎 Gems Interface

### Gems List
```css
/* Gems container */
.gems-list-container
bot-list

/* Individual gems */
bot-list-item
.bot-item
.bot-new-conversation-button
.bot-name
```

### Gem Logos
```css
/* Gem avatars */
bot-logo
.bot-logo-text
.bot-logo-bg
```

## ⚙️ Settings & Configuration

### Settings Access
```css
/* Settings button */
[data-test-id="mobile-settings-and-help-control"]
.sidebard-mobile-menu-item

/* Settings menu */
.settings-menu
.help-menu
```

## 🎯 Automation Best Practices

### Reliable Selectors (Priority Order)
1. **Data Test IDs**: `[data-test-id="..."]` (most reliable)
2. **Unique IDs**: `#chat-history`, `#message-content-id-...`
3. **Component Names**: `chat-window`, `user-query`, `model-response`
4. **Stable Classes**: `.conversation-container`, `.message-content`

### Avoid These Selectors
- Angular-generated classes: `.ng-tns-c...`, `.ng-star-inserted`
- Dynamic IDs with timestamps
- Deeply nested CSS selectors
- Classes with version numbers

### Timing Considerations
```javascript
// Standard wait pattern
await page.goto(url, { waitUntil: 'domcontentloaded' });
await page.wait_for_load_state('networkidle', { timeout: 10000 });
await page.wait_for_timeout(3000); // Additional buffer
```

### Scrolling for Complete Content
```javascript
// Load complete conversation history
for (let i = 0; i < 15; i++) {
    await page.keyboard.press('Home');
    await page.wait_for_timeout(200);
}

// Alternative: Scroll to top
await page.evaluate(() => {
    const chatHistory = document.querySelector('#chat-history');
    if (chatHistory) {
        chatHistory.scrollTop = 0;
    }
});
```

## 🚨 Common Issues & Solutions

### Element Not Visible
- Use `force: true` for clicks: `element.click({ force: true })`
- Scroll element into view: `element.scroll_into_view_if_needed()`
- Check if sidebar is collapsed

### Network Timeouts
- Increase timeout values for slow connections
- Use retry logic with exponential backoff
- Check for loading spinners: `.loading-content-spinner`

### Dynamic Content
- Wait for specific elements to appear
- Use `page.wait_for_function()` for custom conditions
- Monitor network requests for completion

## 📊 Message Structure Patterns

### User Message Pattern
```html
<div class="conversation-container" id="{message_id}">
  <user-query>
    <user-query-content>
      <div class="query-content">
        <span class="user-query-bubble-with-background">
          <div class="query-text">
            <p class="query-text-line">{user_message}</p>
          </div>
        </span>
      </div>
    </user-query-content>
  </user-query>
</div>
```

### Assistant Response Pattern
```html
<div class="conversation-container" id="{message_id}">
  <model-response>
    <response-container>
      <div class="presented-response-container">
        <message-content>
          <div class="markdown">
            {assistant_response_content}
          </div>
        </message-content>
      </div>
    </response-container>
  </model-response>
</div>
```

---

*This documentation is based on extensive browser automation work and should be updated as the UI evolves.*

# Gemini Conversation Extractor

A deterministic Python tool that extracts conversations from Google Gemini using Playwright automation and converts them to high-quality markdown using markitdown. Includes HTTP API server for AI agent integration.

## 🎯 Key Features

- **Deterministic Extraction** - No LLM required, pure DOM-based automation
- **Search Page Discovery** - Uses the correct Gemini search page for complete conversation access
- **High-Quality Markdown** - Converts extracted content using markitdown library
- **Network Stability Handling** - Proper waiting for dynamic content loading
- **Multiple Output Formats** - HTML, Markdown, and JSON metadata
- **HTTP API Server** - FastAPI-based server for AI agent integration
- **RESTful Endpoints** - Search, extract, analyze, and list conversations via HTTP
- **AI Agent Ready** - JSON responses with relevance scoring and structured data

## 📁 Project Structure

```
├── src/                    # Source code
│   ├── gemini_extractor.py # Main implementation
│   └── ...                 # Other Python modules
├── flow/project/           # Project documentation
│   ├── DISCOVERY_PROCESS.md
│   ├── BROWSER_SETUP.md
│   ├── DOM_INSPECTION.md
│   ├── SEARCH_PAGE_DISCOVERY.md
│   ├── CONVERSATION_EXTRACTION.md
│   ├── NETWORK_HANDLING.md
│   └── IMPLEMENTATION_GUIDE.md
├── gemini_extracts/        # Extracted conversations (gitignored)
├── _bak/                   # Backup/deprecated files (gitignored)
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- Google Chrome browser
- Authenticated Google/Gemini account

### 2. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install markitdown for high-quality markdown conversion
pip install markitdown

# For HTTP API server (recommended for AI agents)
pip install fastapi uvicorn pydantic
```

### 3. Browser Setup

```bash
# Start Chrome with remote debugging
google-chrome --remote-debugging-port=9222 --user-data-dir=/home/bhd/ChromeProfiles/default --no-first-run &
```

### 4. Extract Conversations

```bash
# Extract all conversations (first 3)
python src/gemini_extractor.py

# Extract specific conversation by search term
python src/gemini_extractor.py "browser-use"
python src/gemini_extractor.py "debugging"
```

### 5. HTTP API Server (Recommended for AI Agents)

```bash
# Start HTTP API server
python -m src.simple_http_mcp --port 8000

# Test the API
curl http://127.0.0.1:8000/health

# List conversations
curl -X POST http://127.0.0.1:8000/list \
  -H "Content-Type: application/json" -d '{}'

# Search conversations
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "memory", "limit": 5}'

# Extract conversation
curl -X POST http://127.0.0.1:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://gemini.google.com/app/abc123", "title": "My Conversation"}'
```

**API Documentation**: Visit `http://127.0.0.1:8000/docs` for interactive API documentation.

## 📄 Output Files

Extracted conversations are saved to `gemini_extracts/` in multiple formats:

- **HTML**: `conversation_[title]_[timestamp].html` - Complete conversation with original formatting
- **Markdown**: `conversation_[title]_[timestamp].md` - Clean, readable format using markitdown
- **Metadata**: `metadata_[title]_[timestamp].json` - Extraction details and statistics

## 🔍 How It Works

### Discovery Process

The implementation is based on extensive discovery work documented in `flow/project/`:

1. **Browser Setup** - Chrome with remote debugging on port 9222
2. **DOM Inspection** - Real browser tools used to find exact selectors
3. **Search Page Discovery** - Found https://gemini.google.com/search as the correct page
4. **Content Extraction** - Proper network waiting and content filtering
5. **Markdown Conversion** - High-quality conversion using markitdown

### Key Discoveries

- ✅ **Search page** (`/search`) shows all conversations, not the main app sidebar
- ✅ **Gems vs Conversations** - Items with colons are gems (custom apps), not conversations
- ✅ **Network stability** - Must wait for 'networkidle' state and additional buffer time
- ✅ **Content filtering** - Remove suggestion prompts and UI elements
- ✅ **Unique URLs** - Each conversation has format `/app/[unique_id]`

## 📚 Documentation

For complete implementation details, see the documentation in `flow/project/`:

- **[DISCOVERY_PROCESS.md](flow/project/DISCOVERY_PROCESS.md)** - Complete discovery timeline and process
- **[BROWSER_SETUP.md](flow/project/BROWSER_SETUP.md)** - Chrome configuration and debugging setup
- **[SEARCH_PAGE_DISCOVERY.md](flow/project/SEARCH_PAGE_DISCOVERY.md)** - Why search page is the correct approach
- **[IMPLEMENTATION_GUIDE.md](flow/project/IMPLEMENTATION_GUIDE.md)** - Final working implementation

## 🛠️ Technical Details

### Dependencies

- **playwright** - Browser automation
- **markitdown** - High-quality HTML to Markdown conversion
- **asyncio** - Asynchronous execution

### Browser Requirements

- Chrome with remote debugging enabled
- Authenticated Gemini session
- Network stability for dynamic content loading

### Extraction Quality

- **Content Length**: Typical conversations 10KB+ HTML, 5KB+ Markdown
- **Accuracy**: Real user-AI dialogue without UI pollution
- **Completeness**: Full conversation history with scroll-to-top loading

## 🔧 Troubleshooting

### Common Issues

**1. Connection Failed**
```bash
# Check Chrome is running with debug port
curl http://localhost:9222/json/version
```

**2. No Conversations Found**
- Ensure you're signed into Gemini
- Check https://gemini.google.com/search is accessible
- Verify conversations exist in your account

**3. Empty Content**
- Check network stability waiting
- Verify conversation URLs are accessible
- Ensure proper authentication

### Debug Commands

```bash
# Check Chrome processes
ps aux | grep chrome | grep remote-debugging-port

# Test CDP connection
curl http://localhost:9222/json/list
```

## 📊 Example Results

### Successful Extraction

**Conversation**: "Browser-Use vs. Playwright/MCP"  
**Content Length**: 45,000+ characters  
**Structure**: User questions, detailed AI responses, comparison tables, code examples

**Sample Content**:
- User: "What feature that browser-use have that exceed the playwright/mcp repo?"
- AI: Detailed comparison with tables, technical explanations, code examples
- Multiple follow-up questions and comprehensive responses

## 🎯 Success Metrics

- ✅ **Real conversation data** extracted from authenticated account
- ✅ **High-quality markdown** conversion using markitdown
- ✅ **Complete conversation history** with proper scrolling
- ✅ **Clean content** without UI elements or suggestions
- ✅ **Deterministic extraction** without LLM dependencies

## 📝 License

This project is for educational and personal use. Respect Google's Terms of Service when using this tool.

---

*For detailed implementation process and discoveries, see the complete documentation in `flow/project/`.*

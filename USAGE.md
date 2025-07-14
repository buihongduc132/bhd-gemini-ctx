# Gemini Context Extraction - Usage Guide

**Generated:** 2025-07-13 18:47:26

## Overview

This project provides tools for extracting and analyzing conversations from Google Gemini (formerly Bard) with structured message parsing, sender identification, and comprehensive analysis capabilities.

## Features

### 🎯 Core Extraction Capabilities
- **Structured Message Parsing**: Extracts individual messages with sender identification
- **Message Metadata**: Captures message IDs, timestamps, and message types
- **Multiple Output Formats**: HTML, JSON, and Markdown outputs
- **Content Preservation**: Maintains conversation structure and formatting

### 📊 Analysis & Insights
- **Conversation Statistics**: Message counts, sender ratios, response patterns
- **Technical Term Detection**: Identifies programming languages, frameworks, tools
- **Topic Classification**: Categorizes discussions by technical domains
- **Content Analysis**: Code block detection, question patterns, complexity metrics

### 🔧 Browser Integration
- **Chrome DevTools Protocol**: Connects to existing Chrome sessions
- **Playwright Automation**: Robust browser automation for extraction
- **Network Stability**: Handles dynamic loading and network timeouts

## Installation

### Quick Install
```bash
# Clone and install
git clone https://github.com/buihongduc132/bhd-gemini-ctx.git
cd bhd-gemini-ctx
./install.sh
```

### Manual Installation
```bash
# Python 3.8+ required
python --version

# Install package
pip install -e .

# Install Playwright browsers
playwright install chromium

# Create default configuration
python -m src.config create
```

### Chrome Setup
```bash
# Start Chrome with remote debugging (configurable port)
google-chrome --remote-debugging-port=9222 --user-data-dir=$HOME/ChromeProfiles/default
```

### Configuration
```bash
# Show current configuration
gemini-cli config --show

# Configure browser settings
gemini-cli config --cdp-port 9223 --user-data-dir /path/to/profile

# Environment variables (optional)
export GEMINI_CDP_PORT=9222
export GEMINI_USER_DATA_DIR=/home/user/ChromeProfiles/default
export GEMINI_OUTPUT_DIR=gemini_extracts
```

## Usage

### CLI Usage (Recommended for AI Agents)

#### 1. Extract Conversations
```bash
# Extract specific conversation
gemini-cli extract https://gemini.google.com/app/abc123 --title "My Conversation"

# Extract with custom format
gemini-cli extract https://gemini.google.com/app/abc123 --format json
```

#### 2. Search Conversations
```bash
# Search for conversations about memory
gemini-cli search "memory" --limit 5

# Search and extract found conversations
gemini-cli search "memory" --extract
```

#### 3. Analyze Conversations
```bash
# Analyze all conversations (text output)
gemini-cli analyze

# Get JSON analysis for AI processing
gemini-cli analyze --format json
```

#### 4. List and Manage
```bash
# List all extracted conversations
gemini-cli list

# List in JSON format for AI agents
gemini-cli list --format json

# Get specific conversation summary
gemini-cli get-summary structured_conversation_id
```

### Python API Usage

#### 1. Simple Conversation Extraction
```python
from src.enhanced_gemini_extractor import EnhancedGeminiExtractor

# Initialize extractor (uses config automatically)
extractor = EnhancedGeminiExtractor()

# Extract conversation
result = await extractor.extract_conversation_with_structure(
    "https://gemini.google.com/app/conversation_id",
    "My Conversation Title"
)
```

#### 2. Custom Configuration
```python
from src.config import GeminiConfig, BrowserConfig
from src.enhanced_gemini_extractor import EnhancedGeminiExtractor

# Custom configuration
config = GeminiConfig(
    browser=BrowserConfig(cdp_port=9223, user_data_dir="/custom/path"),
    extraction={"output_dir": "custom_extracts"}
)

extractor = EnhancedGeminiExtractor(config=config)
```

### HTTP API Usage (Recommended for AI Agents)

#### 1. Start HTTP API Server
```bash
# Start HTTP API server
gemini-cli http-mcp --host 127.0.0.1 --port 8000

# Or directly
python -m src.simple_http_mcp --port 8000
```

#### 2. API Endpoints
```bash
# Health check
curl http://127.0.0.1:8000/health

# List conversations
curl -X POST http://127.0.0.1:8000/list \
  -H "Content-Type: application/json" \
  -d '{"include_metadata": true}'

# Search conversations
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "memory", "limit": 5}'

# Extract conversation
curl -X POST http://127.0.0.1:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://gemini.google.com/app/abc123", "title": "My Conversation"}'

# Analyze conversations
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"include_details": true}'
```

#### 3. AI Agent Integration
```python
import requests

# AI agents can use the HTTP API
response = requests.post("http://127.0.0.1:8000/search", json={
    "query": "memory system architecture",
    "limit": 5
})

conversations = response.json()["results"]
for conv in conversations:
    print(f"Found: {conv['title']} (relevance: {conv['relevance_score']})")
```

### MCP (Model Context Protocol) Usage

#### 1. Setup MCP Server (Optional)
```bash
# Install MCP support
pip install mcp

# Start MCP server
python -m src.mcp_server
```

#### 2. MCP Configuration
Add to your MCP client configuration:
```json
{
  "mcpServers": {
    "gemini-context-extractor": {
      "command": "python",
      "args": ["-m", "src.mcp_server"],
      "cwd": "/path/to/bhd-gemini-ctx",
      "env": {
        "GEMINI_CDP_PORT": "9222",
        "GEMINI_USER_DATA_DIR": "/home/user/ChromeProfiles/default"
      }
    }
  }
}
```

#### 3. Available MCP Tools
- **extract_conversation**: Extract conversation from URL
- **search_conversations**: Search for conversations by query
- **analyze_conversations**: Analyze all conversations
- **get_conversation_summary**: Get summary of specific conversation
- **list_conversations**: List all available conversations
- **search_conversation_content**: Search within conversation content

#### 4. MCP Resources
- **gemini://conversation/{id}**: Access conversation data
- **gemini://analysis/{id}**: Access analysis results

#### 5. AI Agent Integration Example
```python
# AI agents can use MCP tools like this:
{
  "tool": "search_conversations",
  "arguments": {
    "query": "memory system architecture",
    "limit": 5
  }
}

# Response provides structured conversation data
{
  "conversations": [
    {
      "title": "BHD Memory coder 09Jun25",
      "url": "https://gemini.google.com/app/94cecb9cb34fa6cf",
      "message_count": 20,
      "relevance_score": 0.95
    }
  ]
}
```

### Advanced Features

#### Structured Data Access
```python
import json

# Load extracted conversation
with open('gemini_extracts/structured_conversation.json', 'r') as f:
    data = json.load(f)

# Access messages
for message in data['messages']:
    print(f"{message['sender']}: {message['content'][:100]}...")
```

#### Conversation Analysis
```python
from src.conversation_analyzer import ConversationAnalyzer

analyzer = ConversationAnalyzer()
summary, analyses = analyzer.analyze_all_conversations()

# Print insights
analyzer.print_summary_report(summary)
```

## Output Formats

### 1. JSON Structure
```json
{
  "title": "Conversation Title",
  "url": "https://gemini.google.com/app/...",
  "extracted_at": "2025-07-13T18:44:10.247196",
  "message_count": 20,
  "messages": [
    {
      "id": "message_id",
      "sender": "user|assistant",
      "content": "Message content...",
      "timestamp": "2025-07-13T18:44:10.231935",
      "type": "user_message|assistant_message"
    }
  ]
}
```

### 2. Markdown Format
- **Structured Headers**: Clear message separation with sender icons
- **Metadata Display**: Message IDs, timestamps, and types
- **Content Preservation**: Maintains original formatting and structure

### 3. HTML Format
- **Raw Conversation Data**: Complete DOM structure preserved
- **Metadata Headers**: Extraction details and statistics
- **Browser Viewable**: Can be opened directly in browsers

## Configuration

### Environment Variables
```bash
# Chrome debugging port (default: 9222)
export CHROME_CDP_PORT=9222

# Output directory (default: gemini_extracts)
export EXTRACTS_DIR=./gemini_extracts

# Enable markitdown conversion (default: true if available)
export USE_MARKITDOWN=true
```

### Extractor Settings
```python
# Custom configuration
extractor = EnhancedGeminiExtractor(
    cdp_port=9222,                    # Chrome debugging port
    output_dir="custom_extracts"      # Custom output directory
)
```

## Analysis Features

### Technical Term Detection
Automatically identifies:
- **Programming Languages**: Python, JavaScript, TypeScript, etc.
- **Frameworks**: React, Django, FastAPI, etc.
- **Tools & Platforms**: Docker, GitHub, AWS, etc.
- **Protocols & Standards**: HTTP, JWT, OAuth, etc.

### Topic Classification
Categorizes conversations by:
- Authentication & Security
- Architecture & Design
- API Development
- Frontend/Backend Development
- Testing & Automation
- Deployment & DevOps

### Conversation Insights
Generates insights about:
- **Conversation Balance**: User vs Assistant message ratios
- **Technical Complexity**: Diversity of technical terms used
- **Code Content**: Frequency of code blocks and examples
- **Question Patterns**: Exploratory vs informational discussions

## File Structure

```
gemini_extracts/
├── structured_*.json          # Structured conversation data
├── structured_*.md            # Markdown formatted conversations
├── structured_*.html          # Raw HTML with metadata
└── conversation_analysis_*.json # Analysis results and insights
```

## Troubleshooting

### Common Issues

#### Chrome Connection Failed
```bash
# Ensure Chrome is running with debugging enabled
ps aux | grep chrome
google-chrome --remote-debugging-port=9222 --user-data-dir=/path/to/profile
```

#### Network Timeouts
- The extractor includes automatic retry logic
- Increase timeout values for slow connections
- Check network stability during extraction

#### Missing Dependencies
```bash
# Install missing packages
pip install playwright beautifulsoup4 markitdown

# Install Playwright browsers
playwright install chromium
```

### Debug Mode
```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

### 1. Conversation Preparation
- Ensure conversation is fully loaded before extraction
- Scroll through entire conversation to load all messages
- Wait for network activity to complete

### 2. Batch Processing
- Extract multiple conversations in sequence
- Use consistent naming conventions
- Organize extracts by date or topic

### 3. Analysis Workflow
- Extract conversations first
- Run analysis on complete dataset
- Review insights and patterns
- Export results for further processing

## Integration Examples

### With Data Analysis Tools
```python
import pandas as pd

# Convert to DataFrame for analysis
messages_df = pd.DataFrame(data['messages'])
print(messages_df.groupby('sender').size())
```

### With Documentation Systems
```python
# Generate documentation from conversations
def create_docs_from_conversation(conversation_data):
    # Extract technical discussions
    # Generate API documentation
    # Create tutorial content
    pass
```

## Support

For issues, questions, or contributions:
- Check the troubleshooting section above
- Review the QUICK_REFERENCE.md for common commands
- Examine the source code in `src/` directory

---

*This documentation is automatically generated and updated with each release.*

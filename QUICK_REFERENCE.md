# Gemini Context Extraction - Quick Reference

**Generated:** 2025-07-13 18:47:26

## 🚀 Quick Start

### 1. Setup Chrome
```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/home/user/ChromeProfiles/default
```

### 2. Extract Conversation
```bash
python src/enhanced_gemini_extractor.py
```

### 3. Analyze Results
```bash
python src/conversation_analyzer.py
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `src/enhanced_gemini_extractor.py` | Main extraction tool with structured parsing |
| `src/conversation_analyzer.py` | Analysis and insights generation |
| `src/doc_generator.py` | Documentation generator |
| `extract_ioc_conversation.py` | Legacy simple extractor |
| `flow/gemini_ui_structure.md` | **Comprehensive Gemini UI documentation** |

## 🔧 Common Commands

### Extract Specific Conversation
```python
from src.enhanced_gemini_extractor import EnhancedGeminiExtractor

extractor = EnhancedGeminiExtractor()
result = await extractor.extract_conversation_with_structure(
    "https://gemini.google.com/app/YOUR_CONVERSATION_ID",
    "Conversation Title"
)
```

### Analyze All Conversations
```python
from src.conversation_analyzer import ConversationAnalyzer

analyzer = ConversationAnalyzer()
summary, analyses = analyzer.analyze_all_conversations()
analyzer.print_summary_report(summary)
```

### Load Structured Data
```python
import json

with open('gemini_extracts/structured_*.json', 'r') as f:
    data = json.load(f)

# Access messages
for msg in data['messages']:
    print(f"{msg['sender']}: {msg['content'][:50]}...")
```

## 📊 Output Files

### Structured Extraction
- `structured_*.json` - Complete conversation data
- `structured_*.md` - Formatted markdown
- `structured_*.html` - Raw HTML with metadata

### Analysis Results
- `conversation_analysis_*.json` - Insights and statistics

## 🎯 Message Structure

```json
{
  "id": "message_unique_id",
  "sender": "user|assistant", 
  "content": "Full message content",
  "timestamp": "2025-07-13T18:44:10.231935",
  "type": "user_message|assistant_message"
}
```

## 🔍 Analysis Insights

### Technical Terms Detected
- Programming languages (Python, JavaScript, etc.)
- Frameworks (React, Django, FastAPI, etc.)
- Tools (Docker, GitHub, Playwright, etc.)
- Protocols (HTTP, JWT, OAuth, etc.)

### Topics Classified
- `authentication` - Auth, login, tokens
- `automation` - Playwright, scripts, bots
- `architecture` - Design patterns, structure
- `api` - REST, GraphQL, endpoints
- `deployment` - Docker, containers, CI/CD

### Conversation Patterns
- **Balanced**: Equal user/assistant participation
- **User-driven**: Many questions and exploration
- **Assistant-heavy**: Detailed explanations
- **Technical**: High technical term diversity
- **Code-heavy**: Many code examples

## ⚡ Troubleshooting

### Chrome Not Connected
```bash
# Check if Chrome is running
ps aux | grep chrome

# Restart with debugging
google-chrome --remote-debugging-port=9222 --user-data-dir=/path/to/profile
```

### Network Timeouts
- Wait for page to fully load
- Check internet connection
- Increase timeout values in code

### Missing Dependencies
```bash
pip install playwright beautifulsoup4 markitdown
```

## 📈 Analysis Examples

### Message Statistics
```python
# Load conversation data
data = json.load(open('structured_conversation.json'))

# Count by sender
user_msgs = sum(1 for m in data['messages'] if m['sender'] == 'user')
assistant_msgs = sum(1 for m in data['messages'] if m['sender'] == 'assistant')

print(f"User: {user_msgs}, Assistant: {assistant_msgs}")
```

### Technical Term Frequency
```python
from collections import Counter

# Extract all technical terms
all_terms = []
for analysis in analyses:
    all_terms.extend(analysis['unique_technical_terms'])

# Count frequency
term_freq = Counter(all_terms)
print(term_freq.most_common(10))
```

## 🔗 Integration

### With Pandas
```python
import pandas as pd

df = pd.DataFrame(data['messages'])
print(df.groupby('sender')['content'].apply(lambda x: x.str.len().mean()))
```

### With Documentation Tools
```python
# Extract code blocks for documentation
code_blocks = []
for msg in data['messages']:
    if '```' in msg['content']:
        # Extract and process code blocks
        pass
```

## 📝 File Naming Convention

- `structured_<title>_<timestamp>.json` - Main data
- `structured_<title>_<timestamp>.md` - Markdown format  
- `structured_<title>_<timestamp>.html` - Raw HTML
- `conversation_analysis_<timestamp>.json` - Analysis results

---

*For detailed usage instructions, see USAGE.md*

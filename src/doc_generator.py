#!/usr/bin/env python3
"""
Documentation Generator for Gemini Context Extraction Project
Generates comprehensive USAGE.md and QUICK_REFERENCE.md files.
"""

from pathlib import Path
from datetime import datetime

class DocumentationGenerator:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
    
    def generate_usage_md(self):
        """Generate comprehensive USAGE.md file."""
        usage_content = f"""# Gemini Context Extraction - Usage Guide

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

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

### Prerequisites
```bash
# Python 3.8+ required
python --version

# Install dependencies
pip install playwright beautifulsoup4 markitdown
```

### Chrome Setup
```bash
# Start Chrome with remote debugging
google-chrome --remote-debugging-port=9222 --user-data-dir=/path/to/profile
```

## Usage

### Basic Extraction

#### 1. Simple Conversation Extraction
```python
from src.enhanced_gemini_extractor import EnhancedGeminiExtractor

# Initialize extractor
extractor = EnhancedGeminiExtractor(cdp_port=9222)

# Extract conversation
result = await extractor.extract_conversation_with_structure(
    "https://gemini.google.com/app/conversation_id",
    "My Conversation Title"
)
```

#### 2. Command Line Usage
```bash
# Extract IOC conversation (example)
python src/enhanced_gemini_extractor.py

# Analyze extracted conversations
python src/conversation_analyzer.py
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
    print(f"{{message['sender']}}: {{message['content'][:100]}}...")
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
{{
  "title": "Conversation Title",
  "url": "https://gemini.google.com/app/...",
  "extracted_at": "2025-07-13T18:44:10.247196",
  "message_count": 20,
  "messages": [
    {{
      "id": "message_id",
      "sender": "user|assistant",
      "content": "Message content...",
      "timestamp": "2025-07-13T18:44:10.231935",
      "type": "user_message|assistant_message"
    }}
  ]
}}
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
"""
        
        usage_file = self.project_root / "USAGE.md"
        with open(usage_file, 'w', encoding='utf-8') as f:
            f.write(usage_content)
        
        return usage_file
    
    def generate_quick_reference_md(self):
        """Generate QUICK_REFERENCE.md file."""
        quick_ref_content = f"""# Gemini Context Extraction - Quick Reference

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

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
    print(f"{{msg['sender']}}: {{msg['content'][:50]}}...")
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
{{
  "id": "message_unique_id",
  "sender": "user|assistant", 
  "content": "Full message content",
  "timestamp": "2025-07-13T18:44:10.231935",
  "type": "user_message|assistant_message"
}}
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

print(f"User: {{user_msgs}}, Assistant: {{assistant_msgs}}")
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
"""
        
        quick_ref_file = self.project_root / "QUICK_REFERENCE.md"
        with open(quick_ref_file, 'w', encoding='utf-8') as f:
            f.write(quick_ref_content)
        
        return quick_ref_file
    
    def generate_all_docs(self):
        """Generate all documentation files."""
        print("📚 Generating documentation...")
        
        usage_file = self.generate_usage_md()
        quick_ref_file = self.generate_quick_reference_md()
        
        print(f"✅ Generated: {usage_file}")
        print(f"✅ Generated: {quick_ref_file}")
        
        return usage_file, quick_ref_file

if __name__ == "__main__":
    generator = DocumentationGenerator()
    generator.generate_all_docs()

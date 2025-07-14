#!/bin/bash
# Installation script for Gemini Context Extractor

set -e

echo "🚀 Installing Gemini Context Extractor..."

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Install package in development mode
echo "📦 Installing package..."
pip install -e .

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Create default configuration
echo "⚙️ Creating default configuration..."
python -m src.config create

# Check if Chrome is available
if command -v google-chrome &> /dev/null; then
    echo "✅ Chrome found"
elif command -v chromium-browser &> /dev/null; then
    echo "✅ Chromium found"
else
    echo "⚠️ Chrome/Chromium not found. Please install Chrome for best results."
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "📋 Quick Start:"
echo "  # Show configuration"
echo "  gemini-cli config --show"
echo ""
echo "  # Start Chrome with debugging (in another terminal)"
echo "  google-chrome --remote-debugging-port=9222 --user-data-dir=\$HOME/ChromeProfiles/default"
echo ""
echo "  # Extract a conversation"
echo "  gemini-cli extract https://gemini.google.com/app/YOUR_CONVERSATION_ID"
echo ""
echo "  # Search conversations"
echo "  gemini-cli search \"memory\""
echo ""
echo "  # Analyze conversations"
echo "  gemini-cli analyze"
echo ""
echo "📖 For more information, see USAGE.md"

"""
Gemini Context Extraction Package
Enhanced conversation extraction with structured parsing, analysis, and AI agent integration.
"""

__version__ = "1.0.0"
__author__ = "BHD"
__email__ = "buihongduc132@yahoo.com"

from .config import get_config, save_config, GeminiConfig, BrowserConfig, ExtractionConfig
from .enhanced_gemini_extractor import EnhancedGeminiExtractor
from .conversation_analyzer import ConversationAnalyzer

# Optional imports
try:
    from .search_based_extractor import SearchBasedExtractor
except ImportError:
    SearchBasedExtractor = None

try:
    from .mcp_server import GeminiMCPServer
except (ImportError, NameError):
    GeminiMCPServer = None

__all__ = [
    "get_config",
    "save_config", 
    "GeminiConfig",
    "BrowserConfig",
    "ExtractionConfig",
    "EnhancedGeminiExtractor",
    "ConversationAnalyzer",
    "SearchBasedExtractor",
    "GeminiMCPServer",
]

#!/usr/bin/env python3
"""
Configuration management for Gemini Context Extraction
Handles browser settings, paths, and environment configuration.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class BrowserConfig:
    """Browser configuration settings."""
    cdp_port: int = 9222
    user_data_dir: Optional[str] = None
    headless: bool = False
    timeout: int = 30000
    wait_for_network: bool = True
    
    def __post_init__(self):
        """Set default user data directory if not provided."""
        if self.user_data_dir is None:
            self.user_data_dir = str(Path.home() / "ChromeProfiles" / "default")

@dataclass
class ExtractionConfig:
    """Extraction configuration settings."""
    output_dir: str = "gemini_extracts"
    use_markitdown: bool = True
    max_scroll_attempts: int = 15
    scroll_delay_ms: int = 200
    network_timeout: int = 10000
    
@dataclass
class GeminiConfig:
    """Complete Gemini extraction configuration."""
    browser: BrowserConfig
    extraction: ExtractionConfig
    
    def __init__(self, **kwargs):
        # Handle nested config
        browser_config = kwargs.pop('browser', {})
        extraction_config = kwargs.pop('extraction', {})
        
        # Create sub-configs
        self.browser = BrowserConfig(**browser_config)
        self.extraction = ExtractionConfig(**extraction_config)
        
        # Apply any remaining kwargs to browser config (for backward compatibility)
        for key, value in kwargs.items():
            if hasattr(self.browser, key):
                setattr(self.browser, key, value)
            elif hasattr(self.extraction, key):
                setattr(self.extraction, key, value)

class ConfigManager:
    """Manages configuration loading, saving, and environment variables."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = Path(config_file) if config_file else Path("gemini_config.json")
        self._config: Optional[GeminiConfig] = None
    
    def load_config(self) -> GeminiConfig:
        """Load configuration from file, environment, and defaults."""
        if self._config is not None:
            return self._config
        
        # Start with defaults
        config_data = {}
        
        # Load from file if exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    config_data.update(file_config)
            except Exception as e:
                print(f"⚠️ Warning: Could not load config file {self.config_file}: {e}")
        
        # Override with environment variables
        env_config = self._load_from_env()
        config_data.update(env_config)
        
        self._config = GeminiConfig(**config_data)
        return self._config
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}
        
        # Browser settings
        if os.getenv('GEMINI_CDP_PORT'):
            env_config['cdp_port'] = int(os.getenv('GEMINI_CDP_PORT'))
        
        if os.getenv('GEMINI_USER_DATA_DIR'):
            env_config['user_data_dir'] = os.getenv('GEMINI_USER_DATA_DIR')
        
        if os.getenv('GEMINI_HEADLESS'):
            env_config['headless'] = os.getenv('GEMINI_HEADLESS').lower() == 'true'
        
        # Extraction settings
        if os.getenv('GEMINI_OUTPUT_DIR'):
            env_config['output_dir'] = os.getenv('GEMINI_OUTPUT_DIR')
        
        if os.getenv('GEMINI_USE_MARKITDOWN'):
            env_config['use_markitdown'] = os.getenv('GEMINI_USE_MARKITDOWN').lower() == 'true'
        
        if os.getenv('GEMINI_TIMEOUT'):
            env_config['timeout'] = int(os.getenv('GEMINI_TIMEOUT'))
        
        return env_config
    
    def save_config(self, config: GeminiConfig):
        """Save configuration to file."""
        config_data = {
            'browser': asdict(config.browser),
            'extraction': asdict(config.extraction)
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            print(f"✅ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")
    
    def create_default_config(self):
        """Create and save a default configuration file."""
        default_config = GeminiConfig()
        self.save_config(default_config)
        return default_config
    
    def print_config(self, config: GeminiConfig):
        """Print current configuration in a readable format."""
        print("\n📋 Current Configuration:")
        print("=" * 50)
        
        print("\n🌐 Browser Settings:")
        print(f"  CDP Port: {config.browser.cdp_port}")
        print(f"  User Data Dir: {config.browser.user_data_dir}")
        print(f"  Headless: {config.browser.headless}")
        print(f"  Timeout: {config.browser.timeout}ms")
        print(f"  Wait for Network: {config.browser.wait_for_network}")
        
        print("\n📄 Extraction Settings:")
        print(f"  Output Directory: {config.extraction.output_dir}")
        print(f"  Use Markitdown: {config.extraction.use_markitdown}")
        print(f"  Max Scroll Attempts: {config.extraction.max_scroll_attempts}")
        print(f"  Scroll Delay: {config.extraction.scroll_delay_ms}ms")
        print(f"  Network Timeout: {config.extraction.network_timeout}ms")
        
        print("=" * 50)

def get_config(config_file: Optional[str] = None) -> GeminiConfig:
    """Get the current configuration."""
    manager = ConfigManager(config_file)
    return manager.load_config()

def save_config(config: GeminiConfig, config_file: Optional[str] = None):
    """Save configuration to file."""
    manager = ConfigManager(config_file)
    manager.save_config(config)

def print_config(config_file: Optional[str] = None):
    """Print current configuration."""
    manager = ConfigManager(config_file)
    config = manager.load_config()
    manager.print_config(config)

def create_default_config(config_file: Optional[str] = None):
    """Create default configuration file."""
    manager = ConfigManager(config_file)
    return manager.create_default_config()

# Environment variable documentation
ENV_VARS_HELP = """
Environment Variables:
  GEMINI_CDP_PORT         Chrome DevTools Protocol port (default: 9222)
  GEMINI_USER_DATA_DIR    Chrome user data directory path
  GEMINI_HEADLESS         Run browser in headless mode (true/false)
  GEMINI_OUTPUT_DIR       Output directory for extractions (default: gemini_extracts)
  GEMINI_USE_MARKITDOWN   Use markitdown for conversion (true/false)
  GEMINI_TIMEOUT          Browser timeout in milliseconds (default: 30000)

Example:
  export GEMINI_CDP_PORT=9223
  export GEMINI_USER_DATA_DIR=/home/user/chrome-profile
  export GEMINI_HEADLESS=true
"""

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "create":
            create_default_config()
        elif command == "show":
            print_config()
        elif command == "help":
            print(ENV_VARS_HELP)
        else:
            print("Usage: python config.py [create|show|help]")
    else:
        print_config()

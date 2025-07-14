#!/usr/bin/env python3
"""
Setup script for Gemini Context Extraction
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    requirements = requirements_file.read_text().strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]
else:
    requirements = [
        "playwright>=1.40.0",
        "beautifulsoup4>=4.12.0",
        "markitdown>=0.0.1a2",
        "asyncio",
        "pathlib",
        "dataclasses",
    ]

# Optional MCP requirements
mcp_requirements = [
    "mcp>=0.1.0",
]

setup(
    name="gemini-context-extractor",
    version="1.0.0",
    description="Enhanced Gemini conversation extraction with structured parsing, analysis, and AI agent integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="BHD",
    author_email="buihongduc132@yahoo.com",
    url="https://github.com/buihongduc132/bhd-gemini-ctx",
    packages=find_packages(),
    package_dir={"": "."},
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "mcp": mcp_requirements,
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gemini-cli=src.cli:cli_entry_point",
            "gemini-extract=src.enhanced_gemini_extractor:main",
            "gemini-analyze=src.conversation_analyzer:main",
            "gemini-config=src.config:main",
        ],
        "mcp_servers": [
            "gemini-context-extractor=src.mcp_server:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Text Processing :: Markup :: HTML",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="gemini, conversation, extraction, ai, agent, mcp, cli, browser, automation",
    project_urls={
        "Bug Reports": "https://github.com/buihongduc132/bhd-gemini-ctx/issues",
        "Source": "https://github.com/buihongduc132/bhd-gemini-ctx",
        "Documentation": "https://github.com/buihongduc132/bhd-gemini-ctx#readme",
    },
    include_package_data=True,
    zip_safe=False,
)

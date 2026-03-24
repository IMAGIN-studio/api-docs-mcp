"""IMAGIN.studio Docs MCP server — mcpb entry point.

This thin wrapper is the entry_point for the .mcpb extension.
Claude Desktop's uv runtime installs deps from pyproject.toml
then runs this file.
"""

from src.main import main

main()

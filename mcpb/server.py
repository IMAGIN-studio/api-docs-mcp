"""IMAGIN.studio Docs MCP server: mcpb entry point.

This thin wrapper is the entry_point for the .mcpb extension.
Claude Desktop's uv runtime runs `uv run --directory <bundle> server.py`,
which installs the dependencies from this folder's pyproject.toml
(the imagin-studio-api-docs-mcp package from PyPI) and then runs this file.
"""

from src.main import main

main()

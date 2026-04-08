# IMAGIN.studio API Docs MCP Server

Give your AI coding assistant instant access to the full [IMAGIN.studio](https://www.imaginstudio.com/) [documentation](https://docs.imagin.studio/) — CDN configuration, API references, integration guides, and more.

One tool. One command. Works with every major AI coding assistant.

## Quick Start

Paste this into your agent's MCP config:

```json
{
  "mcpServers": {
    "imagin-docs": {
      "command": "uvx",
      "args": ["imagin-studio-api-docs-mcp"]
    }
  }
}
```

Or just ask your AI assistant:

> Install this MCP server: https://pypi.org/project/imagin-studio-api-docs-mcp/

## How It Works

1. **Install** — `uvx imagin-studio-api-docs-mcp` (no cloning, no venv, no config)
2. **Index** — On first run, clones the docs and builds a local vector index (~30 sec)
3. **Search** — Your AI assistant calls `search_docs` to find relevant documentation
4. **Stay fresh** — The index auto-updates when the upstream docs change

Everything runs locally. No API keys. No external services.

## Supported Agents

| Agent | Config location |
|-------|----------------|
| **Claude Code** | `.mcp.json` in project root |
| **Claude Desktop** | `claude_desktop_config.json` |
| **Cursor** | Settings > Tools & MCP |
| **Windsurf** | `~/.codeium/windsurf/mcp_config.json` |
| **VS Code + Copilot** | `.vscode/mcp.json` |
| **Cline** | MCP servers panel |
| **Zed** | `~/.config/zed/settings.json` |

For detailed setup instructions for each agent, see the [full setup guide on PyPI](https://pypi.org/project/imagin-studio-api-docs-mcp/).

## Alternative: npx

If your agent can't find `uvx` (common with GUI apps like Claude Desktop and Cursor):

```json
{
  "mcpServers": {
    "imagin-docs": {
      "command": "npx",
      "args": ["-y", "@imagin.studio/api-docs-mcp"]
    }
  }
}
```

## What You Can Ask

Once installed, try prompts like:

- *"Search the IMAGIN docs for CDN cache invalidation"*
- *"How do I set up a custom domain with IMAGIN?"*
- *"Find the API endpoint for image transformations"*
- *"What image formats does IMAGIN.studio support?"*

## Packages

| Registry | Package | Install |
|----------|---------|---------|
| **PyPI** | [`imagin-studio-api-docs-mcp`](https://pypi.org/project/imagin-studio-api-docs-mcp/) | `uvx imagin-studio-api-docs-mcp` |
| **npm** | [`@imagin.studio/api-docs-mcp`](https://www.npmjs.com/package/@imagin.studio/api-docs-mcp) | `npx -y @imagin.studio/api-docs-mcp` |

## License

Proprietary — see [LICENSE](LICENSE).

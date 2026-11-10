# IMAGIN.studio API Docs MCP Server

Give your AI coding assistant direct access to the full [IMAGIN.studio](https://www.imaginstudio.com/) [documentation](https://docs.imagin.studio/), from CDN data points and getImage parameters to paint matching, 360° spinners and deployment guides, so you can build faster without leaving your editor.

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

1. **Install:** `uvx imagin-studio-api-docs-mcp` (no cloning, no venv, no config)
2. **Index:** on first run, clones the docs and builds a local search index (~30 sec)
3. **Search:** your AI assistant calls `search_docs`, which matches both meaning and exact names like `safeMode` or `zoomType`
4. **Stay fresh:** the index updates automatically when the docs change

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

Once installed, ask things like:

- *"What parameters do I need for a getImage call?"*
- *"How does zoomType adaptive vs relative work?"*
- *"What are the CDN response headers I should check for substituted images?"*
- *"How do I build a 360° spinner using angles 200 to 231?"*

Or go further and build with it:

- *"Replace all car listing images with IMAGIN.studio imagery, matched down to trim level"*
- *"Embed IMAGIN.studio lifestyle images with lazy loading for Core Web Vitals"*
- *"Add a color picker that fetches swatches from the paint API and updates the hero image"*

Your assistant reads our docs and writes the integration code for you.

## Packages

| Registry | Package | Install |
|----------|---------|---------|
| **PyPI** | [`imagin-studio-api-docs-mcp`](https://pypi.org/project/imagin-studio-api-docs-mcp/) | `uvx imagin-studio-api-docs-mcp` |
| **npm** | [`@imagin.studio/api-docs-mcp`](https://www.npmjs.com/package/@imagin.studio/api-docs-mcp) | `npx -y @imagin.studio/api-docs-mcp` |

## License

Apache License 2.0. See [LICENSE](LICENSE).

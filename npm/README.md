# IMAGIN.studio API Docs MCP Server

Semantic search over [IMAGIN.studio](https://www.imaginstudio.com/)
[documentation](https://docs.imagin.studio/) — CDN, API, integration guides, and more.

This is a thin **npx wrapper** that finds `uvx` on your system and launches
the Python MCP server. It solves the common problem of GUI apps (Claude
Desktop, Cursor, etc.) not finding `uvx` in PATH.

## Dependency note — `fastembed-imagin`

This package depends on `fastembed-imagin`, a temporary fork of
[`fastembed`](https://github.com/qdrant/fastembed) by Qdrant.

**Why:** upstream fastembed 0.7.4 pins `pillow<12.0`, which blocks
Pillow 12.x security fixes (CVE-2026-25990). The fix is merged on
`main` but not yet released.

**What changed:** only the pillow version constraint — relaxed from
`<12.0` to `<13.0` for Python 3.10+. No logic changes. Source:
[IMAGIN-studio/fastembed-imagin](https://github.com/IMAGIN-studio/fastembed-imagin).

**Revert plan:** once upstream releases fastembed 0.7.5+ with the
pillow fix, this package will switch back to `fastembed` and
`fastembed-imagin` will be retired.

## Prerequisites

- **Node.js 18+** (for npx)
- **uv** — install from [astral.sh/uv](https://docs.astral.sh/uv/):
  ```sh
  curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS / Linux
  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows
  ```

## Usage

```sh
npx -y @imagin.studio/api-docs-mcp
```

Or in your agent's MCP config:

```json
{
  "imagin-docs": {
    "command": "npx",
    "args": ["-y", "@imagin.studio/api-docs-mcp"]
  }
}
```

## Full setup guide

For step-by-step instructions for 7 coding agents (Claude Code, Claude
Desktop, Cursor, Windsurf, VS Code + Copilot, Cline, Zed), see the full
setup guide on PyPI:

**https://pypi.org/project/imagin-studio-api-docs-mcp/**

## How it works

The npx wrapper probes common `uvx` install locations (`~/.local/bin`,
Homebrew, cargo) and spawns `uvx imagin-studio-api-docs-mcp`, which downloads and
runs the Python MCP server. On first run, the server clones the docs and
builds a local vector index (~20-30 seconds).

## License

Proprietary — see [LICENSE](https://github.com/IMAGIN-studio/api-docs-mcp/blob/main/LICENSE).

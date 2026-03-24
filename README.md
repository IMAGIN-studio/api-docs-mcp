# IMAGIN.studio API Docs MCP Server

Semantic search over [IMAGIN.studio](https://www.imaginstudio.com/)
[documentation](https://docs.imagin.studio/) — CDN, API, integration guides, and more.

Provides one tool — `search_docs` — for any AI coding assistant that supports
[MCP](https://modelcontextprotocol.io/).

> **Dependency note — `fastembed-imagin`**
>
> This package depends on `fastembed-imagin`, a temporary fork of
> [`fastembed`](https://github.com/qdrant/fastembed) by Qdrant.
>
> **Why:** upstream fastembed 0.7.4 pins `pillow<12.0`, which blocks
> Pillow 12.x security fixes (CVE-2026-25990). The fix PR
> ([#599](https://github.com/qdrant/fastembed/pull/599)) is open but
> unreleased.
>
> **What changed:** only the pillow version constraint — relaxed from
> `<12.0` to `<13.0` for Python 3.10+. No logic changes. Source:
> [IMAGIN-studio/fastembed-imagin](https://github.com/IMAGIN-studio/fastembed-imagin).
>
> **Revert plan:** once upstream releases fastembed 0.7.5+ with the
> pillow fix, this package will switch back to `fastembed` and
> `fastembed-imagin` will be retired.

## Install

**PyPI (recommended):**

```sh
uvx imagin-studio-api-docs-mcp
```

**npm (for GUI apps that can't find uvx):**

```sh
npx -y @imagin.studio/api-docs-mcp
```

For step-by-step setup instructions for 7 coding agents (Claude Code, Claude
Desktop, Cursor, Windsurf, VS Code + Copilot, Cline, Zed), see the full
setup guide on PyPI:

**https://pypi.org/project/imagin-studio-api-docs-mcp/**

## License

Proprietary — see [LICENSE](LICENSE).

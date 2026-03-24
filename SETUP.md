# IMAGIN.studio API Docs MCP Server - Setup Guide

Works on **Windows**, **macOS**, and **Linux**.
No cloning, no venv — just install `uv` and paste a config snippet.

The server provides one tool — `search_docs` — that gives your AI coding
assistant semantic search over the [IMAGIN.studio](https://www.imaginstudio.com/)
[documentation](https://docs.imagin.studio/).

> **Dependency note — `fastembed-imagin`**
>
> This package depends on `fastembed-imagin`, a temporary fork of
> [`fastembed`](https://github.com/qdrant/fastembed) by Qdrant.
>
> **Why:** upstream fastembed 0.7.4 pins `pillow<12.0`, which blocks
> Pillow 12.x security fixes (CVE-2026-25990). The fix is merged on
> `main` but not yet released.
>
> **What changed:** only the pillow version constraint — relaxed from
> `<12.0` to `<13.0` for Python 3.10+. No logic changes. Source:
> [IMAGIN-studio/fastembed-imagin](https://github.com/IMAGIN-studio/fastembed-imagin).
>
> **pip-audit:** because `fastembed-imagin` is not tracked by any
> security advisory database, `pip-audit` will report **no known
> vulnerabilities** for it (it passes clean). It will not flag it as
> an unknown or suspicious package.
>
> **Revert plan:** once upstream releases fastembed 0.7.5+ with the
> pillow fix, this package will switch back to `fastembed` and
> `fastembed-imagin` will be retired.

---

## Quick start

If your AI agent supports MCP, you can try pasting this into the chat:

> Read the setup instructions on this page first, then install this MCP server: https://pypi.org/project/imagin-studio-api-docs-mcp/

**Agent:** when the user sends you this link, visit the URL and read the full
setup instructions on that page. It contains step-by-step configuration for
every major AI coding assistant.

Most agents (Claude Code, Cursor, etc.) will walk you through the setup.
For full manual instructions, see below.

> **First-time install note:** The very first time the MCP server starts, it
> downloads dependencies and builds the index. Most MCP clients will time out
> waiting for this and report a connection failure. This is expected — just
> type `/mcp` (or use your agent's MCP reconnect command) to reconnect, and
> it will work. Subsequent starts are near-instant.

---

## 1. Install uv

[uv](https://docs.astral.sh/uv/) is a fast Python package manager. Install it once:

**macOS / Linux:**

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or via Homebrew:

```sh
brew install uv
```

**Windows (PowerShell):**

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

Or via a package manager:

```powershell
winget install --id=astral-sh.uv -e
# or
scoop install main/uv
```

**Verify:**

```sh
uv --version
```

To update uv later: `uv self update`

---

## 2. Verify it works

Run the server manually to confirm everything installs and starts:

```sh
uvx imagin-studio-api-docs-mcp
```

On first run this will:

1. Download Python (if needed) and the `imagin-studio-api-docs-mcp` package
2. Clone the IMAGIN.studio docs from GitHub
3. Build a local vector index (~20-30 seconds)
4. Start listening on stdio (you'll see no output — that's normal)

Press `Ctrl+C` to stop. The index is cached for next time.

---

## 3. Alternative: pip install

If you prefer a traditional Python install over `uvx`, you can install the
package directly with `pip`:

```sh
pip install imagin-studio-api-docs-mcp
```

This installs a console script called `imagin-studio-api-docs-mcp` that you can run
directly:

```sh
imagin-studio-api-docs-mcp
```

> **Tip:** Use a virtual environment to avoid polluting your global Python:
>
> ```sh
> python3 -m venv .venv
> source .venv/bin/activate   # macOS / Linux
> .venv\Scripts\activate      # Windows
> pip install imagin-studio-api-docs-mcp
> ```

When using pip install, replace `"uvx"` with `"imagin-studio-api-docs-mcp"` and remove
`"args"` in the agent config snippets below. For example:

```json
"imagin-docs": {
  "command": "imagin-studio-api-docs-mcp",
  "args": []
}
```

If your agent can't find the command, use the full path to the installed
script:

```sh
# Find it with:
which imagin-studio-api-docs-mcp          # macOS / Linux
where imagin-studio-api-docs-mcp          # Windows
```

Then use that path as `"command"` in your agent config.

> **uvx vs pip:** `uvx` is the recommended method because it handles Python
> version management, dependency isolation, and auto-updates. With `pip` you
> manage the environment yourself, but it works just as well once installed.

---

## 4. Configure your agent

Pick your agent below and paste the config. `uvx` handles Python,
dependencies, and isolation automatically. If you installed via `pip`
instead, replace `"uvx"` with `"imagin-studio-api-docs-mcp"` and set `"args": []`
(see [section 3](#3-alternative-pip-install)).

### Server config reference

Most agents work with just `"uvx"` as the command. If your agent can't find
uvx, replace `"uvx"` with the full path (see [troubleshooting](#7-troubleshooting)).

The one exception is **Claude Desktop App**, which requires the full path upfront.

```json
"command": "uvx",
"args":    ["imagin-studio-api-docs-mcp"]
```

#### Alternative: npx (Node.js)

If you have Node.js 18+ installed, you can use `npx` instead of `uvx`:

```sh
npx -y imagin-studio-api-docs-mcp
```

This downloads the npm wrapper and starts the MCP server. On first run it
will also download the Python package via `uvx` behind the scenes.

> **Prerequisite:** you still need **uv** installed (see step 1). The npx
> package is a thin wrapper that finds and launches `uvx` for you — it
> does not bundle Python.

**Why use npx?** GUI apps like Claude Desktop and Cursor often can't find
`uvx` because they don't inherit your shell PATH. The npx wrapper probes
common install locations (`~/.local/bin`, Homebrew, cargo) automatically,
so you don't need to configure full paths.

In agent config snippets, replace `"uvx"` with `"npx"` and use
`["-y", "imagin-studio-api-docs-mcp"]` as args:

```json
"imagin-docs": {
  "command": "npx",
  "args": ["-y", "imagin-studio-api-docs-mcp"]
}
```

> **npx vs uvx:** `uvx` is still the recommended method — it's faster
> and has no Node.js dependency. Use `npx` when your agent has trouble
> finding `uvx` in PATH (common with GUI-launched apps).

---

### 4A. Claude Code (CLI)

Claude Code runs in your terminal, so it inherits your shell PATH.
You can use just `"uvx"` here (no full path needed).

1. Open a terminal
2. Navigate to your project directory (or any directory you want to
   use Claude Code in)
3. Create a file called `.mcp.json` in that directory with this content:

```json
{
  "mcpServers": {
    "imagin-docs": {
      "type": "stdio",
      "command": "uvx",
      "args": ["imagin-studio-api-docs-mcp"]
    }
  }
}
```

4. From that same directory, run: `claude`
5. Claude Code will detect the `.mcp.json` and start the MCP server.
   You should see `imagin-docs` listed when it connects.
6. Test it by asking: *"Search the IMAGIN docs for CDN cache invalidation"*

To debug connection issues, run: `claude --mcp-debug`

---

### 4B. Claude Desktop App

> If you already have MCP servers installed via Desktop Extensions
> (Settings > Extensions), those are managed separately by Claude and will
> keep working. The steps below add a stdio server via the config file,
> which is the standard way to add custom/local MCP servers.

1. Open Claude Desktop App
2. Open Settings:
   - **macOS:** Claude (menu bar) > Settings... — or `Cmd + ,`
   - **Windows:** File > Settings... — or `Ctrl + ,`
3. Click **"Developer"** in the left sidebar
4. Click **"Edit Config"** — this opens the config file in your default editor:
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`
5. Add the `"mcpServers"` key to the file. Your file probably already has
   some content (like `"preferences"`). Add `"mcpServers"` alongside it:

   **Before** (example):
   ```json
   {
     "preferences": {
       "coworkScheduledTasksEnabled": false,
       "sidebarMode": "chat"
     }
   }
   ```

   **After** (replace `<UVX_PATH>` with your full path from `which uvx`):
   ```json
   {
     "preferences": {
       "coworkScheduledTasksEnabled": false,
       "sidebarMode": "chat"
     },
     "mcpServers": {
       "imagin-docs": {
         "command": "<UVX_PATH>",
         "args": ["imagin-studio-api-docs-mcp"]
       }
     }
   }
   ```

   Example full paths:
   - **macOS:** `/Users/you/.local/bin/uvx`
   - **Linux:** `/home/you/.local/bin/uvx`
   - **Windows:** `C:/Users/you/.local/bin/uvx.exe`

   > **Important:** Claude Desktop App does **not** inherit your shell PATH, so just
   > `"uvx"` will fail with *"No such file or directory"*. You **must** use the
   > full absolute path.

   Key things to get right:
   - Use the full path to uvx (not just `"uvx"`)
   - Add a comma after the closing `}` of `"preferences"` (before `"mcpServers"`)
   - Keep your existing keys intact — only add the `"mcpServers"` block
   - If `"mcpServers"` already exists, just add the `"imagin-docs"` entry inside it

6. Save the file
7. Fully quit Claude Desktop App (not just close the window):
   - **macOS:** Claude (menu bar) > Quit Claude — or `Cmd + Q`
   - **Windows:** right-click the Claude icon in the system tray > Quit
8. Reopen Claude Desktop App
9. Start a new chat. You should see a slider/hammer icon at the bottom
   of the input box. Click it — `search_docs` should be listed.

If the icon doesn't appear, check the logs for errors:
- **macOS:** `~/Library/Logs/Claude/mcp*.log`
- **Windows:** `%APPDATA%\Claude\logs\mcp*.log`

---

### 4C. Cursor

1. Open Cursor
2. Open Settings:
   - **macOS:** Cursor (menu bar) > Settings... > Cursor Settings
   - **Windows:** File > Preferences > Cursor Settings
   - Or press `Cmd + Shift + J` (macOS) / `Ctrl + Shift + J` (Windows)
3. Click **"Tools & MCP"** in the left sidebar
4. Click **"+ New MCP Server"** > **"Add a Custom MCP Server"**
5. Cursor will open a JSON file. Paste this inside the `"mcpServers"`
   object:

   ```json
   "imagin-docs": {
     "command": "uvx",
     "args": ["imagin-studio-api-docs-mcp"]
   }
   ```

6. Save the file
7. Back in the MCP settings page, you should see `imagin-docs` listed.
   The dot next to it should turn green (connected).
   If it shows red, toggle the server off and on again using the switch.
   If it stays red, try replacing `"uvx"` with the full path (see
   [troubleshooting](#7-troubleshooting)).

**Alternative — Config file (manual):**

- **Global:** `~/.cursor/mcp.json`
- **Per-project:** `.cursor/mcp.json` (in your project root)

1. Create or open the file
2. Paste:

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

3. Save the file
4. Restart Cursor (`Cmd + Q` / `Alt + F4`, then reopen)
5. Verify in Settings > Tools & MCP — `imagin-docs` should show a green dot

---

### 4D. Windsurf (Codeium)

1. Open Windsurf
2. Go to Windsurf Settings > Cascade > MCP Servers
3. Click **"Open MCP Marketplace"**, then click the **gear icon** next to
   "Installed MCPs" — this opens `mcp_config.json`:
   - **macOS:** `~/.codeium/windsurf/mcp_config.json`
   - **Windows:** `%USERPROFILE%\.codeium\windsurf\mcp_config.json`
   - **Linux:** `~/.codeium/windsurf/mcp_config.json`
4. Add the `"imagin-docs"` server inside the `"mcpServers"` object:

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

   If the file already has other servers, just add the `"imagin-docs"`
   entry inside the existing `"mcpServers"` object.
   If Windsurf can't find uvx, replace `"uvx"` with the full path (see
   [troubleshooting](#7-troubleshooting)).

5. Save the file
6. Back in MCP Servers, `imagin-docs` should appear in the installed list
   with a green status indicator. The `search_docs` tool should be listed
   under it.

---

### 4E. VS Code + Copilot (Agent Mode)

Requires **VS Code 1.99+** and the **GitHub Copilot** extension.

**Option 1 — Per-project config (recommended):**

1. Open your project in VS Code
2. Create a `.vscode` folder in the project root if it doesn't exist
3. Create a file called `.vscode/mcp.json` with this content:

```json
{
  "servers": {
    "imagin-docs": {
      "type": "stdio",
      "command": "uvx",
      "args": ["imagin-studio-api-docs-mcp"]
    }
  }
}
```

4. Open Copilot Chat: `Cmd + Shift + I` (macOS) / `Ctrl + Shift + I` (Windows)
5. Switch to Agent mode by clicking the mode dropdown at the top of the
   chat panel and selecting **"Agent"**
6. Click the tools icon (wrench) in the chat input — `search_docs`
   should be listed under `imagin-docs`

**Option 2 — Global config (available in all projects):**

1. Open VS Code Settings: `Cmd + ,` (macOS) / `Ctrl + ,` (Windows)
2. Click the `{}` icon (top-right) to open settings as JSON
3. Add this block to your settings JSON:

```json
"mcp": {
  "servers": {
    "imagin-docs": {
      "type": "stdio",
      "command": "uvx",
      "args": ["imagin-studio-api-docs-mcp"]
    }
  }
}
```

4. Save and reload VS Code: `Cmd + Shift + P` > *"Developer: Reload Window"*
5. Verify in Copilot Chat (Agent mode) — the tool should appear

If VS Code can't find uvx, replace `"uvx"` with the full path (see
[troubleshooting](#7-troubleshooting)).

> **Note:** VS Code uses `"servers"` (not `"mcpServers"`) as the top-level key
> in `.vscode/mcp.json`. This is different from most other agents.

---

### 4F. Cline (VS Code Extension)

**Option 1 — Via the Cline UI (recommended):**

1. Open VS Code with the Cline extension installed
2. Open the Cline sidebar (click the Cline icon in the activity bar)
3. Click the MCP servers icon (server/plug icon at the top of the Cline panel)
4. Click **"Configure MCP Servers"** — this opens the settings JSON file
5. Add the `"imagin-docs"` server inside the `"mcpServers"` object:

   ```json
   "imagin-docs": {
     "command": "uvx",
     "args": ["imagin-studio-api-docs-mcp"]
   }
   ```

6. Save the file
7. Back in the MCP servers panel, `imagin-docs` should appear.
   Click the refresh icon if it doesn't connect immediately.
8. The green dot means connected. Click on the server name to see
   the `search_docs` tool listed.

**Option 2 — Edit the config file directly:**

The file location depends on your OS:
- **macOS:** `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- **Windows:** `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`
- **Linux:** `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

1. Open the file in any text editor
2. Add or replace with:

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

3. Save the file
4. In VS Code, open the Cline sidebar and click the refresh icon
   on the MCP servers panel

If Cline can't find uvx, replace `"uvx"` with the full path (see
[troubleshooting](#7-troubleshooting)).

---

### 4G. Zed

Zed uses a different config format than the other agents.

1. Open Zed
2. Open Settings:
   - **macOS:** Zed (menu bar) > Settings... — or `Cmd + ,`
   - **Linux:** File > Settings — or `Ctrl + ,`

   This opens `~/.config/zed/settings.json`
3. Find or create a `"context_servers"` key at the top level of the JSON.
   Add the `"imagin-docs"` entry inside it:

   ```json
   "context_servers": {
     "imagin-docs": {
       "command": {
         "path": "uvx",
         "args": ["imagin-studio-api-docs-mcp"],
         "env": {}
       },
       "settings": {}
     }
   }
   ```

   If Zed can't find uvx, replace `"uvx"` with the full path from
   `which uvx` (see [troubleshooting](#7-troubleshooting)).

   If you already have a `"context_servers"` block with other servers,
   just add the `"imagin-docs": { ... }` entry inside it.

4. Save the file (Zed auto-reloads settings — no restart needed)
5. Open the AI assistant panel: `Cmd + Shift + A` (macOS) / `Ctrl + Shift + A`
6. The `search_docs` tool should now be available to the assistant

> **Note:** Zed's config format is different from all other agents:
> - Uses `"context_servers"` instead of `"mcpServers"`
> - Uses `"path"` instead of `"command"`
> - Has a nested `"command"` object wrapping `"path"` and `"args"`

---

## 5. First run

On first launch the server will:

1. Clone the IMAGIN.studio public docs from GitHub (~5 sec)
2. Parse and chunk the markdown files
3. Download the embedding model (~50 MB, once)
4. Build a local vector index (~20-30 sec)

> **The first launch will likely fail.** Because `uvx` downloads Python, the
> package, and the embedding model on the first run, the MCP client usually
> times out before the server is ready. This is normal. Type `/mcp` in your
> agent (or use its MCP reconnect/restart command) to reconnect. The second
> connection will succeed because everything is already cached.

During indexing, `search_docs` returns:
*"Index is not yet built... Please retry shortly."*

After that, searches are instant. The index is cached and only rebuilds
when the upstream documentation changes.

---

## 6. Data storage

All data lives under your home directory:

| | Path |
|---|---|
| macOS / Linux | `~/.imagin-docs-mcp/` |
| Windows | `C:\Users\<YOU>\.imagin-docs-mcp\` |

```
docs/           Cloned documentation repository
lancedb/        Vector search index
models/         Cached embedding model
metadata.json   Index state (commit hash, timestamps)
```

To fully reset, delete that folder and restart your agent:

```sh
# macOS / Linux
rm -rf ~/.imagin-docs-mcp

# Windows CMD
rmdir /s /q %USERPROFILE%\.imagin-docs-mcp

# Windows PowerShell
Remove-Item -Recurse -Force $env:USERPROFILE\.imagin-docs-mcp
```

---

## 7. Telemetry (opt-in)

By default, the MCP server sends **no data** anywhere. All processing is
fully local.

If you'd like to help improve the server, you can opt in to anonymous
crash reporting:

```sh
export IMAGIN_DOCS_TELEMETRY=1
```

When enabled, **only unhandled exceptions** (stack traces) are sent to
Google Cloud Error Reporting. This helps us detect and fix startup
failures, indexing errors, and compatibility issues.

**What is collected:**
- Exception type and stack trace
- Package version and OS platform
- No search queries, no document content, no personally identifiable information

**What is NOT collected:**
- Your search queries or results
- Document content from the index
- IP addresses, usernames, or machine identifiers

To disable, unset the variable or set it to `0`:

```sh
unset IMAGIN_DOCS_TELEMETRY
```

---

## 8. Troubleshooting

**"uvx" not found / "No such file or directory" / "Failed to spawn"**
- Replace `"uvx"` in your config with the **full absolute path**:
  - macOS / Linux: run `which uvx` (typically `~/.local/bin/uvx`)
  - Windows: run `where uvx` (typically `C:\Users\<you>\.local\bin\uvx.exe`)
- Claude Desktop App **always** requires the full path.
- If uvx isn't installed at all, re-run the uv installer from step 1.
- Windows: restart your terminal after installing so PATH updates.
- Verify with: `uv --version`

**"Index is not yet built..."**
- Normal on first start. Wait ~30 seconds and retry.
- Ensure you have internet (the server clones docs from GitHub).
- Some agents may retry too quickly before the index finishes building.
  If you see repeated "not yet built" messages, wait for the initial indexing
  to complete (~20-30 sec) before sending another query.

**MCP server fails on first install**
- This is expected. The first run downloads Python, dependencies, and the
  embedding model, which takes longer than most MCP clients will wait.
- Type `/mcp` in your agent (or use its reconnect/restart MCP command) to
  reconnect. The second attempt will work because everything is cached.
- In Claude Code: type `/mcp`, then reconnect the `imagin-docs` server.
- In Cursor: toggle the server off and on in Settings > Tools & MCP.
- In other agents: restart the agent or IDE.

**Agent doesn't see the MCP server**
- Double-check the config file path for your agent (section 4).
- Restart the agent / IDE after saving.
- Claude Code CLI: run `claude --mcp-debug` for protocol logs.

**Slow first startup**
- The embedding model (~50 MB) downloads once on first run.
- Subsequent starts reuse the cached model and are near-instant.

**Windows long path errors**
- Enable long paths: `reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1 /f`
- Restart your terminal.

**PowerShell blocks the uv install script**
- Run: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`
- Then re-run the install command.
- Alternatively, run with: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

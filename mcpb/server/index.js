#!/usr/bin/env node
// Thin wrapper that finds uvx and spawns the imagin-studio-api-docs-mcp Python server.
// Used by: Claude Desktop .mcpb extension, npx imagin-studio-api-docs-mcp.
//
// Why Node.js? GUI apps (Claude Desktop, Cursor, etc.) don't inherit shell
// PATH, so bare "uvx" fails with ENOENT. This script probes common install
// locations before falling back to PATH lookup.

"use strict";

const { spawn, execFileSync } = require("child_process");
const path = require("path");
const fs = require("fs");
const os = require("os");

// -- Configuration -----------------------------------------------------------

const PACKAGE = "imagin-studio-api-docs-mcp";

// TEMPORARY: TestPyPI index (remove when package moves to real PyPI)
const UVX_ARGS = [
  "--index-url", "https://test.pypi.org/simple/",
  "--extra-index-url", "https://pypi.org/simple/",
  PACKAGE,
];

// -- Find uvx ----------------------------------------------------------------

function findUvx() {
  const home = os.homedir();
  const isWin = process.platform === "win32";
  const bin = isWin ? "uvx.exe" : "uvx";

  // Common install locations (ordered by likelihood)
  const candidates = [
    path.join(home, ".local", "bin", bin),       // default uv install (Linux/macOS)
    path.join(home, ".cargo", "bin", bin),        // cargo install uv
    "/opt/homebrew/bin/uvx",                      // Homebrew on Apple Silicon
    "/usr/local/bin/uvx",                         // Homebrew on Intel / manual symlink
  ];

  if (isWin) {
    const localAppData = process.env.LOCALAPPDATA || path.join(home, "AppData", "Local");
    candidates.unshift(path.join(localAppData, "uv", "bin", "uvx.exe"));
  }

  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }

  // Fall back to PATH lookup — works when launched from a terminal
  try {
    const cmd = isWin ? "where" : "which";
    const result = execFileSync(cmd, [bin], { encoding: "utf8", stdio: ["pipe", "pipe", "ignore"] });
    const resolved = result.trim().split("\n")[0];
    if (resolved && fs.existsSync(resolved)) {
      return resolved;
    }
  } catch {
    // which/where failed — uvx not in PATH
  }

  return null;
}

// -- Main --------------------------------------------------------------------

const uvx = findUvx();

if (!uvx) {
  // Write to stderr only — stdout is reserved for MCP JSON-RPC
  process.stderr.write(
    `Error: uvx not found.\n\n` +
    `The imagin-studio-api-docs-mcp server requires uv (https://docs.astral.sh/uv/).\n\n` +
    `Install uv:\n` +
    `  macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh\n` +
    `  Windows:     powershell -c "irm https://astral.sh/uv/install.ps1 | iex"\n` +
    `  Homebrew:    brew install uv\n`
  );
  process.exit(1);
}

process.stderr.write(`[imagin-studio-api-docs-mcp] Found uvx: ${uvx}\n`);
process.stderr.write(`[imagin-studio-api-docs-mcp] Spawning: ${uvx} ${UVX_ARGS.join(" ")}\n`);

const child = spawn(uvx, UVX_ARGS, {
  stdio: "inherit",
  env: { ...process.env },
});

process.stderr.write(`[imagin-studio-api-docs-mcp] Child PID: ${child.pid}\n`);

// Forward signals to the child process
process.on("SIGINT", () => child.kill("SIGINT"));
process.on("SIGTERM", () => child.kill("SIGTERM"));

// Propagate exit code
child.on("exit", (code, signal) => {
  process.stderr.write(`[imagin-studio-api-docs-mcp] Child exited: code=${code} signal=${signal}\n`);
  if (signal) {
    process.kill(process.pid, signal);
  } else {
    process.exit(code ?? 1);
  }
});

child.on("error", (err) => {
  process.stderr.write(`[imagin-studio-api-docs-mcp] Failed to start uvx: ${err.message}\n`);
  process.exit(1);
});

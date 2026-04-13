# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.21] - 2026-04-13

### Added
- Docker image published to `ghcr.io/imagin-studio/api-docs-mcp` on each release — populates GitHub Packages sidebar and enables `docker pull` for containerized deployments
- OCI image labels (source, description, license, vendor, url, documentation) linking the image to the GitHub repository

## [0.1.20] - 2026-04-13

### Added
- `Dockerfile` for Glama MCP registry inspection and containerized deployment
- `.dockerignore` to keep image builds lean
- `NOTICE` file per Apache 2.0 attribution convention

### Changed
- **License changed from Proprietary to Apache License 2.0** — enables GitHub license detection, Glama install button, and aligns with MCP ecosystem norms
- Added `License :: OSI Approved :: Apache Software License` classifier in pyproject.toml
- Release pipeline now creates git tags and GitHub releases on prod deploys

## [0.1.19] - 2026-04-08

### Changed
- Reverted from `fastembed-imagin-studio` fork to upstream `fastembed>=0.8.0` — resolves CVE-2026-25990 (pillow constraint fixed in [qdrant/fastembed 0.8.0](https://github.com/qdrant/fastembed/releases/tag/v0.8.0))
- Removed fastembed fork disclaimers from PyPI, npm, and setup documentation
- Fixed npm license field to SPDX-compliant format for registry compatibility

### Added
- `glama.json` for Glama MCP directory claim

### Chore
- Gitignore MCP Registry publisher tokens and local publishing docs
- Removed TODO.md (all tasks completed)
- Added project logo

## [0.1.18] - 2026-03-24

### Changed
- Improved GitHub README with quick start config, agent compatibility table, example prompts

## [0.1.17] - 2026-03-24

### Fixed
- MCP Registry namespace: use `io.github.IMAGINstudio` (GitHub username) instead of `io.github.IMAGIN-studio` (org name)

## [0.1.16] - 2026-03-24

### Added
- MCP Registry verification: `mcpName` in npm package.json and `mcp-name` comment in PyPI readme
- `server.json` for official MCP Registry publication

## [0.1.15] - 2026-03-24

### Changed
- Renamed fastembed fork dependency from `fastembed-imagin` to `fastembed-imagin-studio`

## [0.1.14] - 2026-03-24

### Added
- `smithery.yaml` for Smithery MCP registry listing

### Changed
- Bump GitHub Actions `checkout` to v5 and Node.js to 22 (fixes deprecation warnings)

## [0.1.13] - 2026-03-24

### Changed
- Fixed fastembed disclaimer: PR #599 is merged, not open — replaced with release request issue #606
- Added pending items to TODO.md (GitBook sync, TestPyPI account, MCP registries)

## [0.1.12] - 2026-03-24

### Changed
- Renamed package from `imagin-docs-mcp` to `imagin-studio-api-docs-mcp`
- npm package scoped as `@imagin.studio/api-docs-mcp`
- Moved fastembed fork disclaimer to top of PyPI and npm readmes
- Repository URLs updated from Bitbucket to GitHub (`IMAGIN-studio/api-docs-mcp`)
- Transferred `imagin-studio-docs-public` and `fastembed-imagin` repos to IMAGIN-studio org

### Added
- GitHub README.md for public repository landing page
- Automated Bitbucket-to-GitHub sync pipeline step (publishes clean commits on prod merge)
- npm package added to `imagin.studio` org

## [0.1.11] - 2026-03-02

### Added
- Telemetry documentation in SETUP.md (what is collected, how to enable/disable)
- Startup log hint encouraging telemetry opt-in

### Changed
- Sanitized internal URLs from CLAUDE.md and CHANGELOG.md for public GitHub publication
- Removed `.mcp.json` from git tracking (contains local paths)

## [0.1.10] - 2026-03-02

### Added
- Opt-in crash reporting via Google Cloud Error Reporting (set `IMAGIN_DOCS_TELEMETRY=1` to enable)
- Telemetry module (`src/telemetry.py`) using GCE REST API — zero new dependencies
- Allowlisted write-only API keys in gitleaks config
- npm README: added `fastembed-imagin` fork disclaimer

## [0.1.9] - 2026-02-27

### Added
- README for npm package (shown on npmjs.com package page)

### Fixed
- PyPI and npm publish steps now run in parallel on prod (npm no longer blocked by PyPI)
- `twine upload --skip-existing` so pipeline re-runs don't fail on already-published versions

## [0.1.8] - 2026-02-27

### Added
- Published `imagin-docs-mcp` npm package — `npx imagin-docs-mcp` now works
- `publish-npm` pipeline step in bitbucket-pipelines.yml (prod branch, after PyPI publish)

### Changed
- SETUP.md: npx install method is now active (removed "coming soon" notice)

## [0.1.7] - 2026-02-27

### Added
- `pip install` instructions in SETUP.md (section 3) as alternative to uvx

### Changed
- `make publish` and `make publish-test` now refuse to run outside Bitbucket Pipelines — publishing must go through the DTAP pipeline

### Fixed
- Install `curl` in pipeline steps that download binaries (gitleaks, taplo) — `python:3.12-slim` doesn't include it
- Pipeline publish steps now read PyPI tokens from Bitbucket repository variables (`PYPI_TOKEN`, `TESTPYPI_TOKEN`)

## [0.1.6] - 2026-02-27

### Changed
- Published to real PyPI — `uvx imagin-docs-mcp` now works without TestPyPI flags
- Upgraded `fastembed-imagin` fork to 0.7.5.2 (rebased on upstream `main`, includes CUDA support, ModernVBERT, Python 3.9 drop)
- Simplified all agent config examples in SETUP.md (removed `--index-url` args)
- Removed TestPyPI `--extra-index-url` from requirements.txt and Makefile setup targets
- Removed TestPyPI `[[tool.uv.index]]` from mcpb/pyproject.toml
- Simplified npx wrapper UVX_ARGS (no index args needed)

### Added
- `publish` Makefile target for real PyPI
- `publish-pypi` pipeline step in bitbucket-pipelines.yml (prod branch, deployment approval)
- Dependency disclaimer in SETUP.md explaining fastembed-imagin fork and pip-audit behavior

## [0.1.5] - 2026-02-19

### Changed
- Reverted from `fastmcp-imagin` fork to upstream `fastmcp>=3.0.0,<4.0.0` — resolves CVE-2025-69872 (`diskcache` removed upstream in [PrefectHQ/fastmcp#3185](https://github.com/PrefectHQ/fastmcp/pull/3185))

## [0.1.4] - 2026-02-13

### Changed
- `SETUP.md` — marked npx install method as "coming soon" (npm package not yet published)

## [0.1.3] - 2026-02-13

### Changed
- Quick start prompt now instructs agents to read setup instructions before installing
- Replaced `fastembed` dependency with temporary `fastembed-imagin` fork to resolve pillow CVE-2026-25990 (tracks [qdrant/fastembed#599](https://github.com/qdrant/fastembed/pull/599))
- Replaced `fastmcp` dependency with temporary `fastmcp-imagin` fork to remove `diskcache` CVE-2025-69872 (tracks [jlowin/fastmcp#3166](https://github.com/jlowin/fastmcp/issues/3166))

### Added
- `npm/` npx wrapper — `npx imagin-docs-mcp` auto-finds uvx and spawns the Python server (no manual PATH config)
- `mcpb/` MCP bundle — `type: "uv"` extension for Claude Desktop one-click install (blocked on PyPI release due to uv index resolution)
- `SETUP.md` — agent instruction in Quick Start to read setup page when user shares the install link
- `SETUP.md` — first-run timeout warnings in Quick Start, First Run, and Troubleshooting sections with per-agent reconnect steps
- `SETUP.md` — cross-platform setup guide with step-by-step instructions for 7 coding agents (Claude Code, Claude Desktop, Cursor, Windsurf, VS Code + Copilot, Cline, Zed), wired as PyPI package description via `readme = "SETUP.md"`
- `MANIFEST.in` to control package contents — only `src/` and `pyproject.toml` included in sdist/wheel
- Proprietary license (all rights reserved, install-and-use only)
- Package metadata: author, maintainer, classifiers, project URLs, keywords
### Changed
- Upgraded `fastembed` from 0.5.x to 0.7.x (resolves pillow CVE-2026-25990 for pillow <12.0)
- Renamed PyPI package from `imagin-docs-mcp-local` to `imagin-docs-mcp` so `uvx imagin-docs-mcp` works without `--from`
- `CHARACTER_LIMIT` now derived from `SEARCH_TOP_K_MAX * (MAX_CHUNK_CHARS + 200)` to guarantee all results fit without truncation at any valid `top_k`
- `publish-test` Makefile target now uses `--repository testpypi` to pick up `~/.pypirc` credentials
- License field uses SPDX expression (`LicenseRef-Proprietary`) per PEP 639
- Removed deprecated `Private :: Do Not Upload` and `License ::` classifiers

### Fixed
- MCP context logging (`ctx.info`, `ctx.warning`, `ctx.error`) now properly sends notifications to clients

### Changed
- Upgraded FastMCP from 0.4.x to 2.14.x (fixes silent log drop due to unawaited async coroutine)
- `search_docs()` tool is now async to support awaited context logging
- Added `asyncio_mode = "auto"` to pytest config for async test support
- Error messages in `search_docs()` are now actionable with retry guidance and rephrasing suggestions
- `_format_results()` now displays source URLs when available

### Added
- Claude skill for syncing TODO.md/CHANGELOG.md to project tracker
- MCP tool annotations on `search_docs()` (readOnlyHint, idempotentHint, destructiveHint, openWorldHint)
- Configurable `top_k` parameter on `search_docs()` (1–20, default 5) with clamping
- Response truncation at `CHARACTER_LIMIT` (derived from `SEARCH_TOP_K_MAX * MAX_CHUNK_CHARS`) with guidance to reduce `top_k`
- Enhanced `search_docs()` docstring with usage examples, return schema, and error documentation
- 6 new tests for top_k passthrough, clamping, character limit truncation, and URL display
- `publish-test` Makefile target for TestPyPI publishing (with full security gate)
- TestPyPI publish step in `preprod` pipeline (`bitbucket-pipelines.yml`)
- `twine>=6.0.0,<7.0.0` dev dependency for package uploads
- `.mcp.json` for Claude Code CLI MCP server configuration
- Chunk merge post-processing to reduce fragmentation of undersized chunks (`src/pipeline/chunker.py`)
- `MIN_CHUNK_CHARS` config constant (200 chars) for merge threshold (`src/config.py`)
- 6 new tests for chunk merge behaviour (`tests/pipeline/test_chunker.py`)
- Local RAG engine: embedding, vector store, and indexing (`src/engine/`)
- Embedding service with fastembed BAAI/bge-small-en-v1.5 (`src/engine/embedder.py`)
- LanceDB vector store with upsert and semantic search (`src/engine/vector_store.py`)
- Indexing pipeline with skip-if-unchanged optimization (`src/engine/__init__.py`)
- Wired `search_docs()` MCP tool with real vector search and result formatting
- 17 new engine tests (60 total, 87% coverage)
- Document pipeline: git sync, markdown parsing, semantic chunking (`src/pipeline/`)
- Configuration module with data paths and settings (`src/config.py`)
- Cross-platform path utilities (`src/utils/paths.py`)
- Pipeline data models: Document, Chunk, IndexMetadata (`src/pipeline/models.py`)
- Pipeline exceptions: PipelineError, GitSyncError, ParseError (`src/pipeline/exceptions.py`)
- Git sync with clone/update via `git reset --hard` (`src/pipeline/git_sync.py`)
- Markdown parser with frontmatter extraction (`src/pipeline/markdown_parser.py`)
- Header-based semantic chunker with code block preservation (`src/pipeline/chunker.py`)
- Pipeline orchestrator `run_pipeline()` (`src/pipeline/__init__.py`)
- python-frontmatter dependency
- 38 new tests for pipeline modules (43 total)
- Initial CI/CD setup from imagin-sre templates
- MCP server foundation structure (src/server.py, src/main.py)
- Pre-commit hooks (branch protection, secrets, conventional commits)
- BitBucket Pipeline configuration
- Security scanning (CVE checks via pip-audit, secrets via gitleaks)
- Claude Code skills (make-pipeline, git-workflow, python-dev, startup)

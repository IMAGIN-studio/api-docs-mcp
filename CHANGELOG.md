# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.29] - 2026-11-10

### Added
- Every release now attaches the Claude Desktop extension to its GitHub Release as `imagin-studio-api-docs-mcp.mcpb` (new `publish-mcpb` job). The job checks that the extension version matches the package version, packs `mcpb/` with the `@anthropic-ai/mcpb` CLI 2.1.2 (its dependencies held to releases at least two weeks old with npm's `--before`), waits for the release that the Bitbucket prod pipeline creates, and uploads the file. Until now no release built the extension, so its name and texts reached nobody.
- README and setup guide link the one-click install: `releases/latest/download/imagin-studio-api-docs-mcp.mcpb` always serves the newest build.

### Fixed
- Claude Desktop extension: the uv runtime now starts the server with `uv run --directory ${__dirname} server.py`, as in the official MCPB uv example. The old `uv run ${__dirname}/server.py` looked for `pyproject.toml` in the host's working folder instead of the bundle, so the package was never installed and the server stopped with `No module named 'src'`.
- CI: the MCP Registry job now waits until PyPI and npm actually serve the new version (up to 10 minutes per package, read from `server.json`) before logging in and publishing, and retries the publish up to 3 times. In the 0.1.28 release the registry validated 77 seconds before npm made the version visible ("version '0.1.28' was not found") and the job failed. Also turns a silently failed npm publish (its `|| echo` fallback) into a visible error.

### Removed
- `mcpb/server/index.js`, an old Node wrapper from before the extension used the uv runtime. The bundle already excluded it, and it still pointed at TestPyPI. The `server/` line in `mcpb/.mcpbignore` went with it.

## [0.1.28] - 2026-11-10

### Added
- The release workflow now publishes `server.json` to the official MCP Registry (new `publish-mcp-registry` job, after the PyPI and npm jobs). It authenticates with GitHub OIDC, so no secret is involved, and runs `mcp-publisher` v1.8.5, pinned by version and SHA-256. Until now the registry entry was published once, by hand, and stayed at 0.1.17 with the old description.

### Changed
- MCP Registry name is now `io.github.IMAGIN-studio/api-docs-mcp` (was `io.github.IMAGINstudio/api-docs-mcp`). The old name belongs to a separate GitHub user account (`IMAGINstudio`), which release-workflow OIDC cannot publish for; OIDC grants the namespace of the repository owner, the `IMAGIN-studio` organization. Updated in `server.json`, the npm `mcpName` and the PyPI `mcp-name` marker in `SETUP.md`. The old 0.1.17 entry stays in the registry until someone logs in to `mcp-publisher` as the `IMAGINstudio` user once and marks it deprecated with `mcp-publisher status`.

## [0.1.27] - 2026-11-10

### Changed
- All dependencies updated to the newest release that is at least two weeks old (cutoff 27 Oct 2026). Runtime: fastmcp 3 to 4.1.4, lancedb 0.17 to 0.40, fastembed 0.8 to 0.9.1 (which allows Pillow 13), plus raised floors for pydantic, python-dotenv, pyyaml and python-frontmatter. Dev: ruff 0.1 to 0.17, mypy 1 to 2.4, twine 6 to 7, pytest 9.1.1 and the rest of `requirements-dev.txt`. No code changes were needed for fastmcp 4; lint and type checks pass unchanged.
- New `requirements.lock`: exact pins for all 146 runtime and dev packages (including the setuptools build backend), transitive ones included, every one at least 14 days old. `make install`, `make install-dev` (and so CI), `make build-package`, the release workflow's build and the Docker image install through it as constraints (`PIP_CONSTRAINT` also reaches pip's isolated build environments). `make lock` regenerates it with a rolling cutoff (`LOCK_MIN_AGE_DAYS`, default 14). Users installing with `uvx` still resolve from the version ranges in `pyproject.toml`.
- lancedb 0.40: replaced the deprecated `table_names()` and `create_fts_index()` with `list_tables()` and `create_index(config=FTS(...))`. The keyword index now removes stop words: lancedb's new BM25 let filler words in sentence-style questions outrank the words that matter. On the 62-question eval this gives hit@1 0.69, hit@5 0.87 and MRR 0.77 (0.1.26: 0.66, 0.85, 0.74); identifier questions are unchanged.
- CI and release tooling pinned to releases at least two weeks old: GitHub Actions by commit SHA (checkout v7.0.1, setup-python v7.1.0, setup-node v7.1.0, pypi-publish v1.14.3, Docker login v4.7.0, setup-buildx v4.4.1, build-push v7.4.0), npm 12.2.1 instead of `npm@latest`, `build` 1.6.1, gitleaks 8.30.1, taplo 0.10.0, and the `python:3.12.15-slim-trixie`, `alpine:3.24.3` and `alpine/git:2.52.0` images by digest.
- Docker image is now built from the release commit instead of `pip install imagin-studio-api-docs-mcp` from PyPI. The release workflow publishes to PyPI and builds the image in parallel, so the image could contain the previous version under the new tag (and with the lock constraints the build would fail outright). Its dependencies and build backend are pinned through `requirements.lock`, and its description label uses the agreed one-liner.

### Security
- Clears the 94 advisories `pip-audit` reported against the previous dependency set (including fastmcp, mcp, cryptography, urllib3, authlib, pyjwt and Pillow), which would have failed the preprod and prod release gate.

## [0.1.26] - 2026-11-10

### Changed
- One consistent set of public texts, agreed with marketing. Name "IMAGIN.studio API Docs MCP Server" (short form "IMAGIN.studio API Docs"); one-liner "Give your AI coding assistant direct access to the IMAGIN.studio vehicle imagery API docs." in `server.json`, `pyproject.toml`, `npm/package.json` and `mcpb/manifest.json`; company link `https://www.imaginstudio.com/` everywhere (`imagin.studio` redirects there). The Claude Desktop extension is now called "IMAGIN.studio API Docs" instead of "IMAGIN.studio Docs".
- README and the PyPI page (`SETUP.md`) open with the docs.imagin.studio pitch, and the README's example prompts are the IMAGIN-specific ones from the docs site. Jargon ("semantic search", "RAG", "npx wrapper") is gone from the one-liners. Agent-facing texts (server instructions, `search_docs` description) are unchanged.

## [0.1.25] - 2026-11-10

### Changed
- `search_docs` now runs a hybrid search: the existing vector search (by meaning) plus a BM25 full-text index (by exact words), merged with reciprocal rank fusion (RRF, implemented in `fuse_rankings`; candidate depth, RRF k and keyword weight are settings in `config.py`, tuned with the eval below). Exact identifiers such as `safeMode` or `x-imaginstudio-performed-matches` are now found even when the vector ranking misses them. The full-text index uses LanceDB's native FTS, so there is no new dependency; if it is missing or fails, search falls back to vector-only.
- Chunks are now at most 2,000 characters (was 8,192). The embedding model only reads the first 512 tokens of an input, so in the 18 longest chunks (including the getImage reference and CDN Data Points) everything past roughly 2,000 characters was invisible to search. Later parts of a split section start with `# <heading> (continued)`.
- Long OpenAPI endpoints are now split into labelled parts (`GET /getImage (continued)`) instead of truncated, so no parameter is dropped at the smaller chunk size.
- Queries are embedded with BGE's retrieval instruction ("Represent this sentence for searching relevant passages: "), as the model expects; documents are embedded without it.
- The docs page about this MCP server (`api-integration/manuals/mcp-api-documentation.md`) is no longer indexed: it lists example questions, so it matched many unrelated queries. Configurable via `INDEX_EXCLUDE_PATHS`.

### Added
- `eval/`: a retrieval evaluation (62 questions with expected pages across identifier, how-to and concept questions, written without looking at the search code) and a script that sweeps chunk size, query instruction, search mode, fusion settings and index exclusions, scoring hit@1, hit@5 and MRR. On this set the combined changes raise hit@1 from 0.39 to 0.66, hit@5 from 0.71 to 0.85 and MRR from 0.50 to 0.74. Dev-only; excluded from the package.

## [0.1.24] - 2026-09-07

### Fixed
- The npx install path in the PyPI setup guide (`SETUP.md`) pointed at `imagin-studio-api-docs-mcp`, an unscoped npm name that was never published — the wrapper has been `@imagin.studio/api-docs-mcp` since 0.1.12. The bulk rename in 0.1.12 (`imagin-docs-mcp` → `imagin-studio-api-docs-mcp`) rewrote the npx lines along with the PyPI ones, so anyone following the guide's `npx -y …` command hit a 404 (or, worse, whoever registers that unclaimed name). Also fixed the stale `npx imagin-studio-api-docs-mcp` header comments in `npm/bin/imagin-studio-api-docs-mcp.js` and `mcpb/server/index.js`.

### Changed
- Synced project scaffolding with the current `imagin-sre` CI/CD templates (`cicd-base` + `cicd-python`): the Makefile gains the template's `install` / `install-dev` targets (both were already documented in AGENTS.md but did not exist), `setup` / `setup-ci` are composed from them, `clean` no longer deletes the venv (that moved to the new `clean-all`), the coverage threshold falls back to 80 when `project.yaml` is absent, and `make hooks` shows up in `make help`. Also picked up the template's `commit` skill wording, the `---` document marker in `lefthook.yml`, the shared `.idea/misc.xml`, and `project.yaml` now tracks the release version. Ruff config intentionally stays in `pyproject.toml` (identical rules to the template's `.config/ruff.toml`, plus this repo's per-file ignores).
- CI: the `publish-github` release step now authenticates to GitHub with a short-lived (~9 min) GitHub App installation token minted in-pipeline, instead of a long-lived `GITHUB_TOKEN` PAT. Requires repo variables `GH_APP_ID`, `GH_APP_INSTALLATION_ID`, and secured `GH_APP_PRIVATE_KEY_B64` (base64 of the App's private key).

### Security
- Dev toolchain: bumped `pytest` (7.x → 9.0.3+, with `pytest-cov` → 7.x and `pytest-asyncio` → 1.4.x) and switched `gitlint` → `gitlint-core` with floor pins `click>=8.3.3` / `sh>=2.2.4`, clearing 3 advisories (PYSEC-2026-1845, PYSEC-2026-2132, CVE-2026-54552) that failed the pre-publish `pip-audit` gate. Dev/CI-only — no runtime dependency or shipped-package change.

## [0.1.23] - 2026-07-21

### Added
- Index the IMAGIN CDN image-API spec (`getImage`, `getCarListing`, `getPaints`, `getPaintswatches`, `getImagecachebundle`) as one searchable chunk per endpoint, alongside the existing markdown docs, so `search_docs` can answer API/parameter questions. Sourced from the committed `openapi (1).yaml` in the docs repo — local `$ref` parameters/schemas are resolved into each chunk, and the spec re-indexes automatically via the existing git sync. Disable with `IMAGIN_DOCS_OPENAPI=0`.
- DTAP promotion guard in Bitbucket Pipelines — blocks deploys/publishes when a branch HEAD does not contain its expected upstream commit (enforces the `main → dev → test → preprod → prod` sequence). Borrowed from `imagin-prospect-demo-platform`.

### Removed
- Dead `publish-pypi` and `publish-npm` step definitions from `bitbucket-pipelines.yml` — never referenced by any branch pipeline. Both PyPI and npm publishing happen through GitHub Actions (OIDC-based) after `publish-github` pushes the release commit. The Bitbucket pipeline variables `PYPI_TOKEN` and `NPM_TOKEN` are no longer used and can be removed from the repo settings.

### Fixed
- npm publish GitHub Actions step now upgrades npm to the latest version before publishing — required for OIDC Trusted Publishing support (npm ≥ 11.5.1). Node 22's bundled npm 10.x cannot auto-detect the OIDC token, which would silently fail the publish.

## [0.1.22] - 2026-05-26

### Security
- npm publishing migrated to Trusted Publishing (OIDC) — eliminates the long-lived `NPM_TOKEN` secret and adds package provenance attestations, matching the existing PyPI flow

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

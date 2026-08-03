# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.4] - 2026-08-03

### Changed

- README install and client-configuration examples now use `uvx mcp-sonarcloud@latest` (and `uv tool install mcp-sonarcloud@latest`). Without `@latest`, `uvx` reuses a previously cached tool environment, so existing users would keep running the broken pre-0.1.4 resolve and never pick up the SDK fix below.

### Fixed

- Constrained the MCP Python SDK dependency to `mcp>=1.10.0,<2`. The SDK's 2.0.0 release (2026-07-28) removed `mcp.server.fastmcp`, which this server imports, so any fresh install resolving to 2.x crashed on startup with `ModuleNotFoundError: No module named 'mcp.server.fastmcp'` and the server never connected. The previous floor of `>=1.0.0` was also wrong in the other direction: `mcp.server.fastmcp` only appeared in 1.2.0, and FastMCP only emits `outputSchema` / structured content from 1.10.0, so older 1.x resolves either crashed identically or started with the tools' declared output schemas silently missing. The committed `uv.lock` pinned the SDK at 1.27.0, so `uv sync` and local development were unaffected; the break reached only installs that resolve fresh from PyPI. CI would have caught it — the `package-smoke` job builds the wheel and resolves it from the index, bypassing the lock — but no run happened on `main` between the SDK 2.0.0 release and this change. The cap stays until the server is ported to the 2.x API.

## [0.1.3] - 2026-04-03

### Added

- Root `CHANGELOG.md` using the Keep a Changelog format and seeded package history.
- Added Ruff and `ty` as supported development checks for the packaged `src/` tree.
- Added a repo-specific `AGENTS.md` contributor guide covering layout, commands, and configuration expectations.

### Changed

- `project.urls.Changelog` now points to the in-repo changelog instead of the generic GitHub releases page.
- The release flow now treats changelog maintenance as a required step and reuses changelog sections for GitHub release notes.
- Reworked `RELEASING.md` into an evergreen release checklist with explicit validation, tagging, and publish steps.

## [0.1.1] - 2026-03-29

### Added

- Exposed `__version__` from installed package metadata for runtime and CLI consistency.

### Changed

- Standardized the sample-config replacement flag on `--overwrite`.
- Strengthened the publish workflow with explicit release gating before PyPI upload.
- Updated GitHub Actions dependencies to Node 24-ready versions.

## [0.1.0] - 2026-03-28

### Added

- Initial PyPI release for `uvx mcp-sonarcloud`.
- Package-native bootstrap commands for `--write-sample-config` and `--print-paths`.
- Trusted PyPI publishing with GitHub Actions and manual `pypi` environment approval.
- Wheel and source-distribution smoke tests for packaged installs.

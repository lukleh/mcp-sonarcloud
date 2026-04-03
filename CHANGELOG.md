# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

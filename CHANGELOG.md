# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

# Repository Guidelines

## Project Structure & Module Organization
`src/mcp_sonarcloud/server.py` contains the FastMCP server, request helpers, Pydantic response models, and the CLI entry point. Runtime-path resolution is isolated in `src/mcp_sonarcloud/runtime_paths.py`, and package metadata lives in `src/mcp_sonarcloud/__init__.py`. Tests are concentrated in `tests/test_server.py`, while `README.md`, `DEVELOPMENT.md`, and `SONARCLOUD_API_SUPPORT.md` document the public API surface and maintenance expectations.

## Build, Test, and Development Commands
- `uv sync --extra dev` installs runtime and development dependencies.
- `uv run mcp-sonarcloud --print-paths` shows the resolved config, state, and cache directories.
- `uv run mcp-sonarcloud --write-sample-config` writes the default `config.toml`; add `--overwrite` only when replacing it intentionally.
- `uv run pytest -q` runs the full test suite.
- `uv run pytest tests/test_server.py -q` runs the focused SonarCloud tool coverage.
- `uv run ruff check src tests` runs linting.
- `uv run ty check` runs the type checker on `src/`.

## Coding Style & Naming Conventions
Target Python 3.11+ with four-space indentation, explicit type hints, and async-first request code. Keep the current single-server-file structure unless a change is large enough to justify extraction. Use `snake_case` for functions, variables, and tests; use `PascalCase` for Pydantic models. New MCP tool parameters should continue to use `pydantic.Field()` descriptions with explicit valid values and concrete examples where that improves agent usability.

## Testing Guidelines
Tests rely on `pytest`, `pytest-asyncio`, and `pytest-httpx`, so new API behavior should be covered with mocked HTTP exchanges rather than live SonarCloud calls. Update `tests/test_server.py` whenever request parameters, response parsing, organization scoping, or hotspot status validation changes. Prefer asserting both the outbound request shape and the structured response model.

## Commit & Pull Request Guidelines
Use short imperative commit subjects and keep each commit scoped to one behavior change. Pull requests should summarize the affected SonarCloud endpoints or tools, list the commands you ran, and call out any config-surface changes to `config.toml`, environment overrides, or tool parameter contracts.

## Security & Configuration Tips
Do not hardcode `SONARCLOUD_TOKEN` or other credentials in source-controlled files; secrets belong in the runtime environment only. Keep the config file focused on non-secret defaults such as base URL, organization, and timeout. Preserve the existing auth header behavior, organization override rules, and explicit validation for hotspot status and resolution values.

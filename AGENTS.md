# Repository Guidelines

## Project Structure & Module Organization

- `synxis_pms_mcp/` contains the MCP server package, API clients, tool implementations, and config helpers for PMS integrations.
- `settings/` stores environment-specific defaults, while `docs/` and root docs should remain the operator-facing source of truth.
- Tests should mirror the package structure for reservation, property, and operations coverage.

## Build, Test, and Development Commands

- `uv sync --group dev` installs development dependencies.
- Use the documented local server commands for smoke tests.
- `uv run pytest` runs the full suite.
- `uv run ruff check synxis_pms_mcp tests` and `uv run ruff format synxis_pms_mcp tests` cover linting and formatting.
- Run project quality checks through Crackerjack before landing changes.

## Coding Style & Naming Conventions

- Use explicit type hints, validated request models, and small composable client helpers.
- Keep modules snake_case and tool responses structured and predictable.

## Testing Guidelines

- Add tests for PMS workflows, property lookups, and provider error handling.
- Prefer mocked API responses over live-network tests unless the case explicitly needs end-to-end verification.

## Commit & Pull Request Guidelines

- Use focused commits such as `feat(property): add room status lookup tool`.
- PRs should describe tool impact, commands run, and any auth or schema changes.

## Security & Configuration Tips

- Never commit credentials, tenant identifiers, or customer data.
- Scrub reservation and guest details from fixtures and troubleshooting logs.

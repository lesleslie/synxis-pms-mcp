# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-08-28

### Documentation

- readme: Bump Python badge from 3.13+ to 3.14+

### Internal

- Bump requires-python to >=3.14
- Re-pin python to 3.14
- synxis-pms-mcp: Bump tool-config pins from 3.13 to 3.14

## [0.4.0] - 2026-08-21

### Added

- Complete SynXis PMS MCP server implementation
- Implement real SynXis PMS API integration with OAuth2
- synxis-pms-mcp: Adopt apply_tool_profile() (W4.8)
- synxis-pms-mcp: Plan 7 Phase 5 — FastMCP 3.4 migration
- synxis-pms: Bodai plugin conversion (manifest, mcp.json, slash commands)

### Changed

- Initial commit: Crackerjack initialization for synxis-pms-mcp
- Update core functionality

### Fixed

- synxis-pms-mcp: Register /healthz outside caller-supplied branch (M-1)
- synxis-pms-mcp: Sort imports in test_doc_drift.py
- synxis-pms-mcp: Sync version stamps (2026-08-19)
- Track .cache dir via .gitkeep for gitleaks support

### Documentation

- Align README version, description, tests tree, and gitignore backup patterns
- synxis-pms-mcp: Fix documented-but-not-wired audit findings (2026-08-19)
- synxis-pms-mcp: Remove duplicate ## Project Overview section (2026-08-19)

### Testing

- synxis-pms-mcp: Add doc-drift CI guard (2026-08-19)

### Internal

- Add mypy.ini and track .cache dir for quality tooling
- Add Unofficial prefix to description
- Adopt register_http_health_route from mcp-common
- Bump oneiric dep to >=0.16.0
- Bump version to 0.1.1
- Bump version to 0.1.3
- Bump version to 0.1.4
- Bump version to 0.1.5
- Bump version to 0.2.0
- Bump version to 0.2.1
- Gitignore runtime artifacts + untrack user-authorized cache files (bodai cleanup 2026-08-17)
- gitignore: Untrack .pyscn/ (bodai 2026-08-20)
- Restore LICENSE and normalize attribution
- synxis-pms-mcp: Bootstrap [tool.crackerjack] section + uv sync upgrade
- synxis-pms-mcp: Bump version 0.2.1 -> 0.3.0
- synxis-pms-mcp: Gitignore .lycheecache (file, not just dir)
- synxis-pms-mcp: Gitignore .lycheecache + .hypothesis
- synxis-pms-mcp: Migrate MCPBaseSettings → OneiricMCPConfig
- synxis-pms-mcp: Remove bare # type: ignore straggler in cli.py
- synxis-pms-mcp: Untrack .lycheecache + .hypothesis runtime artifacts
- Untrack and delete 2 historical *.backup/*.bak files
- Update LICENSE copyright to 2026

## [0.2.1] - 2026-08-17

### Documentation

- Align README version, description, tests tree, and gitignore backup patterns

## [0.2.0] - 2026-08-12

### Added

- synxis-pms-mcp: Plan 7 Phase 5 — FastMCP 3.4 migration

### Internal

- Adopt register_http_health_route from mcp-common
- Bump oneiric dep to >=0.16.0
- Restore LICENSE and normalize attribution
- synxis-pms-mcp: Migrate MCPBaseSettings → OneiricMCPConfig
- synxis-pms-mcp: Remove bare # type: ignore straggler in cli.py

## [0.1.5] - 2026-06-20

### Fixed

- Track .cache dir via .gitkeep for gitleaks support

### Internal

- Add mypy.ini and track .cache dir for quality tooling
- Untrack and delete 2 historical *.backup/*.bak files

## [0.1.4] - 2026-05-10

### Added

- Implement real SynXis PMS API integration with OAuth2

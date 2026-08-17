# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

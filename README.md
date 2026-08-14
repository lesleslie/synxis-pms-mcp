# SynXis PMS MCP Server

[![Code style: crackerjack](https://img.shields.io/badge/code%20style-crackerjack-000042)](https://github.com/lesleslie/crackerjack)
[![Runtime: oneiric](https://img.shields.io/badge/runtime-oneiric-6e5494)](https://github.com/lesleslie/oneiric)
[![Framework: FastMCP](https://img.shields.io/badge/framework-FastMCP-0ea5e9)](https://github.com/jlowin/fastmcp)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Python: 3.13+](https://img.shields.io/badge/python-3.13%2B-green)](https://www.python.org/downloads/)

Unofficial MCP server for SynXis PMS (Property Management System) API.

**Version:** 0.2.0
**Status:** Internal Bodai integration component

## Quick Links

- [Overview](#overview)
- [Capabilities](#capabilities)
- [Quick Start](#quick-start)
- [MCP Server Configuration](#mcp-server-configuration)
- [Tool Reference](#tool-reference)
- [Configuration](#configuration)
- [Development](#development)

## Quality & CI

Crackerjack is the standard quality-control and CI/CD gate for SynXis PMS MCP changes. Local verification should mirror the Crackerjack workflow used across the Bodai ecosystem.

______________________________________________________________________

## Overview

SynXis PMS MCP exposes property-management workflows through a FastMCP server. It is designed for agent-facing hotel operations such as guest lookup, room status checks, check-in, check-out, and folio review while keeping provider credentials, request validation, and transport concerns in a narrow integration boundary.

The server is intentionally separate from `synxis-crs-mcp`. PMS owns on-property operational workflows; CRS owns central reservation shopping, rates, availability, and booking workflows.

## Capabilities

Implemented tool surface:

- **Guest lookup**: retrieve guest profile details by guest ID
- **Room status**: inspect room status, type, features, floor, and occupancy
- **Check-in**: assign a room and complete guest arrival workflow
- **Check-out**: complete departure workflow and return billing summary details
- **Folio lookup**: retrieve charges, payments, totals, and balance information
- **Mock mode**: exercise the MCP tool surface without live SynXis credentials
- **HTTP health routes**: `/health` and `/healthz` for MCP client and process supervision checks

## Quick Start

### Prerequisites

- Python 3.13+
- UV package manager
- SynXis PMS OAuth2 credentials for live API access

### Local Setup

```bash
git clone https://github.com/lesleslie/synxis-pms-mcp.git
cd synxis-pms-mcp
uv sync --group dev
```

### Run In Mock Mode

Mock mode is the safest way to validate client wiring and tool behavior before using live credentials.

```bash
export SYNXIS_PMS_MOCK_MODE=true
uv run synxis-pms-mcp start
uv run synxis-pms-mcp health
```

### Run With Live Credentials

```bash
export SYNXIS_PMS_CLIENT_ID="your-client-id"
export SYNXIS_PMS_CLIENT_SECRET="your-client-secret"
export SYNXIS_PMS_PROPERTY_ID="your-property-id"
uv run synxis-pms-mcp start
```

The default HTTP bind is `127.0.0.1:3047`.

## CLI Commands

The CLI is built with `mcp-common` and provides the standard lifecycle command surface used by Bodai MCP servers.

```bash
uv run synxis-pms-mcp start      # Start the HTTP MCP server
uv run synxis-pms-mcp stop       # Stop the managed server process
uv run synxis-pms-mcp restart    # Restart the managed server process
uv run synxis-pms-mcp status     # Show process status
uv run synxis-pms-mcp health     # Run the local health probe
```

## MCP Server Configuration

### Claude / Codex Style Configuration

Add the server to an MCP client configuration:

```json
{
  "mcpServers": {
    "synxis-pms": {
      "command": "uv",
      "args": ["run", "synxis-pms-mcp", "start"],
      "cwd": "/Users/les/Projects/synxis-pms-mcp",
      "env": {
        "SYNXIS_PMS_MOCK_MODE": "true"
      }
    }
  }
}
```

For live access, replace mock mode with credential environment variables supplied by your secret manager.

### Health Checks

```bash
curl http://127.0.0.1:3047/health
curl http://127.0.0.1:3047/healthz
```

## Tool Reference

| Tool | Purpose | Required Inputs |
|------|---------|-----------------|
| `get_guest` | Retrieve guest profile details | `guest_id` |
| `get_room_status` | Retrieve room status and room metadata | `room_id` |
| `check_in` | Check in a reservation to a room | `reservation_id`, `room_id` |
| `check_out` | Check out a reservation and return billing summary | `reservation_id` |
| `get_folio` | Retrieve folio charges, payments, totals, and balance | `reservation_id` |

Tool responses follow a consistent `ToolResponse` shape:

```json
{
  "success": true,
  "message": "Room 1201 status: clean",
  "data": {},
  "error": null,
  "next_steps": []
}
```

## Configuration

Committed defaults live in `settings/synxis-pms.yaml`. Runtime overrides should come from environment variables or a local `.env` file that is not committed.

| Setting | Environment Variable | Default |
|---------|----------------------|---------|
| Client ID | `SYNXIS_PMS_CLIENT_ID` | empty |
| Client secret | `SYNXIS_PMS_CLIENT_SECRET` | empty |
| Base URL | `SYNXIS_PMS_BASE_URL` | `https://api.synxis.com/pms/v1` |
| Property ID | `SYNXIS_PMS_PROPERTY_ID` | empty |
| Mock mode | `SYNXIS_PMS_MOCK_MODE` | `false` |
| Timeout | `SYNXIS_PMS_TIMEOUT` | `30.0` |
| Max retries | `SYNXIS_PMS_MAX_RETRIES` | `3` |
| HTTP host | `SYNXIS_PMS_HTTP_HOST` | `127.0.0.1` |
| HTTP port | `SYNXIS_PMS_HTTP_PORT` | `3047` |
| Log level | `SYNXIS_PMS_LOG_LEVEL` | `INFO` |
| JSON logs | `SYNXIS_PMS_LOG_JSON` | `true` |

## Project Structure

```text
synxis_pms_mcp/
  cli.py              # mcp-common lifecycle CLI
  client.py           # SynXis PMS client boundary
  config.py           # Pydantic settings and logging
  models.py           # Typed PMS domain models
  server.py           # FastMCP application factory
  tools/pms_tools.py  # Registered MCP tools
settings/
  synxis-pms.yaml     # Committed defaults
tests/
  __init__.py
  test_example.py
  unit/
    test_fastmcp_version.py
    test_no_direct_fastmcp_imports.py
```

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check synxis_pms_mcp tests
uv run ruff format synxis_pms_mcp tests
```

Use direct `pytest` commands for targeted debugging:

```bash
uv run pytest tests/test_example.py -v
```

## Security Notes

- Do not commit SynXis credentials, bearer tokens, tenant identifiers, guest profile data, or folio/payment details.
- Keep examples and tests on mock mode or scrubbed fixtures.
- Treat check-in, check-out, room assignment, and billing payloads as sensitive operational data.
- Keep SynXis URLs, ports, and property settings configurable rather than hard-coded in new code.

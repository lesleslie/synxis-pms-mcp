# SynXis PMS MCP Server

[![Code style: crackerjack](https://img.shields.io/badge/code%20style-crackerjack-000042)](https://github.com/lesleslie/crackerjack)
[![Runtime: oneiric](https://img.shields.io/badge/runtime-oneiric-6e5494)](https://github.com/lesleslie/oneiric)
[![Framework: FastMCP](https://img.shields.io/badge/framework-FastMCP-0ea5e9)](https://github.com/jlowin/fastmcp)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Python: 3.13+](https://img.shields.io/badge/python-3.13%2B-green)](https://www.python.org/downloads/)

MCP server for SynXis PMS (Property Management System) integrations.

## Overview

This repository exposes PMS-oriented SynXis operations through FastMCP, with a focus on property workflows, reservation-adjacent operations, and typed request validation. It is separate from the CRS server so the two integration surfaces can change independently.

## Installation

```bash
uv sync --group dev
```

## Usage

### Stdio Mode

```bash
uv run synxis-pms-mcp
```

### HTTP Mode

```bash
uv run synxis-pms-mcp serve --http --port 3047
```

## Development

```bash
uv run pytest
uv run ruff check synxis_pms_mcp tests
uv run ruff format synxis_pms_mcp tests
```

## Project Structure

- `synxis_pms_mcp/`: MCP server package, clients, tools, and config helpers
- `tests/`: PMS workflow, property lookup, and provider error handling coverage
- `settings/`: environment-specific configuration defaults

## Security Notes

- Never commit credentials, tenant details, or customer data.
- Keep fixtures and examples sanitized before sharing them outside local development.

---
description: Check SynXis PMS property connectivity, credential/mock-mode state, and the available PMS tool surface.
argument-hint: "[--tools] [--query <capability>]"
allowed-tools: mcp__synxis-pms__health_check, mcp__synxis-pms__discover_tools
---

# /synxis-pms-property

Report the operational state of the configured SynXis PMS property connection before running guest, room, or stay workflows.

## Usage

`/synxis-pms-property [--tools] [--query <capability>]`

Arguments:

- `--tools`: optional flag. Also enumerate the registered PMS tool surface via `mcp__synxis-pms__discover_tools`.
- `--query <capability>`: optional. Free-text capability filter passed to `mcp__synxis-pms__discover_tools` (for example `folio` or `check`). Implies `--tools`.

## Workflow

1. Call `mcp__synxis-pms__health_check` to read server status, package version, whether SynXis credentials are configured, and whether the server is running in mock mode.
2. If `--tools` or `--query` was supplied, call `mcp__synxis-pms__discover_tools` (passing `query` when given) to list the tools registered at the active `SYNXIS_PMS_TOOL_PROFILE`.
3. Report a short readiness summary:
   - `configured: false` means `SYNXIS_PMS_CLIENT_ID` / `SYNXIS_PMS_CLIENT_SECRET` are unset — live PMS calls will fail.
   - `mock_mode: true` means responses are synthetic fixtures, not live property data.
4. Warn explicitly when the server is neither configured nor in mock mode, since guest and stay workflows will error.

## Example

`/synxis-pms-property --query folio`

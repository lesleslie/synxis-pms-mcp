# Tool Profile Adoption in synxis-pms-mcp (W4.8)

This document captures the rationale for adopting `apply_tool_profile()`
from `mcp-common` 0.18.0 in `synxis-pms-mcp`. It is the eighth of ten
Tier-A repos in the W4 wave; the first seven were `css-mcp`,
`excalidraw-mcp`, `neo4j-mcp`, `penpot-api-mcp`, `porkbun-dns-mcp`,
`porkbun-domain-mcp`, and `raindropio-mcp`.

## Tier-A trivial profile mapping

| Profile | Tools exposed |
|-----------|------------------------------------------------------------------------------------------------------------------------------|
| `MINIMAL` | `health_check` (MCP) + `discover_tools` (W0 meta). HTTP `/health` + `/healthz` routes always available. |
| `STANDARD` | All 5 `synxis-pms-mcp` tools + `health_check` + `discover_tools` (same as FULL — Tier-A trivial). |
| `FULL` | All 5 `synxis-pms-mcp` tools + `health_check` + `discover_tools`. Default behavior when no env var is set. |

The 5 PMS tools (Tier-A trivial — no "core subset" to drop at STANDARD):

1. `get_guest` (pms_tools group)
1. `get_room_status` (pms_tools group)
1. `check_in` (pms_tools group)
1. `check_out` (pms_tools group)
1. `get_folio` (pms_tools group)

## Why MINIMAL = health-only

`MINIMAL` exposes only the health probe because every PMS tool binds a
`SynXisPMSClient` instance that performs real HTTP calls to the SynXis
PMS API. Without configured credentials (`SYNXIS_PMS_CLIENT_ID` +
`SYNXIS_PMS_CLIENT_SECRET`) and a reachable PMS instance, every tool
call would fail. Operators running a control-plane health probe
(Kubernetes liveness, load-balancer ping) need ONLY the `health_check`
tool — the PMS-bound tools are dead weight and would fail anyway.

## Why `essential_tool_names={"health_check"}`

The W0 helper from `mcp-common` 0.18.0 performs a subset check after
registration: it asserts that every name in `essential_tool_names` is
present in the registered tool set. By passing
`essential_tool_names={"health_check"}`, we make the W4 spec invariant
fail loud if a future refactor accidentally drops `health_check` from
any profile (including the canonical `MINIMAL=health` mapping).

## Why the async dispatch helper, not the sync wrapper

The W0 helper exposes two entry points:

- `apply_tool_profile()` (sync) — calls `asyncio.run()` internally
- `_apply_tool_profile()` (async) — must be awaited

The sync wrapper raises `RuntimeError` when invoked from inside an
already-running event loop (any pytest-asyncio test, any async startup
path). The `synxis-pms-mcp` server now exposes an **async `create_app()`**
that `await`s the W0 helper directly, plus a `create_app_sync()` shim
that bridges via a private thread executor when no loop is running. The
keystone invariant is captured by
`test_profiles_uses_async_helper_not_sync_wrapper` and the AST guard
`test_server_awaits_apply_synxis_pms_tool_profile` (which would fail
if a future refactor dropped the `await`).

## Why caller-supplied settings + client must be threaded

The W0 dispatch lambdas bind the **caller's** `settings` and `client`
instances via default-arg capture. A naive implementation that called
`get_settings()` from inside the registration paths would silently
discard test-injected configuration (the W4.1 round-1 reviewer finding
in `css-mcp`). The `test_create_app_threads_caller_settings_through`
test monkey-patches `SynXisPMSSettings.__init__` to count
constructors; production path must call it exactly once.

The same `client` instance is captured by the lifespan `finally` block
via closure, so `await client.close()` actually closes the
httpx-backed client the registered tools use. The
`test_lifespan_actually_calls_client_close_on_shutdown` test monkey-
patches `SynXisPMSClient.close` and verifies it's called exactly once
when the lifespan exits (the W4.3 reviewer finding in `neo4j-mcp`).

## Why the backend-lambda adapter pattern

The pre-W4 `register_pms_tools(app, client)` takes 2 arguments. The W0
helper expects single-arg callables. We bridge via a wrapper
`register_pms_tools_for_profile(mcp, settings, client)` that takes
the uniform 3-arg signature every group fn uses (so the W0 dispatch
helper can iterate `_GROUP_REGISTRY` without a name conditional — the
W3.2 lesson). The dispatch lambdas in `profiles.py` then default-arg
capture the caller's `settings` and `client` and forward via the
wrapper.

The pre-W4 `register_pms_tools(app, client)` is preserved as a
backward-compat shim so any pre-W4 test/example still works.

## Files touched

- `pyproject.toml` — bump `mcp-common>=0.17.0` → `>=0.18.0`
- `synxis_pms_mcp/server.py` — async `create_app` + `create_app_sync`
  shim + `_run_async_safely` bridge; `_synxis_pms_client` attribute on
  the FastMCP instance (informational, same as pre-W4)
- `synxis_pms_mcp/tools/__init__.py` — add `register_health_tool`
  (MINIMAL group) + `register_pms_tools_for_profile` (FULL/STANDARD
  wrapper). `register_pms_tools` preserved as a backward-compat shim.
- `synxis_pms_mcp/tools/profiles.py` — NEW. `_GROUP_REGISTRY`,
  `PROFILE_REGISTRATIONS`, `_build_registration_map`,
  `register_all_tool_groups`, `apply_synxis_pms_tool_profile`.
- `tests/unit/test_tool_profile.py` — NEW. 32 tests covering all
  W4 keystones (W2b.3, W4.1, W4.3, structural, profile semantics).
- `docs/architecture/tool-profile-rationale.md` — this document.
- `CLAUDE.md` — add "Tool Profile System" subsection.

## Notes for the next W4 wave (fastblocks)

1. **Centralized `mcp_common.fastmcp` import is enforced** by a
   repo-local regression test (`test_no_direct_fastmcp_imports.py`).
   Always import `FastMCP` from `mcp_common.fastmcp`, not from
   `fastmcp` directly. Includes production files AND tests.

1. **`_lifespan_manager()` is the right entry point** to drive the
   production lifespan for the W4.3 close test. It mirrors what
   FastMCP itself uses in `LowLevelServer.run` and `http.py`.

1. **`_apply_tool_profile` AST guard** uses `ast.Await(value=ast.Call( func=ast.Name(id='apply_<repo>_tool_profile')))`. The keystone
   must NOT count occurrences — it must structurally confirm the
   `await` is present (the W3.2 round-1 lesson).

1. **The 3-arg `register_pms_tools_for_profile(mcp, settings, client)` wrapper pattern** works well for repos with 2-arg legacy
   register fns. The third arg can be `_ = settings` if unused
   (decorator-only purpose: uniform signature for `_GROUP_REGISTRY`
   iteration).

1. **`essential_tool_names={"health_check"}` requires a tool
   literally named `health_check`**, NOT `health_check_service` /
   `get_liveness` / etc. (the W0 names from `mcp_common.health`).
   Either define a local `health_check` tool (the W4.6 + W4.7 + W4.8
   pattern) or change the subset check.

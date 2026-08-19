"""Tests for the W4 ToolProfile dispatch in synxis-pms-mcp.

These tests cover the contract introduced by the W4 wave:

- Tier-A trivial mapping: ``MINIMAL=health``, ``STANDARD/FULL=all``.
- The W0 helper from mcp-common 0.18.0 dispatches by group name.
- Production path uses the async ``_apply_tool_profile`` (NOT the sync
  ``apply_tool_profile`` wrapper which raises in event loops).
- Caller-supplied ``settings`` + ``client`` are preserved through every
  registration path (no env re-load — the W4.1 round-1 reviewer fix).
- The lifespan ``finally`` block closes the SAME client the registered
  tools use (the W4.3 reviewer fix).
- ``essential_tool_names={"health_check"}`` is enforced at every profile.

Most of these tests do NOT mock the dispatch helper — they call
``create_app(...)`` end-to-end against a fresh ``FastMCP`` instance so
any regression in the production path is caught.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest
from mcp_common.fastmcp import FastMCP
from mcp_common.tools import ToolProfile
from mcp_common.tools.dispatch import ALL_TOOLS, InvalidProfileError

from synxis_pms_mcp import tools as tools_pkg
from synxis_pms_mcp.config import SynXisPMSSettings
from synxis_pms_mcp.server import create_app
from synxis_pms_mcp.tools.profiles import (
    _GROUP_REGISTRY,
    FULL_REGISTRATIONS,
    MINIMAL_REGISTRATIONS,
    PROFILE_REGISTRATIONS,
    _build_registration_map,
    apply_synxis_pms_tool_profile,
    register_all_tool_groups,
)

if TYPE_CHECKING:
    from synxis_pms_mcp.client import SynXisPMSClient


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


def _test_settings(**overrides: Any) -> SynXisPMSSettings:
    defaults: dict[str, Any] = {
        "client_id": "test-client",
        "client_secret": "test-secret",
    }
    defaults.update(overrides)
    return SynXisPMSSettings.model_validate(defaults)


def _fresh_server() -> FastMCP:
    """Fresh FastMCP with no lifespan — tests inspect registered tools only."""
    return FastMCP(name="test-server")


# ---------------------------------------------------------------------------
# Structural guards — files / dicts / constants exist
# ---------------------------------------------------------------------------


def test_profiles_py_exists() -> None:
    """``synxis_pms_mcp/tools/profiles.py`` must exist."""
    import synxis_pms_mcp.tools.profiles  # noqa: F401


def test_profiles_py_defines_profile_registrations() -> None:
    """``PROFILE_REGISTRATIONS`` covers all 3 profile tiers."""
    assert set(PROFILE_REGISTRATIONS.keys()) == {
        ToolProfile.MINIMAL,
        ToolProfile.STANDARD,
        ToolProfile.FULL,
    }


def test_profiles_py_defines_group_registry() -> None:
    """``_GROUP_REGISTRY`` is a list of (key, attr_name) tuples covering
    every register fn consumed by the dispatch."""
    expected = {
        ("health_tools", "register_health_tool"),
        ("pms_tools", "register_pms_tools_for_profile"),
    }
    assert set(_GROUP_REGISTRY) == expected


def test_profiles_py_defines_build_registration_map() -> None:
    """``_build_registration_map(settings, client)`` returns a dict."""
    settings = _test_settings()
    mapping = _build_registration_map(settings, client=object())  # type: ignore[arg-type]
    assert set(mapping.keys()) == {key for key, _ in _GROUP_REGISTRY}


def test_profiles_py_defines_register_all_tool_groups() -> None:
    """``register_all_tool_groups`` is exported and callable."""
    assert callable(register_all_tool_groups)


def test_profiles_py_defines_apply_synxis_pms_tool_profile() -> None:
    """``apply_synxis_pms_tool_profile`` is async (returns a coroutine fn)."""
    import asyncio

    assert callable(apply_synxis_pms_tool_profile)
    assert asyncio.iscoroutinefunction(apply_synxis_pms_tool_profile)


def test_profiles_py_references_correct_env_var() -> None:
    """The dispatch helper is called with ``SYNXIS_PMS_TOOL_PROFILE``."""
    import inspect

    source = inspect.getsource(apply_synxis_pms_tool_profile)
    assert "SYNXIS_PMS_TOOL_PROFILE" in source


def test_register_health_tool_exists_in_tools_package() -> None:
    """``register_health_tool`` is exposed at the tools package level."""
    assert hasattr(tools_pkg, "register_health_tool")
    assert callable(tools_pkg.register_health_tool)


def test_register_pms_tools_for_profile_exists_in_tools_package() -> None:
    """``register_pms_tools_for_profile`` is exposed at the tools package level."""
    assert hasattr(tools_pkg, "register_pms_tools_for_profile")
    assert callable(tools_pkg.register_pms_tools_for_profile)


def test_register_pms_tools_legacy_still_exported() -> None:
    """``register_pms_tools`` (2-arg) is preserved for backward-compat."""
    assert hasattr(tools_pkg, "register_pms_tools")
    assert callable(tools_pkg.register_pms_tools)


def test_pyproject_bumps_mcp_common_to_0_18() -> None:
    """``pyproject.toml`` pins ``mcp-common>=0.18.0``."""
    import tomllib
    from pathlib import Path

    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    data = tomllib.loads(pyproject_path.read_text())
    deps = data["project"]["dependencies"]
    pin = next((d for d in deps if d.startswith("mcp-common")), None)
    assert pin is not None, "mcp-common not listed in dependencies"
    assert ">=" in pin
    version = pin.split(">=", 1)[1].strip()
    major, minor = version.split(".")[:2]
    assert int(major) == 0
    assert int(minor) >= 18, f"mcp-common pin {pin!r} < 0.18.0"


# ---------------------------------------------------------------------------
# W2b.3 keystone — production path uses the ASYNC helper
# ---------------------------------------------------------------------------


def test_profiles_uses_async_helper_not_sync_wrapper() -> None:
    """``apply_synxis_pms_tool_profile`` calls ``_apply_tool_profile``,
    NOT ``apply_tool_profile`` (the sync wrapper raises in event loops)."""
    import inspect

    source = inspect.getsource(apply_synxis_pms_tool_profile)
    assert "_apply_tool_profile" in source, "must call async _apply_tool_profile"
    # The sync wrapper MUST NOT be referenced anywhere — it would raise
    # RuntimeError inside an event loop.
    assert "apply_tool_profile(" not in source.replace(
        "_apply_tool_profile(", ""
    ), "must not call sync apply_tool_profile"


def test_server_awaits_apply_synxis_pms_tool_profile() -> None:
    """AST guard: ``server.py`` MUST ``await apply_synxis_pms_tool_profile``.

    Structural check for ``ast.Await(value=ast.Call(func=ast.Name(
    id='apply_synxis_pms_tool_profile')))``. NOT just a count of calls
    (the W3.2 round-1 lesson — count-only guards produce false
    positives that silently break in event loops).
    """
    from pathlib import Path

    server_path = (
        Path(__file__).resolve().parents[2] / "synxis_pms_mcp" / "server.py"
    )
    tree = ast.parse(server_path.read_text())

    def _walk(node: ast.AST) -> bool:
        if isinstance(node, ast.Await) and isinstance(node.value, ast.Call):
            call = node.value
            func = call.func
            if (
                isinstance(func, ast.Name)
                and func.id == "apply_synxis_pms_tool_profile"
            ):
                return True
        for child in ast.iter_child_nodes(node):
            if _walk(child):
                return True
        return False

    assert _walk(tree), (
        "server.py must await apply_synxis_pms_tool_profile (the W2b.3 "
        "keystone — sync apply_tool_profile raises RuntimeError in "
        "event loops)."
    )


def test_server_does_not_call_sync_apply_tool_profile() -> None:
    """``server.py`` MUST NOT call the sync ``apply_tool_profile`` wrapper."""
    from pathlib import Path

    server_path = (
        Path(__file__).resolve().parents[2] / "synxis_pms_mcp" / "server.py"
    )
    source = server_path.read_text()
    # Strip the async helper call (which always contains the substring)
    # then ensure no OTHER call to apply_tool_profile exists.
    stripped = source.replace("_apply_tool_profile", "")
    assert "apply_tool_profile(" not in stripped, (
        "server.py must not call sync apply_tool_profile (use "
        "_apply_tool_profile via apply_synxis_pms_tool_profile)."
    )


def test_guard_fails_when_await_is_removed() -> None:
    """Regression: the AST guard must FAIL if ``await`` is removed.

    Build a synthetic module that calls ``apply_synxis_pms_tool_profile``
    WITHOUT ``await`` and confirm the guard returns False. This is the
    W3.2 round-1 lesson — count-based guards produced false positives.
    """
    source = """
async def bad():
    apply_synxis_pms_tool_profile(server, settings, client)
"""
    tree = ast.parse(source)

    def _walk(node: ast.AST) -> bool:
        if isinstance(node, ast.Await) and isinstance(node.value, ast.Call):
            call = node.value
            func = call.func
            if (
                isinstance(func, ast.Name)
                and func.id == "apply_synxis_pms_tool_profile"
            ):
                return True
        for child in ast.iter_child_nodes(node):
            if _walk(child):
                return True
        return False

    assert _walk(tree) is False, (
        "AST guard must NOT match a non-awaited call (false-positive "
        "regression — the W3.2 round-1 lesson)."
    )


# ---------------------------------------------------------------------------
# W4.1 keystone — MINIMAL=health, STANDARD/FULL=all
# ---------------------------------------------------------------------------


def test_minimal_registrations_contain_health_tools() -> None:
    """MINIMAL profile exposes ONLY the health group (the W4 spec)."""
    assert MINIMAL_REGISTRATIONS == ["health_tools"]


def test_full_registrations_lists_all_groups() -> None:
    """FULL profile enumerates every group in the registry."""
    assert FULL_REGISTRATIONS == [key for key, _ in _GROUP_REGISTRY]


def test_profile_registrations_minimal_maps_to_health_only() -> None:
    """MINIMAL key in ``PROFILE_REGISTRATIONS`` maps to a list containing
    only ``health_tools`` (NOT empty, NOT a miscount — the W4.1
    reviewer finding)."""
    minimal = PROFILE_REGISTRATIONS[ToolProfile.MINIMAL]
    assert minimal == ["health_tools"]


def test_profile_registrations_full_maps_to_all_tools() -> None:
    """FULL key maps to the ``ALL_TOOLS`` sentinel so the W0 helper
    invokes ``register_all_fn`` (the canonical bulk registration path)."""
    assert PROFILE_REGISTRATIONS[ToolProfile.FULL] is ALL_TOOLS


def test_profile_registrations_standard_maps_to_full_list() -> None:
    """STANDARD key maps to the same list as FULL_REGISTRATIONS
    (Tier-A trivial — no "core subset" to drop)."""
    assert PROFILE_REGISTRATIONS[ToolProfile.STANDARD] == FULL_REGISTRATIONS


# ---------------------------------------------------------------------------
# W4.1 keystone — caller-supplied settings + client are preserved
# ---------------------------------------------------------------------------


def test_caller_supplied_settings_are_preserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Monkey-patch ``SynXisPMSSettings.__init__`` so any env reload raises.
    Verifies that ``_build_registration_map`` does NOT silently re-load
    settings (the W4.1 round-1 reviewer finding)."""
    # Track whether __init__ is called — we want it called exactly once
    # (by the caller) and NEVER again from inside the registration paths.
    init_call_count = {"n": 0}

    original_init = SynXisPMSSettings.__init__

    def tracking_init(self: SynXisPMSSettings, *args: Any, **kwargs: Any) -> None:
        init_call_count["n"] += 1
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(SynXisPMSSettings, "__init__", tracking_init)
    settings = _test_settings()
    # Caller's init counted. Now build the registration map; if it
    # re-loads, ``tracking_init`` will fire again.
    _build_registration_map(settings, client=object())  # type: ignore[arg-type]
    assert init_call_count["n"] == 1, (
        f"_build_registration_map silently re-loaded settings "
        f"({init_call_count['n']} inits, expected exactly 1)."
    )


def test_register_all_tool_groups_does_not_reload_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``register_all_tool_groups`` does NOT reload settings."""
    init_call_count = {"n": 0}
    original_init = SynXisPMSSettings.__init__

    def tracking_init(self: SynXisPMSSettings, *args: Any, **kwargs: Any) -> None:
        init_call_count["n"] += 1
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(SynXisPMSSettings, "__init__", tracking_init)
    settings = _test_settings()
    register_all_tool_groups(_fresh_server(), settings, client=object())  # type: ignore[arg-type]
    assert init_call_count["n"] == 1


def test_create_app_threads_caller_settings_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end: ``create_app(settings)`` does NOT re-load settings."""
    init_call_count = {"n": 0}
    original_init = SynXisPMSSettings.__init__

    def tracking_init(self: SynXisPMSSettings, *args: Any, **kwargs: Any) -> None:
        init_call_count["n"] += 1
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(SynXisPMSSettings, "__init__", tracking_init)
    settings = _test_settings()

    import asyncio

    asyncio.run(create_app(settings=settings, server=_fresh_server()))
    assert init_call_count["n"] == 1, (
        "create_app silently re-loaded settings (W4.1 round-1 lesson)."
    )


# ---------------------------------------------------------------------------
# W4.3 keystone — lifespan closes the registered client
# ---------------------------------------------------------------------------


def test_lifespan_finally_calls_client_close() -> None:
    """AST guard: ``server.py`` MUST call ``await client.close()`` in the
    lifespan ``finally`` block. Structural check for
    ``ast.Await(value=ast.Call(func=ast.Attribute(attr='close',
    value=ast.Name(id='client'))))`` — NOT just a text search (the
    W4.3 reviewer lesson: false positives if you only count calls)."""
    from pathlib import Path

    server_path = (
        Path(__file__).resolve().parents[2] / "synxis_pms_mcp" / "server.py"
    )
    tree = ast.parse(server_path.read_text())

    def _walk(node: ast.AST) -> bool:
        if isinstance(node, ast.Await) and isinstance(node.value, ast.Call):
            call = node.value
            func = call.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "close"
                and isinstance(func.value, ast.Name)
                and func.value.id == "client"
            ):
                return True
        for child in ast.iter_child_nodes(node):
            if _walk(child):
                return True
        return False

    assert _walk(tree), (
        "server.py lifespan finally must call `await client.close()` "
        "(the W4.3 reviewer finding — long-running servers leak httpx "
        "pools if the close call is dropped or refers to a different "
        "instance)."
    )


@pytest.mark.asyncio
async def test_lifespan_actually_calls_client_close_on_shutdown() -> None:
    """End-to-end: drive the production lifespan and verify the close
    was invoked when the lifespan exits.

    Mirrors the W4.6 round-1 fix:
    1. Calls ``await create_app(settings)`` with no server injection,
       so the production lifespan IS attached.
    2. Drives the production lifespan start/exit cycle via
       ``server._lifespan_manager()`` — the same entry point
       FastMCP itself uses in ``LowLevelServer.run`` and ``http.py``.
    3. Asserts that ``SynXisPMSClient.close`` was called exactly
       once — by the production lifespan's ``finally`` block, not by
       the test itself.
    """
    settings = _test_settings()

    close_called = {"n": 0}
    from synxis_pms_mcp.client import SynXisPMSClient

    original_close = SynXisPMSClient.close

    async def tracking_close(self: SynXisPMSClient) -> None:
        close_called["n"] += 1
        await original_close(self)

    with patch.object(SynXisPMSClient, "close", tracking_close):
        # Production path: no server injection → the ``if server is None``
        # block in ``server.py`` attaches the production lifespan that
        # calls ``await client.close()`` in its ``finally``.
        result = await create_app(settings=settings)
        # Drive the production lifespan start/exit cycle via the same
        # entry point FastMCP itself uses.
        async with result._lifespan_manager():
            # Lifespan is now started; close will run when the
            # context manager exits below.
            pass

    assert close_called["n"] == 1, (
        f"Expected exactly 1 close call from the production lifespan, "
        f"got {close_called['n']} (the W4.3 reviewer finding — the "
        f"production lifespan's ``finally`` block must call "
        f"``await client.close()``)."
    )


# ---------------------------------------------------------------------------
# essential_tool_names subset check — W4.1 invariant
# ---------------------------------------------------------------------------


def test_essential_tool_names_subset_check_enforced() -> None:
    """Source-level: ``apply_synxis_pms_tool_profile`` passes
    ``essential_tool_names={"health_check"}`` to the W0 helper so a
    future refactor that drops ``health_check`` from a profile raises
    ``ValueError``."""
    import inspect

    source = inspect.getsource(apply_synxis_pms_tool_profile)
    assert 'essential_tool_names={"health_check"}' in source


# ---------------------------------------------------------------------------
# Profile semantics — real production path via fresh FastMCP
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_minimal_profile_registers_only_health_check() -> None:
    """MINIMAL profile exposes ``health_check`` + ``discover_tools`` ONLY.

    The W4 spec: no PMS tools at MINIMAL (they would fail without
    credentials / a reachable PMS instance). Strict equality on
    tool names — unreported extras fail loud.
    """
    settings = _test_settings()
    server = _fresh_server()
    with patch.dict("os.environ", {"SYNXIS_PMS_TOOL_PROFILE": "minimal"}):
        await apply_synxis_pms_tool_profile(
            server, settings, client=object()  # type: ignore[arg-type]
        )
    names = {tool.name for tool in await server.list_tools()}
    assert names == {"health_check", "discover_tools"}


@pytest.mark.asyncio
async def test_standard_profile_registers_all_groups() -> None:
    """STANDARD profile exposes every group (Tier-A trivial — same as FULL)."""
    settings = _test_settings()
    server = _fresh_server()
    with patch.dict("os.environ", {"SYNXIS_PMS_TOOL_PROFILE": "standard"}):
        await apply_synxis_pms_tool_profile(
            server, settings, client=object()  # type: ignore[arg-type]
        )
    names = {tool.name for tool in await server.list_tools()}
    expected = {
        # health
        "health_check",
        # pms
        "get_guest",
        "get_room_status",
        "check_in",
        "check_out",
        "get_folio",
        # W0 meta
        "discover_tools",
    }
    assert names == expected


@pytest.mark.asyncio
async def test_full_profile_registers_all_groups() -> None:
    """FULL profile exposes every group (the pre-W4 behavior)."""
    settings = _test_settings()
    server = _fresh_server()
    with patch.dict("os.environ", {"SYNXIS_PMS_TOOL_PROFILE": "full"}):
        await apply_synxis_pms_tool_profile(
            server, settings, client=object()  # type: ignore[arg-type]
        )
    names = {tool.name for tool in await server.list_tools()}
    expected = {
        "health_check",
        "get_guest",
        "get_room_status",
        "check_in",
        "check_out",
        "get_folio",
        "discover_tools",
    }
    assert names == expected


@pytest.mark.asyncio
async def test_create_app_full_profile_real_path() -> None:
    """End-to-end production-path test (no mocks of the dispatch helper).

    Calls ``await create_app(settings, fresh_server)`` and asserts strict
    equality on tool names — every PMS tool + ``health_check`` +
    ``discover_tools`` MUST be present.
    """
    settings = _test_settings()
    server = _fresh_server()
    with patch.dict("os.environ", {"SYNXIS_PMS_TOOL_PROFILE": "full"}):
        result = await create_app(settings=settings, server=server)
    names = {tool.name for tool in await result.list_tools()}
    expected = {
        "health_check",
        "get_guest",
        "get_room_status",
        "check_in",
        "check_out",
        "get_folio",
        "discover_tools",
    }
    assert names == expected


@pytest.mark.asyncio
async def test_create_app_minimal_profile_real_path() -> None:
    """End-to-end MINIMAL profile — health_check + discover_tools ONLY.

    Critical regression guard: a future refactor that drops
    ``health_check`` from the MINIMAL profile would silently degrade
    health probes for control-plane deployments.
    """
    settings = _test_settings()
    server = _fresh_server()
    with patch.dict("os.environ", {"SYNXIS_PMS_TOOL_PROFILE": "minimal"}):
        result = await create_app(settings=settings, server=server)
    names = {tool.name for tool in await result.list_tools()}
    assert names == {"health_check", "discover_tools"}


@pytest.mark.asyncio
async def test_create_app_invalid_profile_raises() -> None:
    """A SET-BUT-INVALID ``SYNXIS_PMS_TOOL_PROFILE`` raises
    ``InvalidProfileError`` (per the W0 spec — UNSET falls through to
    FULL, but a bogus value is loud)."""
    settings = _test_settings()
    server = _fresh_server()
    with patch.dict("os.environ", {"SYNXIS_PMS_TOOL_PROFILE": "bogus-value"}):
        with pytest.raises(InvalidProfileError):
            await apply_synxis_pms_tool_profile(
                server, settings, client=object()  # type: ignore[arg-type]
            )

"""MCP tools for SynXis PMS management.

Each ``register_<group>_tools()`` function attaches a group of MCP tools
to a ``FastMCP`` server. The pre-W4 entries take a pre-constructed
``SynXisPMSClient`` (the old sync ``create_app`` constructed the client
once and reused it). The W4 ``_for_profile`` wrappers and ``register_health_tool``
take ``(mcp, settings, client)`` so the W0 dispatch helper in mcp-common
0.18.0 can bind the caller's settings + client via lambda capture without
re-loading either from the environment.

The W4 split is load-bearing for two reasons:

1. **MINIMAL profile registration** — ``register_health_tool`` exposes
   only the MCP ``health_check`` tool. This MUST be independently
   callable so the W0 helper can register it without also registering the
   5 SynXisPMSClient-bound PMS tools (the W4.1 reviewer finding).
2. **Lifespan cleanup** — the ``SynXisPMSClient`` instance must be the
   SAME object captured by the lifespan finally block (the W4.3
   lesson: long-running servers leak httpx pools if the close call is
   dropped or refers to a different instance). Routing the client
   through every registration lambda keeps a single instance alive.
"""

from __future__ import annotations

from typing import Any

from mcp_common.fastmcp import FastMCP

from synxis_pms_mcp import __version__
from synxis_pms_mcp.client import SynXisPMSClient
from synxis_pms_mcp.config import SynXisPMSSettings
from synxis_pms_mcp.tools.pms_tools import register_pms_tools


def register_health_tool(
    mcp: FastMCP,
    settings: SynXisPMSSettings,
    client: SynXisPMSClient | None = None,
) -> None:
    """Register only the MCP ``health_check`` tool.

    Split out from the pre-W4 monolithic registration so the W0 tool
    profile dispatch can expose ``health_check`` independently at the
    MINIMAL profile (the canonical W4.1 mapping: ``MINIMAL=health``).

    The HTTP ``/health`` route is registered separately via
    ``register_http_health_route`` in ``server.py`` (always-on, not
    gated by profile).

    The third ``client`` argument is accepted (but unused) to give
    every group fn a uniform ``(mcp, settings, client)`` signature so
    the W0 dispatch helper can iterate ``_GROUP_REGISTRY`` without a
    name conditional (the W3.2 lesson).

    Args:
        mcp: FastMCP server instance.
        settings: Server configuration (used to report mock-mode + credentials
            status in the ``health_check`` response body).
        client: Ignored — present only for signature uniformity with
            the other group registration fns.
    """

    @mcp.tool()
    async def health_check() -> dict[str, Any]:
        """Check server health status.

        Returns:
            Health status information including version, server name,
            and configured state (whether SYNXIS_PMS_CLIENT_ID and
            SYNXIS_PMS_CLIENT_SECRET are set).
        """
        return {
            "status": "healthy",
            "name": "synxis-pms-mcp",
            "version": __version__,
            "configured": settings.has_credentials(),
            "mock_mode": settings.mock_mode,
        }


# ---------------------------------------------------------------------------
# Profile-friendly wrapper — takes (mcp, settings, client).
# The W0 dispatch helper from mcp-common 0.18.0 expects single-arg
# callables; this wrapper is invoked via a lambda that default-arg
# captures the caller-supplied settings + client.
# ---------------------------------------------------------------------------


def register_pms_tools_for_profile(
    mcp: FastMCP, settings: SynXisPMSSettings, client: SynXisPMSClient
) -> None:
    """Profile-dispatch entry for the pms_tools group.

    Forwards to the legacy ``register_pms_tools`` (which takes a
    pre-constructed ``SynXisPMSClient``). This is the W3.1 backend-lambda
    adapter pattern: the W0 helper expects a single-arg callable, so
    the dispatch lambdas in ``profiles.py`` wrap this 3-arg fn.

    The third ``settings`` argument is accepted (but unused) to give
    every group fn a uniform ``(mcp, settings, client)`` signature so
    the W0 dispatch helper can iterate ``_GROUP_REGISTRY`` without a
    name conditional (the W3.2 lesson).
    """
    _ = settings  # signature uniformity; legacy fn only uses (mcp, client)
    register_pms_tools(mcp, client)


# ---------------------------------------------------------------------------
# Backward-compat shim — pre-W4 callers (tests, examples) still call
# ``register_pms_tools(app, client)`` directly. Kept so this shim does
# not break callers that don't go through the dispatch helper.
# ---------------------------------------------------------------------------

__all__ = [
    "register_pms_tools",
    "register_pms_tools_for_profile",
    "register_health_tool",
]

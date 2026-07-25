"""FastMCP server for SynXis PMS management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from mcp_common.fastmcp import FastMCP
from mcp_common.health import register_http_health_route

from synxis_pms_mcp import __version__
from synxis_pms_mcp.client import SynXisPMSClient
from synxis_pms_mcp.config import get_logger_instance, get_settings, setup_logging
from synxis_pms_mcp.tools import register_pms_tools

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = get_logger_instance("synxis-pms-mcp.server")

APP_NAME = "synxis-pms-mcp"
APP_VERSION = __version__


def create_app() -> FastMCP:
    settings = get_settings()
    setup_logging(settings)

    logger.info(
        "Initializing SynXis PMS MCP server",
        version=APP_VERSION,
        mock_mode=settings.mock_mode,
    )

    client = SynXisPMSClient(settings)

    @asynccontextmanager
    async def app_lifespan(_server: FastMCP) -> AsyncGenerator[None]:
        """Open/close the SynXis PMS HTTP client around the server's lifetime.

        Plan 7 (FastMCP 3.x) makes ``lifespan=`` a public kwarg on
        ``FastMCP(...)``. The previous implementation read
        ``app._mcp_server.lifespan`` (a private attribute) and reassigned
        it post-construction; FastMCP 3.x silently drops that mutation
        in some code paths, so we declare the lifespan declaratively.
        """
        try:
            yield
        finally:
            await client.close()

    app = FastMCP(name=APP_NAME, version=APP_VERSION, lifespan=app_lifespan)

    # HTTP health endpoint for Claude Code compatibility
    register_http_health_route(
        app,
        service_name="synxis-pms",
        version=APP_VERSION,
    )

    @app.custom_route("/healthz", methods=["GET"])
    async def healthz_check(request: Any) -> Any:
        """Kubernetes-style health check endpoint."""
        from starlette.responses import JSONResponse

        return JSONResponse({"status": "ok"})

    register_pms_tools(app, client)

    return app


_app: FastMCP | None = None


def get_app() -> FastMCP:
    global _app
    if _app is None:
        _app = create_app()
    return _app


def __getattr__(name: str) -> Any:
    if name == "app":
        return get_app()
    if name == "http_app":
        return get_app().http_app
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = ["create_app", "get_app", "APP_NAME", "APP_VERSION"]

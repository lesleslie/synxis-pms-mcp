"""FastMCP server for SynXis PMS management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from fastmcp import FastMCP

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

    app = FastMCP(name=APP_NAME, version=APP_VERSION)
    client = SynXisPMSClient(settings)
    register_pms_tools(app, client)

    original_lifespan = app._mcp_server.lifespan

    @asynccontextmanager
    async def lifespan(server: Any) -> AsyncGenerator[dict[str, Any]]:
        async with original_lifespan(server) as state:
            try:
                yield state
            finally:
                await client.close()

    app._mcp_server.lifespan = lifespan
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

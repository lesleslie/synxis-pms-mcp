"""Unified CLI for SynXis PMS MCP server using mcp-common.

Provides standard lifecycle commands (start, stop, restart, status, health).
"""

from __future__ import annotations

import os
import warnings

os.environ["TRANSFORMERS_VERBOSITY"] = "error"
warnings.filterwarnings("ignore", message=".*PyTorch.*TensorFlow.*Flax.*")

import uvicorn

from mcp_common import MCPServerCLIFactory, MCPServerSettings
from mcp_common.cli.health import RuntimeHealthSnapshot

from synxis_pms_mcp import __version__


class SynXisPMSSettings(MCPServerSettings):
    """SynXis PMS MCP server settings extending MCPServerSettings."""

    server_name: str = "synxis-pms-mcp"
    http_port: int = 3047
    startup_timeout: int = 10
    shutdown_timeout: int = 10
    force_kill_timeout: int = 5


def start_server_handler() -> None:
    """Start handler that launches the SynXis PMS MCP server in HTTP mode."""
    settings = SynXisPMSSettings()
    print(f"Starting SynXis PMS MCP server on port {settings.http_port}...")
    uvicorn.run(
        "synxis_pms_mcp.server:http_app",
        host="127.0.0.1",
        port=settings.http_port,
        log_level="info",
    )


def health_probe_handler() -> RuntimeHealthSnapshot:
    """Health probe handler for SynXis PMS MCP server."""
    from synxis_pms_mcp.config import get_settings

    settings = get_settings()
    return RuntimeHealthSnapshot(
        server_name="synxis-pms-mcp",
        status="healthy",
        version=__version__,
        extra={
            "credentials_configured": settings.has_credentials(),
            "mock_mode": settings.mock_mode,
        },
    )


factory = MCPServerCLIFactory(
    server_name="synxis-pms-mcp",
    settings=SynXisPMSSettings(),
    start_handler=start_server_handler,
    health_probe_handler=health_probe_handler,
)

app = factory.create_app()


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()

"""SynXis PMS MCP - MCP server for SynXis Property Management System."""

from synxis_pms_mcp.client import SynXisPMSClient
from synxis_pms_mcp.config import SynXisPMSSettings, get_settings, setup_logging
from synxis_pms_mcp.models import (
    CheckInResult,
    CheckOutResult,
    Folio,
    Guest,
    Room,
    SynXisPMSError,
)

__version__ = "0.1.1"

__all__ = [
    "SynXisPMSClient",
    "SynXisPMSSettings",
    "get_settings",
    "setup_logging",
    "CheckInResult",
    "CheckOutResult",
    "Folio",
    "Guest",
    "Room",
    "SynXisPMSError",
    "__version__",
]

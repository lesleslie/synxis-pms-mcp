"""SynXis PMS MCP - MCP server for SynXis Property Management System."""

from importlib.metadata import version as _importlib_version

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

__version__ = _importlib_version("synxis-pms-mcp")

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

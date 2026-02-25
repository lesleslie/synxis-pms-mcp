"""Configuration for SynXis PMS MCP server."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import httpx
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    from oneiric.core.logging import LoggingConfig, configure_logging, get_logger

    ONEIRIC_LOGGING_AVAILABLE = True
except ImportError:
    ONEIRIC_LOGGING_AVAILABLE = False
    import logging

    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(name)

    def configure_logging(*args: Any, **kwargs: Any) -> None:
        logging.basicConfig(level=logging.INFO)


class SynXisPMSSettings(BaseSettings):
    """Settings for SynXis PMS MCP server."""

    model_config = SettingsConfigDict(
        env_prefix="SYNXIS_PMS_",
        env_file=(".env",),
        extra="ignore",
        case_sensitive=False,
    )

    # OAuth2 credentials
    client_id: str = Field(default="", description="SynXis OAuth2 client ID")
    client_secret: str = Field(default="", description="SynXis OAuth2 client secret")

    # API configuration
    base_url: str = Field(
        default="https://api.synxis.com/pms/v1",
        description="SynXis PMS API base URL",
    )
    property_id: str = Field(default="", description="Property ID")
    timeout: float = Field(default=30.0, ge=1.0, le=120.0)
    max_retries: int = Field(default=3, ge=0, le=5)

    # Mock mode
    mock_mode: bool = Field(default=False, description="Use mock data")

    # HTTP transport
    enable_http_transport: bool = Field(default=False)
    http_host: str = Field(default="127.0.0.1")
    http_port: int = Field(default=3047, ge=1, le=65535)

    # Logging
    log_level: str = Field(default="INFO")
    log_json: bool = Field(default=True)

    @field_validator("base_url", mode="after")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        return v.rstrip("/") if v else "https://api.synxis.com/pms/v1"

    def has_credentials(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def get_masked_client_id(self) -> str:
        if not self.client_id:
            return "***"
        return f"...{self.client_id[-4:]}" if len(self.client_id) > 4 else "***"

    def http_client_config(self) -> dict[str, Any]:
        return {
            "base_url": self.base_url,
            "timeout": httpx.Timeout(self.timeout),
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "synxis-pms-mcp/0.1.1",
            },
        }


def setup_logging(settings: SynXisPMSSettings | None = None) -> None:
    if settings is None:
        settings = get_settings()

    if ONEIRIC_LOGGING_AVAILABLE:
        config = LoggingConfig(
            level=settings.log_level,
            emit_json=settings.log_json,
            service_name="synxis-pms-mcp",
        )
        configure_logging(config)
    else:
        logging.basicConfig(
            level=getattr(logging, settings.log_level.upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )


@lru_cache
def get_settings() -> SynXisPMSSettings:
    return SynXisPMSSettings()


def get_logger_instance(name: str = "synxis-pms-mcp") -> Any:
    if ONEIRIC_LOGGING_AVAILABLE:
        return get_logger(name)
    return logging.getLogger(name)


__all__ = [
    "SynXisPMSSettings",
    "get_settings",
    "setup_logging",
    "get_logger_instance",
]

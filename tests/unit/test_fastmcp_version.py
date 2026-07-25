"""Regression tests for the FastMCP 3.4 migration (Plan 7 Phase 5).

These tests pin two contracts that the migration must satisfy:

1. ``fastmcp`` must resolve to a version >= 3.4 at runtime.
2. ``mcp_common.fastmcp`` must be importable and re-export ``FastMCP``,
   because every consumer in this repo imports ``FastMCP`` from
   ``mcp_common.fastmcp`` (the centralized re-export surface).

They are intentionally trivial. Their purpose is to fail CI if a
downstream patch downgrades ``fastmcp`` below 3.4 or if someone removes
the ``mcp_common.fastmcp`` re-export shim.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import fastmcp
import pytest

if TYPE_CHECKING:
    pass


@pytest.mark.unit
def test_fastmcp_version_meets_3_4_floor() -> None:
    """fastmcp.__version__ must parse to >= 3.4."""
    from packaging.version import Version

    assert Version(fastmcp.__version__) >= Version("3.4"), (
        f"fastmcp.__version__={fastmcp.__version__!r} is below the 3.4 floor "
        "required by Plan 7 Phase 5."
    )


@pytest.mark.unit
def test_mcp_common_fastmcp_submodule_importable() -> None:
    """mcp_common.fastmcp submodule must exist and be importable.

    The submodule ships in mcp-common 0.17.0+. Pinning mcp-common below
    0.17.0 will surface as this import failing.
    """
    try:
        from mcp_common.fastmcp import FastMCP  # noqa: F401
    except ImportError as exc:
        pytest.fail(
            "mcp_common.fastmcp is not importable; mcp-common must be >= 0.17.0 "
            f"(got: {exc!r})"
        )


@pytest.mark.unit
def test_mcp_common_fastmcp_exposes_fmcp_class() -> None:
    """The re-exported FastMCP must be the actual FastMCP class."""
    from mcp_common.fastmcp import FastMCP as ReexportedFastMCP

    assert ReexportedFastMCP is fastmcp.FastMCP, (
        "mcp_common.fastmcp.FastMCP must re-export fastmcp.FastMCP; "
        f"got id mismatch ({id(ReexportedFastMCP)} vs {id(fastmcp.FastMCP)})."
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "symbol",
    ["FastMCP", "Context", "Middleware", "MiddlewareContext"],
)
def test_mcp_common_fastmcp_reexports_core_symbols(symbol: str) -> None:
    """mcp_common.fastmcp must re-export the core FastMCP symbols consumers use."""
    import mcp_common.fastmcp as mcf

    assert hasattr(mcf, symbol), (
        f"mcp_common.fastmcp.{symbol} is missing; the re-export surface "
        "should expose FastMCP, Context, Middleware, MiddlewareContext."
    )

"""Regression test: production code must import FastMCP via mcp_common.fastmcp.

Plan 7 centralized the FastMCP import surface at ``mcp_common.fastmcp`` so
that version pinning and re-export changes happen in one place (mcp-common).
Direct ``from fastmcp import ...`` imports in consumer code defeat that
centralization. This test greps the production source tree to catch any
regression.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PRODUCTION_ROOTS: tuple[str, ...] = ("synxis_pms_mcp",)

# Pattern matches: ``from fastmcp import ...`` and ``import fastmcp``
# (allowing leading whitespace and indentation, but not comments).
DIRECT_FASTMCP_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+fastmcp\s+import\s+|import\s+fastmcp(?:\s|$|\.))",
    re.MULTILINE,
)


def _production_python_files() -> list[Path]:
    repo_root = Path(__file__).resolve().parent.parent.parent
    files: list[Path] = []
    for root_name in PRODUCTION_ROOTS:
        root = repo_root / root_name
        if not root.exists():
            continue
        files.extend(p for p in root.rglob("*.py") if p.is_file())
    return sorted(files)


@pytest.mark.unit
@pytest.mark.parametrize("path", _production_python_files(), ids=str)
def test_production_files_use_centralized_fastmcp_import(path: Path) -> None:
    """Every production .py file must import FastMCP via mcp_common.fastmcp.

    Allowed: ``from mcp_common.fastmcp import ...``
    Disallowed: ``from fastmcp import ...`` or ``import fastmcp``
    """
    text = path.read_text(encoding="utf-8")
    bad = DIRECT_FASTMCP_IMPORT_RE.findall(text)
    assert not bad, (
        f"{path} imports fastmcp directly; "
        "use `from mcp_common.fastmcp import ...` instead. "
        f"Found: {bad!r}"
    )

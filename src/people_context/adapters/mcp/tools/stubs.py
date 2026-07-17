"""Typed stubs for M3 lifecycle and import tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.types import ToolAnnotations

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

_WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False)
_DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True)


def _pending(milestone: str) -> dict[str, Any]:
    return {"status": "not_implemented", "planned_milestone": milestone}


def register(mcp: FastMCP) -> None:
    """Register M3 stubs with their committed signatures and annotations."""

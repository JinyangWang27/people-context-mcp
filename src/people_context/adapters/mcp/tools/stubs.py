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

    @mcp.tool(annotations=_WRITE)
    def import_content(source_type: str, content: str | None = None, path: str | None = None) -> dict[str, Any]:
        """Extract candidates from content into staging without storing raw content."""
        return _pending("M3")

    @mcp.tool(annotations=_WRITE)
    def review_import(batch_id: str) -> dict[str, Any]:
        """Return staged candidates for user review."""
        return _pending("M3")

    @mcp.tool(annotations=_WRITE)
    def commit_import(batch_id: str, accepted_ids: list[str]) -> dict[str, Any]:
        """Write accepted staged candidates with import provenance."""
        return _pending("M3")

    @mcp.tool(annotations=_WRITE)
    def export_data() -> dict[str, Any]:
        """Export the full dataset as a maximal-disclosure JSON document."""
        return _pending("M3")

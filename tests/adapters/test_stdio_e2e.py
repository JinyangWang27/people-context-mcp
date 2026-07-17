"""End-to-end proof through a real MCP stdio subprocess and the CLI."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from people_context.adapters.sqlite import open_db


def test_real_stdio_remember_resolve_with_hints_context_then_cli_show(tmp_path: Path) -> None:
    uv = shutil.which("uv")
    assert uv is not None
    project_root = Path(__file__).parents[2]
    db_path = tmp_path / "people.db"
    parameters = StdioServerParameters(
        command=uv,
        args=["run", "people-context-mcp", "--db", str(db_path)],
        cwd=project_root,
    )

    async def flow() -> tuple[str, dict[str, Any], dict[str, Any]]:
        async with (
            stdio_client(parameters) as (read_stream, write_stream),
            ClientSession(read_stream, write_stream) as client,
        ):
            await client.initialize()
            tools = await client.list_tools()
            assert {"remember_person", "resolve_person", "get_person_context"} <= {tool.name for tool in tools.tools}

            remembered = await client.call_tool(
                "remember_person",
                {"name": "Alice Example", "aliases": [{"value": "Ally"}], "summary": "Colleague"},
            )
            person_id = remembered.structuredContent["person"]["id"]
            _seed_context(db_path, person_id)

            resolved = await client.call_tool(
                "resolve_person",
                {"query": "Alice Example", "hints": {"org": "Acme"}},
            )
            context = await client.call_tool(
                "get_person_context",
                {"person_id": person_id, "max_items": 1},
            )
            return person_id, resolved.structuredContent, context.structuredContent

    person_id, resolved, context = anyio.run(flow)

    assert resolved["candidates"][0]["person_id"] == person_id
    assert resolved["candidates"][0]["match_reason"] == "exact+hint:org"
    assert context["affiliations"][0]["organization_name"] == "Acme Corp"
    assert context["facts"][0]["value"] == "Dubai"
    assert context["reminders"][0]["text"] == "Prefer written updates"

    shown = subprocess.run(
        [uv, "run", "people-context", "--db", str(db_path), "show", person_id],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert shown.returncode == 0, shown.stderr
    assert "Alice Example" in shown.stdout
    assert "Engineer at Acme Corp" in shown.stdout
    assert "location: Dubai" in shown.stdout
    assert "Prefer written updates" in shown.stdout


def _seed_context(db_path: Path, person_id: str) -> None:
    conn = open_db(db_path)
    try:
        with conn:
            conn.execute("INSERT INTO organizations (id, name, kind) VALUES ('org-1', 'Acme Corp', 'company')")
            conn.execute(
                """
                INSERT INTO affiliations (
                    id, person_id, org_id, role, confidence, provenance_source, created_at
                ) VALUES ('aff-1', ?, 'org-1', 'Engineer', 1.0, 'test', '2025-01-01T00:00:00+00:00')
                """,
                (person_id,),
            )
            conn.execute(
                """
                INSERT INTO facts (
                    id, person_id, predicate, value, recorded_at, confidence, sensitivity, provenance_source
                ) VALUES (
                    'fact-1', ?, 'location', 'Dubai', '2025-01-02T00:00:00+00:00', 1.0, 'public', 'test'
                )
                """,
                (person_id,),
            )
            conn.execute(
                """
                INSERT INTO reminders (
                    id, person_id, text, kind, status, created_at
                ) VALUES (
                    'reminder-1', ?, 'Prefer written updates', 'communication_note', 'active',
                    '2025-01-03T00:00:00+00:00'
                )
                """,
                (person_id,),
            )
    finally:
        conn.close()

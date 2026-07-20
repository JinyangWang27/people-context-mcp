from pathlib import Path


def replace_exact(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one match in {path}, found {count}: {old[:120]!r}")
    file_path.write_text(text.replace(old, new), encoding="utf-8")


PLAN = "docs/specs/pr-plan.md"

replace_exact(
    PLAN,
    '''- [ ] **PR M14.1 — CLI person brief + `list --json`**
  - **Scope:** Add `app/compose_person_brief.py` composing `GetPersonContext` + `GetCommunicationGuidance` + `ListReminders` into one deterministic markdown/JSON brief, and the `people-context brief PERSON` CLI command. Also add `--json` to the existing `list` command (needed as the Obsidian plugin's future person index). Does not touch `export-vcard`, importers, or the plugin.
  - **Touches:**
    - `src/people_context/app/compose_person_brief.py` (new)
    - `src/people_context/cli.py` (`brief` subcommand, `list --json`)
    - `tests/app/test_compose_person_brief.py` (new), `tests/adapters/test_cli*.py` or equivalent CLI test module
  - **Spec:** (docs/specs/m14-ecosystem-interop.md §"`people-context brief`")
    - `ListReminders`' person filter is required, not optional — it's the only way to surface `follow_up`/`occasion` reminders, since context/guidance include only `communication_note` ones.
    - Sensitivity mirrors vault export exactly: elevated material needs explicit `--include-sensitive`; footer states the text is outside server disclosure controls.
    - Output: stdout by default (markdown), `--json` for the stable machine form, or `--output FILE` written with the `0o600` convention (see `cli.py`'s existing `os.open(..., 0o600)` pattern).
    - No MCP tool — CLI-only, per the non-goals list (keeps bulk-disclosure formatting human-operated).
  - **Tests/validation:** `uv run ruff check .` clean, `uv run pytest -q` fully green. Fake-port tests for `ComposePersonBrief` covering composition, sensitivity gating, deterministic ordering, and all open-reminder kinds. CLI snapshot test for `brief` including the `--include-sensitive` diff and `0o600` file-mode check. `list --json` shape test.
  - **Out of scope:** brief style templates (open question 2, deferred); `export-vcard`; any MCP-facing change.
''',
    '''- [ ] **PR M14.1 — CLI person brief + `list --json`**
  - **Scope:** Add `app/compose_person_brief.py` composing `GetPersonContext` + `GetCommunicationGuidance` + `ListReminders` into one deterministic markdown/JSON brief, and the `people-context brief PERSON` CLI command. Also add `--json` to the existing `list` command (needed as the Obsidian plugin's future person index). Does not touch `export-vcard`, importers, or the plugin.
  - **Touches:**
    - `src/people_context/app/compose_person_brief.py` (new)
    - `src/people_context/cli.py` (`brief` subcommand, `list --json`)
    - `tests/app/test_compose_person_brief.py` (new), `tests/adapters/test_cli*.py` or equivalent CLI test module
  - **Spec:** (docs/specs/m14-ecosystem-interop.md §"`people-context brief`")
    - `ListReminders`' person filter is required, not optional — it is the only way to surface `follow_up`/`occasion` reminders, since context/guidance include only `communication_note` ones.
    - Call `GetPersonContext.execute(..., purpose="communication", include_sensitive=flag)` so `--include-sensitive` widens context-backed facts, interactions, and communication traits. `GetCommunicationGuidance` remains ordinary-only by its existing contract; M14.1 must not silently widen that use case or expose a new MCP parameter.
    - The footer states that exported text is outside server disclosure controls and explicitly labels guidance as ordinary-disclosure even when sensitive context is included.
    - Output: stdout by default (markdown), `--json` for the stable machine form, or `--output FILE` written with the `0o600` convention (see `cli.py`'s existing `os.open(..., 0o600)` pattern).
    - No MCP tool — CLI-only, per the non-goals list (keeps bulk-disclosure formatting human-operated).
  - **Tests/validation:** `uv run ruff check .` clean, `uv run pytest -q` fully green. Fake-port tests cover composition, deterministic ordering, all open-reminder kinds, sensitive context appearing only with the flag, and unchanged ordinary-only guidance in both modes. CLI snapshots cover the `--include-sensitive` diff, disclosure labeling, and `0o600`; add a `list --json` shape test.
  - **Out of scope:** changing `GetCommunicationGuidance` or its MCP tool contract; brief style templates; `export-vcard`; any new MCP-facing surface.
''',
)

replace_exact(
    PLAN,
    '''- [ ] **PR M14.2 — `export-vcard` deterministic writer**
  - **Scope:** New `adapters/filesystem/vcard_writer.py` mirroring `vault_writer.py`'s determinism rules, plus the `people-context export-vcard` CLI command. It emits the subset the existing vCard importer can round-trip without changing that importer.
  - **Touches:**
    - `src/people_context/adapters/filesystem/vcard_writer.py` (new)
    - `src/people_context/app/export_vcard.py` (new, thin use case parallel to `app/export_vault.py`)
    - `src/people_context/cli.py` (`export-vcard` subcommand)
    - `tests/adapters/test_vcard_export.py` (new)
  - **Spec:** (docs/specs/m14-ecosystem-interop.md §"`people-context export-vcard`")
    - Stable person/property ordering; byte-identical re-export over unchanged data (same guarantee as `docs/vault-export.md`).
    - Field mapping: `FN`/`N` ← canonical name, `NICKNAME` ← `nickname` aliases, `EMAIL` ← `handle` aliases parsing as addresses, `BDAY` ← `predicate="birthday"` facts.
    - Because the existing importer consumes only the first `ORG`/`TITLE` pair, export at most one active affiliation per person, selected deterministically by normalized organization name, normalized role, then affiliation id. Report additional active affiliations as `omitted_affiliations`; do not silently imply complete affiliation portability.
    - `--version {3.0,4.0}` dialect flag; every emitted field must round-trip through the existing `VCardImportExtractor`.
    - Elevated-sensitivity facts follow the same `--include-sensitive` gate as vault export and `brief`.
  - **Tests/validation:** `uv run ruff check .` clean, `uv run pytest -q` fully green. `test_vcard_export.py`: determinism, sensitivity gating, deterministic affiliation selection and omission count, and a full round trip asserting people/aliases/the selected affiliation/birthday facts survive. CLI `0o600` and determinism checks.
  - **Out of scope:** CardDAV; Outlook/WhatsApp import; multiple-affiliation vCard encoding; any change to the importer side of vCard.
''',
    '''- [ ] **PR M14.2 — `export-vcard` deterministic writer**
  - **Scope:** Add `ExportVCard(ExportReader, VCardWriter, Clock)`, a narrow writer port, its deterministic filesystem adapter, and the `people-context export-vcard` CLI command. The app layer builds the disclosure-gated projection; the adapter only serializes it. Emit only the subset the existing vCard importer can round-trip.
  - **Touches:**
    - `src/people_context/ports/vcard.py` (new — typed export DTOs plus `VCardWriter` Protocol)
    - `src/people_context/app/export_vcard.py` (new — depends only on `ExportReader`, `VCardWriter`, and `Clock`)
    - `src/people_context/adapters/filesystem/vcard_writer.py` (new — pure deterministic serialization)
    - `src/people_context/cli.py` (`export-vcard` subcommand and result summary)
    - app fake-port tests plus `tests/adapters/test_vcard_export.py` and CLI tests
  - **Spec:** (docs/specs/m14-ecosystem-interop.md §"`people-context export-vcard`")
    - The app use case excludes soft-deleted people, applies the sensitivity gate, evaluates active records at `clock.now().date()`, and never imports an adapter. The writer receives an already-filtered typed projection.
    - Stable person/property ordering yields byte-identical output for the same snapshot and injected clock.
    - Field mapping: `FN`/`N` ← canonical name, `NICKNAME` ← `nickname` aliases, `EMAIL` ← `handle` aliases parsing as addresses.
    - Export at most one active affiliation per person, selected by normalized organization name, normalized role, then affiliation id; count the rest in `omitted_affiliations`.
    - Export at most one eligible `birthday` fact per person because the importer consumes only the first `BDAY`: select highest confidence, then newest `recorded_at`, then id; count the rest in `omitted_birthdays`.
    - `--version {3.0,4.0}` selects the dialect; every emitted field must round-trip through the existing `VCardImportExtractor`.
  - **Tests/validation:** Fake reader/writer/clock tests pin filtering, as-of behavior, both omission policies, and no adapter dependency. Adapter tests cover byte determinism and 3.0/4.0 serialization. Full importer round trip asserts people, aliases, selected affiliation, and selected birthday survive; CLI tests cover `0o600`, both omission counts, and sensitivity gating. `uv run ruff check .` and `uv run pytest -q` fully green.
  - **Out of scope:** CardDAV; Outlook/WhatsApp import; multiple-affiliation or multiple-birthday vCard encoding; any change to the importer side of vCard.
''',
)

replace_exact(
    PLAN,
    '''  - **Scope:** CLI-only `people-context stats` report over existing reads plus small adapter count queries (no new port needed if existing readers suffice; otherwise a minimal additive method). Does not touch `doctor` or resolution.
  - **Touches:**
    - `src/people_context/app/compute_stats.py` (new, or a method alongside `run_doctor.py` if a shared adapter query module emerges — keep app-layer policy separate from `run_doctor`)
    - `src/people_context/adapters/sqlite/*.py` (small additive count queries only, e.g. in `repository.py`/`context_reader.py` — no schema change)
    - `src/people_context/cli.py` (`stats` subcommand)
    - `tests/app/test_compute_stats.py`, extend CLI test module
''',
    '''  - **Scope:** Add a narrow aggregate-only `StatsReader` port, its SQLite adapter, `ComputeStats`, and the CLI-only `people-context stats` report. Keep SQL aggregation in the adapter and formatting/redaction policy in the app/CLI; do not scatter count methods across unrelated repositories.
  - **Touches:**
    - `src/people_context/ports/stats.py` (new — aggregate DTO plus `StatsReader` Protocol)
    - `src/people_context/adapters/sqlite/stats_reader.py` (new — counts/distributions/database-size query set)
    - `src/people_context/app/compute_stats.py` (new — report policy and path redaction)
    - `src/people_context/cli.py` (`stats` subcommand; reads process gate env vars and passes explicit booleans to the use case)
    - `tests/app/test_compute_stats.py`, `tests/adapters/test_sqlite_stats_reader.py`, and CLI tests
''',
)
replace_exact(
    PLAN,
    '''    - Disclosure-gate section reads only the local process environment (`PEOPLE_CONTEXT_MCP_ENABLE_SENSITIVE`, `PEOPLE_CONTEXT_MCP_ENABLE_EXPORT` — see `adapters/mcp/tools/people.py`/`portability.py`) — must not probe or start the server; report as "in this environment".
    - Absolute database path is **redacted by default**; `--include-path` opts in explicitly.
    - `--json` mirrors the human output; never emits record contents, only aggregates/counts.
  - **Tests/validation:** `uv run ruff check .` clean, `uv run pytest -q` fully green. Fake-port tests for the stats computation. CLI snapshot test over a seeded fixture including `--json` shape stability and the default-redacted-path / `--include-path` behavior.
''',
    '''    - `SqliteStatsReader` returns aggregates only: it never returns record contents or absolute paths. Database size is part of the aggregate snapshot.
    - The CLI alone reads `PEOPLE_CONTEXT_MCP_ENABLE_SENSITIVE` and `PEOPLE_CONTEXT_MCP_ENABLE_EXPORT`, then passes explicit booleans to `ComputeStats`; neither the app use case nor SQLite adapter reads process environment or probes/starts the server. Report the values as "in this environment".
    - The CLI passes the resolved database path separately; `ComputeStats` redacts it by default and includes it only under `--include-path`.
    - `--json` mirrors the human output and contains aggregates/counts only.
  - **Tests/validation:** Fake `StatsReader` tests pin report policy, explicit gate-state inputs, and path redaction. SQLite adapter tests pin every aggregate against a seeded DB. CLI snapshots cover `--json`, gate env combinations, and default-redacted-path / `--include-path`. `uv run ruff check .` and `uv run pytest -q` fully green.
''',
)

replace_exact(
    "docs/specs/m14-ecosystem-interop.md",
    '''App use case `app/compose_person_brief.py` composing three existing reads — `GetPersonContext`
(`app/get_person_context.py`), `GetCommunicationGuidance` (`app/get_communication_guidance.py`), and
`ListReminders` (`app/list_reminders.py`) — into one deterministic markdown document: identity and aliases,
relationships with perspective `display_type`, current affiliations, durable facts, communication guidance
signals, and open reminders. The third dependency is required, not optional: context and guidance both
deliberately include only `communication_note` reminders, so "open reminders" (scheduled `follow_up` and
`occasion` kinds included) is reachable only through `ListReminders`' person filter. Sensitivity behaves
exactly like vault export: elevated-sensitivity material requires the explicit `--include-sensitive` flag,
and the brief's footer states that the exported text is outside server disclosure controls. Output goes to
stdout by default (it is meant to be piped/pasted) — as markdown, or as a stable JSON document via `--json`
(the machine form the Obsidian plugin below consumes) — or to a file via `--output` with the `0o600` export
convention.
''',
    '''App use case `app/compose_person_brief.py` composes three existing reads — `GetPersonContext`,
`GetCommunicationGuidance`, and `ListReminders` — into one deterministic markdown/JSON document: identity and
aliases, relationships with perspective `display_type`, current affiliations, durable facts, communication
signals, and open reminders. `ListReminders` is required because context and guidance include only
`communication_note` reminders, while the brief also needs scheduled `follow_up` and `occasion` rows. For
sensitivity, call `GetPersonContext.execute(..., purpose="communication", include_sensitive=flag)` so the flag
widens context-backed facts, interactions, and traits. `GetCommunicationGuidance` remains ordinary-disclosure by
its existing contract; M14.1 does not widen that use case or its MCP tool. The brief labels this distinction and
states that exported text is outside server disclosure controls. Output goes to stdout by default, as markdown or
stable JSON, or to a file via `--output` with the `0o600` convention.
''',
)

replace_exact(
    "docs/specs/m14-ecosystem-interop.md",
    '''New filesystem adapter `adapters/filesystem/vcard_writer.py` mirroring the vault writer's determinism rules:
stable person ordering, stable property ordering, byte-identical re-export over unchanged data. Field mapping
emits `FN`/`N` from the person name, `NICKNAME` from `nickname` aliases, `EMAIL` from `handle` aliases that parse as
addresses, and `BDAY` from `predicate="birthday"` facts. The existing importer consumes only the first `ORG` and
first `TITLE`, so this milestone deliberately exports at most one active affiliation per person: choose it by
normalized organization name, normalized role, then affiliation id, and report additional active rows through an
`omitted_affiliations` CLI summary count. This makes affiliation lossiness explicit while preserving a truthful
round-trip guarantee without expanding the importer in the same PR. Elevated-sensitivity facts follow the same
`--include-sensitive` gate as vault export. One `--version {3.0,4.0}` flag selects the dialect (default per Open
Questions); every emitted field must round-trip through the project's own vCard importer, and tests assert the
selected affiliation survives while omitted rows are counted deterministically.
''',
    '''Add a typed `VCardWriter` port, `ExportVCard(ExportReader, VCardWriter, Clock)`, and a filesystem writer adapter.
The app use case excludes soft-deleted people, applies the explicit sensitivity gate, evaluates active records at
the injected clock's date, and constructs a typed projection; the filesystem adapter performs serialization only
and is never imported by `app/`. Stable person/property ordering yields byte-identical output for the same snapshot
and clock. Emit `FN`/`N` from the canonical name, `NICKNAME` from nickname aliases, and `EMAIL` from handle aliases
that parse as addresses. The existing importer consumes only the first `ORG`/`TITLE` and first `BDAY`, so export at
most one of each: choose the active affiliation by normalized organization name, normalized role, then id; choose
an eligible birthday fact by highest confidence, newest `recorded_at`, then id. Report remaining eligible rows as
`omitted_affiliations` and `omitted_birthdays`. One `--version {3.0,4.0}` flag selects the dialect; every emitted
field must round-trip through the existing importer, with tests proving the selected rows survive and omission
counts are deterministic.
''',
)

replace_exact(
    "docs/specs/m15-data-quality-and-credibility.md",
    '''CLI-only report over existing reads plus small adapter count queries: entity counts per table, alias-kind
distribution, facts/observations by `Sensitivity` level, relationship-category distribution, audit-log
operation counts, changelog entries per device, database size, and the current disclosure-gate state
(whether `PEOPLE_CONTEXT_MCP_ENABLE_SENSITIVE` / `PEOPLE_CONTEXT_MCP_ENABLE_EXPORT` are set in the
inspecting shell's environment — reported as "in this environment", since the server's own environment may
differ). The absolute database path is **redacted by default** (`--include-path` opts in): a path routinely
embeds a username, employer, or client name, so the default output is what a user can share when asking for
help. `--json` mirrors the human output. This is the M12 threat-model argument turned into a runnable
artifact: "here is exactly what this store holds and guards."
''',
    '''Add a narrow aggregate-only `ports/stats.py::StatsReader`, implemented by
`adapters/sqlite/stats_reader.py`, plus `app/compute_stats.py`. The adapter owns SQL aggregation and returns entity
counts, alias-kind distribution, facts/observations by `Sensitivity`, relationship-category distribution,
audit-operation counts, changelog entries per device, and database size — never record contents or an absolute
path. The CLI reads `PEOPLE_CONTEXT_MCP_ENABLE_SENSITIVE` / `PEOPLE_CONTEXT_MCP_ENABLE_EXPORT` from its own process
and passes explicit booleans to the use case, which reports them as "in this environment" without probing or
starting the server. The CLI also passes the resolved path separately; the app redacts it by default and includes
it only under `--include-path`. `--json` mirrors the human aggregate output. This keeps the hexagonal boundary
intact while turning the M12 threat-model argument into a runnable artifact.
''',
)

plan = Path(PLAN).read_text(encoding="utf-8")
for forbidden in (
    "Sensitivity mirrors vault export exactly",
    "no new port needed if existing readers suffice",
    "birthday facts survive",
):
    if forbidden in plan:
        raise RuntimeError(f"stale architecture text remains: {forbidden}")
for required in (
    "ExportVCard(ExportReader, VCardWriter, Clock)",
    "omitted_birthdays",
    "ports/stats.py",
    "guidance as ordinary-disclosure",
):
    if required not in plan:
        raise RuntimeError(f"required architecture contract missing: {required}")

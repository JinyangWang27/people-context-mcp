from pathlib import Path


def replace_between(path: str, start: str, end: str, replacement: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    i = text.find(start)
    if i < 0:
        raise RuntimeError(f"{path}: missing start marker {start!r}")
    j = text.find(end, i + len(start))
    if j < 0:
        raise RuntimeError(f"{path}: missing end marker {end!r}")
    file.write_text(text[:i] + replacement + text[j:], encoding="utf-8")


def replace_required(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"{path}: missing required text {old!r}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


plan = "docs/specs/pr-plan.md"

replace_between(
    plan,
    "- [ ] **PR M9.1",
    "- [ ] **PR M9.2",
    '''- [ ] **PR M9.1 — Relocate `ImportExtractorRouter` without dropping `mbox`**
  - **Scope:** Move `ImportExtractorRouter` into `adapters/import_router.py` and replace fall-through dispatch with explicit accepted source values. Preserve all three values that exist before M9: `email` and `mbox` both route to `EmailImportExtractor`; `vcard` routes to `VCardImportExtractor`; unknown values raise `ImportExtractionError("invalid_source_type", ...)`.
  - **Touches:** `adapters/import_router.py` (new), `adapters/vcard_import.py` (remove router only), `adapters/mcp/server.py` (import update), `tests/adapters/test_import_router.py` (new), and affected vCard/router tests.
  - **Spec:** (docs/specs/m9-cold-start-and-onboarding.md, "Router relocation")
    - Dispatch by source value, not extractor count: `email`/`mbox` → email extractor; `vcard` → vCard extractor; later PRs add `ics` and `linkedin`.
    - `mbox` is an existing public import mode; preserve its path-only validation, candidate output, and skip reporting.
    - Unknown values fail closed with `invalid_source_type`; `ImportContent` remains Protocol-based.
  - **Tests/validation:** Router tests cover `email`, `mbox`, `vcard`, and unknown values. Exercise `mbox` through `ImportContent` to pin its existing behavior. `uv run ruff check .` and `uv run pytest -q` fully green.
  - **Out of scope:** implementing ICS or LinkedIn extraction.

''',
)

replace_between(
    plan,
    "- [ ] **PR M9.3",
    "- [ ] **PR M9.4",
    '''- [ ] **PR M9.3 — LinkedIn connections-export import**
  - **Scope:** Add `LinkedInImportExtractor` for `source_type="linkedin"`, producing person, optional affiliation, and optional `linkedin_connected_on` fact candidates; never stage the profile URL.
  - **Touches:** `adapters/linkedin_import.py`, `adapters/import_router.py`, adapter/router/MCP/E2E tests.
  - **Spec:** (docs/specs/m9-cold-start-and-onboarding.md, "LinkedIn connections-export import")
    - Preserve existing `email`, `mbox`, `vcard`, and `ics` branches while adding `linkedin`.
    - Router coverage now spans five accepted source values plus the unknown-value error path.
    - Per-row failures remain independent; free-text/URL content is never staged.
  - **Tests/validation:** Adapter tests cover row independence, required fields, header policy, and raw-content exclusion. Router tests cover `email`, `mbox`, `vcard`, `ics`, `linkedin`, and unknown values. Add one full import E2E case. `uv run ruff check .` and `uv run pytest -q` fully green.
  - **Out of scope:** onboarding commands.

''',
)

replace_between(
    plan,
    "- [ ] **PR M9.4",
    "## M10 — Agent utilization",
    '''- [ ] **PR M9.4 — `people-context init` and packaged `people-context demo`**
  - **Scope:** Add interactive `init` and deterministic `demo [--reset]` CLI compositions. The demo dataset must be usable from an installed wheel: generate it procedurally or ship it as declared package data under `src/people_context/`; production code must never read it from `tests/fixtures`.
  - **Touches:** `cli.py`, `config.py`, `adapters/demo_data.py` or package data under `src/people_context/data/`, CLI tests, packaging smoke coverage, and docs.
  - **Spec:** (docs/specs/m9-cold-start-and-onboarding.md, "`people-context init`" / "`people-context demo`")
    - `init` composes existing import/self/philosophy use cases; no new app port.
    - `demo` ignores the real resolved DB, uses a dedicated path, and refuses reseeding without `--reset`.
    - Fictional seed data is deterministic and present in the built wheel.
  - **Tests/validation:** Test onboarding branches, DB isolation/reset behavior, deterministic seed output, and a clean-environment wheel install followed by `people-context demo --reset`. `uv run ruff check .` and `uv run pytest -q` fully green.
  - **Out of scope:** MCP onboarding and live external integrations.

## M10 — Agent utilization''',
)

replace_between(
    plan,
    "- [ ] **PR M11.2",
    "- [ ] **PR M11.3",
    '''- [ ] **PR M11.2 — Bundle export: `BundleReader`, `ExportSyncBundle`, `sync push` CLI**
  - **Scope:** Add a single-transaction `BundleReader`, an `ExportSyncBundle(BundleReader, Clock)` use case, and `sync push`. Database state comes from one SQLite snapshot; injected `Clock` supplies deterministic/testable `created_at`.
  - **Touches:** sync-bundle port/model, SQLite reader, app use case, CLI/docs, and app/adapter/CLI tests.
  - **Spec:** (docs/specs/m11-sync-bundle-and-bootstrap-restore.md, "Bundle contents and envelope" / "New app-layer use cases")
    - Envelope uses `created_at = clock.now()` and the specified format/version/origin/watermark/devices/snapshot/vocabulary/changelog fields.
    - All database-derived collections come from one transaction; changelog read is unbounded and deterministic.
    - Output file mode is `0o600`.
  - **Tests/validation:** Fake reader + fake clock pin exact metadata; SQLite tests prove consistent snapshot behavior; CLI tests cover output and permissions. `uv run ruff check .` and `uv run pytest -q` fully green.
  - **Out of scope:** restore and MCP exposure.

''',
)

replace_between(
    plan,
    "- [ ] **PR M12.2",
    "- [ ] **PR M12.3",
    '''- [ ] **PR M12.2 — Bump to 1.0.0 and synchronize distribution metadata**
  - **Scope:** Bump `project.version` and classifier, update the release checklist, and synchronize all version-bearing M8 artifacts in the same commit.
  - **Touches:** `pyproject.toml`, `server.json`, `mcpb/manifest.json`, `mcpb/pyproject.toml`, `docs/releasing.md`, and a metadata-sync test.
  - **Spec:** (docs/specs/m12-trust-stability-v1.md, "Version and release checklist")
    - Project version, Registry PyPI package version, MCPB semantic `version`, and MCPB `people-context` dependency pin all become `1.0.0` together.
    - MCPB `manifest_version` is a schema version and is not coupled to the application release.
    - CI fails on semantic-version drift, preferably via one canonical check.
  - **Tests/validation:** Parse all four metadata artifacts and assert semantic synchronization while validating `manifest_version` separately. Existing packaging tests remain green.
  - **Out of scope:** cutting the release/tag, SQLCipher, or changing the MCPB schema version without an upstream requirement.

''',
)

replace_between(
    plan,
    "- [ ] **PR M13.2",
    "- [ ] **PR M13.3",
    '''- [ ] **PR M13.2 — `upcoming_dates` MCP tool + `people-context upcoming` CLI**
  - **Scope:** Add `ListUpcomingDates(ContextReader, ListReminders, PersonReader, Clock)`. `Clock` anchors the date window and `PersonReader` supplies output names; expose through a read-only MCP tool and CLI.
  - **Touches:** app use case, MCP registration, CLI, and app/MCP/CLI/E2E tests.
  - **Spec:** (docs/specs/m13-daily-utility.md, "`upcoming_dates` / CLI report")
    - Use `clock.now()` only; document and test inclusive interval boundaries.
    - Facts come from `ContextReader`, reminders from `ListReminders`, and names from `PersonReader`; skip missing/deleted people deterministically.
    - Only ordinary birthday facts and active dated reminders inside the same window qualify.
  - **Tests/validation:** Fake-clock tests cover today, final included date, and just-outside boundaries, plus recurring dates/leap day, name lookup, missing people, sensitivity, MCP shape, CLI snapshot, and E2E composition. `uv run ruff check .` and `uv run pytest -q` fully green.
  - **Out of scope:** more predicates, elevated variants, and meeting-prep content.

''',
)

replace_between(
    plan,
    "- [ ] **PR M14.3",
    "- [ ] **PR M14.4",
    '''- [ ] **PR M14.3 — Outlook CSV + WhatsApp import extractors**
  - **Scope:** Add Outlook and WhatsApp extractors while explicitly widening the extractor keyword contract. Preserve all five pre-M14 accepted source values: `email`, `mbox`, `vcard`, `ics`, and `linkedin`.
  - **Touches:** router, new extractors, `ImportExtractor` Protocol, `ImportContent`, every concrete extractor, MCP import tool, and complete adapter/router/E2E tests.
  - **Spec:** (docs/specs/m14-ecosystem-interop.md, "Outlook CSV and WhatsApp import extractors")
    - Add optional `self_names` and `self_sender` to the explicit Protocol; every implementation accepts them and the router forwards them.
    - Outlook/WhatsApp become the sixth and seventh accepted source values; unknown values still fail closed.
    - WhatsApp never persists message bodies and excludes self senders by aliases or explicit hint.
  - **Tests/validation:** Exercise `email`, `mbox`, `vcard`, `ics`, and `linkedin` through `ImportContent` after widening. Router tests cover all seven accepted source values plus unknown. Add Outlook/WhatsApp parsing, self-resolution, and raw-content sentinel coverage. `uv run ruff check .` and `uv run pytest -q` fully green.
  - **Out of scope:** Signal and untyped `**kwargs`.

''',
)

m9 = "docs/specs/m9-cold-start-and-onboarding.md"
replace_between(
    m9,
    "### `people-context demo`",
    "### `.ics` calendar import",
    '''### `people-context demo`

The command always uses a dedicated demo database and refuses reseeding without `--reset`. Its deterministic
fictional dataset is runtime product data, so it must ship in installed artifacts: implement it procedurally under
`src/people_context/` or declare package data there. Production code must not read from `tests/fixtures`, which is
not included by the current wheel configuration. Acceptance includes building and installing the wheel in a clean
environment and successfully running `people-context demo --reset`.

''',
)
replace_between(
    m9,
    "### Router relocation",
    "## Migration needs",
    '''### Router relocation

The current router delegates non-vCard sources to `EmailImportExtractor`, which already accepts both `email` and
`mbox`. There are therefore three accepted source values before M9. Move dispatch to `adapters/import_router.py`
and make it explicit: `email`/`mbox` → email extractor; `vcard` → vCard extractor; later branches add `ics` and
`linkedin`; every other value raises `ImportExtractionError("invalid_source_type", ...)`. Preserve `mbox`'s
path-only validation and existing output exactly.

''',
)
replace_between(
    m9,
    "## Testing strategy",
    "## Open questions",
    '''## Testing strategy

- App tests cover `init` and deterministic demo seeding.
- Adapter tests cover ICS/LinkedIn independence, self filtering, deduplication, and raw-content exclusion.
- Router tests cover all five accepted source values (`email`, `mbox`, `vcard`, `ics`, `linkedin`) plus unknown.
- MCP tests exercise the two new sources; E2E retains explicit `mbox` coverage and adds one new-source flow.
- CLI tests prove demo isolation/reset behavior.
- Packaging acceptance builds and installs the wheel in a clean environment and runs `people-context demo --reset`.

''',
)
replace_required(
    m9,
    "4. Should `people-context demo`'s fictional dataset be checked into the repository as a fixture (deterministic,\n   diffable) or generated procedurally at run time?",
    "4. Should the packaged fictional dataset use Python constants or declared JSON package data under `src/people_context/`? Either is acceptable; `tests/fixtures` is not.",
)

m11 = "docs/specs/m11-sync-bundle-and-bootstrap-restore.md"
replace_between(
    m11,
    "### New app-layer use cases",
    "### New port and adapter for verbatim bulk restore",
    '''### New app-layer use cases

`ExportSyncBundle` takes a `BundleReader` and injected `Clock`. The reader supplies one consistent database
snapshot; `clock.now()` supplies deterministic/testable `created_at`, matching `ExportData`. `RestoreSyncBundle`
uses the narrow bootstrap-restorer port and delegates emptiness checks plus verbatim writes to one transaction.

''',
)

m12 = "docs/specs/m12-trust-stability-v1.md"
replace_between(
    m12,
    "### Version and release checklist",
    "### Opt-in SQLCipher",
    '''### Version and release checklist

Bump the project and classifier to `1.0.0`/Production-Stable. In the same commit, synchronize the Registry PyPI
package version in `server.json`, MCPB semantic `version`, and the `people-context` dependency pin in the bundled
MCPB `pyproject.toml`. MCPB `manifest_version` is a schema-version field and remains independent. CI parses all
artifacts and fails on semantic-version drift. Follow the existing release procedure and add the compatibility-doc
checklist item; do not cut the tag in this PR.

''',
)
replace_between(
    m12,
    "## Testing strategy",
    "## Open questions",
    '''## Testing strategy

- Encryption adapter and CLI refusal tests remain as specified.
- Existing plain-SQLite tests remain unchanged.
- Add a distribution metadata test parsing `pyproject.toml`, `server.json`, `mcpb/manifest.json`, and
  `mcpb/pyproject.toml`; assert one semantic release version and treat `manifest_version` separately.
- Documentation-only changes require link checks.

''',
)

m13 = "docs/specs/m13-daily-utility.md"
replace_between(
    m13,
    "### `upcoming_dates` / CLI report",
    "### Meeting preparation",
    '''### `upcoming_dates` / CLI report

`ListUpcomingDates` depends on `ContextReader`, `ListReminders`, `PersonReader`, and an injected `Clock`. The clock
anchors a documented inclusive date interval; person reads supply names and allow missing/soft-deleted people to
be skipped deterministically. Facts must pass ordinary sensitivity, use predicate `birthday`, and parse as ISO or
`--MM-DD`; active reminders qualify when `due_at` lies inside the same window. Tests pin both boundaries, recurring
dates, leap day, and name lookup. Output remains `{person_id, name, kind, date, label}` plus
`skipped_unparseable`.

''',
)

m14 = "docs/specs/m14-ecosystem-interop.md"
replace_required(
    m14,
    "Regression tests exercise every pre-M14 source through `ImportContent` after the signature change.",
    "Regression tests exercise every pre-M14 accepted source value (`email`, `mbox`, `vcard`, `ics`, and `linkedin`) through `ImportContent` after the signature change.",
)

checks = {
    plan: [
        "without dropping `mbox`",
        "all seven accepted source values",
        "ExportSyncBundle(BundleReader, Clock)",
        "ListUpcomingDates(ContextReader, ListReminders, PersonReader, Clock)",
        "MCPB `manifest_version` is a schema version",
        "clean-environment wheel install",
    ],
    m9: ["three accepted source values before M9", "runs `people-context demo --reset`"],
    m11: ["injected `Clock`"],
    m12: ["MCPB `manifest_version` is a schema-version field"],
    m13: ["`ContextReader`, `ListReminders`, `PersonReader`, and an injected `Clock`"],
    m14: ["`email`, `mbox`, `vcard`, `ics`, and `linkedin`"],
}
for path, phrases in checks.items():
    text = Path(path).read_text(encoding="utf-8")
    for phrase in phrases:
        if phrase not in text:
            raise RuntimeError(f"{path}: postcondition missing {phrase!r}")

# M14 — Ecosystem & interoperability

Status: Planned. See [docs/roadmap.md](../roadmap.md#m14--ecosystem--interoperability).

## Motivation

M8 puts the server where MCP users look; this milestone reaches users who are *not* in an MCP client yet, by
meeting three adjacent ecosystems on their own terms. A compact person brief delivers value inside any chat
surface with zero setup — a wedge that converts to full MCP use later. vCard export closes the portability
loop the importer opened, making the store a credible primary address book rather than a one-way sink. New
importers widen the funnel (every "import X into a personal CRM" search is a landing opportunity). And the
Obsidian ecosystem — already half-served by the deterministic vault export — gets a live plugin, whose
community directory is itself a discovery channel like the M8 registries.

The repository already has the precedent this milestone needs for a TypeScript deliverable: `openclaw-plugin/`
is an in-repo TS package with its own `package.json`, `vitest` tests, built `dist/`, and a dedicated publish
workflow (`.github/workflows/package-publish.yml`).

## Scope

In scope:

- `people-context brief PERSON [--include-sensitive]` (CLI-only markdown brief);
- `people-context export-vcard [--output FILE]` (CLI-only deterministic vCard export);
- two new import sources through the (M9-relocated) `adapters/import_router.py`: Outlook/Exchange contacts
  CSV (`source_type="outlook"`) and WhatsApp chat export (`source_type="whatsapp"`);
- an Obsidian community plugin under `obsidian-plugin/`, following the `openclaw-plugin/` packaging precedent.

Non-goals:

- CardDAV or any synchronization protocol — export is one-way file output (CardDAV stays a post-roadmap
  candidate);
- a `brief` MCP tool — agents already have `get_person_context`/`get_communication_guidance`; `brief` exists
  for humans pasting into non-MCP surfaces, and keeping it CLI-only preserves the rule that bulk-disclosure
  formatting stays human-operated;
- parsing WhatsApp message bodies, attachments, or media — participants and timestamps only (see Security);
- Signal import — current Signal backups are encrypted and have no stable plaintext export; revisit if that
  changes;
- an Obsidian plugin that writes to the database — read-only, always.

## Design

### `people-context brief`

App use case `app/compose_person_brief.py` composing two existing reads — `GetPersonContext`
(`app/get_person_context.py`) and `GetCommunicationGuidance` (`app/get_communication_guidance.py`) — into one
deterministic markdown document: identity and aliases, relationships with perspective `display_type`, current
affiliations, durable facts, communication guidance signals, and open reminders. Sensitivity behaves exactly
like vault export: elevated-sensitivity material requires the explicit `--include-sensitive` flag, and the
brief's footer states that the exported text is outside server disclosure controls. Output goes to stdout by
default (it is meant to be piped/pasted), or to a file via `--output` with the `0o600` export convention.

### `people-context export-vcard`

New filesystem adapter `adapters/filesystem/vcard_writer.py` mirroring the vault writer's determinism rules:
stable person ordering, stable property ordering, byte-identical re-export over unchanged data. Field mapping
inverts the existing importer: `FN`/`N` from the person name, `NICKNAME` from `nickname` aliases, `EMAIL`
from `handle` aliases that parse as addresses, `ORG`/`TITLE` from active affiliations, `BDAY` from
`predicate="birthday"` facts (`AliasKind` values in `domain/person.py`; affiliation/fact shapes per
[docs/data-model.md](../data-model.md)). Elevated-sensitivity facts follow the same `--include-sensitive`
gate as vault export. One `--version {3.0,4.0}` flag selects the dialect (default per Open Questions);
everything emitted must round-trip through the project's own vCard importer, and a round-trip test enforces
it.

### Outlook CSV and WhatsApp import extractors

Both are one extractor class plus a router branch, per the M9 pattern:

- `adapters/outlook_import.py::OutlookImportExtractor`: Outlook's contacts CSV export (First/Middle/Last
  Name, E-mail Address, Company, Job Title, Birthday columns among others) maps to the same candidate
  vocabulary vCard already uses — `person` (+ `handle` alias), `affiliation` (`org`, `role`), and a
  `birthday` fact. Column-set drift across Outlook versions is handled the same way the M9 LinkedIn open
  question resolves (tolerate a superset, skip rows missing required fields with per-row skip reasons).
- `adapters/whatsapp_import.py::WhatsAppImportExtractor`: WhatsApp's plain-text chat export interleaves
  `[date, time] Sender Name: message` lines. The extractor parses **only** the timestamp and sender-name
  prefix of each line: senders become `person` candidates deduplicated by normalized name across the file,
  and one `interaction` candidate per calendar day per chat (channel `"whatsapp"`) covers the conversation
  without one-candidate-per-message noise. Message text after the `: ` separator is never read into any
  candidate field.

Both stage through the unchanged `import_content` → `review_import` → `commit_import` gate.

### Obsidian plugin (`obsidian-plugin/`)

A TypeScript package in-repo, structured like `openclaw-plugin/` (own `package.json`, `tsconfig.json`,
`vitest`, built `dist/`, dedicated publish workflow) and distributed through the Obsidian community plugin
directory. It renders read-only "person view" panes — identity, relationships with `display_type`,
facts, recent interactions — resolved live from the local SQLite file, so pages never go stale the way
one-shot vault exports do. It opens the database strictly read-only and never holds a write lock; the
concrete driver (WASM SQLite reading a snapshot copy vs. platform bindings) is an Open Question with a hard
requirement either way: the plugin must never block or corrupt a concurrently writing server. The vault
export (M7) remains the offline/portable path; the plugin is the live path, and both follow the same naming
and perspective conventions ([docs/vault-export.md](../vault-export.md)).

## Migration needs

None. No schema change; new importers write only staged candidates, exports and the plugin only read.

## CLI / MCP surface changes

CLI only; no MCP tool is added or changed. `import_content` gains two accepted `source_type` values
(`"outlook"`, `"whatsapp"`) with unchanged tool signature and response shape.

```text
uv run people-context brief PERSON [--include-sensitive] [--output FILE]
uv run people-context export-vcard [--output FILE] [--include-sensitive] [--version 4.0]
```

## Security / privacy considerations

- `brief` and `export-vcard` produce text outside server disclosure controls — both carry the vault-export
  caveat, both default to excluding elevated-sensitivity material, and both stay CLI-only so no model can
  trigger bulk formatted disclosure.
- WhatsApp import is the strictest raw-content test this project has faced: chat text is exactly the material
  [docs/privacy-and-safety.md](../privacy-and-safety.md#no-raw-emails-conversations-or-transcripts) exists to
  keep out. The extractor's contract — nothing after the sender-name separator is ever read into a candidate —
  is enforced by a sentinel test (a unique string planted in message bodies must appear in no staged
  candidate), the same `_NOTE_SENTINEL` pattern the vCard tests use.
- Both new importers are local, file-based, and offline, per the existing no-surprise-network rule.
- The Obsidian plugin reads the same plaintext database the CLI reads, under the same OS user; it must not
  copy the database anywhere outside the vault-local cache it documents, and it must never implement a write
  path, keeping every mutation behind the audited server/CLI surfaces.

## Testing strategy

- App layer: fake-port tests for `ComposePersonBrief` (composition, sensitivity gating, deterministic
  ordering).
- Adapter layer: `test_vcard_export.py` — determinism (byte-identical re-export), sensitivity gating, and a
  full round-trip through `VCardImportExtractor` asserting people/aliases/affiliations/birthday facts
  survive; `test_outlook_import.py` and `test_whatsapp_import.py` modeled on `test_vcard_import.py`
  (per-row/line independence, skip reasons, cross-file dedup, raw-content sentinel).
- Router: extend the M9 `test_import_router.py` dispatch matrix with both new source types.
- CLI layer: `brief` snapshot test incl. `--include-sensitive` difference; `export-vcard` determinism and
  `0o600` checks.
- Obsidian plugin: `vitest` unit tests over the data-access layer against a fixture database, following the
  `openclaw-plugin/` test layout; rendering is exercised by fixture snapshots, not a live Obsidian instance.
- E2E: one stdio case committing a WhatsApp import and asserting the sentinel never reaches
  `get_person_context` output.

## Open questions

1. Which vCard dialect should be the export default — 4.0 (cleaner, UTF-8 native) or 3.0 (wider legacy
   importer support, notably older Outlook/Google flows)?
2. Should `brief` offer named templates (e.g. `--style meeting-prep` vs. `--style intro`) in this milestone,
   or ship one canonical layout first?
3. WhatsApp export formats vary by platform and locale (bracket styles, date order, 12/24h). Should v1
   support a fixed set of detected formats with explicit per-file failure, or accept a `--format` hint flag?
4. Obsidian plugin database access: bundle a WASM SQLite build reading a snapshot copy (safe, slightly stale)
   or use platform bindings against the live file (fresh, but WAL-locking risk beside a running server)?
5. Should the Obsidian plugin live in this repository (shared CI, versioned with the schema it reads) or in a
   sibling repository (cleaner community-plugin submission and release cadence)?

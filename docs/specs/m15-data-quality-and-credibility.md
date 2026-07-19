# M15 — Data quality, insight, and credibility

Status: Planned. See [docs/roadmap.md](../roadmap.md#m15--data-quality-insight-and-credibility).

## Motivation

Memory tools die when users stop trusting their data. After M9/M14 widen the import funnel, real databases
will accumulate near-duplicates (the same person from vCard, LinkedIn, and calendar imports under differing
name spellings), and the longer a database lives the more its facts can drift into contradiction. The
machinery to *fix* problems already exists — `merge_people` with its `duplicate_relationships_removed`
dedupe, `correct_record`'s lossless before/after audit, `forget` — but nothing *finds* problems. Meanwhile
the project's strongest differentiator, inspectable local-first privacy, is documented
([docs/privacy-and-safety.md](../privacy-and-safety.md)) but not operationalized: there is no command that
shows a user what the store holds, at which sensitivity, disclosed through which gates.

Two further credibility gaps are cheap to close. First, the domain model already has
`AliasKind.NATIVE_SCRIPT` and `AliasKind.TRANSLITERATION` (`domain/person.py`), and `normalize_name`
(`domain/shared.py`) already NFKC-normalizes, casefolds, and strips combining marks — but resolution ranking
and explanations do not yet treat script-pair aliases as first-class, and no doc shows the bilingual
workflow. Second, the project has no published evidence: an evaluation with numbers, and use-case narratives,
are what turn a technically excellent README into something that travels.

## Scope

In scope:

- `people-context doctor`: report-only data-quality findings with suggested follow-up commands;
- `people-context stats`: local inventory of counts, sensitivity distribution, audit/changelog activity, and
  disclosure gates;
- transliteration-aware resolution polish (ranking + explanation + documentation);
- a scripted, reproducible evaluation under `evals/` and a use-case gallery under `docs/use-cases/`.

Non-goals:

- any auto-applied fix — `doctor` never merges, edits, or deletes; it prints findings and the exact
  `merge_people`/`correct_record`/CLI invocations a human could run, preserving the rule that destructive
  operations stay explicit and human-approved;
- LLM-based duplicate detection or fact reconciliation — findings must be deterministic and explainable
  (shared normalized aliases, identical handles, overlapping validity periods), like the staged explanations
  `resolve_person` already returns;
- a hosted or telemetry-backed benchmark — the eval runs locally, and publishing results is a documentation
  act, not a data-collection feature;
- new MCP tools — `doctor` and `stats` are CLI-only; surfacing curation findings to agents can be revisited
  once the report format has stabilized.

## Design

### `people-context doctor`

New narrow read port `ports/curation.py::CurationReader` implemented in `adapters/sqlite/curation_reader.py`
(the finding *queries* live in the adapter; finding *policy* — thresholds, ordering, message text — lives in
`app/run_doctor.py`). Deterministic finding classes, each with a stable code:

- `duplicate_alias`: two non-deleted persons share a normalized alias or name
  (`persons.canonical_name_normalized` / `aliases.value_normalized`, both already indexed), the strongest
  duplicate signal and the same normalization identity resolution already trusts;
- `duplicate_handle`: two persons share a `handle` alias value (e.g. the same email address), which imports
  treat as identity-bearing;
- `contradictory_fact`: one person has two facts with the same `predicate` whose validity periods
  (`Fact.period`) overlap but whose `value`s differ — flagged, not adjudicated;
- `dangling_reference`: relationships, affiliations, or interaction participants pointing at soft-deleted
  people (visible via `include_deleted` reads), which merges and forgets can legitimately leave behind and a
  user may want to prune.

Output is a human-readable report (and `--json` for scripting) where every finding includes the evidence and
a copy-pasteable suggested follow-up (`people-context show`, a `merge_people` MCP call, `correct_record`,
or `delete`). Exit code 0 with findings; a non-zero exit is reserved for actual errors, so `doctor` can run
in cron/scripts without treating findings as failures.

### `people-context stats`

CLI-only report over existing reads plus small adapter count queries: entity counts per table, alias-kind
distribution, facts/observations by `Sensitivity` level, relationship-category distribution, audit-log
operation counts, changelog entries per device, database file path and size, and the current disclosure-gate
state (whether `PEOPLE_CONTEXT_MCP_ENABLE_SENSITIVE` / `PEOPLE_CONTEXT_MCP_ENABLE_EXPORT` are set in the
inspecting shell's environment — reported as "in this environment", since the server's own environment may
differ). `--json` mirrors the human output. This is the M12 threat-model argument turned into a runnable
artifact: "here is exactly what this store holds and guards."

### Transliteration-aware resolution polish

Small, additive changes inside the existing five-stage pipeline (`app/resolve_person.py`), no port changes:

- an exact match on a `native_script` or `transliteration` alias ranks with (not below) primary-name exact
  matches, and the returned explanation names the alias kind that matched, so bilingual users can see *why* a
  script-form query resolved;
- `docs/identity-resolution.md` gains a documented bilingual workflow: store the native-script form and
  romanization as paired aliases (kinds already exist), with examples showing both directions resolving;
- fixture-backed tests with CJK + romanization pairs (and one non-CJK case, e.g. Cyrillic) demonstrating both
  directions and asserting explanation text.

Existing response shapes are unchanged; only ranking behavior and explanation strings improve, within the
M12 additive-contract promise.

### Evaluation and use-case gallery

- `evals/` at the repository root: a scripted harness that seeds a fixture database, runs a fixed task set
  through an MCP-connected agent twice — with and without the `people-context` server attached — and scores
  results (identity disambiguation accuracy against fixture ground truth; rubric-scored communication-draft
  quality). The harness pins model IDs and prompts in config so runs are reproducible and re-runnable as
  models change; results are published as a dated `docs/evals.md` with the harness version. The eval is a dev
  workflow (like `openclaw-plugin/`'s tests), not part of the shipped package, and any API keys it uses stay
  in the runner's environment.
- `docs/use-cases/`: three to five short narrative recipes (job-search networking, founder investor
  relations, caregiving coordination, community organizing), each walking real commands/tools end to end and
  linked from the README — adoption narratives for people who don't read architecture docs.

## Migration needs

None required. As with M13, if finding queries need support, an additive index migration is permitted under
the M12 promise; `doctor` and `stats` otherwise read existing tables only.

## CLI / MCP surface changes

CLI only; no MCP tool changes, and `resolve_person`'s request/response contract is unchanged (ranking and
explanation strings are behavior, documented as such).

```text
uv run people-context doctor [--json] [--only CODE[,CODE...]]
uv run people-context stats [--json]
```

## Security / privacy considerations

- `doctor` findings necessarily juxtapose personal data (two people's names/handles side by side); output is
  local stdout only, and `--json` documents the same user-owned-disclosure caveat as `watch` and the export
  commands.
- `stats` reports aggregates and counts, never record contents — safe to paste into an issue when asking for
  help, and the docs say exactly that, giving users a support artifact that leaks nothing.
- The disclosure-gate section of `stats` reads only the local process environment; it must not probe or start
  the server.
- The eval harness must ship with fictional fixture data only, and its docs must warn against pointing it at
  a real personal database.
- Resolution-ranking changes must not widen disclosure: `resolve_person` already returns candidate names and
  match explanations; naming the alias *kind* adds no new personal data beyond what the match itself reveals.

## Testing strategy

- Adapter layer: `test_sqlite_curation_reader.py` with fixture databases per finding class (planted duplicate
  normalized aliases, shared handles, overlapping contradictory facts, dangling post-merge references),
  asserting both detection and non-detection (clean data yields zero findings).
- App layer: fake-port tests for `run_doctor` policy — stable finding codes, deterministic ordering, correct
  suggested-command rendering.
- Resolution: extend the existing resolution test suites with script-pair fixtures asserting rank parity and
  explanation content for `native_script`/`transliteration` matches.
- CLI layer: `doctor` and `stats` snapshot tests over a seeded fixture, including `--json` shape stability
  (these outputs become de-facto contracts once scripts consume them).
- Eval harness: a dry-run mode test that executes the harness end to end against a stub agent (no network),
  verifying scoring plumbing without model calls.

## Open questions

1. Should `doctor` support an interactive mode that applies a selected merge after explicit confirmation
   (reusing the `delete`-style `--yes` gate), or stay strictly report-only in its first release?
2. Are `--json` outputs of `doctor`/`stats` part of the M12 compatibility promise from day one, or marked
   experimental for one release first?
3. Should transliteration rank parity extend to *fuzzy* matches on script-pair aliases, or only exact
   normalized matches in the first pass (fuzzy cross-script matching has a much higher false-positive risk)?
4. What is the minimum credible eval task set — is identity disambiguation + guided drafting enough, or
   should staging-quality (does the agent stage good candidates?) be scored too?
5. Should eval results live in the README (maximum visibility, fastest staleness) or only in a dated
   `docs/evals.md` the README links (slower decay, one click away)?

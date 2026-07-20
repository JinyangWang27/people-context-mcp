# M12 — Trust, stability, and v1.0

Status: Planned. See [docs/roadmap.md](../roadmap.md#m12--trust-stability-and-v10).

## Motivation

`pyproject.toml` still classifies the project as Alpha, although the implementation already follows an additive
response-contract discipline and forward-only migrations. M12 turns that practice into an explicit compatibility
promise, synchronizes every distribution surface for 1.0, adds an opt-in encrypted SQLite connection path, and
publishes a factual local-first threat-model comparison.

## Scope

In scope:

- a written MCP, CLI, and DB compatibility promise;
- a synchronized `1.0.0` release metadata update;
- opt-in SQLCipher at-rest encryption;
- a sourced threat-model comparison with cloud-hosted memory tools;
- README demo polish built on M9's packaged demo.

Non-goals:

- redesigning existing tools or response fields;
- making encryption the default;
- key rotation, keychain integration, or multi-key support;
- implementing deferred incremental sync or multi-user behavior.

## Design

### Compatibility promise

Add `docs/compatibility.md`, linked from the README and `docs/mcp-interface.md`, stating:

- **MCP responses:** within a major version, existing fields are not removed or repurposed; new fields are
  additive; tool names and required parameters remain stable; optional parameters may be added with compatible
  defaults.
- **Database:** migrations are forward-only and additive within a major version; no migration drops or narrows a
  column read by shipped application code.
- **CLI:** existing commands and flags keep working; new flags are additive and preserve previous defaults.
- **Machine-readable outputs:** a command explicitly documented as a stable JSON interface, such as the M14 brief
  and person-index outputs, follows the same additive field rule. Human-formatted tables/Markdown remain outside
  the frozen contract unless separately declared.
- **Vault Markdown:** deterministic but explicitly not frozen as a compatibility surface in 1.0.

Do not promise a deprecation window the project has not historically practiced.

### Version and release checklist

Bump the root project and classifier to `1.0.0`/Production-Stable. In the same commit synchronize:

1. `pyproject.toml` project version;
2. top-level `server.json.version`;
3. the `people-context` PyPI package entry version in `server.json`;
4. MCPB semantic `mcpb/manifest.json.version`;
5. the exact `people-context` dependency pin in `mcpb/pyproject.toml`.

MCPB `manifest_version` remains an independent schema-version field and is validated against the supported MCPB
schema, never set to the application version.

Because the repository runs `uv sync --locked --all-extras` and `uv lock --check`, the same PR must regenerate and
commit root `uv.lock`; its editable `people-context` package metadata must reflect `1.0.0`. A parser-based metadata
test locates the Registry package by identifier rather than array position and asserts all semantic release values
match. `uv lock --check` remains a separate generated-lock integrity gate.

The compatibility package under `compat/people-context-mcp/` remains a renamed-distribution shim with its own
post-release version. Its dependency lower bound already accepts `people-context==1.0.0`; do not falsely force the
shim's version to match the primary distribution unless that package is intentionally republished.

Follow the existing release procedure and update its checklist, but do not create the tag or live release in this
PR.

### Opt-in SQLCipher

Add an optional dependency extra:

```toml
[project.optional-dependencies]
semantic = ["model2vec>=0.8.2,<0.9", "sqlite-vec>=0.1.9,<0.2"]
encrypted = ["sqlcipher3-binary>=<verified-lower>,<next-breaking>"]
```

Use `sqlcipher3-binary` unless an implementation-time wheel/platform probe demonstrates a blocker for the
project's supported Python/OS matrix; record the exact supported platforms and pinned range. Do not silently ship
an extra that cannot install on a claimed supported platform.

Add `adapters/sqlite/db.py::open_encrypted_db(path, key)` alongside, not as a parameter to, `open_db(path)`. It
must set the key before reading schema metadata or running migrations, apply the same foreign-key, WAL, busy-timeout,
and migration setup after keying, and return the same connection interface consumed by existing repositories.
Every plain-SQLite caller remains unchanged.

`people-context-mcp --encrypted` and the global CLI form `people-context --encrypted ...` require
`PEOPLE_CONTEXT_DB_KEY`. Without the flag, existing plaintext behavior is byte-for-byte unchanged. With the flag
and no non-empty key, startup refuses clearly and never falls back to plaintext.

Changing optional dependencies requires regenerating and committing `uv.lock`. M12.4's required validation is:

```text
uv lock --check
uv sync --locked --all-extras
uv run --locked ruff check .
uv run --locked pytest -q
```

CI must actually install the encrypted extra on every platform declared supported for 1.0; tests may skip only on
explicitly unsupported platforms documented by the release, not because the dependency was omitted from CI.

### Threat-model comparison

Append a dated, sourced subsection under `docs/privacy-and-safety.md#threat-model-notes`. Compare local-first and
cloud-hosted memory tools only on verifiable axes:

- where data is stored at rest;
- what a vendor breach or legal demand can expose;
- whether the product functions fully offline;
- what deletion means compared with this project's hard `forget` behavior.

Use an “as of YYYY-MM-DD” note and primary vendor documentation. Keep the language factual rather than promotional.

### README polish

Add a short Demo section between “Why” and “Quick start”, showing the packaged `people-context demo` flow and its
dedicated database. All referenced assets and commands must be link/path checked.

## Migration needs

No new schema migration. SQLCipher changes the connection-open path, not the logical schema.

## CLI / MCP surface changes

- `people-context-mcp --encrypted`;
- global `people-context --encrypted ...`;
- no MCP tool or response-shape changes.

## Security and privacy

- The key comes only from `PEOPLE_CONTEXT_DB_KEY`, never a flag value, config file, log, exception payload, audit
  payload, or changelog payload.
- Empty/whitespace-only keys are rejected.
- Wrong-key errors are generic and never echo key material or sensitive page contents.
- Verify that the chosen binding encrypts WAL/SHM data as configured; do not infer protection only because the main
  database cannot be opened by plain SQLite.
- Plain SQLite remains the default and documentation must not imply otherwise.
- A new encrypted database and an existing encrypted database both use the same canonical migration path after the
  key is applied.

## Testing strategy

### Compatibility and release metadata

- Link checks for the compatibility document and README additions.
- Parser-based synchronization test over `pyproject.toml`, `server.json`, `mcpb/manifest.json`, and
  `mcpb/pyproject.toml`.
- Assert the root package version recorded in `uv.lock` matches `pyproject.toml` and run `uv lock --check`.
- Validate MCPB `manifest_version` separately from semantic version fields.

### Encryption

- missing, empty, and whitespace-only key refusal;
- create/read/reopen encrypted database with the correct key;
- wrong-key refusal;
- plain `sqlite3.connect()` cannot read schema/data from the encrypted database;
- WAL-mode writes followed by inspection proving companion files do not reveal plaintext sentinel values;
- existing migrations run after keying;
- server and CLI refusal without the environment key;
- key sentinels never appear in stdout, stderr, logs, exceptions, audit rows, or changelog rows;
- all existing `open_db` tests pass unmodified;
- locked all-extras installation and tests run in CI.

## Open questions

1. If `sqlcipher3-binary` lacks maintained wheels for a currently supported platform, should 1.0 document the
   encrypted extra as platform-limited or defer encryption until one binding covers the supported matrix?
2. Should a future major version freeze the vault Markdown layout, or should integrations continue to consume
   stable JSON only?
3. When should the dated cloud-tool comparison be reviewed for staleness?
4. Should import-boundary enforcement become automated with import-linter or Ruff in a later hardening PR?

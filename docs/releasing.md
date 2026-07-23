# Releasing and coverage

## One-time repository setup

### Codecov

Codecov uploads use GitHub OIDC through `codecov/codecov-action`; no long-lived `CODECOV_TOKEN` secret is
required. Ensure the Codecov GitHub App has access to `JinyangWang27/people-context`. The CI workflow
generates `coverage.xml` and uploads it on pushes and same-repository pull requests. Fork pull requests still
run the tests but skip the upload because they do not receive a trusted OIDC context for this repository.

### PyPI trusted publishing

One PyPI project is published from this repository using Trusted Publishing, so no long-lived PyPI API token is
stored in GitHub:

- **`people-context`** — the primary distribution, built from the repository root.

Its trusted publisher uses these coordinates:

| Field             | Value            |
| ----------------- | ---------------- |
| GitHub owner      | `JinyangWang27`  |
| GitHub repository | `people-context` |
| Workflow filename | `release.yml`    |
| Environment name  | `pypi`           |

Keep a GitHub Actions environment named `pypi`. Requiring approval and limiting deployments to release tags
is recommended.

## Distribution and command names

- PyPI distribution: `people-context`.
- Python import package: `people_context`.
- MCP server executables: `people-context` (Registry/package-aligned) and `people-context-mcp` (compatibility alias).
- Human-operated CLI executable: `pctx`.

Documentation and integrations use the `people-context` distribution name.

## Publish a release

1. Update `project.version` in `pyproject.toml`. In the same commit, update the MCP Registry metadata in
   `server.json` — its top-level `version` and the `--from people-context==<version>` package pin.
   (`tests/test_registry_metadata.py` fails if `server.json` drifts from `project.version`.) See
   [mcp-registry.md](mcp-registry.md) for the full Registry publication procedure. Merge the change to `main`.
2. Create a GitHub Release from that commit using a matching tag such as `v0.1.1`.
3. Publish the GitHub Release.
4. Approve the `pypi` environment deployments when prompted.

`.github/workflows/release.yml` then:

1. verifies that `uv.lock` matches `pyproject.toml`;
2. builds and checks the `people-context` wheel and source distribution;
3. publishes the primary artifacts to the `people-context` PyPI project using short-lived OIDC credentials.

PyPI release filenames and versions are immutable. If a primary upload partially succeeds, publish a new
version rather than attempting to overwrite existing files.

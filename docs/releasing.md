# Releasing and coverage

## One-time repository setup

### Codecov

1. Add this repository to Codecov.
2. Add the repository upload token as a GitHub Actions secret named `CODECOV_TOKEN`.

The CI workflow generates `coverage.xml` with `pytest-cov` and uploads it on pushes and same-repository pull requests. Fork pull requests still run tests, but skip the upload because GitHub does not expose repository secrets to forks.

### PyPI trusted publishing

Publishing uses PyPI Trusted Publishing, so no long-lived PyPI API token is stored in GitHub.

Create a pending trusted publisher on PyPI with these values:

| Field | Value |
|---|---|
| PyPI project name | `people-context-mcp` |
| GitHub owner | `JinyangWang27` |
| GitHub repository | `people-context-mcp` |
| Workflow filename | `release.yml` |
| Environment name | `pypi` |

Create a GitHub Actions environment named `pypi`. Requiring approval and limiting deployment to release tags is recommended.

The first successful trusted publication creates the PyPI project if the name is still available. Later publications use the same trusted publisher configuration.

## Publish a release

1. Update `project.version` in `pyproject.toml` and merge the change to `main`.
2. Create a GitHub Release from that commit using a matching tag such as `v0.1.0`.
3. Publish the GitHub Release.
4. Approve the `pypi` environment deployment when prompted.

`.github/workflows/release.yml` then:

1. builds the wheel and source distribution with `uv build`;
2. validates their metadata with `twine check`;
3. passes the distributions to a separate least-privilege publishing job; and
4. uploads them to PyPI through `pypa/gh-action-pypi-publish` using short-lived OIDC credentials.

PyPI release filenames and versions are immutable. If an upload partially succeeds, publish a new version rather than attempting to overwrite the existing files.

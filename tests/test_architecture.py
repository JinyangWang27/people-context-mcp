"""Dependency guardrails for the hexagonal architecture."""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).parents[1] / "src" / "people_context"
PROJECT_PACKAGE = "people_context"
CORE_LAYER_DEPENDENCIES = {
    "domain": {"domain"},
    "ports": {"domain", "ports"},
    "app": {"app", "domain", "ports"},
}


def _module_name(path: Path) -> str:
    relative_path = path.relative_to(PACKAGE_ROOT.parent).with_suffix("")
    parts = list(relative_path.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _project_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    current_module = _module_name(path)
    type_checking_imports = {
        id(child)
        for node in ast.walk(tree)
        if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING"
        for child in ast.walk(node)
        if isinstance(child, (ast.Import, ast.ImportFrom))
    }

    for node in ast.walk(tree):
        if id(node) in type_checking_imports:
            continue
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names if alias.name.startswith(f"{PROJECT_PACKAGE}."))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                current_package = current_module.split(".")[:-1]
                module_parts = current_package[: len(current_package) - node.level + 1]
                if module:
                    module_parts.extend(module.split("."))
                module = ".".join(module_parts)
            if module == PROJECT_PACKAGE or module.startswith(f"{PROJECT_PACKAGE}."):
                imports.add(module)

    return imports


@pytest.mark.parametrize("layer", CORE_LAYER_DEPENDENCIES)
def test_core_layer_imports_only_allowed_project_layers(layer: str) -> None:
    """Keep concrete adapters and process concerns outside the core."""
    allowed_layers = CORE_LAYER_DEPENDENCIES[layer]
    violations: list[str] = []

    for path in sorted((PACKAGE_ROOT / layer).rglob("*.py")):
        for imported_module in sorted(_project_imports(path)):
            parts = imported_module.split(".")
            imported_layer = parts[1] if len(parts) > 1 else ""
            if imported_layer not in allowed_layers:
                violations.append(f"{path.relative_to(PACKAGE_ROOT)} -> {imported_module}")

    assert not violations, "Core dependency violations:\n" + "\n".join(violations)


def test_internal_project_imports_are_acyclic() -> None:
    """Prevent project modules from acquiring circular import dependencies."""
    paths = sorted(PACKAGE_ROOT.rglob("*.py"))
    modules = {_module_name(path): path for path in paths}
    graph: dict[str, set[str]] = defaultdict(set)

    for module, path in modules.items():
        for imported_module in _project_imports(path):
            candidate = imported_module
            while candidate not in modules and "." in candidate:
                candidate = candidate.rsplit(".", maxsplit=1)[0]
            if candidate in modules and candidate != module:
                graph[module].add(candidate)

    visited: set[str] = set()
    active: list[str] = []
    active_set: set[str] = set()

    def visit(module: str) -> None:
        if module in active_set:
            cycle_start = active.index(module)
            cycle = active[cycle_start:] + [module]
            pytest.fail("Internal import cycle: " + " -> ".join(cycle))
        if module in visited:
            return

        active.append(module)
        active_set.add(module)
        for dependency in sorted(graph[module]):
            visit(dependency)
        active.pop()
        active_set.remove(module)
        visited.add(module)

    for module in sorted(modules):
        visit(module)

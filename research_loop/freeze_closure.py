"""Fail-closed static audit of repository-local Python freeze dependencies.

Remote workflow locks are only meaningful when every local Python module that
an executable frozen input can import is frozen too.  This module computes that
closure without importing project code: it parses every reachable ``.py`` file
with :mod:`ast`, resolves repository-local absolute and relative imports, and
reports any reachable file omitted from ``freeze_inputs``.

The analysis is deliberately conservative.  Imports in functions, conditional
branches, and exception handlers count because they can execute in a remote
run.  The sole special case is an explicit ``if TYPE_CHECKING`` body, which is
not executable at runtime.  Dynamic imports cannot be proven statically and
remain outside this contract.
"""

from __future__ import annotations

import argparse
import ast
from collections import deque
from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any, Iterable, Mapping


class FreezeClosureError(RuntimeError):
    """The workflow freeze declaration cannot be audited or is not closed."""


@dataclass(frozen=True, order=True)
class ImportEdge:
    importer: str
    dependency: str


@dataclass(frozen=True)
class FreezeClosureAudit:
    spec: str
    declared_python: tuple[str, ...]
    reachable_python: tuple[str, ...]
    missing: tuple[str, ...]
    edges: tuple[ImportEdge, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "spec": self.spec,
            "declared_python": list(self.declared_python),
            "reachable_python": list(self.reachable_python),
            "missing": list(self.missing),
            "closed": not self.missing,
            "edges": [
                {"importer": edge.importer, "dependency": edge.dependency}
                for edge in self.edges
            ],
        }


class _RuntimeImportVisitor(ast.NodeVisitor):
    """Collect imports while excluding explicit type-checking-only bodies."""

    def __init__(self) -> None:
        self.nodes: list[ast.Import | ast.ImportFrom] = []

    @staticmethod
    def _is_type_checking(test: ast.expr) -> bool:
        return (
            isinstance(test, ast.Name) and test.id == "TYPE_CHECKING"
        ) or (
            isinstance(test, ast.Attribute)
            and test.attr == "TYPE_CHECKING"
            and isinstance(test.value, ast.Name)
            and test.value.id in {"typing", "t"}
        )

    def visit_If(self, node: ast.If) -> None:  # noqa: N802 - ast API name
        if self._is_type_checking(node.test):
            for statement in node.orelse:
                self.visit(statement)
            return
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        self.nodes.append(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        self.nodes.append(node)


def _safe_relative(value: str) -> str:
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise FreezeClosureError(
            f"freeze input must be repository-relative: {value!r}"
        )
    normalized = candidate.as_posix()
    if normalized in {"", "."}:
        raise FreezeClosureError(f"invalid freeze input: {value!r}")
    return normalized


def _module_context(relative_path: str) -> tuple[tuple[str, ...], bool]:
    path = PurePosixPath(relative_path)
    if path.suffix != ".py":
        raise FreezeClosureError(f"not a Python source path: {relative_path}")
    parts = path.with_suffix("").parts
    is_package = bool(parts and parts[-1] == "__init__")
    module = parts[:-1] if is_package else parts
    return tuple(module), is_package


def _package_prefixes(root: Path, module: tuple[str, ...], *, package: bool) -> list[str]:
    """Return existing package initializers executed while importing module."""
    limit = len(module) if package else max(0, len(module) - 1)
    result: list[str] = []
    for size in range(1, limit + 1):
        relative = PurePosixPath(*module[:size], "__init__.py").as_posix()
        if (root / relative).is_file():
            result.append(relative)
    return result


def _module_files(root: Path, module: tuple[str, ...]) -> list[str]:
    """Map one module name to local source plus executed package initializers."""
    if not module:
        return []
    package_path = PurePosixPath(*module, "__init__.py").as_posix()
    module_path = PurePosixPath(*module).with_suffix(".py").as_posix()
    if (root / package_path).is_file():
        return [*_package_prefixes(root, module, package=True)]
    if (root / module_path).is_file():
        return [*_package_prefixes(root, module, package=False), module_path]
    return []


def _absolute_base(
    node: ast.ImportFrom,
    *,
    importer_module: tuple[str, ...],
    importer_is_package: bool,
) -> tuple[str, ...] | None:
    named = tuple(node.module.split(".")) if node.module else ()
    if node.level == 0:
        return named
    package = importer_module if importer_is_package else importer_module[:-1]
    ascents = node.level - 1
    if ascents > len(package):
        return None
    return (*package[: len(package) - ascents], *named)


def _dependencies_for_import(
    root: Path,
    node: ast.Import | ast.ImportFrom,
    *,
    importer_module: tuple[str, ...],
    importer_is_package: bool,
) -> set[str]:
    dependencies: set[str] = set()
    if isinstance(node, ast.Import):
        for alias in node.names:
            dependencies.update(_module_files(root, tuple(alias.name.split("."))))
        return dependencies

    base = _absolute_base(
        node,
        importer_module=importer_module,
        importer_is_package=importer_is_package,
    )
    if base is None:
        return dependencies
    dependencies.update(_module_files(root, base))
    # ``from package import child`` asks the import machinery to resolve child
    # as a submodule when one exists.  Attribute imports simply add nothing.
    for alias in node.names:
        if alias.name != "*":
            dependencies.update(_module_files(root, (*base, alias.name)))
    return dependencies


def _local_dependencies(root: Path, relative_path: str) -> set[str]:
    source_path = root / relative_path
    try:
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=relative_path)
    except (OSError, SyntaxError, UnicodeError) as exc:
        raise FreezeClosureError(f"cannot parse {relative_path}: {exc}") from exc
    visitor = _RuntimeImportVisitor()
    visitor.visit(tree)
    module, is_package = _module_context(relative_path)
    dependencies: set[str] = set()
    for node in visitor.nodes:
        dependencies.update(
            _dependencies_for_import(
                root,
                node,
                importer_module=module,
                importer_is_package=is_package,
            )
        )
    dependencies.discard(relative_path)
    return dependencies


def audit_freeze_inputs(
    root: Path,
    *,
    spec_name: str,
    freeze_inputs: Iterable[str],
) -> FreezeClosureAudit:
    root = root.resolve()
    declared = tuple(sorted({_safe_relative(value) for value in freeze_inputs}))
    absent = tuple(path for path in declared if not (root / path).is_file())
    if absent:
        raise FreezeClosureError(f"declared freeze inputs do not exist: {list(absent)}")
    declared_python = tuple(path for path in declared if path.endswith(".py"))

    reachable = set(declared_python)
    pending = deque(declared_python)
    edges: set[ImportEdge] = set()
    while pending:
        importer = pending.popleft()
        for dependency in sorted(_local_dependencies(root, importer)):
            edges.add(ImportEdge(importer, dependency))
            if dependency not in reachable:
                reachable.add(dependency)
                pending.append(dependency)

    missing = tuple(sorted(reachable - set(declared_python)))
    return FreezeClosureAudit(
        spec=spec_name,
        declared_python=declared_python,
        reachable_python=tuple(sorted(reachable)),
        missing=missing,
        edges=tuple(sorted(edges)),
    )


def audit_workflow(root: Path, spec_path: Path) -> FreezeClosureAudit:
    root = root.resolve()
    resolved_spec = spec_path if spec_path.is_absolute() else root / spec_path
    try:
        spec: Mapping[str, Any] = json.loads(resolved_spec.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        raise FreezeClosureError(f"cannot read workflow {spec_path}: {exc}") from exc
    values = spec.get("freeze_inputs")
    if not isinstance(values, list) or not values or not all(
        isinstance(value, str) for value in values
    ):
        raise FreezeClosureError("workflow freeze_inputs must be a non-empty string list")
    try:
        spec_name = resolved_spec.resolve().relative_to(root).as_posix()
    except ValueError:
        spec_name = str(resolved_spec.resolve())
    return audit_freeze_inputs(root, spec_name=spec_name, freeze_inputs=values)


def assert_workflow_freeze_closed(root: Path, spec_path: Path) -> FreezeClosureAudit:
    audit = audit_workflow(root, spec_path)
    if audit.missing:
        importers: dict[str, list[str]] = {path: [] for path in audit.missing}
        for edge in audit.edges:
            if edge.dependency in importers:
                importers[edge.dependency].append(edge.importer)
        detail = "; ".join(
            f"{path} <- {','.join(sorted(importers[path]))}"
            for path in audit.missing
        )
        raise FreezeClosureError(
            f"workflow freeze_inputs omit reachable local Python dependencies: {detail}"
        )
    return audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        audit = assert_workflow_freeze_closed(args.root, args.spec)
    except BaseException as exc:
        print(f"freeze-closure error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(audit.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

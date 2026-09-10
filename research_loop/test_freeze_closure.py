from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from research_loop.freeze_closure import (
    FreezeClosureError,
    assert_workflow_freeze_closed,
    audit_workflow,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _spec(root: Path, freeze_inputs: list[str]) -> Path:
    path = root / "workflow.json"
    path.write_text(json.dumps({"freeze_inputs": freeze_inputs}), encoding="utf-8")
    return path


def test_lands_init_reexports_must_be_frozen() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        _write(
            root / "lands/__init__.py",
            "from .model import Thing\n"
            "from .world import World\n"
            "from .reachout import Session\n"
            "from .claims import Codec\n"
            "from .corpus import Corpus\n",
        )
        for name in ("model", "world", "reachout", "claims", "corpus"):
            _write(root / f"lands/{name}.py", "\n")
        spec = _spec(
            root,
            ["lands/__init__.py", "lands/model.py", "lands/world.py"],
        )
        audit = audit_workflow(root, spec)
        assert audit.missing == (
            "lands/claims.py",
            "lands/corpus.py",
            "lands/reachout.py",
        )
        try:
            assert_workflow_freeze_closed(root, spec)
        except FreezeClosureError as exc:
            assert "lands/reachout.py" in str(exc)
        else:
            raise AssertionError("incomplete lands package freeze was accepted")


def test_imports_inside_functions_and_transitive_omissions_are_found() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        _write(root / "app.py", "def load():\n    from pkg.worker import run\n")
        _write(root / "pkg/__init__.py", "\n")
        _write(root / "pkg/worker.py", "from .helper import help_me\n")
        _write(root / "pkg/helper.py", "\n")
        spec = _spec(root, ["app.py"])
        assert audit_workflow(root, spec).missing == (
            "pkg/__init__.py",
            "pkg/helper.py",
            "pkg/worker.py",
        )


def test_imported_package_initializers_are_part_of_closure() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        _write(root / "entry.py", "from outer.inner.worker import run\n")
        _write(root / "outer/__init__.py", "\n")
        _write(root / "outer/inner/__init__.py", "\n")
        _write(root / "outer/inner/worker.py", "\n")
        spec = _spec(root, ["entry.py", "outer/inner/worker.py"])
        assert audit_workflow(root, spec).missing == (
            "outer/__init__.py",
            "outer/inner/__init__.py",
        )


def test_explicit_type_checking_import_is_not_a_runtime_dependency() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        _write(
            root / "entry.py",
            "from typing import TYPE_CHECKING\n"
            "if TYPE_CHECKING:\n"
            "    from hidden import TypeOnly\n",
        )
        _write(root / "hidden.py", "\n")
        spec = _spec(root, ["entry.py"])
        assert_workflow_freeze_closed(root, spec)


def test_current_recurrent_workflow_freeze_is_transitively_closed() -> None:
    root = Path(__file__).resolve().parents[1]
    spec = root / "research_loop/workflows/recurrent_microdream_text_v0.remote.json"
    audit = assert_workflow_freeze_closed(root, spec)
    assert "lands/reachout.py" in audit.reachable_python
    assert "lands/claims.py" in audit.reachable_python
    assert "lands/corpus.py" in audit.reachable_python
    assert "research_loop/microdream_classification.py" in audit.reachable_python

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from research_loop.architecture_intake import (
    initialize_intake,
    record_human_ratification,
)
from research_loop.io import load_json
from research_loop.supervisor import WorkflowError, initialize, load_runtime, step
from research_loop.test_architecture_intake import (
    _advance_to_human,
    _base,
    _ratification,
    _write,
)


def _approved_intake(root: Path, authorized_scope: list[str]) -> Path:
    change_path, _, _, _, paths = _base(root)
    state_path = root / "intake.state.json"
    initialize_intake(root, change_path, state_path)
    _advance_to_human(root, state_path, paths)
    ratification_path = _ratification(root, state_path, paths["consensus"])
    ratification = load_json(ratification_path)
    ratification["authorized_scope"] = authorized_scope
    ratification["forbidden_scope"] = ["unreviewed scientific claim"]
    _write(ratification_path, ratification)
    record_human_ratification(root, state_path, ratification_path)
    return state_path


def _workflow(
    root: Path,
    *,
    state: str,
    requested_scope: list[str],
    name: str = "architecture-gated",
) -> Path:
    workflow_path = root / "workflow.json"
    _write(
        workflow_path,
        {
            "schema_version": 1,
            "name": name,
            "workspace": ".",
            "state_dir": ".supervisor",
            "architecture_intake": {
                "mode": "material_change",
                "state": state,
                "requested_scope": requested_scope,
            },
            "start": "mutation_or_gpu",
            "nodes": {
                "mutation_or_gpu": {
                    "kind": "command",
                    "argv": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; Path('executed.txt').write_text('ran')",
                    ],
                    "next": "done",
                },
                "done": {"kind": "end", "status": "complete"},
            },
        },
    )
    return workflow_path


def test_material_workflow_fails_closed_without_intake_state() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        workflow = _workflow(
            root,
            state="missing.state.json",
            requested_scope=["CPU acceptance tests"],
        )
        try:
            initialize(load_runtime(workflow))
        except WorkflowError as exc:
            assert "architecture intake authorization failed" in str(exc)
        else:
            raise AssertionError("material workflow initialized without an intake")
        assert not (root / "executed.txt").exists()


def test_forged_approval_flags_without_ratification_fail_closed() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        change_path, _, _, _, paths = _base(root)
        intake_state = root / "intake.state.json"
        initialize_intake(root, change_path, intake_state)
        _advance_to_human(root, intake_state, paths)
        forged = load_json(intake_state)
        forged["phase"] = "human_approved"
        forged["human_required"] = False
        forged["implementation_authorized"] = True
        _write(intake_state, forged)
        workflow = _workflow(
            root,
            state=intake_state.name,
            requested_scope=["CPU acceptance tests"],
        )
        try:
            initialize(load_runtime(workflow))
        except WorkflowError as exc:
            assert "architecture intake authorization failed" in str(exc)
        else:
            raise AssertionError("forged intake flags initialized a workflow")
        assert not (root / "executed.txt").exists()


def test_requested_scope_must_be_exact_authorized_subset() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        intake_state = _approved_intake(root, ["CPU acceptance tests"])
        workflow = _workflow(
            root,
            state=intake_state.name,
            requested_scope=["CPU acceptance tests", "GPU science run"],
        )
        try:
            initialize(load_runtime(workflow))
        except WorkflowError as exc:
            assert "requested architecture scope is not authorized" in str(exc)
            assert "GPU science run" in str(exc)
        else:
            raise AssertionError("over-broad workflow scope was accepted")
        assert not (root / "executed.txt").exists()


def test_scoped_material_workflow_binds_authorization_and_runs() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        intake_state = _approved_intake(
            root, ["architecture delta implementation", "CPU acceptance tests"]
        )
        workflow = _workflow(
            root,
            state=intake_state.name,
            requested_scope=["CPU acceptance tests"],
        )
        runtime = load_runtime(workflow)
        state = initialize(runtime)
        binding = state["architecture_authorization"]
        assert binding["mode"] == "material_change"
        assert binding["intake_state_sha256"]
        assert binding["ratification_sha256"]
        assert binding["workflow_sha256"]
        assert binding["requested_scope"] == ["CPU acceptance tests"]
        assert len(binding["artifact_bindings"]) == 6
        state = step(runtime, state)
        assert state["status"] == "running"
        assert state["current"] == "done"
        assert (root / "executed.txt").read_text(encoding="utf-8") == "ran"


def test_post_initialize_intake_or_workflow_mutation_pauses_before_node() -> None:
    for mutation in ("intake_state", "ratification", "evidence", "workflow"):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake_state = _approved_intake(root, ["CPU acceptance tests"])
            workflow = _workflow(
                root,
                state=intake_state.name,
                requested_scope=["CPU acceptance tests"],
                name=f"stale-{mutation}",
            )
            runtime = load_runtime(workflow)
            state = initialize(runtime)
            if mutation == "intake_state":
                value = load_json(intake_state)
                value["history"].append({"at": "later", "transition": "forged"})
                _write(intake_state, value)
            elif mutation == "ratification":
                ratification_path = root / "ratification.json"
                value = load_json(ratification_path)
                value["decision_statement"] += " changed"
                _write(ratification_path, value)
            elif mutation == "evidence":
                (root / "human-approval.txt").write_text("changed\n", encoding="utf-8")
            else:
                value = load_json(workflow)
                value["max_steps"] = 99
                _write(workflow, value)
            state = step(runtime, state)
            assert state["status"] == "paused", mutation
            assert "architecture authorization failed" in state["last_result"]["reason"]
            assert not (root / "executed.txt").exists()


def test_repository_legacy_workflow_mode_is_explicit() -> None:
    workflow = Path(__file__).parent / "workflows" / "dream_ladder_v5.json"
    runtime = load_runtime(workflow)
    assert runtime.workflow["architecture_intake"] == {
        "mode": "legacy_no_material_change"
    }


def test_repository_workflow_cannot_bypass_intake_by_omission() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        workflows = root / "research_loop" / "workflows"
        workflows.mkdir(parents=True)
        workflow = workflows / "undeclared.json"
        workflow.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "name": "undeclared",
                    "workspace": "../..",
                    "state_dir": ".supervisor",
                    "start": "done",
                    "nodes": {"done": {"kind": "end", "status": "complete"}},
                }
            ),
            encoding="utf-8",
        )
        try:
            load_runtime(workflow)
        except WorkflowError as exc:
            assert "must explicitly declare architecture_intake" in str(exc)
        else:
            raise AssertionError("repository workflow bypassed intake by omission")

from __future__ import annotations

import copy
import json
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from research_loop.architecture_deliberation import (
    DeliberationError,
    initialize_deliberation,
    load_deliberation_runtime,
    run_to_human_required,
    status,
)
from research_loop.architecture_intake import IntakeError, validate_authorized_intake
from research_loop.io import atomic_write_json, load_json, sha256_file
from research_loop.test_architecture_intake import _base, _ratification
from research_loop.architecture_intake import record_human_ratification


PACKAGE_DIR = Path(__file__).parent


def _install_resources(root: Path) -> None:
    for relative in [
        *(f"prompts/{Path(spec).name}" for spec in [
            "architecture_advocate.md",
            "architecture_systems_interpreter.md",
            "architecture_benchmark_interpreter.md",
            "architecture_adversarial_reviewer.md",
            "architecture_adjudicator.md",
        ]),
        *(f"schemas/{name}" for name in [
            "architecture_change.schema.json",
            "architecture_interpretation.schema.json",
            "architecture_critique.schema.json",
            "architecture_consensus.schema.json",
        ]),
    ]:
        source = PACKAGE_DIR / relative
        destination = root / "research_loop" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _workflow(root: Path, *, fallback: bool = False) -> Path:
    _install_resources(root)
    executors = [{"provider": "codex", "timeout_sec": 30}]
    if fallback:
        executors.append({"provider": "fable_mailbox", "timeout_sec": 30})
    value = {
        "schema_version": 1,
        "workflow_kind": "architecture_deliberation",
        "name": "test-deliberation",
        "workspace": ".",
        "change_id": "recurrent-dream-1",
        "directive_file": "context.md",
        "context_files": [],
        "output_dir": "generated",
        "state_path": ".state/deliberation.json",
        "intake_state_path": "generated/intake.state.json",
        "run_dir": ".state/runs",
        "roles": {
            role: {"executors": copy.deepcopy(executors)}
            for role in ("advocate", "systems", "benchmark", "critique", "consensus")
        },
    }
    path = root / "workflow.json"
    _write(path, value)
    return path


class FakeExecutor:
    def __init__(
        self,
        root: Path,
        *,
        invalid: set[tuple[str, str]] | None = None,
        consensus_recommendation: str = "proceed_to_implementation",
    ):
        self.root = root
        self.invalid = invalid or set()
        self.consensus_recommendation = consensus_recommendation
        self.calls: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def __call__(
        self,
        role: str,
        node: dict[str, Any],
        workspace: Path,
        output_dir: Path,
        timeout_sec: int,
    ) -> tuple[int, dict[str, Any] | None]:
        del workspace, output_dir, timeout_sec
        with self._lock:
            self.calls.append({
                "role": role,
                "provider": node["provider"],
                "context_files": list(node["context_files"]),
                "started": time.monotonic(),
            })
            call_index = len(self.calls) - 1
        if role in {"systems", "benchmark"}:
            time.sleep(0.03)
        if (role, node["provider"]) in self.invalid:
            return 0, {"not": "the required schema"}
        value = self._artifact(role)
        with self._lock:
            self.calls[call_index]["finished"] = time.monotonic()
        return 0, value

    def _artifact(self, role: str) -> dict[str, Any]:
        generated = self.root / "generated"
        if role == "advocate":
            return load_json(self.root / "change.json")
        if role in {"systems", "benchmark"}:
            source = (
                self.root / "interpretation.json"
                if role == "systems"
                else self.root / "benchmark-interpretation.json"
            )
            value = load_json(source)
            value["architecture_change_sha256"] = sha256_file(generated / "change.json")
            value["interpretation_id"] = f"recurrent-dream-1.{role}"
            value["perspective"] = role
            return value
        systems = generated / "interpretation_systems.json"
        benchmark = generated / "interpretation_benchmark.json"
        if role == "critique":
            value = load_json(self.root / "critique.json")
            value["architecture_change_sha256"] = sha256_file(generated / "change.json")
            value["interpretation_hashes"] = [
                {
                    "interpretation_id": "recurrent-dream-1.benchmark",
                    "sha256": sha256_file(benchmark),
                },
                {
                    "interpretation_id": "recurrent-dream-1.systems",
                    "sha256": sha256_file(systems),
                },
            ]
            return value
        if role == "consensus":
            value = load_json(self.root / "consensus.json")
            value["recommendation"] = self.consensus_recommendation
            value["architecture_change_sha256"] = sha256_file(generated / "change.json")
            value["interpretation_hashes"] = [
                {
                    "interpretation_id": "recurrent-dream-1.benchmark",
                    "sha256": sha256_file(benchmark),
                },
                {
                    "interpretation_id": "recurrent-dream-1.systems",
                    "sha256": sha256_file(systems),
                },
            ]
            value["critique_sha256"] = sha256_file(generated / "critique.json")
            return value
        raise AssertionError(role)


def _fixture(directory: str, *, fallback: bool = False):
    root = Path(directory)
    _base(root)
    workflow = _workflow(root, fallback=fallback)
    runtime = load_deliberation_runtime(workflow)
    return root, runtime


def test_full_runner_reaches_human_required_and_never_authorizes() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root, runtime = _fixture(directory)
        fake = FakeExecutor(root)
        final = run_to_human_required(runtime, executor=fake)
        assert final["phase"] == "human_required"
        assert final["status"] == "human_required"
        assert final["human_required"] is True
        assert final["implementation_authorized"] is False
        intake = load_json(root / "generated" / "intake.state.json")
        assert intake["phase"] == "human_required"
        assert intake["implementation_authorized"] is False
        try:
            validate_authorized_intake(root, root / "generated" / "intake.state.json")
        except IntakeError as exc:
            assert "not human_approved" in str(exc)
        else:
            raise AssertionError("model consensus authorized implementation")


def test_rework_verdict_is_preserved_and_cannot_be_human_routed_to_implementation() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root, runtime = _fixture(directory)
        final = run_to_human_required(
            runtime,
            executor=FakeExecutor(root, consensus_recommendation="rework"),
        )
        assert final["phase"] == "human_required"
        consensus_path = root / "generated" / "consensus.json"
        assert load_json(consensus_path)["recommendation"] == "rework"
        intake_path = root / "generated" / "intake.state.json"
        ratification = _ratification(root, intake_path, consensus_path)
        try:
            record_human_ratification(root, intake_path, ratification)
        except IntakeError as exc:
            assert "not releasable" in str(exc)
            assert "rework" in str(exc)
        else:
            raise AssertionError("human routing overrode a preserved rework verdict")
        assert load_json(intake_path)["phase"] == "human_required"


def test_interpreters_are_parallel_and_context_isolated() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root, runtime = _fixture(directory)
        fake = FakeExecutor(root)
        run_to_human_required(runtime, executor=fake)
        calls = {item["role"]: item for item in fake.calls}
        systems = calls["systems"]
        benchmark = calls["benchmark"]
        assert systems["started"] < benchmark["finished"]
        assert benchmark["started"] < systems["finished"]
        assert not any("interpretation_benchmark" in path for path in systems["context_files"])
        assert not any("interpretation_systems" in path for path in benchmark["context_files"])
        assert calls["critique"]["context_files"] == [
            "generated/change.json",
            "generated/interpretation_systems.json",
            "generated/interpretation_benchmark.json",
            "context.md",
        ]


def test_once_is_resumable_across_every_stage() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root, runtime = _fixture(directory)
        fake = FakeExecutor(root)
        phases = []
        for _ in range(4):
            state = run_to_human_required(runtime, executor=fake, once=True)
            phases.append(state["phase"])
        assert phases == [
            "interpretations_pending", "critique_pending", "consensus_pending", "human_required"
        ]
        final = run_to_human_required(runtime, executor=fake)
        assert final["phase"] == "human_required"
        assert len(fake.calls) == 5


def test_crash_window_adopts_exact_validated_interpretation_without_regeneration() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root, runtime = _fixture(directory)
        fake = FakeExecutor(root)
        run_to_human_required(runtime, executor=fake, once=True)
        # Simulate a hard crash after canonical promotion and before the intake
        # transition/state save.
        atomic_write_json(
            root / "generated" / "interpretation_systems.json",
            fake._artifact("systems"),
        )
        fake.calls.clear()
        state = run_to_human_required(runtime, executor=fake, once=True)
        assert state["phase"] == "critique_pending"
        assert [call["role"] for call in fake.calls] == ["benchmark"]
        intake = load_json(root / "generated" / "intake.state.json")
        assert len([
            key for key in intake["artifacts"]
            if key.startswith("architecture_interpretation:")
        ]) == 2


def test_invalid_primary_executor_falls_back_and_records_both_attempts() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root, runtime = _fixture(directory, fallback=True)
        fake = FakeExecutor(root, invalid={("advocate", "codex")})
        state = run_to_human_required(runtime, executor=fake, once=True)
        assert state["phase"] == "interpretations_pending"
        attempts = [item for item in state["attempts"] if item["role"] == "advocate"]
        assert [item["status"] for item in attempts] == ["failed", "validated"]
        assert [item["provider"] for item in attempts] == ["codex", "fable_mailbox"]


def test_two_bad_interpreters_fail_closed_before_critique() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root, runtime = _fixture(directory)
        fake = FakeExecutor(root, invalid={("benchmark", "codex")})
        run_to_human_required(runtime, executor=fake, once=True)
        state = run_to_human_required(runtime, executor=fake, once=True)
        assert state["status"] == "paused"
        assert state["phase"] == "interpretations_pending"
        assert any(
            item["role"] == "benchmark" and item["status"] == "failed"
            for item in state["attempts"]
        )
        assert not (root / "generated" / "critique.json").exists()
        intake = load_json(root / "generated" / "intake.state.json")
        assert intake["phase"] == "collecting_interpretations"
        assert not any(key.startswith("architecture_interpretation:") for key in intake["artifacts"])


def test_source_mutation_fails_closed_before_any_agent_call() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root, runtime = _fixture(directory)
        initialize_deliberation(runtime)
        (root / "context.md").write_text("mutated directive\n", encoding="utf-8")
        fake = FakeExecutor(root)
        try:
            run_to_human_required(runtime, executor=fake)
        except DeliberationError as exc:
            assert "directive or durable context changed" in str(exc)
        else:
            raise AssertionError("mutated directive was accepted")
        assert fake.calls == []


def test_generated_artifact_mutation_fails_closed_on_status() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root, runtime = _fixture(directory)
        run_to_human_required(runtime, executor=FakeExecutor(root))
        (root / "generated" / "interpretation_systems.json").write_text(
            "{}\n", encoding="utf-8"
        )
        try:
            status(runtime)
        except DeliberationError as exc:
            assert "intake state is invalid" in str(exc)
        else:
            raise AssertionError("mutated deliberation artifact was accepted")


def test_workflow_rejects_duplicate_directive_context_and_unknown_executor_fields() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        _base(root)
        workflow = _workflow(root)
        value = load_json(workflow)
        value["context_files"] = ["context.md"]
        _write(workflow, value)
        try:
            load_deliberation_runtime(workflow)
        except DeliberationError as exc:
            assert "must be unique" in str(exc)
        else:
            raise AssertionError("duplicate directive/context was accepted")

        value["context_files"] = []
        value["roles"]["advocate"]["executors"][0]["shell"] = "arbitrary"
        _write(workflow, value)
        try:
            load_deliberation_runtime(workflow)
        except DeliberationError as exc:
            assert "unsupported fields" in str(exc)
        else:
            raise AssertionError("arbitrary executor field was accepted")


def test_existing_unowned_artifacts_are_not_adopted() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root, runtime = _fixture(directory)
        (root / "generated").mkdir()
        (root / "generated" / "change.json").write_text("{}\n", encoding="utf-8")
        try:
            initialize_deliberation(runtime)
        except DeliberationError as exc:
            assert "exist without runner state" in str(exc)
        else:
            raise AssertionError("unowned artifact was adopted")


def test_valid_manual_proposal_is_adopted_without_rewriting_or_advocate_call() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root, runtime = _fixture(directory)
        canonical = root / "generated" / "change.json"
        canonical.parent.mkdir()
        canonical.write_bytes((root / "change.json").read_bytes())
        before = canonical.read_bytes()
        before_sha = sha256_file(canonical)
        fake = FakeExecutor(root)

        state = run_to_human_required(runtime, executor=fake, once=True)

        assert state["phase"] == "interpretations_pending"
        assert fake.calls == []
        assert canonical.read_bytes() == before
        assert sha256_file(canonical) == before_sha
        assert state["artifacts"]["advocate"] == {
            "path": "generated/change.json",
            "sha256": before_sha,
        }
        intake = load_json(root / "generated" / "intake.state.json")
        assert intake["phase"] == "collecting_interpretations"
        assert intake["artifacts"]["architecture_change"]["sha256"] == before_sha


def test_manual_proposal_adoption_ignores_unrelated_shared_run_directory() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root, runtime = _fixture(directory)
        unrelated = root / ".state" / "runs" / "prior-unrelated-run"
        unrelated.mkdir(parents=True)
        (unrelated / "result.json").write_text("{}\n", encoding="utf-8")
        canonical = root / "generated" / "change.json"
        canonical.parent.mkdir()
        canonical.write_bytes((root / "change.json").read_bytes())
        before = canonical.read_bytes()

        state = run_to_human_required(
            runtime, executor=FakeExecutor(root), once=True
        )

        assert state["phase"] == "interpretations_pending"
        assert canonical.read_bytes() == before
        assert state["artifacts"]["advocate"]["sha256"] == sha256_file(canonical)


def test_manual_proposal_conflicts_fail_closed_before_model_or_mutation() -> None:
    for conflict in ("downstream", "intake"):
        with tempfile.TemporaryDirectory() as directory:
            root, runtime = _fixture(directory)
            canonical = root / "generated" / "change.json"
            canonical.parent.mkdir()
            canonical.write_bytes((root / "change.json").read_bytes())
            before = canonical.read_bytes()
            if conflict == "downstream":
                (root / "generated" / "interpretation_systems.json").write_text(
                    "{}\n", encoding="utf-8"
                )
            else:
                (root / "generated" / "intake.state.json").write_text(
                    "{}\n", encoding="utf-8"
                )
            fake = FakeExecutor(root)
            try:
                run_to_human_required(runtime, executor=fake)
            except DeliberationError as exc:
                assert "refuse ambiguous adoption" in str(exc)
            else:
                raise AssertionError("conflicting manual artifacts were adopted")
            assert fake.calls == []
            assert not runtime.state_path.exists()
            assert canonical.read_bytes() == before


def test_stale_manual_proposal_context_fails_before_model_call() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root, runtime = _fixture(directory)
        canonical = root / "generated" / "change.json"
        canonical.parent.mkdir()
        proposal = load_json(root / "change.json")
        proposal["context_files"][0]["sha256"] = "0" * 64
        _write(canonical, proposal)
        fake = FakeExecutor(root)
        try:
            run_to_human_required(runtime, executor=fake)
        except DeliberationError as exc:
            assert "context hash mismatch" in str(exc)
        else:
            raise AssertionError("stale manual proposal was adopted")
        assert fake.calls == []
        assert not runtime.state_path.exists()


def test_status_on_clean_workflow_is_observational() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root, runtime = _fixture(directory)
        result = status(runtime)
        assert result["status"] == "uninitialized"
        assert result["phase"] == "advocate_pending"
        assert not runtime.state_path.exists()
        assert not (root / "generated" / "intake.state.json").exists()

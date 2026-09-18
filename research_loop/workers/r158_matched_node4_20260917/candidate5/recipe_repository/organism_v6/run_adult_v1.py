"""Bounded parent-free adult running/shadow execution, not a scientific claim.

Only the current strict reasoning nursery writer is supported. Compiler or
task-exposed admission is incompatible with its UNEXPOSED-only receipt contract.
The initial corpus is replayed as already-admitted child targets; childhood
source bytes are audit evidence only, never adult context or retrieval. No new
lineage manifest or clean-ancestry declaration is issued. Neutral ON/OFF probes,
resumption, parent services, lessons, reflection and clone groups are absent.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path
import subprocess
import sys

from . import adult_controls as adult
from . import life_lineage as lineage
from . import nursery_selection_receipt as selection
from . import preschool_reasoning as writer
from . import run_life_v2 as nursery
from . import train_adapter
from .batch_loop import driver_class_for, run_episodes_batch
from .ledger import Ledger
from .model_backend import configured_generation_identity
from .reasoning_gym_gym import ReasoningGymGym


class UnsupportedAdultInterface(ValueError):
    pass


@dataclass(frozen=True)
class AdultRunSpec:
    life_dir: str
    mode: str
    lineage_root: str
    manifest_path: str
    expected_manifest_sha256: str
    initial_adapter_dir: str
    initial_corpus_path: str
    model_dir: str
    expected_model_id: str
    expected_model_files: dict
    episode_ids: list[str]
    seed: int
    train_seed: int
    sleep_every: int
    budget_ticks: int
    wake_batch: int
    note_after_max_tokens: int = 100
    min_items: int = 64
    base_lr: float = 1e-4


@dataclass(frozen=True)
class TrainingRequest:
    model_dir: str
    corpus_path: str
    output_dir: str
    gate_receipt_path: str
    expected_gate_sha256: str
    previous_manifest_sha256: str
    trainer_receipt_path: str
    rank: int
    seed: int
    lr: float
    epochs: int = 3


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _publish(path, value):
    return lineage._write(Path(path), writer._encoded(value))


def _read(path):
    return lineage._json(lineage._read(Path(path)))


class _AdultLedger(Ledger):
    def recall(self, query, k=6):
        return []


class _AdultSlot(writer.PostOutcomeSlot):
    def __init__(self, occurrence_floor, **kwargs):
        super().__init__(**kwargs)
        self.occurrence_floor = occurrence_floor

    def reserve_occurrences(self, drivers, ledger):
        import fcntl
        with open(ledger.path, "a+") as locked:
            fcntl.flock(locked, fcntl.LOCK_EX)
            indices = [row["occurrence_index"] for row in ledger.rows() if "occurrence_index" in row]
            _require(all(type(index) is int and index > 0 for index in indices), "invalid adult occurrence")
            next_index = max([self.occurrence_floor, *indices]) + 1
            for driver in drivers:
                occurrence = f"{driver.ep.eid}#occ{next_index}"
                ledger.append(dict(kind="episode_occurrence", episode_id=driver.ep.eid,
                    occurrence_id=occurrence, occurrence_index=next_index, slot_kind=self.kind))
                driver.occurrence_id = occurrence
                driver.occurrence_index = next_index
                next_index += 1
            os.fsync(locked.fileno())


def _identity(model, control, adapter):
    expected = configured_generation_identity(control.model_dir, adapter)
    _require(model.generation_identity() == expected, "actual backend identity mismatch")
    adult.select_adapter(control)


class _CheckedBackend:
    def __init__(self, model, control, adapter):
        self.model = model
        self.expected = configured_generation_identity(control.model_dir, adapter)

    def generation_identity(self):
        _require(self.model.generation_identity() == self.expected, "backend changed during generation")
        return dict(self.expected)

    def batch(self, prompts, **kwargs):
        self.generation_identity()
        outputs = self.model.batch(prompts, **kwargs)
        self.generation_identity()
        _require(isinstance(outputs, (list, tuple)) and len(outputs) == len(prompts)
                 and all(isinstance(output, str) for output in outputs), "incomplete generation batch")
        return outputs


def _initial_checkpoint(control):
    startup = json.loads(control.startup_json)
    return (Path(startup["lineage_root"]) / startup["manifest_path"]).parent


def _replay(control, admission_dir, sleep_dir, previous_pin):
    """Compose existing admissions; never infer eligibility from candidate bytes."""
    initial = _initial_checkpoint(control)
    segments = [(initial / "ledger.jsonl", initial / "corpus.json", initial / "gate_receipt.json"),
                (admission_dir / "reasoning_ledger.jsonl", admission_dir / "corpus.json",
                 admission_dir / "gate_receipt.json")]
    all_lines, items, admissions, provenance = [], [], [], []
    executions = set()
    for ledger_path, corpus_path, gate_path in segments:
        ledger_bytes = lineage._read(ledger_path)
        corpus_bytes = lineage._read(corpus_path)
        gate_bytes = lineage._read(gate_path)
        gate = lineage._json(gate_bytes)
        lineage._admissions(ledger_bytes, corpus_bytes, gate_bytes, gate["previous_manifest_sha256"])
        lines = ledger_bytes.splitlines(keepends=True)
        offset = len(all_lines)
        identifiers = {row["execution_id"] for row in map(lineage._json, lines) if row["kind"] == "act"}
        _require(not identifiers & executions, "childhood/adult execution identity collision")
        executions.update(identifiers)
        for item, admission in zip(lineage._json(corpus_bytes)["corpus"], gate["admissions"]):
            _require(item not in items, "duplicate replay item across initial/adult corpora")
            items.append(item)
            admissions.append(dict(admission, record_line=admission["record_line"] + offset,
                                   source_line=admission["source_line"] + offset))
        all_lines.extend(lines)
        provenance.append(dict(ledger_path=str(ledger_path), ledger_sha256=lineage._digest(ledger_bytes),
                               corpus_path=str(corpus_path), corpus_sha256=lineage._digest(corpus_bytes),
                               gate_path=str(gate_path), gate_sha256=lineage._digest(gate_bytes)))
    corpus = dict(recipe=lineage.RECIPE, corpus=items, principles=[],
                  n_new=_read(admission_dir / "corpus.json")["n_new"], n_dropped_legacy=0)
    corpus_bytes = writer._encoded(corpus)
    ledger_bytes = b"".join(all_lines)
    receipt = dict(schema_version=1, recipe=lineage.RECIPE, decision="ADMIT",
                   exposure_status="UNEXPOSED", previous_manifest_sha256=previous_pin,
                   ledger_sha256=lineage._digest(ledger_bytes), corpus_sha256=lineage._digest(corpus_bytes),
                   admissions=admissions)
    gate_bytes = writer._encoded(receipt)
    lineage._admissions(ledger_bytes, corpus_bytes, gate_bytes, previous_pin)
    _require(set(adult.initial_prior(control)) <= set(items), "initial prior lost")
    lineage._write(sleep_dir / "training_source_audit.jsonl", ledger_bytes)
    lineage._write(sleep_dir / "corpus.json", corpus_bytes)
    lineage._write(sleep_dir / "gate_receipt.json", gate_bytes)
    _publish(sleep_dir / "replay_sources.json", dict(sources=provenance,
             policy="initial child corpus plus cumulative admitted adult records; audit only, never context"))


def _verify_training(control, sleep_dir, adapter, request):
    nursery.validate_clean_training(adapter, rank=request.rank, seed=request.seed, lr=request.lr)
    corpus = lineage._read(sleep_dir / "corpus.json")
    gate = lineage._read(sleep_dir / "gate_receipt.json")
    _require(lineage._digest(gate) == request.expected_gate_sha256, "training changed gate inputs")
    lineage._admissions(lineage._read(sleep_dir / "training_source_audit.jsonl"),
                        corpus, gate, request.previous_manifest_sha256)
    files = {name: (adapter / name, lineage._hash_file(adapter / name)) for name in
             ("adapter_config.json", "adapter_model.safetensors", "adapter_model.bin")
             if (adapter / name).exists()}
    lineage._trainer_evidence(lineage._read(request.trainer_receipt_path), gate, corpus,
                             request.previous_manifest_sha256, files,
                             lineage._read(adapter / "train_meta.json"))
    adult.select_adapter(control)


def run_adult(spec, *, gym, backend_factory, trainer):
    """Run a finite fresh life; inject only model lifetime and actual trainer boundaries.

    backend_factory(model_dir, adapter_dir) must be a context manager which fully
    closes its backend. trainer(TrainingRequest) must execute the nursery writer
    and emit its actual row-linked receipt. No caller-supplied gate verdict or
    eligibility callback exists. Pins must be independently trusted externally.
    """
    _require(isinstance(spec, AdultRunSpec), "expected AdultRunSpec")
    if not isinstance(gym, ReasoningGymGym) or gym.strict_verifier is not True:
        raise UnsupportedAdultInterface("only strict reasoning nursery admission is supported; not compiler/task-exposed")
    for name in ("sleep_every", "budget_ticks", "wake_batch", "note_after_max_tokens"):
        value = getattr(spec, name)
        _require(type(value) is int and value > 0, "invalid " + name)
    _require(type(spec.min_items) is int and spec.min_items >= 64, "nursery minimum remains 64")
    _require(all(type(seed) is int and 0 <= seed < 2**31 for seed in (spec.seed, spec.train_seed)),
             "explicit valid wake/training seeds required")
    _require(type(spec.base_lr) in (int, float) and math.isfinite(spec.base_lr) and spec.base_lr > 0,
             "invalid nursery learning rate")
    _require(isinstance(spec.episode_ids, list) and spec.episode_ids
             and all(isinstance(episode, str) for episode in spec.episode_ids)
             and len(set(spec.episode_ids)) == len(spec.episode_ids), "explicit unique training IDs required")
    _require(all(gym.split_of(episode) == "train" for episode in spec.episode_ids), "held-out adult training ID")
    _require(bool(gym.canary_set()), "actual canary cannot be empty")
    expected_runtime = lineage._absolute(spec.lineage_root) / "birth/model"
    _require(lineage._absolute(spec.model_dir) == expected_runtime, "actual model path must be pinned runtime")
    lineage._base_inputs(spec.model_dir, spec.expected_model_files, spec.expected_model_id)
    config = dict(asdict(spec), adult_mode=spec.mode, arm="B", gym="reasoning_gym", rank=8,
                  epochs=3, wake_max_tokens=400, canary=selection.evaluation_config(gym),
                  gym_configuration=gym.cfg)
    control = adult.prepare_adult(spec.life_dir, mode=spec.mode, startup_config=config,
        lineage_root=spec.lineage_root, manifest_path=spec.manifest_path,
        expected_manifest_sha256=spec.expected_manifest_sha256,
        initial_adapter_dir=spec.initial_adapter_dir, initial_corpus_path=spec.initial_corpus_path)
    life = Path(control.life_dir)
    admission_root = life / "admission_runs"
    lineage._mkdir(admission_root)
    ledger = _AdultLedger(str(life / "ledger.jsonl"))
    Path(ledger.path).touch(exist_ok=False)
    initial_rows = [lineage._json(line) for line in lineage._read(
        _initial_checkpoint(control) / "ledger.jsonl").splitlines(keepends=True)]
    occurrence_floor = max((row.get("occurrence_index", 0) for row in initial_rows), default=0)
    slot = _AdultSlot(occurrence_floor, max_tokens=spec.note_after_max_tokens)
    bootstrap = adult.wake_context(control, gym.birth_prompt())
    outcomes = []
    try:
        for start in range(0, len(spec.episode_ids), spec.sleep_every):
            checkpoint = min(start + spec.sleep_every, len(spec.episode_ids))
            selected_adapter = adult.select_adapter(control)
            with backend_factory(control.model_dir, selected_adapter) as model:
                _identity(model, control, selected_adapter)
                checked = _CheckedBackend(model, control, selected_adapter)
                for offset in range(start, checkpoint, spec.wake_batch):
                    ids = spec.episode_ids[offset:min(offset + spec.wake_batch, checkpoint)]
                    run_episodes_batch(checked, gym,
                        [gym.episode_from_id(episode, spec.budget_ticks) for episode in ids],
                        bootstrap, ledger, spec.budget_ticks, log=lambda message: None,
                        gen_seed=1000 + spec.seed, driver_cls=driver_class_for(gym), note_after=slot)
                _identity(model, control, selected_adapter)
            rows = ledger.rows()
            nursery.assert_split_hygiene(gym, rows)
            _require(not any(row["kind"] == "parent_turn" for row in rows), "parent is forbidden in adult ledger")
            sleep_dir = life / f"sleep_{checkpoint:04d}"
            admission_dir = admission_root / sleep_dir.name
            lineage._mkdir(sleep_dir)
            lineage._mkdir(admission_dir)
            report = writer.gate_sleep(rows, str(admission_root), str(admission_dir), "enforce",
                min_items=spec.min_items, ledger_path=ledger.path,
                previous_manifest_sha256=spec.expected_manifest_sha256, exposure_status="UNEXPOSED")
            if report["training_skipped"]:
                outcome = dict(checkpoint=checkpoint, status="SKIPPED_INSUFFICIENT_RECORDS",
                               selected_adapter=adult.select_adapter(control))
                _publish(sleep_dir / "skipped.json", outcome)
                outcomes.append(outcome)
                continue
            _replay(control, admission_dir, sleep_dir, spec.expected_manifest_sha256)
            stage, candidate = sleep_dir / "adapter.train", sleep_dir / "adapter"
            request = TrainingRequest(control.model_dir, str(sleep_dir / "corpus.json"), str(stage),
                str(sleep_dir / "gate_receipt.json"), lineage._hash_file(sleep_dir / "gate_receipt.json"),
                spec.expected_manifest_sha256, str(sleep_dir / "trainer_receipt.json"), 8,
                spec.train_seed, spec.base_lr)
            train_adapter.load_gate_binding(request.gate_receipt_path, request.expected_gate_sha256,
                request.previous_manifest_sha256, lineage._read(request.corpus_path))
            trainer(request)
            _verify_training(control, sleep_dir, stage, request)
            nursery.promote_trained_adapter(str(stage), str(candidate))
            _verify_training(control, sleep_dir, candidate, request)
            arguments = dict(candidate_dir=str(candidate), corpus_path=str(sleep_dir / "corpus.json"))
            key = adult.candidate_key(control, checkpoint, **arguments)
            canary_config = config["canary"]
            _publish(sleep_dir / "canary_key.json", dict(candidate_key=key, config=canary_config))
            with backend_factory(control.model_dir, str(candidate)) as model:
                _identity(model, control, str(candidate))
                checked = _CheckedBackend(model, control, str(candidate))
                recorder = selection.SelectionRecorder(checked, model_input=control.model_dir,
                    adapter_dir=str(candidate), config=canary_config,
                    previous_manifest_sha256=spec.expected_manifest_sha256)
                accepted, rate = nursery.format_canary(checked, gym, selection=recorder)
                receipt = recorder.write(sleep_dir / "canary_selection", ok=accepted, rate=rate)
            _require(adult.candidate_key(control, checkpoint, **arguments) == key, "candidate changed during actual canary")
            selection.verify_selection(receipt["receipt_path"], expected_receipt_sha256=receipt["receipt_sha256"],
                adapter_dir=str(candidate), expected_model_input=control.model_dir,
                expected_adapter_input=str(candidate), expected_config=canary_config,
                previous_manifest_sha256=spec.expected_manifest_sha256, require_acceptance=False)
            _verify_training(control, sleep_dir, candidate, request)
            decision = adult.record_decision(control, checkpoint, **arguments, evaluated_key=key,
                                             accepted=accepted, reason="OK" if accepted else "CANARY")
            outcomes.append(dict(status="DECIDED", **asdict(decision)))
        latest = adult.select_adapter(control)
        with backend_factory(control.model_dir, latest) as model:
            _identity(model, control, latest)
        result = dict(mode=spec.mode, selected_adapter=latest, checkpoints=outcomes,
                      scope="parent-free reasoning adult; no new ancestry or neutral probe claim")
        _publish(life / "adult_result.json", result)
        return result
    except Exception as error:
        _publish(life / "adult_failure.json", dict(error_type=type(error).__name__, message=str(error)))
        raise


@contextmanager
def local_backend(model_dir, adapter_dir):
    from . import model_backend
    previous = model_backend.MODEL
    model_backend.MODEL = model_dir
    backend = None
    try:
        backend = model_backend.VLLMBackend(adapter_path=adapter_dir)
        yield backend
    finally:
        try:
            if backend is not None and not model_backend.close_backend(backend):
                raise RuntimeError("backend did not close; refusing another load")
        finally:
            model_backend.MODEL = previous


def local_trainer(request):
    """Isolate trainer CUDA state in a fresh process; preserve the nursery recipe.

    Both output streams go directly to the exclusive sleep-sibling training.log,
    never an unbounded in-memory capture. Failed logs remain for review; retrying
    cannot overwrite them. The caller's argv and environment are untouched.
    """
    command = [sys.executable, "-B", "-m", "organism_v6.train_adapter",
               "--corpus", request.corpus_path, "--out", request.output_dir,
               "--rank", str(request.rank), "--epochs", str(request.epochs), "--lr", str(request.lr),
               "--seed", str(request.seed), "--gate-receipt", request.gate_receipt_path,
               "--expected-gate-sha256", request.expected_gate_sha256,
               "--previous-manifest-sha256", request.previous_manifest_sha256,
               "--trainer-receipt", request.trainer_receipt_path]
    environment = dict(os.environ, V6_MODEL=request.model_dir,
                       HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    log_path = lineage._absolute(request.output_dir).parent / "training.log"
    with lineage._output(log_path) as log:
        try:
            subprocess.run(command, cwd=str(Path(__file__).resolve().parents[1]),
                           env=environment, stdout=log, stderr=subprocess.STDOUT, check=True)
        finally:
            log.flush()
            os.fsync(log.fileno())
            os.fchmod(log.fileno(), 0o444)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="JSON AdultRunSpec; no parent options")
    parser.add_argument("--execute", action="store_true", help="explicitly enable local model/training execution")
    args = parser.parse_args(argv)
    if not args.execute:
        parser.error("execution requires --execute; use CPU tests for non-launch validation")
    spec = AdultRunSpec(**_read(args.config))
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    run_adult(spec, gym=ReasoningGymGym(strict_verifier=True),
              backend_factory=local_backend, trainer=local_trainer)


if __name__ == "__main__":
    main()

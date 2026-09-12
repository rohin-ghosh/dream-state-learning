"""Exploratory static lesson versus active-sham material formation, inference only.

Local byte pins are not official base authentication. No adapter, training,
clean-nursery bypass, admission certificate, lineage, evaluation or H1 claim.
The existing source/content judges are used descriptively, never as admission.
Main owns single-GPU reservation and the hard two-hour outer timeout.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path

from . import batch_loop
from . import preschool_reasoning as policy
from .ledger import Ledger
from .reasoning_gym_gym import ReasoningGymGym
from .state import State


LABEL = "EXPLORATORY_LOCAL_BASE"
BOUNDARY = dict(label=LABEL, clean_lineage=False, official_base_authentication="UNRESOLVED",
                inference_only=True, evaluation="NONE", training=False, admission_certificate=False,
                claim="descriptive material formation; not persistence, learning or H1")
SCHEDULE = dict(episodes=64, schedule_seed=6101, generation_seed=7101,
                budget_ticks=16, wake_batch=8, note_max_tokens=100,
                wake_max_tokens=400, temperature=0.7,
                clock_policy="deterministic_tick_only_no_alive_seconds")


class DiagnosticState(State):
    def clock_line(self) -> str:
        stale = self.tick - self.last_progress_tick
        return (f"CLOCK: chunk {self.tick}/{self.budget_ticks} | "
                f"chunks since last progress: {stale}")


class DiagnosticDriver(batch_loop.NoEndTokenDriver):
    def __init__(self, episode, bootstrap, gym, ledger, budget_ticks=16):
        super().__init__(episode, bootstrap, gym, ledger, budget_ticks)
        self.st = DiagnosticState(**asdict(self.st))


@dataclass(frozen=True)
class Config:
    out: str
    mode: str
    model_path: str
    expected_files: dict


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def local_files(model_path):
    """Actual local inventory, explicitly not an official-origin assertion."""
    root = Path(model_path).resolve(strict=True)
    _require(root.is_dir(), "local model directory required")
    files = {}
    for path in sorted(root.rglob("*")):
        _require(not (path.is_symlink() and path.is_dir()), "model directory symlink")
        if path.is_dir():
            continue
        _require(path.is_file(), "nonregular local model file")
        _require(not path.name.startswith("adapter_"), "adapter files are forbidden")
        files[path.relative_to(root).as_posix()] = _hash(path)
    _require({"config.json", "tokenizer.json", "tokenizer_config.json"} <= set(files),
             "base/tokenizer inventory incomplete")
    config = json.loads((root / "config.json").read_bytes())
    _require(config.get("model_type") == "qwen2" and config.get("num_hidden_layers") == 28
             and config.get("hidden_size") == 3584 and not config.get("auto_map"),
             "expected local Qwen2.5-7B configuration, not origin authentication")
    _require(any(name.endswith((".safetensors", ".bin")) for name in files), "base weights missing")
    return files


def _write(path, value):
    with Path(path).open("xb") as target:
        target.write(policy._encoded(value))
        target.flush()
        os.fsync(target.fileno())
    Path(path).chmod(0o444)


def _sources():
    return {str(path.resolve()): _hash(path) for path in
            (Path(__file__), Path(policy.__file__), Path(batch_loop.__file__), Path(policy.FAMILIES_FILE))}


class ObservedBackend:
    def __init__(self, model, model_path, out, teacher):
        from .model_backend import configured_generation_identity
        self.model = model
        self.identity = configured_generation_identity(model_path, None)
        self.out = out
        self.teacher = teacher
        self.requests = 0
        self.teacher_presentations = 0
        self.tokenizer = model.tok
        self.teacher_tokens = len(self.tokenizer.encode(teacher, add_special_tokens=False))

    def generation_identity(self):
        _require(self.model.generation_identity() == self.identity, "actual local model/adapter identity changed")
        return dict(self.identity)

    def batch(self, prompts, max_tokens=400, seeds=None):
        self.generation_identity()
        _require(max_tokens in (100, 400) and seeds is not None and len(seeds) == len(prompts),
                 "fixed seeded generation ceilings required")
        pending = []
        for prompt, seed in zip(prompts, seeds):
            rendered = self.tokenizer.apply_chat_template([{"role": "user", "content": prompt}],
                                                          tokenize=False, add_generation_prompt=True)
            count = prompt.count(self.teacher)
            _require(count >= 1, "supplied lesson/sham missing from generation context")
            entry = dict(kind="request", request_index=self.requests, prompt=prompt,
                rendered_prompt=rendered, prompt_sha256=policy._sha(prompt.encode()),
                seed=seed, max_tokens=max_tokens, temperature=.7, source_identity=self.identity,
                teacher_presentations=1, teacher_text_occurrences=count, teacher_tokens=self.teacher_tokens,
                prompt_tokens=len(self.tokenizer.encode(rendered, add_special_tokens=False)))
            self.requests += 1
            self.teacher_presentations += 1
            pending.append(entry)
        self._append(pending)
        outputs = self.model.batch(prompts, max_tokens=max_tokens, temperature=.7, seeds=seeds)
        _require(isinstance(outputs, (list, tuple)) and len(outputs) == len(prompts)
                 and all(isinstance(output, str) for output in outputs), "incomplete child generation")
        self._append([dict(kind="output", request_index=entry["request_index"], text=text,
                           output_sha256=policy._sha(text.encode())) for entry, text in zip(pending, outputs)])
        self.generation_identity()
        return outputs

    def _append(self, rows):
        with (self.out / "generations.jsonl").open("ab") as target:
            for row in rows:
                target.write(policy._encoded(row))


def summarize(out):
    """Describe source-grounded child records; return no corpus or admission receipt."""
    out = Path(out)
    lines, rows = policy._lines((out / "ledger.jsonl").read_bytes())
    teaching = policy._lesson_rows((out / "lesson_deliveries.jsonl").read_bytes())
    _require([row for row in rows if row["kind"] == "parent_turn"] ==
             [policy._teacher_row(receipt) for receipt in teaching], "teacher receipt/ledger mismatch")
    lesson_payloads = []
    for receipt in teaching:
        lesson_payloads.extend(policy._copy_key(part.removeprefix("- "))
            for part in [receipt["text"], *receipt["text"].splitlines()]
            if len(policy._copy_key(part).split()) >= 8)
    executions, notes, reservations, batches, prefixes = {}, {}, {}, {}, {}
    prefix = hashlib.sha256()
    measured, unmeasured, invalid_acts = 0, 0, 0
    for index, row in enumerate(rows):
        group = {"act": executions, "note_after": notes, "episode_occurrence": reservations}.get(row["kind"])
        if group is not None:
            group.setdefault(row.get("occurrence_id" if row["kind"] == "episode_occurrence" else "execution_id"), []).append(index)
        generation = row.get("generation", {})
        if row["kind"] == "note_after" and isinstance(generation, dict) and generation.get("batch_id"):
            batches.setdefault(generation["batch_id"], []).append(row)
            prefixes.setdefault(generation["batch_id"], prefix.hexdigest())
        prefix.update(lines[index])
        if row["kind"] == "act":
            try:
                facts = policy.facts_from_act(row)
                measured += int(facts.measured)
                unmeasured += int(not facts.measured)
            except policy.InvalidFeedback:
                invalid_acts += 1
    generated = [json.loads(line) for line in (out / "generations.jsonl").read_bytes().splitlines()]
    requests = {row["request_index"]: row for row in generated if row["kind"] == "request"}
    wake, records = {}, {}
    for row in generated:
        if row["kind"] == "output":
            request = requests[row["request_index"]]
            _require(request["prompt_sha256"] == policy._sha(request["prompt"].encode())
                     and row["output_sha256"] == policy._sha(row["text"].encode()),
                     "actual generation hash mismatch")
            if request["max_tokens"] == 400:
                wake[request["prompt_sha256"], row["output_sha256"], request["seed"]] = row["text"]
            elif request["max_tokens"] == 100:
                records[request["prompt_sha256"], row["output_sha256"], request["seed"]] = row["text"]
    judgments, reasons, unique = [], Counter(), set()
    grounded = 0
    for index, row in enumerate(rows):
        if row["kind"] != "note_after":
            continue
        rejection, source_index = policy._judge_source(index, rows, executions, notes, reservations,
                                                       lesson_payloads, batches)
        if rejection is None:
            generation = row["generation"]
            if generation.get("ledger_prefix_sha256") != prefixes[generation["batch_id"]]:
                rejection = "generation-ledger-prefix-mismatch"
            if records.get((generation["prompt_sha256"], generation["output_sha256"],
                            generation["seed"])) != row["text"]:
                rejection = "record-not-in-actual-note-generation"
            source = rows[source_index]
            receipt = source.get("generation", {})
            output = wake.get((receipt.get("prompt_sha256"), receipt.get("output_sha256"), receipt.get("seed")))
            actions = [] if output is None else [match.group(2).strip() for match in batch_loop._MARK.finditer(output)
                                                if match.group(1) == "ACT"]
            if source["action"] not in actions:
                rejection = "source-not-in-actual-wake-generation"
        if rejection is None:
            grounded += 1
            key = policy._copy_key(row["text"])
            if key in unique:
                rejection = "duplicate-grounded-record"
            else:
                unique.add(key)
        if rejection:
            reasons[rejection] += 1
        judgments.append(dict(record_line=index, source_line=source_index,
            execution_id=row.get("execution_id"), unique_grounded=rejection is None,
            reason=rejection or "grounded-record-observed"))
    missing = sum(not notes.get(execution) for execution in executions)
    reasons["missing-note-after"] += missing
    return dict(**BOUNDARY, n_actions=sum(row["kind"] == "act" for row in rows),
        n_measured_actions=measured, n_unmeasured_actions=unmeasured, n_invalid_feedback_actions=invalid_acts,
        n_post_outcome_records=len(judgments), n_missing_notes=missing,
        n_grounded_records=grounded, n_unique_grounded_records=len(unique),
        unique_per_measured_action=len(unique) / measured if measured else None,
        rejection_reasons=dict(reasons), judgments=judgments,
        no_writer_qualified=len(unique) == 0, qualification_scope="descriptive only; not admission",
        teacher_receipts=len(teaching), actual_teacher_presentations=sum(row["teacher_presentations"] for row in requests.values()),
        teacher_tokens_per_presentation=sorted({row["teacher_tokens"] for row in requests.values()}),
        teacher_token_budget_matched="NOT_ASSERTED; actual arm doses recorded",
        generation_requests=len(requests))


def run(config, *, gym, backend_factory):
    _require(isinstance(config, Config) and config.mode in ("lesson", "sham"), "one fixed lesson/sham mode required")
    _require(isinstance(gym, ReasoningGymGym) and gym.strict_verifier is True, "strict reasoning verifier required")
    model_path = Path(config.model_path).resolve(strict=True)
    _require(str(model_path) == config.model_path, "use actual resolved local model path")
    before = local_files(model_path)
    _require(before == config.expected_files, "local base file pins mismatch")
    out = Path(config.out).absolute()
    _require(not any(path.is_symlink() for path in (out, *out.parents)), "output symlink")
    _require(not out.is_relative_to(model_path) and not model_path.is_relative_to(out), "output/model overlap")
    schedule = gym.training_schedule(64, 6101)
    _require(len(schedule) == len(set(schedule)) == 64 and all(gym.split_of(episode) == "train" for episode in schedule),
             "fixed training-only schedule required")
    from .multikey_writer_gateway_simple import assert_output_fds_outside_run
    sources = _sources()
    out.mkdir()
    assert_output_fds_outside_run(out)
    _write(out / "config.json", dict(**BOUNDARY, **asdict(config), protocol=SCHEDULE, source_hashes=sources))
    _write(out / "local_base_pins.json", dict(**BOUNDARY, model_path=config.model_path, files=before))
    _write(out / "schedule.json", schedule)
    ledger = Ledger(str(out / "ledger.jsonl"))
    Path(ledger.path).touch(exist_ok=False)
    (out / "generations.jsonl").touch(exist_ok=False)
    try:
        teacher = policy.deliver_lesson(str(out), config.mode, 0, ledger=ledger)
        _require(isinstance(teacher, str) and teacher, "missing actual lesson/sham")
        bootstrap = gym.birth_prompt() + "\n\n" + teacher
        with backend_factory(config.model_path) as model:
            observed = ObservedBackend(model, config.model_path, out, teacher)
            observed.generation_identity()
            _write(out / "teaching_dose.json", dict(**BOUNDARY, mode=config.mode, delivered_phases=[0],
                text_sha256=policy._sha(teacher.encode()), actual_token_counts={mode: len(model.tok.encode(
                    policy.lesson_block(mode, 0), add_special_tokens=False)) for mode in ("lesson", "sham")},
                bootstrap=bootstrap, dose_policy="one fixed receipt; same text present once per generated context"))
            slot = policy.PostOutcomeSlot(max_tokens=100)
            for start in range(0, 64, 8):
                episodes = [gym.episode_from_id(episode, 16) for episode in schedule[start:start + 8]]
                batch_loop.run_episodes_batch(observed, gym, episodes, bootstrap, ledger, 16,
                    log=lambda message: None, gen_seed=7101, driver_cls=DiagnosticDriver, note_after=slot)
            observed.generation_identity()
        _require(local_files(model_path) == before and sources == _sources(), "base/source changed during diagnostic")
        result = dict(status="COMPLETE", mode=config.mode, **summarize(out))
        _write(out / "results.json", result)
        return result
    except Exception as error:
        _write(out / "failure.json", dict(**BOUNDARY, error_type=type(error).__name__, error=str(error)))
        if (out / "lesson_deliveries.jsonl").exists():
            try:
                _write(out / "partial_results.json", dict(status="INCOMPLETE", mode=config.mode, **summarize(out)))
            except Exception as summary_error:
                _write(out / "partial_summary_error.json", dict(error=str(summary_error), **BOUNDARY))
        raise
    finally:
        try:
            after = local_files(model_path)
            _write(out / "base_after.json", dict(**BOUNDARY, model_path=config.model_path,
                                                 files=after, unchanged=after == before))
        except Exception as error:
            _write(out / "base_after_error.json", dict(error=str(error), **BOUNDARY))
        _write(out / "artifact_hashes.json", dict(**BOUNDARY,
            files={path.name: _hash(path) for path in out.iterdir() if path.is_file()}))
        for path in out.iterdir():
            path.chmod(0o444)
        out.chmod(0o555)


@contextmanager
def local_backend(model_path):
    from . import model_backend
    _require(model_backend.MODEL == model_path and os.environ.get("V6_MODEL") == model_path,
             "set V6_MODEL to the pinned actual path before starting Python")
    _require(os.environ.get("HF_HUB_OFFLINE") == os.environ.get("TRANSFORMERS_OFFLINE") == "1",
             "offline environment required")
    backend = model_backend.VLLMBackend(adapter_path=None)
    try:
        yield backend
    finally:
        _require(model_backend.close_backend(backend), "backend cleanup did not release GPU")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    if not args.execute:
        parser.error("explicit --execute required; main owns GPU reservation and hard 2h outer timeout")
    config = Config(**json.loads(Path(args.config).read_bytes()))
    result = run(config, gym=ReasoningGymGym(strict_verifier=True), backend_factory=local_backend)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

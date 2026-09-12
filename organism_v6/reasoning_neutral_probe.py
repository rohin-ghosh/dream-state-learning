"""Evaluation-only expression of child-authored measured action records.

This is q14 section 5's narrow competency: an optional neutral Scratchpad
after actual reasoning-gym feedback, not strategy, H2, a message12 policy,
training admission, clean ancestry, or proof of base-model origin. The caller
authenticates base origin and owns fresh-process adapter ON/OFF comparisons.
This module only drives ONE already-selected backend; it never loads a model,
launches processes, trains, or writes to a life/lineage. See the run_probe API.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
from pathlib import Path

from . import batch_loop, gym_backend, preschool, preschool_reasoning, reasoning_gym_gym, state
from .ledger import Ledger
from .preschool_reasoning import PostOutcomeSlot, facts_from_act, judge_record
from .reasoning_gym_gym import ReasoningGymGym


EVIDENCE_LABEL = "EVALUATION_ONLY"


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"


def _digest(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_hashes(directory):
    """Hash every configured local file; these hashes do not authenticate origin."""
    root = Path(directory).resolve(strict=True)
    _require(root.is_dir(), "model/adapter path must be a local directory")
    files = {}
    for path in sorted(root.rglob("*")):
        _require(not (path.is_symlink() and path.is_dir()), "directory symlink in source")
        if path.is_file():
            files[str(path.relative_to(root))] = _digest(path)
        else:
            _require(path.is_dir(), "unsupported source file")
    _require(bool(files), "empty model/adapter directory")
    return files


def _overlap(first, second):
    return first == second or first in second.parents or second in first.parents


def _write(path, value):
    with path.open("x", encoding="utf-8") as target:
        target.write(_json(value))
        target.flush()
        os.fsync(target.fileno())


class _ProbeLedger(Ledger):
    def append(self, rec):
        return super().append(dict(rec, evidence_label=EVIDENCE_LABEL))

    def recall(self, query, k=6):
        return []


class _BoundedBackend:
    def __init__(self, model, identity, path, max_tokens, total_budget):
        self.model = model
        self.source_identity = identity
        self.path = path
        self.max_tokens = max_tokens
        self.total_budget = total_budget
        self.reserved_tokens = 0
        self.requests = 0

    def check(self):
        _require(self.model.generation_identity() == self.source_identity,
                 "backend identity changed")

    def generation_identity(self):
        self.check()
        return dict(self.source_identity, default_max_tokens=self.max_tokens)

    def batch(self, prompts, max_tokens=None, seeds=None):
        self.check()
        limit = self.max_tokens if max_tokens is None else max_tokens
        _require(seeds is not None and len(seeds) == len(prompts), "explicit seeds required")
        reservation = len(prompts) * limit
        _require(self.reserved_tokens + reservation <= self.total_budget,
                 "total generation token budget exceeded")
        self.reserved_tokens += reservation
        request = dict(evidence_label=EVIDENCE_LABEL, kind="generation_request",
                       request_index=self.requests, prompts=prompts, seeds=seeds,
                       max_tokens=limit, source_identity=self.source_identity,
                       temperature=self.source_identity["default_temperature"],
                       prompt_scope="batch_user_text_before_chat_template")
        self.requests += 1
        with self.path.open("a", encoding="utf-8") as target:
            target.write(_json(request))
        outputs = self.model.batch(prompts, max_tokens=limit, seeds=seeds,
                                   temperature=self.source_identity["default_temperature"])
        with self.path.open("a", encoding="utf-8") as target:
            target.write(_json(dict(evidence_label=EVIDENCE_LABEL, kind="generation_output",
                                    request_index=request["request_index"], outputs=outputs)))
        self.check()
        _require(isinstance(outputs, (list, tuple)) and len(outputs) == len(prompts)
                 and all(isinstance(text, str) for text in outputs), "invalid generation cardinality")
        return outputs


def _counts(rows):
    actions = {row["execution_id"]: row for row in rows if row.get("kind") == "act"}
    _require(len(actions) == sum(row.get("kind") == "act" for row in rows),
             "duplicate execution identity")
    facts = {key: facts_from_act(row) for key, row in actions.items()}
    judgments = []
    seen = set()
    for row in rows:
        if row.get("kind") != "scratchpad":
            continue
        execution = row["execution_id"]
        _require(execution in facts and execution not in seen, "unbound scratchpad")
        seen.add(execution)
        _require(all(row.get(field) == actions[execution].get(field) for field in
                     ("episode_id", "tick", "action", "outcome", "score", "occurrence_id")),
                 "scratchpad source mismatch")
        judgments.append(dict(execution_id=execution,
                              **judge_record(row["text"], facts[execution])))
    _require(seen == set(actions), "missing post-outcome scratchpad")
    measured = sum(fact.measured for fact in facts.values())
    correct = sum(judgment["content_eligible"] for judgment in judgments)
    return dict(n_actions=len(actions), n_measured_actions=measured,
                n_scratchpads=len(judgments), n_correct_grounded_scratchpads=correct,
                articulation_rate=correct / measured if measured else None,
                judgments=judgments)


def run_probe(model, gym, *, episode_ids, output_dir, probe_root,
              training_life_roots, lineage_roots, model_path, adapter_path,
              expected_model_hashes, expected_adapter_hashes, gen_seed,
              budget_ticks, wake_max_tokens, scratchpad_max_tokens,
              total_token_budget, max_episodes, seed_salt=0x3C3C):
    """Run one backend on supplied held-out IDs, with no parent/history input.

    All paths are local. output_dir must be NEW, below an existing probe_root,
    disjoint (in both directions, resolving symlinks) from every caller-declared
    training life and lineage root. Both exclusion lists must be nonempty.
    Expected manifests map every relative file name to its SHA256. They bind
    configured files, not loaded weights or base origin. The caller verifies
    that origin independently. Seeds and generation caps are mandatory; the
    total budget reserves maximum output tokens before each batch, not measured
    token usage. No partial/failed invocation produces successful results.

    Each episode gets its own fresh driver and non-retrieving ledger. There is
    no harvesting/admission call. Outputs are exclusively created, sealed
    read-only and hash-manifested, including failures; never reuse a directory.
    Read-only modes are an accidental-write guard, not adversarial immutability.
    """
    _require(isinstance(gym, ReasoningGymGym) and gym.strict_verifier is True,
             "a strict ReasoningGymGym verifier is required")
    for name, value in (("budget_ticks", budget_ticks), ("wake_max_tokens", wake_max_tokens),
                        ("scratchpad_max_tokens", scratchpad_max_tokens),
                        ("total_token_budget", total_token_budget), ("max_episodes", max_episodes)):
        _require(type(value) is int and value > 0, "invalid " + name)
    for seed in (gen_seed, seed_salt):
        _require(type(seed) is int and 0 <= seed <= 0x7fffffff, "invalid explicit seed")
    _require(isinstance(episode_ids, (list, tuple)) and len(episode_ids) <= max_episodes,
             "invalid episode panel or episode limit")
    _require(all(isinstance(episode, str) for episode in episode_ids)
             and len(set(episode_ids)) == len(episode_ids), "invalid/duplicate episode IDs")
    _require(all(gym.split_of(episode) in ("canary", "gate", "exam") for episode in episode_ids),
             "episode is not held out")
    root = Path(probe_root).resolve(strict=True)
    output = Path(output_dir).resolve()
    _require(root.is_dir() and root in output.parents, "output outside probe root")
    if os.path.lexists(output_dir):
        raise FileExistsError("probe directory already exists; preserve it and use a new path")
    _require(bool(training_life_roots) and bool(lineage_roots), "declare life and lineage roots")
    protected = [Path(path).resolve() for path in (*training_life_roots, *lineage_roots)]
    _require(not any(_overlap(output, path) for path in protected), "output conflicts with protected roots")
    sources = {"model": Path(model_path).resolve(strict=True)}
    if adapter_path is not None:
        sources["adapter"] = Path(adapter_path).resolve(strict=True)
    _require(not any(_overlap(output, path) for path in sources.values()), "output conflicts with sources")
    before = {name: file_hashes(path) for name, path in sources.items()}
    _require(before["model"] == expected_model_hashes, "model file hash mismatch")
    _require(before.get("adapter", {}) == expected_adapter_hashes, "adapter file hash mismatch")
    identity = json.loads(_json(model.generation_identity()))
    _require(preschool_reasoning._identity_status(identity) == "RECORDED_BACKEND",
             "unsupported backend identity")
    _require(Path(identity["model_input"]).resolve(strict=True) == sources["model"],
             "wrong model identity")
    claimed_adapter = identity["adapter_input"]
    _require((claimed_adapter is None) == (adapter_path is None), "wrong adapter identity")
    if claimed_adapter is not None:
        _require(Path(claimed_adapter).resolve(strict=True) == sources["adapter"], "wrong adapter identity")
    _require(all(before.get("adapter", {}).get(name) == digest
                 for name, digest in identity["adapter_files"].items()), "backend adapter hash mismatch")
    bootstrap = gym.birth_prompt()
    code_paths = {str(Path(module.__file__).resolve()) for module in
                  (batch_loop, gym_backend, preschool, preschool_reasoning, reasoning_gym_gym, state)}
    code_paths.add(str(Path(__file__).resolve()))
    for instance in (model, gym, Ledger):
        source = inspect.getsourcefile(instance if isinstance(instance, type) else type(instance))
        if source:
            code_paths.add(str(Path(source).resolve()))
    code_before = {path: _digest(path) for path in sorted(code_paths)}
    output.mkdir()
    backend = _BoundedBackend(model, identity, output / "generations.jsonl",
                              wake_max_tokens, total_token_budget)
    try:
        backend.path.touch(exist_ok=False)
        _write(output / "configuration.json", dict(
            evidence_label=EVIDENCE_LABEL, episode_ids=episode_ids, gen_seed=gen_seed,
            seed_salt=seed_salt, budget_ticks=budget_ticks, wake_max_tokens=wake_max_tokens,
            scratchpad_max_tokens=scratchpad_max_tokens, total_token_budget=total_token_budget,
            max_episodes=max_episodes, birth_prompt=bootstrap, source_identity=identity,
            sources={name: str(path) for name, path in sources.items()}, hashes_before=before,
            code_hashes_before=code_before, gym_configuration=gym.cfg,
            reasoning_gym_version=reasoning_gym_gym.installed_version(),
            protected_roots=[str(path) for path in protected], probe_root=str(root),
            origin_verification="EXTERNAL_CALLER_REQUIRED; configured inputs are not authentication"))
        results = []
        for index, episode_id in enumerate(episode_ids):
            ledger = _ProbeLedger(str(output / f"episode_{index:04d}.jsonl"))
            Path(ledger.path).touch(exist_ok=False)
            slot = PostOutcomeSlot(label="Scratchpad", kind="scratchpad",
                                   max_tokens=scratchpad_max_tokens, seed_salt=seed_salt)
            summaries = batch_loop.run_episodes_batch(
                backend, gym, [gym.episode_from_id(episode_id, budget_ticks)], bootstrap,
                ledger, budget_ticks, log=lambda message: None, gen_seed=gen_seed,
                driver_cls=batch_loop.driver_class_for(gym), note_after=slot)
            results.append(dict(episode_id=episode_id, ledger=Path(ledger.path).name,
                                summary=summaries[0], **_counts(ledger.rows())))
        backend.check()
        after = {name: file_hashes(path) for name, path in sources.items()}
        code_after = {path: _digest(path) for path in code_before}
        _write(output / "source_check.json", dict(evidence_label=EVIDENCE_LABEL,
                                                  hashes_after=after, code_hashes_after=code_after))
        _require(before == after and code_before == code_after, "source file hashes changed during probe")
        measured = sum(result["n_measured_actions"] for result in results)
        correct = sum(result["n_correct_grounded_scratchpads"] for result in results)
        result = dict(evidence_label=EVIDENCE_LABEL, episodes=results,
                      n_actions=sum(item["n_actions"] for item in results),
                      n_measured_actions=measured, n_correct_grounded_scratchpads=correct,
                      n_scratchpads=sum(item["n_scratchpads"] for item in results),
                      articulation_rate=correct / measured if measured else None,
                      reserved_output_tokens=backend.reserved_tokens,
                      generation_batches=backend.requests)
        _write(output / "results.json", result)
        return result
    except Exception as error:
        if not (output / "source_check.json").exists():
            try:
                after = {name: file_hashes(path) for name, path in sources.items()}
                code_after = {path: _digest(path) for path in code_before}
                check = dict(hashes_after=after, code_hashes_after=code_after,
                             unchanged=before == after and code_before == code_after)
            except Exception as source_error:
                check = dict(error_type=type(source_error).__name__, error=str(source_error))
            _write(output / "source_check.json", dict(evidence_label=EVIDENCE_LABEL, **check))
        _write(output / "failure.json", dict(evidence_label=EVIDENCE_LABEL,
                                             error_type=type(error).__name__, error=str(error)))
        raise
    finally:
        artifacts = {path.name: _digest(path) for path in output.iterdir() if path.is_file()}
        _write(output / "manifest.json", dict(evidence_label=EVIDENCE_LABEL, sha256=artifacts))
        for path in output.iterdir():
            path.chmod(0o444)
        output.chmod(0o555)

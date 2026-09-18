"""Bounded fresh parenting capture; candidates only, not an admission or fit.

CPU: --out NEW --model-path BASE --pins PINS [--prior-source-ids AUDIT]
     [--prior-questions AUDIT]. Audit inputs are metadata only (schemas below),
never scout generations, ledgers, answers, or training material. Without a
prior-source ID inventory preparation remains pending. Optional prior question
comparison is explicitly scoped to the supplied inventory, not global freshness.

Main alone may execute a READY preparation with --preparation PREP --out NEW
--allow-gpu, after its full GPU/CUDA/queue check and reservation. The controller
uses separate owned workers, each bounded to 1800 seconds. There is no launcher.
CPU replay: --replay ARM --out NEW. Replay never calls a model or verifier and
returns candidates for later public-constraint audit and V3 sleep, not targets.
Local hashes do not authenticate base origin; no clean-lineage or truth claim.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
from types import SimpleNamespace

from . import batch_loop, model_backend, preschool, state
from . import parent_material_diagnostic as formation
from . import parent_competency_diagnostic as packages
from . import preschool_reasoning as policy
from . import reasoning_gym_gym as native
from . import run_reasoning_neutral as supervisor
from .ledger import Ledger
from .mini_sudoku_behavior_material import EVAL_IDS, TRAIN_IDS, board_from_text
from .parent_material_write import _load_tokenizer


IDS = tuple(f"rg/mini_sudoku/{seed}" for seed in range(1850100, 1850132))
MODES = ("process", "sham")
PROTOCOL = dict(episodes=32, budget_ticks=2, batch_size=8, generation_seed=7101,
                temperature=.7, wake_max_tokens=400, scratchpad_max_tokens=100,
                max_model_len=4096, worker_timeout_seconds=1800,
                scratchpad_round="one per actual first-wake ACT; none after wake2")
BOUNDARY = dict(role="DEVELOPMENT_TRAINING_EXPERIENCE", fresh_collection=True,
                clean_lineage=False, adapter=None, fit=False, admission=False,
                reflection_truth="NOT_ASSERTED", useful_training="NOT_ASSERTED",
                origin="UNRESOLVED_LOCAL_BASE_HASHES_ONLY", H1_claim=False,
                candidates="later public-constraint audit and V3 sleep only")
require = packages.require
read = packages.read
seal = packages.seal
verify_inventory = packages.verify_inventory
fresh_output = packages.fresh_output
sha = policy._sha


def source_pins(*, synthetic=False):
    modules = (sys.modules[__name__], formation, packages, batch_loop, model_backend,
               policy, preschool, state, native, supervisor, sys.modules[Ledger.__module__],
               sys.modules[board_from_text.__module__], sys.modules[_load_tokenizer.__module__])
    paths = {Path(module.__file__).resolve() for module in modules}
    paths.update((Path(native.FAMILIES_JSON), Path(native.BOOTSTRAP_PATH)))
    if not synthetic:
        require(native.installed_version() == native.PINNED_VERSION, "native package version mismatch")
        spec = importlib.util.find_spec("reasoning_gym")
        require(spec is not None and spec.origin, "native package unavailable")
        paths.update(Path(spec.origin).parent.rglob("*.py"))
    return {str(path.resolve()): formation._hash(path) for path in sorted(paths)}


def audit_metadata(value, schema, field):
    require(isinstance(value, dict) and set(value) == {"schema", field}
            and value["schema"] == schema and isinstance(value[field], list),
            "metadata-only audit required; STATIC scout outputs/ledgers are forbidden inputs")
    return value[field]


def selected_ids(ids, gym, prior_source_ids=None):
    require(ids == list(IDS), "exact ordered 32 fresh IDs required; no replacements")
    held = set(EVAL_IDS) | set(TRAIN_IDS)
    for split in ("canary", "gate", "exam"):
        held.update(gym.benchmarks(split))
    require(not set(ids) & held and all(gym.split_of(episode) == "train" for episode in ids),
            "training membership or held/gate/exam disjointness failed")
    if prior_source_ids is not None:
        prior = audit_metadata(prior_source_ids, "prior-source-ids-v1", "episode_ids")
        require(all(isinstance(episode, str) for episode in prior), "invalid prior source ID")
        require(not set(ids) & set(prior), "prior source ID overlap; no replacements")
    return sorted(held)


class EpisodeLedger(Ledger):
    """Real append-only ledger, but native RECALL can see only this episode."""

    def __init__(self, path, episode_id):
        super().__init__(path)
        self.episode_id = episode_id

    def rows(self):
        return [row for row in super().rows() if row.get("episode_id") == self.episode_id]


class CorrectionDriver(formation.DiagnosticDriver):
    """Native ACT parser/NoEndTokenDriver; local untruncated two-tick context."""

    def prompt(self):
        require(self.st.tick < 2, "only two wake opportunities")
        self.st.tick += 1
        current = self.st
        head = ["=== YOU ===", self.bootstrap, "=== STATE ===", f"GOAL: {current.goal}",
                f"METRIC: {current.metric}", current.clock_line(),
                f"BEST SCORE THIS EPISODE: {current.best_score:.4f}"
                + (f"  (via: {current.best_action})" if current.best_action else ""),
                f"LAST OUTCOME: {current.last_outcome}"]
        if current.open_surprises:
            head += ["OPEN SURPRISES (you expected vs got):"]
            head += [f"  - {item}" for item in current.open_surprises]
        if current.notes:
            head += ["YOUR NOTES (you wrote these to yourself):"]
            head += [f"  - {item}" for item in current.notes]
        self._last_prompt = "\n".join(head + ["=== RECALLED EXPERIENCE ==="]
                                    + (self.recalled or ["(nothing recalled)"])
                                    + ["=== YOUR THINKING (continues) ==="] + self.tail) + "\n"
        return self._last_prompt

    def consume(self, chunk):
        position = len(self.tail)
        super().consume(chunk)
        self.tail[position] = chunk


class BoundedBackend(formation.ObservedBackend):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.captures = []
        self.deadline = time.monotonic() + PROTOCOL["worker_timeout_seconds"]

    def batch(self, prompts, max_tokens=400, seeds=None):
        require(time.monotonic() < self.deadline, "arm time budget exhausted")
        require(0 < len(prompts) <= 8 and max_tokens in (100, 400), "bounded batch/output ceiling")
        rendered = [self.tokenizer.apply_chat_template([dict(role="user", content=prompt)],
                    tokenize=False, add_generation_prompt=True) for prompt in prompts]
        counts = [len(self.tokenizer.encode(text, add_special_tokens=False)) for text in rendered]
        fits = all(count + max_tokens <= 4096 for count in counts)
        self._append([dict(kind="live_input_check", request_index=self.requests + index,
                           prompt=prompt, rendered_prompt=text, prompt_tokens=count,
                           output_headroom=max_tokens, fits=count + max_tokens <= 4096)
                      for index, (prompt, text, count) in enumerate(zip(prompts, rendered, counts))])
        require(fits, "live input plus output headroom exceeds 4096; no truncation")
        first_index = self.requests
        outputs = super().batch(prompts, max_tokens=max_tokens, seeds=seeds)
        for index, (prompt, text, output, count, seed) in enumerate(zip(prompts, rendered, outputs, counts, seeds)):
            self.captures.append(dict(request_index=first_index + index, prompt=prompt,
                rendered_prompt=text, prompt_sha256=sha(prompt.encode()), rendered_sha256=sha(text.encode()),
                text=output, output_sha256=sha(output.encode()), prompt_tokens=count,
                output_tokens=len(self.tokenizer.encode(output, add_special_tokens=False)),
                max_tokens=max_tokens, seed=seed, temperature=.7))
        require(time.monotonic() < self.deadline, "arm time budget exhausted after generation")
        return outputs


def question_audit(gym, ids, held, prior_questions):
    questions = [dict(episode_id=episode, question=gym.question(episode)) for episode in ids]
    for row in questions:
        row["question_sha256"] = sha(row["question"].encode())
        row["episode"] = asdict(gym.episode_from_id(row["episode_id"], 2))
    digests = {row["question_sha256"] for row in questions}
    require(len(digests) == 32, "duplicate actual native questions; no replacements")
    excluded = [dict(episode_id=episode, question_sha256=sha(gym.question(episode).encode())) for episode in held]
    require(not digests & {row["question_sha256"] for row in excluded}, "held/prior configured question overlap")
    comparison = None
    if prior_questions is not None:
        comparison = audit_metadata(prior_questions, "prior-question-hashes-v1", "questions")
        require(all(isinstance(row, dict) and set(row) == {"episode_id", "question_sha256"}
                    and isinstance(row["episode_id"], str)
                    and isinstance(row["question_sha256"], str)
                    and re.fullmatch(r"[0-9a-f]{64}", row["question_sha256"]) for row in comparison),
                "prior question audit must contain only IDs and SHA256 hashes")
        require(not digests & {row["question_sha256"] for row in comparison}, "prior actual question overlap")
    return dict(questions=questions, excluded_question_hashes=excluded,
                supplied_prior_question_comparison=comparison,
                global_prior_question_freshness="UNRESOLVED; supplied inventory only",
                references="audit-only; reference answers never requested or placed in prompts")


def prepare(out, model_path, expected_files, *, ids=None, prior_source_ids=None,
            prior_questions=None, gym=None, tokenizer=None):
    ids = list(IDS) if ids is None else ids
    model = Path(model_path).resolve(strict=True)
    root = fresh_output(out, [model, Path(__file__).resolve().parents[1]])
    require(formation.local_files(model) == expected_files, "local base pins mismatch")
    synthetic = gym is not None or tokenizer is not None
    config = dict(schema="fresh-parent-correction-v1", boundary=BOUNDARY, protocol=PROTOCOL,
                  packages=packages.PACKAGES, episode_ids=ids, model_path=str(model),
                  expected_files=expected_files, synthetic=synthetic,
                  prior_source_ids=prior_source_ids, prior_questions=prior_questions)
    root.mkdir(parents=True)
    try:
        try:
            gym = gym if gym is not None else native.ReasoningGymGym(require_package=True, strict_verifier=True)
            require(isinstance(gym, native.ReasoningGymGym) and gym.strict_verifier, "native strict verifier required")
            config["sources"] = source_pins(synthetic=synthetic)
            held = selected_ids(ids, gym, prior_source_ids)
            audit = question_audit(gym, ids, held, prior_questions)
            formation._write(root / "questions.json", audit)
            tokenizer = tokenizer if tokenizer is not None else _load_tokenizer(str(model))
        except (ImportError, OSError, RuntimeError) as error:
            check = dict(status="PENDING_NATIVE_OR_TOKENIZER", blocker=str(error))
        else:
            first_prompts = {}
            for mode in MODES:
                bootstrap = gym.birth_prompt() + "\n\n" + packages.PACKAGES[mode]
                first_prompts[mode] = []
                for episode in ids:
                    prompt = CorrectionDriver(gym.episode_from_id(episode, 2), bootstrap, gym, None, 2).prompt()
                    rendered = tokenizer.apply_chat_template([dict(role="user", content=prompt)],
                        tokenize=False, add_generation_prompt=True)
                    first_prompts[mode].append(dict(episode_id=episode, prompt=prompt, rendered_prompt=rendered,
                        prompt_tokens=len(tokenizer.encode(rendered, add_special_tokens=False))))
            tokens = {mode: len(tokenizer.encode(packages.PACKAGES[mode], add_special_tokens=False)) for mode in MODES}
            fits = all(row["prompt_tokens"] + 400 <= 4096 for arm in first_prompts.values() for row in arm)
            matched = tokens["process"] == tokens["sham"] and all(
                left["prompt_tokens"] == right["prompt_tokens"]
                for left, right in zip(first_prompts["process"], first_prompts["sham"]))
            blockers = ([] if fits else ["initial context exceeds 4096"]) + ([] if matched else ["fixed package token mismatch"])
            if prior_source_ids is None:
                blockers.append("prior source ID overlap check pending")
            check = dict(status="PENDING" if blockers else "SYNTHETIC_CPU_ONLY" if synthetic else "READY",
                         blockers=blockers, first_prompts=first_prompts, package_tokens=tokens,
                         input_token_match=matched, later_context_checks="LIVE; no truncation",
                         prior_question_comparison="SUPPLIED_SCOPE_ONLY" if prior_questions is not None else "NOT_SUPPLIED_UNRESOLVED",
                         launch="Main only after full GPU/CUDA/queue check; no launch authorization here")
        require(formation.local_files(model) == expected_files, "base changed during prepare")
        formation._write(root / "config.json", config)
        formation._write(root / "preflight.json", check)
        return check
    except BaseException as error:
        formation._write(root / "failure.json", dict(error=repr(error)))
        raise
    finally:
        seal(root)


def validate_preparation(preparation, *, allow_synthetic=False):
    prep = Path(preparation).resolve(strict=True)
    digest = verify_inventory(prep)
    config, check = read(prep / "config.json"), read(prep / "preflight.json")
    require(config["schema"] == "fresh-parent-correction-v1" and config["boundary"] == BOUNDARY
            and config["protocol"] == PROTOCOL and config["packages"] == packages.PACKAGES
            and config["episode_ids"] == list(IDS), "source/mode/IDs/protocol mismatch")
    require((not config["synthetic"] and check["status"] == "READY") or
            (allow_synthetic and config["synthetic"] and check["status"] == "SYNTHETIC_CPU_ONLY"),
            "native preparation pending or synthetic/GPU mode mismatch")
    require(config["sources"] == source_pins(synthetic=config["synthetic"]), "source pins changed")
    require(formation.local_files(config["model_path"]) == config["expected_files"], "base pins changed")
    return prep, digest, config


def raw_act_spans(text):
    return [dict(start_byte=len(text[:match.start()].encode()), end_byte=len(text[:match.end()].encode()),
                 raw=text[match.start():match.end()], action=match.group(2).strip())
            for match in batch_loop._MARK.finditer(text) if match.group(1) == "ACT"]


def injection_block(record):
    return (f"[Scratchpad from {record['execution_id']} after first-wake public outcome]\n"
            + record["text"])


def collect(observed, gym, ledger, mode, questions):
    bootstrap = gym.birth_prompt() + "\n\n" + packages.PACKAGES[mode]
    collected = []
    for start in range(0, 32, 8):
        selected = questions[start:start + 8]
        drivers = [CorrectionDriver(gym.episode_from_id(row["episode_id"], 2), bootstrap, gym,
                   EpisodeLedger(ledger.path, row["episode_id"]), 2) for row in selected]
        slot = policy.PostOutcomeSlot(label="Scratchpad", kind="scratchpad", max_tokens=100)
        slot.reserve_occurrences(drivers, ledger)
        records = []
        for driver, question in zip(drivers, selected):
            driver.note_after = slot
            records.append(dict(episode_id=driver.ep.eid, question=question["question"],
                question_sha256=question["question_sha256"], episode=asdict(driver.ep),
                occurrence_id=driver.occurrence_id, wakes=[], scratchpads=[], injections=[]))
        for tick in (1, 2):
            prompts = [driver.prompt() for driver in drivers]
            before = len(observed.captures)
            seeds = [batch_loop._seed_for(driver.ep.eid, tick, 7101) for driver in drivers]
            chunks = observed.batch(prompts, max_tokens=400, seeds=seeds)
            for driver, record, chunk, capture in zip(drivers, records, chunks, observed.captures[before:]):
                driver._generation_receipt = dict(schema="child-generation-v1", identity=observed.generation_identity(),
                    prompt_sha256=capture["prompt_sha256"], output_sha256=capture["output_sha256"],
                    seed=capture["seed"], max_tokens=400, temperature=.7)
                driver.consume(chunk)
                actions = [pending["act_row"] for pending in driver.pending_after]
                record["wakes"].append(dict(tick=tick, generation=capture, actions=actions,
                                            raw_act_spans=raw_act_spans(chunk)))
            if tick == 1:
                pending = [SimpleNamespace(pending_after=[action], _last_prompt=driver._last_prompt)
                           for driver in drivers for action in driver.pending_after]
                for offset in range(0, len(pending), 8):
                    slot.run_round(observed, pending[offset:offset + 8], ledger, 7101)
                by_execution = {row["execution_id"]: row for row in ledger.rows() if row["kind"] == "scratchpad"}
                by_prompt = {row["prompt_sha256"]: row for row in observed.captures if row["max_tokens"] == 100}
                for driver, record in zip(drivers, records):
                    for action in driver.pending_after:
                        scratch = by_execution[action["execution_id"]]
                        capture = by_prompt[scratch["generation"]["prompt_sha256"]]
                        record["scratchpads"].append(dict(record=scratch, capture=capture))
                        block = injection_block(scratch)
                        driver.tail.append(block)
                        record["injections"].append(dict(execution_id=scratch["execution_id"], block=block,
                            scratchpad_sha256=sha(scratch["text"].encode()), block_sha256=sha(block.encode())))
            for driver in drivers:
                driver.pending_after = []
        for driver, record in zip(drivers, records):
            require(driver.done and driver.st.tick == 2, "incomplete two-tick trajectory")
            next_prompt = record["wakes"][1]["generation"]["prompt"]
            for binding in record["injections"]:
                offset = next_prompt.rfind(binding["block"])
                require(offset >= 0, "source-bound Scratchpad missing in second prompt")
                binding.update(start_byte=len(next_prompt[:offset].encode()),
                               end_byte=len(next_prompt[:offset + len(binding["block"])].encode()),
                               next_prompt_sha256=sha(next_prompt.encode()))
            record["summary"] = driver.summary()
            ledger.append(dict(kind="correction_capture", episode_id=record["episode_id"], capture=record))
            collected.append(record)
    return collected


def check_capture(capture):
    require(sha(capture["prompt"].encode()) == capture["prompt_sha256"]
            and sha(capture["rendered_prompt"].encode()) == capture["rendered_sha256"]
            and sha(capture["text"].encode()) == capture["output_sha256"], "raw generation binding mismatch")
    require(capture["prompt_tokens"] + capture["max_tokens"] <= 4096, "captured context budget exceeded")
    require(capture["temperature"] == .7, "captured temperature mismatch")


def reduce_captures(records):
    """Pure capture validation/counting; deliberately no reflection-content judge."""
    require([row["episode_id"] for row in records] == list(IDS), "all 32 ordered episodes required")
    episodes, candidates = [], []
    for record in records:
        episode = record["episode_id"]
        require(sha(record["question"].encode()) == record["question_sha256"], "actual question hash mismatch")
        require([wake["tick"] for wake in record["wakes"]] == [1, 2]
                and record["summary"]["ticks"] == 2 and record["summary"]["episode_id"] == episode,
                "exactly two ticks in the same episode required")
        wakes = []
        for wake in record["wakes"]:
            capture = wake["generation"]
            check_capture(capture)
            require(capture["max_tokens"] == 400 and capture["seed"] == batch_loop._seed_for(episode, wake["tick"], 7101),
                    "wake generation protocol mismatch")
            spans = raw_act_spans(capture["text"])
            require(spans == wake["raw_act_spans"] and [span["action"] for span in spans]
                    == [action["action"] for action in wake["actions"]], "raw ACT order mismatch")
            for action in wake["actions"]:
                require(action["episode_id"] == episode and action["occurrence_id"] == record["occurrence_id"]
                        and action["tick"] == wake["tick"]
                        and action["generation"]["output_sha256"] == capture["output_sha256"]
                        and action["generation"]["prompt_sha256"] == capture["prompt_sha256"], "cross-episode/action binding")
                policy.facts_from_act(action)
            summary = packages.action_summary(wake["actions"])
            summary["first_native_accepted"] = bool(wake["actions"] and wake["actions"][0]["score"] == 1)
            summary["first_native_partial"] = bool(wake["actions"] and 0 < wake["actions"][0]["score"] < 1)
            wakes.append(summary)
        first_actions = record["wakes"][0]["actions"]
        require(record["summary"]["n_acts"] == sum(wake["n_actions"] for wake in wakes), "native action count mismatch")
        require(len(record["scratchpads"]) == len(record["injections"]) == len(first_actions),
                "one Scratchpad per first-wake ACT required")
        next_prompt = record["wakes"][1]["generation"]["prompt"]
        for action, scratch, binding in zip(first_actions, record["scratchpads"], record["injections"]):
            row, capture = scratch["record"], scratch["capture"]
            check_capture(capture)
            expected_prompt = record["wakes"][0]["generation"]["prompt"].rstrip("\n") + "\n\n" + policy.outcome_block(
                policy.facts_from_act(action), "Scratchpad")
            require(row["kind"] == "scratchpad" and row["label"] == "Scratchpad" and row["tick"] == 1
                    and all(row[key] == action[key] for key in ("episode_id", "occurrence_id", "execution_id", "action", "outcome", "score"))
                    and capture["prompt"] == row["generation"]["prompt"] == expected_prompt
                    and capture["prompt_sha256"] == row["generation"]["prompt_sha256"]
                    and capture["output_sha256"] == row["generation"]["output_sha256"]
                    and capture["seed"] == row["generation"]["seed"]
                    and capture["text"] == row["text"] and capture["max_tokens"] == 100,
                    "Scratchpad is not source-bound to real first-wake public outcome")
            require(binding["execution_id"] == action["execution_id"] and binding["block"] == injection_block(row)
                    and binding["scratchpad_sha256"] == sha(row["text"].encode())
                    and binding["block_sha256"] == sha(binding["block"].encode())
                    and binding["next_prompt_sha256"] == sha(next_prompt.encode())
                    and next_prompt.encode()[binding["start_byte"]:binding["end_byte"]] == binding["block"].encode(),
                    "Scratchpad/next prompt injection binding mismatch")
        qualifying = (all(wake["n_actions"] == 1 for wake in wakes) and not wakes[0]["first_native_accepted"]
                      and wakes[1]["first_native_accepted"] and bool(record["scratchpads"][0]["record"]["text"].strip()))
        episodes.append(dict(episode_id=episode, wakes=wakes, qualifying_correction=qualifying,
                             multi_act=any(wake["n_actions"] > 1 for wake in wakes)))
        if qualifying:
            candidates.append(dict(episode_id=episode, capture_sha256=sha(policy._encoded(record)),
                first_execution_id=first_actions[0]["execution_id"],
                second_execution_id=record["wakes"][1]["actions"][0]["execution_id"],
                status="CANDIDATE_ONLY_REQUIRES_PUBLIC_CONSTRAINT_AUDIT", training_approved=False))
    return dict(boundary=BOUNDARY, denominator=32, ticks=64, episodes=episodes, candidates=candidates,
        first_act_solves=[sum(row["wakes"][tick]["first_native_accepted"] for row in episodes) for tick in (0, 1)],
        first_act_formats=[sum(row["wakes"][tick]["first_action_format_valid"] for row in episodes) for tick in (0, 1)],
        first_act_native_partial=[sum(row["wakes"][tick]["first_native_partial"] for row in episodes) for tick in (0, 1)],
        all_actions=sum(wake["n_actions"] for row in episodes for wake in row["wakes"]),
        first_act_failure_opportunities=sum(bool(row["wakes"][0]["n_actions"]) and not row["wakes"][0]["first_native_accepted"] for row in episodes),
        qualifying_corrections=len(candidates), multi_act_episodes=sum(row["multi_act"] for row in episodes))


def run_arm(preparation, out, mode, *, gym, backend_factory, allow_synthetic=False):
    require(mode in MODES, "unknown mode")
    require(allow_synthetic or backend_factory is formation.local_backend, "GPU execution requires fresh local no-LoRA backend")
    prep, digest, config = validate_preparation(preparation, allow_synthetic=allow_synthetic)
    require(isinstance(gym, native.ReasoningGymGym) and gym.strict_verifier, "native strict verifier required")
    require(allow_synthetic or type(gym) is native.ReasoningGymGym, "synthetic gym forbidden in GPU mode")
    selected_ids(config["episode_ids"], gym, config["prior_source_ids"])
    questions = read(prep / "questions.json")["questions"]
    require([gym.question(episode) for episode in IDS] == [row["question"] for row in questions], "actual native questions changed")
    root = fresh_output(out, [prep, config["model_path"], Path(__file__).resolve().parents[1]])
    root.mkdir(parents=True)
    formation._write(root / "config.json", dict(config, mode=mode, preparation_sha256=digest))
    ledger = Ledger(str(root / "ledger.jsonl"))
    Path(ledger.path).touch(exist_ok=False)
    (root / "generations.jsonl").touch(exist_ok=False)
    try:
        with backend_factory(config["model_path"]) as model:
            observed = BoundedBackend(model, config["model_path"], root, packages.PACKAGES[mode])
            observed.generation_identity()
            records = collect(observed, gym, ledger, mode, questions)
            result = reduce_captures(records)
            formation._write(root / "captures.json", records)
            result.update(status="COMPLETE", mode=mode,
                execution_backend="SYNTHETIC_CPU_FIXTURE" if allow_synthetic else "LOCAL_GPU_BACKEND",
                package_presentations=observed.teacher_presentations,
                cumulative_package_tokens=observed.teacher_presentations * observed.teacher_tokens,
                generated_tokens=sum(row["output_tokens"] for row in observed.captures),
                generation_requests=len(observed.captures),
                package_dose="actual requests including per-ACT Scratchpad; may differ with ACT counts")
        validate_preparation(prep, allow_synthetic=allow_synthetic)
        formation._write(root / "results.json", result)
        return result
    except BaseException as error:
        formation._write(root / "failure.json", dict(error=repr(error), failed_utc=packages.utc()))
        raise
    finally:
        seal(root)


def replay(arm, out):
    source = Path(arm).resolve(strict=True)
    digest = verify_inventory(source)
    config = read(source / "config.json")
    require(config["schema"] == "fresh-parent-correction-v1" and config["boundary"] == BOUNDARY
            and config["protocol"] == PROTOCOL and config["packages"] == packages.PACKAGES
            and config["mode"] in MODES, "only fresh correction captures, never STATIC outputs/ledgers")
    records = read(source / "captures.json")
    ledger_rows = [json.loads(line) for line in (source / "ledger.jsonl").read_bytes().splitlines()]
    require([row["capture"] for row in ledger_rows if row["kind"] == "correction_capture"] == records,
            "capture/real ledger mismatch")
    events = {row["execution_id"]: row for row in ledger_rows if row["kind"] == "act"}
    scratchpads = {row["execution_id"]: row for row in ledger_rows if row["kind"] == "scratchpad"}
    generations = [json.loads(line) for line in (source / "generations.jsonl").read_bytes().splitlines()]
    requests = {row["request_index"]: row for row in generations if row["kind"] == "request"}
    outputs = {row["request_index"]: row for row in generations if row["kind"] == "output"}
    captured_indices = []
    for record in records:
        for wake in record["wakes"]:
            require(all(events.get(row["execution_id"]) == row for row in wake["actions"]), "ACT/real ledger mismatch")
        for scratch in record["scratchpads"]:
            row = scratch["record"]
            require(scratchpads.get(row["execution_id"]) == row, "Scratchpad/real ledger mismatch")
        captures = [wake["generation"] for wake in record["wakes"]] + [scratch["capture"] for scratch in record["scratchpads"]]
        for capture in captures:
            index = capture["request_index"]
            require(index in requests and index in outputs, "missing raw observed generation")
            require(all(capture[key] == requests[index][key] for key in
                        ("prompt", "rendered_prompt", "prompt_sha256", "prompt_tokens", "seed", "max_tokens", "temperature"))
                    and all(capture[key] == outputs[index][key] for key in ("text", "output_sha256")),
                    "capture/observed generation mismatch")
            captured_indices.append(index)
    require(len(captured_indices) == len(set(captured_indices)) and set(captured_indices) == set(requests) == set(outputs),
            "unbound or duplicate observed generation")
    result = reduce_captures(records)
    root = fresh_output(out, [source, config["model_path"], Path(__file__).resolve().parents[1]])
    root.mkdir(parents=True)
    formation._write(root / "reduction.json", dict(result, source_inventory_sha256=digest,
                                                 mode=config["mode"], synthetic=config["synthetic"], replay="CPU_CAPTURE_ONLY"))
    seal(root)
    return result


def execute_pair(preparation, out, *, allow_gpu=False):
    require(allow_gpu, "explicit --allow-gpu required; Main owns full GPU/CUDA/queue check")
    prep, digest, config = validate_preparation(preparation)
    device = supervisor.selected_device()
    require(os.environ.get("V6_MODEL") == config["model_path"], "set pinned V6_MODEL before Python starts")
    root = fresh_output(out, [prep, config["model_path"], Path(__file__).resolve().parents[1]])
    root.mkdir(parents=True)
    formation._write(root / "STARTED.json", dict(preparation_sha256=digest, device=device,
        started_utc=packages.utc(), order=list(MODES), timeout_per_arm=1800,
        scope="Main-reserved GPU only; no automatic launch or queue admission"))
    try:
        results = {}
        for mode in MODES:
            command = [sys.executable, "-B", "-m", "organism_v6.parent_correction_diagnostic",
                       "--preparation", str(prep), "--out", str(root / mode), "--condition", mode, "--allow-gpu"]
            supervisor.run_worker(command, log_path=root / f"{mode}.log", timeout=1800, device=device)
            verify_inventory(root / mode)
            result = read(root / mode / "results.json")
            require(result["status"] == "COMPLETE" and result["mode"] == mode
                    and result["execution_backend"] == "LOCAL_GPU_BACKEND"
                    and result["denominator"] == 32 and result["ticks"] == 64, "incomplete arm")
            results[mode] = result
        formation._write(root / "COMPLETED.json", dict(boundary=BOUNDARY, arms=results,
            dose_caveat="post-outcome request counts can differ; actual package tokens reported per arm"))
        return results
    except BaseException as error:
        formation._write(root / "FAILED.json", dict(error=repr(error)))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--model-path")
    parser.add_argument("--pins", help="JSON {model_path, files}: complete local base inventory")
    parser.add_argument("--prior-source-ids", help='metadata {schema: prior-source-ids-v1, episode_ids: [...]}')
    parser.add_argument("--prior-questions", help='metadata {schema: prior-question-hashes-v1, questions: [{episode_id, question_sha256}]}')
    parser.add_argument("--preparation")
    parser.add_argument("--condition", choices=MODES, help="owned worker only; controller provides 1800s timeout")
    parser.add_argument("--allow-gpu", action="store_true")
    parser.add_argument("--replay")
    args = parser.parse_args(argv)
    if args.replay:
        require(not any((args.preparation, args.allow_gpu, args.condition, args.model_path, args.pins,
                         args.prior_source_ids, args.prior_questions)), "replay accepts only fresh arm and output")
        result = replay(args.replay, args.out)
    elif args.preparation:
        require(args.allow_gpu and not any((args.model_path, args.pins, args.prior_source_ids, args.prior_questions)),
                "explicit --allow-gpu with prepared inputs only")
        if args.condition:
            supervisor.selected_device()
            result = run_arm(args.preparation, args.out, args.condition,
                gym=native.ReasoningGymGym(require_package=True, strict_verifier=True), backend_factory=formation.local_backend)
        else:
            result = execute_pair(args.preparation, args.out, allow_gpu=True)
    else:
        require(args.model_path and args.pins and not args.allow_gpu and not args.condition, "CPU prepare requires model-path and pins")
        pins = read(args.pins)
        require(set(pins) == {"model_path", "files"} and pins["model_path"] == str(Path(args.model_path).resolve(strict=True)),
                "metadata-only model pin path mismatch")
        result = prepare(args.out, args.model_path, pins["files"],
            prior_source_ids=read(args.prior_source_ids) if args.prior_source_ids else None,
            prior_questions=read(args.prior_questions) if args.prior_questions else None)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

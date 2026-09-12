"""Eight observed public-constraint exercises; production only, no fits.

CPU preparation: --out NEW --model-path LOCAL --pins PINS
                --generation-seed {7101,7102,7103} [--prior-source-ids METADATA]
PINS uses {"model_path": absolute_path, "files": relative_path_sha256_map}.
Collision metadata uses {"schema":"prior-source-ids-v1","episode_ids":[...]}.
Without that supplied inventory preparation is pending, never launchable.
Main alone runs --preparation PREP --out NEW --allow-gpu after reserving a
device and setting CUDA_VISIBLE_DEVICES, V6_MODEL and both offline flags.
The controller uses two fresh subprocesses, eight single-record calls each.
It reserves 60 seconds of each 900-second arm for supervisor cleanup (840
seconds maximum worker wait), within a 1800-second controller alarm. Cleanup
failure is not success or permission to start another worker.
CPU analysis: --analyze PAIR --out NEW. No model or native answer is queried.
Prepare one v2 pair per generation seed: three pairs give 48 calls, zero fits.
Execution/replay infer the frozen seed unless --generation-seed is supplied
as an equality assertion. Workers receive it explicitly. These are sampling
seeds, not learner/optimizer seeds. Use the original source to replay v1.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import signal
import sys
import time

from . import model_backend, parent_competency_diagnostic as receipts
from . import parent_material_diagnostic as formation
from . import reasoning_gym_gym as native, run_reasoning_neutral as supervisor
from .mini_sudoku_behavior_material import EVAL_IDS, TRAIN_IDS, board_from_text
from .parent_material_write import _load_tokenizer


IDS = tuple(f"rg/mini_sudoku/{seed}" for seed in range(1851100, 1851108))
MODES = ("process", "format")
SCHEMA = "constraint-check-v2"
GENERATION_SEEDS = (7101, 7102, 7103)
SEED_ROLE = "generation_sampling_only_not_learner_or_optimizer"
PROTOCOL = dict(cases=8, calls_per_arm=8, max_tokens=128, max_input_and_output=4096,
                temperature=0.7, arm_seconds=900, total_seconds=1800,
                worker_wait_seconds=840, cleanup_reserve_seconds=60)
BOUNDARY = dict(origin="externally_generated_observed_exercise", own_failed_act=False,
                clean_ancestry=False, fit=False, adapter=None, live_parent=False,
                stage="production_analysis_only", P1_claim=False, internalization_claim=False,
                lesson_machine_verified=False, training_approved=False,
                record_clean_scope="schema, case binding and all citations only; excludes lesson truth",
                base_origin="UNRESOLVED_LOCAL_HASHES_ONLY")
CARDS = {
    "process": "Before reporting, inspect a row, column or box. Compare values at two distinct "
               "coordinates in that group. Check that both displayed digits equal the digit you cite. "
               "Verify the group and coordinates against the candidate, then write the requested JSON.",
    "format": "Before reporting, review the requested JSON syntax. Use the stated field names, "
              "double quotes for strings and brackets for coordinate lists. Keep integer fields as "
              "integers and the lesson short. Return the requested JSON without headings or fences.",
}
TASK = ("This is an externally generated observed exercise, not your attempted solution. "
        "Find a duplicate in the displayed 4x4 candidate; do not solve or replace the board. "
        "Public rule: digits 1..4 must not repeat within any row, column or 2x2 box. "
        "Coordinates are [row,column], one-based. "
        "Each coordinate component must be an unquoted JSON integer 1..4; do not use numeric strings. "
        "Return exactly one JSON object with keys "
        "case_id, checks, lesson. Give exactly ONE check in the checks list, with keys "
        "group (row, column or box), cells (two distinct coordinates), digit (integer 1..4). "
        "Any real duplicate is acceptable. lesson is your own next-check reminder in at most eight words. "
        "Use no other keys, prose outside JSON, or ACT wrapper.")
require = receipts.require
read = receipts.read
write = formation._write
sha = formation.policy._sha


def validate_generation_seed(generation_seed):
    require(type(generation_seed) is int and generation_seed in GENERATION_SEEDS,
            "generation_seed must be one of 7101, 7102, 7103 (sampling only)")
    return generation_seed


def selected_generation_seed(config, requested=None):
    seed = validate_generation_seed(config["generation_seed"])
    require(config["generation_seed_role"] == SEED_ROLE, "generation seed role mismatch")
    if requested is not None:
        require(validate_generation_seed(requested) == seed, "requested generation seed differs from preparation")
    return seed


def verify_preflight_seed(check, generation_seed):
    require(check["generation_seed"] == generation_seed and all(
        len(check["prompts"][mode]) == 8 and all(type(row["seed"]) is int and row["seed"] == generation_seed
                                               for row in check["prompts"][mode]) for mode in MODES),
        "prepared prompt generation seed mismatch")


@contextmanager
def time_budget(seconds):
    def expired(signum, frame):
        raise TimeoutError("constraint-check wall-clock budget exhausted")

    previous = signal.signal(signal.SIGALRM, expired)
    prior_timer = signal.setitimer(signal.ITIMER_REAL, seconds)
    started = time.monotonic()
    try:
        yield
    finally:
        remaining = max(.000001, prior_timer[0] - (time.monotonic() - started)) if prior_timer[0] else 0
        signal.setitimer(signal.ITIMER_REAL, remaining, prior_timer[1])
        signal.signal(signal.SIGALRM, previous)


def runtime():
    versions = {}
    for name in ("reasoning-gym", "transformers", "tokenizers", "torch", "vllm"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return dict(utc=receipts.utc(), pid=os.getpid(), python=sys.version,
                executable=sys.executable, platform=platform.platform(), versions=versions,
                environment={key: os.environ.get(key) for key in
                             ("CUDA_VISIBLE_DEVICES", "V6_MODEL", "HF_HUB_OFFLINE",
                              "TRANSFORMERS_OFFLINE", "VLLM_WORKER_MULTIPROC_METHOD")},
                backend_settings=dict(max_model_len=16384, gpu_memory_utilization=0.85,
                                      enforce_eager=True, adapter=None),
                dtype="native backend automatic; not measured by this capture")


def source_pins(synthetic=False):
    modules = (sys.modules[__name__], formation, receipts, native, model_backend, supervisor,
               formation.policy, sys.modules[board_from_text.__module__],
               sys.modules[_load_tokenizer.__module__])
    paths = {Path(module.__file__).resolve() for module in modules}
    paths.update((Path(native.FAMILIES_JSON), Path(native.BOOTSTRAP_PATH)))
    if not synthetic:
        require(native.installed_version() == native.PINNED_VERSION, "native version mismatch")
        spec = importlib.util.find_spec("reasoning_gym")
        require(spec is not None and spec.origin, "native source unavailable")
        paths.update(Path(spec.origin).parent.rglob("*.py"))
    return {str(path): formation._hash(path) for path in sorted(paths)}


def make_case(episode_id, question, index):
    require(episode_id == IDS[index], "fixed native source order required")
    puzzle = board_from_text(question, question=True)
    candidate = [[cell or 1 + (row * 2 + row // 2 + column + index) % 4
                  for column, cell in enumerate(values)] for row, values in enumerate(puzzle)]
    filled = [row[:] for row in candidate]
    row, column = index % 4, (index // 4) * 2
    donor = column + 1
    digit = candidate[row][column] % 4 + 1
    candidate[row][column] = candidate[row][donor] = digit
    return dict(case_id=f"c{index + 1:02}", episode_id=episode_id, split="train",
                origin=BOUNDARY["origin"], question=question, question_sha256=sha(question.encode()),
                source_board=puzzle, source_board_sha256=sha(formation.policy._encoded(puzzle)),
                filled_candidate=filled, candidate=candidate,
                candidate_sha256=sha(formation.policy._encoded(candidate)),
                program=dict(recipe="fill-public-blanks-cyclic-then-overwrite-pair-v1", index=index,
                             cells=[[row + 1, column + 1], [row + 1, donor + 1]], digit=digit,
                             before=[filled[row][column], filled[row][donor]],
                             givens_may_be_corrupted=True, reference_answer_accessed=False))


def cases_from_gym(gym, prior_ids):
    require(gym.strict_verifier, "strict native gym required")
    excluded = set(TRAIN_IDS) | set(EVAL_IDS)
    for split in ("canary", "gate", "exam"):
        excluded.update(gym.benchmarks(split))
    if prior_ids is not None:
        require(isinstance(prior_ids, dict) and set(prior_ids) == {"schema", "episode_ids"}
                and prior_ids["schema"] == "prior-source-ids-v1"
                and isinstance(prior_ids["episode_ids"], list)
                and all(isinstance(value, str) for value in prior_ids["episode_ids"]),
                "metadata-only prior-source-ids-v1 required")
        excluded.update(prior_ids["episode_ids"])
    require(not set(IDS) & excluded, "source ID collision; no replacement hunt")
    require(all(gym.split_of(episode) == "train" for episode in IDS), "non-training source")
    cases = [make_case(episode, gym.question(episode), index) for index, episode in enumerate(IDS)]
    unique_cases(cases)
    return cases


def unique_cases(cases):
    require(len(cases) == 8, "exactly eight cases required")
    for key in ("question_sha256", "candidate_sha256"):
        require(len({case[key] for case in cases}) == 8, f"duplicate actual {key}; no replacements")


def prompt_for(case, mode):
    board = "\n".join(" ".join(map(str, row)) for row in case["candidate"])
    return f"{TASK}\n\nParent card:\n{CARDS[mode]}\n\ncase_id: {case['case_id']}\nCandidate:\n{board}"


def preflight(cases, tokenizer, *, generation_seed):
    generation_seed = validate_generation_seed(generation_seed)
    rows = {}
    for mode in MODES:
        rows[mode] = []
        for case in cases:
            prompt = prompt_for(case, mode)
            rendered = tokenizer.apply_chat_template([dict(role="user", content=prompt)],
                                                      tokenize=False, add_generation_prompt=True)
            count = len(tokenizer.encode(rendered, add_special_tokens=False))
            require(count + PROTOCOL["max_tokens"] <= PROTOCOL["max_input_and_output"],
                    "input plus output headroom exceeds 4096; no truncation")
            rows[mode].append(dict(case_id=case["case_id"], prompt=prompt, rendered_prompt=rendered,
                prompt_sha256=sha(prompt.encode()), rendered_sha256=sha(rendered.encode()),
                prompt_tokens=count, seed=generation_seed, max_tokens=128))
    tokens = {mode: len(tokenizer.encode(card, add_special_tokens=False)) for mode, card in CARDS.items()}
    return dict(prompts=rows, card_tokens=tokens, generation_seed=generation_seed,
                card_sha256={mode: sha(card.encode()) for mode, card in CARDS.items()},
                input_tokens_equal=all(left["prompt_tokens"] == right["prompt_tokens"] for left, right in
                                       zip(rows["process"], rows["format"])),
                package_tokens_equal=tokens["process"] == tokens["format"],
                token_matching="measured, not assumed; no padding or answer-dependent edits")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def score_record(text, case):
    result = dict(format_valid=False, grounded=0, valid_citations=0, invalid_citations=0,
                  whole_structured_record_clean=False, lesson_machine_verified=False,
                  training_approved=False, reasons=[])
    try:
        record = json.loads(text, object_pairs_hook=_unique_object)
        require(isinstance(record, dict) and set(record) == {"case_id", "checks", "lesson"}, "record keys")
        require(isinstance(record["case_id"], str) and isinstance(record["lesson"], str)
                and record["lesson"].strip(), "case_id and nonempty own lesson required")
        checks = record["checks"]
        require(isinstance(checks, list) and 1 <= len(checks) <= 3, "one to three checks required")
        for check in checks:
            require(isinstance(check, dict) and set(check) == {"group", "cells", "digit"}, "check keys")
            require(check["group"] in ("row", "column", "box") and type(check["digit"]) is int
                    and 1 <= check["digit"] <= 4, "group or digit")
            require(isinstance(check["cells"], list) and len(check["cells"]) == 2
                    and all(isinstance(cell, list) and len(cell) == 2
                            and all(type(value) is int and 1 <= value <= 4 for value in cell)
                            for cell in check["cells"]), "coordinate shape or range")
    except (ValueError, TypeError) as error:
        result["reasons"].append("invalid_schema: " + str(error))
        return result
    result["format_valid"] = True
    if record["case_id"] != case["case_id"]:
        result["reasons"].append("wrong_case_id")
        return result
    seen = set()
    for index, check in enumerate(checks):
        first, second = check["cells"]
        same_unit = {"row": first[0] == second[0], "column": first[1] == second[1],
                     "box": ((first[0] - 1) // 2, (first[1] - 1) // 2) ==
                            ((second[0] - 1) // 2, (second[1] - 1) // 2)}[check["group"]]
        equal = all(case["candidate"][row - 1][column - 1] == check["digit"]
                    for row, column in check["cells"])
        key = (check["group"], check["digit"], tuple(sorted(map(tuple, check["cells"]))))
        if first == second or not same_unit or not equal:
            result["invalid_citations"] += 1
            result["reasons"].append(f"check_{index}: not a concrete duplicate in the named group")
        elif key in seen:
            result["reasons"].append(f"check_{index}: repeated citation, not counted twice")
        else:
            seen.add(key)
            result["valid_citations"] += 1
    result["grounded"] = int(result["valid_citations"] > 0)
    result["whole_structured_record_clean"] = result["valid_citations"] == len(checks)
    return result


def prepare(out, model_path, expected_files, *, generation_seed, prior_ids=None, gym=None, tokenizer=None):
    generation_seed = validate_generation_seed(generation_seed)
    synthetic = gym is not None or tokenizer is not None
    model = Path(model_path).resolve(strict=True)
    require(formation.local_files(model) == expected_files, "local model pins mismatch")
    root = receipts.fresh_output(out, [model, Path(__file__).resolve().parents[1]])
    gym = gym if gym is not None else native.ReasoningGymGym(require_package=True, strict_verifier=True)
    tokenizer = tokenizer if tokenizer is not None else _load_tokenizer(str(model))
    cases = cases_from_gym(gym, prior_ids)
    check = preflight(cases, tokenizer, generation_seed=generation_seed)
    check.update(status="PENDING_COLLISION_CHECK" if prior_ids is None else
                 "SYNTHETIC_CPU_ONLY" if synthetic else "READY",
                 collision_scope="supplied ID inventory and configured held IDs only; global/question overlap unverified")
    config = dict(schema=SCHEMA, model_path=str(model), expected_files=expected_files,
                  generation_seed=generation_seed, generation_seed_role=SEED_ROLE,
                  sources=source_pins(synthetic), synthetic=synthetic, protocol=PROTOCOL,
                  cards=CARDS, task=TASK, boundary=BOUNDARY, episode_ids=list(IDS), prior_ids=prior_ids)
    root.mkdir(parents=True)
    write(root / "config.json", config)
    write(root / "cases.json", cases)
    write(root / "preflight.json", check)
    write(root / "runtime.json", dict(runtime(), generation_seed=generation_seed, generation_seed_role=SEED_ROLE))
    receipts.seal(root)
    return check


def validate_preparation(preparation, allow_synthetic=False):
    prep = Path(preparation).resolve(strict=True)
    digest = receipts.verify_inventory(prep)
    config, check = read(prep / "config.json"), read(prep / "preflight.json")
    require(config["schema"] == SCHEMA and config["protocol"] == PROTOCOL
            and config["cards"] == CARDS and config["task"] == TASK and config["boundary"] == BOUNDARY
            and config["episode_ids"] == list(IDS), "prepared protocol changed")
    verify_preflight_seed(check, selected_generation_seed(config))
    require((not config["synthetic"] and check["status"] == "READY") or
            (allow_synthetic and config["synthetic"] and check["status"] == "SYNTHETIC_CPU_ONLY"),
            "preparation pending or synthetic/native mismatch")
    require(config["sources"] == source_pins(config["synthetic"]), "source pins changed")
    require(formation.local_files(config["model_path"]) == config["expected_files"], "model pins changed")
    cases = read(prep / "cases.json")
    require(len(cases) == 8 and cases == [make_case(episode, case["question"], index)
            for index, (episode, case) in enumerate(zip(IDS, cases))], "case program/provenance changed")
    unique_cases(cases)
    return prep, digest, config, cases, check


class CaptureBackend(formation.ObservedBackend):
    """Reuse identity and raw JSONL capture, without the old 100/400 ceiling."""

    def __init__(self, *args, synthetic=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.synthetic = synthetic

    def generate_record(self, row):
        self.generation_identity()
        self._append([dict(kind="request", request_index=self.requests, **row,
                           source_identity=self.identity, temperature=PROTOCOL["temperature"])])
        if self.synthetic:
            outputs = self.model.batch([row["prompt"]], max_tokens=128,
                                       temperature=PROTOCOL["temperature"], seeds=[row["seed"]])
            raw = dict(kind="raw_return", request_index=self.requests, synthetic=True, outputs=outputs)
            self._append([raw])
            require(isinstance(outputs, (list, tuple)) and len(outputs) == 1
                    and isinstance(outputs[0], str), "incomplete generation")
            text = outputs[0]
            metadata = dict(usage_source="SYNTHETIC_RETOKENIZATION_NOT_ACTUAL_USAGE",
                            actual_output_tokens=None, actual_prompt_tokens=None,
                            synthetic_retokenized_output_tokens=len(self.tokenizer.encode(text, add_special_tokens=False)),
                            finish_reason="synthetic_fixture", stop_reason=None)
        else:
            from vllm import SamplingParams

            params = SamplingParams(max_tokens=128, temperature=PROTOCOL["temperature"], seed=row["seed"])
            requests = self.model.llm.generate([row["rendered_prompt"]], [params], lora_request=None, use_tqdm=False)
            raw = dict(kind="raw_return", request_index=self.requests, synthetic=False,
                       requests=[dict(request_id=request.request_id, prompt=request.prompt,
                                      prompt_token_ids=list(request.prompt_token_ids), finished=request.finished,
                                      outputs=[dict(text=output.text, token_ids=list(output.token_ids),
                                                    finish_reason=output.finish_reason, stop_reason=output.stop_reason)
                                               for output in request.outputs]) for request in requests])
            self._append([raw])
            require(len(raw["requests"]) == 1 and len(raw["requests"][0]["outputs"]) == 1, "incomplete native generation")
            request = raw["requests"][0]
            output = request["outputs"][0]
            text = output["text"]
            metadata = dict(usage_source="NATIVE_VLLM_TOKEN_IDS", actual_output_tokens=len(output["token_ids"]),
                            actual_prompt_tokens=len(request["prompt_token_ids"]), finish_reason=output["finish_reason"],
                            stop_reason=output["stop_reason"])
        capture = dict(request_index=self.requests, case_id=row["case_id"], text=text,
                       generation_seed=row["seed"],
                       output_sha256=sha(text.encode()), **metadata,
                       input_truncated=False, output_rewritten=False)
        self._append([dict(kind="output", **capture)])
        self.requests += 1
        if not self.synthetic:
            require(all(type(token) is int and token >= 0 for token in
                        request["prompt_token_ids"] + output["token_ids"]), "native token IDs missing or invalid")
            require(request["prompt"] == row["rendered_prompt"]
                    and request["prompt_token_ids"] == list(self.tokenizer.encode(row["rendered_prompt"], add_special_tokens=False)),
                    "native prompt/token IDs differ; truncation or tokenizer mismatch")
            require(request["finished"] and output["finish_reason"] == "stop"
                    and len(output["token_ids"]) <= 128,
                    "protocol failure: native length/unfinished/unknown stop; raw output preserved")
        self.generation_identity()
        return capture


def run_arm(preparation, out, mode, *, generation_seed=None, backend_factory=formation.local_backend, allow_synthetic=False):
    with time_budget(PROTOCOL["arm_seconds"]):
        return _run_arm(preparation, out, mode, generation_seed=generation_seed,
                        backend_factory=backend_factory, allow_synthetic=allow_synthetic)


def _run_arm(preparation, out, mode, *, generation_seed, backend_factory, allow_synthetic):
    started = time.monotonic()
    require(mode in MODES, "unknown arm")
    require(allow_synthetic or backend_factory is formation.local_backend, "fresh native backend required")
    prep, digest, config, cases, check = validate_preparation(preparation, allow_synthetic)
    generation_seed = selected_generation_seed(config, generation_seed)
    root = receipts.fresh_output(out, [prep, config["model_path"], Path(__file__).resolve().parents[1]])
    root.mkdir(parents=True)
    write(root / "config.json", dict(config, mode=mode, preparation_sha256=digest))
    write(root / "runtime.json", dict(runtime(), generation_seed=generation_seed, generation_seed_role=SEED_ROLE))
    try:
        captures = []
        with backend_factory(config["model_path"]) as model:
            current = preflight(cases, model.tok, generation_seed=generation_seed)
            require(all(current[key] == check[key] for key in current), "runtime tokenizer differs")
            observed = CaptureBackend(model, config["model_path"], root, CARDS[mode], synthetic=config["synthetic"])
            for row, case in zip(current["prompts"][mode], cases):
                require(time.monotonic() - started < 900, "arm deadline exhausted")
                capture = observed.generate_record(row)
                capture["score"] = score_record(capture["text"], case)
                captures.append(capture)
        require(time.monotonic() - started < 900, "arm deadline exhausted after cleanup")
        result = dict(status="COMPLETE", mode=mode, preparation_sha256=digest,
                      generation_seed=generation_seed, generation_seed_role=SEED_ROLE,
                      synthetic=config["synthetic"], generation_calls=observed.requests,
                      execution_backend="SYNTHETIC_CPU_FIXTURE" if config["synthetic"] else "LOCAL_GPU_BACKEND",
                      grounded_citation_count=sum(row["score"]["grounded"] for row in captures),
                      cases_with_valid_citation=sum(row["score"]["grounded"] for row in captures),
                      invalid_citation_count=sum(row["score"]["invalid_citations"] for row in captures),
                      whole_structured_record_clean_count=sum(row["score"]["whole_structured_record_clean"] for row in captures),
                      denominator=8, format_count=sum(row["score"]["format_valid"] for row in captures),
                      elapsed_seconds=time.monotonic() - started, records=captures,
                      card_tokens=current["card_tokens"][mode], presentations=8, boundary=BOUNDARY)
        write(root / "results.json", result)
        return result
    except BaseException as error:
        write(root / "failure.json", dict(status="FAILED", error=repr(error), utc=receipts.utc(),
                                         complete=False, raw_outputs="preserved in generations.jsonl when returned"))
        raise
    finally:
        receipts.seal(root)


def analyze_pair(pair, preparation, *, generation_seed=None):
    pair, prep = Path(pair).resolve(strict=True), Path(preparation).resolve(strict=True)
    digest = receipts.verify_inventory(prep)
    cases, check = read(prep / "cases.json"), read(prep / "preflight.json")
    prepared = read(prep / "config.json")
    require(prepared["schema"] == SCHEMA and prepared["episode_ids"] == list(IDS)
            and prepared["protocol"] == PROTOCOL and prepared["cards"] == CARDS
            and prepared["task"] == TASK and prepared["boundary"] == BOUNDARY,
            "captured protocol mismatch")
    generation_seed = selected_generation_seed(prepared, generation_seed)
    verify_preflight_seed(check, generation_seed)
    require(check["status"] == ("SYNTHETIC_CPU_ONLY" if prepared["synthetic"] else "READY"), "captured preparation pending")
    require(len(cases) == 8 and cases == [make_case(episode, case["question"], index)
            for index, (episode, case) in enumerate(zip(IDS, cases))], "captured case mismatch")
    unique_cases(cases)
    arms, pids = {}, []
    for mode in MODES:
        root = pair / mode
        receipts.verify_inventory(root)
        require(not (root / "failure.json").exists(), "arm failed")
        config, result = read(root / "config.json"), read(root / "results.json")
        require(config == dict(prepared, mode=mode, preparation_sha256=digest), "arm model/panel/settings differ")
        require(result["synthetic"] == prepared["synthetic"] and result["boundary"] == BOUNDARY
                and result["execution_backend"] == ("SYNTHETIC_CPU_FIXTURE" if prepared["synthetic"] else "LOCAL_GPU_BACKEND"),
                "synthetic/native result mismatch")
        run_runtime = read(root / "runtime.json")
        require(result["generation_seed"] == run_runtime["generation_seed"] == generation_seed
                and result["generation_seed_role"] == run_runtime["generation_seed_role"] == SEED_ROLE,
                "arm/runtime/result generation seed mismatch")
        pids.append(run_runtime["pid"])
        require(config["mode"] == result["mode"] == mode and
                config["preparation_sha256"] == result["preparation_sha256"] == digest
                and result["status"] == "COMPLETE" and result["generation_calls"] == 8,
                "completion/arm/pair mismatch")
        events = [json.loads(line) for line in (root / "generations.jsonl").read_text().splitlines()]
        require([row["kind"] for row in events] == ["request", "raw_return", "output"] * 8,
                "exactly eight generation calls required")
        scores = []
        for index, case in enumerate(cases):
            request, raw, output = events[index * 3:index * 3 + 3]
            expected = check["prompts"][mode][index]
            require(all(row["request_index"] == index for row in (request, raw, output))
                    and all(request[key] == value for key, value in expected.items())
                    and request["temperature"] == PROTOCOL["temperature"]
                    and request["source_identity"] == model_backend.configured_generation_identity(config["model_path"], None),
                    "generation settings/identity/prompt mismatch")
            require(raw["synthetic"] == prepared["synthetic"], "raw synthetic/native mismatch")
            if prepared["synthetic"]:
                require(raw["outputs"] == [output["text"]] and output["actual_output_tokens"] is None
                        and output["actual_prompt_tokens"] is None
                        and output["usage_source"] == "SYNTHETIC_RETOKENIZATION_NOT_ACTUAL_USAGE", "synthetic raw output mismatch")
            else:
                require(len(raw["requests"]) == 1 and len(raw["requests"][0]["outputs"]) == 1, "native raw cardinality")
                native_request = raw["requests"][0]
                native_output = native_request["outputs"][0]
                require(all(type(token) is int and token >= 0 for token in
                            native_request["prompt_token_ids"] + native_output["token_ids"]), "invalid captured native token IDs")
                require(native_request["finished"] and native_request["prompt"] == expected["rendered_prompt"]
                        and len(native_request["prompt_token_ids"]) == expected["prompt_tokens"]
                        and native_output["finish_reason"] == output["finish_reason"] == "stop"
                        and native_output["stop_reason"] == output["stop_reason"]
                        and native_output["text"] == output["text"]
                        and len(native_output["token_ids"]) == output["actual_output_tokens"] <= 128
                        and len(native_request["prompt_token_ids"]) == output["actual_prompt_tokens"]
                        and output["usage_source"] == "NATIVE_VLLM_TOKEN_IDS", "native stop/token/output mismatch")
            require(output["output_sha256"] == sha(output["text"].encode())
                    and output["case_id"] == case["case_id"] and output["generation_seed"] == generation_seed,
                    "raw output/case/generation seed mismatch")
            score = score_record(output["text"], case)
            require(result["records"][index] == dict({key: value for key, value in output.items() if key != "kind"},
                                                    score=score), "summary differs from raw output")
            scores.append(dict(case_id=case["case_id"], **score))
        grounded = sum(row["grounded"] for row in scores)
        formats = sum(row["format_valid"] for row in scores)
        invalid = sum(row["invalid_citations"] for row in scores)
        clean = sum(row["whole_structured_record_clean"] for row in scores)
        require(result["grounded_citation_count"] == grounded and result["format_count"] == formats
                and result["cases_with_valid_citation"] == grounded and result["invalid_citation_count"] == invalid
                and result["whole_structured_record_clean_count"] == clean
                and result["card_tokens"] == check["card_tokens"][mode] and result["presentations"] == 8
                and result["denominator"] == 8 and len(result["records"]) == 8, "summary count mismatch")
        arms[mode] = dict(grounded_citation_count=grounded, cases_with_valid_citation=grounded,
                          denominator=8, format_count=formats, invalid_citation_count=invalid,
                          whole_structured_record_clean_count=clean, cases=scores,
                          parent_presentations=8, standalone_card_tokens_per_presentation=check["card_tokens"][mode],
                          actual_output_tokens=None if prepared["synthetic"] else
                          sum(row["actual_output_tokens"] for row in result["records"]),
                          actual_prompt_tokens=None if prepared["synthetic"] else
                          sum(row["actual_prompt_tokens"] for row in result["records"]))
    require(prepared["synthetic"] or len(set(pids)) == 2, "two fresh model processes required")
    return dict(status="COMPLETE", generation_calls=16, arms=arms, synthetic=prepared["synthetic"],
                generation_seed=generation_seed, generation_seed_role=SEED_ROLE,
                execution_backend="SYNTHETIC_CPU_FIXTURE" if prepared["synthetic"] else "LOCAL_GPU_BACKEND",
                verification_scope="captured inventories and pair receipts; absolute source/model paths not rehashed in CPU replay",
                process_minus_format=arms["process"]["grounded_citation_count"] - arms["format"]["grounded_citation_count"],
                boundary=BOUNDARY, token_metadata={key: check[key] for key in
                ("card_tokens", "input_tokens_equal", "package_tokens_equal", "token_matching")})


def execute_pair(preparation, out, *, generation_seed=None):
    with time_budget(PROTOCOL["total_seconds"]):
        return _execute_pair(preparation, out, generation_seed=generation_seed)


def _execute_pair(preparation, out, *, generation_seed):
    started = time.monotonic()
    prep, digest, config, _, _ = validate_preparation(preparation)
    generation_seed = selected_generation_seed(config, generation_seed)
    device = supervisor.selected_device()
    require(os.environ.get("V6_MODEL") == model_backend.MODEL == config["model_path"], "set pinned V6_MODEL before Python")
    root = receipts.fresh_output(out, [prep, config["model_path"], Path(__file__).resolve().parents[1]])
    root.mkdir(parents=True)
    write(root / "STARTED.json", dict(preparation=str(prep), preparation_sha256=digest, runtime=runtime(),
                                      generation_seed=generation_seed, generation_seed_role=SEED_ROLE))
    try:
        for mode in MODES:
            remaining = 1800 - (time.monotonic() - started)
            reserve = PROTOCOL["cleanup_reserve_seconds"]
            require(remaining > reserve, "pair deadline exhausted; retain cleanup reserve")
            command = [sys.executable, "-B", "-m", "organism_v6.constraint_check_diagnostic",
                       "--preparation", str(prep), "--out", str(root / mode), "--condition", mode,
                       "--generation-seed", str(generation_seed), "--allow-gpu"]
            supervisor.run_worker(command, log_path=root / f"{mode}.log",
                                  timeout=min(PROTOCOL["worker_wait_seconds"], remaining - reserve), device=device)
        require(time.monotonic() - started < 1800, "pair deadline exhausted after cleanup")
        result = analyze_pair(root, prep, generation_seed=generation_seed)
        require(time.monotonic() - started < 1800, "pair deadline exhausted during analysis")
        result["elapsed_seconds"] = time.monotonic() - started
        write(root / "COMPLETED.json", result)
        return result
    except BaseException as error:
        write(root / "FAILED.json", dict(error=repr(error), utc=receipts.utc()))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--model-path")
    parser.add_argument("--pins")
    parser.add_argument("--prior-source-ids")
    parser.add_argument("--preparation")
    parser.add_argument("--condition", choices=MODES)
    parser.add_argument("--allow-gpu", action="store_true")
    parser.add_argument("--analyze")
    parser.add_argument("--generation-seed", type=int, choices=GENERATION_SEEDS)
    args = parser.parse_args(argv)
    if args.analyze:
        require(not any((args.allow_gpu, args.condition, args.model_path, args.pins, args.prior_source_ids)), "analysis is read-only CPU")
        prep = args.preparation or read(Path(args.analyze) / "STARTED.json")["preparation"]
        result = analyze_pair(args.analyze, prep, generation_seed=args.generation_seed)
        root = receipts.fresh_output(args.out, [args.analyze, prep, Path(__file__).resolve().parents[1]])
        root.mkdir(parents=True)
        write(root / "analysis.json", result)
        receipts.seal(root)
    elif args.preparation:
        require(args.allow_gpu and not any((args.model_path, args.pins, args.prior_source_ids)), "explicit GPU opt-in required")
        if args.condition:
            supervisor.selected_device()
            result = run_arm(args.preparation, args.out, args.condition, generation_seed=args.generation_seed)
        else:
            result = execute_pair(args.preparation, args.out, generation_seed=args.generation_seed)
    else:
        require(args.model_path and args.pins and not args.allow_gpu and not args.condition, "CPU preparation requires model and pins")
        validate_generation_seed(args.generation_seed)
        pins = read(args.pins)
        require(pins["model_path"] == str(Path(args.model_path).resolve(strict=True)), "pin model path mismatch")
        result = prepare(args.out, args.model_path, pins["files"],
                         generation_seed=args.generation_seed,
                         prior_ids=read(args.prior_source_ids) if args.prior_source_ids else None)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

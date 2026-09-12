"""Read-only CPU terminal reduction; stdout JSON, never launch or read remote weights.

The capture JSON has schema correction-utility-capture-v1, synthetic (boolean),
material and panel paths, and recipients: six {arm, seed, logs, adapter} objects.
All paths are relative to the capture JSON's directory. Preserve original bytes
in extracted logs/material/adapter directories; adapter weights alone may be
omitted. Do not rewrite absolute remote paths inside the captured documents.

Example: python3 -B -m gpu.astra_correction_utility_analysis --capture INDEX.json
--capture-sha256 SHA256. Redirect stdout to a new report outside the capture.
Incomplete captures fail closed; this is not a running-job progress reducer.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
import zlib

from organism_v6 import batch_loop
from organism_v6 import neutral_pair_custody as custody
from organism_v6.preschool_reasoning import InvalidFeedback, facts_from_act, outcome_block


ARMS = ("whole_raw", "act_only")
SEEDS = (0, 1, 2)
PANEL_SHA256 = "11b87e8b901978bcb331f2d126632517214e2a62c82221a47afd5baedd01cb2e"
EPISODES = [f"rg/mini_sudoku/{1900000 + suffix}" for suffix in
            (0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
             43, 44, 45, 46, 47, 48, 49, 70, 71, 72, 73, 74, 75)]
BUDGET = dict(budget_ticks=1, gen_seed=0, max_episodes=32, max_model_len=4096,
              scratchpad_max_tokens=100, seed_salt=15420, total_token_budget=48000,
              wake_max_tokens=400)
TARGETS = dict(whole_raw="2bb4313d7faf713090143fb8b79148422295aee3610b63c15437666983d2587d",
               act_only="74887f842a07dd4e8e0992ecdc50d903859be33e5684c4709bdf5ceb4c084575")
PROJECTIONS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
WEIGHTS = {"adapter_model.safetensors", "adapter_model.bin"}
RECIPE = dict(rank=8, alpha=16, dropout=.05, lr=1e-4, epochs=3, max_len=4096,
              batch_size=1, grad_accum=1, pack=False, optimizer="adamw",
              target_modules=PROJECTIONS, layers="all", svd_init=False, freeze_a=False,
              chat_template=True, add_eos=True, grad_checkpoint=True, max_steps=96,
              device="cuda", dtype="bf16", overflow="split")
LIMITATIONS = [
    "One selected source experience, 32 explicit replays and 96 steps per fit, not 32 discoveries.",
    "Three recipient seeds per arm; episodes and repeated OFF runs are not independent learners.",
    "Equal optimizer steps are not equal target tokens, input tokens, compute or information.",
    "Development same-gym material utility only: no P1, H1/H2, parenting, retention or generalization claim.",
    "First ACT acceptance uses recorded native measured feedback, not independent board re-solving.",
    "Strict format is a separate text diagnostic; it does not replace native first-ACT acceptance.",
    "Absolute remote paths are labels only: no remote code, model or omitted weights are opened or rehashed.",
    "Captured receipt/hash consistency is not original-source replay, GPU-state or official model-origin authentication.",
    "Generation logs contain text and reserved token caps, not actual tokenizer usage or finish reasons.",
]
require = custody._require


def text_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def finite(value, minimum=0):
    return type(value) in (int, float) and math.isfinite(value) and value >= minimum


def remote(path):
    require(isinstance(path, str) and path.startswith("/") and ".." not in PurePosixPath(path).parts,
            "invalid recorded remote path")
    return PurePosixPath(path)


class Inputs:
    def __init__(self):
        self.hashes = {}
        self.directories = {}

    def path(self, root, name):
        require(isinstance(name, str) and name and "\\" not in name, "invalid capture path")
        parts = PurePosixPath(name)
        require(not parts.is_absolute() and ".." not in parts.parts and name not in (".", ".."),
                "capture paths must be relative and contained")
        path = root / name
        require(not any(parent.is_symlink() for parent in (path, *path.parents)), "symlink capture path")
        require(path.exists(), "missing captured artifact: " + str(path))
        return path

    def hash(self, path):
        require(path.is_file() and not any(parent.is_symlink() for parent in (path, *path.parents)),
                "unsafe captured file: " + str(path))
        digest = custody._digest(path)
        require(self.hashes.setdefault(str(path), digest) == digest, "input changed during reduction")
        return digest

    def read(self, path, jsonl=False):
        before = self.hash(path)
        text = path.read_text(encoding="utf-8")
        def decode(value):
            result = json.loads(value, object_pairs_hook=custody._object,
                                parse_constant=custody._invalid_constant)
            require(isinstance(result, dict), "JSON object required")
            return result
        value = [decode(line) for line in text.splitlines() if line.strip()] if jsonl else decode(text)
        require(self.hash(path) == before, "input changed while reading")
        return value

    def inventory(self, root):
        require(root.is_dir() and not any(parent.is_symlink() for parent in (root, *root.parents)),
                "unsafe capture directory")
        entries = {}
        for path in root.rglob("*"):
            require(not path.is_symlink(), "symlink in capture directory")
            require(path.is_file() or path.is_dir(), "special file in capture directory")
            entries[path.relative_to(root).as_posix()] = "file" if path.is_file() else "directory"
        require(self.directories.setdefault(str(root), entries) == entries, "capture directory changed")
        return {name for name, kind in entries.items() if kind == "file"}

    def verify(self):
        for name in list(self.hashes):
            self.hash(Path(name))
        for name in list(self.directories):
            self.inventory(Path(name))


def material_inputs(root, panel_path, inputs):
    files = inputs.inventory(root)
    inventory = inputs.read(root / "artifact_hashes.json")["files"]
    require(files == set(inventory) | {"artifact_hashes.json"}, "material inventory differs")
    for name, expected in inventory.items():
        require(custody._sha(expected) and inputs.hash(inputs.path(root, name)) == expected,
                "material artifact hash mismatch")
    prepared = inputs.read(root / "preparation.json")
    require(prepared["status"] == "READY_CPU_PREPARATION_ONLY" and prepared["synthetic"] is False
            and prepared["unique_events"] == 1 and prepared["explicit_replays_per_arm"] == 32
            and prepared["recipient_seeds"] == list(SEEDS) and prepared["optimizer_steps_per_recipient"] == 96
            and prepared["token_matched"] is False, "wrong preparation scope")
    require(prepared["selection"]["scratchpad_sha256"] == TARGETS["whole_raw"]
            and prepared["selection"]["act_sha256"] == TARGETS["act_only"], "wrong selected source event")
    require(inputs.hash(panel_path) == PANEL_SHA256, "prospective panel hash mismatch")
    panel = inputs.read(panel_path)
    require(panel["status"] == "NATIVE_PANEL_PREPARED_NO_INFERENCE" and panel["episode_ids"] == EPISODES
            and panel["prospective_probe"] == BUDGET and panel["model_path"] == prepared["model_path"]
            and panel["source_act_sha256"] == TARGETS["act_only"], "wrong native panel or settings")
    require([row["episode_id"] for row in panel["questions"]] == EPISODES, "question order mismatch")
    for row in panel["questions"]:
        require(text_hash(row["initial_prompt"]) == row["initial_prompt_sha256"]
                and text_hash(row["question"]) == row["question_sha256"], "panel prompt hash mismatch")
    return prepared, panel


def fit_inputs(root, material, prepared, arm, seed, spec, completed, inputs):
    inputs.inventory(root)
    require(not (root / "EMPTY_CORPUS").exists(), "empty training corpus")
    inputs.hash(root / "DONE")
    commands = inputs.read(material / arm / "training_commands.json")["commands"]
    selected = [command for command in commands if command["seed"] == seed]
    require(len(selected) == 1, "missing or duplicate selected training command")
    command = selected[0]
    manifest = inputs.read(root / "train_manifest.json")
    config = manifest["config"]
    require(config == command["config"] and all(config.get(key) == value for key, value in RECIPE.items())
            and type(config["seed"]) is int and config["seed"] == seed
            and config["model"] == prepared["model_path"], "fit arm/seed/recipe mismatch")
    destination = str(remote(prepared["recipient_root"]) / arm / f"seed{seed}")
    require(command["output"] == spec["adapter_path"] == destination
            and command["fresh_base"] is True and command["adapter_input"] is None, "wrong recipient path/start")
    require(manifest["steps"] == completed["steps"] == 96 and manifest["nonfinite_batches"] == 0
            and finite(manifest["final_loss"]) and manifest.get("empty") is False
            and manifest["base_model"] == config["model"], "incomplete/nonfinite fit")
    require(inputs.hash(root / "train_manifest.json") == completed["manifest_sha256"], "completion manifest hash")
    corpus_hash = inputs.hash(material / arm / "corpus.json")
    corpus = manifest["corpus"]
    require(corpus["sha256"] == command["corpus_sha256"] == corpus_hash
            and corpus["n_items"] == corpus["n_encoded"] == 32 and corpus["n_skipped_no_target"] == 0,
            "wrong corpus or dropped replays")
    require(all(manifest["truncation"][key] == 0 for key in
                ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")),
            "training truncation/splitting")
    tokenization = inputs.read(material / arm / "tokenizer_preflight.json")
    require(tokenization["status"] == "PASS_ACTUAL_TOKENIZER_V3_ENCODE_AND_COLLATE"
            and tokenization["optimizer_steps"] == 96 and tokenization["add_eos"] is True
            and tokenization["truncation"] is False and tokenization["splits"] == 0, "invalid token preflight")
    token_rows = tokenization["rows"]
    require(len(token_rows) == 32 and [row["replay_index"] for row in token_rows] == list(range(32)),
            "token preflight replay coverage")
    for row in token_rows:
        require(row["raw_target_sha256"] == TARGETS[arm] and row["supervised_eos_tokens"] == 1
                and row["supervised_context_tokens"] == row["supervised_padding_tokens"] == 0
                and row["truncation"] is False and row["splits"] == 0 and row["target_roundtrip_exact"] is True,
                "token preflight source/mask mismatch")
        require({key: value for key, value in row.items() if key != "replay_index"}
                == {key: value for key, value in token_rows[0].items() if key != "replay_index"},
                "token preflight replays differ")
    target, total = manifest["tokens"]["target"], manifest["tokens"]["total"]
    require(type(target) is int and type(total) is int and 0 < target < total
            and target == tokenization["supervised_tokens_per_epoch"]
            and total == tokenization["input_tokens_per_epoch"]
            and manifest["train_tokens_seen"] == tokenization["input_tokens_all_epochs"] == 3 * total
            and tokenization["supervised_tokens_all_epochs"] == 3 * target, "fit token dose mismatch")
    require(sum(row["input_tokens"] for row in token_rows) == total
            and sum(row["supervised_target_tokens"] for row in token_rows) == target, "token preflight sums mismatch")
    adapter = inputs.read(root / "adapter_config.json")
    require(adapter["r"] == 8 and adapter["lora_alpha"] == 16 and adapter["lora_dropout"] == .05
            and adapter["bias"] == "none" and set(adapter["target_modules"]) == set(PROJECTIONS),
            "saved LoRA configuration mismatch")
    hashes = spec["expected_adapter_hashes"]
    require(hashes == completed["adapter_sha256"] and
            {"DONE", "train_manifest.json", "train_meta.json", "adapter_config.json"} <= hashes.keys()
            and len(WEIGHTS & hashes.keys()) == 1, "incomplete adapter inventory")
    absent = {}
    for name, expected in hashes.items():
        require(custody._sha(expected) and PurePosixPath(name).name == name, "unsafe adapter hash entry")
        if name in WEIGHTS and not (root / name).exists():
            absent[name] = expected
        else:
            require(inputs.hash(inputs.path(root, name)) == expected, "captured adapter hash mismatch")
    meta = inputs.read(root / "train_meta.json")
    require(meta["steps"] == 96 and meta["seed"] == seed and meta["tokens"] == 3 * total
            and meta["rank"] == 8 and meta["epochs"] == 3 and meta["lr"] == 1e-4,
            "train_meta disagrees")
    for field in ("train_seconds", "wall_seconds"):
        require(finite(manifest[field]), "invalid fit cost")
    require(manifest["wall_seconds"] >= manifest["train_seconds"], "fit wall time below training time")
    return dict(steps=96, unique_events=1, explicit_replays=32, input_token_passes=3 * total,
                target_token_passes=3 * target, train_seconds=manifest["train_seconds"],
                wall_seconds=manifest["wall_seconds"], final_loss=manifest["final_loss"],
                context_sha256=token_rows[0]["rendered_context_sha256"],
                paired_recipe={key: value for key, value in config.items() if key not in ("seed", "note")},
                missing_weight_hashes=absent, recorded_adapter_path=destination,
                weight_verification="OMITTED_WEIGHTS_NOT_REHASHED" if absent else "CAPTURED_WEIGHT_BYTES_REHASHED")


def pair_custody(root, spec_path, spec, inputs):
    inputs.inventory(root)
    require(not (root / "PAIR_FAILED.json").exists(), "failed pair")
    done = inputs.read(root / "PAIR_DONE.json")
    started = inputs.read(root / "PAIR_STARTED.json")
    spec_hash = inputs.hash(spec_path)
    require(done["evidence_label"] == "EVALUATION_ONLY" and done["spec_sha256"] == spec_hash
            and started["spec_sha256"] == spec_hash and started["spec"] == spec
            and started["source_snapshot"] == done["source_snapshot"], "pair spec/source binding mismatch")
    require(set(done["workers"]) == {"off", "on"}
            and done["workers"]["off"]["pid"] != done["workers"]["on"]["pid"], "worker pair identity")
    for condition in ("off", "on"):
        worker = done["workers"][condition]
        require(worker["pid"] != started["controller_pid"] and worker["device"] == started["device"]
                and worker["multiprocessing"] == "spawn", "fresh worker/controller receipt mismatch")
        custody.verify_condition(root, condition, spec_hash, done["workers"][condition])
        receipt = root / f"{condition}_WORKER_DONE.json"
        require(inputs.hash(receipt) == done["receipt_sha256"][condition], "pair receipt hash mismatch")
        manifest = inputs.read(root / condition / "manifest.json")
        for name, expected in manifest["sha256"].items():
            require(inputs.hash(inputs.path(root / condition, name)) == expected, "probe manifest mismatch")
    return dict(status="CAPTURED_PAIR_ARTIFACTS_VALIDATED", source_snapshot=done["source_snapshot"],
                spec_sha256=spec_hash, receipt_sha256=done["receipt_sha256"],
                original_source_replay=False, remote_paths_rehashed=False)


def strict_action(marker):
    line = marker.group(0)
    if not re.match(r"^ACT:\s+", line):
        return False
    board = line.split(":", 1)[1].strip()
    rows = board.split(";")
    return len(rows) == 4 and all(re.fullmatch(r"[1-4](?:\s+[1-4]){3}", row.strip()) for row in rows)


def generation_pairs(directory, config, results, inputs):
    events = inputs.read(directory / "generations.jsonl", jsonl=True)
    require(len(events) % 2 == 0, "unfinished generation")
    pairs = []
    reserved = 0
    for index in range(0, len(events), 2):
        request, output = events[index:index + 2]
        require(request.get("kind") == "generation_request" and output.get("kind") == "generation_output"
                and request["request_index"] == output["request_index"] == index // 2
                and request["evidence_label"] == output["evidence_label"] == "EVALUATION_ONLY",
                "generation ordering/cardinality")
        require(request["source_identity"] == config["source_identity"]
                and request["temperature"] == .7 and request["max_tokens"] in (400, 100)
                and request["prompt_scope"] == "batch_user_text_before_chat_template", "generation settings")
        prompts, seeds, texts = request["prompts"], request["seeds"], output["outputs"]
        require(isinstance(prompts, list) and isinstance(seeds, list) and isinstance(texts, list)
                and 0 < len(prompts) == len(seeds) == len(texts)
                and all(isinstance(text, str) for text in prompts + texts)
                and all(type(seed) is int for seed in seeds), "generation payload/cardinality")
        reserved += len(texts) * request["max_tokens"]
        pairs.append((request, texts))
    require(results["generation_batches"] == len(pairs) and results["reserved_output_tokens"] == reserved
            and reserved <= config["total_token_budget"], "generation budget/count mismatch")
    return pairs, reserved


def condition(root, name, spec, panel, snapshot, inputs):
    directory = root / name
    config = inputs.read(directory / "configuration.json")
    results = inputs.read(directory / "results.json")
    require(config["episode_ids"] == EPISODES and [row["episode_id"] for row in results["episodes"]] == EPISODES,
            "probe episode order mismatch")
    require(all(config[key] == value for key, value in BUDGET.items() if key != "max_model_len"),
            "actual probe settings mismatch")
    identity = config["source_identity"]
    expected_adapter = spec["expected_adapter_hashes"] if name == "on" else {}
    backend_adapter = {key: value for key, value in expected_adapter.items()
                       if key in WEIGHTS | {"adapter_config.json"}}
    require(config["hashes_before"]["model"] == spec["expected_model_hashes"]
            and config["hashes_before"].get("adapter", {}) == expected_adapter
            and config["sources"]["model"] == identity["model_input"] == spec["model_path"]
            and identity["adapter_input"] == (spec["adapter_path"] if name == "on" else None)
            and identity["adapter_files"] == backend_adapter
            and identity["default_temperature"] == .7, "actual model/adapter identity mismatch")
    remote_root = remote(snapshot["source_root"])
    require(text_hash(config["birth_prompt"]) == snapshot["sha256"]["organism_v6/bootstrap_reasoning_gym.txt"],
            "bootstrap snapshot mismatch")
    code = config["code_hashes_before"]
    require(bool(code), "missing recorded probe code hashes")
    for path, digest in code.items():
        try:
            relative = remote(path).relative_to(remote_root).as_posix()
        except ValueError as error:
            raise ValueError("recorded probe code outside source snapshot") from error
        require(custody._sha(digest) and snapshot["sha256"].get(relative) == digest, "recorded code snapshot mismatch")
    pairs, reserved = generation_pairs(directory, config, results, inputs)
    cursor = 0
    episodes, output_projection, scratch_seconds = [], [], 0.0
    for index, (entry, question) in enumerate(zip(results["episodes"], panel["questions"])):
        episode = EPISODES[index]
        require(cursor < len(pairs), "missing wake generation")
        request, outputs = pairs[cursor]
        cursor += 1
        require(request["max_tokens"] == 400 and request["prompts"] == [question["initial_prompt"]]
                and request["seeds"] == [batch_loop._seed_for(episode, 1, 0)], "wake prompt/order/seed mismatch")
        output = outputs[0]
        ledger = inputs.read(directory / entry["ledger"], jsonl=True)
        require(all(row.get("episode_id") == episode
                    and (row.get("evidence_label") == "EVALUATION_ONLY" or
                         row.get("kind") == "scratchpad" and "evidence_label" not in row)
                    for row in ledger), "ledger episode/label mismatch")
        thoughts = [row for row in ledger if row.get("kind") == "thought"]
        actions = [row for row in ledger if row.get("kind") == "act"]
        scratches = [row for row in ledger if row.get("kind") == "scratchpad"]
        markers = [match for match in batch_loop._MARK.finditer(output) if match.group(1) == "ACT"]
        require(len(thoughts) == 1 and thoughts[0]["tick"] == 1
                and thoughts[0]["note"] == output.strip()[:2000]
                and thoughts[0]["prompt"] == question["initial_prompt"][:24000], "raw thought/generation mismatch")
        receipt = dict(schema="child-generation-v1", identity=dict(identity, default_max_tokens=400),
                       prompt_sha256=text_hash(question["initial_prompt"]), output_sha256=text_hash(output),
                       seed=request["seeds"][0], max_tokens=400, temperature=.7)
        require(all(row.get("generation") == receipt for row in thoughts + actions), "ledger generation receipt mismatch")
        require([row["action"] for row in actions] == [match.group(2).strip() for match in markers],
                "raw ACT markers/ledger mismatch")
        require(len({row["execution_id"] for row in actions}) == len(actions), "duplicate action execution")
        summary = entry["summary"]
        require(summary["episode_id"] == episode and summary["ticks"] == 1
                and summary["n_acts"] == entry["n_actions"] == len(actions), "summary ACT count mismatch")
        facts = []
        for row in actions:
            try:
                fact = facts_from_act(row)
                facts.append(dict(status="measured" if fact.measured else "unmeasured", score=fact.score if fact.measured else 0))
            except InvalidFeedback as error:
                facts.append(dict(status="invalid", score=0, reason=str(error)))
        measured = sum(fact["status"] == "measured" for fact in facts)
        require(entry["n_measured_actions"] == measured and entry["n_scratchpads"] == len(actions) == len(scratches),
                "measured action/scratchpad count mismatch")
        require(all(finite(row["score"]) and row["score"] <= 1 for row in actions), "invalid raw native score")
        require(summary["best_score"] == max([0.0] + [row["score"] for row in actions]), "native best summary mismatch")
        scratch_outputs = []
        if actions:
            require(cursor < len(pairs), "missing post-outcome generation")
            scratch_request, scratch_outputs = pairs[cursor]
            cursor += 1
            expected_seeds = [(zlib.crc32(row["execution_id"].encode()) ^ BUDGET["seed_salt"]) & 0x7fffffff
                              for row in actions]
            require(scratch_request["max_tokens"] == 100 and len(scratch_outputs) == len(actions)
                    and scratch_request["seeds"] == expected_seeds, "post-outcome generation binding")
            for action, scratch, prompt, text in zip(actions, scratches, scratch_request["prompts"], scratch_outputs):
                require(scratch["execution_id"] == action["execution_id"] and scratch["action"] == action["action"]
                        and scratch["outcome"] == action["outcome"] and scratch["text"] == text
                        and scratch["n_chars"] == len(text) and scratch["score"] == action["score"]
                        and all(scratch[field] == action[field] for field in ("tick", "occurrence_id", "occurrence_index"))
                        and prompt == question["initial_prompt"].rstrip("\n") + "\n\n"
                        + outcome_block(facts_from_act(action), "Scratchpad"), "scratchpad raw-output/source mismatch")
                generation = scratch["generation"]
                require(generation["prompt"] == prompt and generation["prompt_sha256"] == text_hash(prompt)
                        and generation["output_sha256"] == text_hash(text) and generation["max_tokens"] == 100
                        and generation["backend_identity"] == dict(identity, default_max_tokens=400)
                        and generation["temperature"] == .7 and generation["base_seed"] == 0
                        and generation["seed_salt"] == BUDGET["seed_salt"]
                        and generation["seed"] == (zlib.crc32(action["execution_id"].encode()) ^ BUDGET["seed_salt"]) & 0x7fffffff,
                        "scratchpad generation receipt mismatch")
                require(finite(scratch["gen_seconds"]), "invalid scratchpad time")
                scratch_seconds += scratch["gen_seconds"]
        first = facts[0] if facts else dict(status="missing", score=0)
        strict = bool(markers) and strict_action(markers[0])
        episodes.append(dict(episode_id=episode, first_act=first, first_action=actions[0]["action"] if actions else None,
            first_act_accepted=int(first["status"] == "measured" and first["score"] == 1),
            first_act_score=first["score"], native_best=summary["best_score"], n_acts=len(actions),
            first_act_strict_format=strict, exactly_one_strict_act=len(markers) == 1 and strict,
            malformed_act_markers=sum(not strict_action(marker) for marker in markers),
            multiple_acts=len(markers) > 1, learned_board_compatible=question["learned_board_compatible"]))
        output_projection.append(dict(episode_id=episode, wake=output, scratchpads=scratch_outputs))
    require(cursor == len(pairs), "unassigned/extra generation requests")
    require(results["n_actions"] == sum(row["n_acts"] for row in episodes)
            and results["n_scratchpads"] == sum(entry["n_scratchpads"] for entry in results["episodes"])
            and results["n_measured_actions"] == sum(entry["n_measured_actions"] for entry in results["episodes"]),
            "top-level result count mismatch")
    totals = dict(denominator=32, first_act_accepted=sum(row["first_act_accepted"] for row in episodes),
                  first_act_score_mean=sum(row["first_act_score"] for row in episodes) / 32,
                  native_best_mean=sum(row["native_best"] for row in episodes) / 32,
                  strict_first_act_count=sum(row["first_act_strict_format"] for row in episodes),
                  exactly_one_strict_act_count=sum(row["exactly_one_strict_act"] for row in episodes),
                  multiple_act_episodes=sum(row["multiple_acts"] for row in episodes),
                  malformed_act_markers=sum(row["malformed_act_markers"] for row in episodes),
                  missing_act_episodes=sum(row["n_acts"] == 0 for row in episodes))
    totals["first_act_accepted_rate"] = totals["first_act_accepted"] / 32
    compatibility = {}
    for compatible in (False, True):
        rows = [row for row in episodes if row["learned_board_compatible"] is compatible]
        compatibility["compatible" if compatible else "incompatible"] = dict(
            denominator=len(rows), first_act_accepted=sum(row["first_act_accepted"] for row in rows))
    shared = custody._shared(config)
    for field in ("probe_root", "protected_roots"):
        shared.pop(field)
    return dict(episodes=episodes, summary=totals, source_board_compatibility=compatibility,
                first_act_status_counts=dict(Counter(row["first_act"]["status"] for row in episodes)),
                costs=dict(reserved_output_tokens=reserved, generation_batches=len(pairs),
                           generated_characters=sum(len(text) for _, texts in pairs for text in texts),
                           measured_output_tokens=None, truncations=None, scratchpad_gen_seconds=scratch_seconds),
                outputs=output_projection), shared


def difference(left, right):
    return {key: left["summary"][key] - right["summary"][key] for key in
            ("first_act_accepted", "first_act_accepted_rate", "first_act_score_mean", "native_best_mean",
             "strict_first_act_count", "exactly_one_strict_act_count", "multiple_act_episodes", "missing_act_episodes")}


def reduce_capture(capture_path, expected_sha256):
    inputs = Inputs()
    capture_path = Path(capture_path).absolute()
    require(custody._sha(expected_sha256) and inputs.hash(capture_path) == expected_sha256, "capture index hash mismatch")
    index = inputs.read(capture_path)
    require(index["schema"] == "correction-utility-capture-v1" and type(index["synthetic"]) is bool, "capture schema")
    root = capture_path.parent
    material = inputs.path(root, index["material"])
    panel_path = inputs.path(root, index["panel"])
    prepared, panel = material_inputs(material, panel_path, inputs)
    recipients = index["recipients"]
    require(len(recipients) == 6 and all(type(row["seed"]) is int for row in recipients)
            and {(row["arm"], row["seed"]) for row in recipients} == {(arm, seed) for arm in ARMS for seed in SEEDS},
            "exactly six distinct terminal recipient cells required")
    require(len({row["logs"] for row in recipients}) == len({row["adapter"] for row in recipients}) == 6,
            "reused recipient capture directory")
    local_directories = [inputs.path(root, row[field]).resolve() for row in recipients for field in ("logs", "adapter")]
    require(len(set(local_directories)) == 12, "reused canonical recipient directory")
    cells, shared_reference, snapshot_reference = {}, None, None
    runner_hashes = set()
    for row in sorted(recipients, key=lambda row: (row["seed"], row["arm"])):
        arm, seed = row["arm"], row["seed"]
        logs = inputs.path(root, row["logs"])
        inputs.inventory(logs)
        require(not (logs / "FAILED.json").exists(), "failed recipient")
        started = inputs.read(logs / "STARTED.json")
        completed = inputs.read(logs / "COMPLETED.json")
        require(started["arm"] == completed["arm"] == arm and started["seed"] == completed["seed"] == seed
                and completed["status"] == "COMPLETED_NOT_A_LEARNING_CLAIM"
                and completed["clean_lineage"] is False and completed["parenting_advantage"] is False
                and completed["unique_events"] == started["unique_events"] == 1
                and started["explicit_replays"] == 32 and started["token_matched"] is False,
                "recipient completion/arm/seed mismatch")
        require(started["material_sha256"] == inputs.hash(material / "artifact_hashes.json")
                and started["panel_sha256"] == inputs.hash(panel_path) and custody._sha(started["script_sha256"]),
                "recipient preparation binding mismatch")
        runner_hashes.add(started["script_sha256"])
        for name in ("fit.log", "pair.log"):
            inputs.hash(logs / name)
        spec_path = logs / "probe_spec.json"
        spec = inputs.read(spec_path)
        require(all(spec[key] == value for key, value in BUDGET.items())
                and spec["episode_ids"] == EPISODES and spec["order"] == ["off", "on"]
                and spec["model_path"] == prepared["model_path"]
                and spec["expected_model_hashes"] == prepared["expected_model_files"]
                and spec["families_sha256"] == panel["families_sha256"]
                and spec["panel_role"] == "development_validation"
                and spec["selection_used_episode_ids"] == ["rg/mini_sudoku/1850124"], "probe spec mismatch")
        fit = fit_inputs(inputs.path(root, row["adapter"]), material, prepared, arm, seed, spec, completed, inputs)
        pair_root = logs / "probes/pair"
        receipts = pair_custody(pair_root, spec_path, spec, inputs)
        snapshot = receipts["source_snapshot"]
        if snapshot_reference is None:
            snapshot_reference = snapshot
        require(snapshot == snapshot_reference, "recipient source snapshots differ")
        cell = dict(arm=arm, seed=seed, fit=fit, custody=receipts)
        for name in ("off", "on"):
            cell[name], shared = condition(pair_root, name, spec, panel, snapshot, inputs)
            if shared_reference is None:
                shared_reference = shared
            require(shared == shared_reference, "paired model/panel/settings/code mismatch")
        begin, end = datetime.fromisoformat(started["started_utc"]), datetime.fromisoformat(completed["finished_utc"])
        require(begin.tzinfo is not None and end.tzinfo is not None and end >= begin, "invalid condition timestamps")
        cell["condition_wall_seconds"] = (end - begin).total_seconds()
        cell["on_minus_off"] = difference(cell["on"], cell["off"])
        cells[f"{arm}/seed{seed}"] = cell
    require(len({cell["fit"]["context_sha256"] for cell in cells.values()}) == 1,
            "recipient teaching contexts differ")
    require(len({custody._json(cell["fit"]["paired_recipe"]) for cell in cells.values()}) == 1
            and len(runner_hashes) == 1, "recipient training settings/runner hashes differ")
    baseline = cells["whole_raw/seed0"]["off"]
    comparisons = {key: dict(outputs_equal=cell["off"]["outputs"] == baseline["outputs"],
                            outcomes_equal=cell["off"]["episodes"] == baseline["episodes"])
                   for key, cell in cells.items()}
    identical = all(all(value.values()) for value in comparisons.values())
    contrasts = []
    for seed in SEEDS:
        whole, action = cells[f"whole_raw/seed{seed}"], cells[f"act_only/seed{seed}"]
        contrasts.append(dict(seed=seed, whole_raw_gain=whole["on_minus_off"], act_only_gain=action["on_minus_off"],
            whole_raw_minus_act_only_on=difference(whole["on"], action["on"]),
            whole_raw_minus_act_only_gain={key: whole["on_minus_off"][key] - action["on_minus_off"][key]
                                          for key in whole["on_minus_off"]}))
    inputs.verify()
    return dict(schema="correction-utility-analysis-v1", status="SIX_TERMINAL_CELLS_VALIDATED",
                evidence_label="SYNTHETIC_FIXTURE_NOT_EVIDENCE" if index["synthetic"] else "SELECTED_MATERIAL_UTILITY_DEV_ONLY",
                synthetic=index["synthetic"], recipient_seeds=list(SEEDS), unique_source_events=1,
                protocol="research_notes/astra_memos/ASTRA_CORRECTION_UTILITY_COMPARISON_2026-09-12.md",
                recorded_runner_sha256=next(iter(runner_hashes)),
                token_matched=False, cells=cells, per_seed=contrasts, paired_settings=shared_reference,
                off_baseline=dict(identical_outputs_and_outcomes=identical, comparisons=comparisons,
                    independent_learner_replications=0, reference_cell="whole_raw/seed0",
                    interpretation="ONE_SHARED_DETERMINISTIC_BASELINE" if identical else
                    "OFF_MISMATCH_DO_NOT_COLLAPSE; per-cell gains retained, investigate before interpretation"),
                input_sha256=inputs.hashes, reducer_sha256=custody._digest(__file__), limitations=LIMITATIONS)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", required=True)
    parser.add_argument("--capture-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        report = reduce_capture(args.capture, args.capture_sha256)
    except (ValueError, KeyError, TypeError, OSError, IndexError) as error:
        print(f"CORRECTION_UTILITY_INVALID: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Seed-zero raw-child-wake exploratory fork; no clean lineage or H1 claim."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys


SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE))
from gpu.astra_mini_sudoku_diagnostic import check_free, digest, write_new
from organism_v6 import run_reasoning_neutral as supervisor
from organism_v6.neutral_pair_custody import validate_pair
from organism_v6.parent_note_replay_diagnostic import _inventory
from organism_v6.reasoning_neutral_probe import file_hashes


ARMS = ("lesson", "sham")
CANARIES = [f"rg/mini_sudoku/{seed}" for seed in range(1900050, 1900066)]
TRAIN_CONFIG = dict(rank=8, alpha=16, dropout=0.05, lr=1e-4, epochs=3,
                    seed=0, batch_size=1, grad_accum=1, chat_template=False,
                    pack=False, max_len=4096, add_eos=True, optimizer="adamw",
                    grad_checkpoint=True)
BOUNDARY = dict(label="EXPLORATORY_P0_RAW_WAKE_FORK", clean_lineage=False,
                H1_claim=False, G5_claim=False, model_origin="UNRESOLVED_LOCAL_HASHES_ONLY",
                target_token_equivalence=False, teacher_dose_equivalence=False,
                endpoint="first ACT solved count; missing/invalid first ACT is zero; retain all actions",
                evaluation_scope="16 existing mini_sudoku canaries only; other source families untested",
                panel_role="reused development panel, not untouched confirmation")


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def overlap(left, right):
    return left == right or left in right.parents or right in left.parents


def native_gym():
    if importlib.util.find_spec("reasoning_gym") is None:
        return None
    from organism_v6.reasoning_gym_gym import ReasoningGymGym
    return ReasoningGymGym(require_package=True, strict_verifier=True)


def question_audit(source_rows):
    questions = {}
    for rows in source_rows.values():
        for row in rows:
            episode = row["item"]["meta"]["episode_id"]
            if not episode.startswith("rg/mini_sudoku/"):
                continue
            prompt = row["source"]["original_prompt"]
            require(prompt.count("=== STATE ===\nGOAL: ") == 1, "ambiguous native task head")
            goal = prompt.split("=== STATE ===\nGOAL: ", 1)[1]
            head, separator, _ = goal.partition("\nWrite each attempt on one ACT: line;")
            require(separator and "\n" in head, "missing native question bytes")
            question = head.split("\n", 1)[1]
            require(episode not in questions or questions[episode] == question, "paired source question mismatch")
            questions[episode] = question
    result = dict(selected_mini_episodes=list(questions),
                  source_question_sha256={episode: hashlib.sha256(text.encode()).hexdigest()
                                          for episode, text in questions.items()},
                  solution_overlaps=None, all64_source_membership="episode-disjoint only")
    gym = native_gym()
    if gym is None:
        return dict(result, status="EPISODE_DISJOINT_ONLY", reason="native reasoning_gym unavailable; no unseen-puzzle claim")
    entries = {episode: gym._item("mini_sudoku", int(episode.rsplit("/", 1)[1]))[1]
               for episode in [*questions, *CANARIES]}
    require(all(entries[episode]["question"].strip() == text for episode, text in questions.items()),
            "native generator differs from actual source question")
    require(not any(question == entries[canary]["question"].strip()
                    for question in questions.values() for canary in CANARIES), "exact source/canary puzzle overlap")
    result["solution_overlaps"] = [dict(source=episode, canary=canary) for episode in questions for canary in CANARIES
                                   if entries[episode].get("answer") is not None
                                   and entries[episode]["answer"] == entries[canary].get("answer")]
    return dict(result, status="SELECTED_MINI_QUESTION_DISJOINT", solution_overlap_policy="reported, never excluded",
                canary_question_sha256={episode: hashlib.sha256(entries[episode]["question"].strip().encode()).hexdigest()
                                        for episode in CANARIES})


def inspect_material(material):
    inventory = _inventory(material)
    required = {"results.json", "selection.json", "original_sources.json", "source_hashes.json"}
    required.update(f"{arm}{suffix}.json" for arm in ARMS for suffix in ("", "_source_map"))
    require(set(inventory["files"]) == required, "unexpected export artifacts")
    result, selection = read(material / "results.json"), read(material / "selection.json")
    require(result["status"] == "READY" and result["selection"] == selection
            and result["boundary"]["tokenizer_validation"] == "actual local tokenizer",
            "native tokenizer READY export required")
    selected = selection["selected_episodes"]
    require(selection["count"] == len(selected) == len(set(selected)) == 32
            and selection["selection"] == "measured" and selection["max_len"] == 4096,
            "fixed 32 measured examples at maxlen4096 required")
    sources = read(material / "original_sources.json")
    pins = sources["lesson"]["local_pins"]
    require(pins == sources["sham"]["local_pins"], "paired local model pins differ")
    schedules, tokens, source_rows = [], {}, {}
    for arm in ARMS:
        source = sources[arm]
        root = Path(source["root"]).resolve(strict=True)
        schedule_path = root / "schedule.json"
        require(digest(schedule_path) == source["inventory"]["files"]["schedule.json"],
                "source schedule hash mismatch")
        schedule = read(schedule_path)
        require(len(schedule) == len(set(schedule)) == 64 and set(selected) <= set(schedule)
                and not set(schedule) & set(CANARIES), "source/canary episode overlap or membership mismatch")
        schedules.append(schedule)
        corpus = read(material / f"{arm}.json")
        rows = read(material / f"{arm}_source_map.json")["rows"]
        source_rows[arm] = rows
        require(corpus["recipe"] == "source_linked_raw_wake_v3_spans_v1"
                and corpus["boundary"] == result["boundary"] and len(rows) == 32
                and corpus["corpus"] == [row["item"] for row in rows], "export corpus/source-map mismatch")
        require([item["meta"]["episode_id"] for item in corpus["corpus"]] == selected,
                "selected episode order mismatch")
        for row in rows:
            spans = row["item"]["spans"]
            require(spans == [[row["rendered_context"], False, "parent_removed_context"],
                              [row["source"]["raw_output"], True, "raw_child_wake"]],
                    "training spans differ from exported child bytes/mask")
            require(type(row["input_tokens"]) is int and type(row["target_tokens"]) is int
                    and 0 < row["target_tokens"] < row["input_tokens"] <= 4096,
                    "invalid bound token counts")
        tokens[arm] = {name: sum(row[name] for row in rows) for name in ("input_tokens", "target_tokens")}
        require(result["arms"][arm]["selected_examples"] == 32
                and all(result["arms"][arm][name] == value for name, value in tokens[arm].items()),
                "export token totals mismatch")
    require(schedules[0] == schedules[1], "source schedules differ")
    for name, expected in read(material / "source_hashes.json").items():
        require(Path(name).is_absolute() and digest(Path(name)) == expected, "export source hash mismatch")
    require(file_hashes(pins["model_path"]) == pins["files"], "local model pins changed")
    return dict(inventory=inventory, pins=pins, selected=selected, source_episodes=schedules[0],
                source_roots=[sources[arm]["root"] for arm in ARMS], tokens=tokens,
                question_audit=question_audit(source_rows),
                teacher_tokens={arm: result["arms"][arm]["teacher_tokens"] for arm in ARMS})


def trainer_command(root, material, model, arm):
    return [sys.executable, "-B", "-m", "organism_v6.train_adapter_v3",
            "--corpus", str(material / f"{arm}.json"), "--out", str(root / "training" / f"{arm}_seed0"),
            "--model", model, "--rank", "8", "--alpha", "16", "--dropout", "0.05",
            "--lr", "1e-4", "--epochs", "3", "--seed", "0", "--batch-size", "1",
            "--grad-accum", "1", "--no-pack", "--max-len", "4096"]


def prepare(material_root, run_root):
    material, root = Path(material_root).resolve(strict=True), Path(run_root).absolute()
    require(not root.exists() and not root.is_symlink() and root == root.resolve(), "fresh canonical run root required")
    require(not overlap(root, material) and not overlap(root, SOURCE), "run root overlaps inputs/source")
    bound = inspect_material(material)
    require(not any(overlap(root, Path(path).resolve()) for path in
                    [bound["pins"]["model_path"], *bound["source_roots"]]), "run root overlaps protected input")
    families = SOURCE / "organism_v6/reasoning_gym_families.json"
    plan = dict(boundary=BOUNDARY, root=str(root), material=str(material), bound=bound,
                source=str(SOURCE), script_sha256=digest(Path(__file__)),
                families_sha256=digest(families), canaries=CANARIES, training_seed=0,
                expected_steps=96, fit_timeout_seconds=900, pair_timeout_seconds=2100,
                commands={arm: trainer_command(root, material, bound["pins"]["model_path"], arm) for arm in ARMS})
    root.mkdir(parents=True, exist_ok=False)
    for path in (root / "logs", root / "training", root / "probes"):
        path.mkdir()
    for arm in ARMS:
        (root / "logs" / arm).mkdir()
    write_new(root / "plan.json", plan)
    write_new(root / "PREPARED.json", dict(plan_sha256=digest(root / "plan.json")))
    return plan


def verify_plan(root):
    require(digest(root / "plan.json") == read(root / "PREPARED.json")["plan_sha256"], "plan changed")
    plan = read(root / "plan.json")
    require(plan["root"] == str(root) and plan["source"] == str(SOURCE)
            and plan["script_sha256"] == digest(Path(__file__))
            and plan["families_sha256"] == digest(SOURCE / "organism_v6/reasoning_gym_families.json"),
            "prepared execution source changed")
    material = Path(plan["material"])
    require(inspect_material(material) == plan["bound"], "material binding changed")
    require(plan["commands"] == {arm: trainer_command(root, material, plan["bound"]["pins"]["model_path"], arm)
                                 for arm in ARMS}, "trainer command/interpreter changed")
    return plan


def verify_fit(root, plan, arm):
    adapter = root / "training" / f"{arm}_seed0"
    manifest = read(adapter / "train_manifest.json")
    require(all(manifest["config"][name] == value for name, value in TRAIN_CONFIG.items()), "trainer config mismatch")
    require(manifest["base_model"] == plan["bound"]["pins"]["model_path"]
            and (adapter / "DONE").is_file() and manifest["steps"] == 96
            and manifest["nonfinite_batches"] == 0 and math.isfinite(manifest["final_loss"]), "incomplete/nonfinite fit")
    require(manifest["corpus"]["sha256"] == plan["bound"]["inventory"]["files"][f"{arm}.json"]
            and manifest["corpus"]["n_items"] == manifest["corpus"]["n_encoded"] == 32
            and manifest["corpus"]["n_skipped_no_target"] == 0, "trainer corpus mismatch")
    require(all(manifest["truncation"][name] == 0 for name in
                ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "trainer material loss")
    tokens = plan["bound"]["tokens"][arm]
    require(manifest["tokens"]["target"] == tokens["target_tokens"]
            and manifest["tokens"]["total"] == tokens["input_tokens"]
            and manifest["tokens"]["context"] == tokens["input_tokens"] - tokens["target_tokens"]
            and manifest["train_tokens_seen"] == 3 * tokens["input_tokens"], "trainer token mismatch")
    hashes = file_hashes(adapter)
    require("adapter_config.json" in hashes and any(name.endswith(".safetensors") for name in hashes), "missing adapter weights")
    config = read(adapter / "adapter_config.json")
    require(config["r"] == 8 and config["lora_alpha"] == 16 and config["lora_dropout"] == 0.05,
            "actual adapter configuration mismatch")
    return hashes


def probe_spec(root, plan, arm, adapter_hashes):
    pins = plan["bound"]["pins"]
    return dict(model_path=pins["model_path"], adapter_path=str(root / "training" / f"{arm}_seed0"),
                expected_model_hashes=pins["files"], expected_adapter_hashes=adapter_hashes,
                families_path=str(SOURCE / "organism_v6/reasoning_gym_families.json"),
                families_sha256=plan["families_sha256"], probe_root=str(root / "probes"),
                output_dir=str(root / "probes" / arm),
                training_life_roots=[str(root / "training"), plan["material"], *plan["bound"]["source_roots"]],
                lineage_roots=[str(root / "training")], episode_ids=CANARIES,
                gen_seed=0, seed_salt=15420, budget_ticks=1, wake_max_tokens=400,
                scratchpad_max_tokens=100, total_token_budget=38400, max_episodes=16,
                max_model_len=4096, worker_timeout_seconds=900, order=["off", "on"],
                panel_role="development_validation", selection_used_episode_ids=plan["bound"]["source_episodes"])


def verify_probe(root, arm, spec_hash, expected=None):
    output = root / "probes" / arm
    require(not (output / "PAIR_FAILED.json").exists(), "neutral pair failed")
    done = read(output / "PAIR_DONE.json")
    require(done["spec_sha256"] == spec_hash and (expected is None or done == expected), "pair seal changed")
    require(validate_pair(output, spec_hash, done["workers"], done["source_snapshot"]) == done["receipt_sha256"],
            "neutral pair receipt mismatch")
    return done


def execute(root, device):
    require(supervisor.selected_device() == device, "controller must retain the reserved GPU selector")
    plan = verify_plan(root)
    write_new(root / "STARTED.json", dict(device=device, pid=os.getpid(), arms=list(ARMS), started_utc=utc_now()))
    completed = {}
    try:
        for arm in ARMS:
            verify_plan(root)
            require(not (root / "training" / f"{arm}_seed0").exists(), "adapter destination exists")
            logs = root / "logs" / arm
            supervisor.run_worker(plan["commands"][arm], log_path=logs / "train.log", timeout=900, device=device)
            hashes = verify_fit(root, plan, arm)
            spec = probe_spec(root, plan, arm, hashes)
            spec_path = logs / "probe_spec.json"
            write_new(spec_path, spec)
            spec_hash = digest(spec_path)
            supervisor.read_spec(spec_path, spec_hash)
            supervisor.run_worker([sys.executable, "-B", "-m", "organism_v6.run_reasoning_neutral",
                                   "--spec", str(spec_path), "--spec-sha256", spec_hash, "--allow-gpu"],
                                  log_path=logs / "pair.log", timeout=2100, device=device)
            done = verify_probe(root, arm, spec_hash)
            completed[arm] = dict(adapter_hashes=hashes, spec_sha256=spec_hash, pair_done=done, completed_utc=utc_now())
            write_new(logs / "result.json", completed[arm])
        verify_plan(root)
        for arm, evidence in completed.items():
            require(verify_fit(root, plan, arm) == evidence["adapter_hashes"], "prior arm adapter changed")
            require(digest(root / "logs" / arm / "probe_spec.json") == evidence["spec_sha256"], "prior probe spec changed")
            verify_probe(root, arm, evidence["spec_sha256"], evidence["pair_done"])
        write_new(root / "COMPLETED.json", dict(boundary=BOUNDARY, arms=completed, completed_utc=utc_now(),
                  tokens=plan["bound"]["tokens"], teacher_tokens=plan["bound"]["teacher_tokens"],
                  interpretation="Raw four-condition evidence only; no computed scientific success gate"))
    except BaseException as error:
        write_new(root / "FAILED.json", dict(error=repr(error), completed_arms=list(completed), failed_utc=utc_now(),
                  gpu_processes_absent=supervisor.gpu_processes_absent(device),
                  reservation="caller-owned; inspect worker cleanup receipts before releasing"))
        raise


def launch(root, device):
    plan = verify_plan(root)
    require(not any((root / name).exists() for name in ("LAUNCHED.json", "STARTED.json", "FAILED.json", "COMPLETED.json")),
            "run already attempted")
    metadata, xml = check_free(device)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=device, V6_MODEL=plan["bound"]["pins"]["model_path"],
                       PYTHONPATH=str(SOURCE), PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
                       HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", VLLM_WORKER_MULTIPROC_METHOD="spawn")
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "--root", str(root), "--device", device, "--execute"]
    with (root / "logs" / "gpu_before.xml").open("x") as target:
        target.write(xml)
    with (root / "logs" / "controller.log").open("xb") as output:
        process = subprocess.Popen(command, cwd=SOURCE, env=environment, stdin=subprocess.DEVNULL,
                                   stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(status="LAUNCHED_NOT_COMPLETED", pid=process.pid, device=device, command=command,
                   launched_utc=utc_now(), source=str(SOURCE), script_sha256=digest(Path(__file__)),
                   continuous_caller_reservation=True, sequential_arms=list(ARMS), gpu=metadata)
    write_new(root / "LAUNCHED.json", receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--material")
    parser.add_argument("--device")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--launch", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    if args.launch or args.execute:
        require(args.device is not None and args.material is None, "execution needs device and a prepared root")
        root = Path(args.root).resolve(strict=True)
        result = launch(root, args.device) if args.launch else execute(root, args.device)
    else:
        require(args.material is not None, "preparation needs --material")
        result = prepare(args.material, args.root)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

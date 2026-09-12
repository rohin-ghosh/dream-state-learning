"""Fixed root0 AUTH/DERANGED fresh-fit pair. Main alone allocates and launches."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import sys
import time


ARMS = ("AUTH", "DERANGED")
SECONDS = 1200
CLAIM = "ORACLE_AUTHORED_DIAGNOSTIC_NOT_CHILD_EXPERIENCE_NOT_CLEAN_LINEAGE"
PINS = {
    "manifest.json": "d70aea1ae832cd9a60c28cd41f4f2ff2a4071716d1859f50a28405891ce6c4b6",
    "candidate.json": "5d1644b90ff7621ee121aba65be7dd7cae7f15168f5a3c3a09a1bc9aa9a7af8c",
    "AUTH.json": "344ec17779696b184468d96ce26ef89e8d3bd0cb5b8dbfde84a4b8dc1c437d48",
    "DERANGED.json": "060255b11551b55b20d39f91301cc4e0362134af321bc740134b86e3ca6d511d",
    "native_audit.json": "9c1f9f22a17caf17b36d62b08c35371eb809e6a3feb03b7e60710546257d0760",
    "recipe.json": "99deef7593dfc7e8d8ffe14af082876bcff5f27d3ce1ba0580050bb5e54dbf0e",
    "teacher_forcing_interface.json": "eaf287d50ffb623e6efb0fd4744c5749375061317dc0dcf1a63f64ece6407211",
}
COUNTS = dict(rows=128, steps=128, epochs=4, input_per_epoch=11248, target_per_epoch=1888,
              input_presentations=44992, target_presentations=7552)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def write(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def bind(source):
    global base, trainer
    source = Path(source).resolve(strict=True)
    sys.path.insert(0, str(source))
    from organism_v6 import rulegame_parenting_diagnostic as base
    from organism_v6 import train_adapter_v3 as trainer
    require(all(Path(module.__file__).resolve().parent.parent == source for module in (base, trainer)), "wrong imported source root")
    require(base.REPO.resolve() == source, "wrong native working source")


def sources():
    return dict(base.sources(), **{name: digest(base.REPO / "organism_v6" / name) for name in
        ("train_adapter_v3.py", "conditional_behavior_corpus.py", "reasoning_neutral_probe.py")},
        conditional_fit_sidecar=digest(__file__))


def fresh(path, protected=()):
    path = Path(path).expanduser().absolute()
    require(not path.exists() and not path.is_symlink() and path == path.resolve(), "fresh canonical output required; no retry/resume")
    for other in protected:
        other = Path(other).resolve()
        require(path != other and other not in path.parents and path not in other.parents, "output overlaps protected input")
    return path


def bounds(started, deadline, lease_end):
    require(all(math.isfinite(value) for value in (started, deadline, lease_end)), "nonfinite bounds")
    require(base.WORKER_SECONDS == 600 and base.CLEANUP_RESERVE == 140, "native supervisor bounds changed")
    effective = min(started + SECONDS, deadline, lease_end - 10)
    require(effective == started + SECONDS and effective - time.time() > 150, "full1200s pair/cleanup window required")
    return effective


def inspect_material(root):
    require(base.tree_hashes(root) == PINS, "material changed/not pinned native attempt2")
    manifest, audit, candidate, recipe = (read(root / name) for name in
        ("manifest.json", "native_audit.json", "candidate.json", "recipe.json"))
    require(manifest["root"] == str(root) and manifest["source"] == str(base.REPO) and
            manifest["status"] == "NATIVE_PREPARED_NO_FIT_NO_LAUNCH", "material root/source/status mismatch")
    require(manifest["files"] == {name: value for name, value in PINS.items() if name != "manifest.json"}, "material inventory mismatch")
    require(candidate["root"] == 0 and candidate["spellings"] == {"actions": ["dax", "wug"], "outcomes": ["fep", "nup"]}, "wrong root/labels")
    require(manifest["origin"] == "UNRESOLVED_LOCAL_HASHES_ONLY" and audit["origin_authenticated"] is False and
            audit["status"] == "NATIVE_TOKEN_MATCH_VERIFIED" and audit["no_truncation"] is True and
            audit["loss_bearing_padding"] is False, "native audit/origin mismatch")
    require(audit["source_sha256"] == manifest["source_sha256"] and all(
        digest(base.REPO / "organism_v6" / name) == value for name, value in audit["source_sha256"].items()), "native source pins changed")
    for key, expected in (("input_tokens_per_epoch", 11248), ("target_tokens_per_epoch", 1888)):
        require(manifest[key] == audit[key] == {arm: expected for arm in ARMS}, "native token totals mismatch")
    for arm in ARMS:
        rows = read(root / (arm + ".json"))["corpus"]
        require(rows == audit["corpora"][arm] and len(rows) == len(audit["rows"][arm]) == 128, "native corpus/row mismatch")
        require(sum(row["input_tokens"] for row in audit["rows"][arm]) == 11248 and
                sum(row["target_tokens"] for row in audit["rows"][arm]) == 1888, "native row token sum mismatch")
    schedule = audit["optimizer_update_rows"]["0"]
    require(len(schedule) == 128 and all(len(batch) == 4 for batch in schedule) and
            Counter(index for batch in schedule for index in batch) == Counter({index: 4 for index in range(128)}), "native128-update schedule mismatch")
    model = Path(audit["tokenizer_path"]).resolve(strict=True)
    require(str(model) == audit["tokenizer_path"] and read(model / "config.json")["model_type"] == "qwen2", "native model path/config mismatch")
    tokenizer_names = {"config.json", "tokenizer.json", "tokenizer_config.json"} | {
        name for name in ("vocab.json", "merges.txt", "special_tokens_map.json", "added_tokens.json", "chat_template.jinja", "chat_template.json")
        if (model / name).exists()}
    require(set(audit["tokenizer_file_hashes"]) == tokenizer_names and not (model / "chat_templates").exists(), "unbound tokenizer/template files")
    require(all(Path(name).name == name and digest(model / name) == value for name, value in
                audit["tokenizer_file_hashes"].items()), "tokenizer pins changed")
    config = asdict(trainer.TrainConfig(model=str(model), lr=1e-4, epochs=4, batch_size=4, grad_accum=1,
        rank=8, alpha=16, dropout=.05, seed=0, pack=False, max_len=512, overflow="truncate"))
    require(all(config[key] == value for key, value in recipe.items()) and config["dtype"] == "bf16" and
            config["device"] == "cuda", "native recipe differs from fixed fresh V3 recipe")
    return dict(model=str(model), model_files=base.model_hashes(model), config=config,
                tokenizer_files=audit["tokenizer_file_hashes"], material_files=dict(PINS))


def fit_command(plan, root, arm):
    require(arm in ARMS, "unknown arm")
    return [sys.executable, "-B", "-m", "organism_v6.train_adapter_v3", "--corpus",
        str(Path(plan["materialroot"]) / (arm + ".json")), "--out", str(root / "run" / arm / "adapter"),
        "--model", plan["model"], "--rank", "8", "--alpha", "16", "--dropout", "0.05", "--lr", "1e-4",
        "--epochs", "4", "--batch-size", "4", "--grad-accum", "1", "--seed", "0", "--no-pack",
        "--max-len", "512", "--overflow", "truncate"]


def prepare(root, materialroot, device, deadline, lease_end):
    require(isinstance(device, str) and re.fullmatch(r"(?:0|[1-9][0-9]*|GPU-[0-9a-fA-F-]{36})", device), "one Main-selected device required")
    started = time.time()
    bounds(started, deadline, lease_end)
    materialroot = Path(materialroot).resolve(strict=True)
    root = fresh(root, (materialroot, base.REPO))
    bound = inspect_material(materialroot)
    fresh(root, (bound["model"],))
    plan = dict(schema=1, root=str(root), materialroot=str(materialroot), source_root=str(base.REPO),
        source_hashes=sources(), source_label="5f6e1f1d217dcdb15176dc84b9ac34ec960c48de; native source hashes authoritative",
        **bound, device=device, seed=0, arms=list(ARMS), counts=COUNTS, controller_seconds=1200,
        cleanup_seconds=140, deadline=float(deadline), real_lease_end=float(lease_end),
        initialization="FRESH_FROM_FROZEN_BASE_SEPARATE_PROCESS_PER_ARM_NO_PARENT_NO_RESUME",
        claim=CLAIM, origin="UNRESOLVED_LOCAL_HASHES_ONLY", generation_calls=0,
        counts_used_for_selection=False, preparation=dict(started=started, ended=time.time(), scope="CPU only; outside later reservation"))
    plan["commands"] = {arm: fit_command(plan, root, arm) for arm in ARMS}
    root.mkdir(parents=True)
    write(root / "plan.json", plan)
    write(root / "plan.sha256.json", {"sha256": digest(root / "plan.json")})
    return dict(status="PREPARED_NOT_LAUNCHED", root=str(root), plan_sha256=digest(root / "plan.json"))


def read_plan(root):
    require(digest(root / "plan.json") == read(root / "plan.sha256.json")["sha256"], "sealed plan changed")
    return read(root / "plan.json")


def verify(root):
    plan = read_plan(root)
    require(plan["schema"] == 1 and plan["root"] == str(root) and plan["source_root"] == str(base.REPO) and
            plan["source_hashes"] == sources(), "root/source changed")
    require(plan["arms"] == list(ARMS) and plan["seed"] == 0 and plan["counts"] == COUNTS and
            plan["controller_seconds"] == 1200 and plan["cleanup_seconds"] == 140 and plan["claim"] == CLAIM and
            plan["origin"] == "UNRESOLVED_LOCAL_HASHES_ONLY" and plan["generation_calls"] == 0 and
            plan["counts_used_for_selection"] is False, "fixed pair contract changed")
    bound = inspect_material(Path(plan["materialroot"]))
    require(all(plan[key] == value for key, value in bound.items()) and
            plan["commands"] == {arm: fit_command(plan, root, arm) for arm in ARMS}, "base/material/config/command changed")
    return plan


def validate_manifest(plan, arm, manifest):
    require(manifest["config"] == plan["config"] and manifest["base_model"] == plan["model"] and
            "warm_start" not in manifest and "svd_init" not in manifest and manifest["empty"] is False and
            manifest["steps"] == manifest["micro_batches"] == 128 and manifest["epochs_run"] == 4 and
            manifest["nonfinite_batches"] == 0 and math.isfinite(manifest["final_loss"]), "incomplete/nonfresh/wrong fit")
    corpus = manifest["corpus"]
    require(corpus["sha256"] == plan["material_files"][arm + ".json"] and
            corpus["n_items"] == corpus["n_encoded"] == 128 and corpus["n_skipped_no_target"] == 0 and
            all(manifest["truncation"][key] == 0 for key in
                ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "corpus/drop/split mismatch")
    require(manifest["tokens"]["total"] == 11248 and manifest["tokens"]["target"] == 1888 and
            manifest["tokens"]["context"] == 9360 and manifest["train_tokens_seen"] == 44992 and
            manifest["epochs_run"] * manifest["tokens"]["target"] == 7552, "actual token accounting mismatch")
    lora = manifest["lora"]
    require(lora["rank"] == 8 and lora["alpha"] == 16 and lora["dropout"] == .05 and
            lora["target_modules"] == plan["config"]["target_modules"] and lora["layers"] == "all" and
            lora["freeze_a"] is False and lora["trainable_params"] > 0, "LoRA manifest mismatch")


def verify_fit(plan, stage, arm):
    adapter = stage / "adapter"
    require((adapter / "DONE").is_file(), "missing DONE")
    validate_manifest(plan, arm, read(adapter / "train_manifest.json"))
    files = base.tree_hashes(adapter)
    weights = [name for name in ("adapter_model.safetensors", "adapter_model.bin") if name in files]
    require(len(weights) == 1 and (adapter / weights[0]).stat().st_size > 0 and
            not any(name.startswith(("model", "pytorch_model", "optimizer", "checkpoint")) or "/" in name for name in files), "missing/ambiguous/nested/full-model checkpoint")
    config = read(adapter / "adapter_config.json")
    require(config["r"] == 8 and config["lora_alpha"] == 16 and config["lora_dropout"] == .05 and
            set(config["target_modules"]) == set(plan["config"]["target_modules"]) and config["bias"] == "none" and
            config["peft_type"] == "LORA" and config["base_model_name_or_path"] == plan["model"] and
            not config.get("modules_to_save") and not config.get("rank_pattern") and not config.get("alpha_pattern") and
            not config.get("layers_to_transform") and not config.get("layers_pattern") and not config.get("fan_in_fan_out", False) and
            not config.get("use_dora", False) and not config.get("use_rslora", False), "saved adapter configuration mismatch")
    return dict(arm=arm, adapter=str(adapter), adapter_files=files, manifest_sha256=digest(adapter / "train_manifest.json"),
                counts=COUNTS, initialization="fresh frozen base; no parent/optimizer resume", claim=CLAIM,
                base_freezing_evidence="pinned V3 fresh PEFT path and LoRA manifest; not an independent base-tensor dump")


def execute_arm(root, plan, arm, effective):
    stage = fresh(root / "run" / arm)
    stage.mkdir()
    require(not (stage / "adapter").exists(), "fresh adapter required")
    receipt = base.supervise(root / "run", dict(plan, lease_end=effective), stage / "worker", plan["commands"][arm])
    require(receipt["ok"] is True and receipt["reservation_release_verified"] is True, "supervision failed")
    result = verify_fit(plan, stage, arm)
    verify(root)
    result.update(supervision=receipt, plan_sha256=digest(root / "plan.json"))
    write(stage / "fit-result.json", result)
    return result


def run(root, allow_gpu=False, clock=None):
    require(allow_gpu, "Main allocation and explicit --allow-gpu required")
    started, monotonic = clock if clock is not None else (time.time(), time.monotonic())
    root = Path(root).resolve(strict=True)
    plan = read_plan(root)
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["device"], "wrong inherited Main device")
    effective = bounds(started, plan["deadline"], plan["real_lease_end"])
    pair = fresh(root / "run")
    pair.mkdir()
    record = dict(controller_pid=os.getpid(), device=plan["device"], started=started, effective_deadline=effective,
        real_lease_end=plan["real_lease_end"], plan_sha256=digest(root / "plan.json"),
        reservation="continuous controller/CPU/gaps/cleanup; Main full vacancy check before spawn and external ledger")
    write(pair / "reservation.json", record)
    completed, error = {}, None
    def interrupted(number, frame):
        raise RuntimeError(f"pair interruption/cleanup boundary: {number}")
    handlers = {number: signal.signal(number, interrupted) for number in (signal.SIGALRM, signal.SIGINT, signal.SIGTERM)}
    signal.setitimer(signal.ITIMER_REAL, max(.001, effective - time.time() - 140))
    try:
        verify(root)
        for arm in ARMS:
            require(time.time() < effective - 150, "pair budget exhausted")
            completed[arm] = execute_arm(root, plan, arm, effective)
        require(all(base.tree_hashes(result["adapter"]) == result["adapter_files"] for result in completed.values()), "completed adapter changed")
    except BaseException as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        accounted = False
        try:
            receipts = [read(path) for path in pair.glob("**/supervision.json")]
            require(all(math.isfinite(item["reserved_seconds"]) and item["reserved_seconds"] >= 0 for item in receipts), "invalid worker cost")
            accounted = all((path.parent / "supervision.json").is_file() for path in pair.glob("**/process.json"))
            released = accounted and base.supervisor.gpu_processes_absent(plan["device"]) is True and all(
                all(item.get(key) is True for key in ("reservation_release_verified", "owned_group_empty", "gpu_processes_absent")) for item in receipts)
        except Exception as failure:
            receipts, released = [], False
            error = error or dict(type=type(failure).__name__, message=str(failure))
        ended = time.time()
        result = dict(record, status="COMPLETE" if error is None and list(completed) == list(ARMS) and len(receipts) == 2 and
            all(item.get("ok") is True and item.get("returncode") == 0 for item in receipts) and released and ended <= effective
            else "FAILED_PARTIAL_NO_RETRY", arms=completed, error=error, ended=ended,
            reserved_seconds=time.monotonic()-monotonic, worker_reserved_seconds=sum(item["reserved_seconds"] for item in receipts),
            release_verified=released, worker_accounting_complete=accounted, deadline_met=ended <= effective, generation_calls=0,
            claim=CLAIM, origin="UNRESOLVED_LOCAL_HASHES_ONLY", monetary_cost=None)
        write(pair / "terminal.json", result)
        for number, handler in handlers.items():
            signal.signal(number, handler)
    require(result["status"] == "COMPLETE", "partial pair; retain artifacts; no retry/resume")
    return result


def main():
    clock = time.time(), time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "run", "status"))
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--runroot", required=True)
    parser.add_argument("--materialroot")
    parser.add_argument("--device")
    parser.add_argument("--deadline", type=float)
    parser.add_argument("--lease-end", type=float)
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args()
    bind(args.source_root)
    if args.stage == "prepare":
        require(all(getattr(args, key) is not None for key in ("materialroot", "device", "deadline", "lease_end")), "missing prepare inputs")
        result = prepare(args.runroot, args.materialroot, args.device, args.deadline, args.lease_end)
    elif args.stage == "run":
        result = run(args.runroot, args.allow_gpu, clock)
    else:
        root = Path(args.runroot).resolve(strict=True)
        read_plan(root)
        result = read(root / "run/terminal.json") if (root / "run/terminal.json").is_file() else dict(
            status="NONTERMINAL_OR_ABANDONED" if (root / "run").exists() else "NOT_STARTED")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()

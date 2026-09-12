"""Fixed seed1/seed2 replication utility. Preparation is NOT launch authorization."""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict
import json
import math
from pathlib import Path
import sys
import time

from organism_v6 import fundamental_teaching_readout as readout
from organism_v6 import rulegame_parenting_diagnostic as base
from organism_v6 import train_adapter_v3 as trainer
from gpu.astra_mini_sudoku_diagnostic import check_free


SEEDS = (1, 2)
ARMS = ("teach", "control")
DEVICES = {1: {"teach": "0", "control": "1"}, 2: {"teach": "2", "control": "3"}}
SEED0_PLAN_SHA256 = "d5a3d0297290184061b5cfcc3bf7fa5ba36a5995fbaedb021df464be7879ec5e"
PAIR_SCRIPT_SHA256 = "06d292311e0307b3121593cc2d34bb5c753480eb1537cced1c7fdbff913bd89a"
OFF_PLAN_SHA256 = "e275ebf4f27f0a3b35fd87ac983843e9edcf73e1239bd01be60f4952f3845fc8"
TOKENS = dict(input_tokens=4517, target_tokens=912)
MATERIAL_ROLE = "OPEN_LOOP_AUTHORED_BIRTH_POSITIVE_CONTROL_NOT_CHILD_SLEEP"


def sealed_plan(root, expected=None):
    root = Path(root)
    actual = base.digest(root / "plan.json")
    base.require(actual == base.read(root / "plan.sha256.json")["sha256"] and
                 (expected is None or actual == expected), "plan seal/pinned attempt1 differs")
    return base.read(root / "plan.json")


def recipe(model, seed):
    return asdict(trainer.TrainConfig(rank=8, alpha=16, dropout=.05, lr=3e-4, epochs=4,
        seed=seed, batch_size=4, grad_accum=1, pack=False, max_len=512, model=model))


def device_for(plan, arm):
    base.require(arm in ARMS and type(plan["config"]["seed"]) is int and plan["config"]["seed"] in SEEDS,
                 "only fixed seed1/seed2 paired allocation is allowed")
    return DEVICES[plan["config"]["seed"]][arm]


def validate_seed0(plan):
    base.require(plan["config"] == recipe(plan["model"], 0), "seed0 recipe differs")
    base.require(plan["status"] == "NATIVE_ENCODER_AND_PAIRED_TOKENS_VERIFIED" and
                 plan["selected_control_label"] == "COMPUTED" and
                 plan["material_role"] == MATERIAL_ROLE and
                 plan["model_origin"] == "UNRESOLVED_LOCAL_HASHES_ONLY" and
                 plan["fits_authorized_by_script"] is False, "seed0 material contract differs")
    base.require(plan["eval_dev_ids"] == list(readout.CASE_IDS), "fixed dev cases differ")
    base.require(type(plan["lease_end"]) is float and math.isfinite(plan["lease_end"]), "invalid lease")
    base.require(plan["tokens"] == {arm: TOKENS for arm in ARMS}, "paired token totals differ")
    reference = None
    for arm in ARMS:
        rows = plan["row_audits"][arm]
        signature = [(row["case_id"], row["input_tokens"], row["target_tokens"]) for row in rows]
        base.require(len(rows) == len({row["case_id"] for row in rows}) == 80 and
                     all(type(row["input_tokens"]) is int and type(row["target_tokens"]) is int and
                         0 < row["target_tokens"] < row["input_tokens"] <= 512 for row in rows),
                     "invalid per-row token audit")
        base.require(sum(row["input_tokens"] for row in rows) == TOKENS["input_tokens"] and
                     sum(row["target_tokens"] for row in rows) == TOKENS["target_tokens"], "row totals differ")
        base.require(reference is None or reference == signature, "paired row tokens/order differ")
        reference = signature
    base.require(base.WORKER_SECONDS == 600 and base.RESERVED_SECONDS == 1800, "supervision bounds changed")


def transform_plan(seed0, seed, provenance):
    validate_seed0(seed0)
    base.require(type(seed) is int and seed in SEEDS, "only paired seeds 1 and 2 are allowed")
    plan = copy.deepcopy(seed0)
    plan["config"]["seed"] = seed
    plan["replication"] = dict(copy.deepcopy(provenance), seed=seed, paired_seeds=list(SEEDS),
        status="PREPARED_NOT_AUTHORIZED", fresh_adapter_per_arm=True, off_binding_scope="plan-only same base; Main verifies OFF results")
    return plan


def dependency_hashes():
    result = readout.sources()
    result["train_adapter_v3.py"] = base.digest(base.REPO / "organism_v6" / "train_adapter_v3.py")
    result["gpu/astra_mini_sudoku_diagnostic.py"] = base.digest(base.REPO / "gpu" / "astra_mini_sudoku_diagnostic.py")
    result["replication_script"] = base.digest(__file__)
    return result


def load_seed0(root, pair_script, off_root):
    root, pair_script, off_root = Path(root), Path(pair_script), Path(off_root)
    plan = sealed_plan(root, SEED0_PLAN_SHA256)
    validate_seed0(plan)
    sources = dict(base.sources(), **{name: base.digest(base.REPO / "organism_v6" / name)
        for name in ("fundamental_teaching_corpus.py", "train_adapter_v3.py")})
    sources["launcher_script"] = base.digest(pair_script)
    base.require(sources["launcher_script"] == PAIR_SCRIPT_SHA256 and sources == plan["source_hashes"],
                 "seed0 launcher or source bytes changed")
    base.require(base.model_hashes(plan["model"]) == plan["model_files"], "base model bytes changed")
    material = {}
    for arm in ARMS:
        path = root / (arm + ".json")
        base.require(not path.is_symlink() and base.digest(path) == plan["corpus_sha256"][arm], "seed0 corpus changed")
        material[arm] = path.read_bytes()
        rows = base.decode(material[arm].decode("utf-8"))["corpus"]
        base.require(len(rows) == 80 and [row["group"] for row in rows] ==
                     [row["case_id"] for row in plan["row_audits"][arm]], "export/audit order differs")
    off = sealed_plan(off_root, OFF_PLAN_SHA256)
    base.require(off["adapter"] is None and off["adapter_files"] == {} and off["model"] == plan["model"] and
                 off["model_files"] == plan["model_files"] and off["source_hashes"] == readout.sources() and
                 off["cases"] == readout.selected_cases() and off["requests"] == readout.requests(off["cases"]) and
                 off["worker_seconds"] == 600 and off["output_token_ceiling"] == 3072, "OFF plan/base/dev binding differs")
    return plan, material


def require_fresh(path):
    path = Path(path)
    base.require(not path.exists() and not path.is_symlink(), "stale/partial path; never retry or overwrite: " + str(path))


def write_plan(root, plan):
    base.write_json(root / "plan.json", plan)
    base.write_json(root / "plan.sha256.json", dict(sha256=base.digest(root / "plan.json")))


def prepare(seed0_root, out, pair_script, off_root):
    for path in (out, Path(out) / "seed1", Path(out) / "seed2"):
        require_fresh(path)
    seed0_root, pair_script, off_root = (Path(path).expanduser().resolve(strict=True)
                                        for path in (seed0_root, pair_script, off_root))
    destination = Path(out).expanduser().resolve()
    for source in (seed0_root, off_root):
        base.require(destination != source and destination not in source.parents and
                     source not in destination.parents, "output overlaps seed0 evidence")
    base.require(destination != pair_script and destination not in pair_script.parents, "output overlaps seed0 launcher")
    seed0, material = load_seed0(seed0_root, pair_script, off_root)
    provenance = dict(seed0_root=str(seed0_root), seed0_plan_sha256=SEED0_PLAN_SHA256,
                      pair_script=str(pair_script), pair_script_sha256=PAIR_SCRIPT_SHA256,
                      off_root=str(off_root), off_plan_sha256=OFF_PLAN_SHA256,
                      dependency_hashes=dependency_hashes(), python=sys.executable)
    root = base.fresh_directory(out, seed0["model"])
    prepared = {}
    for seed in SEEDS:
        child = base.fresh_directory(root / f"seed{seed}", seed0["model"])
        plan = transform_plan(seed0, seed, provenance)
        for arm in ARMS:
            with (child / (arm + ".json")).open("xb") as target:
                target.write(material[arm])
            base.require(base.digest(child / (arm + ".json")) == plan["corpus_sha256"][arm], "copy changed corpus bytes")
        write_plan(child, plan)
        prepared[str(seed)] = dict(root=str(child), plan_sha256=base.digest(child / "plan.json"))
    result = dict(status="BOTH_SEEDS_PREPARED_NOT_AUTHORIZED", seeds=prepared,
                  optimizer_seeds=list(SEEDS), off_root=str(off_root), model_calls=0, training_calls=0)
    base.write_json(root / "preparation.json", result)
    return result


def verify(root):
    root = Path(root).resolve(strict=True)
    plan = sealed_plan(root)
    provenance = plan["replication"]
    seed = provenance["seed"]
    completion = base.read(root.parent / "preparation.json")
    base.require(completion["status"] == "BOTH_SEEDS_PREPARED_NOT_AUTHORIZED" and
                 completion["optimizer_seeds"] == list(SEEDS) and set(completion["seeds"]) == {"1", "2"},
                 "partial paired preparation")
    for selected in SEEDS:
        item = completion["seeds"][str(selected)]
        child = root.parent / f"seed{selected}"
        base.require(item["root"] == str(child) and base.digest(child / "plan.json") == item["plan_sha256"],
                     "paired plan changed or missing")
        sibling = sealed_plan(child)
        for arm in ARMS:
            material = child / (arm + ".json")
            base.require(not material.is_symlink() and base.digest(material) == sibling["corpus_sha256"][arm],
                         "paired corpus changed or missing")
    base.require(root.name == f"seed{seed}" and provenance["dependency_hashes"] == dependency_hashes() and
                 provenance["python"] == sys.executable and provenance["seed0_plan_sha256"] == SEED0_PLAN_SHA256 and
                 provenance["pair_script_sha256"] == PAIR_SCRIPT_SHA256 and provenance["off_plan_sha256"] == OFF_PLAN_SHA256,
                 "replication source/interpreter/provenance changed")
    seed0, material = load_seed0(provenance["seed0_root"], provenance["pair_script"], provenance["off_root"])
    base.require(plan == transform_plan(seed0, seed, provenance), "replication changed more than the fixed seed")
    for arm in ARMS:
        path = root / (arm + ".json")
        base.require(not path.is_symlink() and path.read_bytes() == material[arm], "replication corpus bytes changed")
    return plan


def fit_command(root, plan, arm):
    base.require(arm in ARMS, "teach/control only")
    command = [sys.executable, "-B", "-m", "organism_v6.train_adapter_v3", "--corpus", str(Path(root) / (arm + ".json")),
        "--out", str(Path(root) / ("fit_" + arm) / "adapter"), "--model", plan["model"], "--rank", "8", "--alpha", "16",
        "--dropout", "0.05", "--lr", "0.0003", "--epochs", "4", "--seed", str(plan["config"]["seed"]),
        "--batch-size", "4", "--grad-accum", "1", "--no-pack", "--max-len", "512"]
    base.require(asdict(trainer.config_from_args(trainer.build_parser().parse_args(command[4:]))) == plan["config"],
                 "effective native CLI recipe differs")
    return command


def successful_supervision(receipt, device):
    base.require(all(receipt.get(key) is True for key in ("ok", "reservation_release_verified", "owned_group_empty",
                 "gpu_processes_absent")) and receipt.get("returncode") == 0 and receipt.get("error") is None and
                 receipt["device"] == device and math.isfinite(receipt["reserved_seconds"]) and
                 receipt["reserved_seconds"] > 0, "worker failed/partial or cleanup unverified")


def validate_fit_manifest(plan, arm, manifest, saved):
    base.require(manifest["config"] == plan["config"] and manifest["base_model"] == plan["model"], "actual recipe/base differs")
    base.require(manifest["steps"] == manifest["micro_batches"] == 80 and manifest["epochs_run"] == 4 and
                 manifest["nonfinite_batches"] == 0 and manifest["empty"] is False and
                 math.isfinite(manifest["final_loss"]), "incomplete/nonfinite fit")
    counts = manifest["corpus"]
    base.require(counts["sha256"] == plan["corpus_sha256"][arm] and
                 counts["n_items"] == counts["n_encoded"] == 80 and counts["n_skipped_no_target"] == 0, "actual corpus differs")
    base.require(all(manifest["truncation"][name] == 0 for name in
                 ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "actual truncation/split")
    base.require(manifest["tokens"]["total"] == TOKENS["input_tokens"] and
                 manifest["tokens"]["target"] == TOKENS["target_tokens"] and
                 manifest["train_tokens_seen"] == 4 * TOKENS["input_tokens"], "actual tokens differ")
    base.require(saved["r"] == 8 and saved["lora_alpha"] == 16 and saved["lora_dropout"] == .05 and
                 saved["peft_type"] == "LORA" and saved["bias"] == "none" and
                 Path(saved["base_model_name_or_path"]).resolve() == Path(plan["model"]).resolve() and
                 set(saved["target_modules"]) == set(plan["config"]["target_modules"]), "saved adapter config differs")


def verify_fit(root, arm, seal=True):
    base.require(arm in ARMS, "teach/control only")
    root = Path(root).resolve()
    plan = verify(root)
    stage = root / ("fit_" + arm)
    adapter = stage / "adapter"
    supervision = base.read(stage / "worker" / "supervision.json")
    device = device_for(plan, arm)
    successful_supervision(supervision, device)
    process = base.read(stage / "worker" / "process.json")
    base.require(process["argv"] == fit_command(root, plan, arm) and process["device"] == device and
                 0 < process["timeout"] <= 600, "worker command/bounds differ")
    launch = base.read(stage / "allocation.json")
    base.require(launch["plan_sha256"] == base.digest(root / "plan.json") and launch["arm"] == arm and
                 launch["device"] == device and launch["fresh_adapter"] is True, "fit allocation differs")
    base.require((adapter / "DONE").is_file() and not (adapter / "EMPTY_CORPUS").exists(), "missing DONE/empty fit")
    weights = [adapter / name for name in ("adapter_model.safetensors", "adapter_model.bin") if (adapter / name).is_file()]
    base.require(len(weights) == 1 and weights[0].stat().st_size > 0, "missing/ambiguous adapter weights")
    manifest = base.read(adapter / "train_manifest.json")
    validate_fit_manifest(plan, arm, manifest, base.read(adapter / "adapter_config.json"))
    result = dict(status="FIT_COMPLETE_PENDING_PAIRED_READOUT", seed=plan["config"]["seed"], arm=arm,
        adapter=str(adapter), adapter_files=base.tree_hashes(adapter), plan_sha256=base.digest(root / "plan.json"),
        supervision_sha256=base.digest(stage / "worker" / "supervision.json"), steps=80,
        input_tokens_seen=18068, target_tokens_seen=3648)
    receipt = stage / "verified.json"
    if receipt.exists():
        base.require(base.read(receipt) == result, "verified fit artifact changed")
    elif seal:
        base.write_json(receipt, result)
    else:
        base.require(False, "fit not terminally sealed; use verify-fit")
    return result


def launch_fit(root, arm, allow_gpu=False):
    base.require(allow_gpu and arm in ARMS, "Main selection/allocation and explicit --allow-gpu required")
    root = Path(root).resolve()
    stage = root / ("fit_" + arm)
    require_fresh(stage)
    plan = verify(root)
    device = device_for(plan, arm)
    base.require(plan["lease_end"] - time.time() > 1800, "insufficient inherited lease")
    command = fit_command(root, plan, arm)
    gpu, xml = check_free(device)
    stage = base.fresh_directory(stage, plan["model"])
    require_fresh(stage / "adapter")
    with (stage / "gpu.xml").open("x") as target:
        target.write(xml)
    base.write_json(stage / "allocation.json", dict(arm=arm, device=device, gpu=gpu,
        plan_sha256=base.digest(root / "plan.json"), fresh_adapter=True, started=time.time()))
    base.supervise(root, dict(plan, device=device), stage / "worker", command)
    return verify_fit(root, arm)


def prepare_readouts(root):
    root = Path(root).resolve()
    require_fresh(root / "readouts")
    require_fresh(root / "readout_preparation.json")
    plan = verify(root)
    fits = {arm: verify_fit(root, arm, seal=False) for arm in ARMS}
    parent = base.fresh_directory(root / "readouts", plan["model"])
    prepared = {}
    for arm in ARMS:
        target = parent / arm
        actual = readout.prepare(target, plan["model"], fits[arm]["adapter"], device_for(plan, arm), plan["lease_end"])
        base.require(actual["model_files"] == plan["model_files"] and actual["adapter_files"] == fits[arm]["adapter_files"] and
                     [case["id"] for case in actual["cases"]] == plan["eval_dev_ids"], "native readout fit/base/dev binding differs")
        prepared[arm] = dict(root=str(target), plan_sha256=base.digest(target / "plan.json"))
    base.require(sealed_plan(parent / "teach")["requests"] == sealed_plan(parent / "control")["requests"],
                 "paired readout requests differ")
    result = dict(status="BOTH_ADAPTER_READOUTS_PREPARED", cells=prepared,
                  off_root=plan["replication"]["off_root"], off_plan_sha256=OFF_PLAN_SHA256,
                  off_scope="same-base plan reference only; Main verifies seed0 OFF completion/results",
                  new_off_calls=0, confirmation_calls=0)
    base.write_json(root / "readout_preparation.json", result)
    return result


def launch_readout(root, arm, allow_gpu=False):
    base.require(allow_gpu and arm in ARMS, "Main selection/allocation and explicit --allow-gpu required")
    root = Path(root).resolve()
    target = root / "readouts" / arm
    require_fresh(target / "launch")
    require_fresh(target / "run")
    plan = verify(root)
    device = device_for(plan, arm)
    fit = verify_fit(root, arm, seal=False)
    preparation = base.read(root / "readout_preparation.json")
    base.require(preparation["status"] == "BOTH_ADAPTER_READOUTS_PREPARED" and set(preparation["cells"]) == set(ARMS),
                 "partial paired readout preparation")
    for selected in ARMS:
        binding = preparation["cells"][selected]
        base.require(binding["root"] == str(root / "readouts" / selected), "readout root differs")
        sealed_plan(binding["root"], binding["plan_sha256"])
    actual, cases = readout.verify(target)
    base.require(actual["model_files"] == plan["model_files"] and actual["model"] == plan["model"] and
                 actual["adapter"] == fit["adapter"] and actual["adapter_files"] == fit["adapter_files"] and
                 actual["device"] == device and len(cases) == 48 and
                 actual["lease_end"] == plan["lease_end"], "readout binding differs")
    base.require(plan["lease_end"] - time.time() > 1800, "insufficient inherited lease")
    gpu, xml = check_free(device)
    launch = base.fresh_directory(target / "launch", plan["model"])
    with (launch / "gpu.xml").open("x") as output:
        output.write(xml)
    base.write_json(launch / "allocation.json", dict(gpu=gpu, device=device,
        plan_sha256=base.digest(target / "plan.json"), started=time.time()))
    return readout.run(target, allow_gpu=True)


def terminal_status(root):
    root = Path(root).resolve()
    plan = verify(root)
    result = dict(seed=plan["config"]["seed"], fits={}, readouts={}, reads_model_outputs=False)
    for arm in ARMS:
        stage = root / ("fit_" + arm)
        if not stage.exists():
            result["fits"][arm] = "NOT_STARTED"
        else:
            try:
                verify_fit(root, arm, seal=False)
                result["fits"][arm] = "VERIFIED_COMPLETE"
            except (ValueError, OSError, KeyError, TypeError) as error:
                result["fits"][arm] = "NOT_TERMINALLY_VERIFIED_DO_NOT_RELAUNCH: " + str(error)
        target = root / "readouts" / arm
        if not target.exists():
            result["readouts"][arm] = "NOT_PREPARED"
        else:
            try:
                preparation = base.read(root / "readout_preparation.json")
                base.require(preparation["status"] == "BOTH_ADAPTER_READOUTS_PREPARED" and
                             preparation["cells"][arm]["root"] == str(target), "partial readout preparation")
                sealed_plan(target, preparation["cells"][arm]["plan_sha256"])
                if not (target / "run").exists() and not (target / "launch").exists():
                    result["readouts"][arm] = "PREPARED_ONLY"
                else:
                    successful_supervision(base.read(target / "run" / "worker" / "supervision.json"), device_for(plan, arm))
                    result["readouts"][arm] = "SUPERVISED_COMPLETE_NATIVE_REDUCTION_REQUIRED"
            except (ValueError, OSError, KeyError, TypeError) as error:
                result["readouts"][arm] = "NOT_TERMINALLY_VERIFIED_DO_NOT_RELAUNCH: " + str(error)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "launch-fit", "verify-fit", "prepare-readouts", "launch-readout", "status"))
    parser.add_argument("--seed0-root", type=Path)
    parser.add_argument("--off-root", type=Path)
    parser.add_argument("--pair-script", type=Path, default=Path("/tmp/astra_fundamental_pair_20260912.py"))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--arm", choices=ARMS)
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args(argv)
    if args.stage == "prepare":
        base.require(args.seed0_root is not None and args.out is not None and args.off_root is not None,
                     "--seed0-root, --off-root, --out required")
        result = prepare(args.seed0_root, args.out, args.pair_script, args.off_root)
    else:
        base.require(args.root is not None, "--root required")
        if args.stage in ("launch-fit", "launch-readout"):
            result = (launch_fit if args.stage == "launch-fit" else launch_readout)(args.root, args.arm, args.allow_gpu)
        elif args.stage == "verify-fit":
            result = verify_fit(args.root, args.arm)
        else:
            result = prepare_readouts(args.root) if args.stage == "prepare-readouts" else terminal_status(args.root)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()

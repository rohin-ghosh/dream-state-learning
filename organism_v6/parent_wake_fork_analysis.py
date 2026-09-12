"""Offline lesson/sham raw-wake fit/probe accounting; no parenting or success gate."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path, PurePosixPath

from . import mini_sudoku_behavior_analysis as native
from . import neutral_pair_custody as custody


ARMS = ("lesson", "sham")
WEIGHTS = {"adapter_model.safetensors", "adapter_model.bin"}
TRAIN_CONFIG = dict(rank=8, alpha=16, dropout=0.05, lr=1e-4, epochs=3, seed=0,
                    batch_size=1, grad_accum=1, chat_template=False, pack=False,
                    max_len=4096, add_eos=True, optimizer="adamw", grad_checkpoint=True)
MODULES = {"q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"}
BUDGET = dict(gen_seed=0, seed_salt=15420, budget_ticks=1, wake_max_tokens=400,
              scratchpad_max_tokens=100, total_token_budget=38400, max_episodes=16)
DOSES = {"lesson": dict(input_tokens=31747, target_tokens=4289),
         "sham": dict(input_tokens=31527, target_tokens=5360)}
TEACHER_TOKENS = {"lesson": 203, "sham": 158}
require = native._require


def _hash(path, inputs):
    require(path.is_file() and not path.is_symlink(), f"missing or unsafe file: {path}")
    value = custody._digest(path)
    require(inputs.hashes.setdefault(str(path), value) == value, f"file changed: {path}")
    return value


def _material(plan, material, inputs):
    bound = plan["bound"]
    inventory = inputs.read(material / "artifact_hashes.json")
    require(dict(files=inventory["files"], manifest_sha256=inputs.hashes[str(material / "artifact_hashes.json")])
            == bound["inventory"], "plan/export inventory mismatch")
    required = {"results.json", "selection.json", "original_sources.json", "source_hashes.json"}
    required.update(f"{arm}{suffix}.json" for arm in ARMS for suffix in ("", "_source_map"))
    require(set(inventory["files"]) == required, "export file inventory mismatch")
    exported = {}
    for name, expected in inventory["files"].items():
        path = custody._file(material, name)
        exported[name] = inputs.read(path)
        require(inputs.hashes[str(path)] == expected, f"export hash mismatch: {name}")
    selection, result = exported["selection.json"], exported["results.json"]
    selected = selection["selected_episodes"]
    require(selection["count"] == len(selected) == len(set(selected)) == 32
            and selection["selection"] == "measured" and selection["max_len"] == 4096
            and selected == bound["selected"], "export selection mismatch")
    require(result["status"] == "READY" and result["selection"] == selection
            and result["boundary"]["tokenizer_validation"] == "actual local tokenizer", "export not native READY")
    require(len(bound["source_episodes"]) == len(set(bound["source_episodes"])) == 64
            and set(selected) <= set(bound["source_episodes"])
            and not set(bound["source_episodes"]) & set(native.EPISODE_IDS), "source/canary ID mismatch")
    require(bound["tokens"] == DOSES and bound["teacher_tokens"] == TEACHER_TOKENS, "prospective dose mismatch")
    sources = exported["original_sources.json"]
    require([sources[arm]["root"] for arm in ARMS] == bound["source_roots"], "original source roots mismatch")
    for arm in ARMS:
        corpus, rows = exported[f"{arm}.json"], exported[f"{arm}_source_map.json"]["rows"]
        require(sources[arm]["local_pins"] == bound["pins"], "original source model pins mismatch")
        require(corpus["recipe"] == "source_linked_raw_wake_v3_spans_v1"
                and corpus["boundary"] == result["boundary"] and len(rows) == 32
                and corpus["corpus"] == [row["item"] for row in rows]
                and [row["item"]["meta"]["episode_id"] for row in rows] == selected, "corpus/source-map mismatch")
        for row in rows:
            require(row["item"]["spans"] == [[row["rendered_context"], False, "parent_removed_context"],
                    [row["source"]["raw_output"], True, "raw_child_wake"]], "exported spans changed")
            require(type(row["input_tokens"]) is int and type(row["target_tokens"]) is int
                    and 0 < row["target_tokens"] < row["input_tokens"] <= 4096, "invalid exported token counts")
        totals = {key: sum(row[key] for row in rows) for key in ("input_tokens", "target_tokens")}
        require(totals == bound["tokens"][arm] and result["arms"][arm]["selected_examples"] == 32
                and all(result["arms"][arm][key] == value for key, value in totals.items())
                and result["arms"][arm]["teacher_tokens"] == bound["teacher_tokens"][arm], "export dose accounting mismatch")
    return dict(source_hashes=exported["source_hashes.json"], original_sources=sources,
                selection=selection, boundary=result["boundary"], question_audit=bound["question_audit"])


def _fit(root, plan, arm, inputs):
    remote_root, material = PurePosixPath(plan["root"]), PurePosixPath(plan["material"])
    model = plan["bound"]["pins"]["model_path"]
    command = plan["commands"][arm]
    expected = [command[0], "-B", "-m", "organism_v6.train_adapter_v3", "--corpus", str(material / f"{arm}.json"),
                "--out", str(remote_root / "training" / f"{arm}_seed0"), "--model", model,
                "--rank", "8", "--alpha", "16", "--dropout", "0.05", "--lr", "1e-4", "--epochs", "3",
                "--seed", "0", "--batch-size", "1", "--grad-accum", "1", "--no-pack", "--max-len", "4096"]
    require(command == expected, "planned trainer command/arm mismatch")
    directory = root / "training" / f"{arm}_seed0"
    manifest, meta, adapter = [inputs.read(directory / name) for name in
                               ("train_manifest.json", "train_meta.json", "adapter_config.json")]
    _hash(directory / "DONE", inputs)
    require((directory / "DONE").read_text().strip() == "ok", "training DONE mismatch")
    require(all(manifest["config"][key] == value for key, value in TRAIN_CONFIG.items()), "actual trainer config mismatch")
    require(manifest["base_model"] == manifest["config"]["model"] == adapter["base_model_name_or_path"] == model,
            "fit model mismatch")
    require(adapter["r"] == 8 and adapter["lora_alpha"] == 16 and adapter["lora_dropout"] == 0.05
            and set(adapter["target_modules"]) == set(manifest["config"]["target_modules"]) == MODULES,
            "adapter shape/targets mismatch")
    corpus = manifest["corpus"]
    require(corpus["file"] == f"{arm}.json" and corpus["sha256"] == plan["bound"]["inventory"]["files"][f"{arm}.json"]
            and corpus["n_items"] == corpus["n_encoded"] == 32 and corpus["n_skipped_no_target"] == 0,
            "actual fit corpus/arm mismatch")
    require(manifest["steps"] == meta["steps"] == 96 and manifest["nonfinite_batches"] == 0
            and math.isfinite(manifest["final_loss"]) and meta["final_loss"] == manifest["final_loss"], "incomplete fit")
    require(all(meta[key] == TRAIN_CONFIG[key] for key in ("rank", "epochs", "lr", "seed"))
            and meta["n_texts"] == 32, "train_meta configuration mismatch")
    dose = plan["bound"]["tokens"][arm]
    require(manifest["tokens"]["target"] == dose["target_tokens"]
            and manifest["tokens"]["total"] == dose["input_tokens"]
            and manifest["tokens"]["context"] == dose["input_tokens"] - dose["target_tokens"]
            and manifest["train_tokens_seen"] == meta["tokens"] == 3 * dose["input_tokens"], "actual fit dose mismatch")
    require(all(manifest["truncation"][key] == 0 for key in
                ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "fit material loss")
    return dict(train_manifest=manifest, train_meta=meta, adapter_config=adapter,
                input_token_passes=3 * dose["input_tokens"], target_token_passes=3 * dose["target_tokens"],
                historical_teacher_tokens=plan["bound"]["teacher_tokens"][arm])


def _probe(root, plan, arm, spec, inputs):
    remote = PurePosixPath(plan["root"])
    pins = plan["bound"]["pins"]
    expected = dict(BUDGET, model_path=pins["model_path"], expected_model_hashes=pins["files"],
        adapter_path=str(remote / "training" / f"{arm}_seed0"), episode_ids=list(native.EPISODE_IDS),
        probe_root=str(remote / "probes"), output_dir=str(remote / "probes" / arm),
        families_path=str(PurePosixPath(plan["source"]) / "organism_v6/reasoning_gym_families.json"),
        families_sha256=plan["families_sha256"], max_model_len=4096, order=["off", "on"],
        panel_role="development_validation", selection_used_episode_ids=plan["bound"]["source_episodes"],
        training_life_roots=[str(remote / "training"), plan["material"], *plan["bound"]["source_roots"]],
        lineage_roots=[str(remote / "training")])
    require(all(spec[key] == value for key, value in expected.items()), "probe spec/plan/arm mismatch")
    inventory = spec["expected_adapter_hashes"]
    require({"train_manifest.json", "train_meta.json", "adapter_config.json", "DONE"} <= inventory.keys()
            and len(WEIGHTS & inventory.keys()) == 1, "incomplete adapter inventory")
    absent = {}
    for name, expected_hash in inventory.items():
        require(custody._sha(expected_hash), "invalid expected adapter hash")
        path = root / "training" / f"{arm}_seed0" / name
        if name in WEIGHTS and not path.exists() and not path.is_symlink():
            absent[name] = expected_hash
        else:
            path = custody._file(root / "training" / f"{arm}_seed0", name)
            require(_hash(path, inputs) == expected_hash, f"adapter hash mismatch: {arm}/{name}")
    pair_root = root / "probes" / arm
    pair = dict(path=str(pair_root), custody=native._pair_custody(pair_root, inputs))
    require(pair["custody"]["status"] == "ARTIFACT_CUSTODY_VALIDATED", "completed native pair required")
    shared = None
    for condition in ("off", "on"):
        cell, settings = native._condition(pair_root, condition, inputs)
        if shared is None:
            shared = settings
        require(shared == settings, "within-pair settings mismatch")
        config = inputs.read(pair_root / condition / "configuration.json")
        identity = config["source_identity"]
        adapter_path = spec["adapter_path"] if condition == "on" else None
        backend_files = {key: value for key, value in inventory.items()
                         if key in WEIGHTS | {"adapter_config.json"}} if condition == "on" else {}
        require(all(config[key] == value for key, value in BUDGET.items())
                and identity["default_temperature"] == 0.7, "actual probe budget mismatch")
        require(identity["model_input"] == pins["model_path"] and config["hashes_before"]["model"] == pins["files"]
                and identity["adapter_input"] == adapter_path and identity["adapter_files"] == backend_files,
                "actual backend model/adapter mismatch")
        require(config["hashes_before"].get("adapter", {}) == (inventory if condition == "on" else {}),
                "actual backend adapter inventory mismatch")
        requests = inputs.read(pair_root / condition / "generations.jsonl", jsonl=True)
        for request in requests:
            if request.get("kind") != "generation_request":
                continue
            actual = request["source_identity"]
            require(actual["model_input"] == pins["model_path"] and actual["adapter_input"] == adapter_path
                    and actual["adapter_files"] == backend_files and request["temperature"] == 0.7,
                    "generation backend binding mismatch")
        for episode in cell["episodes"]:
            ledger = inputs.read(pair_root / condition / episode["ledger"], jsonl=True)
            episode["later_acts"] = [row for row in ledger if row.get("kind") == "act"][1:]
        pair[condition] = cell
    pair["on_minus_off"] = native._difference(pair["on"], pair["off"])
    return pair, shared, dict(expected_adapter_hashes=inventory, missing_weights=absent,
        weight_verification="REMOTE_WEIGHT_HASH_NOT_REHASHED_LOCALLY" if absent else "LOCAL_WEIGHT_BYTES_REHASHED")


def analyze_run(run_root, material_root, remote_rehash=None):
    root, material = Path(run_root).resolve(strict=True), Path(material_root).resolve(strict=True)
    inputs = native._Inputs()
    require(not (root / "FAILED.json").exists(), "run FAILED marker present")
    plan = inputs.read(root / "plan.json")
    prepared = inputs.read(root / "PREPARED.json")
    require(prepared["plan_sha256"] == inputs.hashes[str(root / "plan.json")], "PREPARED/plan hash mismatch")
    require(plan["training_seed"] == 0 and plan["expected_steps"] == 96
            and plan["canaries"] == list(native.EPISODE_IDS), "prospective plan mismatch")
    export = _material(plan, material, inputs)
    launched, started, completed = [inputs.read(root / name) for name in
                                    ("LAUNCHED.json", "STARTED.json", "COMPLETED.json")]
    require(launched["source"] == plan["source"] and launched["script_sha256"] == plan["script_sha256"]
            and launched["pid"] == started["pid"] and launched["device"] == started["device"]
            and launched["sequential_arms"] == started["arms"] == list(ARMS), "controller/source binding mismatch")
    require(set(completed["arms"]) == set(ARMS) and completed["tokens"] == plan["bound"]["tokens"]
            and completed["teacher_tokens"] == plan["bound"]["teacher_tokens"]
            and completed["boundary"] == plan["boundary"], "COMPLETED/plan mismatch")
    pairs, fits, specs, reference = {}, {}, {}, None
    for arm in ARMS:
        fit = _fit(root, plan, arm, inputs)
        spec_path = root / "logs" / arm / "probe_spec.json"
        spec = inputs.read(spec_path)
        evidence = inputs.read(root / "logs" / arm / "result.json")
        done = inputs.read(root / "probes" / arm / "PAIR_DONE.json")
        beginning = inputs.read(root / "probes" / arm / "PAIR_STARTED.json")
        require(evidence == completed["arms"][arm] and evidence["pair_done"] == done
                and evidence["spec_sha256"] == done["spec_sha256"] == beginning["spec_sha256"] == inputs.hashes[str(spec_path)]
                and beginning["spec"] == spec and evidence["adapter_hashes"] == spec["expected_adapter_hashes"],
                "completion/spec/adapter binding mismatch")
        pair, shared, weights = _probe(root, plan, arm, spec, inputs)
        if reference is None:
            reference = shared
        require(shared == reference, "cross-arm probe settings/model mismatch")
        pairs[arm], fits[arm], specs[arm] = pair, dict(**fit, **weights), spec
    remote = dict(status="NOT_PROVIDED", scope="Remote rehash can be attached later; no local weight claim")
    if remote_rehash is not None:
        receipt = inputs.read(Path(remote_rehash).resolve(strict=True))
        records = receipt["records"]
        require(len(records) == 2 and {row["arm"] for row in records} == set(ARMS), "remote rehash arms mismatch")
        for row in records:
            arm = row["arm"]
            require(row["training_seed"] == 0 and row["adapter_path"] == specs[arm]["adapter_path"]
                    and row["spec_sha256"] == inputs.hashes[str(root / "logs" / arm / "probe_spec.json")]
                    and row["actual_adapter_hashes"] == row["expected_adapter_hashes"] == specs[arm]["expected_adapter_hashes"],
                    "remote rehash binding mismatch")
        remote = dict(status="RECORDED_REMOTE_REHASH_BOUND", receipt=receipt,
                      scope="Receipt-backed remote byte claim, not local rehash or loaded-runtime authentication")
    contrasts = {condition: native._difference(pairs["lesson"][condition], pairs["sham"][condition])
                 for condition in ("off", "on", "on_minus_off")}
    off = [dict(episode_id=left["episode_id"], lesson=left["metrics"]["first_act_native_score_zero_filled"],
                sham=right["metrics"]["first_act_native_score_zero_filled"])
           for left, right in zip(pairs["lesson"]["off"]["episodes"], pairs["sham"]["off"]["episodes"])]
    inputs.verify()
    return dict(schema="parent-wake-fork-analysis-v1", evidence_label="EXPLORATORY_P0_RAW_WAKE_FORK",
        binding_status="OFFLINE_CAPTURE_BINDINGS_VALIDATED", training_seed=0, episode_ids=list(native.EPISODE_IDS),
        pairs=pairs, lesson_minus_sham=contrasts, fits=fits, paired_settings=reference,
        off_agreement=dict(per_board=off, exact_score_agreement=all(row["lesson"] == row["sham"] for row in off)),
        material=export, plan=plan, controller_receipts=dict(launched=launched, started=started, completed=completed),
        remote_rehash=remote, input_sha256=inputs.hashes, analyzer_sha256=custody._digest(__file__),
        native_reducer_sha256=custody._digest(native.__file__),
        limitations=["One recipient initialization and reused 16-board development panel; no significance or pass threshold.",
            "Historical teacher dose 203/158 and supervised target passes 12867/16080 are unequal; package-level contrast only.",
            "First ACT is primary; missing/invalid/unmeasured is zero. Later ACT records/native best are separate diagnostics.",
            "Source formation/teacher exclusion was not re-judged; captured exported bytes and accounting are bound, not truth certified.",
            "Historical source/model paths were not opened; pins do not authenticate official origin or GPU-loaded state.",
            "No parenting, G5, H1/H2 or clean-lineage pass; six other source families are untested."])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--material-root", required=True)
    parser.add_argument("--remote-rehash", help="Optional JSON receipt with two arm/seed/path/spec/hash records")
    parser.add_argument("--output-new", required=True)
    args = parser.parse_args(argv)
    output = Path(args.output_new).absolute()
    require(not output.exists() and not output.is_symlink(), "output-new already exists")
    require(all(Path(source).resolve() not in output.resolve().parents
                for source in (args.run_root, args.material_root)), "output-new must be outside captured inputs")
    report = analyze_run(args.run_root, args.material_root, args.remote_rehash)
    encoded = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    with output.open("x", encoding="utf-8") as target:
        target.write(encoded)
    print(f"PARENT_WAKE_FORK_ANALYSIS_WRITTEN {output}")


if __name__ == "__main__":
    main()

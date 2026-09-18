"""One explicitly selected recipient fit and teacher-free probe; Main owns allocation."""
from __future__ import annotations

import argparse
import datetime
import json
import math
import os
from pathlib import Path
import sys

from gpu.astra_mini_sudoku_diagnostic import digest, write_new
from organism_v6 import parent_correction_write as material_writer
from organism_v6 import run_reasoning_neutral as supervisor
from organism_v6.neutral_pair_custody import validate_pair
from organism_v6.reasoning_neutral_probe import file_hashes


SOURCE = Path(__file__).resolve().parents[1]
PANEL_SHA256 = "11b87e8b901978bcb331f2d126632517214e2a62c82221a47afd5baedd01cb2e"
require = material_writer.require


def read(path):
    return json.loads(Path(path).read_bytes())


def inspect_preparation(material, panel_path):
    material = Path(material).resolve(strict=True)
    inventory = read(material / "artifact_hashes.json")["files"]
    actual = {path.relative_to(material).as_posix(): digest(path)
              for path in material.rglob("*") if path.is_file()
              and path != material / "artifact_hashes.json"}
    require(actual == inventory, "material inventory differs")
    report = read(material / "preparation.json")
    require(report["status"] == "READY_CPU_PREPARATION_ONLY" and not report["synthetic"]
            and report["boundary"] == material_writer.BOUNDARY and report["selection"] == material_writer.APPROVED,
            "native approved material required")
    require(report["unique_events"] == 1 and report["explicit_replays_per_arm"] == 32
            and report["recipient_seeds"] == [0, 1, 2] and report["optimizer_steps_per_recipient"] == 96,
            "fixed one-event/replay/seed budget")
    require(material_writer.implementation_pins() == report["implementation"], "implementation drift")
    require(file_hashes(report["model_path"]) == report["expected_model_files"], "base bytes changed")
    require(digest(panel_path) == PANEL_SHA256, "prospective panel changed")
    panel = read(panel_path)
    require(panel["status"] == "NATIVE_PANEL_PREPARED_NO_INFERENCE"
            and len(panel["episode_ids"]) == len(set(panel["episode_ids"])) == 32
            and panel["model_path"] == report["model_path"]
            and panel["families_sha256"] == digest(SOURCE / "organism_v6/reasoning_gym_families.json"),
            "panel/model/native split mismatch")
    gym = material_writer.correction.native.ReasoningGymGym(require_package=True, strict_verifier=True)
    require(all(gym.split_of(row["episode_id"]) == "canary"
                and gym.question(row["episode_id"]) == row["question"] for row in panel["questions"]),
            "native questions changed")
    return report, panel


def selected_command(material, report, arm, seed):
    require(arm in material_writer.ARMS and seed in material_writer.SEEDS, "unknown arm/seed")
    candidates = read(material / arm / "training_commands.json")["commands"]
    selected = [item for item in candidates if item["seed"] == seed]
    require(len(selected) == 1, "one command per selected seed")
    command = selected[0]
    expected = Path(report["recipient_root"]) / arm / f"seed{seed}"
    require(command["output"] == str(expected) and not expected.exists()
            and command["cwd"] == str(SOURCE) and Path(command["argv"][0]).absolute() == Path(sys.executable).absolute()
            and command["argv"][1:4] == ["-B", "-m", "organism_v6.train_adapter_v3"],
            "fresh recipient/interpreter/source required")
    arguments = material_writer.trainer.build_parser().parse_args(command["argv"][4:])
    require(arguments.out == str(expected) and arguments.corpus == str(material / arm / "corpus.json"),
            "trainer argv destinations differ from preparation")
    parsed = material_writer.trainer.config_from_args(arguments)
    require(material_writer.asdict(parsed) == command["config"] and parsed.seed == seed
            and parsed.rank == 8 and parsed.epochs == 3 and parsed.max_steps == 96,
            "prepared trainer configuration differs")
    require(command["corpus_sha256"] == digest(material / arm / "corpus.json")
            and command["trainer_sha256"] == digest(Path(material_writer.trainer.__file__)),
            "corpus/trainer hash differs")
    return command


def verify_fit(adapter, command, tokenization):
    manifest = read(adapter / "train_manifest.json")
    require((adapter / "DONE").is_file() and manifest["config"] == command["config"]
            and manifest["steps"] == 96 and manifest["nonfinite_batches"] == 0
            and math.isfinite(manifest["final_loss"]), "incomplete/nonfinite or wrong-recipe fit")
    require(manifest["base_model"] == command["config"]["model"]
            and manifest["corpus"]["sha256"] == command["corpus_sha256"]
            and manifest["corpus"]["n_items"] == manifest["corpus"]["n_encoded"] == 32
            and manifest["corpus"]["n_skipped_no_target"] == 0, "wrong corpus/base or dropped replay")
    require(all(manifest["truncation"][name] == 0 for name in
                ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")),
            "training material truncated or split")
    require(manifest["tokens"]["target"] == tokenization["supervised_tokens_per_epoch"]
            and manifest["tokens"]["total"] == tokenization["input_tokens_per_epoch"]
            and manifest["train_tokens_seen"] == tokenization["input_tokens_all_epochs"],
            "actual fit token dose differs")
    hashes = file_hashes(adapter)
    require("adapter_config.json" in hashes and any(name.endswith(".safetensors") for name in hashes),
            "adapter weights missing")
    config = read(adapter / "adapter_config.json")
    require(config["r"] == 8 and config["lora_alpha"] == 16 and config["lora_dropout"] == .05,
            "actual saved adapter configuration differs")
    return manifest, hashes


def execute(material, panel_path, out, arm, seed, device):
    require(supervisor.selected_device() == device, "Main's continuous device reservation required")
    material, panel_path, out = Path(material).resolve(strict=True), Path(panel_path).resolve(strict=True), Path(out).absolute()
    report, panel = inspect_preparation(material, panel_path)
    command = selected_command(material, report, arm, seed)
    adapter = Path(command["output"])
    require(not out.exists() and out == out.resolve(), "fresh canonical recipient log directory required")
    protected = [material, Path(report["recipient_root"]), SOURCE, Path(report["model_path"])]
    require(not any(material_writer.writer._overlap(out, path) for path in protected), "logs overlap inputs/weights")
    out.mkdir(parents=True, exist_ok=False)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    write_new(out / "STARTED.json", dict(started_utc=started, device=device, arm=arm, seed=seed,
        material_sha256=digest(material / "artifact_hashes.json"), panel_sha256=PANEL_SHA256,
        script_sha256=digest(Path(__file__)), worker_caps=dict(fit=600, pair=1800, condition=750),
        unique_events=1, explicit_replays=32, clean_lineage=False, token_matched=False))
    try:
        os.environ["V6_MODEL"] = report["model_path"]
        supervisor.run_worker(command["argv"], log_path=out / "fit.log", timeout=600, device=device)
        manifest, hashes = verify_fit(adapter, command, read(material / arm / "tokenizer_preflight.json"))
        probes = out / "probes"
        probes.mkdir()
        spec = dict(panel["prospective_probe"], model_path=report["model_path"], adapter_path=str(adapter),
            expected_model_hashes=report["expected_model_files"], expected_adapter_hashes=hashes,
            families_path=str(SOURCE / "organism_v6/reasoning_gym_families.json"),
            families_sha256=panel["families_sha256"], probe_root=str(probes), output_dir=str(probes / "pair"),
            training_life_roots=[str(material), report["recipient_root"]], lineage_roots=[report["recipient_root"]],
            episode_ids=panel["episode_ids"], worker_timeout_seconds=750, order=["off", "on"],
            panel_role="development_validation", selection_used_episode_ids=[material_writer.EPISODE])
        write_new(out / "probe_spec.json", spec)
        spec_hash = digest(out / "probe_spec.json")
        supervisor.read_spec(out / "probe_spec.json", spec_hash)
        supervisor.run_worker([sys.executable, "-B", "-m", "organism_v6.run_reasoning_neutral",
            "--spec", str(out / "probe_spec.json"), "--spec-sha256", spec_hash, "--allow-gpu"],
            log_path=out / "pair.log", timeout=1800, device=device)
        done = read(probes / "pair" / "PAIR_DONE.json")
        require(not (probes / "pair" / "PAIR_FAILED.json").exists()
                and done["spec_sha256"] == spec_hash, "neutral pair failed or changed spec")
        require(validate_pair(probes / "pair", spec_hash, done["workers"], done["source_snapshot"])
                == done["receipt_sha256"], "neutral pair receipt mismatch")
        inspect_preparation(material, panel_path)
        write_new(out / "COMPLETED.json", dict(status="COMPLETED_NOT_A_LEARNING_CLAIM", arm=arm, seed=seed,
            finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), adapter_sha256=hashes,
            manifest_sha256=digest(adapter / "train_manifest.json"), steps=manifest["steps"],
            clean_lineage=False, parenting_advantage=False, unique_events=1))
    except BaseException as error:
        write_new(out / "FAILED.json", dict(error_type=type(error).__name__, error=str(error), preserve_attempt=True))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--material", required=True)
    parser.add_argument("--panel", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--arm", required=True, choices=material_writer.ARMS)
    parser.add_argument("--seed", required=True, type=int, choices=material_writer.SEEDS)
    parser.add_argument("--device", required=True)
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args(argv)
    require(args.allow_gpu, "explicit allow-gpu and Main's separate resource precheck required")
    execute(args.material, args.panel, args.out, args.arm, args.seed, args.device)


if __name__ == "__main__":
    main()

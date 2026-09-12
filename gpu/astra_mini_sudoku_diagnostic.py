"""Bounded external-oracle writer diagnostic; never a clean child lineage."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE))
from organism_v6 import run_reasoning_neutral as supervisor
from organism_v6.reasoning_neutral_probe import file_hashes


def write_new(path, value):
    with path.open("x") as target:
        json.dump(value, target, sort_keys=True, indent=2, allow_nan=False)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_material(root):
    material = root / "material"
    manifest = json.loads((material / "manifest.json").read_text())
    if manifest["status"] != "PREPARED":
        raise ValueError("material not prepared")
    for name, expected in manifest["files"].items():
        if digest(material / name) != expected:
            raise ValueError("changed material: " + name)
    validation = json.loads((material / "validation.json").read_text())
    if validation["boundary"]["validation_backend"] != "NATIVE_PACKAGE_CPU":
        raise ValueError("native CPU validation required")
    for name, expected in json.loads((material / "source_hashes.json").read_text()).items():
        if digest(Path(name)) != expected:
            raise ValueError("changed preparation source: " + name)
    return material


def check_free(device):
    display = subprocess.run(["nvidia-smi", "-i", device, "-q", "-x"],
                             capture_output=True, text=True, timeout=30, check=True)
    devices = ET.fromstring(display.stdout).findall("gpu")
    processes = devices[0].find("processes") if len(devices) == 1 else None
    if processes is None or list(processes) or (processes.text or "").strip():
        raise ValueError("GPU has processes or cannot be inspected")
    uuid = devices[0].findtext("uuid")
    ancestors = set()
    ancestor = os.getppid()
    while ancestor > 1 and ancestor not in ancestors:
        ancestors.add(ancestor)
        ancestor = int((Path("/proc") / str(ancestor) / "stat").read_text().rsplit(")", 1)[1].split()[1])
    reconciled = []
    for process in Path("/proc").glob("[0-9]*"):
        try:
            if process.stat().st_uid != os.getuid():
                continue
            entries = (process / "environ").read_bytes().split(b"\x00")
        except FileNotFoundError:
            continue
        except PermissionError:
            try:
                command = (process / "cmdline").read_bytes().replace(b"\x00", b" ").strip()
            except FileNotFoundError:
                continue
            system_service = (process.name, command) in (
                ("3245", b"/usr/lib/systemd/systemd --user"), ("3246", b"(sd-pam)"))
            ssh_ancestor = int(process.name) in ancestors and command == b"sshd: local-rohing@notty"
            if not (system_service or ssh_ancestor):
                raise RuntimeError("unreconciled own process " + process.name)
            reconciled.append(dict(pid=process.name, command=command.decode()))
            continue
        for entry in entries:
            if entry.startswith(b"CUDA_VISIBLE_DEVICES=") and set(
                    entry.split(b"=", 1)[1].decode().split(",")) & {device, uuid, "all"}:
                raise RuntimeError("GPU reservation " + process.name)
    for state in ("pending", "running"):
        if list((Path.home() / "queue" / state).glob("*.job")):
            raise RuntimeError("queue requires reconciliation")
    return dict(gpu_uuid=uuid, reconciled_system_services=reconciled), display.stdout


def execute(root, arm, device, seed=0):
    material = verify_material(root)
    logs = root / "logs" / arm
    training = root / "training"
    adapter = training / (arm + "_seed" + str(seed))
    validation = json.loads((material / "validation.json").read_text())
    if validation.get("training_seed", 0) != seed:
        raise ValueError("material training seed mismatch")
    command_file = json.loads((material / "trainer_commands.json").read_text())
    if command_file.get("training_seed", 0) != seed:
        raise ValueError("trainer command seed mismatch")
    commands = command_file["commands"]
    command = commands[arm]
    if command["cwd"] != str(SOURCE) or adapter.exists():
        raise ValueError("wrong source or preexisting adapter")
    argv = command["argv"]
    if (Path(argv[0]).absolute() != Path(sys.executable).absolute()
            or argv[argv.index("--out") + 1] != str(adapter)
            or argv[argv.index("--seed") + 1] != str(seed)
            or command["seed"] != seed):
        raise ValueError("trainer interpreter, seed, or destination mismatch")
    supervisor.run_worker(command["argv"], log_path=logs / "train.log", timeout=900, device=device)
    manifest = json.loads((adapter / "train_manifest.json").read_text())
    expected = dict(rank=8, alpha=0, dropout=0.05, lr=1e-4, epochs=3, seed=seed,
                    batch_size=1, grad_accum=1, chat_template=False, pack=False,
                    max_len=4096, add_eos=True, optimizer="adamw", grad_checkpoint=True)
    if any(manifest["config"][key] != value for key, value in expected.items()):
        raise ValueError("trainer configuration mismatch")
    if not (adapter / "DONE").is_file() or manifest["steps"] != 96 or manifest["nonfinite_batches"] != 0:
        raise ValueError("incomplete or nonfinite fit")
    if manifest["corpus"]["sha256"] != digest(material / (arm + ".json")):
        raise ValueError("trainer corpus mismatch")
    if manifest["corpus"]["n_items"] != 32 or any(manifest["truncation"][key] != 0 for key in (
            "items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")):
        raise ValueError("trainer material loss")
    tokens = validation[arm + "_tokens"]
    if (manifest["tokens"]["target"] != sum(row["target_tokens"] for row in tokens)
            or manifest["train_tokens_seen"] != 3 * sum(row["input_tokens"] for row in tokens)
            or not math.isfinite(manifest["final_loss"])):
        raise ValueError("trainer token budget or finite loss mismatch")
    pins = json.loads((material / "local_pins.json").read_text())
    ids = json.loads((material / "ids.json").read_text())
    families = SOURCE / "organism_v6/reasoning_gym_families.json"
    probes = root / "probes"
    spec = dict(model_path=pins["model_path"], adapter_path=str(adapter),
                expected_model_hashes=pins["files"], expected_adapter_hashes=file_hashes(adapter),
                families_path=str(families), families_sha256=digest(families),
                probe_root=str(probes), output_dir=str(probes / arm),
                training_life_roots=[str(training), str(material)], lineage_roots=[str(training)],
                episode_ids=ids["canary"], gen_seed=0, seed_salt=15420, budget_ticks=1,
                wake_max_tokens=400, scratchpad_max_tokens=100, total_token_budget=38400,
                max_episodes=16, max_model_len=4096, worker_timeout_seconds=900,
                order=["off", "on"], panel_role="development_validation",
                selection_used_episode_ids=ids["declared_prior_cpu_examined_ids"])
    spec_path = logs / "probe_spec.json"
    write_new(spec_path, spec)
    supervisor.read_spec(spec_path, digest(spec_path))
    supervisor.run_worker([sys.executable, "-B", "-m", "organism_v6.run_reasoning_neutral",
                           "--spec", str(spec_path), "--spec-sha256", digest(spec_path), "--allow-gpu"],
                          log_path=logs / "pair.log", timeout=2100, device=device)
    verify_material(root)
    write_new(logs / "result.json", dict(status="COMPLETED", arm=arm, training_seed=seed,
              finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              clean_lineage=False, parenting=False, model_origin="UNRESOLVED_LOCAL_HASHES_ONLY"))


def execute_selected(root, selection, device, seed):
    arms = ("useful", "corrupt") if selection == "paired" else (selection,)
    for arm in arms:
        execute(root, arm, device, seed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--arm", required=True, choices=("useful", "corrupt", "paired"))
    parser.add_argument("--seed", type=int, default=0, choices=(0, 1, 2))
    parser.add_argument("--device", required=True, choices=("1", "3"))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve(strict=True)
    logs = root / "logs" / args.arm
    if args.execute:
        try:
            execute_selected(root, args.arm, args.device, args.seed)
            if args.arm == "paired":
                write_new(logs / "result.json", dict(status="BOTH_ARMS_COMPLETED", training_seed=args.seed,
                          finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        except BaseException as error:
            write_new(logs / "failure.json", dict(error=repr(error),
                      failed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
            raise
        return
    material = verify_material(root)
    validation = json.loads((material / "validation.json").read_text())
    if validation.get("training_seed", 0) != args.seed:
        raise ValueError("material training seed mismatch")
    metadata, xml = check_free(args.device)
    logs.mkdir(parents=True, exist_ok=False)
    if args.arm == "paired":
        for arm in ("useful", "corrupt"):
            (root / "logs" / arm).mkdir(exist_ok=False)
    (root / "training").mkdir(exist_ok=True)
    (root / "probes").mkdir(exist_ok=True)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=args.device, PYTHONPATH=str(SOURCE),
                       PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
                       HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                       VLLM_WORKER_MULTIPROC_METHOD="spawn")
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "--root", str(root),
               "--arm", args.arm, "--device", args.device, "--seed", str(args.seed), "--execute"]
    with (logs / "controller.log").open("xb") as output:
        process = subprocess.Popen(command, cwd=SOURCE, env=environment, stdin=subprocess.DEVNULL,
                                   stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(metadata, status="LAUNCHED_NOT_COMPLETED", node=3, device=args.device,
                   pid=process.pid, command=command, source=str(SOURCE), script_sha256=digest(Path(__file__)),
                   started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   training_cap_seconds=900, paired_probe_cap_seconds=2100,
                   training_seed=args.seed, selection=args.arm,
                   same_device_sequential_arms=args.arm == "paired")
    write_new(logs / "launch_receipt.json", receipt)
    with (logs / "gpu_before.xml").open("x") as output:
        output.write(xml)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()

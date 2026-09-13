"""Main-owned launch wrapper for a separately prepared full-dose comparison."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def launch(options):
    source, root, stdout = (Path(value).resolve() for value in
                            (options.source, options.root, options.stdout))
    executor = source / "gpu/astra_pairwise_q0_fulldose.py"
    if not options.allow_gpu:
        raise ValueError("explicit Main launch opt-in required")
    if digest(executor) != options.executor_sha256 or digest(root / "manifest.json") != options.manifest_sha256:
        raise ValueError("source or prepared manifest changed")
    if stdout.exists() or stdout.is_symlink() or stdout == root or root in stdout.parents:
        raise ValueError("fresh external stdout required")
    if any((root / name).exists() for name in ("STARTED.json", "SEAL.json", "FAILED.json")):
        raise ValueError("started or failed root cannot be relaunched")
    manifest = json.loads((root / "manifest.json").read_bytes())
    prepared = json.loads((root / "PREPARED.json").read_bytes())
    if manifest["version"] != options.version or not manifest["ready"]:
        raise ValueError("wrong version or unready manifest")
    if prepared["manifest_sha256"] != options.manifest_sha256:
        raise ValueError("prepared manifest seal differs")
    config = manifest["config"]
    if config["lease_cutoff_unix"] > config["lease_end_unix"] - 21600:
        raise ValueError("six-hour lease margin missing")
    if time.time() + 10800 + 180 >= config["lease_cutoff_unix"]:
        raise ValueError("full-dose and collection window unavailable")
    if digest(options.precheck) != options.precheck_sha256:
        raise ValueError("allocation checker changed")
    subprocess.run([sys.executable, "-B", options.precheck, "--gpu-index", str(options.gpu_index),
                    "--gpu-uuid", config["gpu_uuid"]], check=True,
                   env=dict(os.environ, CUDA_VISIBLE_DEVICES=""))
    command = [os.path.abspath(sys.executable), "-B", str(executor), "execute", "--out", str(root), "--allow-gpu"]
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=config["gpu_uuid"], CUBLAS_WORKSPACE_CONFIG=":4096:8",
                       PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1",
                       HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
                       PYTHONHASHSEED="0", TOKENIZERS_PARALLELISM="false")
    with stdout.open("xb") as stream:
        process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
                                   stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
    fields = Path(f"/proc/{process.pid}/stat").read_text().rsplit(")", 1)[1].split()
    return dict(status="CONTROLLER_STARTED_NOT_SCIENTIFIC_RESULT", controller_pid=process.pid,
                pgid=os.getpgid(process.pid), start_ticks=int(fields[19]), command=command,
                stdout=str(stdout), source=str(source), root=str(root), started_wall=time.time(),
                executor_sha256=options.executor_sha256, manifest_sha256=options.manifest_sha256,
                gpu_uuid=config["gpu_uuid"], runtime_cap_seconds=10800, launcher_sha256=digest(__file__))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "root", "stdout", "executor-sha256", "manifest-sha256", "version",
                 "precheck", "precheck-sha256"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--gpu-index", type=int, required=True)
    parser.add_argument("--allow-gpu", action="store_true")
    print(json.dumps(launch(parser.parse_args()), sort_keys=True), flush=True)

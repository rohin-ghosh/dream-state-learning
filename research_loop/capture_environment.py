from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import subprocess
import sys
from pathlib import Path

from .io import atomic_write_json, utc_now


PACKAGES = (
    "torch", "transformers", "vllm", "peft", "accelerate", "numpy",
    "ninja", "huggingface-hub",
)


def cuda_runtime_metadata() -> dict[str, object]:
    metadata: dict[str, object] = {
        "torch_cuda_build": None,
        "cudnn_runtime": None,
        "cuda_available": None,
        "nvcc": None,
    }
    try:
        import torch
        metadata["torch_cuda_build"] = torch.version.cuda
        metadata["cudnn_runtime"] = torch.backends.cudnn.version()
        metadata["cuda_available"] = torch.cuda.is_available()
    except BaseException as exc:
        metadata["torch_error"] = f"{type(exc).__name__}: {exc}"
    try:
        nvcc = subprocess.run(
            ["nvcc", "--version"], text=True, capture_output=True,
            timeout=30, check=False,
        )
        metadata["nvcc"] = {
            "returncode": nvcc.returncode,
            "stdout": nvcc.stdout.strip(),
            "stderr": nvcc.stderr.strip(),
        }
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        metadata["nvcc"] = f"unavailable: {type(exc).__name__}"
    return metadata


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args(argv)
    packages = {}
    for package in PACKAGES:
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = None
    try:
        gpu = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,uuid,driver_version,memory.total",
             "--format=csv,noheader"],
            text=True, capture_output=True, timeout=30, check=False,
        )
        gpu_text = gpu.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        gpu_text = f"unavailable: {type(exc).__name__}"
    result = {
        "captured_at": utc_now(),
        "python": sys.version,
        "platform": platform.platform(),
        "packages": packages,
        "gpu": gpu_text,
        "cuda": cuda_runtime_metadata(),
        "model": args.model,
        "revision": args.revision,
    }
    atomic_write_json(args.out, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Cheap fail-closed runtime compatibility checks before model loading."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path

from alchemy.backend import VLLMBackend
from research_loop.io import atomic_write_json, utc_now


def tokenizer_contract(model: str, revision: str) -> dict[str, object]:
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model, revision=revision)
    backend = object.__new__(VLLMBackend)
    backend.tok = tokenizer
    ids = backend._chat_ids("runtime compatibility probe")
    if not ids or any(not isinstance(token_id, int) for token_id in ids):
        raise RuntimeError("tokenizer contract did not return integer IDs")
    return {
        "tokenizer_class": type(tokenizer).__name__,
        "token_count": len(ids),
        "min_token_id": min(ids),
        "max_token_id": max(ids),
        "return_type": type(ids).__name__,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args(argv)

    ninja_path = shutil.which("ninja")
    if ninja_path is None:
        raise RuntimeError("ninja is absent from PATH")
    ninja = subprocess.run(
        [ninja_path, "--version"], text=True, capture_output=True,
        timeout=30, check=False,
    )
    if ninja.returncode != 0:
        raise RuntimeError(f"ninja preflight failed: {ninja.stderr.strip()}")
    result = {
        "captured_at": utc_now(),
        "python": sys.version,
        "model": args.model,
        "revision": args.revision,
        "transformers": importlib.metadata.version("transformers"),
        "vllm": importlib.metadata.version("vllm"),
        "ninja": {"path": ninja_path, "version": ninja.stdout.strip()},
        "tokenizer_contract": tokenizer_contract(args.model, args.revision),
    }
    atomic_write_json(args.out, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

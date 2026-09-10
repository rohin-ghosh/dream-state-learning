"""Bind a structured fresh-agent decision to the exact reviewed bytes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .io import atomic_write_json, fingerprint, load_json, sha256_file, utc_now


def create_binding(
    root: Path,
    output: Path,
    *,
    run_id: str,
    node_id: str,
    review_result: Path,
    prompt_file: Path,
    schema_file: Path,
    context_files: list[Path],
    route_field: str,
) -> dict[str, Any]:
    root = root.resolve()
    reviewed = [prompt_file, schema_file, *context_files]
    value = load_json(review_result)
    review_result = review_result.resolve()
    try:
        review_result_key = str(review_result.relative_to(root))
    except ValueError:
        review_result_key = str(review_result)
    binding = {
        "schema_version": 1,
        "created_at": utc_now(),
        "run_id": run_id,
        "node_id": node_id,
        "route_field": route_field,
        "verdict": value.get(route_field),
        "review_result_path": review_result_key,
        "review_result_sha256": sha256_file(review_result),
        "review_result": value,
        "reviewed_files": fingerprint(reviewed, root),
    }
    atomic_write_json(output, binding)
    return binding


def verify_binding(
    root: Path,
    binding_path: Path,
    required_verdict: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    binding = load_json(binding_path)
    expected = binding["reviewed_files"]
    actual = fingerprint([Path(path) for path in expected], root)
    changed = {
        path: {"expected": digest, "actual": actual.get(path)}
        for path, digest in expected.items()
        if actual.get(path) != digest
    }
    if changed:
        raise RuntimeError(f"review binding changed: {changed}")
    if required_verdict is not None and binding.get("verdict") != required_verdict:
        raise RuntimeError(
            f"review verdict is {binding.get('verdict')!r}, expected "
            f"{required_verdict!r}"
        )
    return {
        "verified_at": utc_now(),
        "binding_sha256": sha256_file(binding_path),
        "verdict": binding.get("verdict"),
        "reviewed_files": actual,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--required-verdict")
    args = parser.parse_args(argv)
    try:
        result = verify_binding(
            args.root, args.binding, required_verdict=args.required_verdict
        )
    except BaseException as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}))
        return 1
    print(json.dumps({"ok": True, **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

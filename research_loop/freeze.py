from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .io import atomic_write_json, fingerprint, load_json, utc_now


def _safe_files(values: list[str]) -> list[Path]:
    files = [Path(value) for value in values]
    if any(path.is_absolute() or ".." in path.parts for path in files):
        raise ValueError("freeze paths must be repository-relative")
    return files


def create(root: Path, output: Path, files: list[str]) -> dict[str, object]:
    root = root.resolve()
    lock = {
        "schema_version": 1,
        "created_at": utc_now(),
        "root": str(root),
        "files": fingerprint(_safe_files(files), root),
    }
    atomic_write_json(output, lock)
    return lock


def verify(root: Path, lock_path: Path) -> dict[str, object]:
    root = root.resolve()
    lock = load_json(lock_path)
    expected = lock["files"]
    actual = fingerprint(_safe_files(list(expected)), root)
    changed = {
        path: {"expected": digest, "actual": actual.get(path)}
        for path, digest in expected.items()
        if actual.get(path) != digest
    }
    if changed:
        raise RuntimeError(f"frozen inputs changed: {changed}")
    return {"verified_at": utc_now(), "files": actual}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("create")
    make.add_argument("--root", type=Path, required=True)
    make.add_argument("--out", type=Path, required=True)
    make.add_argument("--file", action="append", required=True)
    check = sub.add_parser("verify")
    check.add_argument("--root", type=Path, required=True)
    check.add_argument("--lock", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            result = create(args.root, args.out, args.file)
        else:
            result = verify(args.root, args.lock)
    except BaseException as exc:
        print(f"freeze error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

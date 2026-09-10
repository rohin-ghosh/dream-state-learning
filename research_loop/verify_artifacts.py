from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .io import load_json, sha256_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    done_path = args.job_dir / "done.json"
    try:
        done = load_json(done_path)
        mismatches = {}
        groups = {
            "artifacts": done["artifact_fingerprints"],
            "inputs": done["input_snapshot_fingerprints"],
        }
        for group, fingerprints in groups.items():
            for relative, expected in fingerprints.items():
                path = args.job_dir / relative
                actual = sha256_file(path) if path.is_file() else None
                if actual != expected:
                    mismatches[f"{group}:{relative}"] = {
                        "expected": expected, "actual": actual
                    }
        if mismatches:
            raise RuntimeError(f"artifact hash mismatch: {mismatches}")
    except BaseException as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}))
        return 1
    print(json.dumps({
        "ok": True,
        "artifacts": len(done["artifact_fingerprints"]),
        "frozen_inputs": len(done["input_snapshot_fingerprints"]),
        "approval_sha256": done["approval_sha256"],
        "approved_lock_sha256": done["approved_lock_sha256"],
        "remote_spec_sha256": done["remote_spec_sha256"],
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())

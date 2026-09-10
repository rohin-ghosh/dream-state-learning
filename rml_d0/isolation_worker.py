"""Disposable restricted evaluator used only by the Stage-A isolation probe."""

from __future__ import annotations

import builtins
import hashlib
import json
import sys


def main() -> int:
    request = json.loads(sys.stdin.read())
    snapshot = request["snapshot"]
    original = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    real_import = builtins.__import__
    real_open = builtins.open
    denied_imports = {
        "network": ("socket", "urllib", "http", "requests"),
        "model": ("torch", "transformers", "openai"),
        "gpu": ("cupy", "cuda", "nvidia"),
        "generator": ("rml_d0.targets", "rml_d0.world"),
        "scorer": ("rml_d0.probes",),
    }

    def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
        if any(
            name == prefix or name.startswith(prefix + ".")
            for prefixes in denied_imports.values()
            for prefix in prefixes
        ):
            raise PermissionError(f"denied import: {name}")
        return real_import(name, globals, locals, fromlist, level)

    def read_only_open(path, mode="r", *args, **kwargs):
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            raise PermissionError("source descriptor is write denied")
        return real_open(path, mode, *args, **kwargs)

    builtins.__import__ = restricted_import
    builtins.open = read_only_open
    denied: dict[str, bool] = {}
    for capability, prefixes in denied_imports.items():
        try:
            restricted_import(prefixes[0])
        except PermissionError:
            denied[capability] = True
        else:
            denied[capability] = False
    try:
        read_only_open(request["source_descriptor_path"], "a")
    except PermissionError:
        denied["source_write"] = True
    else:
        denied["source_write"] = False
    # A private disposable cache is permitted and never returned as source.
    local_cache = {
        "cache_canary": f"CACHE_LIFE_{request['life_id']}",
        "fd_canary": f"FD_LIFE_{request['life_id']}",
        "process_canary": f"PROCESS_LIFE_{request['life_id']}",
        "temp_canary": request["temp_canary"],
    }
    after = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    result = {
        "audit_only_hash": hashlib.sha256(
            json.dumps(local_cache, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "denied": denied,
        "snapshot_sha256": hashlib.sha256(after).hexdigest(),
        "snapshot_unchanged": original == after,
    }
    sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""CPU-only bounded source warmup and fresh host proof; never dispatches or activates."""

import argparse
import json
from pathlib import Path
import time

from epoch_cache import cache_for, SourceEpochPending
from host import LocalHost
import probe_runtime as runtime


def inspect(policy, max_seconds=60):
    runtime.require(0 < max_seconds <= 600, "bounded_cpu_preflight_required")
    host = LocalHost(policy)
    started = time.monotonic()
    calls = 0
    ready = False
    failure = None
    while time.monotonic() - started < max_seconds:
        calls += 1
        try:
            host.source_guard()
            ready = True
            break
        except SourceEpochPending:
            continue
        except (ValueError, OSError, KeyError) as error:
            failure = type(error).__name__ + ":" + str(error)
            break
    cold_elapsed = time.monotonic() - started
    cold_stats = {source: dict(cache_for(policy, source).last) for source in policy["supported_journals"]}
    warm = None
    if ready:
        began = time.monotonic()
        try:
            host.source_guard()
            warm = dict(elapsed_seconds=time.monotonic() - began,
                sources={source: dict(cache_for(policy, source).last) for source in policy["supported_journals"]})
        except SourceEpochPending:
            ready = False
        except (ValueError, OSError, KeyError) as error:
            ready = False
            failure = type(error).__name__ + ":" + str(error)
    return dict(status="SOURCE_EPOCHS_VERIFIED" if ready else "SOURCE_EPOCHS_BLOCKED" if failure else "SOURCE_EPOCHS_PENDING",
        observed_unix=time.time(), elapsed_seconds=time.monotonic() - started,
        cold_elapsed_seconds=cold_elapsed, bounded_calls=calls, sources=cold_stats,
        source_heads=host.source_cursors, warm=warm, failure=failure,
        current_gpu_occupancy_checked=False, capsule_runtime_binding_checked=False,
        activation_performed=False, gpu_execution_performed=False, signals_sent=False,
        cache_persistence="PROCESS_ONLY_COLD_RESTART_REVALIDATES_NO_DISK_TRUST",
        other_admission_checks="UNCHANGED_AND_STILL_REQUIRED_BEFORE_INTENT")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--max-seconds", type=float, default=60)
    args = parser.parse_args()
    result = inspect(runtime.read(args.policy), args.max_seconds)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if result["status"] == "SOURCE_EPOCHS_VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())

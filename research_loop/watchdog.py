"""Persistent outer runner for a resumable research workflow.

The watchdog is deliberately boring: it never edits experiments or decides
science.  It keeps the deterministic supervisor alive across provider errors,
writes a heartbeat while long nodes run, and waits at explicit human gates.
"""

from __future__ import annotations

import argparse
import os
import signal
import sys
import threading
import time
import traceback
from pathlib import Path

from .io import atomic_write_json, load_json, utc_now
from .supervisor import Lock, WorkflowError, initialize, load_runtime, run


class Heartbeat:
    def __init__(self, path: Path, base: dict, interval_sec: float):
        self.path = path
        self.base = base
        self.interval_sec = interval_sec
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._loop, daemon=True)

    def _write(self) -> None:
        atomic_write_json(self.path, {**self.base, "heartbeat_at": utc_now()})

    def _loop(self) -> None:
        while not self.stop_event.wait(self.interval_sec):
            self._write()

    def __enter__(self):
        self._write()
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop_event.set()
        self.thread.join(timeout=5)
        self._write()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow", type=Path)
    parser.add_argument("--interval-sec", type=float, default=10.0)
    parser.add_argument("--heartbeat-sec", type=float, default=30.0)
    parser.add_argument("--max-consecutive-errors", type=int, default=20)
    args = parser.parse_args(argv)
    runtime = load_runtime(args.workflow)
    heartbeat_path = runtime.state_dir / f"{runtime.workflow['name']}.watchdog.json"
    watchdog_lock = runtime.state_dir / f"{runtime.workflow['name']}.watchdog.lock"
    stopping = threading.Event()

    def stop_handler(_signum, _frame):
        stopping.set()

    signal.signal(signal.SIGTERM, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)
    consecutive_errors = 0
    with Lock(watchdog_lock):
        while not stopping.is_set():
            try:
                state = initialize(runtime)
            except WorkflowError as exc:
                atomic_write_json(heartbeat_path, {
                    "pid": os.getpid(), "status": "workflow_changed",
                    "error": str(exc), "heartbeat_at": utc_now(),
                })
                return 2
            current = state["current"]
            node = runtime.workflow["nodes"][current]
            if state["status"] in {"complete", "failed"}:
                atomic_write_json(heartbeat_path, {
                    "pid": os.getpid(), "run_id": state["run_id"],
                    "status": state["status"], "node": current,
                    "heartbeat_at": utc_now(),
                })
                return 0 if state["status"] == "complete" else 1
            if (node["kind"] == "human"
                    and current not in state.get("approvals", [])):
                atomic_write_json(heartbeat_path, {
                    "pid": os.getpid(), "run_id": state["run_id"],
                    "status": "waiting_human", "node": current,
                    "reason": node["instructions"],
                    "heartbeat_at": utc_now(),
                })
                stopping.wait(args.interval_sec)
                continue
            base = {
                "pid": os.getpid(), "run_id": state["run_id"],
                "status": "node_running", "node": current,
                "started_at": utc_now(),
            }
            try:
                with Heartbeat(heartbeat_path, base, args.heartbeat_sec):
                    state = run(runtime, once=True)
            except BaseException as exc:
                consecutive_errors += 1
                atomic_write_json(heartbeat_path, {
                    **base, "status": "retrying_error",
                    "consecutive_errors": consecutive_errors,
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                    "heartbeat_at": utc_now(),
                })
                if consecutive_errors >= args.max_consecutive_errors:
                    return 3
                stopping.wait(min(args.interval_sec * consecutive_errors, 60))
                continue
            consecutive_errors = 0
            atomic_write_json(heartbeat_path, {
                "pid": os.getpid(), "run_id": state["run_id"],
                "status": state["status"], "node": state["current"],
                "steps": state["steps"], "heartbeat_at": utc_now(),
            })
            stopping.wait(args.interval_sec)
    return 0


if __name__ == "__main__":
    sys.exit(main())

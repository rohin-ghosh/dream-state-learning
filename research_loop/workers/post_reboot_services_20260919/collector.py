"""Non-material recovery: read-only, epoch-separated, lease-bounded collection."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LEGACY = HERE.parent / "rohin233_recovery_20260918"
OWNER = HERE.parent / "rohin233_ovx4_recovery_20260918"
LOCK = LEGACY / "CAPTION_HOURLY.lock"
MAX_UNTIL = 1790791170.0
BACKFILL = ("2026-09-18T23:00:00+00:00", "2026-09-19T00:00:00+00:00")
sys.path.insert(0, str(LEGACY))
from caption_hourly_service import markdown, project


def utc(timestamp=None):
    return datetime.fromtimestamp(time.time() if timestamp is None else timestamp,
                                  timezone.utc).isoformat()


def encoded(document):
    return (json.dumps(document, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def save(path, document, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = encoded(document)
    if exclusive:
        temporary = path.with_name(path.name + "." + str(os.getpid()) + ".next")
        with temporary.open("xb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        try:
            os.link(temporary, path)
        finally:
            temporary.unlink()
    else:
        temporary = path.with_name(path.name + "." + str(os.getpid()) + ".next")
        with temporary.open("wb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        temporary.replace(path)


def identity():
    fields = Path("/proc/self/stat").read_text().rsplit(") ", 1)[1].split()
    return dict(pid=os.getpid(), start_ticks=fields[19],
                boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
                hostname=os.uname().nodename)


def remote_reader():
    source = (LEGACY / "judge_epoch_report.py").read_text()
    original = "    cut = time.time()\n"
    if source.count(original) != 1:
        raise ValueError("reader_cut_anchor_changed_requires_review")
    return source.replace(original,
        "    cut = min(time.time(), float(specification['cut_unix']))\n")


def specifications(cut):
    supports = json.loads((OWNER / "SUPPORT_COMPONENT_TABLE.json").read_text())
    result = []
    for role, component, wrapper in (("SHARED2", "shared_node3_scorer", "ovx4"),
                                    ("SHARED3", "shared_node2_scorer", "ovx4"),
                                    ("BASE", "base_scorer", "ovx4"),
                                    ("P3", "P3_scorer", "a40r")):
        adopted = json.loads((OWNER / ("JUDGE_" + role + "_ADOPTED.json")).read_text())["actual_loaded"]
        process = next(row for row in supports["rows"] if row["name"] == component)
        if process["pid"] != adopted["pid"]:
            raise ValueError("support_identity_matches_loaded_judge")
        result.append(dict(role=role, pid=adopted["pid"], start_ticks=process["start_ticks"],
            command_sha256=process["command_sha256"], cutoff_unix=adopted["deadline_unix"],
            players=[dict(player=row["player"], epoch_sha256=row["epoch_sha256"])
                     for row in adopted["sessions"]], wrapper=wrapper,
            cut_unix=math.nextafter(cut, -math.inf)))
    return result


def fetch(specification, reader):
    remaining = specification["cutoff_unix"] - time.time() - 5
    if remaining <= 0:
        return dict(role=specification["role"], status="SOURCE_LEASE_BOUND_REACHED_NOT_QUERIED")
    try:
        response = subprocess.run(
            ["bash", str(REPO / ("gpu/" + specification["wrapper"] + "_ssh.sh")),
             "python3 -B -c " + shlex.quote(reader)],
            input=json.dumps(specification), capture_output=True, text=True,
            timeout=min(40, remaining))
        if response.returncode:
            return dict(role=specification["role"], status="READ_FAILED_NOT_ZERO_COUNTS",
                returncode=response.returncode,
                stderr_sha256=hashlib.sha256(response.stderr.encode()).hexdigest())
        result = json.loads(response.stdout)
        expected = {(row["player"], row["epoch_sha256"]) for row in specification["players"]}
        actual = {(row["player"], row["epoch_sha256"]) for row in result["players"]}
        if result["role"] != specification["role"] or expected != actual:
            raise ValueError("exact_expected_players_and_epochs_required")
        return result
    except (subprocess.TimeoutExpired, ValueError, KeyError, OSError) as error:
        return dict(role=specification["role"], status="READ_FAILED_NOT_ZERO_COUNTS",
                    error_type=type(error).__name__)


def collect(cut, backfill=False):
    reader = remote_reader()
    with ThreadPoolExecutor(max_workers=4) as executor:
        roles = list(executor.map(lambda specification: fetch(specification, reader), specifications(cut)))
    observed = time.time()
    stamp = datetime.fromtimestamp(cut, timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    attempt = HERE / "receipts" / ("AUDIT_" + stamp + "_" + str(time.time_ns()) + ".json")
    audit = dict(schema="POST_REBOOT_ADOPTED_EPOCH_AUDIT_V1", observed_utc=utc(cut),
        collected_utc=utc(observed), requested_cut_unix=cut, roles=roles,
        reader_sha256=hashlib.sha256(reader.encode()).hexdigest(),
        legacy_reader_sha256=hashlib.sha256((LEGACY / "judge_epoch_report.py").read_bytes()).hexdigest(),
        backfill=backfill, old_and_new_epochs_combined=False, raw_text_exported=False,
        historical_completion_time_reconstructed=False,
        cut_semantics="ACT origins and admissions strictly before cut; immutable score outcomes observed at recovery, not certified completed by cut.",
        native_signals=[], GPU_work=0)
    save(attempt, audit, exclusive=True)
    source = dict(path=str(attempt.relative_to(REPO)), sha256=hashlib.sha256(attempt.read_bytes()).hexdigest())
    document = project(audit, source)
    document.update(backfill=backfill, collected_utc=utc(observed),
                    historical_completion_time_reconstructed=False, cut_semantics=audit["cut_semantics"])
    successful = not document["errors"]
    report = HERE / "cuts" / (stamp + ".json") if successful else attempt.with_name(attempt.stem + "_PARTIAL.json")
    save(report, document, exclusive=True)
    with report.with_suffix(".md").open("x") as output:
        output.write(markdown(document) + "\nRecovery caveat: " + audit["cut_semantics"] + "\n")
    receipt = dict(observed_utc=utc(), cut_utc=utc(cut), backfill=backfill,
        success=successful, report=str(report.relative_to(REPO)), source_receipt=source,
        players=len(document["players"]), errors=document["errors"],
        epoch_separated=True, git_commit=None, publication_attempted=False, **identity())
    save(HERE / "COLLECTOR_LAST_ATTEMPT.json", receipt)
    if successful:
        save(HERE / "COLLECTOR_LAST_SUCCESS.json", receipt)
    print(json.dumps(receipt), flush=True)
    return successful


def pending_backfill(now=None):
    result = []
    first = int(datetime.fromisoformat(BACKFILL[0]).timestamp())
    last = int(min(time.time() if now is None else now, MAX_UNTIL) // 3600) * 3600
    for timestamp in range(first, last + 1, 3600):
        stamp = datetime.fromtimestamp(timestamp, timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        if not (HERE / "cuts" / (stamp + ".json")).exists():
            result.append(timestamp)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--until-unix", type=float, default=MAX_UNTIL)
    arguments = parser.parse_args()
    if not math.isfinite(arguments.until_unix) or arguments.until_unix > MAX_UNTIL:
        raise ValueError("cannot_extend_existing_collector_lease")
    if time.time() >= arguments.until_unix:
        return 0
    with LOCK.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps(dict(status="SINGLE_COLLECTOR_ALREADY_LOCKED")), flush=True)
            return 75
        started = dict(started_utc=utc(), until_unix=arguments.until_unix,
                       lock=str(LOCK.relative_to(REPO)),
                       collector_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), **identity())
        save(HERE / "receipts" / ("COLLECTOR_STARTED_" + str(time.time_ns()) + ".json"), started, exclusive=True)
        save(HERE / "COLLECTOR_STARTED.json", started)
        next_live = 0.0
        while time.time() < arguments.until_unix:
            retry = False
            historical = pending_backfill()[:4]
            live_cut = time.time() if time.time() >= next_live else None
            live_failed = False
            for cut in historical + ([] if live_cut is None else [live_cut]):
                if time.time() >= arguments.until_unix:
                    break
                try:
                    successful = collect(cut, backfill=cut in historical)
                    retry |= not successful
                    live_failed |= cut == live_cut and not successful
                except Exception as error:
                    retry = True
                    live_failed |= cut == live_cut
                    failure = dict(observed_utc=utc(), cut_utc=utc(cut), error_type=type(error).__name__, success=False)
                    save(HERE / "receipts" / ("COLLECTOR_ERROR_" + str(time.time_ns()) + ".json"), failure, exclusive=True)
                    print(json.dumps(failure), flush=True)
            if live_cut is not None:
                next_live = time.time() + 60 if live_failed else (int(time.time() // 3600) + 1) * 3600
            retry |= bool(pending_backfill())
            next_run = min(next_live, time.time() + 60 if retry else math.inf, arguments.until_unix)
            save(HERE / "COLLECTOR_HEARTBEAT.json", dict(observed_utc=utc(), next_run_unix=next_run, **identity()))
            time.sleep(max(0, next_run - time.time()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

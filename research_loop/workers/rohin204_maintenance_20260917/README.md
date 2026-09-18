# R204 standing maintenance

Authorized scope: this worker directory and dated entries prepended to `research_loop/COORDINATION.md`. No learner, operator, source-bundle, arm-table, GPU, or model mutation. This monitor only routes observations to sole operators; it is never a launch gate. Current owner labels: NODE1 sole operator; Leibniz/node2; Turing/node4; Descartes/node5.

## Implementation and safety

`audit.py` runs one finite read-only pass, or schedules passes every 1,200 seconds start-to-start in a detached local process using the existing `subprocess.Popen(..., start_new_session=True)` pattern in node1's operator helpers (for example `activate_modern.py`). A local flock prevents a second monitor. No cron/systemd or child-process control is installed. The STOP sentinel affects this audit only, with up to 125 seconds to finish an in-flight read and five seconds between idle checks.

The initial nohup-only monitor PID2649363 completed a pass but did not survive its launching terminal command. It was not signaled or treated as a learner failure. The replacement monitor **PID2656637**, UID158984/start ticks180945900, was independently verified after launcher exit with PPID1 and its own session/process-group2656637. It completed the 03:34:01 UTC correcting pass: **30 observed native processes (14 R, 13 S, 3 T), all identities verified, no bounded readout failures**. C2 was then PID3179563, matching LOADED6057 and REQUEST6079/prompt8665. The 1,200-second cadence is scheduled; a second timed interval is not yet claimed observed at handoff.

The exact R195 `/proc` census and journal metadata/hash helpers are retained in `R195_HELPERS.json`, with their original path and full-source SHA-256; the helpers no longer depend on temporary source files surviving. Census is fresh every pass, not the old R195 roster. SSH uses only existing `a100_ssh.sh`, `ovx_ssh.sh`, `a40r_ssh.sh`, `ovx3_ssh.sh`: node1/2/4/5. Node3 is absent from the allowlist. The preserved R195 inventory supplies labels and lease ceilings; nodes are skipped 300 seconds before their recorded lease expiry, and missing lease evidence is a skip, not an authorization guess. No host secrets/environment values or SSH stderr are logged.

Every process is read through its own `/proc/PID/root` mount namespace, then UID/start ticks/cwd are rechecked. Current metrics require a hash-verified LOADED record matching that PID and incarnation time. The observed trial and plan-file hash are retained. Before matching LOADED there is **no current REQUEST, stage, sleep, parent count, or raw sample**. Source-history head/REQUEST are a separate `inherited_source` object. Loading/unknown never means broken. `T` is observed stopped/held, not a failure diagnosis; census totals are observed processes, not actively learning children.

Journal collection is capped at 2,000 current-window records, with up to 10,000 tail-metadata probes to locate the current LOADED. Remote time is 110 seconds/node; SSH timeout is 125 seconds; tracked journal reads are at most 256 MiB/node and full records 2 MiB each. Current raw last-ten TRAIN responses are resolved from RESPONSE documents only after a matching TRAIN REQUEST; record hashes and exact raw-text hashes are checked. No sealed/FINAL documents, checkpoint tensors, evaluation outputs, provider calls, or GPU APIs are accessed. Exceptions record bounded machine reasons, not raw credential-bearing errors.

Fullwidth, CJK/Kana/Hangul, cross-script, whitespace, zero-width, and case-join counts are descriptive. Capitalization reuses the existing R203 `scan_target` unchanged, with its exact in-memory source hash. Every counter has a denominator; missing evidence is unverified. Deliberate typography, code, names, quotations, and language choice are confounds. There is no degradation, human-parenting, runtime, or LoRA causal inference.

Sleep dose joins actual presentation counts to new-row hashes, reporting new/replay optimizer updates separately. Sleep duration uses SLEEP_REQUEST-to-COMPLETE mtimes, including checkpoint writing. Parent counts are accepted TRAIN INBOX records in up to one hour **after this native's LOADED**, not proof of model attention, full REQUEST inclusion, or an extrapolated hourly rate. State-rejection opportunities deduplicate consolidation source IDs and exclude NO_EXPLICIT_STATE_DELTA. Raw samples never appear in COORDINATION or Markdown.

## Control

Run from the repository root:

```bash
python3 -B research_loop/workers/rohin204_maintenance_20260917/audit.py status
python3 -B research_loop/workers/rohin204_maintenance_20260917/audit.py stop
```

`SERVICE.json` pins the monitor PID, UID, start ticks and command-line hash, interval and stop command. `status` verifies that identity rather than relying on PID alone. `SERVICE.lock`, `STOP`, `STATUS.json`, `STATUS.md` and the bounded `service.log` are in this directory. The status command does not read credentials. Starting after an intentional stop requires explicitly clearing/archiving the worker's STOP sentinel; it never clears it automatically.

Retain the last 36 JSON/Markdown passes (12 hours at the requested cadence), plus latest STATUS. Rotating service logs have a 64 KiB limit with two backups. A 16 MiB per-pass raw-copy threshold withholds local raw copies if reached, retaining source references/hashes/metrics; original remote raw journals are never changed. Possible credential patterns similarly withhold whole local raw strings rather than rewriting them. COORDINATION gets a compact counted table and owner routing, never raw text or parent/evaluation scores.

## Measurement correction

The initial 03:27:26 UTC pass falsely presented zero-mtime inherited clone history as ancient current staleness and inherited REQUEST13003 as current. Its last C2 readout exhausted the old prefix-read budget and reported only RuntimeError. Those measurement claims are superseded, not evidence of learner failure. The 03:28:45 recheck resolved C2 PID3165023, LOADED5976 and REQUEST5996/prompt4251; the original failure message was not recorded, so the exact old exception reason is not asserted. Moving prompt-prefix reads to the latest REQUEST reduced reads substantially; new errors expose bounded reasons.

The correcting 03:30:52 UTC pass resolves all 28 observed process identities. C2 had independently changed to operator-owned PID3179563 and had no matching LOADED at that instant: current REQUEST correctly absent. Fresh native counts may change while sole operators perform authorized replacements; this monitor does not infer failures from count differences.

## CPU regression command

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CUDA_VISIBLE_DEVICES='' \
/data/home/rohing/.cache/uv/builds-v0/.tmpSWv1MH/bin/python -B -m pytest \
-q -p no:cacheprovider --basetemp=research_loop/workers/rohin204_maintenance_20260917/test_tmp \
research_loop/workers/rohin204_maintenance_20260917/test_audit.py
```

Tests cover the active-node allowlist, expired-lease no-call behavior, hash verification, exact raw/scanner counts, large prompt/checkpoint metadata, zero-mtime timestamps, current-incarnation LOADED matching, and the no-current-request-before-LOADED boundary.

Validation at handoff: **10 passed in 0.12s**. Existing unrelated whitespace in COORDINATION was not edited. No runtime, arm-table, learner code, or operator code was changed.

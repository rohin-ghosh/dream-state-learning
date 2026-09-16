# F2 R139: CPU-staged, Main-only saved-state handoff

Non-reset prospective parent choice under `bb2f2eb9:COORDINATION_2026-09-16T02:35Z`.
No release, signal, native/model load, provider call, stale-lock removal or launch performed.
No A2/F1/F4 edits. All raw history/carry/config/prompt material remains node-local or in private controller `/data` runtime, never this receipt directory.

## Frozen artifacts and tests

- Source `gpu/orch_r139_math_astra_handoff.py`: `ab81a47a460e129c0fdd8017f9cd42fbedf698b3e0581b79f16f5a1b42eb50e2`.
- Tests `tests/test_orch_r139_math_astra_handoff.py`: `a03c8779a0ef6d53b4a2f3063398dada3b3ef312e83efd0c7a0a4c5df080a8e1`.
- Local26 PASS; exact native venv26 PASS plus frozen R12410 PASS. Native and controller CPU check phases PASS.
- Native source: `/localhome/local-rohing/orch_r139_math_astra_handoff_source_20260916_v1`;212 frozen R124 dependencies plus wrapper/tests and bound CPU receipts.
- Native manifest `7af97488f8f54a534777f077c57e5f3c52138f4c11443fe24628c333d9a57f1e`.
- Native root: `/localhome/local-rohing/orch_r139_math_astra_handoff_20260916_v1/F2`.
- Native REQUEST SHA `b1302fc822ea549e1605209b486e65611f4e2ac5b374ffa979ca5c6e34cd3f5c`.
- Controller stage: `/data/home/rohing/courier/runtime/r139_f2_astra_handoff_v1`.
- Controller manifest `428713960d2bb44ed804228f0a133861a486e8598c250703d6fc8fbc8a0eeddc`.

```bash
python3 -B -m unittest discover -s tests -p test_orch_r139_math_astra_handoff.py -q
CUDA_VISIBLE_DEVICES= python3 -B /data/home/rohing/courier/runtime/r139_f2_astra_handoff_v1/orch_r139_math_astra_handoff.py broker-check --manifest-sha256 428713960d2bb44ed804228f0a133861a486e8598c250703d6fc8fbc8a0eeddc
bash gpu/ovx3_ssh.sh 'CUDA_VISIBLE_DEVICES= PYTHONPATH=/localhome/local-rohing/orch_r139_math_astra_handoff_source_20260916_v1 /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r139_math_astra_handoff check'
```

Existing staging is immutable: **do not rerun prepare/broker-stage, overwrite files or reuse the source path for edits.** `R139_SOURCE_MANIFEST.json` and `R139_CPU_TESTS.json` bind native preparation; `CPU_NATIVE_REGRESSIONS.json` in the new root additionally binds the exact live venv's26+10 tests. The staged `MAIN_GO_TEMPLATE.json` files deliberately remain unauthorized.

## Exact state seam

Original actor3953966/start3542788/boot`2c05ffec-1b4c-472f-9688-2a37543a6f4a`, original guard3953521. Original source/PLAN pins and exact host hash/index1/GPU UUID are enforced. Native Python is `/localhome/local-rohing/v2/venv/bin/python`, not the controller/system environment.

R124's existing pidfd boundary is retained: wait for the actor's own saved sleep/readout wait; identity-bound STOP; let only its existing DEV readout finish naturally without any readout-child signal; recheck stable counters/checkpoint; TERM+CONT that exact actor; require pidfd exit and the original guard terminal. The only removed execution tail is automatic successor guard spawning. Release does not launch anything.

Latest observation was committed44/native1140/parent130/AdamW15508, not an activation boundary. Main's release captures the then-current saved cycle, all counters, original reservation/disposition hashes, whole saved carry and exact ordered `history.extend(rows)` for every completed sleep. It retains the original adapter/AdamW/CPU+CUDA RNG checkpoint references. F2 has no persistent route-style actor head-settings variable; its original `child()` uses delivery-specific reflection settings. That unchanged machinery and saved carry/rows are reused, not supplemented with synthetic state.

New PLAN retains the original train/dev/final/clock/anchor references, all caps/walls, parent wait/injection semantics and historical provenance. Only new-segment admission names Astra; it does not relabel old Fable. Old pending/delivered/reservations are archived separately, and new active pending/delivered start empty. Original queue and claim ledger remain in place. No old request, refusal, partial, claim, missing or late COMPLETE can become eligible. The high-water/timestamp/request-inventory boundary is finalized **after release**, before the broker and successor start. R124 paired before/after probes are not replayed; existing FINAL outputs anywhere in the predecessor chain are not replayed.

The controller copies exact frozen A2 R137v3 provider code and NEXT_GUIDANCE repair, using the original authorized wrapper context. Only F2 transport routing and new immutable source pins differ. F2 caps remain parent384/output8192/budget1.0/deadline1789596120, not A2's100000/1024. Original claim count continues charging the broker cap. Auth/provider/low effort/one-attempt timeout/output parsing and visibility are unchanged. Packet storage uses `/tmp/r139_f2_astra_packets_v1` as a compatibility symlink into the private `/data` stage, not VM-root raw storage.

## Main-only publication and release

After publishing the exact source/tests, Main creates the new native root's `MAIN_GO.json` from its template: set `authorized=true`, `publication` to Main's actual publication identifier; retain the exact request/source-manifest hashes and intake. Do not place authorization in frozen source.

Main may then arm release with this **foreground command** (waits for the next safe saved readout, within REQUEST's one-hour preparation window; no successor launch):

```bash
bash gpu/ovx3_ssh.sh 'cd /localhome/local-rohing/orch_r139_math_astra_handoff_source_20260916_v1 && CUDA_VISIBLE_DEVICES= PYTHONPATH=/localhome/local-rohing/orch_r139_math_astra_handoff_source_20260916_v1 /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r139_math_astra_handoff release'
```

Wait for `READY.json`, not merely `RELEASED.json`. A failed boundary race resumes the original; a stopped original with a failed subsequent build is **not** readiness. Do not rerun release to replay work. Read only compact READY refs/BOUNDARY counters, not full checkpoints or history. Native `check` reports `released`, `ready`, `launched` and counters without raw data.

## Pending stale-lock handoff, no process signals

At audit the old Fable broker4101008 was absent; all122 claim directories had `PUBLISHED.json`, no unfinished claim, and no matching exact-F2 broker process was observed on node or controller. Original queue's empty `RUNNER.lock` remains; inode31852110/device66307/ctime_ns1789500736021483138/uid2524. Nothing removed it. Broker serve intentionally fails closed while it exists.

Main must coordinate exclusive ownership and recheck no F2 broker/provider call before removing **only that exact empty stale directory**. Do not remove a changed lock or replay its historical claims. With no other F2 broker launch concurrent, this bounded node command verifies original identity/claims and the captured inode before removal; it never signals any process:

```bash
bash gpu/ovx3_ssh.sh 'python3 -B -' <<'PY'
import json, os
from pathlib import Path
new = Path('/localhome/local-rohing/orch_r139_math_astra_handoff_20260916_v1/F2')
queue = Path('/localhome/local-rohing/orch_math_feedback_uptake_r115_f2_20260915_attempt1/lane1')
go = json.loads((new/'MAIN_GO.json').read_text())
assert go['authorized'] is True and go['publication']
assert (new/'READY.json').exists() and not (new/'LAUNCH.json').exists()
assert not Path('/proc/4101008').exists()
scope = (str(queue).encode(), b'F2_math_r124', b'orch_r139_math_astra_handoff')
for process in Path('/proc').iterdir():
    if not process.name.isdigit():
        continue
    try:
        argv = (process/'cmdline').read_bytes().split(b'\0')
    except (FileNotFoundError, ProcessLookupError):
        continue
    except PermissionError:
        if process.stat().st_uid == os.getuid():
            raise
        continue
    assert not (argv and b'python' in argv[0] and b'broker' in b' '.join(argv)
                and any(marker in b' '.join(argv) for marker in scope))
assert all((claim/'PUBLISHED.json').exists() for claim in (queue/'parent_claude').glob('*.claim'))
lock = queue/'parent_claude/RUNNER.lock'
stat = lock.stat()
assert (stat.st_ino, stat.st_dev, stat.st_ctime_ns, stat.st_uid) == (31852110, 66307, 1789500736021483138, 2524)
assert not lock.is_symlink() and not any(lock.iterdir())
lock.rmdir()
print(json.dumps({'exact_stale_lock_removed': True, 'signals': 0}))
PY
```

This is a Main-reviewed pending command, **not an action already performed**. If an active broker/changed lock/unpublished claim is observed, stop and investigate; do not remove/replace it.

## Main-only broker then successor launch

After release, Main creates controller `MAIN_GO.json` from its controller template: authorize, use actual publication in `source_reference` **including the full controller manifest hash**, retain its config digest and not-before window. That legacy schema is the unchanged broker authorization envelope, not model attribution. Main's existing authorized provider environment is reused; no credentials are copied or edited.

```bash
CUDA_VISIBLE_DEVICES= nohup python3 -B /data/home/rohing/courier/runtime/r139_f2_astra_handoff_v1/orch_r139_math_astra_handoff.py broker-serve --manifest-sha256 428713960d2bb44ed804228f0a133861a486e8598c250703d6fc8fbc8a0eeddc > /data/home/rohing/courier/runtime/r139_f2_astra_handoff_v1/BROKER.log 2>&1 < /dev/null &
```

Require actual `BROKER_ACTIVE.json` publication in the new native root and a live controller broker. It binds model, config, manifest and actual release boundary. Serve acquires the original queue lock and its own controller flock, requires no unfinished claim, and requires native counters still equal the release counters. It cannot activate after new child requests already started.

Then, and only then, Main starts the native successor from the immutable source with the **original native venv**:

```bash
bash gpu/ovx3_ssh.sh 'cd /localhome/local-rohing/orch_r139_math_astra_handoff_source_20260916_v1 && CUDA_VISIBLE_DEVICES= PYTHONPATH=/localhome/local-rohing/orch_r139_math_astra_handoff_source_20260916_v1 nohup /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r139_math_astra_handoff guard > /localhome/local-rohing/orch_r139_math_astra_handoff_20260916_v1/F2/GUARD.log 2>&1 < /dev/null &'
```

The original privileged GPU admission remains mandatory, with no waiver. Check exact optimizer step and CPU/CUDA RNG restoration, new LAUNCH identity, advancing inherited counters, and only a naturally generated post-boundary parent request. Distinguish broker COMPLETE publication from native injection, as with A2. Failure is not permission to replay, reset, switch provider again or weaken admission.

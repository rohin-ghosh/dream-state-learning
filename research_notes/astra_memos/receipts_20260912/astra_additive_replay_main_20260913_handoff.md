# Additive Main launcher — EDITSTOP

September 13, 2026. Bounded outer-launcher sidecar complete. No native/network/
GPU/model operations, repo edits, Git actions, process launches or alterations
to earlier trainer/core/runner/helper files by this worker. Main owns actual
preparation, allocation, launch, process reconciliation and scientific outcomes.

## Final owned files

- `/tmp/astra_additive_replay_main_20260913.py` SHA256
  `1ed1b383f2a36855f53e7b165dc9d75fe99620e930a3ae89332fcbe22c7ce05c`
- `/tmp/test_astra_additive_replay_main_20260913.py` SHA256
  `b98c2430b4638c772a398959a16272e3f8c43e3ab9fd104a03c36552e9916add`
- This handoff's hash is returned separately, avoiding self-reference.

Local validation: `python3 -B /tmp/test_astra_additive_replay_main_20260913.py`
passed22/22 tests in0.125s. CLI `--help` passes without loading the runner or
performing native operations. All Popen, allocation, reservation, native-prepare,
verify and GPU-state operations in tests are mocks. The actual accepted receipt
bytes were read from the existing VM mirror; no Torch tests repeated, receipt
archive extraction, score reduction or broad custody review performed.

## Bound final sources

| Input | SHA256 |
|---|---|
| Additive runner | ca54e7e1971d89224bb8dec8f3518d0a6a73ec4d1abe6f29278bab335b1618a5 |
| Additive core | b58e4c90e2abdd26648475c9fb1fe92e3bc3fef2fa7664ecaaa69fc93591076a |
| Additive trainer | 3f2e73ef69b12c8db211e1d3043e4559713e036ffe09571ab8bc4c5199a426a0 |
| Additive trainer tests | 49e1fc9d266f89dfc69c1ea1c0112ed61e035190fd1ad2abfb8d7867828fdce1 |
| Protocol | 724d5a6e1aea7dca4b0ae42aec6e2fd0252b98646f7c903432927263f2c391e9 |
| Old repair runtime | f1e3782378959f0c2552eaf9646a6b8827b876652a535d3248e38fe28371c4fe |
| Accepted tiny CPU receipt | ff2346a72f7e4fed9f4cdb51c90bb701c736557add56f0462f2b1e7ef2bc0b7d |
| Reservation helper | 03ac5f43f19e3a54ed57c7362085ff2d96d7a06c2d9f7fc354c5789e84f8f6c2 |
| Existing roster prechecks | 71e8eaa0c326ddef4414539684d20315e3752c48ce425a280438100e32815929 |

Receipt default:
`/tmp/astra_additive_replay_tiny_cpu_20260913_attempt1/receipt.json`.
The optional `--tiny-cpu-receipt` accepts another absolute path only to the EXACT
same bytes. Gate checks PASS, exact candidate/test/frozen-helper/protocol pins,
all five expected checks strictly true, fixture_only=true and
native_scientific_evidence=false. It does not mistake tiny acceptance for native
scientific evidence. No override for failed/different receipts exists.

## Stable launcher API and staging

```python
specs(checksum, core_checksum=CORE_PIN, receipt_path=TINY_RECEIPT)
prepare(seed, checksum, receipt_path=TINY_RECEIPT)
launch(seed, checksum, receipt_path=TINY_RECEIPT)
hold(seed, checksum, receipt_path=TINY_RECEIPT) -> integer_returncode
```

The CLI has `specs`, `prepare`, `launch`, `hold`, required `--runner-sha256`,
required `--seed` except specs, optional `--core-sha256` for specs, and optional
`--tiny-cpu-receipt`. Exact source pins are fixed, not arbitrary accepted flags.
CLI converts hold's returncode to process exit status. Main alone uses the CLI
on node2; do not call hold manually after launch.

Main reports protocol.md and accepted receipt already staged at the defaults.
Main still copies the frozen launcher to `/tmp/astra_additive_replay_main_20260913.py`.
Other required native inputs are the final core/trainer/runner/old runtime,
existing SOURCE tree `/tmp/astra_level1_real_record_source_20260913_attempt1`,
the pinned reservation helper and roster prechecks at their existing paths,
and the three completed old own-replay roots plus their `_collected` directories.

Default specs directory: `/tmp/astra_additive_replay_specs_20260913_attempt1`.
`specs` leaves the runner's exact13-key spec schema unchanged. It binds each
`/localhome/local-rohing/astra_diagnostics/own_replay_repair_seedN_20260913_attempt1`
using actual-byte hashes of plan.json, capture_complete.json,
`ROOT_collected/collection.json`, and scores.json. Boot ID and lease are inherited
from that original root's spec.json, with seed/runtime checks. The runner's
unchanged bind/verify enforces the full source/history/parent semantics.

Separate `seedN_gate.json` binds the accepted receipt, new launcher hash,
runner hash and actual new spec-file hash. `seedN_prepared.json` binds that
same launcher gate to the returned native prepared-plan hash. This is launcher
custody, not an extra unrecognized runner spec field. Exact receipt path must
remain the same across specs/prepare/launch/hold because the gate includes it.

All spec/gate/prepared files are exclusive-create; all three specifications are
validated before any is written. Partial failures are preserved, never deleted
or retried by this launcher. Native tokenizer preparation remains the pinned
runner's implementation, explicitly empty CVD and allow_native=True; no replica
of the training or scoring framework is introduced.

## Exact roots / allocation

| Seed | New native root suffix | Node2 physical GPU | UUID |
|---|---|---:|---|
| 0 | additive_replay_seed0_20260913_attempt1 | 0 | GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0 |
| 1 | additive_replay_seed1_20260913_attempt1 | 1 | GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4 |
| 2 | additive_replay_seed2_20260913_attempt1 | 2 | GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05 |

Roots are under `/localhome/local-rohing/astra_diagnostics/`. No placement,
seed substitution, retry or output deletion option is provided. These UUIDs
retain the prior own-replay/alignment mapping; current availability is NOT
inferred from the old roster or Main's earlier empty-process snapshot.

At launch, call the runner's THREE-value verify (memory,plan,bound), current
allocation check, probe GPU state, pinned reservations(config,index,UUID), and
probe GPU state again. Reservation helper performs actual /proc/queue checks
only when Main invokes launch. Boot/lease checks use runner.allocation: current
boot and7200+180seconds plus six-hour lease-finish margin; no copied alternative
lease rule. Main remains responsible for campaign-wide eight-A40-hour accounting
and completing the protocol's all-three-root native preparation before fitting.

## Holder / controller / collection custody

- Main invokes prepare/launch with explicit `CUDA_VISIBLE_DEVICES=''`.
- Launch makes exclusive `ROOT.launcher`, writes precheck, and starts one detached
  holder with CVD equal to the exact GPU UUID and PYTHONPATH=SOURCE.
- Holder validates the same prepared gate/plan and current allocation. Its
  exclusive `holder_started.json` makes repeated hold attempts fail before spawn.
- Controller and collector are both detached with CVD empty. Only the runner
  assigns actual GPU worker visibility; holder retains its reservation UUID.
- Holder waits for controller, writes controller_exit.json, and starts collect
  exactly once ONLY after returncode0 and hashing actual capture_complete.json.
  It passes both prepared plan hash and completion-file hash, with fixed output
  `ROOT_collected`; no external collection command on these new roots is needed.
- Nonzero controller exit skips collect; collector failure propagates without
  retry. Missing completion or spawn exceptions preserve failure receipts.
- Exclusive collection_started.json precedes collector spawn. Collector and
  final exit receipts record actual observed returncodes. PID/PGID and command
  receipts remain separate from exit evidence, not claims of live release.
- Launch failure after possible spawn records holder_may_be_running rather than
  killing/assuming cleanup; holder failures likewise record conservative child
  uncertainty. No kill, deletion, remote operation or retry logic is present.

Retained custody in ROOT.launcher: precheck.json, stdout.log, launched.json,
holder_started.json, controller.json, controller_exit.json,
collection_started.json, collector.json, collector_exit.json, exit.json;
failure.json or holder_failure.json when applicable. No launcher file asserts
successful scientific outcomes, promotion, release or current process absence.

## Main-only command shapes (not executed by this worker)

```sh
CUDA_VISIBLE_DEVICES='' python3 -B /tmp/astra_additive_replay_main_20260913.py specs \
  --runner-sha256 ca54e7e1971d89224bb8dec8f3518d0a6a73ec4d1abe6f29278bab335b1618a5
CUDA_VISIBLE_DEVICES='' python3 -B /tmp/astra_additive_replay_main_20260913.py prepare --seed N \
  --runner-sha256 ca54e7e1971d89224bb8dec8f3518d0a6a73ec4d1abe6f29278bab335b1618a5
CUDA_VISIBLE_DEVICES='' python3 -B /tmp/astra_additive_replay_main_20260913.py launch --seed N \
  --runner-sha256 ca54e7e1971d89224bb8dec8f3518d0a6a73ec4d1abe6f29278bab335b1618a5
```

N is one of0,1,2; prepare all three first. No launch has been performed here.

## Tests and limits

22passing mock tests cover exact accepted receipt and raw-byte reserialization
rejection; failed check/candidate/status; strict seed roots; pin-before-import;
exact closed spec/history hashes; duplicate/spec-preservation; wrong old seed;
empty-CVD preparation; prepare failures; altered plan/gate; three-value verify;
UUID holder environment; reservation conflicts; boot/lease rejection; GPU change
after reservation; rc0 once-collection with empty child CVD and completion pin;
controller/collector failure propagation; absent completion; wrong holder CVD;
spawn failure custody and existing collection refusal. No real process was
spawned and no GPU/process table was inspected during these tests.

No API blocker found. Mock tests establish control flow, not native availability
or successful preparation/controller/collection. Final native acceptance,
source placement and observations belong to Main. Earlier trainer EDITSTOP
and Parfit's final core/runner files remain unchanged.

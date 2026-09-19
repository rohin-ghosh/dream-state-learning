# Node2 extra-caption checkpoint/tail port — CPU result, not admission

[Builder] 2026-09-19 04:11 UTC — Non-material, caption-only continuity repair.
The original-source reader port preserves experiment/learning/visibility policies,
all rows and prompts, original `RecoveryJournal` transitions, the original
`gpu.r233_node2_recovery` confined dispatch route, and the September 20, 2026
18:00 UTC hard end. CPU-only work; no native/parent signals, native launch,
reservation, writer-lock acquisition on the actual journal, GPU/model load,
service management, old-source/control modification, guard reuse, or admission.
Only this worker and its new declared source/operator directories were written.
C0/Astra7 and other cohorts are outside scope.

## Ready artifacts

- `prepared_v2/MANIFEST.json`: 218 Python files plus exact original startup text.
- `prepared_v2/PLAN_CANDIDATE.json`: deterministic candidate, **not authorized**.
- `prepared_v2/GUARD_REQUIREMENTS.json`: derivable fields and missing fresh
  dependencies; deliberately **not an executable guard**.
- `CPU_TEST_RECEIPT.json`: hashes of code, named test logs and actual CPU evidence.
- `COMMITTED_BINARY_VERIFIED.json`: first operation hashed committed adapter
  files and optimizer/RNG against COMMIT, before preparing the port.
- `STAGED_V2.json`: exact immutable staging receipt and operator hashes.
- `ACTUAL_CPU_V2.json`: full small semantic/state/inbox/sidecar/timing receipt.

Node2 base (all following paths relative to this original fork):

```text
/localhome/local-rohing/orch_r229_unparented_caption_20260918/r213_r226_caption_unparented_fork
```

New staged source: `source_checkpoint_tail_20260919_v2`.
New staged CPU operator: `caption_checkpoint_tail_cpu_20260919_v2`.
Candidate future control: `control_checkpoint_tail_20260919_v2` — **not created**.
Local `prepared_v1` is preserved, superseded and **never staged**. Its synthetic
tests exposed working-state serialization/projection differences; v2 fixes that
without changing history bytes. Original sources and sealed v1 remain untouched.

## Exact source delta

All 216 original Python source pins were fetched and verified. Only one existing
file changes; two files are added. No `organism_v6` file changes.

| Path | Original SHA256 | Receiving SHA256 |
| --- | --- | --- |
| `gpu/r233_node2_recovery.py` | `a411b7fed8ed8338725467ff483b552e60db3365e3e0ac962d2325aeec8eb4a0` | `38b2da26b45aa687cbf4d474de18d38bd9d2100a404a0fa3e349402d3035c2aa` |
| `gpu/checkpoint_tail_runtime.py` | added, exact tested reader | `972456b7d6cb026cc922e067114701d4f157fa6ed775e4406ecb52c86eef7d3e` |
| `gpu/caption_tail_runtime.py` | added | `8394ee88c9d67ae03ecacd1c5afd42b136835ea851f088cc34d8112cf71c997a` |

Manifest file SHA256:
`3f104df589064af3c038dee83d4d79b3490fe9a9f7616db662f558bd61cd9570`.

The only dispatch-module change binds the original `RecoveryJournal` through
an optional caption-only reader immediately before original runtime installation.
Absent `checkpoint_tail_recovery`, it returns the original class unchanged.
It does not replace `_advance`, caption sleep/tool hooks, native resume/model
loading, device confinement, admission, one-shot dispatch, or management checks.
The original journal constructor still takes its exclusive writer lock before
scanning; cold create is refused on the opt-in path. Full explicit `audit()`
continues to replay original transitions. Startup requires exact saved COMPLETE,
exact matching LEARN and only INBOX arrivals beyond it; pending or intervening
work is never erased to obtain admission.

## Actual node2 evidence

- COMMIT `sleep_000119/COMMIT.json` SHA256:
  `a5d4034d71916d9f5af8eecd9653fb1be62ecd8c37e29259cf06448dd0008c44`.
- Adapter aggregate `edbd4fe25b6706349a14b5df5a2d99b6607f5f3874ac65700088137efd674838`;
  optimizer/RNG file `f438987995b73a12d6519bb2771fb889a676d9cb850c8d4e3f316943f8fb2260`.
  All three adapter files match COMMIT. 392 saved AdamW parameters have complete
  CPU payloads and counter 10236; Python/CPU/CUDA RNG payloads validate without
  initializing CUDA. No model or adapter-tensor state reconstruction claimed.
- Exact COMPLETE **8527**, matching LEARN/head **8528**, sleep **119**, optimizer
  **10236**, **487 rows / frontier 487**, pending **null**, next driver cycle **120**.
- COMPLETE SHA256 `9bce737fd97a81cb8bee4a0be486db7ee9ae633887e90ab614d04f7d55fce430`;
  head SHA256 `58177fb38f89c7ab66cfa79a4f7d1a8c30d4eb1e8385dc410fb8abcc70a45c39`.
- State `058e9001c3c2947163b8b3eb52fe5913ea8c83924462dfc5b2fd6329193f979e`;
  history `22625a3fe4cb116060d98bae4644bd4f18c13042319d294160abd1a570fc423b`;
  working state `45774118e27975cfc41a2e96392a8ebb3414aa1c7357b5d758989679255c7435`.
- **15,398,786,560 raw journal bytes** authenticated; 8,529 records, only one
  9,107-byte LEARN tail. 35 historical INBOX registrations and exact COMPLETE
  decoded, plus correction-ledger provenance. No historical REQUEST/RESPONSE
  replay or new prefix-proof authority is introduced.
- Reader **33.545493 s**; boundary/binary verification **0.285584 s**;
  saved optimizer/RNG loading **1.181825 s**; total **36.532585 s**.
  Prefix hashing remains O(journal bytes). This is an exited life, not a
  sub-30-second live reservation design; no cap was raised or reservation used.
- All **70 inbox files** and their identities/hashes retained. 35 registered
  message IDs; zero additional unregistered JSON IDs at observation. This does
  **not** assert that every external message was consumed by the child.
- Correction ledger at record8450 / max cycle119 is bound and retained;
  exploration JSONL, manifest, writer-lock file, all 17,058 record/intent files
  and original source/guard/plan bytes unchanged. No same-UID process using the
  exact old source/guard was found before or after; fresh privileged admission
  must independently establish absence/allocation.
- Observer uses actual `guard.copy_raw/stream` FDs and original virtual inbox
  source IDs; it does not rewrite stored paths or pretend host observation is
  startup namespace proof. Production selection remains `plan.root/stream`
  under the **unchanged original confinement mapping**.

## Plan normalization and main-owned gates

**Concrete provenance launch blocker (main's explicit review requirement):**
the required `allocation['builder_entry_pushed'] is True` cannot truthfully be
provided under this task's no-commit/no-push scope. No commit or push occurred;
no such marker or new allocation was fabricated, and the consumed allocation
was not recycled. CPU/reader success is not a substitute. Main must obtain a
real compatible provenance disposition before any original admission/launch.

Exact-byte discrepancy to resolve, not exploit: the main repository's
`gpu/orch_r125_continual_guard.py:38` checks `builder_entry_pushed`, while the
guard-pinned original caption closure's same file/line checks
`builder_entry_logged` plus a bound passed CPU receipt. Both observations were
read directly. The prepared caption closure keeps its original guard bytes
unchanged. This work neither weakens the main-required pushed provenance nor
silently swaps guard versions. `LAUNCH_BLOCKERS.json` binds this unresolved
provenance requirement separately from the successful CPU receipt.

Only source/startup-context paths, explicit exact checkpoint-tail selection,
and removal of the **consumed** wall authorization change. The old authorization
new deadline equals the authenticated saved COMPLETE deadline and unchanged
new-plan deadline `1789927200`; `ACTUAL_CPU_V2.json` binds this proof to the old
plan SHA and saved-state SHA. No wall extension, row/prompt/control change, new
recovery/rollback event, or cold birth is authorized by these artifacts.

Main must create an unused original-route control/guard with fresh allocation,
source-bound CPU evidence/Builder entry and the real provenance disposition
above, lease proof, original privileged
admission, service/device confinement, source/root mount mapping and actual
absence verification. Never reuse the consumed old guard. Main also owns disk
headroom and failed-readout/service reconciliation. The original driver enters
cycle120 from 119 saved sleeps; this patch does not duplicate sleep119 or rerun
the failed readout119. No sealed readout scores were inspected.

## CPU tests and precise limitations

- **23/23 new worker tests pass on VM and on node2's actual staged source**.
  Exact replay parity, original recovery transition, no historical body replay,
  pending REQUEST/RESPONSE, corruption/intent failure, moved journal, same wall,
  writer lock, cold-create refusal, LEARN count, all-INBOX retention, sidecar
  requirement, exact source delta and original caption hook installation.
- **126/126 focused original history/stream/journal/r233 and caption forwarding
  tests pass** on the receiving closure (`TESTS_FOCUSED_VALID_V2.txt`).
- An exploratory broader invocation has **one pre-existing topology assertion
  failure** in `test_r227_caption.test_only_caption_slots_and_no_filter_configuration`:
  the archived test expects five old slots instead of the original node2 slot2
  mapping. Identical failure reproduced on untouched source; not repaired here.
- That exploratory invocation also cannot import `test_ny_caption_life` because
  VM system Python lacks pytest. No dependency install or whole-suite-green claim.

Safe VM command:

```sh
python3 -B research_loop/workers/post_recovery_node2_caption_20260919/test_caption_tail.py
```

Safe node2 commands (use `gpu/ovx_ssh.sh`, not ovx4; full evidence stays node-local):

```sh
BASE=/localhome/local-rohing/orch_r229_unparented_caption_20260918/r213_r226_caption_unparented_fork
OP="$BASE/caption_checkpoint_tail_cpu_20260919_v2"
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 CAPTION_TEST_SOURCE="$BASE/source_checkpoint_tail_20260919_v2" /localhome/local-rohing/v2/venv/bin/python -B "$OP/test_caption_tail.py"
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B "$OP/node_probe.py" --prepared "$OP/prepared_v2"
```

Do **not** rerun `stage_and_probe.py` after staging: it deliberately refuses
existing declared paths instead of overwriting. Preparation/staging and CPU
validation are complete; **fresh original admission and native launch are not**.

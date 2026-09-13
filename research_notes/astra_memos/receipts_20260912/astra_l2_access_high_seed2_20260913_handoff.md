# Seed2-high saved-checkpoint access diagnostic — implementation handoff

2026-09-13. COMPLETE CPU implementation; EDITSTOP. Main owns exact protocol
freeze, native preparation, allocation, launch and collection. No native/model/
GPU/network execution, collection, fit, Git, repository change or live-root
access was performed here. Only the five files listed below were created.
Old SEQ136 sources, archives, child records, answers and adapters are unchanged.

## Scope and fixed measurement

Exploratory checkpoint-specific acquisition/access after the higher-LR loss
drop, not a new objective, exposure budget, dataset or qualification. The
completed seed2-high fit2 checkpoint had training last-batch loss .0145319579
and final epoch mean .01929. Those values motivate inspection; they do not
establish acquisition or saved-checkpoint eval loss. Both original and new
fits used20epochs. No stronger fit or dose trajectory is implemented.

Retain SEQ136's OFF / fit1 / fit2_PROMOTE, each with16exact TRAIN and16READOUT
prefixes, each scored against both original legal actions:64teacher-forced
candidate forwards/state,192total, zero updates. Fit1 experienced8keys; fit2
experienced16. Every worker cold-loads the same frozen base; fitted states
load their saved adapter, not an evolving adapter. No SHADOW refit, generation,
retry, alternate target, prompt rewriting or output-conditioned choice is added.

Unchanged measurements: native causal token log probabilities including EOS;
full likelihood sum, length-normalized mean, first-divergent-token margins;
strict first/full choices and exact ties; old/new counts; common/decision/
first-decision/EOS loss decomposition and comparison against OFF. Full-sum
choices are NOT greedy successes. Multiple divergent positions and unequal
12/14-token continuations remain explicit; no tuned tie tolerance is added.

HF teacher-forced candidate choices are not vLLM full-vocabulary greedy output,
and no HF-vLLM numerical parity is claimed. Original vLLM reports remain
historical comparators. SEQ136 already tested this method; this measures a
different saved checkpoint, not a new diagnostic method. Same inputs/targets
do not imply identical raw experiences or causal isolation of LR from seed.
No H1/H2, internalization, parenting, general learning or endpoint promotion.

## Implementation delta and API

`astra_l2_access_high_seed2_20260913.py` is a new copy of pinned SEQ136 v2.
An AST regression verifies all original functions are unchanged except:

- `collection_metadata`: new completed-run pins and explicit seed2/high-LR
  collection check; retains COMPLETE, plan/seal and128calls/3fits/100updates checks.
- `build_cases`: obtains `runtime.plan_learner_seed(plan)`, requires seed2
  and the pinned runtime's validated LR1e-4, explicitly passes
  `learner_seed=learner_seed` into `runtime.encode_training`. Full training
  JSON equality, including epoch orders, remains mandatory. No field is ignored.
- `main`: only the default collection binding changes. Worker/reducer commands,
  scoring algorithms, tensor route checks and receipt validators are unchanged.

New schema: `astra_l2_access_high_seed2_20260913_v1`. All raw native encodings,
assistant labels, supervised EOS and masked context/template tail are retained.
Source inventory, collection, plan/seal, interpreter, base, helper, candidate,
prepared/captured prompt and saved/loaded tensor guards remain fail-closed.
Old receipts cannot be relabeled as new receipts or passed into this reducer.

Python API remains `build_cases(...)`, `worker(source, collection, state,
output, deadline_unix, allow_native=False)`, `reduce_receipts(...)` and the
original scoring helpers. CLI remains `worker` / `reduce`; see commands below.
Preparation helper API: `prepare(probe_path, probe_pin, collection_path)`.
Controller API: `controller(options)` with CLI flags shown below.

## Fresh allocation, not a historical reservation

New controller uses GPU index3 and UUID
`GPU-e1277146-04f2-c38f-d1ae-1a98132f907e`, but does NOT treat SEQ136's old
reservation or the training plan's allocation as current permission. The
seed2-high training plan records GPU6; it stays untouched. Evaluation on3 is
a separate allocation whose current index/UUID is checked before each worker.

Main must supply independently freshly verified `--expected-boot-id` and
`--lease-end-unix`; there is no historical default. Before creation and every
precheck/release, require matching current `/proc/.../boot_id` and more than
1200seconds plus6hours lease margin. Controller CUDA visibility must be empty.
Workers receive only the fixed GPU UUID. Source interpreter path/hash remains
bound to the original run; do not substitute a different Python environment.

The unchanged pinned `/tmp/astra_node3_targeted_prelaunch_20260913.py`
(`32d366afc432d9e8dcf0c188cbf0725cdadfcc68a1a0f8e0b11532ca7629862a`)
executes fresh index/UUID, compute-process and same-user environment-reservation
checks before every worker and after release. The new controller additionally
requires a current-timestamp receipt with matching UUID/index and empty compute,
reservation and unresolved-user lists; zero exit alone is insufficient.
Failed checks stop the diagnostic, not relax the source guard.

Limits: this inherited precheck is not a global scheduler lock or proof of
other users' environment reservations. It retains its narrow exact-identity
systemd exclusion. Main must reconcile the current roster/queues and ensure
exclusive allocation separately; if that helper cannot resolve the current
node, stop rather than weakening it here. No node/lease was checked live here.

Same1200-second controller envelope,64forwards/worker,192total, no retries.
Worker hard contract is400seconds; controller passes at most390seconds and
keeps60seconds of outer cleanup/reducer margin. Fresh process groups, PID/start
identity checks, owned-process-only cleanup, release checks and fresh output
files are retained. Outputs must not overlap protected inputs.

## Frozen artifact bindings

- ROOT: `/localhome/local-rohing/astra_diagnostics/l2_lr_seed2_high_20260913_attempt1`.
- SOURCE: `/localhome/local-rohing/astra_sources/l2_lr_comparison_20260913_attempt1`.
  CPU source fixture: `/tmp/astra_l2_lr_source_20260913_attempt1`.
- PLAN: `74569b1e8c3e0330e0c4f387120fedd4d9f71406366d8b5459088a35ab1a3593`.
- SEAL: `c5ddc5585d33e1ffd6f1bcce46d9b6a2b23bfed334e7117c5e83586cf9fb9a2d`.
- COLLECTION: `/tmp/l2_lr_seed2_high_20260913_attempt1_collected`,
  `24f6e79530b575a8923e5b1145f2e26d7cd95590ceebf9d12b6fd79013ebbd7e`.
- fit1 candidate: `ed76540db3db67c5fba560c4441b30ac0855009a09889dae489ff99183a54192`.
- fit2_PROMOTE candidate: `8e79df460e52e94b342de285bcc85ef69cc5fb468a8904d443c665af37bc8ff4`.
- fit2 weights: `94e2bb58cff753dd8500f227b8172a59e51122a9bb556d9e230f8e9812946c63`.
- Base: `1a28421dffcee174137818b590991ba80678b58f6c63fd8eab027a933486efd5`.
- Runtime: `dce8cd88b82bd51ec4f12e482ce70dc220453cb85dcaeb758206c7b5200a4277`.
- Core: `0bb33988f003a0111e14cdfb53b3dc86a695e8e20656c90e71cfadb5ad28d352`.
- Trainer: `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`.
- Public helper: `59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c`.
- Reflection helper: `0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc`.

The source inventory also requires the original empty `organism_v6/__init__.py`.
Native helper paths stay exactly as recorded in the plan. Main must make the
exact pinned collection bytes available at the path above; this implementation
does not regenerate or collect them.

## Exact native commands — Main only; not executed here

On node3 after Main stages and hashes the new files and frozen inputs, use
the original pinned interpreter `/localhome/local-rohing/v2/venv/bin/python`
(SHA256 `a92f0f95e883390c7256b2e441484aac06b1002dbe1d924141a77c8d82f96223`).

Native CPU preparation (tokenizer only, no model or GPU):

```sh
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 \
  HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false \
  /localhome/local-rohing/v2/venv/bin/python -B \
  /tmp/prepare_astra_l2_access_high_seed2_20260913.py \
  /tmp/astra_l2_access_high_seed2_20260913.py \
  d319c53aeeaf45743d77e87af30eafe1ae8e2f111d35e440c8c0b1402b4b2525 \
  /tmp/l2_lr_seed2_high_20260913_attempt1_collected
```

Expect `PASS_NATIVE_CPU_ENCODING`,32cases, seed2/LR.0001, zero forwards/updates,
and a case hash. Preserve stdout/stderr into fresh Main-owned paths. This
native tokenizer replay remains unexecuted; a mismatch must stop before launch.

Main must explicitly set `NODE3_BOOT_ID` and `NODE3_LEASE_END_UNIX` from its
fresh node/lease inventory, not copy a historical reservation. Then:

```sh
: "${NODE3_BOOT_ID:?Set from fresh node3 identity inventory}"
: "${NODE3_LEASE_END_UNIX:?Set from current verified lease}"
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  /localhome/local-rohing/v2/venv/bin/python -B \
  /tmp/controller_astra_l2_access_high_seed2_20260913.py \
  --root /localhome/local-rohing/astra_diagnostics/l2_access_high_seed2_20260913_attempt1 \
  --probe /tmp/astra_l2_access_high_seed2_20260913.py \
  --probe-sha256 d319c53aeeaf45743d77e87af30eafe1ae8e2f111d35e440c8c0b1402b4b2525 \
  --collection /tmp/l2_lr_seed2_high_20260913_attempt1_collected \
  --precheck /tmp/astra_node3_targeted_prelaunch_20260913.py \
  --expected-boot-id "$NODE3_BOOT_ID" \
  --lease-end-unix "$NODE3_LEASE_END_UNIX" --allow-gpu
```

The output root must not exist. Do not delete a prior attempt; Main assigns a
new version if that name is taken. Controller executes each original worker
CLI and pinned reducer automatically, records `controller_started.json`,
per-state launch/precheck/release receipts, state JSON/stdout/stderr, report
and terminal. Terminal may be `FAILED_NO_RETRY` despite controller exit0;
Main must inspect terminal status, report pins and release evidence, not just
shell exit. Completion is diagnostic-only, never scientific promotion.

## CPU verification and exact owned files

One suite run: **40 tests PASS in5.570seconds**, including the original20
probe tests,6new seed/order regressions, AST algorithm equivalence, inherited
10controller tests, fresh allocation tests and prepare-before-import pin gate.
No torch/HF/model is instantiated: encoder fixtures use the pinned pure
trainer/core and toy tokenization; forward and subprocess APIs are mocks.
The seed2-positive test verifies both actual encoder calls receive2 and full
fixture replay succeeds. Seed0 encoded JSON fails without rewriting bytes;
wrong plan seed/LR, internal seed disagreement and epoch-order tampering fail.
Native tokenizer, saved-checkpoint tensors and current allocation are NOT
certified by these CPU fixtures. No tests were rerun after success.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s /tmp \
  -p 'test_astra_l2_access_high_seed2_20260913.py' -v
```

All three CLI help commands and four-file AST/whitespace checks also passed.
Original probe/controller/prepare/test hashes rechecked unchanged. No new
data/material selection or result-driven target changes occurred.

Owned files and SHA256:

- `/tmp/astra_l2_access_high_seed2_20260913.py`:
  `d319c53aeeaf45743d77e87af30eafe1ae8e2f111d35e440c8c0b1402b4b2525`.
- `/tmp/test_astra_l2_access_high_seed2_20260913.py`:
  `555d93f5d642d905046cb4e6573b3cf95ec1faca0b8e1950162633ad8c170708`.
- `/tmp/prepare_astra_l2_access_high_seed2_20260913.py`:
  `0857c542ab293ed497ec37677764102138803104077cf122051864a6fe3a795e`.
- `/tmp/controller_astra_l2_access_high_seed2_20260913.py`:
  `3f5f6118e3fef60074ac533b2650d415b6bd57ff15e379e2bf548be470233721`.
- `/tmp/astra_l2_access_high_seed2_20260913_handoff.md`: hash supplied separately
  to avoid a self-referential file hash.

EDITSTOP. Main may review/freeze/test/prepare/launch; this handoff is not a
claim that native preparation or execution has happened.

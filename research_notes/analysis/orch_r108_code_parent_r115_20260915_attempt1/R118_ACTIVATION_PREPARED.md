# F3 / A3 released; activation prepared, not launched

Both branch handoffs are native-local `R118_SHARED_HANDOFF_BRANCH.json`:

- F3 root `/localhome/local-rohing/orch_r108_code_parent_r115_node5_2_20260915_attempt1`, SHA `dfda09edf9a26e34fe1bdde3e4c7d29719000c03988e63dfff1ad6cf97ca9aa0`, completed20 / next21.
- A3 root `/localhome/local-rohing/orch_r108_code_parent_r115_node5_6_20260915_attempt1`, SHA `4f2d9752acbecdb36931163384407dcdfc48c9ea4587fd334b5f09e3d360e182`, completed6 / next7.

Original native, guard and pending-readout identities have exited. Each receipt
binds the original PLAN, linked release request and cycle receipt, every charged
reservation, published parent claims and raw node-local artifacts, plus carry.
Neither original lifetime, quota, task cursor nor completed-call status changed.
Both last actually bound REFLECTION generation caps are3072; their source IDs
are F3 `C020_E1_PARENT` and A3 `C006_META_PARENT`.

## Immutable overlay

Source: `/localhome/local-rohing/orch_r108_code_parent_r118_activation_20260915_v2/source`.
Source manifest SHA `2454c50f32d070558d7caf9abb93e45b3993633f04110fde3efe0861070695eb`.
CPU receipt SHA `c2fb7025d581aa9f5566a2a2d64a4bb1cccdf02e24fb3deea6d0f15b007cb02e`.
56 isolated CPU tests pass; native import/integrity/hostname-literal checks pass,
CUDA remains uninitialized. This is not a native GPU test or shared activation.

The182-file overlay retains all176 previously frozen source/fixture bytes and
adds three helpers plus three tests. ROSTER-pinned runnable/readiness sources
remain untouched. A thin successor-only wrapper restores recorded carry before
using the unchanged two-episode shared lifecycle. It never loads old BASE rows
as new replay and never creates an optimizer. Unicode requests use the already
tested canonical broker digest. No current life was hotpatched.

## Commands after Main's ADOPTION follow-up only

For each branch, set ROOT to the exact root above. SOURCE is the overlay path;
COMMON is `/localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1`.
Use the existing node Python `/localhome/local-rohing/v2/venv/bin/python`.

```bash
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$SOURCE" "$PYTHON" -B -m gpu.orch_r108_code_parent_r118_activate prepare --root "$ROOT" --initialized "$COMMON/INITIALIZED.json" --source "$SOURCE"
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$SOURCE" "$PYTHON" -B -m gpu.orch_r108_code_parent_r118_activate guard --root "$ROOT"
```

Prepare requires Main's exact initialized branch/config/adoption binding and
preserved released handoff; it only writes SHARED_ACTIVATION.json. Guard checks
CPU/source/handoff/carry/bounds, takes the original exact UUID custody lock,
runs fresh full privileged proc/CVD/minor admission, and enforces the original
hard deadline. Failed admission is never converted to a launch. No scan,
prepare, guard or successor launch has been performed by this preparation.

## Brokers

Hubble owns F3. Its successor must use SHARED_TERMINAL.json after exact adoption,
while preserving the original TERMINAL/CONTINUATION_TERMINAL artifacts.

A3 old broker956791 naturally exited. The prepared
`gpu.orch_r108_code_parent_r118_astra_shared` wrapper verifies an exact native
SHARED_ACTIVATION reference in the prospective launch receipt, checks Main's
INITIALIZED/config/adoption hashes, then redirects only its own old TERMINAL
lookup to SHARED_TERMINAL. Every queue/claim/response lookup is unchanged.
Launch receipt field: `shared_activation: {path, sha256}`. Keep original CONFIG,
ledger, memory floor, four shared HTTP slots, one attempt and all cutoffs. The
VM runtime requires the existing hosts.env symlink, not a copied secret. No
new broker is started before Main's follow-up and actual bound activation.

## A3 delivery diagnosis, no salvage

At12:11:57UTC, the preceding30minutes contained3COMPLETE/9MISSING. All nine
missing responses had completed envelopes and valid JSON, but custom
intervention_class values outside the actual broker's fixed enum. The actual
broker source SHA is `ec6056e44066d40395b15166a5c3795481722c2767a4ba917c4cc229dd547169`.
There were no explicit refusal fields or incomplete envelopes in those nine.
This diagnosis adds no provider call, does not reinterpret past deliveries and
does not change the strict parser or reroute refusals. Metadata-policy changes,
if requested, must be prospective and coordinated with the transport owner.

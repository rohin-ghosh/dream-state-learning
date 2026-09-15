# Exact route recovery binding commands — 2026-09-15 16:06 UTC

CPU only; no GPU dispatch. Native binder6 tests PASS; recovery launcher14 tests
PASS. Existing prepared request expiry remains **16:10 UTC**, not silently
extended. TRAIN remains16:55; hard end17:02. If expiry is reached, these commands
fail closed and require an explicitly authorized later startup window—not a
quota/deadline reset. No command below invokes the model or starts a GPU guard.

Binder source (CPU preparation only; not part of the scientific actor closure):
`/localhome/local-rohing/orch_r118_route_recovery_binder_20260915_v1/source/gpu/orch_r118_route_recovery_bind.py`
SHA256 `9013aa34003a58804e285024c3017248494e76081cede08ddaac44a778c81b3e`.
Native `CPU.json` SHA256 `43b6d4049c6263c8680000a750a0cfbaef2b4a27df3e1180d52737e6a5a8c840`.
Existing recovery wrapper remains c6e8e9b0, original scientific closure c56 unchanged.

## 1. Bind the actual new Main campaign

Replace only the two angle-bracket placeholders with the actual published
campaign path and full SHA. This archives each previous PLAN and broker binding,
changes only campaign reference/activation directory in PLAN, and writes a fresh
request. It does not fabricate a broker binding or replace old attempt evidence.
Use a fresh output directory; do not rerun over an existing stage directory.

```sh
bash gpu/ovx3_ssh.sh 'set -eu
export CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1
PY=/localhome/local-rohing/v2/venv/bin/python
BINDER=/localhome/local-rohing/orch_r118_route_recovery_binder_20260915_v1/source/gpu/orch_r118_route_recovery_bind.py
PREP=/localhome/local-rohing/orch_r118_route_startup_recovery_20260915_v2/owners
OUT=/localhome/local-rohing/orch_r118_route_recovery_binder_20260915_v1/stage_1606
CAMPAIGN="<NEW_CAMPAIGN_ABSOLUTE_PATH>"
CAMPAIGN_SHA="<NEW_CAMPAIGN_FULL_SHA256>"
for branch in F1 A1; do
  case "$branch" in
    F1) prepared_sha=f59a2655fe83a938d29d4f3954a9ed1158726cf8944586f29ce2291b42e52973 ;;
    A1) prepared_sha=ec27ee04eb76a0e2d67e62363ffd8a8c690da4c310944d12f75b1d1b139e042b ;;
  esac
  "$PY" -B "$BINDER" stage \
    --prepared "$PREP/$branch/FRESH_OWNER_RECOVERY_PREPARED.json" \
    --prepared-sha256 "$prepared_sha" \
    --campaign "$CAMPAIGN" --campaign-sha256 "$CAMPAIGN_SHA" \
    --output "$OUT/$branch"
done'
```

## 2. Actual broker rebinding is required

Send the two `STAGED.json` PLAN references to Hubble for F1 and Poincare for A1.
Do not merely rewrite the broker PLAN hash and retain an incompatible process.
**A1's existing native custodian checks the old PLAN hash every3 seconds:**
changing PLAN requires actual custodian/provider-era rebinding. The binder
preserves the old binding, but does not claim that process already supports the
new PLAN. Hubble owns F1's provider process; Poincare owns A1 custody. No provider
call is needed for this CPU-only rebinding. Existing queues, wait120, claims,
responses, source and original terminal writer must remain preserved.

This is an actual process/data dependency, not another human approval gate.
The following preflight intentionally rejects stale/dead broker identities.

## 3. Preflight the exact final requests without launching

```sh
bash gpu/ovx3_ssh.sh 'set -eu
export CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1
PY=/localhome/local-rohing/v2/venv/bin/python
RUN=/localhome/local-rohing/orch_r118_route_startup_recovery_20260915_v2/source/gpu/orch_r118_route_startup_recovery.py
OUT=/localhome/local-rohing/orch_r118_route_recovery_binder_20260915_v1/stage_1606
for branch in F1 A1; do
  request="$OUT/$branch/REQUEST_FINAL.json"
  request_sha=$(sha256sum "$request" | cut -d" " -f1)
  "$PY" -B "$RUN" --request "$request" --request-sha256 "$request_sha" --verify-only
done'
```

## 4. Export final owners for Main's new all-eight session

This repeats preflight and writes the final owner references; it never dispatches.
Run only after successful actual broker rebinding. Do not ignore nonzero exits.

```sh
bash gpu/ovx3_ssh.sh 'set -eu
export CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1
PY=/localhome/local-rohing/v2/venv/bin/python
BINDER=/localhome/local-rohing/orch_r118_route_recovery_binder_20260915_v1/source/gpu/orch_r118_route_recovery_bind.py
PREP=/localhome/local-rohing/orch_r118_route_startup_recovery_20260915_v2/owners
OUT=/localhome/local-rohing/orch_r118_route_recovery_binder_20260915_v1/stage_1606
for branch in F1 A1; do
  case "$branch" in
    F1) prepared_sha=f59a2655fe83a938d29d4f3954a9ed1158726cf8944586f29ce2291b42e52973 ;;
    A1) prepared_sha=ec27ee04eb76a0e2d67e62363ffd8a8c690da4c310944d12f75b1d1b139e042b ;;
  esac
  "$PY" -B "$BINDER" final \
    --prepared "$PREP/$branch/FRESH_OWNER_RECOVERY_PREPARED.json" \
    --prepared-sha256 "$prepared_sha" --output "$OUT/$branch"
  sha256sum "$OUT/$branch/FRESH_OWNER_FINAL.json" "$OUT/$branch/FINAL_EXPORT.json"
done'
```

Main consumes the returned **new** owner paths and hashes when creating the new
session. CPU launcher CVD remains empty; the unchanged supervisor receives its
original UUID only after a new strict admission. Keep `R118_STARTUP_RECOVERY_1552`
as the single-use recovery attempt namespace. Never retry e834ff or remove its
FAILED file, original A1 LAUNCH_ATTEMPT or scans. Selector1519259 is untouched.

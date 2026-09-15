# Actual CODE release and Main-only staging

Both branches actually RELEASED by15:25:36.649UTC,2026-09-15. Original native /
guardian identities exited, all original reservation hashes unchanged, original
gen1 submissions reused only as custody evidence. Both central c56 pending
validators PASS. No GPU successor launched; no CONFIG/STATE change.

## Frozen source and tests

Source: `/localhome/local-rohing/orch_r118_code_parallel_source_20260915_v4_drain/source`

Absolute source_files dictionary:
`/localhome/local-rohing/orch_r118_code_parallel_source_20260915_v4_drain/SOURCE_FILES_ABSOLUTE.json`
SHA256 `566a09b53bf374aa64ea084cdef54e7f4ecb4e035ba4ce6ed2bbf34bddd65c37`.

Relative SOURCE_SHA256.json sibling SHA
`0de882fd5d3ea81d1429dc6c3f0624ac0a40612c90f06d423be99ead79b15d9a`.
Native CPU_TESTS.json sibling SHA
`b7f4e056c662a208956ec07835922e04c4495fdef73ccbb4c430ce4a45072e37`:
68focused native CPU tests PASS; source before/after verified. Frozen helper
`c56bb57b69405877a65124b623316f9b8bd769aa8f51db6f2481ff65325c5cdb`.

## Actual owner exports

F3 root `/localhome/local-rohing/orch_r108_code_parent_r115_node5_2_20260915_attempt1`:

- `parallel_v4/release_1524/OWNER_PREPARED.json` SHA `4ed1f0141f23c1a1d3fc48468f0a8eca3178e4668bbd84244fe92bf77c669289`.
- `parallel_v4/release_1524/OWNER_RELEASE.json` SHA `fb9142f0a94e9380bb5fb8b41ede8c45543915c863077937e59cf3fd86e3157a`.
- `parallel_v4/release_1524/HANDOFF.json` SHA `3ea0c2c0de57edcaf6011e7e77fe6f27440fdefdc48069c452dfca574ac1fa97`.

A3 root `/localhome/local-rohing/orch_r108_code_parent_r115_node5_6_20260915_attempt1`:

- `parallel_v4/release_1524/OWNER_PREPARED.json` SHA `28448cd27e3d62f79fcc6ca3c9a675aad61a95b9fe0eacd581336e453def38c8`.
- `parallel_v4/release_1524/OWNER_RELEASE.json` SHA `a9d4ccbccd7bac0273f9d8025bd9f1e00a347310d492036af15e1e5ad0f917fc`.
- `parallel_v4/release_1524/HANDOFF.json` SHA `befe7950b9b7ce9de700aa57322b0c65d6d1e3f2435d616016f71e9d017f30d7`.

OWNER_PREPARED is explicitly RELEASED_PENDING_MAIN_CAMPAIGN, not a running
actor or complete OWNER_REQUEST. It contains actual central owner boundary,
release envelope, absolute source export reference, interpreter, proposed
service path and exact remaining LAUNCH fields. V4_ACTUAL_DRAIN_RESULTS.json
contains all absolute release, pending, cursor and source refs/hashes.

## Main campaign requirements and CPU stage commands

Main LAUNCH authorization retains existing exact schema/all8 roots and own
PLAN/source/checkpoint binding, plus `boundary_mode=SETTLED_PENDING_CONSOLIDATION`.
Provide `campaign:{path,sha256}`, `activation_directory`, `anchor_root`, exact
original42 ordered `anchor_task_ids`, `common_root`, `service`, `final_old_root`
and `final_new_root`. These are not invented or authorized by the DRAIN export.
Current DRAIN document MUST NOT be reused as a LAUNCH authorization.

Once Main supplies its actual LAUNCH JSON, CPU preparation only:

```sh
SOURCE=/localhome/local-rohing/orch_r118_code_parallel_source_20260915_v4_drain/source
PYTHON=/localhome/local-rohing/v2/venv/bin/python
for SLOT in 2 6; do
  ROOT=/localhome/local-rohing/orch_r108_code_parent_r115_node5_${SLOT}_20260915_attempt1
  SERVICE=$ROOT/parallel_v4/service_1
  CUDA_VISIBLE_DEVICES= PYTHONPATH="$SOURCE" "$PYTHON" -B -m gpu.orch_r118_code_parallel_loop prepare \
    --root "$ROOT" --service "$SERVICE" \
    --handoff "$ROOT/parallel_v4/release_1524/HANDOFF.json" --authorization "$MAIN_LAUNCH_JSON"
  CUDA_VISIBLE_DEVICES= PYTHONPATH="$SOURCE" "$PYTHON" -B -m gpu.orch_r118_code_parallel_loop owner-request \
    --service "$SERVICE" --interpreter "$PYTHON"
done
```

Main consumes each generated service/OWNER_REQUEST.json for central dispatch.
No standalone CODE guard/native command is executed by this preparation.
Pending F3C22/A3C8 first resume existing submission, then campaign boundary;
new TRAIN C23/C9 waits for actual shared commit and fresh settled DEV.
Native/parent lifetime charges are respectively735/100 and274/40. Carried
reflection3072, original deadlines, quotas and same8-call FINAL allocations
remain unchanged. Broker/FINAL rebind commands in INTEGRATION.md still apply
after actual new guard/native start. Hubble owns F3 broker; CODE A3 overlay.

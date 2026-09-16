# F4 consumer: NOT supported under no-restart constraint

Read-only observation: **2026-09-16 02:08:42 UTC**. No provider invocation,
broker launch, child restart, model/optimizer change, shared-ledger edit, or Git action.

The resident F4 config binds `parent_model=claude-fable-5-1`. The native loop
loads that config once and passes the same in-memory object into each life.
`orch_r119_grid_async_parent.py:29` invokes the existing consumer with that model.
`orch_r111_grid.py:155` rejects an honest Astra COMPLETE/SILENT response as
`MISSING / actual_parent_model_mismatch`. The source-pinned synthetic CPU probe
reproduces F4 rejection and A4 acceptance with the same honest Astra response.
Editing a broker config cannot change this running child's in-memory binding.

**Do not launch a broker-only switch.** Do not forge `actual_model` or
`usage.model_usage.*.canonicalModel`, overwrite `parent_received`, rephrase prompts,
or redispatch a refusal. No model-label substitution is implemented here.

## Boundary and budget

- Snapshot: cumulative P0316; 315 received slots; 298 original Claude claims
  P0001–P0298 intact; no old broker runner lock. The ledger has reached cycle100.
- P0316 belongs to cycle98/open_turn and is historical even though its deadline
  had not expired at observation. First *possible* future slot is P0317, and
  the staged filter requires cycle >100. Neither is a launch authorization.
- Main must take a fresh publication-time high-water/cycle snapshot and exclude
  every earlier reservation, including missing queue files and unexpired backlog.
  New requests must be reserved after publication. Skip claimed, received,
  responded, missing, expired, non-TRAIN and non-experience requests. Retain the
  existing full TRAIN provenance/prompt validation before any eventual dispatch.
- Old broker cap298 is exhausted and remains unchanged. F4's already-pinned R119
  lease budget has cumulative PARENT ceiling404430; the conservative proposed
  new segment bound is 404430−316=404114 slots at this snapshot, not extra budget
  and not a dose target. **Authorized Astra segment allocation is currently 0.**
- Existing TRAIN end: September16 22:02 UTC; hard wall: September16 22:04 UTC.
  No extension, counter reset, visibility expansion, or Level2/3 change.

## Existing A4 transport and missing consumer seam

Reuse the existing `orch_r119_grid_fast_parent.py` /
`orch_r118_node3_6_grid_broker_http.py` / `orch_r115_grid_astra.py` transport
only after the consumer problem is resolved: truthful Astra attribution,
TRAIN-public prompt policy, episode-only cadence, low effort,1024 output cap,
existing HTTP slots and bounded cutoff, one attempt/no retry. Do not clone its
old `after_parent=40` into F4 or erase the old `parent_claude` ledger.

Under the current no-restart instruction there is **no supported attachment
command**. A saved-state boundary handoff requires explicit permission to
replace/resume the consumer and a separately tested truthful prospective model
binding. It must preserve the same frozen LoRA/checkpoint and optimizer state,
completed-cycle carry, cumulative ledger, pending-request dispositions, budgets
and wall. Such a handoff is **not implemented or authorized** by this preflight.

## Immutable read-only command (not a launch)

Only the two owned new Python files were staged in a separate node `/tmp` tree.
The command checks its exact SHA and the existing native-source pins. Exit3
means the demonstrated consumer block; it must not trigger a fallback broker.

```bash
bash gpu/ovx3_ssh.sh 'PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/localhome/local-rohing/orch_r118_grid_shared_source_20260915_attempt2 python3 -B /tmp/orch_r137_F4_astra_preflight_v1/gpu/orch_r137_grid_astra_switch.py --expected-self-sha256 b1cb939973961cebf5a3c401558cc9c9ae82347ed5dc7b8f90460487cfb44beb'
```

Local regression suite:23 passed. Native read-only snapshot and source-pinned
synthetic consumer probe passed with expected exit3; native system Python lacks
pytest, so a native full pytest run was not claimed.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/mse-release-python-deps-20260915 python3 -B -m pytest -q -p no:cacheprovider tests/test_orch_r137_grid_astra_switch.py
```

R136 diagnostic is paused. No R136 files had been created before the override.

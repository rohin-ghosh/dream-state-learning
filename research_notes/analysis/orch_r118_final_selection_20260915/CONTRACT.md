# Canonical shared FINAL checkpoint selection

Scope: separate evaluation allocation on September15,2026,17:00–17:20UTC,
bounded earlier by each verified lease margin. No old parenting/training quota
is extended or reset. This selector reads no sealed tasks and launches no model.

Main alone runs `wait_select`/`select` and publishes:
`/localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1/FINAL_SELECTION.json`.
Schema: **R118_FINAL_SELECTION_V1**. It is not
`R118_FINAL_SHARED_CHECKPOINT_V1`. No family creates another selection.

Each family uses the pure read-only API in `gpu.orch_r118_final_selection`:

```python
selected = validate_selection(
    common_root,
    config_sha256='e5ac72af0d88e4481174f853fbf3951294278b1c9f62c88080f7d4b816cceb51',
    initialized_sha256='d4e2c87e97bcfccb639d332d996f9f239023bbaa19f9312ce95d30f3f0aecff6',
    adoption_sha256='6dfc7dcd59e86648478a13852ff740701930f36499c92bef1178d3e645dcf7b5',
)
checkpoint_path = selected['checkpoint']['path']
```

`checkpoint` also contains `path_sha256`, `optimizer_path` and
`optimizer_path_sha256`. Other fields include `generation`, `shared_metrics`,
`lifetime_metrics`, `evaluation_deadline_unix`, `lineage_sha256` and the exact
eight-branch roster. The full schema is source-defined. The read-only validator
requires the published selection and the17:00 clock; it cannot create one.
Do not call `select` from family evaluators as a fallback.

Selection binds a separately saved immutable state snapshot. Consumers do not
chase a later mutable STATE. Partial optimizer logs are not committed learning;
a positive generation requires its matching COMPLETE receipt and a checkpoint
completed no later than17:00. If publication/counters/checkpoint/optimizer do not
match, fail visibly rather than guess a replacement. Generation0 is permissible
but contains no shared-learning credit. A selection does not prove that any
FINAL readout ran.

This helper does not stop resident actors, grant GPU custody, waive admission,
reserve model calls or suppress old FINAL execution. Each family must establish
its own exact predecessor release and avoid duplicate partial/completed morning
FINAL reservations before dispatch. The route fuse controls ONLY F1/A1, not the
six other branches. Preserve the original held IDs/decoder and keep all FINAL
outputs/evaluation-attached activity out of sleep and parent/head/exchange inputs.

Selected immutable node source:
`/localhome/local-rohing/orch_r118_final_selector_source_20260915_v2`.
Source SHA256 `64ccee2884b1dddafde70da8ccc2795127c8a4553fb6eb1a301484da369334ed`.
Test SHA256 `c43677672a84f3f8698150830b62e13d16d1c2bb9823502da4a52e25cfc2609c`.
16 local and16 native standard-library CPU tests pass. V1 was never armed;
its native files remain as superseded preparation evidence.

# Read-only adjacent pre/post pointer contract

For Main's separate L2-ADJACENT worker. This does not delay or alter SHORT.
Select FIRST `SHORT/cycle{1,2,3}/sleep/COMPLETE.json` with status COMPLETE and
actual updates>0, in cycle order, without reading any held outcome. UNPARENTED
nonzero sleeps do NOT trigger this selection. If all three SHORT sleeps are
zero-update, no adjacent native diagnostic is authorized by this contract.

## Immutable source and current readout implementation

All remote paths are on the A100 host under the owned root
`/tmp/orch_l2_shared_20260914_attempt1` (read-copy only):

- `COHORT.json`: canonical document SHA256
  `a1746f1c49339da60e9508d82496a257438614af64657fab261f38283c653844`.
  Select `held[cycle]` for the selected sleep, eight worlds/two tasks each.
- `SOURCE.json`: canonical document SHA256
  `920deb00f6d0836f2dc9c2d49e22f260dd76e2bc6ee71fd1b077f37f7bbe261f`,
  file SHA256 `6f5f8811c28bc3ccee94232d628a246f70b604e7ea70be746e3e09536553627d`.
  Exact accepted native EVENT bytes in `store`; verify all collections with
  `organism_v6.orch_l2_shared.verify_source`, but give each child ONLY current
  task/world EVENT subset. Never regenerate source or give source to a parent.
- `LEGACY_READOUT.json`: exact W0/W8 memory and held audit inputs; file SHA
  in `PREPARE_RUNTIME_V2.json.legacy_files['LEGACY_READOUT.json']`.
- `source_runtime_v2.tar`, file SHA256
  `7ccd3c9aa998b54767a64d52090f9654fee9c24dfd41724459c35924ac1c898d`, extracted
  immutable at `source_runtime_v2/`; `PREPARE_RUNTIME_V2.json` inventories every
  Python file. This is the actual SHORT lane snapshot (not mutable HEAD).
- Native neutral readout: `gpu/orch_l2_shared_run.py`, phase `readout`;
  actor `organism_v6/orch_l2_guided.py:episode(...,parent=None,rich_contract=False)`;
  tasks `organism_v6/orch_l2_shared.py:tasks(world)`. System is exact
  `organism_v6.orch_full_rich.SYSTEM`, WITHOUT GUIDANCE, parent messages or
  reflection. Context2048/generation512, six turns; same actual READ receipts,
  two committed routes, action-last parser and legality score. Parent-free
  retention uses old.memory.recall and audit.collect_cases(coached=False).

## Checkpoint schema, populated only after the selected sleep completes

`SHORT/cycleN/sleep/COMPLETE.json` includes:

```
status: COMPLETE
arm: SHORT
cycle: N
updates: actual integer > 0
unchanged: actual boolean (do not select on it)
input_adapter: {path, state_sha256, base_sha256, files: [[name, sha256], ...]}
output_adapter: {path, state_sha256, base_sha256, files: [[name, sha256], ...]}
process: [boot_id, pid, start_ticks]
```

Previous child is `input_adapter.path`; child after sleep is
`output_adapter.path` (normally `SHORT/cycleN/sleep/adapter`). The ordered file
inventory must match each read-copy. `sleep/LOADED.json.observed` records
actual mounted named_parameters LoRA hash BEFORE training; output_adapter in
COMPLETE is accepted only after native.observe_adapter remeasures actual
mounted weights/base and exactly equals the saved output identity. These are
not PEFT-export-name hashes. Both base hashes must be
`a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`.
Initial child, if cycle1, is
`e226cea230b4b970cd5a94cb2b853350aa8bfb95ab4ba69cba3e78ebdd0ad3bf`.
Do not substitute expected names for native remeasurement at sidecar load.

Bind COMPLETE and LOADED file hashes before copying/evaluation. Use separate
fresh processes per previous/output child, exact SAME held[cycle]/EVENT bytes
and neutral implementation. No training, source generation or new family.
Report actual READ→evidence→goal-dependent route paths as well as task counts.
This is a checkpoint-paired diagnostic within one lineage, not independent
training replication, H2 proof, or causal validation of across-stage slopes.

At publication no nonzero SHORT sleep exists yet; dynamic checkpoint pointers
are deliberately NOT fabricated. Worker journal will name the first eligible
immutable receipt when it actually completes.

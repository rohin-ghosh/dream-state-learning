# Fresh audit: warmfix4 prelaunch boundary

Date: 2026-09-13 PT  
Auditor: independent Codex subagent (`warmfix_followup_audit`)  
Audited repair: `cd2b8cea71a42d2af88d145b1d7a9095a7bd5a82`  
Scope: source/test diff, committed native-CPU receipt, attempt-2/3/4
ancestry, and the prospective attempt-5 gate. I launched no model or GPU work.

## Verdict

- **Warmfix4 validator and operator repair: GO.** The evidence-only and
  for-write paths are now genuinely separate. Actual output freshness remains
  mandatory before worker execution; completed output can be checked after a
  fit without trying to recreate it.
- **Existing acquisition: PASS and unchanged.** Every prospective warm arm
  still starts from the original measured A200 receipt. Attempts 2, 3, and 4
  remain terminal failed evidence and none of their checkpoints is eligible.
- **Fresh attempt 5 execution: NO-GO at this snapshot.** The final reducer and
  reducer tests remain uncommitted. Their 12-test synthetic suite reportedly
  passed in 532.070 seconds, but passing uncommitted bytes are not an immutable
  evidence contract. Commit and pin those exact bytes, then independently
  audit the committed reducer before launching attempt 5.

## Exact source and receipt identity

The committed files hash to:

- fit: `563354304444b306b7d1ba210c3dce42a4d9e6c1b1322f239e5256341210c45f`
- outer: `c9f01d41872fc3a890826eff1a5367c847c8e93d02be9d0fa274feb19424f319`
- follow-up operator:
  `ca82b3b2d13023d67b1a3c3e33d4ed951dbb86ff07b271cd710ef8486c1ba849`
- overlay builder:
  `7c69c44bf9253a536ceec9ebe5b081e38dd7e4d421a48563797fccd463ecfaaa`
- native-CPU receipt:
  `bc934349fd19aae76bc9ed53e92156aa57e4bd7f4dd0495be362a874195ff622`
- native-CPU log:
  `a2f62017a63dd7595a44c7f778eeb4117cf94992ef11a2b2308c157b6a742ad0`

Every source/test hash recorded inside the native-CPU receipt matches the
corresponding file in `cd2b8cea`. The receipt records return code 0, no GPU
calls, no scientific fit, and 35 tests passing in 50.673 seconds. Those tests
include real tiny-Qwen2/PEFT CPU warm initialization and the exact mutated
unwrapped caller boundary. I did not repeat the model-bearing test. I
independently ran 77 synthetic/non-model CPU boundary tests; all passed in
33.534 seconds.

## Boundary findings

1. `validate_predecessor` is now evidence-only. It rechecks the sealed A200
   completion, material/model/base/seed/config identity, full immutable parent
   inventory, corpus and train manifest, adapter completeness, base identity,
   LoRA recipe compatibility, nonoverlap, and absence of symlink aliases. It
   never calls `_warm_parent` and does not create or inspect a hypothetical
   child checkpoint.
2. `validate_predecessor_for_write` is an exact small wrapper: call the
   evidence validator, then call `_warm_parent(parent, root / "checkpoint",
   config)`. Therefore the actual destination—not a dummy path—must be fresh.
3. The fit worker's `run_phase` uses the for-write path. The outer controller
   also uses the for-write path twice before spawn: once at input entry and
   again after resource preflight. The outer's post-fit `validate_stage` and
   final `_inputs` replay use only the evidence path.
4. The outer test inserts a pre-existing file at the actual
   `fit/checkpoint` destination between the two pre-fit checks. The controller
   refuses it with `output must be fresh`, never spawns a worker, and leaves
   both child and parent unchanged. The complementary completed-fit test shows
   post-fit validation preserves the completed child and parent inventories.
5. The overlay binds this exact split structurally. For fit source it permits
   only the warm-tensor validator, read-only predecessor body, one exact new
   for-write wrapper, and the single `run_phase` call rename. For outer source
   it requires `_inputs` to remain byte-identical, permits one exact wrapper,
   permits only the first two controller calls to change to for-write, and
   requires the postflight call to remain read-only. Any other AST delta is
   rejected. The frozen original inventory and `material_reexported=false` /
   `original_modified=false` remain bound.
6. PEFT tensor joining remains collision-safe. Both caller trainable names and
   saved state keys canonicalize only the known `base_model.model.` wrapper
   prefix and `.default.weight` suffix. Set/dictionary cardinality checks
   reject either-side collisions before exact coverage; source and initialized
   tensor coverage, SHA-256, shape, dtype, sparse-conversion keys, same-dtype
   equality, and parent inventory are still checked.

## Failure ancestry and attempt-5 preparation

The committed operator recognizes only the exact diagnosed chain:

- attempt 2: preworker/CVD failure, zero fit work;
- attempt 3: worker completed 200 updates and 800 presentations, then the
  exact warm-prefix namespace validator failed; checkpoint ineligible;
- attempt 4 seed 0 only: worker returned zero and completed the same 200/800,
  then the exact outer post-fit freshness error occurred; authoritative outer
  remains failed, no readout, checkpoint ineligible.

It recursively pins stopped/manifest/collection/input/stage evidence, checks
the exact error and release state, rejects missing ancestry and altered costs,
rejects any later readout under a failed attempt, and requires a fresh,
nonoverlapping attempt-5 root. Seed 0 is charged two failed fits / 400 updates /
1,600 presentations; seeds 1 and 2 are each charged one / 200 / 800. All four
new scientific fits remain present and warm branches still name the original
measured A200 parent; there is no recovered-checkpoint input.

The no-model preparation receipt reports four of four pre-fit inputs passing
for each seed, original material identity preserved, and failed checkpoints
explicitly ineligible. This is useful prospective evidence, but it and its
three prepared manifests are uncommitted runtime artifacts and do not override
the reducer gate.

## Exact condition for execution GO

Attempt 5 becomes scientifically authorized only after the current reducer
and its tests are committed, their hashes are bound to the attempt-5 manifests
or launch packet, and a fresh audit verifies the committed bytes still:

- reject recovery/promotion of every failed outer;
- validate the complete attempt-2/3/4 chain and exact failed physical work;
- apply the collision-rejecting PEFT name join and all tensor receipt checks;
- require all four fresh fit/readout branches and raw-response reductions; and
- preserve the fixed descriptive claim boundary.

Until then: **do not launch attempt 5**.

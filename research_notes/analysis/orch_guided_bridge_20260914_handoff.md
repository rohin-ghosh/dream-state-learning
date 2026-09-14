# GUIDED-BRIDGE: explicit CPU state-binding boundary

2026-09-14. Preparation only under Main board d7a7e6f2, published 45becf56.
No global invariant, frozen driver, released helper, claim or promotion gate
changed. Update after reading raw Rohin79 (`36a0a2db`): Main owns family
designation; this contract represents PENDING or MAIN_APPROVED named families
without performing approval or issuing launch authority. No GPU, model call,
actual L2/L3 material, allocation, native launch, result SEQ or paper work.

## Delivered API

`organism_v6.orch_guided_bridge` imports only the standard library and the
released `GoalReplayLayout`; it has no CLI, process launcher or model imports.

- `AdapterIdentity`: canonical absolute directory, loaded-state SHA256,
  frozen-base SHA256, exact immutable relative-file/hash manifest. Verifies
  files by streaming, rejects traversal, aliases, missing/extra/changed files.
- `CallerContract`: explicit named family/status and Main-designation hash
  when MAIN_APPROVED, fixed per-lineage row count,
  presentations, AdamW reset policy, complete AdamW options, learning rate,
  seed and prospective native-protocol hash. No optimizer defaults inferred.
- `ArmLineage` and `plan_cycle`: reconstruct each completed same-arm receipt
  from the common initial state. Cycle is derived from verified history, never
  supplied as an unchecked CLI counter. Only cycles 1–3 are supported.
- `CyclePlan.binding('collection')` and `.binding('training')`: both select
  exactly the preceding completed adapter, not the old quality driver's37ec
  constant. GUIDED+FROZEN selects the initial weights forever and rejects
  training entirely; it is not a loss-off optimizer pretending to be frozen.
- `complete_cycle`: accepts a completed receipt, revalidates prior history,
  and returns the next immutable lineage plus a fresh parent-free readout
  binding to the output adapter. `initial_readout` supplies the before-sleep
  binding. `StageBinding.verify_loaded` checks observed adapter/base identities,
  receipt hashes, parent visibility and, for readout, a fresh process with
  empty transient context and no sleep prompt.
- `project_child_capture`: returns the separately captured public student
  prefix and exact admitted child response bytes, not a cleaned/rewritten
  target. Only declared actual-child-output or child-produced-record origins
  are accepted. Rejects known private guidance in either prefix or target.
- `validate_encoding_boundary`: explicit tokenizer/mask caller boundary,
  using an injected existing `validate_masks` function. Prefix/suffix are
  entirely masked; exact target and EOT remain supervised. Not a new encoder.

Both sleeping arms have their own path and receipt chain. Adapter output is
`<output_root>/<run_id>/<arm>/cycle-<N>/adapter`; all arms, including frozen,
place completion receipts at the adjacent `COMPLETE.json`. Frozen output
identity itself remains the original adapter directory. Common initial bytes
are intentional; later sleeping outputs must not reuse any prior own state
or file manifest. Same-arm/cycle input, output, recipe, plan hash and all prior
receipt locators are checked. A changed prior receipt invalidates later use.

## Prospective caller sequence, not executable native integration

1. Main/next worker publishes the actual protocol and Main's family designation
   while preserving the qualification gates. Bind initial loaded state/base and adapter-file hashes. Keep
   the frozen Qwen2.5-7B-Instruct/one-LoRA invariant; this module does not choose
   or qualify that model. Declare matched arm budgets and actual yield outside
   this adapter bridge; never select from sealed readouts.
2. Instantiate a distinct `ArmLineage` for each exact arm in `ARMS`, sharing
   the qualified starting identity. Bind `CallerContract.recipe_json` to the
   actual native protocol. The protocol hash in unit tests is synthetic only.
3. Obtain `plan_cycle(lineage, contract)`, then its collection binding. The
   new collector must actually load that adapter and independently measure
   its state/base before calling `verify_loaded`; repeating old CLI commands
   is not this step. Preserve actual captures and independent admission.
4. Project only admitted captures whose run/arm/cycle/actor identity matches.
   Hash the original capture, including its public prefix and exact raw child
   output, and supply the complete private-guidance inventory separately.
   Failed or guidance-contaminated rows are rejected, not repaired or filled.
5. For sleeping arms load the SAME input adapter in training. Count actual
   admitted rows against the prospectively declared count; preserve original
   222 legacy rows and their masks. Use `GoalReplayLayout` for the actual
   schedule and original reference-label loss normalization. Roundtrip each
   public prefix, child target, EOT and suffix with the real tokenizer, then
   call `validate_encoding_boundary` with the existing mask validator.
6. Only after a complete fit and saved-file verification, a native caller
   writes the completion receipt. Its exact fields are `schema` (value
   `ORCH_GUIDED_BRIDGE_COMPLETION_V1`), `status` (`COMPLETE`), `plan_sha256`
   (`document_sha256(plan.document())`), `run_id`, `arm`, `cycle`,
   `input_adapter`, `output_adapter` (both `AdapterIdentity.document()`), and
   `contract` (`contract.manifest(arm)`). `ReceiptRef.sha256` hashes exact file
   bytes, NOT the canonical document hash. Frozen completion attests no fit
   and the unchanged starting adapter. This module never writes receipts.
7. Call `complete_cycle(plan, receipt_ref)`. Consume its returned readout in
   a genuinely fresh evaluator, with no parent/sleep prompt/conversation.
   Check observed identities/context through `verify_loaded`. Keep the
   returned lineage for the next plan. No metric interpretation is provided.

## Dose and optimizer decision

Tested policy is **RESET_EACH_CYCLE**, not optimizer restore: fresh AdamW each
sleep, continuing adapter weights. This matches the original266 lifecycle and
the available adapter-only stage endpoints. All six sleeping-arm transitions
in the synthetic three-cycle test bind that explicit same reset recipe.
Optimizer checkpoints are explicitly `None`; restore requests fail closed.
Frozen uses `NONE`, zero updates and zero training presentations. The bridge
tests declarations and receipt consistency, not a real optimizer instance or
exact numerical/mid-fit recovery. Native AdamW creation still belongs to caller.

For1452 new rows: FOUR presentations =>2928 four-slot updates and5808 new-row
presentations; SIXTEEN =>11712 updates and23232 new-row presentations. The
declared layout and **executed** frozen counts are separate. No exposure or
token-equality claim is manufactured for frozen. No hidden dose adjustment.

## Existing APIs inspected and native obstacle

`experienced_event_goal_quality._world_quality` already copies the captured
public `student_prefix` and raw child response. The bridge preserves that
policy; it does not call fixed-source `source_plan`, instantiate worlds, or
apply rich action projection to delete text from training targets.
`experienced_event_rich_trajectory.project_action` is an exact executable
action-span parser, not permission to scrub parental target contamination.

`astra_goal_quality_train.encode_new_rows` remains coupled to1452 rows and
the fixed collector/native object graph; `load_inputs` still requires37ec.
The boundary reuses the released layout and tests the existing
`astra_reader_audit_lesson_train.validate_masks` through injection. It does
not pretend to integrate native variable-row tokenization/training. The new
native caller is the obstacle: collector/trainer observed-state loads,
variable-row exact tokenizer roundtrips/reference normalization, actual
completed receipts, and clean fresh readout still need an explicitly published
protocol and implementation by Main's next worker (not Main executing cells).

## Tests, assumptions and falsification

CPU tests use only temporary synthetic byte files and toy captures. They are
not a behavioral corpus, generated child targets or a new dataset. They cover
nine completed cycles across three arms, six distinct sleeping output paths,
frozen identity, same-state collector/trainer and output-state fresh readout;
foreign/stale/incomplete/tampered receipts, wrong cycle/path/base,37ec reset,
manifest alias/tampering, recipe drift, parent leakage, exact byte projection,
prefix/EOT/suffix masks and released-layout dose integration. A subprocess
forbids torch/transformers/peft/safetensors imports, including mask-helper import.

Run: `python3 -m unittest tests.test_orch_guided_bridge tests.test_experienced_event_goal_replay_layout tests.test_astra_goal_quality_train -v`.
The initial10-second combined invocation timed out after bridge/layout tests;
its partial log is retained. The longer invocation passed36 tests (20 new,
7 released-layout,9 frozen-driver). The final bridge-only recheck follows the
explicit clean-readout-context addition; see the separate final recheck log.

Limits/falsifiers, not claims hidden by green tests:

- Metadata hashes cannot authenticate the actor, recompute a model's loaded
  tensor-state hash, prove the base is frozen, or prove a process is fresh.
  Native code must measure rather than echo the expected binding. A caller
  ignoring this API, fabricating receipts or restarting at cycle1 can still
  fake continuity; there is no supervisor/authentication stack here.
- Public-prefix origin and semantic/grounding admission remain upstream.
  Exact matching catches inventoried private strings and the known guidance
  marker, not every paraphrase or unreported secret. Accepted/child-origin
  metadata is not evidence of actual child authorship or semantic truth.
- Native text-to-token roundtrip and legacy-reference normalization are not
  established by a toy mask test. Failure at either native boundary blocks
  use; do not repair targets or call this a learned compiler.
- This minimal contract fixes row count/dose/recipe across one arm's three
  cycles. Different arms can declare differing actual yields prospectively,
  but a later mismatch/zero yield stops; no silent truncation, padding, target
  sharing or dose adaptation. Variable-per-cycle yields require a separately
  explicit caller-contract extension, not relabeling this implementation.
- A numerically unchanged sleeping endpoint is rejected as stale/reset, even
  if a future genuine fit could produce no change. It cannot count as a new
  evolving state through this boundary. No improvement, unseen-family, H1/H2,
  promotion, independent review or statistical result follows from these tests.

Compute recommendation: zero additional GPUs for this bridge. Do not hold
node3 reserve0/1/5. Continue independently authorized work; actual loop launch
requires Main's family designation, child qualification and a separately bound
native protocol. No further Rohin family-permission gate is imposed here.

Peer message to Main/next native worker: consume both collection AND training
bindings, not just AFTER adapter reload. The old quality runner is untouched
and still cannot provide continuity by repeated invocation. CPU boundary is
ready for review; native integration and all launch decisions remain yours.

## Message79 correction and frozen loader seam

The first patch only accepted the then-pending route-family proposal. After
reading raw message79 and Main's follow-up, named families may instead carry
`family_status='MAIN_APPROVED'` and `family_designation_sha256` for Main's
published designation. This helper neither reads a registry nor authenticates
Main's decision; it binds caller-supplied metadata. There is no
`launch_authorized` field, only `execution_scope='CPU_PREPARATION_ONLY'`.
The designation is frozen into the plan/receipt just like the native recipe;
changing it beneath an existing lineage fails. It should be settled before
native cycle1, not retroactively substituted into old receipts.

Public loader seam is frozen in `orch_guided_bridge_INTERFACE_V1.md` beside
this handoff. Old Builder's disjoint `orch_guided_native*` paths remain untouched.
Coordinate through Main only. The substantive next work is actually loading
and measuring the requested adapter, not another registry. The authority-fix
test log records22 passing bridge CPU tests; previous logs remain historical.

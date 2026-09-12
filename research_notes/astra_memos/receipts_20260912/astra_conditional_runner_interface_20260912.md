# Proposed conditional runner/readout interface — 2026-09-12

**PROPOSAL ONLY / EDIT-STOP. No implementation, launch, network, Git, or repository edits.**

## Starting point

Consume Main's already prepared node3 `~/astra_diagnostics/astra_conditional_behavior_20260912_attempt2/material` unchanged. Do not reconstruct default preview labels or overwrite attempt1. Main reports native audit PASS with actions `(dax,wug)`, outcomes `(fep,nup)` and source commit `5f6e1f1d217dcdb15176dc84b9ac34ec960c48de`. This task inspected local source interfaces, not the remote receipt bytes.

Main-provided file SHA256 pins:
- candidate: `5d1644b90ff7621ee121aba65be7dd7cae7f15168f5a3c3a09a1bc9aa9a7af8c`
- AUTH: `344ec17779696b184468d96ce26ef89e8d3bd0cb5b8dbfde84a4b8dc1c437d48`
- DERANGED: `060255b11551b55b20d39f91301cc4e0362134af321bc740134b86e3ca6d511d`

Per arm: 11248 total nonpadding input tokens /1888 supervised target tokens per epoch; four epochs =44992/7552. Both fits together =89984/15104. Total input includes target+EOS; these are processed training counts, not readout costs or caps. Validate against actual fit manifests.

## Smallest implementation scope to allocate

One new `organism_v6/conditional_behavior_readout.py` plus its CPU tests. It holds the thin conditional plan/CLI, request construction, reduction, control registry and HF scoring adapter loader. Keep existing corpus/trainer/capture/supervision modules unchanged. Main can retain its ordinary small fit-launch script; no new orchestration framework or guard.

Proposed phases/interfaces (names are not implemented commands):

1. `prepare(material, out, model, controls, generation_settings)` — verify the three files and existing native audit/recipe; freeze exact requests, control bytes/keys and teacher-forced orientation before outcomes. No model calls.
2. Main's two ordinary v3 fit invocations — fresh AUTH and DERANGED adapter directories from the same frozen base, seed0, caller-selected LR1e-4, rank8/alpha16/dropout.05, four epochs, batch4/accum1, no packing, no warmstart; retain shared groups and EOS. Exactly128 steps per fit,256 total. No in-readout training or follow-up writes.
3. `prepare_state(plan, state, adapter)` and `generate(state_plan)` — fresh process for each of OFF/AUTH/DERANGED, one adapter at most, no feedback/history. OFF has no adapter and is shared across both comparisons, never duplicated as independent evidence.
4. `score_candidates(state_plan)` — separate fresh HF process per same three states, same base and saved adapter bytes, eval/inference mode. Complete candidate likelihoods only; no gradients.
5. `reduce(plan, captures)` — CPU-only complete-ID checks, raw scoring, paired interactions, controls and cost tables; missing phase means INCOMPLETE, not a scientific zero or L1 PASS.

Bind all state adapters to their fit manifest and actual serialized files. Verify DONE,128 items/encoded rows,128 steps, zero skips/nonfinite batches/truncation/splitting, recipe, corpus file hash and processed tokens. Existing `gpu/astra_parent_wake_diagnostic.py:156` (command) and `:201` (manifest verification) are patterns only: their32-row/96-step/three-epoch constants cannot be reused unchanged.

## Existing reuse: exact boundary

- **Direct generic generation capture:** `organism_v6/fundamental_teaching_readout.py:142`, `capture(plan, path, factory=None, closer=None)`. Despite its module name, this function iterates supplied `requests`/`native_inputs`; it never uses `CASE_IDS`. Supply `model`, `adapter`, `identity`, `model_files`, `adapter_files`, `requests`, `native_inputs`. It records raw text and actual IDs, enforces prepared input equality, closes the owned backend and writes usage/manifest.
- **Do not reuse its fixed wrappers:** `selected_cases`, `requests`, `prepare`, `verify`, `worker`, `run`, `reduce` bind the old48-case corpus or worker module. In particular, do not monkeypatch `CASE_IDS`. New conditional wrappers select exactly the prepared candidate's128 train plus64 dev IDs.
- Generation backend/identity: `organism_v6/rulegame_parenting_diagnostic.py:294` `NativeBackend`, `organism_v6/model_backend.py:13` `configured_generation_identity`; validation/usage at `rulegame_parenting_diagnostic.py:283/:503`. They accept arbitrary prompt strings. Its RuleGame replay/check_capture/material functions are not generic and must not be called for this panel.
- **Reuse supervision, not a new guard:** `rulegame_parenting_diagnostic.py:715` `supervise`, as already used by fundamental readouts; group cleanup lives in `organism_v6/run_reasoning_neutral.py`. Important existing limits:600s worker,180s load,120s individual call,1800s aggregate under the supplied root. Use separate state/phase roots, and predetermined panel splits if Main's budget needs them; do not silently extend limits or monkeypatch globals. Main retains allocation and full-device release checks. GPU runtime is not estimated from token counts alone.
- **Direct generic teacher-forced kernel:** `organism_v6/semantic_carrier_diagnostic.py:332` `score(torch, model, request)` accepts arbitrary two complete encoded candidates and an input-only prefix. It performs causal next-token indexing, shared-prefix checks, future-only aligned padding and returns actual per-token logprobs. Reuse this function, not its fixed compiler-action `encode_candidate`, material/preflight, execution or reduction wrappers. Validate explicit EOS/prefix construction in the new wrapper; the kernel checks shared terminal IDs but the wrapper must bind the real tokenizer EOS.
- `organism_v6/multikey_writer_gateway_simple.py:1253` is **not** a drop-in scorer: `score_request` calls fixed `token_pair`/`CANDIDATES=(ACT:a0,ACT:a1)`. No need to change that module.
- Existing `conditional_behavior_corpus.py:586/:641` supplies generation scoring and common-input candidate interface. Keep those executed source bytes unchanged.

## Primary generation and teacher-forced accounting

Use all128 training inputs and all64 dev inputs in each of three states: **576 primary generations**,192/state. Shared OFF responses are scored against AUTH and DERANGED maps separately; they are still192 actual calls. Preserve exact raw strings, all invalid/capped calls, case/source IDs, strict surface, component/joint semantics, own-map exact score, all four twin families and strata. Training readout is in-sample diagnosis, not held transfer. Generation settings should be fixed before calls (proposed temperature0, seed20260912,64-token cap); actual output IDs determine cost, not576×64.

Teacher forcing on the64 dev cases: two complete continuations/case/state =384 candidate forwards, or192 two-candidate scoring requests. No train likelihood sweep is necessary for the first test. Include EOS and sum supervised token logprobs (do not length-normalize); retain native prefix/continuation IDs and per-token scores. Input must be the same rendered user prefix plus empty assistant stub, never an answer-bearing gold PREDICT/COMPARE prefix.

Fix interaction orientation before outcomes. For each PROSPECT belief pair or REVISE outcome pair, let A be AUTH's complete target at the first endpoint, B its target at the second; verify the exact strings swap across endpoints. Compute `I = [logP(A|x0)-logP(B|x0)] - [logP(A|x1)-logP(B|x1)]`. Report all16 values and the predeclared mean per operation/state; ≥1nat is the proposed operation aggregate, not a favorable selected pair. AUTH-oriented sign is positive, DERANGED's own direction negative; report both orientations and OFF. Do not subtract two dynamically relabeled AUTH-minus-DERANGED odds without accounting for the swap: that changes the contrast. Other twin families are generation diagnostics, not post-hoc replacement primary interactions.

HF and vLLM must use identical prepared prefixes and serialized base/adapter states; neither token matching nor generation agreement establishes full-logit backend parity.

## Controls: small explicit registration still needed

The executed conditional material has **no actual locality/copy panel**: its composition/teacher-forcing interfaces are declarations, not control cases. This is a concrete remaining preparation item, not a reason to change the fits/corpus. Freeze a small JSON control registry before readout; never select controls after seeing outcomes or count missing controls as passes.

Minimal proposed32 control requests/state:
-16 no-phase ordinary-task inputs: reuse exact `eval-addition-000` through `eval-addition-015` records from `fundamental_teaching_corpus.build_candidate()['eval']`, preserving source IDs/keys. `addition_context` at line69 requests ACT only. Score integer task correctness, legal ACT, invalidity and unwanted PREDICT/COMPARE/POLICY/NEXT tags. These are known diagnostic items, not fresh confirmation or proof of preserving the old learned habit.
-16 unrelated interface/copy requests: the existing `semantic_carrier_diagnostic.build_items()` `native_action_copy` records are available unchanged, eight fixed action spellings across two source roots. **They have only eight unique prompt strings**, so report8 unique inputs/16 executions, not16 independent tasks. Score literal one-line ACT copying and tag spill without invoking CompilerGym or claiming executable compiler performance. If Main requires16 unique interface inputs, it must instead approve16 distinct literal copy bytes before calls; do not silently deduplicate or invent a registered panel.

This proposal makes **672 total generation calls** including96 controls, plus384 teacher-forced candidate forwards. Main must explicitly accept the exact registry (particularly the duplicate-copy scope) or substitute an already registered panel; counts then follow its actual fixed length. Control families are reported separately; no aggregate can mask a failed locality family. With16 rows, a .05 absolute drop permits zero lost successes; with8 unique copy items the corresponding unique-item bound likewise permits zero. Copy/interface carriage is not arbitrary task competence.

## Readiness, limits and effort estimate

Proposed first useful generation slice: **30–45 minutes of implementation/CPU tests after allocation**, reusing the capture function, with fit orchestration left to Main. Complete common-input likelihood wrapper, control registry, exact threshold/interaction reductions and mocked failure tests: **another30–45 minutes**. Total CPU implementation estimate60–90 minutes; excludes GPU runtime/native qualification and assumes the control registry is accepted. No model/run-duration guarantee.

Tests should cover full panel cardinality/shared OFF, no fixed fundamental-ID selection in primary requests, exact material/adapter links, causal candidate indexing/EOS, pair orientation, control parsing, missing captures, cap-vs-native usage and existing supervisor failure propagation. No extra framework.

Root0 is one original material/optimizer seed, not three replications. Report primary results as partial until interactions and locality/copy are complete. Even a complete passing root0 panel only qualifies progression to the prescribed unchanged roots1–2; it is not full all-root L1, composition, H1, child-experience/clean-lineage, or general plasticity. Preserve literal31/32 strict validity,116/128 own-map,14/16 twins and per-stratum bounds; do not call30/32 “95%”.

**Await Main's scope allocation; no implementation performed.**

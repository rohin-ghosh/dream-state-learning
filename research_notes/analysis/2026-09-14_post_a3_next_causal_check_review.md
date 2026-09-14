# Post-A3 review: original SEQ239 checkers on identical captured stimuli

September 14, 2026. Bounded design/code-path review; no native execution.

## Verdict on Main's selected comparison

**Informative and feasible as a zero-fit, fixed-stimulus transfer diagnostic.**
Use exactly the original SEQ239 `AUDIT_SFT` and `AUDIT_LOSS_OFF` checkpoints,
each on A3 attempt2 BEFORE's eight faulty-reader prompts followed by
SELECTED AFTER's six accurate-reader prompts: **14 calls per arm, 28 total**.
I find no concrete design reason to reject this comparison within that claim.
Do not add another sleep, prompt variant, descendant control, or extra bank.

This removes the different-reader-stimulus confound of SEQ240 for these
captured inputs. Returning to the original SEQ239 pair also avoids SEQ241's
common 62-row audit-lesson supervision of both repaired descendants. A
difference in their fresh outputs would inform transfer of the original
taught checking behavior to this fixed A3 packet. It would not establish
useful selection, improved learning, or either evaluator's own on-policy
auditing behavior.

**Design endorsement is not approval of an implementation I have not seen.**
Kant owns the new runner/tests. At this inspection, no dedicated selector-
transfer runner/test file was present under the searched transfer/audit paths.
The native interfaces and necessary fail-closed checks below are concrete;
their implementation and CPU qualification remain with Kant/Main. Nothing
in this review launches, gates, or delays Main's work.

## Scoped A3 evidence inspected

Local capsule:
`gpu_artifacts_local/astra_fresh_reader_cycle_terminal_20260914_attempt2/extracted/`.
Its recorded source commit is
`8e520bc5b359163b2e54d70d39f317d0ab914102`.
I inspected the three actual-audit bundles and their stage metadata, not the
full training schedule, adapter inventory, or primary reducer.

| Packet | Actual calls | Distinct model-visible prompts | Truth stratum | Existing descendant audit |
| --- | ---: | ---: | --- | --- |
| `before/ACTUAL_CASES.json` | 8 | 4 | 8 fault, 0 true | 8/8; choices `[1,0,1,0,3,2,3,2]` |
| `SELECTED/after/ACTUAL_CASES.json` | 6 | 4 | 0 fault, 6 true | 6/6; no admitted pointer |
| `UNIFORM/after/ACTUAL_CASES.json` | 6 | 4 | 0 fault, 6 true | 6/6; no admitted pointer |

These existing outputs belong to later descendants, **not** the original
SEQ239 evaluators. They are context for freezing the input packet, not
predictions or substitute responses for the proposed runs. Native AFTER
`chosen_source_indexes` is six null entries, not six selections.

SELECTED and UNIFORM AFTER `ACTUAL_CASES.json` files are byte-identical.
Using SELECTED AFTER therefore follows the declared chain without choosing
the more favorable stimulus set. It also avoids six redundant prompts per
evaluator. Keep both original capsule arms intact; do not delete duplicates.

A3 source indexes identify:

| Index | EVENT | BEFORE invocation positions | SELECTED AFTER positions |
| ---: | --- | --- | --- |
| 0 | `E_OBOXFV6WG4` | 1, 3 | 1 |
| 1 | `E_BF3K34VYXU` | 0, 2 | 0, 2 |
| 2 | `E_PRS7JYHK37` | 5, 7 | 4 |
| 3 | `E_LT27MCC2IZ` | 4, 6 | 3, 5 |

Positions are zero-based within each packet. Every BEFORE reply preserves
the requested EVENT but has **all four node/port/outcome/receipt fields
wrong**. Every SELECTED AFTER reply has all five fields correct. The same
source table and requested addresses occur on both sides of this true/fault
contrast. Always returning the address or always returning `NONE` cannot
pass both strata.

BEFORE tasks 2/3 end `invalid_route` after real memory reads. There are eight
auditable reads and no unavailable reader captures. Those reads must stay
in scope; a valid eventual route is not a prerequisite for inspecting text
that was actually returned. Do not reconstruct a missing transition. This
is why the capsule's fresh-reader audit V2 helper, rather than the original
committed-route helper, matters.

The collection metadata still names
`/tmp/astra_fresh_reader_cycle_20260914_attempt1/collect` as its original
output. Attempt2 reuses that completed collection and reruns BEFORE after
the audit-wrapper repair. Preserve this lineage; do not describe attempt2
as an independently recollected bank or pool attempts as independent data.

Packet anchors, computed only for these scoped inputs:

| Packet | File SHA-256 | Embedded `cases_sha256` |
| --- | --- | --- |
| BEFORE | `a172b541c68c4bf7e7d02c9d167be85e760ea382a52305d5af7d5cc534cb573a` | `41e4372fb5908060ae6c7ad07af923229ca964014cbe0ac8d7db8b29d06d9c1f` |
| SELECTED AFTER, also UNIFORM AFTER | `650986b109af67b6b52a863891587e01e8f05ddd7a6d33e39acdab1368f7a761` | `c6e4174a19d5fefc1122d12e9e29ffa8a5148800d29263cfd1dd00298da82db3` |

File hashes and embedded canonical-document seals are different types of
binding; do not substitute one for the other.

## Exact evaluators: original SEQ239, not repaired descendants

Native checkpoint directories:

- `/tmp/astra_reader_audit_lesson_20260914_attempt1/AUDIT_SFT/train/adapter`
- `/tmp/astra_reader_audit_lesson_20260914_attempt1/AUDIT_LOSS_OFF/train/adapter`

Both complete train directories are also preserved locally beneath:
`gpu_artifacts_local/astra_reader_audit_lesson_independent_20260914/terminal_saved_adapters_20260914/files/`.
Append `AUDIT_SFT/train/adapter` or `AUDIT_LOSS_OFF/train/adapter` respectively.
The neighboring `RESULT.json`, `REQUEST.json`, `ADAPTER_PROVENANCE.json`, and
training receipts identify the original 200-update treatment/control pair.
Both local adapter directories are present. Remote availability was not
rechecked during this local-only review.

| SEQ239 evaluator | Recorded tensor-state SHA-256 | Previously preserved weight-file SHA-256 |
| --- | --- | --- |
| AUDIT_SFT | `db3f213b0040ac92dbc45ab8373bf4a0c55185d4eb23a3fca781f0bf89b431c5` | `5b7c422dc3b61cbfc4b51363f2aef2ab3b4edb6b6bee680d10dda0c172ea5fcb` |
| AUDIT_LOSS_OFF | `42c8a7e212945dd71035d13655bbfc04214a51f17bf8baf969909961b0556684` | `f9275b58be20c3a2900a3d3e61fbbb806498f8b788ada6481b7ec606e76fe43b` |

These identities are read from preserved train receipts and the completed
SEQ239 preservation memo; I did not reload tensors or repeat weight hashing.
The eventual runner must verify the files and loaded state itself.

The original paired lesson loader's common baseline is:
`/tmp/astra_adult_cycle2_20260914_attempt1/CUE_REPLAY/corrective_sleep/CHILD_CORRECTIVE/after`.
Its shared lesson collection is:
`/tmp/astra_reader_audit_lesson_20260914_attempt1/collect`.
Those supply the original load/provenance context, **not** the A3 stimuli.

Explicitly exclude checkpoints under
`/tmp/astra_selected_reader_repair_20260914_attempt1/` and the A3
`SELECTED/train` or `UNIFORM/train` directories as evaluators. The former
OFF descendants already receive the later 62 lesson rows; the latter are
descendants of the taught SFT-selected chain, not the original control.

## Separate stimulus provenance from evaluator provenance

The A3 collection and BEFORE routing/reader producer is the SEQ241
SFT-selected descendant, recorded state
`48dc1d6d77852bddba75e04ee7442f4ef2a8e72bce5719d39ade4ed974a2b042`.
SELECTED AFTER's producer is recorded state
`207ad43ef65f1f6ba7c50d37f5d5dfa8c2253d1cb301e585d7b6b7a78bb93990`.
Neither is either proposed SEQ239 evaluator.

The appropriate designation is **counterfactual, cross-checkpoint selector
evaluation on replayed actual-reader stimuli**, with new native classifier
outputs. The underlying reader strings really are captured actual outputs;
the relationship to the evaluated selector is off-policy/counterfactual.
The authentic A3 experiences belong to the recorded A3 source actor, not to
the older evaluator simply because it is shown their source table.

Retain each immutable input bundle and its original case/trace/response/
collection hashes. Use a separate run envelope containing at least:

- Evaluator arm, exact original train receipt and loaded adapter identity.
- Stimulus phase and producer identity, original collection lineage and
  packet file hashes/seals; explicit cross-actor, not-own-on-policy labeling.
- Ordered `(packet, case_index)` identifiers and shared model-visible
  prompt-list digest, identical across both evaluators.
- Native output captures with terminal/error flags, strict correctness,
  source admission and the input case they answer; `fits=0` and unchanged
  base/adapter checks.

Do not overwrite producer identities, relabel the A3 episodes as SEQ239
episodes, or weaken existing own-AFTER checks to make an old CLI accept them.
Keep labels, `kind`, expected outputs, phase names, lineage metadata and the
other evaluator's outputs **outside the model messages**. Each call receives
only its captured neutral system/user messages in a fresh context. The
receipt-grounded source table is explicit evaluator scaffolding, not a
parent turn or a test of parametric recall.

## Existing reusable interfaces and the necessary new boundary

The five referenced helper/driver files below match their frozen A3 capsule
copies at inspection. Source references use the current matching paths;
the frozen counterparts are under the capsule's `source/` directory.

| Interface | Reusable behavior | Boundary to preserve |
| --- | --- | --- |
| `organism_v6/experienced_event_fresh_reader_audit.py:28` `_replay_route` and `:81` `build_cases` | Pure replay of all actual routes/reads; builds exact neutral prompts and source bindings, including invalid routes | Authenticate the original A3 producer separately; do not fabricate transition outcomes or reader text |
| `organism_v6/experienced_event_fresh_reader_audit.py:144` `collect_audit(cases, generate)` | Revalidates a complete bundle, invokes a supplied callback, retains all responses and duplicate/wrong source pointers | Call separately on the eight-case and six-case bundles; it is not an existing 14-case merged-bank interface |
| `organism_v6/experienced_event_actual_reader_audit.py:70` `_score` | Existing exact-output scoring and independent source-table admission | Only expected bare address/`NONE`, optionally one LF; no substring or format salvage |
| `gpu/astra_reader_audit_lesson.py:89` `checked_training` | Binds an original arm's completed 200-update training receipt, lesson/provenance and adapter files | Reuse original baseline/lesson context; do not swap in later repaired training receipts |
| `gpu/astra_experienced_event_microloop.py:114` `Engine`, `:162` `verify_base`, `:168` `generate` | Native offline loader, bounded greedy inference and frozen-base verification | A new runner still needs explicit original loaded-state binding and end-of-run adapter-state equality |

The old SEQ239 `actual` entrypoint is **not directly suitable**:
`gpu/astra_reader_audit_lesson.py:107` `actual_cases` requires an AFTER from
the same actor/arm/training and uses the older actual-audit construction.
Likewise `gpu/astra_fresh_reader_cycle.py:74` `read_collection`, `:85`
`read_before`, and the native state check at `:195` bind the A3 actor chain.
Its CLI has no arbitrary evaluator-on-captured-packet mode. Those safeguards
are correct for their existing jobs; leave them unchanged.

Kant's separate runner can compose the pure A3 replay/scoring with the
original SEQ239 checkpoint loader and native engine. The new run schema must
carry the cross-actor boundary rather than inheriting an unqualified
“own-reader” claim from a convenience wrapper. No new model, prompt,
classifier rule, fault generator or fit interface is needed.

## Bounded native-readiness checklist for the new runner

1. **Freeze before calls.** Bind original checkpoint/receipt identities and
   both packet hashes; replay/compare each packet against its collection and
   routing captures. Require exactly 8 and 6 cases, no omitted actual reads,
   and identical ordered prompts in both arm preparations. Preserve attempt1
   collection ancestry and attempt2 invalid routes without inventing commits.
2. **Use the original pair only.** Reject wrong arm, later lesson-trained
   descendants, wrong file hashes or loaded tensor state before any
   classifier call. Do not require evaluator identity to equal producer
   identity; require both identities to be separately correct.
3. **Exactly 14 isolated calls per arm.** BEFORE 0–7 then SELECTED AFTER
   0–5, same order in both arms, no coaching or previous answers in context.
   Keep the existing 2048-input/160-output token bounds, greedy generation,
   exact terminal handling and no retries/best-of. Call the existing bundle
   collector twice. Its eight-read limit is per bundle, not a reason to
   truncate the combined 14-call run. Capture names/IDs must distinguish
   the two bundles' repeated local case indexes.
4. **Fail without erasing evidence.** New exclusive output directory,
   per-call raw capture including exceptions, no replacement answers, no
   missing/extra-call completion. Preserve attempted failures and return
   an incomplete/failed run if native execution or final integrity checks
   fail. Never silently score missing outputs as a completed denominator.
5. **No state-changing path.** No trainer/optimizer, memory write, routing
   rollout, synthetic source generation, or automatic fit from selections.
   `fits=0`, evaluator adapter state identical before/after, frozen-base
   verification, offline model loading, and a finite runtime/call cap.
6. **Regression cases to cover.** Drift in a captured prompt/response or
   source bundle; substituted checkpoint; swapped producer/evaluator labels;
   invalid-route reads retained; wrong valid pointer admitted but scored
   wrong; malformed pointer never rescued; NONE remains unselected; duplicate
   calls retained; no model import/load during preparation; state drift or
   partial failure cannot yield a valid completed result.

Existing test coverage to reuse includes
`tests/test_experienced_event_fresh_reader_audit.py:74` (invalid-route reads),
`:128` (missing/fabricated transitions), `:140` (trace drift), and `:171`
(captured audit replay/failures), plus
`tests/test_astra_fresh_reader_cycle.py:501` (prepare without native loading)
and `:636` (wrong loaded actor). These are inspected code paths, not tests
run by this review, and do not replace tests of Kant's new boundary.

## Prospective reporting and concrete limits

Keep the declared per-arm **8-fault / 6-true / 14-total** strict counts and
paired SFT-minus-OFF differences. Also show every matched raw output and
separate errors into invalid pointer, valid-pointer false positive, wrong
valid address, fault abstention, and native call/termination failure. Report
source admissions separately from correctness: a wrong-but-source-valid
pointer stays admitted and wrong; do not use it to manufacture utility.

The 14 invocations are only **eight distinct prompts, four addresses with
one true and one fault stimulus each**. Retain all calls and report their
alias mapping; do not claim 14 independent samples. A compact secondary
per-address table can show whether both the true and fault prompts are
answered correctly, without replacing the invocation denominators or
assuming duplicate responses must agree. True calls weight sources 1/3
twice and 0/2 once; fault calls weight each source twice. Stratum counts and
the per-address table prevent a pooled 14-call score from hiding that fact.

Concrete limits, none fatal to the selected question:

- **Ceiling and fault breadth:** all faults alter four body fields, while
  all true cases are exact full tuples. This cannot test subtle receipt-only
  or node-only discrimination. If both original checkpoints reach ceiling,
  there is no detectable treatment advantage on this packet—not proof that
  the original lesson had no effect anywhere. A positive difference supports
  only the observed kind of transfer; invalid-to-valid gains still require
  their format/decision decomposition.
- **Conditional causal scope:** SEQ239's matched comparison changes audit-
  target loss on the successful captured lesson responses, not every aspect
  of parenting. Fixed prompts remove the contemporaneous reader-output
  confound, but the A3 packet was produced by a taught descendant in one
  chosen task family. It is not a randomized population sample of faults or
  an independent on-policy test for the original control. One paired
  checkpoint contrast cannot establish a general treatment effect.
- **No selection-usefulness contrast:** BEFORE selects all four facts, each
  twice; UNIFORM also covers all four. There is no omitted-fact or sparse
  prioritization contrast here. A3's successful writes and this proposed
  no-fit classifier comparison cannot establish better downstream selection
  utility. A pointer into the externally supplied A3 table also does not
  become the older evaluator's own remembered experience.
- **No measured prospective effect yet:** A3 descendant 8/8 and 6/6 do not
  determine the original pair's outputs. Do not import their answers, claim
  efficacy, or declare an original-pair result before new native captures.

**Recommendation:** proceed with Main's chosen comparison once its new
runner is bound and CPU-qualified by its owners; no broader alternative or
additional fit is recommended in this review. The most defensible result
statement will be “original taught versus loss-off checkpoint on identical
captured A3 reader-check prompts, zero fits,” with actual-stimulus provenance
and counterfactual evaluator provenance both explicit.

Only this new memo is written. Prior released memos, primary reductions,
shared notes, code, adapters and other workers' changes remain untouched.

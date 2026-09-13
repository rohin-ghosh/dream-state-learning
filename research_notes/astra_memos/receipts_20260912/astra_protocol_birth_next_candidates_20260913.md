# Two minimal prospective birth-data deltas — ready queue only

Read-only design, not implementation, fit approval, or a selection from unread probe
outcomes. Exactly TWO alternatives below, not a combined curriculum or factorial.
Current16-case/32-call probe remains frozen. All historical birth/source artifacts,
graders, parent visibility, native selectors and runtime remain unchanged.

## Common smallest paired overlay proposed here

Start from `birth_conditional_corpus.build_candidate(root=0)` (256train/128dev).
Retain ALL64 PROSPECT +64 REVISE AUTH rows, byte-identical contexts/targets, original
source IDs, group/order and four presentations at epochs4. Do not translate their
opaque labels into RuleGame labels: the semantics are different, not mere aliases.
Both proposed arms share this same AUTH conditional background, including every
belief/goal/expected/observed/prior factor and original twin support.

Replace only16 anchor rows with16 bridge rows: eight pairs in eight existing groups.
Precisely, for k=0..7 choose zero-based group g=4*k; replace order4+(k%2) (ADDITION)
and order6+(k%2) (COPY). Each replacement pair stays in its original eight-row group.
This removes anchor indices0,9,16,25,32,41,48,57 in EACH family; no outcome selection.
Remaining anchors are56 ADDITION +56 COPY, with28 examples of each train template.
Unselected240rows stay unchanged. Final counts:128 conditional +112 anchors +16bridge
=256rows,32groups,128updates at4epochs,64bridge presentations per fit.

This preserves conditional example dose, NOT original locality dose: each anchor
family falls256→224 presentations/fit (12.5% less). This explicit tradeoff avoids
appending examples or increasing optimizer steps. Longer targets can still dilute
conditional gradients/change padding and token exposure; preserved rows do not
guarantee preserved learned behavior. If Main requires every original anchor and
its dose too, this fixed256-row overlay is not the right design; do not hide additions.

Control for either alternative: `BRIDGE_AUTH` versus `BRIDGE_DERANGED`, both fresh
base fits. All240 background rows use ORIGINAL AUTH targets in BOTH arms. Only the
new paired bridge targets are swapped as specified below; input contexts/groups
are identical. Do NOT reuse the original full DERANGED arm, which would also break
the conditional background and confound the narrow bridge comparison. These names
are new proposed data-arm labels, not permissions to relabel existing receipts.

## Candidate A — serialization/state bridge, not rule learning

Use this alternative only if Main interprets the closed probe as a protocol/format
gap. Change output-form coverage; do not add a hidden-rule-learning objective.

Source templates/specification: `rulegame_parenting_diagnostic.parse_action`, BOOT,
`record_prompt`, `record_instruction('interaction_v3')`, `judge_record`, and the
existing protocol material's `_context`/`_target` as reference renderers (private,
not a general training API). `RuleGame.evaluate/quiz_triples` supply authored public
observations/reveal text where needed. Whole targets contain no appended world reply.

| Replacement groups k | New AUTH examples and public-input → target contract | Narrow control |
| --- | --- | --- |
| 0..3 | Four fresh triples, each shown with supplied forecast T and F: `PREDICT: T/F` then `ACT: TRY a,b,c` (8rows) | Swap opposite-forecast targets within the same triple; action remains identical/legal |
| 4 | One already-executed triple with prior T and two actual public outcomes T/F: four-key record JSON; matched/mismatched (2rows) | Swap entire records; preserves target multiset but breaks public fidelity |
| 5 | One already-executed triple with prior absent and two actual public outcomes T/F: record predicted=null, relation=unavailable (2rows) | Swap entire records; never repair absence into a forecast |
| 6 | Two actual revealed quiz instances; explicitly supplied ordered labels TTFFTF / FFTTFT → canonical six-label ACT QUIZ (2rows) | Swap whole label targets, retaining six-label syntax; no hidden accuracy claim |
| 7 | Two distinct public practice states, zero TRY budget and unrevealed → `ACT: QUIZ ?` (2rows) | SAME truthful targets in both arms; identical reveal targets cannot be nontrivially deranged |

Thus14/16new rows have a nonidentity target swap; two reveal rows are shared truthful
scaffolds. The contrast tests correct field/state-output alignment on the swapped
families, not the causal value of reveal training itself. No extra SHAM fit needed.

Source construction, if later authorized: choose the first four lexicographic
triples from integers0..9 after the fixed-probe tuple exclusions below; forecasts
are supplied, never environment truth labels. For record k4 use the first remaining
triple where rule6/7 disagree; k5 similarly rule8/9. Generate both observations,
keep prior T/null fixed within each pair, and derive records from the PUBLIC result.
New quiz source IDs use rules6/7 and `/birth-protocol-next-A-v1/quiz-0|1`; supplied
labels are authoring scaffolds even if they coincidentally match any hidden answer.
No dataset is generated in this note; exact resulting source bytes must be frozen
before any fit, independently of model outputs. Reveal's existing INVALID-with-triples
world string is preserved, not treated as a new error/accuracy label.

Risks: learns transcription and faithful record serialization, not self-generated
forecasts or choosing probes. Four-key records are not process-v2 training targets;
they are role-integrity support, not a replacement for eligible complete own-wake
responses. Scaffolds must NEVER be added to native BOOT/parent context/grader.

## Candidate B — observed-evidence next-wake bridge, not an exploration policy

Use this alternative only if Main interprets the closed probe as adequate syntax
but weak evidence-sensitive revision. Same16-row overlay, all eight pairs are wake
examples; no quiz/record block or auxiliary skills added.

Source: `RuleGame.evaluate` supplies two authored episodes for each chosen triple;
`play_task`'s interaction_v3 history/state layout supplies the template. Target
checking reuses `parse_action` and process-v2 `validate_wake`. The body contains
the actual preceding emitted TRY, its PUBLIC outcome, remaining TRY budget2,
unrevealed state, and an explicit author instruction to repeat that observed triple.
Target is exactly `PREDICT: <observed T/F>\nACT: TRY <same triple>`.
No hidden function is consulted to justify target truth once observation is public.

For k0..3 use first four eligible lexicographic triples where rules6/7 disagree;
k4..7 use first four where rules8/9 disagree, excluding already chosen/probe tuples.
For even k set the common earlier prediction T; odd k F. Both members preserve that
same prior prediction, triple, neutral visible ID and wording, differing ONLY in
the public observed Boolean. Each pair therefore contains one prior match and one
prior mismatch. Truth comes from the actual generated response in each source.
Source IDs `/birth-protocol-next-B-v1/revision-k-side` retain the rule prefix ONLY
in metadata, not the prompt. Choice by generator truth is authored contrast design,
not selection by model success or mining current formation failures.

BRIDGE_DERANGED swaps each pair's full next-wake targets: identical legal repeated
TRY, opposite public forecast. All16bridge rows participate. Earlier wrong
predictions remain verbatim; no selective deletion, retrospective correction, or
new target feedback. Do not impose the opaque REVISE "match keep / mismatch switch"
policy here: a native repeated observation warrants the same triple, not that policy.

Risks: explicit repetition is a narrow evidence-use exercise, not informative
probe selection, hidden-rule induction or a guarantee of a second native TRY.
A model could over-repeat/under-explore; leave native quiz/formation behavior intact
and report it, rather than reward repetition in the environment or change the selector.

## Partition, controls and falsifiers shared by both candidates

Reserve practice generator rules6–9; never source rows from current formation0–1,
evaluation2–5, teacher recaps, captured child output, or descendant written material.
Training IDs are new. Exclude every fixed probe's TRY/record/revision triple and all
its `source.revealed_triples` before enumerating training sources. For new generated
quiz instances, require source-ID and complete-quiz nonidentity with probe instances;
report any shared component triples rather than claim globally novel tuples.
Do not train on probe prompts, targets-as-examples, or paraphrases of its particular
histories. Grammar and repeated Boolean/QUIZ targets inevitably overlap and are not
held-out concepts. This is within-practice-source developmental transfer, not unseen
rule-family confirmation; no clean-lineage guarantee follows from IDs/hashes.

Before native audit: AUTH targets must pass raw chronology/reveal/record controls;
each intended nonidentity swap must actually change target, preserve full batch
target multiset and retain context parity. Check every public action/outcome/triple
join, prior null/wrong case and pair contrast. Invalidates labels: hidden-only truth,
invented outcomes, ambiguous source prediction, pre-target future feedback, early
quiz scoring, altered earlier predictions, or claiming a repeated action is optimal.
Missing source or mismatched native token parity is reported, not fixed by selecting
model-favorable cases or silently changing group composition.

## Same recipe; explicit new candidate/audit surface needed later

Reuse `birth.training_recipe(learning_rate=1e-4, seed=0, epochs=4)`: fresh frozen base,
one rank8/alpha16/dropout.05 LoRA, batch8/accum1, group shuffle, AdamW, no warmstart,
packing or split/drop; max_len512, target-only loss and exactly one target EOS.
Unchanged256rows yield128updates/arm, but NOT equal tokens to the previous birth fit.
Actual per-row/per-batch full input, target, EOS, padded exposure must be measured.
Paired target swaps alone do not guarantee prefix lengths, target positions or
padded mass match; native audit must test them, not assert old receipt equivalence.
No truncation accepted, including longer record/native-style prompts. If incompatible,
report the mismatch for Main's explicit revision rather than silently shorten history.

Existing `birth.audit_candidate`, `train_items`, `audit_tokenizer/audit_native` call
exact regeneration and the frozen SWAP=(2,3,0,1,4,5,6,7); neither accepts an overlay.
Future implementation therefore needs a SMALL separate candidate/export audit, not
patches to those functions or a false old-schema/native-pass receipt. Reuse v3
normalize/encode/group-order/collate helpers as the old audit does. Background pairs
are no longer deranged; selected anchor-slot swaps replace the old SWAP contract.
Keep old `birth.readout_cases(original_candidate)` and `birth.score_outputs` untouched.

## Evaluation and native transfer interpretation

Keep the fixed16 probe requests/settings byte-identical and the current32call
OFF/birth-AUTH experiment intact. A future candidate fit would need separately
authorized complete16-request panels for its BRIDGE_AUTH and BRIDGE_DERANGED, using
the same probe, not substituting new adapters into an old run/identity. Those extra
panels are future work, not a claim that all three states fit the fixed32call budget.
Fresh processes, teacher-free prompts, capture-all-before-reduction; invalids remain.
Report parser validity, formatting-sensitive public_contract_correct, exact output
and paired evidence sensitivity separately; never relabel them hidden-rule mastery.

Retain the original128dev conditional/locality readout unchanged for preservation
assessment. Score BOTH proposed arms against original AUTH semantics/assigned_arm=AUTH,
since both received the authentic conditional background; retain twin and anchor/spill
counts. No new threshold or automatic L1 verdict. Existing old artifacts remain a
historical reference, not a randomized control for the reduced-anchor/new-token dose.

Only a separately authorized unchanged interaction_v3 sample can test autonomous
native transfer. Process-v2 still selects each prescribed SECOND pre-reveal TRY,
requires explicit preceding PREDICT T/F and uses its complete own-wake target;
wrong predictions and shortages remain visible, no replacements/KEEP-DROP/record
substitution. Native rules0–1/2–5, teacher visibility and graders do not change.
Success on either scaffold bridge would not prove useful writes, persistence,
informative exploration, full birth, clean ancestry or H1/H2.

Source pins inspected: birth corpus43bf074938e8c4e3a995e43d747ff24f2c6cf70252359cb35134391ff88da74b;
conditional corpus a0ea3717508f05b751935fa3070792d33fe4a21dd46d8a2a93dadb6c2a8b606a;
probe material2799efda619f7686db88d7990b203a3c7ad39eb8577228a26402037de16cc66b.
Only this note was written; no candidates/data/code/tests/native runs were generated.

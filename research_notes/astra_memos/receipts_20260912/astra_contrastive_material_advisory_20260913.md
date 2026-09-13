# Contrastive material: bounded causal/data advisory

2026-09-13 UTC. CPU read-only inspection and in-memory checks; the only authored file is this advisory. This is not a permission gate, independent approval, formal C11 review, source redesign, or instruction to pause Main's native integration. No Git, network, GPU, tokenizer, native execution, or repository writes were performed.

## Answer

**Yes, PLAIN and CONTRASTIVE match the literal source-fact and assistant-target budgets. No, this is not a grouping-only intervention, and D1/D2 strict totals do not identify source discrimination separately from interface improvement.** The scorer supplies useful error categories, but the actual candidate admits both a formatting-only screen pass and a perfect-score shortcut that never reads the final outcome. These are claim limitations, not reasons to stop integration.

## Artifact identity and checks

- Material: `/tmp/astra_contrastive_perception_material_20260913.py`, SHA256 `b3c7fa549fdade0866da51131f64fe067ad7cd3ce36187f67e4c56ac7fbe5c1d`.
- Matching tests: `/tmp/test_astra_contrastive_perception_material_20260913.py`, SHA256 `2f73b41a01f0d735e7568a511c3b332068cf1e2128fa2824181b6b80088875c9`.
- Handoff: `/tmp/astra_contrastive_perception_material_handoff_20260913.md`, SHA256 `2f22e3e93e036e7e629c4366063dc7286bce5092cc73177159b9bf9414c010ff`.
- Actual candidate: `/tmp/astra_contrastive_material_native_candidate_20260913.json`, 232584 bytes, SHA256 `7f9045242e98dc05b85f814574a1eb87cacebf463af88dcca60729c4aa5ebd66`. Exact byte equality with an in-memory pinned rebuild passed. All JSON locations below refer to line 1 of this compact file and the specified JSON path.
- Ran 18 existing material tests in memory: all passed, 0.291 seconds. Deliberately omitted `test_source_pins_and_output_custody` and `test_cli_build_and_score_mock_responses`, because they write files. No tests were changed. The handoff's 20-test statement is historical, not this advisory's execution count.
- Additionally inspected the native integration's prompt projection and matching tests as text only: `/tmp/astra_contrastive_perception_run_20260913.py:211`, `:417`; `/tmp/test_astra_contrastive_perception_run_20260913.py:225`. This does not attest a deployed runtime.

## 1. Matched facts/targets; treatment includes instruction and length

Measured on the candidate: each arm has 12 rows, 96 labeled field cells, and 986 UTF-8 assistant-target bytes per corpus pass. Every paired selected source, companion source, target string, and note-line multiset matches. Each row contains both original transcripts and the same eight cells. Reciprocal pairing reuses each of the 12 sources as selected and companion; it does not create 24 unique sources per arm.

Evidence: material `:91` derives cells from public-source proofs; `:101` changes ordering; `:123` pairs sources and builds prompts; `:181` verifies target/source/cell equality. Tests `:42`, `:50`, `:62` check preservation, reciprocal pairing and literal prompt-cell multiplicity. Candidate paths: `$.training.{plain,contrastive}[*].{source,raw_target,target_sha256,material}`.

**Valid causal qualification:** the contrastive arm also says to notice shared action/prediction and opposing observations and explains how relation follows. PLAIN has different prose. Thus the intervention bundles grouping, attention/relational guidance, and context length, not grouping alone. Material `:30`–`:32`, `:138`–`:140`; candidate `$.provenance.templates.{plain,contrastive}` and training `input_messages`.

Context totals are PLAIN 15900 versus CONTRASTIVE 16692 UTF-8 bytes: +792 (+66 per row, about 4.98%). Token counts remain null in the candidate. Byte-equal targets do not alone establish native target-ID/mask equality, realized update counts, or equal compute. Recipe totals (two fits, 24 updates, 96 presentations, 144 evaluation calls) are planned, not achieved costs. Evidence: material `:112`, `:199`–`:209`; candidate `$.costs` and `$.recipe_only_not_executed`; handoff `:135`–`:150` already qualifies these correctly.

**Smallest correction:** describe results as an “equal-source/equal-target authored grouping-plus-guidance intervention,” not a grouping-only or matched-compute effect. Retain the handoff's native token/mask checks and measured cost reporting. No generator change requested.

## 2. Strict-screen success can be entirely interface improvement

The scorer separates syntax, schema, completion, and source errors, but all four `field_correct` values stay null when syntax/schema fails. A record with one invalid field likewise loses field diagnostics for its other valid fields. Strict totals and the exploratory screen use the conjunction of interface and content correctness; they do not isolate either component. Evidence: material `:219`–`:267`, `:289`–`:310`; tests `:107`–`:128` explicitly verify this behavior. Candidate `$.screen` contains only strict-score thresholds and canary preservation.

**Executed counterexample, synthetic only:** all canaries were identical perfect responses in all states. On D1/D2, OFF and PLAIN emitted the exact correct target wrapped in a Markdown JSON fence; CONTRASTIVE emitted that same content unfenced. The actual scorer returned held totals OFF=0, PLAIN=0, CONTRASTIVE=24, no canary regressions, and `exploratory_screen_pass=true`. No source-value improvement occurred in this construction. This is not an observed model outcome.

**Smallest correction:** never equate the screen flag with source-discrimination success. Report interface-invalid→valid transitions separately from wrong-source→correct-source transitions on pairs schema-valid in both states; give eligible denominators and keep malformed fields unevaluable. Do not repair malformed text to award strict credit. Conditional field accuracy still is not mechanism proof. Handoff `:126`–`:129`, `:155`–`:158` already calls for this distinction; ensure the eventual readout actually makes it.

## 3. Perfect held scores need not use the selected outcome

The generator always makes the earlier observation the Boolean opposite of the selected final observation. All 12 D1 cases and their 12 D2 re-renderings have this relationship. Evidence: material `:150`–`:164`, especially `:157`; test `:83`–`:91`; handoff `:78`; candidate `$.evaluation.{D1,D2}[*].source.events`.

**Executed counterexample, synthetic only:** parse the final event's action/prediction, obtain `observed` by negating the earlier event's outcome, and derive `relation` from that value and the final prediction. This procedure never reads the final event's `raw_outcome`. The unmodified scorer awarded **24/24 strict passes** on the actual candidate. It does still read the final action/prediction; the specific failure of identification is final-outcome provenance, not all event selection.

This is a deterministic cue in the intended public evidence, not proof that a model exploits it or a hidden-target transport leak. Both arms face the same cue, so it does not invalidate their descriptive performance comparison. It does prevent even perfect, well-formed responses from proving that the selected outcome was used. Also, the action triple appears in both the action and its outcome string, and relation is explicitly defined in the shared interface instruction: successful field reconstruction need not establish the advertised internal source-binding mechanism.

**Smallest correction within this advisory's scope:** state “performance on fixed conflicting-event fixtures; selected-outcome use is not identified.” Do not claim that D1/D2 strict or field scores prove source-bound discrimination. Resolving that mechanism would require separately authorized future evidence; no new dataset or source redesign is proposed here.

## 4. Exposure and provenance: no demonstrated model-prompt leak

The candidate does contain evaluator answers/proofs and answer-bearing metadata, including `source.case` (for example `unavailable_true`), alongside input messages. D1/D2 retain exposed DEV ancestry in `source.derivation.parent_source_id`, with new source identity/proofs after the event edits. This is disclosed ancestry, not independent newly sampled semantic material. Evidence: material `:158`–`:164`, `:189`–`:197`; corpus `/data/home/rohing/dream-state/organism_v6/birth_skill_corpus.py:128`–`:170` verifies identity and derives proofs from public events. Candidate paths: `$.evaluation.D1[*].{raw_target,source_proof,source.case,source.derivation}`.

Actual D1/D2 `input_messages` contain public events and shared response instructions, not companion field notes, serialized target records, case labels, proof objects, or ancestry IDs. The final action/outcome and prediction are intentionally answer-bearing task evidence; their visibility is not itself contamination. Training's notes explicitly contain all target field values in both arms: this is authored scaffolding, not unaided discovery. Six copy-canary target strings occur verbatim in their prompts by the definition of copying, not by accidental leakage.

The handoff forbids giving the full dataset/manifest to the learner (`:103`–`:108`). The inspected native code builds calls from `row['input_messages']` and invokes `backend.generate(call['messages'])` (runner `:211`–`:213`, `:411`–`:417`); its test checks the call envelope excludes `raw_target` (`:225`–`:230`). No target/proof transport into the model was found in this inspected path. Material tests alone do not prove runtime visibility or loss masking, and native fixture tests are not actual inference evidence.

**Smallest correction:** preserve that explicit input-message projection; describe whole-dataset secrecy as a required boundary, not an already observed end-to-end guarantee. Keep case/proof/target metadata evaluator-only. No new formal guard work requested.

## 5. Independence and success language

D1 and D2 have exactly identical paired sources and targets, differing in wrappers: 24 renderings of 12 constructed cases on **two fresh triples**, not 24 independent trials. The six outcomes/predictions per triple come from the same authored factorial; “independent hypothetical boxes” distinguishes fictional worlds and must not be read as statistical independence. TRAIN similarly has reciprocal reuse. C-record is exact exposed DEV12, suitable as a preservation canary, not held-out semantic evidence. Evidence: material `:148`–`:165`, `:208`–`:213`; tests `:80`–`:100`; handoff `:57`–`:88`; candidate `$.limitations`, `$.evaluation`, `$.provenance.held_triples`.

These limitations are mostly already labeled correctly. “Fresh targets” in handoff `:81` means new full records/triples; the Boolean/relation factorial and DEV ancestry are reused. Neither an exploratory threshold pass nor one seed establishes mechanism repair, child-generated learning, broad transfer, H1/H2, or original L2 endpoint promotion. The existing handoff explicitly says so.

**Smallest correction:** retain paired-case/wrapper counts and the two-triple limitation in the headline readout; do not attach an independent-n=24 significance or generalization claim. Summarize any observed win as descriptive authored-fixture performance, with interface and source-error transitions shown separately and the final-outcome shortcut disclosed.

## Disposition

No artifact inconsistency or demonstrated hidden-evaluator prompt leak was found. Three concrete interpretation risks remain: grouping is bundled with guidance/length, a formatting-only change can pass the screen, and ignoring the final outcome can attain 24/24. The minimal response is accurate readout/claim qualification, not halting integration or modifying the frozen material. All counterexamples above are CPU synthetic probes, not native results.

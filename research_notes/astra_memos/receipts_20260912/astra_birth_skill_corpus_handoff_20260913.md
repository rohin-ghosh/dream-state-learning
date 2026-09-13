# EDITSTOP — bounded birth-v2 per-skill DEVELOPMENT corpus

Prepared 2026-09-13 UTC. Main review required before native use. No native grid,
model generation, fit, GPU operation, network request, Git operation, notebook
edit, or scientific qualification was performed. Only the three assigned files
were written. This work is independent of the frozen run Main monitors.

## Design and counts

Origin is `AUTHOR_SOURCED_DEVELOPMENT_ONLY`, not teacher-generated context
distillation. The public outcomes are literal authored hypothetical observations,
not evaluated hidden rules or actual child experience. Opposite outcomes for
the same triple describe independent hypothetical boxes, not one inconsistent
world. No hidden-rule name, oracle, future answer, or inferred rule is a target.

| Separate slice | Train rows / targets | Dev probe rows / targets | Response schema and limit |
| --- | ---: | ---: | --- |
| perception | 12 / 12 | 12 / 12 | Existing `record` JSON: `try`, `observed`, `predicted`, `relation`; public-record fidelity only. |
| reflection | 12 / 12 | 12 / 12 | Existing free-prose `restate` role, two sentences; author-supported reusable recording correction, not spontaneous reflection or rule induction. |
| judgement | 24 / 12 | 24 / 12 | Same record JSON for 12 supported sources; 12 paired insufficient-source probes have **no native target**. No invented abstention token. |

Counts above are per anchor condition, not a mixture. Every positive slice/split
crosses two selected triples with six cases: predicted/observed T/T, F/F, F/T,
T/F, absent/T, absent/F. Thus each has four matched, four mismatched, and four
unavailable relations; six True and six False observations. Absent prediction
is sufficient for a valid record with `predicted: null`, unlike ambiguous
prediction or missing outcome. This separates uncertainty from evidence failure.

Reflection uses the same 12 sources. Four discrepancy examples teach preserving
the observation instead of copying a contradicted prediction; four agreement
controls prevent treating every event as a correction; four absent-prediction
controls teach not fabricating a prior belief. The procedural support is an
explicit author-supplied parent message in the input, traced in the proof.
This is scaffolded restatement, not proof of independently acquired reflection.

Judgement pairs each supported source with an authored alteration: six have
ambiguous prior predictions and six return an outcome for a different triple.
The unmodified parent source and alteration operation are preserved. Positive
and negative eligibility are balanced within each selected triple and case.
Missing-outcome refusal is additionally CPU-tested, not added as more corpus.

## Stable API and source/anchor conditions

```python
from organism_v6.birth_skill_corpus import build_slice, build_variants, audit_split_pair

train = build_slice("perception", split="train", system_anchor=None)
dev_conditions = build_variants(
    "perception", split="dev", system_anchor="EXACT CALLER-SUPPLIED ANCHOR HYPOTHESIS"
)
assert audit_split_pair(train, dev_conditions["absent"])["disjoint"]
```

The skill and literal split are explicit. `system_anchor` is required, either
exact supplied text (preserved including whitespace) or explicit `None`.
There is no mixture default, training/export adapter, or built-in anchor claim.
The same source, source proof, `row_id`, and raw target are used in absent and
supplied variants; only the extra system message/input hash changes. `row_id`
is the stable skill-specific probe ID; `source.source_id` joins correlated public
situations across all three slices. Keep the dev rows fixed for Main's readout.

Each row holds `input_messages` separately from `raw_target`, raw events,
selected event ID, content-addressed source ID, field-level `source_proof`, input
and target hashes, response role, admissibility diagnostics, and target status.
These diagnostics/proofs/case names are metadata, not model input or new output
labels. `raw_target=None` means **no expressible target**, never an assistant
JSON null, empty response, DONE, or ABSTAIN training example.

## Literal split, templates, provenance and checks

- Ordering seed: `20260913`; a different integer changes row order only.
- Train selected triples: `(-4,1,7)`, `(2,-5,9)`; dev: `(11,-8,3)`, `(-6,12,5)`.
- Train has one public event. Dev uses a held-out wrapper and one preceding
  distractor event `(20,21,22)` before the selected event. Its supplied outcome
  is fixed within each situation, independent of the selected outcome/case.
- Manifest embeds the literal split, six-case table, templates, earlier public
  outcomes, ordering seed, anchor bytes/hash, row/source/target hashes, and
  hashes of the actual selected public parser/record definitions.
- Only standard-library AST loading of named parser functions/constants from
  `rulegame_parenting_diagnostic.py` is used; no runner imports, native model
  imports, world execution, or RuleGame rule function calls. Born formation's
  `record` and free-prose `restate` interfaces supplied the compatibility boundary.
- Record targets pass the existing `interaction_v3` parser/scorer. Proofs join
  exact raw response/outcome bytes to the selected event and derive relation
  only by the existing explicit equality/null definition. Hashes demonstrate
  byte custody, not authentication of real-world experience or semantic truth.
- Every slice has zero conflicting input/target collisions, zero duplicate
  inputs, and full six-case coverage per selected triple/template. Judgement
  additionally checks one negative per original source. No triple/template or
  earlier-result-only shortcut determines the positive targets. This is a
  bounded check, not a universal claim of shortcut freedom.
- Train/dev overlap is zero for row IDs, rendered inputs, non-null targets,
  selected triples, and selected raw-event bytes. Shared grammar and semantic
  cases are intentional. These are authored development holdouts, not L2 gates.

## Explicit grammar and scoring limits

The public record grammar has no abstain response. Judgement negative fixtures
return `passed=None` / `unsupported_native_abstention` for every proposed model
response, including silence and faithful-looking JSON. They are source-side
admission tests, not scored model abstention. **Do not drop the negatives and
call positive-only SFT a balanced judgement birth.** Main must resolve the
native admission interface before that slice can support the intended training.

Reflection's free-prose role has no existing semantic correction parser.
`score_response` checks exact authored wording only and explicitly identifies
that score as `exact_authored_restatement_only`; a valid different paraphrase
can fail it. Main needs native semantic review plus application-to-a-new-public-
discrepancy evidence, not merely reproducing that sentence. The development
wrapper deliberately omits the native prompt's precomputed `Observed fields`,
so perception cannot simply copy normalized answers. Response grammar is
compatible, but prompt/token parity with native formation is not yet certified.

## Main's minimum native follow-up — documented only, NOT implemented

First distinguish prompt-dependent elicitation from weight-persistent skills;
do not claim "activated connections". Keep skills separate. For each eligible
skill, use OFF plus skill-SFT with training anchor absent/present, each crossed
with readout anchor absent/present over the same fixed public-situation probes.
This is six distinct cells per skill: two OFF readouts and four SFT readouts;
OFF has no training-anchor condition. Exact anchor bytes remain caller-supplied.

Main still owns native tokenization/chat-template and response-budget checks,
matched exposure/optimization and source-visibility controls, model identity
and adapter provenance, and unchanged probe/source hashes across cells. Test
the anchor-present-trained adapter with its anchor withdrawn against OFF and
absent-anchor-trained controls, including matched delayed/continued-use readout
if making a persistence claim. Paired absent *inputs* alone establish none of
this. Resolve judgement's missing abstain interface; independently review free
reflection semantics and transfer. No actual L2 qualification or persistence
claim follows from these CPU fixtures.

## CPU validation and pins

Command:
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_birth_skill_corpus.py -v`

Result: **22 tests passed**, 0.170 seconds on the final code/test revision.
Tests cover factorial truth/negation/uncertainty, raw source joins, exact anchor
pairing, reproducibility, split leakage, duplicates/collisions, negative pairing,
malformed/duplicate-key/type-invalid records, action/outcome mismatch, absent vs
ambiguous vs post-action prediction, missing outcome, free-prose scoring limits,
and a fresh-process check that no native/world modules were imported.

File SHA-256:

- `organism_v6/birth_skill_corpus.py`: `078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6`
- `tests/test_birth_skill_corpus.py`: `3dd12a8bef0095e488f75c32dfad6251e12f38441ee992ac9d5731454200d0e9`

Selected public-interface definition pin:
`82b894ae9f226e739cc23ef9fa0ccd0106cc7ad1e04cd8fb86202d5656a7ccb6`

Default-seed, absent-anchor `rows_sha256`:

| Slice | Train | Dev |
| --- | --- | --- |
| perception | `d394bd7af11208e3b2aebb99e4151cdc2c78ee9163011acf3a29b4521eab662a` | `7ced906e87d68f042ef90eadb57b8b785d6de42d7a77169d2df8a89c56172cf5` |
| reflection | `bc382060b3f76fc03368c0da40ef60157d232a39b6cbe603f4759d68d89f1507` | `b3fff54c17125c4db15ba7efb51155d666ea793162474e44c6d496217a433537` |
| judgement | `a05cbb8d612bfde9ed527bd1f82781a380168732abf626906e07cc02a4465924` | `6e3de74d8885e5f1134189d3f951d472822b1e7b5a12000ebc234374171eb155` |

This handoff's hash is supplied in the final EDITSTOP response, avoiding a
self-referential file hash. All three files are now handed back to Main.

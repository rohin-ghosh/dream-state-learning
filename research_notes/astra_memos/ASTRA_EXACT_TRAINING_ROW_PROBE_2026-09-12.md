# Prospective supplementary exact-training-row probe

September12,2026,14:08UTC. Main-selected diagnostic after SEQ083–086.
No new fit, model, target, curriculum, gate threshold or original artifact edit.

## Question and data

Did the four existing semantic-Q0 adapters acquire their intended associations
on their actual training prompts, despite weak held-form generation?
Use originald160e0b2sealed `fits.json`, all128rows per root/mapping. Supply
only each row's recorded prompt/prefix for generation; never append its target.
The two maps for one root must have identical ordered prompt bytes/token IDs,
with opposed source targets. OFF is evaluated once per root and scored against
both target maps analytically, not regenerated as independent controls.
Both roots and all source rows are selected before inspection; no convenient
key/template subset or exclusion after output. Original arrays/hashes pinned.

Per root: fresh OFF, matching W+ and W- adapter processes; each state generates
and scores128prompts.384generations+384two-candidate scores per root; total
768generations+768scores=1536requests/1536candidate forwards, zero fits.
Use frozen base/tokenizer, original four saved adapters, greedy max32tokens,
gen_seed0, exact chat prefixes, existing native parse and repaired equal-total-
shape BF16scorer. Capture all generated IDs/text/EOS/truncations and per-token
candidate scores. Fixed padded-forward likelihoods are distinct from actual
dynamic-length generation; LF+EOS scoring versus LF-omitting output remains
an explicit interface limitation. No claim of FP32/backend equivalence.

## Endpoints and interpretation

Primary diagnostic: generated correct action count/128 for each matching map,
OFF count under that map, format validity, and per-key/per-template counts.
Report paired map contrasts and corresponding original64held-form counts
descriptively; their different contexts/template counts are not independent
learner replicates. Secondary fixed-shape target scores/margins cannot replace
generation accuracy or serve as a new passing writer gate.

High exact-training generation with poor held-form generation localizes a
retrieval/rendering gap within this tested instance. Poor performance on both
does not demonstrate stored usable associations; investigate material/update
capacity or implementation before another fit. Better target likelihood alone
is compatible with formatting/bias effects and is not proof of useful memory.
Report continuous counts, not a newly invented pass threshold. The original
half-nat criterion and old score defects are not repaired by this diagnostic.

Two original roots are optimizer-seed-confounded and are not three learner
replications. No retention, unseen-key, H1/H2, parenting, clean-lineage or
mechanism-freeze claim. Exact-training questions are not evaluation holdouts;
this assay intentionally tests training associations, not generalization.

## Execution and stopping

Main may run the two roots concurrently on freshly checked node3GPUs0and7,
one continuous reservation per root through its three fresh state workers.
Record runtime GPU identity separately from original training GPU identity;
weights/model/settings stay fixed. Main owns launch/cleanup; do not share
mutable adapter state, retry into a prior output root, or kill another owner.
Maximum30minutes per root, three bounded state workers; explicit finalized
worker caps and source commit must be logged before launch. Native CPU tests,
token/material preparation and stored adapter hashes must pass first.
Stop on prefix/mass/record mismatch, invalid model identity, nonfinite output,
deadline or worker failure; preserve failed attempt and never promote partial
rows. Full source/reduction/cleanup checks precede release. Formal C11 guard
remains deferred; no new fit is authorized by a diagnostic success label.

Maxwell owns only `gpu/astra_semantic_train_probe.py` and its focused test.
Main reviews/freezes source, pins exact commands and launches after native
preflight. Future training design depends on these outputs, not assumed success.

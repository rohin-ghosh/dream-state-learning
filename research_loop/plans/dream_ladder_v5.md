# Frozen development transition: dream ladder v5

Split: aligned skin, seed 0, development only.

Named defect: single-sample hypothesis generation has high variance and low
candidate recall. The previous best candidate recall was 2/12; v4 produced
1/12 and one malformed target response.

Condition label (permanent): **task-family-scaffolded,
public-evidence-exact-gate ceiling/reference diagnostic**.  It is not the
headline verifier-free autonomous-dreaming arm.  Its purpose is to measure the
proposal frontier and certify the downstream corpus contract without claiming
that the checker itself is learnable intelligence.

Change: take four independently seeded role-stage samples and four independently
seeded parent-stage samples at the existing k=6 budget, using temperature 0.7.
At prefix `i`, parent sample `i` receives only the role union available through
prefix `i`; later role samples cannot assist earlier parent samples. Union
claims that pass the existing public-evidence filters and deduplicate canonical
pairs/parent sets. Do not change the world, target observations, gold-control
thinker, or hidden truth scorer. Save the genuinely nested cumulative curve
after 1, 2, 3, and 4 samples.

Evidence split: role discovery sees only observations from the six ordinary
source lands. Target-land observations are excluded from every role prompt and
role prefix; their evidence IDs are recorded and they are used only for the
later blind comparison of committed parent predictions. This global split is
fixed in preference to a per-target leave-one-out policy.

The artifact records every excluded target-observation ID and, for each target,
the exact evidence ID, entity, land, and observed token used by the public
comparison. A true parent set appearing among retained claims is reported as
`retained_truth_presence`, never parent-exact, because false retained claims may
coexist. Compute metadata is self-contained: k=6 per target/sample, four
samples, a 24-candidate-per-target ceiling, and `matched_compute_to_v4=false`.

Before the 32B model is loaded, a frozen runtime preflight must confirm that
`ninja` is executable and that the pinned tokenizer chat template produces a
flat integer token-id list for vLLM. This is an infrastructure contract only;
it receives no world data and cannot affect proposal content.

This is an increased compute condition: k=6 x four parent calls permits at most
24 candidate lines per target.  It must be reported as such and is not a
matched-compute improvement over v4.

Only the first six emitted `CANDIDATE:` lines in each target/sample call are
eligible; later lines are recorded as overflow and never parsed, filtered, or
credited. An eligible line must name the current target, contain 2–5 distinct
valid source lands, and predict exactly both observed entities. Token budgets
are counts of the actual templated, potentially truncated input token IDs and
generated output token IDs supplied by/returned from the inference engine.

Falsifier: repeated sampling may fail to increase candidate recall, or may
accumulate false role/parent accepts. Therefore report raw proposals, unique
supported claims, and the exact retained corpus separately, including
fallback claims.  A candidate missing one already-known public observation is
**contradicted**, not merely "unverified"; if retained as the legacy fallback
ablation it must carry that exact status.  Report cumulative true/total values
for each and the generation/query/token budget. Do not assert that filtering
guarantees truth.

Thinker answers are scored only when the complete emitted answer is exactly one
canonical state-token. Prose, negation, punctuation, and substring matches are
malformed and are reported separately.

The canonical state-token vocabulary is parsed exclusively from the public
lifetime/workshop text, never from the hidden answer key. Every raw thinker
completion is retained. Each completion must full-match exactly one permitted
operation; embedded or multiline operations are malformed. Report exact
thinker-generation and memory-query counts plus actual model input/output token
ID counts and truncation metadata for the entire downstream stage.

Next gate: this run is diagnostic. It does not authorize prompt tuning on
replication seeds. Any move to frozen LoRA transport or any further scientific
repair requires review of the committed artifact.

Execution privacy: reviewer-only context (including the mini ledger) remains on
the local machine. The remote worker verifies the exact approval-receipt hash,
the reviewed lock and remote-spec hashes, and every execution input declared by
the remote spec against that lock. It must fail closed for a missing or changed
declared input, but it must not require unrelated reviewer context to be copied
to the GPU host.

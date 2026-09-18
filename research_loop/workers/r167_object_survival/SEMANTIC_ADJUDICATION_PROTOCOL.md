# R167 semantic adjudication: private, not executed

This is a pre-output methods specification, not a claim that semantic scoring
has happened. The executable string scorer emits lexical candidates only.
No additional provider calls or semantic-scoring budget is implicitly granted.
Existing fixed readouts and R159 items, answers and scores are excluded.

## Visibility and blinding

An evaluator who is not parenting these lives receives only opaque response
IDs, the applicable TRAIN-only fingerprint/witness packet, exact original
system/birth/probe text, and the response with its truncation flag. The packet
must omit adapter condition, checkpoint index, schedule order, lexical flag,
and the outcome of other conditions. Keep the ID-to-condition/checkpoint map
private and separate. Freeze annotations and their evidence-span references
before unblinding. Conflicting/ambiguous annotations stay explicit; no tuning
of anchors or criteria after seeing answers. Do not show detailed annotations,
fingerprints, answers, scores or qualitative conclusions to Main/other parents.

The evaluator may write its detailed appendix directly under the node-local
R167 private_appendices directory. Shared COORDINATION receives status, counts,
hashes and paths only. Merely renaming a public COORDINATION section an appendix
does not protect blindness. Mode0700/0600 is not a same-account security boundary;
the Main-approved parent/repo-reader exclusion is still necessary.

## Identity and continuation are different judgments

Classify each answer as NO_IDENTIFIABLE_EVIDENCE, GENERIC_CATEGORY_ONLY,
SPECIFIC_IDENTITY, SPECIFIC_IDENTITY_WITH_RELATIONAL_DETAIL, AMBIGUOUS, or
CONFLICTING_FEATURES. Specific identity requires convergent distinctive
features/relations grounded in that checkpoint's pre-evaluation TRAIN history,
not the mere domain word or name. A faithful paraphrase may qualify without
literal anchors. Mark supporting spans, contradicting spans, and uncertain
features separately. Exact faithful recurrence supports identity and does not
need novelty. Contradictions are not erased by one matching phrase.

Separately classify faithful recurrence, coherent extension of that same
object, unrelated novelty, or insufficient visible evidence. A novel five-gram
is not itself coherent continuation. Cap-truncation never negates already
visible identity evidence; it limits what can be concluded about an unfinished
continuation. A negative answer to an open prompt is not proof of absent memory.

Audit semantic as well as literal birth/system/probe cueing privately. If the
input already provides the distinguishing object features, label expression
as cued; do not call it uncued recovery. The historical birth is never rewritten
to improve this result. Current exact-gram checks alone do not certify semantic
leakage clearance.

## Attention-control behavior

For prompt3, independently annotate whether the answer identifies a concrete
uncertainty or choice, explains WHAT deserves attention, HOW to examine it,
and HOW MUCH evidence or effort is proportionate (including a stopping/change
criterion). Distinguish generic strategy/vocabulary from practices supported
by this life's prior TRAIN evidence. Record contradicted or invented practices.
This remains reported judgment in an answer, not demonstrated attention
allocation, improved task performance, consciousness, or causal learning gain.

## Paired interpretation after annotations are frozen

Prompt1 ON-not-OFF is the primary exploratory comparison. Prompt2 remains
independent; prompt3 is a separate instrument. Record initial ON/OFF and each
checkpoint OFF, including positive baseline matches, missing/ambiguous cases,
and semantic cueing. Do not condition the user's primary flag on prompt2 or
quietly replace it with a baseline-adjusted criterion. Report all18 selected
sleeps, not only the first favorable checkpoint. One deterministic decode,
correlated checkpoints, repeated OFF responses and retrospective object
selection are not independent replications or an onset date for retention.

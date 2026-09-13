# Binding successor v1: P-CHAIN-2

**Date:** 2026-09-13 PT
**Status:** binding design only. Source authoring, deterministic
materialization, tokenizer/model execution, fitting, adapter/checkpoint work,
GPU use, remote execution, and scientific claims remain **closed**.
**Preserves:** the five model states, identity-domain sizes, fact and skill
counts, D1/D2 doses, and hard resource caps in
`2026-09-13_smallest_parametric_two_hop_composition_ceiling.md`.
**Supersedes:** that document's one-hop candidate gate, CoT/direct causal
interpretation, D1/D2 selection wording, underspecified atomic and LOCAL
serialization, unbound shortcut-null algorithms, and ambiguous LR0
`byte-zero` wording.
**Audit basis:**
`2026-09-13_parametric_two_hop_ceiling_fresh_preimplementation_audit.md`.

## 1. Frozen question and maximum claim

P-CHAIN-2 asks whether one rank-8 adapter can make two separately supervised
opaque NEXT atoms freely available and return the assigned endpoint on a held
two-hop query. It then asks whether an adapter trained over the same
identifiers, with only the second-hop bindings reassigned, preserves the
first hop and redirects the endpoint.

The primary positive is binding-sensitive parametric composition under a
canonical supervised interface. It is not own-life learning, retention,
DREAM, parenting, autonomous memory cueing, action improvement, a stored
graph, population evidence, or the Dream--LoRA--Think flywheel.

The printed trace is an observable canonical output, not proof that its first
line causally mediated its second. Direct-answer calls measure transfer to a
different output format; they do not test whether CoT was necessary or
enabled a hidden computation.

## 2. Frozen domains and states

Keep the original three concrete-identifier-disjoint domains:

- `EVAL-MEM`: 16 chains in two eight-chain blocks;
- `PROMPT-ONLY`: 16 chains whose identifiers occur in no training byte; and
- `JUNCTION-TRAIN`: 32 target-disjoint skill examples.

For EVAL-MEM, AUTH contains:

```text
A_i -> B_i
B_i -> C_i
```

Within each eight-chain block, a presealed fixed-point-free permutation
`pi` produces DERANGED:

```text
A_i -> B_i
B_i -> C_pi(i)
```

Use the original five states and no others:

- `BASE`;
- `LR0`;
- `ATOM-LOCAL`;
- `ATOM-JUNCTION`; and
- `DERANGED-JUNCTION`.

All fitted states use frozen Qwen2.5-7B-Instruct, all-layer rank-8 LoRA,
`alpha=16`, dropout `.05`, LR `3e-5` except LR0's exact zero LR, batch `4`,
and response-only loss, unless EVENT-retention-v2 prospectively disqualifies
that writer recipe. There is one DEV material root and one learner seed.

## 3. Exact text and loss contract

All authored content is UTF-8, Unicode NFC, with ASCII punctuation and
exactly one terminal LF. Placeholders below are replaced by one opaque
identifier and contain no angle brackets after rendering. No trailing space,
blank leading line, Markdown fence, or additional prose is permitted.

Every training/readout call uses exactly this system content:

```text
You work with opaque NEXT relations. Return only the requested canonical lines.
```

The system and user roles are fully loss-masked. During training, loss applies
only to all assistant-content tokens below plus the chat template's terminal
assistant end-of-turn token. Store both the canonical role/content JSON and
the exact post-template token IDs and mask bits in the material receipt.

### 3.1 Atomic source-to-memory unit

Each relation is one independent training unit. Its user content is exactly:

```text
OBSERVED RELATION
NEXT <SOURCE> => <TARGET>
TASK
Store exactly this one relation.
```

Its assistant target is exactly:

```text
MEMORY NEXT <SOURCE> => <TARGET>
```

The input exposes the one observed relation because this is a supervised
write ceiling. No unit contains a second relation, endpoint candidates, a
held question, a trace, a chain label, `A/B/C`, an episode/thread label, or a
shared provenance token. The only concrete byte shared by the paired
`A_i -> B_i` and `B_i -> C_i` units beyond the fixed wrapper is the legitimate
middle identifier `B_i`.

The two units from one chain never occupy the same minibatch or adjacent
optimizer slots. Their lag class is balanced over the predeclared tape and is
not encoded in any model-visible byte.

### 3.2 JUNCTION skill unit

Each JUNCTION user content is exactly:

```text
AVAILABLE RELATIONS
NEXT <D> => <E>
NEXT <E> => <F>
QUERY
Starting at <D>, apply NEXT exactly twice.
OUTPUT
Return exactly two MEMORY lines followed by one ANSWER line.
```

Its assistant target is exactly:

```text
MEMORY NEXT <D> => <E>
MEMORY NEXT <E> => <F>
ANSWER <F>
```

### 3.3 LOCAL-TWO-READ skill unit

Each matched LOCAL user content is exactly:

```text
AVAILABLE RELATIONS
NEXT <U> => <V>
NEXT <D> => <E>
QUERY
Starting at <D>, apply NEXT exactly once.
OUTPUT
Return exactly two MEMORY lines followed by one ANSWER line.
```

Its assistant target is exactly:

```text
MEMORY NEXT <U> => <V>
MEMORY NEXT <D> => <E>
ANSWER <E>
```

`U,V,D,E` are four distinct identifiers and neither relation joins the
other. The queried/relevant fact is always the second line; the answer is
always that second line's target. Thus JUNCTION and LOCAL match line order,
answer-line position, command count, wrapper roles, example count,
identifier-token marginals over the complete curriculum, assistant target
tokens per batch, and presentation tape. No padding field is permitted. Report
the irreducible user-side byte/token difference caused by `once` versus
`twice` and by nonjoining versus shared-middle identifiers; do not describe
the inputs or gradients as exactly matched.

The remaining semantic/input difference is the treatment: a two-hop joining
example versus a nonjoining one-hop example. A gap can support only
`the target-disjoint junction curriculum package helped`.

### 3.4 Readout text

One-hop EVAL-MEM user content is exactly:

```text
QUERY
Recall NEXT for <SOURCE>.
OUTPUT
Return exactly one MEMORY line.
```

There is **no candidate list**. The only accepted assistant response is:

```text
MEMORY NEXT <SOURCE> => <ASSIGNED_TARGET>
```

The 16 first-hop and 16 second-hop calls are independent cold calls.

The EVAL-MEM canonical two-hop user content is exactly:

```text
QUERY
Starting at <A>, apply NEXT exactly twice.
ENDPOINT CANDIDATES
<CANDIDATE_1>
<CANDIDATE_2>
<CANDIDATE_3>
<CANDIDATE_4>
<CANDIDATE_5>
<CANDIDATE_6>
<CANDIDATE_7>
<CANDIDATE_8>
OUTPUT
Return exactly two MEMORY lines followed by one ANSWER line.
```

Its only accepted AUTH response is:

```text
MEMORY NEXT <A> => <B>
MEMORY NEXT <B> => <C>
ANSWER <C>
```

DERANGED uses the byte-identical user message and must replace only the
second-hop target and answer with its assigned `C_pi(i)`. The intermediate
`B` is absent from all endpoint candidates and must be freely generated.
This panel therefore tests free intermediate generation plus assigned
endpoint selection, not free generation of both outputs.

The direct user content is identical through the eight candidate lines and
then ends:

```text
OUTPUT
Return exactly one ANSWER line.
```

Only `ANSWER <ASSIGNED_ENDPOINT>\n` passes. Direct results are descriptive
alternate-format transfer only.

PROMPT-ONLY uses the same canonical two-hop format, but inserts exactly these
lines before `QUERY`:

```text
AVAILABLE RELATIONS
NEXT <A> => <B>
NEXT <B> => <C>
```

Its empty control instead inserts:

```text
AVAILABLE RELATIONS
NONE
```

All calls use fresh conversations, fresh KV state, and no conversation,
cache, or hidden-state reuse.

## 4. Binding and batch coupling

Identifiers have identical byte length and tokenizer length and use one
role-blind generator. Assignment to source/middle/endpoint, domain, candidate
position, and AUTH/DERANGED relation is independently shuffled subject only
to the prospectively declared balance constraints.

Within each eight-chain EVAL block, `pi` is four disjoint transpositions.
Every transposed pair of second-hop atomic rows occupies the same coupled
batch shard on every presentation. Swapping their targets therefore preserves
the exact per-batch target-token multiset. No first-hop row shares a minibatch
with the second-hop row from its own chain.

ATOM-JUNCTION and DERANGED-JUNCTION share exact base bytes, initialization,
optimizer/dropout seeds, wrapper/token/mask arrays, batch order, update count,
and RNG tape. Their only assistant/source difference is the presealed
second-hop target permutation. ATOM-LOCAL and ATOM-JUNCTION share the exact
atomic fact units and all non-treatment receipts.

## 5. Executable shortcut-null registry

The generator must emit a fixed null-policy registry before binding any NEXT
targets. Null policies see only the query source identifier and the ordered
eight endpoint candidate identifiers. They cannot read any NEXT mapping,
training row, EVAL label, AUTH/DERANGED assignment, raw model output, score,
or adapter state. There is no fitting, feature selection, or threshold choice
after labels exist.

For every candidate define the following raw features:

1. zero-based display position;
2. lexicographic rank of its UTF-8 bytes among the eight candidates;
3. byte length;
4. tokenizer length under the frozen tokenizer;
5. longest common byte-prefix length with the query source;
6. longest common byte-suffix length with the query source;
7. bytewise Levenshtein distance from the query source;
8. unsigned byte value at every identifier position independently; and
9. sum of unsigned identifier bytes modulo `257`.

For each raw feature, register two single-feature policies: choose its minimum
or maximum. Ties choose the smaller display position. Also register the eight
constant display-position policies and lexicographic-min/max explicitly.

For every unordered pair of nonconstant raw features and each sign pair
`(+,+)`, `(+,-)`, `(-,+)`, `(-,-)`, convert both features to within-question
ordinal ranks using display position for ties, sum the signed ranks, and
choose the minimum summed value with smaller display position as final tie
break. These are the complete predeclared pairwise policies; no other
combination is inspected for a material gate.

The fixed material builder is a deterministic constraint solver, not a
resampling loop. Given the one declared seed, it binds relation assignments
and candidate order once while requiring, for AUTH and DERANGED separately:

- every single-feature and pairwise policy scores `<=4/16`;
- every candidate position is correct exactly `2/16`;
- authentic and deranged endpoints are both in every relevant eight-item
  list; and
- all output-token and role marginals remain exact.

Unsatisfiable constraints or a post-build score above `4/16` invalidate this
generator version. Do not increment a seed or search roots until one happens
to pass. Any repaired generator receives a new version and prospectively
declared seed before materialization.

The same-prompt AUTH/DERANGED paired redirection remains the decisive
shortcut control. The registry only closes the enumerated surface rules.

## 6. Custody and visibility

Materialize separate immutable roots for:

1. training-only atomic and skill tensors/manifests;
2. evaluation-only questions, answers, candidate orders, and null receipts;
3. raw model outputs; and
4. reduced scores.

The trainer process receives only root 1. Its manifest contains no evaluation
path, inode, hash, answer, candidate order, score, evaluator label, or prior
raw output. The evaluator receives a mounted adapter plus roots 2--4 and
cannot write or canonicalize an answer before strict parsing.

All D1 AUTH fitting completes before the D1 evaluation root is exposed. If the
raw D1 reduction prospectively opens D2, continuation runs in a new trainer
process whose namespace again contains only root 1; D1 evaluation/raw/reduced
roots are not mounted. D2 evaluation is exposed only after that continuation
ends. DERANGED is launched later from another clean trainer process whose
namespace contains only its coupled training root; it cannot traverse AUTH
evaluation or PROMPT-ONLY artifacts. Process command lines, environment,
mounted roots, hashes, open-file audit, and output paths enter the custody
receipt.

No PROMPT-ONLY or EVAL identifier may occur in JUNCTION/LOCAL; no `A,C` pair,
two-hop answer, scored question, or scored trace may occur in any training
byte. Exact substring, normalized-token, identifier-pair, rooted-signature,
and role-aware scans must all return zero before fitting.

## 7. LR0 semantics

LR0 runs AUTH atoms plus JUNCTION through the complete selected tape with LR
exactly zero. Standard LoRA initialization may contain a nonzero random `A`
tensor and zero `B` tensor; therefore LR0 integrity is defined by the
effective per-layer update:

```text
delta_W = scaling * B @ A
```

For every adapted layer, `delta_W` must be bitwise all-zero before and after
the LR0 tape. Hash every effective delta and record that optimizer step count,
batch order, losses, dropout draws, and training invocation completed while
no effective parameter update occurred.

BASE and mounted LR0 must emit byte-identical raw responses on their 80 common
greedy deterministic prompts. Any difference stops the experiment as
`UNSAFE_OR_LEAKED_PIPELINE`. Do not require every serialized A/B tensor to be
zero.

## 8. Dose and primary-safe stopping

The dose is unchanged.

At D1, per training state:

```text
32 atomic facts x 40 presentations = 1,280
32 skill rows   x  8 presentations =   256
total                               = 1,536 presentations
1,536 / batch 4                     =   384 optimizer updates
```

Fit LR0, ATOM-LOCAL, and ATOM-JUNCTION to D1 and preserve all checkpoints and
raw outputs.

Select D1 immediately if ATOM-JUNCTION satisfies:

1. LR0/material/custody integrity;
2. free one-hop Gate 1;
3. prompt-fact Gate 2;
4. authentic canonical two-hop threshold; and
5. canary preservation.

An underfit or failed ATOM-LOCAL at this point makes only the curriculum
contrast uninterpretable. It cannot force continuation of a successful
primary adapter. Train DERANGED-JUNCTION from the coupled clean start to D1
and apply the redirection gate terminally; DERANGED failure is not rescued by
D2.

If ATOM-JUNCTION does not qualify at D1, open D2 only when custody/canaries
remain intact and either:

- ATOM-JUNCTION misses a free one-hop acquisition threshold; or
- prompt-fact composition passes but learned-fact composition misses.

If free one-hop passes but the prompt-fact ceiling fails, stop at D1 as
`COMPOSITION_INTERFACE_NOT_QUALIFIED`; do not spend D2 on a post-result
interface rescue. When D2 opens, continue LR0, ATOM-LOCAL, and ATOM-JUNCTION
on their uninterrupted predeclared tapes to exactly double the counts:

```text
768 cumulative optimizer updates per state
```

D2 is terminal and selected prospectively by this branch. Then train
DERANGED-JUNCTION from the coupled clean start to D2. Never compare D1 and D2
and choose the better observed endpoint.

## 9. Gates

### Gate 0: material, custody, and LR0

Every overlap, role, tokenizer, batch, null, oracle, visibility, and custody
receipt above passes. Every LR0 effective delta is bitwise zero. BASE and LR0
raw bytes are identical on all 80 common prompts. Otherwise stop.

### Gate 1: free one-hop extraction

ATOM-LOCAL and ATOM-JUNCTION each require:

- first-hop exact canonical completion `>=15/16`;
- second-hop AUTH exact canonical completion `>=15/16`; and
- strict terminal output `>=30/32`.

DERANGED-JUNCTION requires unchanged first-hop `>=15/16`, assigned permuted
second-hop `>=15/16`, and strict terminal `>=30/32`. BASE and LR0 may score at
most `1/16` in either stratum. No candidate list appears on these calls.

Failure is `FREE_ATOMS_NOT_EXTRACTABLE`; no composition inference follows.

### Gate 2: prompt-fact ceiling

On target-disjoint PROMPT-ONLY, ATOM-JUNCTION with both exact relations
visible must emit the full correct trace on `>=14/16`; its empty-fact control
must score `<=4/16`. Report BASE, LR0, and ATOM-LOCAL identically.

If ATOM-LOCAL and ATOM-JUNCTION both reach `>=14/16`, junction demonstrations
were unnecessary for this prompt ceiling. If ATOM-JUNCTION is `>=14/16`,
exceeds ATOM-LOCAL by `>=4/16`, and ATOM-LOCAL is `<=10/16`, report only that
the target-disjoint junction curriculum package helped at this interface.

### Gate 3: parametric composition and content redirection

ATOM-JUNCTION must emit the exact AUTH trace on `>=14/16`. At the selected
dose, DERANGED-JUNCTION must emit its assigned exact trace on `>=14/16` of the
same byte-identical questions.

On `>=14/16` paired questions, both adapters must emit the same correct
intermediate `B_i`, then their different assigned endpoint, and terminate
with that endpoint. Cross-scoring against the other adapter's endpoint is
`<=2/16`. ATOM-JUNCTION exceeds BASE and LR0 by `>=10/16`. Both AUTH and
DERANGED retain `>=15/16` generic canaries with a gap `<=1/16`.

ATOM-LOCAL receives a curriculum interpretation only after it independently
passes Gate 1. If it reaches `>=14/16`, local practice was sufficient and
junction demonstrations were unnecessary. If ATOM-JUNCTION exceeds an
acquired ATOM-LOCAL by `>=4/16` while LOCAL is `<=10/16`, the junction
curriculum package helped. Every middle pattern is ambiguous.

### Direct output: descriptive only

Report ATOM-JUNCTION and DERANGED direct-answer accuracy beside canonical
trace accuracy. No threshold gates the primary claim. Do not write
`CoT-enabled`, `CoT necessary`, `latent composition`, or infer internal token
mediation from the gap. A causal format comparison requires a separately
bound, dose-matched direct-trained state and is outside this successor.

## 10. Frozen resource arithmetic

Replacing candidate-assisted one-hop calls with no-candidate calls changes no
count or token cap. Keeping direct calls descriptive also changes no work.

At a D1 selection:

```text
4 training invocations
1,536 optimizer updates total
448 model calls
83,968 generated tokens maximum
```

On the terminal D2 path:

```text
7 training invocations
3,072 optimizer updates total
736 model calls
139,264 generated tokens maximum
0 external-reader calls
```

Continuation is a new invocation but not a fresh lineage. Record actual
target tokens/update, elapsed seconds/update, generated tokens, engine load
time, and peak memory. These are caps, not elapsed-time forecasts.

## 11. Scheduling relative to M-COMBINE-4

EVENT-retention-v2 acquisition must qualify this numerical writer family
before P-CHAIN-2 fitting. A failed writer prerequisite stops P-CHAIN-2 without
a heat/rank rescue.

P-CHAIN-2 does **not** serially gate M-COMBINE-4 Stage 2A. P-CHAIN-2 tests
parametric atom extraction/composition; M-COMBINE-4 tests a supervised
READ/STEP/CHECK/STOP controller over an exact text service. Their source work
and, after their separate gates, model work may proceed in parallel. Both
must qualify before binding a later same-adapter memory-plus-controller
junction.

P-CHAIN identifiers, texts, outputs, and adapters are DEV-only and forbidden
from later clean M-COMBINE confirmation, personal-memory, GOAL-BRAID, or
paper-grade lineages.

## 12. Allowed terminal wording

If all gates pass while endpoint candidates remain in the two-hop prompt:

> In a single-seed development ceiling, a rank-8 adapter freely generated
> each separately supervised opaque NEXT atom in isolation, freely generated
> the correct intermediate on held two-hop queries, and selected its assigned
> endpoint. A same-identifier counterfactual adapter preserved the first atom
> and redirected the second-hop selection and final answer under its alternate
> learned binding.

Add `the target-disjoint junction curriculum package helped` only under the
registered acquired-LOCAL margin. Do not claim that the printed intermediate
causally mediated the answer, explicit CoT was necessary, the facts were
independently acquired, or this was retained/own-life/autonomous memory.

## 13. Closed authority

This successor resolves the audit at the design level only. It grants no
authority to author a generator or runner, materialize a fixture, invoke a
tokenizer or model, fit or mount an adapter, use a GPU, touch a remote node,
or make a scientific claim. Any such scope requires an explicit later ruling
under the repository operating contract.

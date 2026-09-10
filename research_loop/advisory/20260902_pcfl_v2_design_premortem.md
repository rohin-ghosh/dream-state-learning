# PCFL-Compose staged-v2 design premortem

**Date:** 2026-09-02  
**Status:** pre-authoring, read-only scientific/design advisory. This document
was written before inspection of any authored v2 proposal bytes. It does not
create, edit, approve, or ratify v2; authorize implementation, model, CPU, GPU,
or network work; or license a scientific, paper, or public claim.

## Bound inputs and assumed decisions

This premortem is bound to the following exact inputs:

- `20260902_pcfl_v1_value_and_efficiency_audit.md`, SHA-256
  `376d6e60d760407dbf7b983955c9d675880aa2affbf523755b84493385686a9a`;
- `20260902_pcfl_v1_interpretation_repair_map.md`, SHA-256
  `c0d02d4f08141c5b6bd7a6015681efe961d94c625d237e3e1916861b4770ca84`;
- `20260902_pcfl_v2_roster_adjudication.md`, SHA-256
  `471d001b76963ab7bd3032cc535f9c4ce733cc2a002c985aaab19d45803a9066`;
- `20260902_pcfl_v2_staged_roster_arithmetic_audit.md`, SHA-256
  `75d2c22fe25b934fa5735c51b247a47847104b50d17da4083aa6592aea7510d8`;
- v1 adjudicated consensus, SHA-256
  `3293b8386241417f74457fc360a356981066d1c9af4e3a5b88e09239734e1b63`.

The following design decisions are treated as binding for this review rather
than reopened:

1. the all-pass staged scientific roster has exactly 3,414 assigned model-call
   opportunities: 484 Dream, 2,926 recurrent Think, and four structured
   one-shot Think;
2. one-shot Think is structured-only and supports no claim about recurrence in
   `OPAQUE_NOTE_SELF`;
3. there are no optional model panels, including no failure-triggered model
   diagnostics, A-MEM, RAG, prompt variants, public-gate variants, or AST cuts;
4. every eligible arm receives the same mechanically defined, factor-blind
   event extractor;
5. Dream commits a content address for an immutable staged object rather than
   repeating the object in the terminal response; and
6. opaque notes have a strict nonsemantic evaluator boundary.

The accepted v1 repairs are assumed: typed pre-READ catalogs, explicit RNG and
private-field contracts, q-specific controls, failure-inclusive row reduction,
separated prediction/revision/action language, versioned canonicalization,
actual-versus-CPU call ledgers, and exact-root DEV-only reporting. Repeating
those twenty concerns would add little. This review asks what can still go
wrong after those repairs are made.

## Strongest case for the staged design

The staged design is a materially better DEV purchase than v1's simultaneous
full panel. It retains the exact construct theorem, one immutable Dream-1
forked over two public-A continuations, prospective B commitments, physical
goal-conditioned action, whole-corpus interventions, same-q independent
controls, an untouched factor root, and a non-rescuing structured diagnostic.
It removes discretionary diagnostic routing, declines an unidentifiable opaque
one-shot Think comparison, uses common preprocessing, and fixes the terminal
copy-cap contradiction with an immutable object reference. If its gates and
interfaces are frozen literally, 3,414 is a coherent all-pass branch subtotal
and the design can efficiently answer whether this exact prompted organism is
worth a separately powered and post-context program.

That is meaningful value. It is still possible, however, to obtain a clean
green receipt while having tested a weaker or different proposition than the
paper-facing story suggests. The main remaining hazards arise from interactions
among staging, preprocessing, content addressing, opacity, and sparse selected
cells—not from the already-adjudicated v1 defects in isolation.

## Premortem verdict

**The staged design is authorable, but not yet self-sealing.** A v2 author must
resolve the obligations below in the frozen bytes. Four issues are especially
easy to miss:

- passing Stage 1 conditionally opens Stage 2, so “untouched” is not an
  unconditional replication and cannot be pooled with the open root;
- common factor-blind extraction can silently become the real symbolic solver
  or bypass Dream's charged read-selection loop;
- content addressing can expose corpus identity as a causal side channel and
  fixes terminal duplication without proving the full object fits the earlier
  `PREDICT` generation cap; and
- the 3,414 roster tests whole-corpus action causality only on one preselected
  h branch and does not test h-swapped corpus mediation.

Any one of these can leave the software internally consistent while making the
scientific description too strong.

## New risk register

### `V2_PM_R01`: Stage-gated evidence is conditionally selected

Stage 2 is observed only if the open root passes a large conjunction in Stage
1. Presealing the untouched and independent roots prevents result-contingent
root replacement, but it does not make their evidence unconditional. The
realized Stage-2 dataset is selected on success of the same model, prompts,
harness, and construct family on the open root. Pooling the open and untouched
roots, calling the latter a replication, or describing two-factor-root success
without the gate condition hides this selection.

The author must define “untouched” narrowly: its bytes, selected sides, target
packets, model assignments, and analysis rows were sealed before Stage 1 and
were not used for model-facing debugging or protocol revision. It means
output-blind conditional canary, not an independent confirmatory replicate.
Stage-1 and Stage-2 summaries must remain separate. `NOT_TRIGGERED` Stage-2
rows are not zeros in a factor performance mean, and a Stage-2 pass may not be
used to reinterpret the Stage-1 gate that selected it.

### `V2_PM_R02`: “Untouched” can be lost operationally between stages

Even with sealed JSON, implementers can inspect root payloads, patch a parser,
restart a model server with different caching, or alter a timeout after seeing
Stage-1 outputs. That is an adaptive protocol change even when root IDs and
prompts do not change. Global prefix caches, object stores, tokenizer caches,
error counters, and process-local state can also carry open-root information
into the supposedly fresh Stage-2 sessions.

The executable bundle—not only the scientific assignment table—must be hashed
and locked before Stage 1: code, dependency/container image, model revision,
tokenizer, renderer, canonicalizer, extractor, reader, sampler, timeouts,
device topology policy, and environment allowlist. No midstream repair is
permitted. An implementation or infrastructure defect ends the staged run and
requires a new authorized execution; it cannot be patched before opening the
sealed roots. A reset test must cover global caches and the content-addressed
store, not only model KV state.

### `V2_PM_R03`: The 3,414 roster supports selected-h corpus causality only

The arithmetic is exact only under the narrow selected-h reading. In Stage 1,
EMPTY, crossed-antipode, and sham each run for one presealed h over z plus
antipode. The other h branch receives authentic SELF evaluation but no matched
corpus cuts. The analogous Stage-2 whole-corpus rows are also on one ordinary
h. Therefore the frozen reducer may establish raw-A-conditioned B commitments
on both h branches, but the memory-value, crossing, sham, and action-redirection
contrasts apply only to the selected h.

The v2 bytes must name that h before any output and attach every causal clause
to its actual row keys. They must not average the selected-h cuts with the
uncut h, claim action causality on both h branches, or use the both-h SELF rows
as if they supplied missing both-h controls. Expanding those cuts to both h
would add 372 recurrent-Think calls before any other change and would no longer
be the binding 3,414 design.

### `V2_PM_R04`: No h-swap means the revision-to-action mediation path is untested

The staged roster varies raw A across h and observes Dream-2 commitments, then
varies authentic versus antipodal-z/sham corpora at target time on a selected
h. It does not place the h=0 committed corpus into the h=1 target world and
vice versa at fixed z. Thus it separately identifies an A-to-Dream-2 response
and a selected-h whole-corpus-to-action effect, but not the mediated proposition
that the h-specific revision selected by raw A is what caused the h-specific
later action.

Content-address inequality across h is insufficient: two opaque byte strings
can differ without the difference doing useful work. Exact B commitments are
also insufficient: B predictions can change while the same corpus supports
both branches. Because the roster is binding, v2 should explicitly leave
h-specific corpus mediation untested. It must not say “raw A revised memory,
which thereby caused the branch action.” If that sentence is scientifically
required, an h-crossed corpus intervention must be added, its targets and seeds
predeclared, and the 3,414 arithmetic abandoned and recomputed.

### `V2_PM_R05`: A factor-blind extractor can still be an engineered oracle

“Factor-blind” is a necessary but weak runtime property. An extractor can omit
the family flag yet use cross-event state, a factor-specific canonical frame,
known graph topology, closure tables, shortest words, orientation/gauge
normalization, or root-wide regularity to hand the model the latent solution
basis. It can also expose all extracted events at once and thereby remove the
model-owned read-selection question. Common use across factor and independent
arms does not cure either problem.

The permissible extractor should be a pure, stateless, event-local map from one
already-public before/after tray pair and public item labels to the literal
observed permutation in those labels. It must receive no root, family, h/q,
graph, history, target, goal, certificate, comparator, or private orientation
input; maintain no cross-event cache; and emit no decomposition, closure,
path, inverse table, group word, canonical gauge, or factor name. Its output
must appear only inside the charged read receipt for the selected event. A
pre-READ catalog or workspace containing extracted values for unread events
would bypass the recurrent Dream treatment.

The exact extractor source/hash belongs in the proposal. Stage 0 must show
equivariance under arbitrary global public-label relabelings, totality on every
legal S6 permutation, identical code paths for factor and null roots, and
preservation of the independent target's conditional `1/16` law after the
complete renderer/extractor interface—not merely in the abstract generator.

### `V2_PM_R06`: Common extraction narrows the construct and claim

Supplying exact observed permutations to every eligible arm is a defensible
fairness decision, but it changes the task. A positive result is no longer
evidence that the model inferred operators from raw before/after trays. It is
evidence about selection and connection over mechanically extracted public
operators, followed by opaque compilation and target-time use. If both raw
trays and extracted permutations are returned, the extractor remains supplied
scaffolding; the model need not use the raw bytes.

The prompt and result descriptor must name this preprocessing. “Learned from
raw experience,” “discovered the event algebra,” “autonomous schema
discovery,” and any visual/perceptual induction language are out of scope. The
factor/independent comparison localizes connection under a supplied local
operator representation. A future raw-only ablation would require another
design; no optional panel exists in this v2 to answer it.

### `V2_PM_R07`: Content-addressed COMMIT can become an identity side channel

A digest is safe as a harness integrity key only if it is not also a model-
visible treatment label. If target-time prompts, reader catalogs, candidate
catalogs, or note IDs expose content hashes, authentic, crossed, and sham
conditions are distinguishable before any note byte is read. The model can
condition an action on the hash string itself. Similarly, a fresh Dream-2 can
compare candidate hashes before paying a candidate read. A resulting action
difference is a corpus-identity effect, not evidence of literal retrieval and
use.

The design needs two identifier layers. Model-visible catalogs use fixed,
opaque, per-session capability handles whose names, count, order, and envelope
metadata are invariant across interventions. Harness-only content addresses
verify immutable storage. A commit capability may be revealed only after the
model has staged the corresponding object and must not survive into an
unrelated life or target prompt. For every authentic/crossed/sham/EMPTY pair,
a rendering-diff test must prove that no digest, variant name, storage path,
dedup flag, or cache status is visible; only authorized reader returns and
their downstream model-owned consequences may differ.

### `V2_PM_R08`: The digest must bind the whole scientific object

Replacing repeated bytes with a hash changes the ownership boundary. A Dream-2
digest over only the note payload does not bind the already-staged B
predictions, RETAIN/REVISE decision, parents, citations, representation lane,
or their order. Those fields could be altered after the apparent commit. A
generic digest can also be replayed across Dream phases, roots, lanes, or
sessions; global content deduplication can alias objects across lives.

Use a versioned, domain-separated commitment manifest that binds at least the
change/contract version, phase, lane, root/session namespace, candidate slot
or ordered candidate set, complete canonical envelope, every prediction,
decision, parent, citation, and payload byte. Dream-1 must bind A1/A2 and the
ordered current candidates; Dream-2 must bind B1/B2 and the complete staged
decision. Mutation of any bound byte, stale-object selection, cross-phase
reuse, cross-root reuse, reordered candidates, or post-commit write must fail.
The model must emit an explicit valid commit capability; the harness may
verify and materialize it but may not choose or auto-commit an object. Reports
must say “the model selected an immutable object that the harness materialized
by content address,” not that the model regenerated the object at COMMIT.

The store must be per-run/per-life namespaced even for identical content. No
global dedup hit, object-existence test, cache timing, or shared pointer may
cross the reset boundary.

### `V2_PM_R09`: Content addressing fixes COMMIT, not PREDICT generation

The v1 terminal contradiction disappears only at the last operation. A full
candidate still has to be generated and staged by `PREDICT`. Under the carried
v1 maxima, a complete candidate may occupy 8,192 UTF-8 bytes while one
`PREDICT` call receives at most 2,048 generated tokens. Legal byte strings can
require roughly one token per byte under byte fallback, before the JSON
envelope, predictions, citations, and escaping are counted. Two candidates in
a one-shot Dream-1 object create the analogous problem. A short terminal hash
does not make those earlier legal maxima executable.

Before freezing v2, the author must choose one coherent repair: lower complete
object and field byte caps to tokenizer-proven maxima; increase PREDICT and
one-shot output entitlements and recompute all phase/token/device envelopes;
or define a model-owned chunked staging protocol and account for every added
operation/call. A maximum-object test must use the pinned production tokenizer
and adversarial valid UTF-8/JSON strings, not only the compact 2,510-byte AST
fixture. It must prove every legal recurrent and one-shot staged object fits
both its per-call and phase-cumulative output cap. Otherwise T06/T07/T16 remain
unsatisfiable despite content-addressed terminal commits.

### `V2_PM_R10`: Opaque notes are untrusted prompt data, not inert data

The nonsemantic rule allows an opaque note to contain delimiter strings,
JSON-looking fields, action names, imperative prose, Unicode controls, or a
complete self-instruction. When literal note bytes are inserted into a later
prompt, they can alter model behavior by prompt injection. That behavior may
be a legitimate part of this self-authored memory interface, but it cannot be
described as proof that the model reasoned over a latent factor representation.
Nor may rendering bugs let note text escape its data field or spoof system,
target, citation, or action-schema bytes.

Opaque bytes must be framed through one length-delimited, escaped, canonical
data channel with no string concatenation into control syntax. Adversarial
fixtures must include prompt delimiters, apparent role headers, braces/quotes,
newlines, NUL-like escapes, bidi/control characters, action tokens, and valid
maximum-size text. The parser must show that these alter only the note value
and can never add a field, change a role, expose hidden bytes, or bypass
USE/LOCK validation. This is a syntactic guarantee only: v2 must explicitly
allow that the model can follow instructions contained inside the note and
must call the endpoint a causal effect of the opaque byte corpus, not a
semantic-mechanism result.

### `V2_PM_R11`: Strict opacity constrains sham validity and qualitative reporting

A “footprint-matched” opaque sham is not automatically a matched nuisance
control. Equal envelope count and byte-length bucket may leave large
differences in tokenizer length, index postings, lexical accessibility,
NOT_FOUND rate, cursor depth, and returned-byte count. Matching those fields
after seeing target queries, however, would be target-aware and potentially
result-contingent. The author must predeclare a target-independent sham
constructor and state exactly which mechanical properties it matches and does
not match. A sham failure cannot be promoted into evidence that authentic note
meaning was correct.

The same nonsemantic boundary applies after scoring. A human or model cannot
read successful notes and then characterize them as a factor law, explanation,
plan, abstraction, or absence of a solution packet. Default reports should
surface hashes, provenance, sizes, mechanical retrieval receipts, predictions,
and actions—not selected prose examples. Any later qualitative interpretation
must be a separately labeled, non-gating exploratory analysis with no role in
the frozen endpoint, and it still cannot retroactively establish the primary
causal mechanism.

### `V2_PM_R12`: The four structured one-shot Think calls need an exact estimand

The four-call arithmetic requires exactly two presealed root-lives—one factor
and one independent, each with one h/q continuation and one z side—and two D4
goal twins per life. “The matched OPERATOR_AST cells” is not sufficient if it
can also mean z plus antipode or both continuations. The exact root, h/q, z,
target, goal, AST corpus, iterative comparator, and coupling group must be in
the T0 assignment table.

A one-shot D4 planner emits an open-loop action sequence in one call, whereas
the 31-operation iterative arm can see intermediate action trays and adapt its
queries/actions. Giving those trays to one-shot after each action would no
longer be one call. The contract must freeze open-loop physical execution,
illegal/short/early-lock scoring, full sequence requirements, and the one-shot
output cap. It must say that the comparison changes interaction and feedback,
not recurrence alone. Its result applies only to those two selected structured
D4 packets: one-shot failure cannot prove iterative Think necessary, and
one-shot success can remove at most a claim about that disclosed structured
interface.

### `V2_PM_R13`: “No optional panels” must remove all adaptive model-call escape hatches

The earlier advisories contain failure-triggered AST, class-informed, gate,
RAG, neutral, and structural-cut panels. The binding design rejects them. If
even one survives in a routing table, 3,414 is only a subtotal and the old
adaptive-cap defect returns. Likewise, the 186 calls between 3,414 and a 3,600
hard stop are safety slack, not a discretionary reserve.

The assignment ledger must enumerate exactly 3,414 scientific call
opportunities on the all-pass branch and no optional scientific row. A
Stage-1 scientific failure makes every Stage-2 row `NOT_TRIGGERED` and ends
model science; it does not dispatch a failure panel. A-MEM/RAG/prompt variants
and all other excluded arms are `NOT_IN_SCOPE`, not latent `NOT_RUN` choices.
Malformed, timeout, and charged PASS calls count against the appropriate
session and process cap and are never replaced.

If two infrastructure replays remain, their triggers, exact source call IDs,
seeds, allowed purpose, and disposition must be frozen. Replay output may not
replace the first scientific output or enter a scientific denominator. A
byte mismatch invalidates the claimed deterministic replay receipt rather than
selecting the better output. The process maximum is then 3,416, while 3,600 is
only a kill switch. If replay policy is not exact, remove the replays.

### `V2_PM_R14`: “3,414 successful calls” is the wrong accounting noun

The arithmetic counts maximum assigned invocation opportunities on the
all-pass stage branch. It is not a promise that 3,414 responses will be valid
or that a successful session always consumes its maximum operations. Using
“successful calls” can cause malformed attempts, timeouts, early commits, or
replays to disappear from the ledger and token/time estimates.

The manifest must separately count assigned opportunities, attempted model
invocations, valid parsed responses, charged malformed/PASS responses,
infrastructure failures, scientific replays, and completed row outcomes. The
headline should be “3,414-call all-pass-branch scientific ceiling,” not “3,414
successful calls.” Every attempt consumes call and token budgets. No
denominator is keyed to valid response count.

### `V2_PM_R15`: Token and storage costs do not shrink with the terminal hash

Content addressing avoids terminal regeneration but not initial generation,
candidate reads in fresh Dream-2, repeated live-state prompts, Sleep
materialization, index construction, or target-time reader returns. The common
extractor also adds bytes to every relevant read receipt. Linear extrapolation
from call count can therefore understate combined tokens even if the output
subtotal looks smaller.

The resource manifest must sum input and output entitlements from literal row
and operation assignments. It must account separately for raw tray bytes,
extracted permutation bytes, catalogs, workspace, staged-object capabilities,
candidate read payloads, repeated prompt/schema bytes, AST/NOTE bytes, reader
returns, and one-shot packets. The pinned tokenizer must render maximum legal
states for recurrent Dream, fresh Dream-2, recurrent Think, one-shot Dream,
and structured one-shot Think. The proposed 3-million-output, 36-million-
combined, 14-device-hour, and 20-wall-hour figures may survive only if that
literal proof fits them; they cannot be inherited from the advisory estimate.

### `V2_PM_R16`: The independent alarm needs joint-orbit calibration

The proposed deterministic specificity alarm uses four rows per q (z plus
antipode by two goal twins). Those rows are nested and algebraically coupled;
they are not four Bernoulli trials. A “three of four” rule or two positive
means cannot be assigned a binomial false-alarm interpretation. Certain fixed,
target-blind action policies may induce correlated success across twins or
antipodes even under the conditional-independent q construction.

Stage 0 should exhaustively enumerate the joint four-row success vectors under
the exact rendered q target packets for all legal target-blind deterministic
plans (and any declared stochastic policy coupling), report the worst-case
alarm rate under the uniform private prior, and freeze the alarm truth table.
If that calibration is not meaningful for the model policy class, call the
rule a conservative descriptive warning only. It is not a p-value, specificity
estimate, or proof of factor identification. A factor-positive/independent-
quiet outcome on one root pair remains a DEV signature, not generalization.

### `V2_PM_R17`: Failure-mediated differences must not count as action redirection

A crossed corpus can lower exact success by causing abstention, malformed
output, illegal actions, unavailable reads, or early lock. That establishes a
whole-interface effect but not the stronger claim that memory redirected a
goal-conditioned physical policy. Similarly, a sham that crashes or retrieves
nothing is not a matched demonstration that nuisance bytes have no effect.

The action endpoint needs a literal truth table. “Redirection” should require
two valid executions with distinct registered first legal actions (and, where
claimed, the registered complementary exact sequence), not merely a success
difference or one zero-valued failure. Failure remains zero for totality but is
reported under a distinct failure-effect endpoint. Golden reducer fixtures
must enumerate authentic success/control failure, authentic failure/control
success, both failure, ties, different wrong legal actions, malformed, early
lock, and true complementary redirection. Only the row patterns declared
beforehand may open Stage 2 or support the action-causality clause.

### `V2_PM_R18`: The public-prefix causal diff set grows in v2

The h fork's intended treatment is raw public A and its declared mechanical
descendants. With a common extractor and content-addressed staging, additional
derived fields exist: extracted permutation, payload digest, read receipt,
staged-object digest/capability, cache status, and serialized lengths. Some are
legitimate descendants after a charged read; others are forbidden labels.
Saying “raw A only” without naming this set is inaccurate.

Freeze an end-to-end causal-diff allowlist. Before A, the two h renderings,
catalogs, Dream-1 object/capability, seeds, caches, and traces must be
byte-identical. After A, allowed differences are raw A bytes, the pure
extractor output, the charged read digest/count, and model-authored downstream
state. h labels, variant names, storage addresses, target fields, outcome
metadata, and branch-specific timeouts remain forbidden. A differential trace
test must fail on any difference outside that transitive allowlist. The report
may then say “raw A plus its frozen mechanical extraction changed Dream-2,”
not that literally no derived byte differed.

## Exact pre-authoring acceptance obligations

The v2 author should create acceptance tests at least as strong as the
following. IDs are advisory placeholders; the authored proposal may map them
to its own stable IDs, but no obligation should disappear.

| Premortem test | Exact obligation before ratification |
|---|---|
| `V2_PM_T01_STAGE_CONDITIONALITY` | Given every possible Stage-1 gate result, materialize the complete terminal row-status table. Prove Stage 2 opens only on the one frozen all-pass vector, `NOT_TRIGGERED` rows never enter a mean, Stage-1 and Stage-2 roots are never pooled, and report lint rejects “replication,” “two-root estimate,” or an unconditional untouched-root claim. |
| `V2_PM_T02_EXECUTABLE_FREEZE` | Hash the complete executable environment before Stage 1; audit that no code/config/model/tokenizer/extractor/timeout/cache policy changes between stages; force a simulated infrastructure defect and require terminal invalidation rather than patch-and-continue. |
| `V2_PM_T03_UNTOUCHED_ACCESS` | Preseal open, untouched-factor, and independent root/side/target artifacts; expose only allowed Stage-0 certificates; log access; inject cross-stage cache/object-store canaries; prove no open-root model or note bytes are readable in any Stage-2 process. |
| `V2_PM_T04_SELECTED_H_SUPPORT` | Freeze the selected h and z before output and enumerate claim support by exact row key. Golden analysis must reject any both-h memory/action aggregate while the roster stays 3,414 and must show that adding the missing h cuts changes the scientific ceiling by 372 calls. |
| `V2_PM_T05_NO_H_MEDIATION_CLAIM` | Construct synthetic outputs where h changes B predictions and corpus hashes but only a z-crossed corpus affects action. Require the result generator to report the two separate causal clauses and reject h-revision-mediated-action wording. |
| `V2_PM_T06_EXTRACTOR_PURITY` | Run the exact extractor on all legal permutations and adversarial factor/null events; prove stateless event-local dependencies, global-label equivariance, family/root/graph/target independence, no cross-event cache, and no emitted closure/path/decomposition/orientation/gauge feature. |
| `V2_PM_T07_EXTRACTOR_READ_GATE` | Render recurrent Dream traces with unread event payloads/extracted values mutated. Before the corresponding charged READ, catalogs, prompts, workspace, and decisions must remain identical; after READ, only the selected raw event and declared extracted record may enter state. |
| `V2_PM_T08_RENDERED_NULL_THEOREM` | Recompute the q conditional target distribution after canonical rendering, extraction, handle assignment, and reader serialization. For every visible extracted prefix and A receipt, the exact B/target fiber remains the declared conditional null; abstract-generator certification alone does not pass. |
| `V2_PM_T09_COMMIT_INTEGRITY` | Mutate each prediction, decision, parent, citation, payload byte, order, phase, lane, root, and session namespace; verify the commit fails. Reject stale, cross-phase, cross-life, and reordered capabilities; require an explicit model COMMIT and prove the harness never chooses one. |
| `V2_PM_T10_HASH_INVISIBILITY` | Across authentic/crossed/sham/EMPTY target-time variants and before candidate reads, compare rendered model-visible bytes. Content digests, object paths, dedup/cache flags, and variant labels must be absent; fixed opaque handles and metadata must match exactly. |
| `V2_PM_T11_MAX_STAGEABLE_OBJECT` | With the pinned tokenizer and worst-tokenizing valid UTF-8/JSON fixtures, generate every maximum NOTE/AST candidate, prediction envelope, two-candidate one-shot object, and Dream-2 revision. Each must fit the actual PREDICT/one-shot and cumulative output caps; no truncation, repair, or harness-authored chunk may occur. |
| `V2_PM_T12_OPAQUE_RENDER_SAFETY` | Feed delimiter, role-header, JSON, newline, control-character, bidi, action-token, and maximum-size adversarial notes through the real reader and prompt renderer. They may alter only a length-delimited note value and may not add control fields, change roles, bypass schema/action validation, or expose hidden data. |
| `V2_PM_T13_SHAM_CONTRACT` | Freeze the target-independent sham constructor and verify every claimed mechanical match—envelope count/order, fixed handles, provenance graph, byte and tokenizer caps, document/index shape, and declared reader nuisance measures. Report and lint every property not matched; never label the sham semantically false. |
| `V2_PM_T14_STRUCTURED_ONESHOT_ROWS` | Materialize exactly four one-shot Think assignments: two frozen root-lives by two D4 goal twins, with one preselected h/q and z each. Bind the matching AST bytes, iterative rows, target packets, seeds, open-loop execution, output cap, and failure rules; reject any recurrence-necessity or opaque extrapolation. |
| `V2_PM_T15_EXACT_3414_LEDGER` | Sum an exhaustive assignment table to 484 Dream + 2,926 recurrent Think + 4 structured one-shot Think = 3,414 on the all-pass branch. Prove no optional model row exists, safety slack is unusable scientifically, failures count, Stage-1 failure dispatches no model panel, and any replay is bounded and non-replacing. |
| `V2_PM_T16_LITERAL_TOKEN_ENVELOPE` | Sum per-row/per-operation input and output maxima including extractor bytes, staged-object reads, repeated state, prompts, reader returns, and one-shot packets. Render maximum legal inputs/outputs and demonstrate compliance with model context, 3M output, 36M combined, storage, device, and wall limits—or revise the limits and roster before deliberation. |
| `V2_PM_T17_SPECIFICITY_CALIBRATION` | Exhaustively enumerate joint q-side/antipode/goal-twin success vectors under legal target-blind policies, freeze the exact alarm truth table, and report its worst-case null behavior. Lint out binomial, p-value, prevalence, or proof-of-identification interpretations. |
| `V2_PM_T18_REDIRECTION_TRUTH_TABLE` | Evaluate every success/failure/tie/wrong-action/complementary-action endpoint combination. Only two valid, distinct registered action executions may count as redirection; failure-mediated differences remain separately visible and cannot satisfy the stronger action clause. |
| `V2_PM_T19_CAUSAL_DIFF_ALLOWLIST` | Differentially trace both h branches through raw A, extraction, read receipts, staging, and commit. Require exact pre-A identity and allow post-A differences only for raw A, pure mechanical descendants, and downstream model-owned state; fail on h/variant/hash/cache/target side channels. |
| `V2_PM_T20_REPORT_BOUNDARY` | Run forbidden-phrase and structured-claim fixtures over every generated summary. Reject raw-perception discovery, h-mediated action, semantic-note interpretation, recurrence benefit, comparator superiority, replication/generalization, persistence/compression, or paper-efficacy language. Require the exact-root, conditional-stage, common-extractor, selected-h, opaque-byte, harness-materialization qualifications. |

## Minimum claim boundary for a green v2

If every authored v2 gate passes, a defensible internal description is no
stronger than:

> On a predeclared open DEV factor root and, conditional on its frozen all-pass
> gate, one sealed factor and one independent DEV root, the frozen resolver
> authored and explicitly selected immutable opaque byte objects from charged
> reads of public events accompanied by a common mechanical per-event
> permutation extractor. In both public-A continuations it made the registered
> prospective commitments. On the preselected h rows that received corpus
> interventions, changing the already-frozen corpus changed later physically
> executed actions under the registered truth table. The independent rows and
> structured diagnostics were reported separately under their exact frozen
> interfaces.

Even that paragraph must be shortened when a constituent gate fails. It does
not say that the model discovered operators from raw trays; that h-specific
memory revision mediated action; that opaque notes contained or omitted a
factor program; that recurrence was beneficial; that content addressing was a
model memory mechanism; that the sealed root was an unconditional replication;
or that the result is population, benchmark, lifetime, LoRA, or paper evidence.

## Final disposition

Proceed to authorship only if the v2 proposal makes these obligations literal
and hash-bound. The highest-priority blockers are maximum stageable-object
capacity after the content-address repair, extractor locality/read gating,
digest invisibility and whole-object binding, selected-h claim support, and the
absence of h-specific mediation. The stage and paper boundaries are not prose
polish: they determine which causal graph the 3,414-call roster actually
identifies.

After the v2 bytes exist, they require fresh independent interpretation,
adversarial critique, adjudicated consensus, and exact human ratification. This
premortem cannot substitute for any of those gates.

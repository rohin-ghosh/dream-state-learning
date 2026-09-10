# One-parent/one-child strong-baseline closure audit v8

Date: 2026-09-06

Status: fresh independent read-only closure audit of the current proposal
bytes after the v7 repairs. I read `AGENTS.md`, the complete headline plan,
supporting contract, source-bound prompt schema, scope proposal, and closure
audits v6 and v7. This advisory changes no candidate byte and authorizes no
implementation, model/tokenizer call, benchmark generation, adapter
operation, external deliberation, or GPU use.

## Verdict

**REVISE.** The two exact v7 repairs are present. The merger now constructs
one exact canonical prescribed `CURATE` response, measures the generated
assistant suffix under the pinned official chat template plus exactly one EOS,
accepts 384 and rejects more than 384 before the call, and preserves the
accepted `REFLECT` on that no-call path. Certificate execution now totally
accounts for both valid-`REFLECT` pre-`CURATE` input overflow and prescribed-
output unrepresentability with unchanged store, normal reflection scoring,
exactly one gold-class false negative, no `CURATE` false positive, and no case
exclusion.

The proposal still does not close the larger operation-totality invariant.
The pre-call selector does not test whether its fully derived transition can
satisfy the stored-record cardinality and 256-token constraints after ID
assignment, evidence union, link insertion, sorting, recomputation, and
provenance assignment. Consequently a valid accepted `REFLECT` can prescribe
a response that fits the outer 384-token-plus-EOS ceiling but for which the
only exact prescribed transition is necessarily rejected. This is a narrow
contract defect, not a topology, estimand, resource, or baseline redesign.

## Disposition of the two v7 blockers

### 1. Exact prescribed `CURATE` serialization under 384 including EOS

**CLOSED for the outer response-length question.**

- The contract constructs the complete canonical object from the accepted
  model-produced reflection and immutable pre-call store, including top-level
  fields, ordered deltas, complete embedded records, prior hashes, and sole
  `NOOP` where applicable.
- The exact measurement domain is the generated assistant-response suffix
  token IDs for those canonical JSON bytes under the official pinned chat
  template, followed by exactly one pinned EOS token.
- The comparison is `>384`, so 384 including EOS is accepted and 385 is a
  deterministic `OUTPUT_UNREPRESENTABLE` no-call. Nothing may be shortened,
  omitted, truncated, or moved to another partition.
- The same rule appears in the headline and model-visible schema. Required
  model-free fixtures cover one through four deltas plus inclusive 384 and
  rejecting 385 boundaries.
- No tokenizer was called in this audit. The later exact receipt remains a
  hard gate; proposal bytes do not assert measured fit.

This closes v7's literal outer-ceiling defect. It does not by itself prove
that the prescribed delta is a legal post-merge store transition, which is the
new blocker below.

### 2. Certificate accounting for valid `REFLECT` with pre-`CURATE` no-call

**CLOSED.**

- Before sealing, every gold fixture must have exact gold second-call input
  bytes within all fixed partitions and an exact gold prescribed response plus
  one EOS within 384. Thus the gold unit itself is not allowed to rely on an
  input/output-size skip.
- At execution, only the accepted canonical model-produced `REFLECT`, never
  gold `REFLECT`, constructs the required input and prescribed response
  against the immutable pre-call store.
- If that model-produced path has `INPUT_OVERFLOW` or
  `OUTPUT_UNREPRESENTABLE`, the second call is not made, the temporary store is
  sealed unchanged, the emitted reflection is scored normally, the fixture's
  presealed `CURATE_CLASS` receives exactly one false negative, no `CURATE`
  false positive is added because no prediction attempt occurred, and the case
  is never excluded.
- The contract supplies zero-denominator behavior and keeps this no-call path
  inside the ordinary eight-class macro-F1 and recall denominators.

## Remaining exact blocker: prescribed transition feasibility is not preflighted

The selector processes valid items against the immutable store and its stated
pre-`CURATE` rejection set covers `ADD_CONTRADICTED`, repeated changed/created
IDs, conflicting link-source mutation, and dependence on an in-call changed
ID or hash. It does not cover deterministic post-transition record bounds.
Three reachable construction families remain:

1. **Evidence-union overflow.** A legal live record may already contain 16
   support IDs. A concise, otherwise valid same-key/same-signature reflection
   can cite a new complete observation. Rule 2 unconditionally prescribes
   `REVISE`, requires the union of old and new evidence, and forbids discarding
   old evidence. The derived replacement therefore has more than 16 support
   IDs, while every stored support/counter array is capped at 16. The same
   construction applies on the counter side.
2. **Link-capacity or record-size overflow.** Rule 4 chooses the first eligible
   unlinked source and prescribes `LINK` without checking whether adding the
   target would exceed 16 links or make the changed source exceed 256 pinned
   tokens. The compact `LINK` response contains only IDs and hashes, not the
   changed source record, so outer response-length preflight cannot establish
   post-link record fit.
3. **Post-construction token overflow.** `ADD` and `SUPERSEDE` assign an ID and
   provenance after the model-visible null-ID record; `REVISE` unions and
   recomputes; `LINK` inserts and sorts a link. The stored record is checked
   for 256-token fit only as an atomic transition condition. The listed
   pre-call admissibility law does not derive and gate that final record.

In each family, the model is required to emit the exact prescribed delta and
is forbidden to drop evidence, links, fields, or deltas. Yet exact emission
cannot make the resulting transition legal. The current fallback is merely to
call `CURATE` and atomically reject the inevitable transition. That is
deterministic failure accounting, not a total legal operation mapping from
accepted reflection to executable prescribed delta.

Bind one disposition everywhere. The smallest repair consistent with the v7
design is to construct the complete post-transition temporary-store state
before `CURATE`, including deterministic IDs, full evidence unions, links,
provenance, sorting, derived fields, every cardinality, the one-live-key
invariant, and final stored-record tokenizer length. If any prescribed
transition fails, record a named no-call outcome such as
`TRANSITION_UNREPRESENTABLE`, retain and score the accepted reflection, leave
the store unchanged, and give the certificate the same one-FN/no-FP/no-
exclusion disposition as the two existing pre-call skips. Alternatively make
such a reflection call-level invalid, but then its reflection scoring law must
be explicit. Mirror the chosen rule into the prompt schema and headline.

Required model-free boundaries should include: 16-to-17 support IDs,
16-to-17 counter IDs, link-count capacity, and a 256-to-257 final stored record
for each applicable operation (`ADD`, `REVISE`, `LINK`, `SUPERSEDE`). Gold-case
generation must reject any fixture whose complete gold transition cannot
commit, not merely one whose input or response suffix does not fit.

## Certificate gold firewall

**PASS.** Each case has an isolated temporary store. Parse, semantic
validation, required-input construction, prescribed-output construction,
transition validation, and commit all use only the model-produced accepted
reflection plus the immutable case store. A contract-valid gold-different
path commits before offline comparison. Gold cannot select, veto, repair, or
redirect execution; it opens only after raw responses and the post-commit or
unchanged store seal. Stores, IDs, indices, and ordering effects never cross
cases. The remaining blocker is transition-language closure, not a gold edge.

## Operation and state reattack

Apart from the unpreflighted final-record bounds above, the operation table is
single-valued: no live key gives `ADD`; same-signature new observation identity
gives `REVISE`; a contradicted different signature may give `SUPERSEDE`; a
no-new-evidence process item may give the lexicographically first directed
`LINK`; and all other states give no delta/sole `NOOP`. First-seen ordinary
contradictions reject, citation sets are exact, novelty is observation-level,
all items read the immutable pre-call store, and mutation/hash dependencies
reject before the second call. Current-record receipts, hash domains, union
construction, block-first/record-second ordering, store version locking, and
one-live-semantic-key enforcement remain closed.

## Resource arithmetic

**PASS.** Independent recomputation gives:

- updater calls: `5*48*2 = 480/root`;
- updater generated tokens: `240*(512+384) = 215,040/root`;
- all calls: `576+24+24+12+2,880+480+15+1,280 = 5,291/root`;
- all generated tokens: `972,544/root`;
- updater input: `240*(10,240+6,144) = 3,932,160/root`;
- actor/probe returned memory: `(2,880+1,280)*1,024 = 4,259,840/root`;
- combined active-memory input: `8,192,000/root`;
- query embeddings: `2,880+1,280+240 = 4,400/root`;
- changed live-record embeddings: at most `240*4 = 960/root`;
- BM25 work: at most 3,840 insertions plus 960 removals = 4,800 physical
  mutations/root, using zero persistent probe mutations.

For 26 roots on the `N=20` route, 5,291 calls and 972,544 tokens/root give
137,566 calls and 25,286,144 tokens; fits are `18+12*26=330`. For 38 roots on
the `N=32` route, they give 201,058 calls, 36,956,672 tokens, and
`18+12*38=474` fits. The optional comparator increments to 5,451 calls,
1,017,600 tokens, and 13 fits/root, reproducing 141,726 / 26,457,600 / 356 on
the 20-root route and 207,138 / 38,668,800 / 512 on the 32-root route. The
separately bounded writer canary convention remains recoverable.

## `R0` fairness and claim boundary

**PASS.** `R0`, `U0`, `U1`, `P0`, and `P1` share the pinned child base,
ordinary call/context/token budgets, tools, skills, files, task opportunities,
public outcomes, DREAM schedule, retrieval/updater policy, and independently
evolving `ACTIVE_TEXT_FIXED` affordance. Every store and index is isolated.
`R0` receives all 48 wake programs, 96 updater opportunities, three deployment
DREAM opportunities, and the same probes; only personal parametric fitting is
off. It is therefore an equally provisioned, fit-free frozen-parameter active-
memory reference, not a crippled or never-learning complete system.

The public `P1-R0` quantity is correctly labeled a full-package difference in
lifetime gain and makes no parenting-isolation, carrier-only, equal-memory, or
equal-compute claim. Parenting causality remains confined to the registered
P/U difference-in-differences. On-policy store-content differences are not
used for root selection, matching, regression, or stratification.

## Exact one-parent/one-child/no-classroom topology

**PASS; it matches the latest ruling.** Exactly one frozen, target-blind
parent teaches exactly one parented child process-level thinking through the
closed childhood task/correction/application channel. The parent supplies
only one of three typed process lessons or `NO_CORRECTION`; it supplies no
answer, free strategy, action, deployment feedback, or training target. The U
branch is an isolated counterfactual child for causal estimation and has no
edge to the dyad. Roots are sealed replications, not a learning population.

After the deletion audit, the parent, parent feedback/restatements, nursery
state, and every unapproved edge disappear. Deployed `P1` continues its own
THINK--DREAM--SLEEP life with one personal cumulative rank-8 LoRA, while the
equally provisioned `R0` comparator keeps parameters frozen and independently
evolves only its own active textual memory. Lifetime learning is measured from
the repeated sealed cuts at 0/16/32/48, with `P1` versus `R0` shown publicly
and the P/U factorial carrying the parenting estimand. There is no classroom,
cohort, peer channel, teacher ensemble, population learning, shared ledger,
shared store/index, cross-root state, or post-deletion parent access. A common
frozen updater policy is a per-service mechanism, not shared learning.

## Disposition

Do not promote `ACTIVE_TEXT_FIXED` as a validated strong baseline and do not
spend scientific roots from these bytes. Close post-transition cardinality
and stored-record fit before `CURATE`, bind its certificate disposition, add
the boundary fixtures above, regenerate source bindings, and obtain another
fresh independent byte audit. No change is needed to the one-parent/one-child
architecture, P/U estimand, `P1` versus `R0` public story, root plan, or
resource envelope.

## Audited candidate hashes

- `AGENTS.md`: `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e`
- headline plan: `e2cc7afcbf364e990c8d170e281262094a279b1bbf59a50efb478ca909332a0e`
- active-text contract: `cd53da13fae7009880cca802f5b72737257800effd32feee5c49c83531eebac4`
- model-visible prompt schema: `8f5d4357d6b07c5bfb7aec42ed490add1486a7570c0e81303092700c5f65f164`
- scope proposal: `466319fa741a583f2cb9cf1dd6e01fd255877feae5818ea7697e3fab1e17dc75`
- closure audit v6: `c67596a795b13559c2209db63e71f03af63c015f56c76e148e41c7fa5b0f2809`
- closure audit v7: `180cc017f84877663c3e63fbf283162f6322a6a705edf09b1ee07a09fadd8a4c`

## Advisory hash receipt

Because a file cannot contain its own ordinary whole-file digest without
changing that digest, the embedded self-receipt uses this reproducible domain:
SHA-256 over the exact final UTF-8 advisory bytes with the 64 hexadecimal
characters after `normalized-self-sha256=` replaced by 64 ASCII zeroes.

`normalized-self-sha256=fc1e7a49c1e23b28fc23edaf5ff69ef90dd2e24af40a92f5648c0d4392d30e5b`

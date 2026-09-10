# One-parent/one-child strong-baseline closure audit v7

Date: 2026-09-06

Status: fresh independent read-only byte/semantic audit of the current
proposal after the v6 repairs. This advisory changes no candidate byte and
authorizes no implementation, model/tokenizer call, benchmark generation,
adapter operation, external call, or GPU use.

## Verdict

**REVISE.** The current bytes close every exact blocker from v6:
first-seen ordinary contradictions are rejected before they can prescribe an
illegal `ADD`; revision novelty is defined over complete observation
identities under exact per-kind citation sets; and `CURATE` receives one exact
block-first/record-second union that includes a full-store same-key record even
when `REFLECT` retrieval missed it. The earlier hash-receipt,
multi-item-collision, exception-direction, certificate-gold, resource,
active-baseline, and one-parent repairs remain intact.

A fresh operation-totality attack found one new representability defect and
its certificate counterpart. The contract bounds each stored record at 256
pinned-child tokens and permits up to four record-bearing deltas, but the
entire `CURATE` response is capped at 384 generated tokens. A valid accepted
`REFLECT` can therefore prescribe a complete deterministic delta list for
which no response within the registered generation ceiling exists. The
pre-`CURATE` admissibility law checks IDs, hashes, mutation collisions, and
`ADD_CONTRADICTED`, but not the exact token length of the prescribed canonical
`CURATE` object. The certificate likewise has no total outcome for a valid
`REFLECT` whose required `CURATE` input is `INPUT_OVERFLOW` and therefore must
not invoke the second call.

These are narrow byte/protocol fixes. They do not require a change to the
parenting architecture, causal estimands, root count, active-memory
comparator, or public `P1` versus `R0` story.

## Disposition of every v6 blocker

1. **First-seen `ADD_CONTRADICTED` — CLOSED.** Section 4 now derives the
   prescribed list before `CURATE` and rejects any ordinary item whose first
   rule would be an `ADD` with derived `CONTRADICTED` status. The visible
   schema states the same rule, the exhaustive class set contains only
   `ADD_PROVISIONAL` and `ADD_SUPPORTED`, and the model-free fixture list names
   this rejection.
2. **Citation and observation identity — CLOSED.** Citation sets are exact by
   proposition kind. Extra assistant, clock, unused-prediction, duplicate,
   partial, and cross-block IDs reject. Novelty is one block for single-block
   claims and exception sides, one ordered same-state block pair for
   `ACTION_CONTRAST`, and one complete one-/two-block tuple for
   `PROCESS_ASSOCIATION`. Rule 2 requires a newly represented complete
   observation identity, so an already represented block with a newly cited
   redundant ID cannot create `PROVISIONAL -> PROVISIONAL`.
3. **Revision/status totality — CLOSED for every representable prescribed
   list.** A provisional record plus a genuinely new same-signature support
   becomes supported; a new counter makes an ordinary record contradicted; a
   supported same-signature record may remain supported or become
   contradicted; and a contradicted same-signature record remains
   contradicted. A different newly provisional/supported signature can replace
   a contradicted record only through `SUPERSEDE`. No legal
   `REVISE_PROVISIONAL` or `ADD_CONTRADICTED` class remains.
4. **Exact `CURATE` input union, order, and the retrieval-miss case — CLOSED.**
   The union contains every cited complete block, the sole live full-store
   same-key record consulted for every item whether or not retrieval displayed
   it, and every record named by `related_memory_ids`. Blocks deduplicate by
   block ID and sort by `(program_event_id,ACTION.ordinal,block_id)`; receipts
   deduplicate by memory ID and sort afterward by memory ID. Required overflow
   skips `CURATE` without omission, truncation, retrieval fallback, or borrowed
   partition capacity.
5. **Record receipts and hashes — CLOSED.** SHA-256 covers the exact canonical
   current `RECORD` UTF-8 bytes with no leading or terminal byte. Every
   updater-visible live record is inside a checked `RECORD_RECEIPT`; mutation
   operations copy the visible digest; store version changes abort without
   retry. Reflection and block ID byte domains are also explicit, and
   nonidentical collisions reject.
6. **Multi-item mutation collisions — CLOSED, apart from the new output-size
   blocker below.** Semantic keys are unique in one reflection; all prescribed
   operations are derived against the immutable pre-call store; repeated
   changed/created IDs, changed link sources/consumers, and in-call hash/ID
   dependencies reject before `CURATE`. I found no remaining path that can
   commit two live records under one semantic key or consume an intermediate
   hash unavailable in the prompt.
7. **Exception basis and direction — CLOSED.** Opposite validity has fixed
   precedence over score sign; otherwise only opposite strict score signs can
   select `SCORE_SIGN`. Local/external bins are exact opposites and actor
   visible, object is null, support is one local program, and constitutive
   counter observations are external. The chosen direction is part of the
   proposition signature while basis is part of the one-live-record semantic
   key.
8. **Certificate dependency and gold firewall — CLOSED except for the
   pre-call overflow path below.** Each fixture owns an isolated store. Only an
   accepted model-produced `REFLECT` can feed `CURATE`; invalid reflection
   skips the second call; commit validation has no gold access; and a
   contract-valid gold-different path commits before offline scoring. Cases
   share no store, IDs, index state, or ordering effect.

## Exact blockers

### 1. A valid `REFLECT` can prescribe a `CURATE` response that cannot fit the 384-token ceiling

The output language permits one to four deltas. A record-bearing delta embeds
one complete record of up to 256 pinned-child-tokenizer tokens, plus operation,
ID/hash, and top-level JSON bytes. Two independent valid reflection items with
different semantic keys can prescribe two independent `ADD`, `REVISE`, or
`SUPERSEDE` deltas without triggering any current collision rule. Four are
also legal. Yet the headline gives the whole `CURATE` response at most 384
output tokens.

The contract therefore does not prove that the deterministic complete delta
list has a representable serialization. Even a single near-limit record may
exceed the whole-call ceiling after its operation wrapper; two independently
legal near-limit records can plainly exceed it. The current input-overflow law
does not apply because all evidence and receipts may fit the input partitions.
At generation time the correct JSON is then necessarily truncated or omitted,
and the accepted `REFLECT` has no legal second-call answer under the registered
budget. This is the same closure class as v6's now-fixed accepted-reflection /
unrepresentable-operation defects.

Bind one deterministic solution. The smallest repair is to construct the
complete prescribed canonical `CURATE` object before the second call, measure
that exact object plus EOS under the pinned child tokenizer, and reject
`REFLECT` during call-level admissibility if it exceeds 384 tokens. Mirror the
rule into the visible schema and add one- through four-delta boundary fixtures.
Alternatively raise the output ceiling enough for the worst legal four-delta
object and recalculate every output-token total. Restricting each call to one
prescribed delta is also total, but changes the accepted reflection language.

No tokenizer should be called merely to repair the proposal bytes. The exact
measurement belongs to the later, separately authorized tokenizer gate; until
then the version remains proposal-only and the existing fixed-partition NO-GO
law continues to apply.

### 2. Certificate scoring is undefined when valid `REFLECT` must skip `CURATE` for input overflow

Section 6 correctly says that, after a valid reflection, an over-cap required
union records `INPUT_OVERFLOW`, does not call `CURATE`, and makes no update.
Section 8 defines the certificate path for invalid `REFLECT` (skip the second
call; one missing-gold false negative) and for valid `REFLECT` (pass it to and
score `CURATE`), but not for valid `REFLECT` followed by this mandatory
pre-call overflow skip.

This is reachable in the contract language: one accepted item may cite up to
16 support and 16 counter IDs, and up to four accepted items may require
multiple complete blocks and receipts; the cited partition is only 1,280
tokens. Gold fixtures saying they display only required evidence does not
state that every sealed gold input fits, nor does it assign confusion counts
when a gold-different but valid model reflection requires an overflowing
union. Two conforming reducers can therefore disagree between “no predicted
CURATE unit,” “invalid CURATE attempt,” and “case excluded,” with different
precision/recall.

Freeze the path. Require the certificate generator to reject any gold fixture
whose exact gold second-call input or exact gold prescribed output does not
fit. For a valid model-produced gold-different `REFLECT` whose required union
overflows, execute no `CURATE`, seal unchanged store plus the overflow receipt,
score the emitted reflection normally, add exactly one false negative in the
fixture's gold `CURATE_CLASS`, add no CURATE false positive because no second
call occurred, and never exclude the case. State the corresponding disposition
for the output-representability rejection chosen in Blocker 1.

## Fresh attacks that pass

- **Operation selection:** Empty reflection gives sole `NOOP`; same-key
  same-signature evidence enrichment gives one `REVISE`; contradicted
  different-signature evidence gives `SUPERSEDE`; no-new-evidence process
  items give the lexicographically first eligible directed `LINK`; every other
  state yields no delta. With the two size paths above closed, the selector is
  total.
- **Process reconstruction:** Subject-only blocks are each one sequence. A
  nonnull object requires all cited blocks to partition exactly once into
  immediate subject-then-object action pairs with no intervening action;
  reversed, unmatched, duplicate, reused, and extraneous blocks reject. The
  terminal outcome and `INVALID` tie position are bound for support and
  counters.
- **Confusion accounting:** Empty/parse/top-level-invalid, element-invalid,
  wrong-class, same-class field-wrong, duplicate/extra, missing, illegal NOOP,
  and zero-denominator cases have an explicit class destination. Macro-F1 is
  the unweighted mean of eight defined class F1 values; the reusable-record
  gold set contains exact final ADD/REVISE/SUPERSEDE records only.
- **Pinned-tokenizer partition:** No tokenizer or model was called. The source-
  bound schema is 10,671 UTF-8 bytes, 1,011 whitespace-delimited words, 25
  lines, and has exactly one terminal U+000A. Those counts do not imply fit.
  The proposal correctly makes a later exact pinned-tokenizer receipt a NO-GO
  gate: fixed laws cannot be truncated, summarized, or moved into evidence
  partitions.
- **Resource arithmetic:** The registered hard numbers independently
  recalculate to 5,291 calls, 972,544 generated tokens, 3,932,160 updater input
  tokens, 4,259,840 returned actor/probe memory tokens, 8,192,000 combined
  active-memory input tokens, 4,400 query embeddings, at most 960 changed-live-
  record embeddings, and 3,840 lexical inserts plus 960 removals per root.
  The `N=20` and `N=32` root totals and optional comparator totals also
  recalculate. The separately bounded writer canary remains outside the
  reported call/token root multiples and inside the reported total-fit count.
- **Probe persistence:** Probe actions go only to the sealed evaluation
  artifact and create zero life-ledger/store/index mutations; this makes the
  2,880 raw-block and 4,800 physical BM25-mutation ceilings consistent.
- **`R0` fairness:** `R0`, `U0`, `U1`, `P0`, and `P1` have the same actor-call
  budget, context, tools/files/skills, DREAM opportunities, public outcomes,
  retrieval/updater mechanism, and isolated evolving textual store. `R0` is
  correctly a frozen-parameter active-memory reference. `P1-R0` is labeled a
  full-package effect; only the P/U factorial identifies parenting.
- **One-parent/no-classroom topology:** One frozen parent has one closed
  childhood correction edge to one parented child. U is an isolated
  counterfactual branch, roots are sealed replications, and no classroom,
  cohort, peer exchange, ensemble, population learning, shared memory, or
  post-deletion parent access exists. The common frozen active-text updater is
  a per-service memory mechanism, not a teacher or cross-child channel.

## Nonblocking notes

- A supported scope exception remains intentionally difficult to reverse:
  constitutive external contrast supports it, so a reverse same-basis
  direction cannot supersede it unless another mechanism first produces a
  contradicted same-key record. This is deterministic and actor-visible, not a
  byte ambiguity, but it should remain a reported semantic limitation.
- The optional comparator paragraph reports root-multiple call/token totals
  excluding the separately bounded writer-canary calls/tokens while explicitly
  including the canary's 18 fits in total fits. The preceding paragraph makes
  that convention recoverable; a final resource table should label it directly
  to prevent readers from treating the mixed convention as one all-in total.
- Passing this audit would still not authorize the parent, updater, tokenizer,
  benchmark, LoRA, or GPU. Exact source rebinding, human ratification,
  implementation/static fixtures, fresh implementation review, and a separate
  pre-GPU gate remain mandatory.

## Disposition

Do not promote `ACTIVE_TEXT_FIXED` as a validated strong baseline and do not
spend scientific roots from these bytes. Add exact prescribed-`CURATE` output
representability to pre-call admissibility, totalize certificate handling for
pre-`CURATE` input/output size failures, mirror the model-actionable law into
the source-bound prompt schema, add boundary fixtures, regenerate bindings,
and obtain one more fresh independent closure audit. No headline architecture
or experimental-topology change is needed.

## Audited hashes

- `AGENTS.md`: `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e`
- headline plan: `dfb3cbaa856940de582593bd7c55d9a2b552dd0a03e5d4fa0ad955b2d4dbcda3`
- active-text contract: `87c92896e33ab1df59521438173e79521d2403027c0b0f391fcefd198dcb5c55`
- model-visible prompt schema: `7f58f95012a9dd4a16bece083a72300d530650d3412dd76176226338a2aee4a3`
- scope proposal: `466319fa741a583f2cb9cf1dd6e01fd255877feae5818ea7697e3fab1e17dc75`
- prior closure audit v5: `28339bb997f7a5a7e22fd4603427d5d09d1f6107d4eb9ca57e00004818c002f1`
- prior closure audit v6: `c67596a795b13559c2209db63e71f03af63c015f56c76e148e41c7fa5b0f2809`

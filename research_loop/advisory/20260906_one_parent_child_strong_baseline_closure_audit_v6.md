# One-parent/one-child strong-baseline closure audit v6

Date: 2026-09-06

Status: fresh independent read-only audit of the current proposal bytes after
the v5 repairs. This advisory changes no candidate byte and authorizes no
implementation, model/tokenizer call, benchmark generation, adapter operation,
external call, or GPU use.

## Verdict

**REVISE.** All four exact v5 blockers are repaired in the current bytes:
current-record hashes have one exact byte domain and visible receipts;
multi-item `REFLECT` conflicts are rejected before `CURATE`; exception-basis
precedence is deterministic; and certificate execution/commit has no gold
edge. The one-parent/no-classroom topology and `R0` fairness also remain
intact, and the call/token/index arithmetic independently recalculates.

Fresh counterexample construction nevertheless found two accepted
single-item `REFLECT` states for which the prompt-visible transition language
has no legal `CURATE` result, plus one undefined `CURATE` input construction
that can make a required current-record receipt unavailable. These are narrow
contract-closure defects, not reasons to redesign the experiment.

## Disposition of every v5 blocker

1. **Current-record hash byte domain and receipt — CLOSED.** A current record
   hash is SHA-256 over the complete canonical `RECORD` UTF-8 bytes with no
   leading or terminal byte. Every updater-visible record is a closed
   `RECORD_RECEIPT`; the receipt hash is checked against the version-locked
   store, and `REVISE`, `SUPERSEDE`, and `LINK` copy the displayed digest. The
   compact visible schema states the same no-newline domain and tells the
   updater never to invent a hash.
2. **Multi-item call-level admissibility — CLOSED for the v5 collision
   family.** Semantic keys are unique across `REFLECT.items`; prescribed
   deltas are derived against the immutable pre-call store; repeated
   mutated/created IDs, a `LINK` source mutated elsewhere, and any dependency
   on an ID/hash created or changed by another item reject `REFLECT` before
   `CURATE`. The law is also visible in the compact prompt schema. This closes
   revise/revise, add/revise, link/link, and link/mutation dependence inside a
   single call.
3. **Exception-basis precedence — CLOSED.** An opposite validity split always
   selects `VALIDITY`; only when that condition is false may opposite strict
   score signs select `SCORE_SIGN`. Local and external bins are then forced.
   The merger and prompt schema agree.
4. **Gold-independent certificate commit — CLOSED.** Each case has an isolated
   temporary store. Only accepted model-produced `REFLECT` enters `CURATE`.
   The commit validator has no certificate-gold access and commits every path
   valid under that reflection and the pre-call store, even when gold-
   different. Gold opens only after responses and the post-commit store seal.

## Exact blockers

### 1. First-seen contradiction prescribes an unrepresentable `ADD`

The semantic language permits a valid ordinary reflection with at least one
complete support observation and ordinary counterevidence. It therefore
derives `kind=CONTRADICTION` and `status=CONTRADICTED`. If the service store has
no live same-key record, Section 4's first matching operation rule
unconditionally prescribes `ADD`.

But the source-bound prompt schema says `ADD` derives only
`PROVISIONAL|SUPPORTED`, and the certificate declares eight exhaustive
classes containing `ADD_PROVISIONAL` and `ADD_SUPPORTED` but no
`ADD_CONTRADICTED`. Thus an otherwise valid first-seen contradicted reflection
has no legal emitted delta under the visible contract, and the certificate
does not cover an operation the merger currently prescribes.

Choose one rule and bind it everywhere. The minimal repair consistent with the
current eight-class certificate is to reject `REFLECT` during call-level
admissibility whenever its first matching rule would be an `ADD` whose derived
status is `CONTRADICTED`. The alternative is to permit
`ADD_CONTRADICTED`, add it to the legal transition table and certificate class
space, and include sealed cases. Do not leave Rule 1 unconditional while the
prompt and certificate prohibit its result.

### 2. Event-ID novelty can prescribe illegal `PROVISIONAL -> PROVISIONAL`

`REVISE` currently triggers when a same-key/same-signature item cites at least
one support/counter **ID** absent from the live record. The evidence law states
the IDs required to reconstruct a complete observation, but it does not say
that the array contains only those minimal IDs or reject an additional event
from an already represented block.

Concrete case: a provisional `ACTION_VALIDITY` record cites one block's action
and terminal-outcome IDs. A later otherwise valid same-signature reflection
cites those two IDs plus that same block's displayed prediction (or another
redundant public event from the block). There is a new evidence ID, so Rule 2
prescribes `REVISE`; there is still exactly one complete support observation
and no counterevidence, so recomputation remains `PROVISIONAL`. The legal
transition table omits `PROVISIONAL -> PROVISIONAL`, and the exhaustive
certificate space omits `REVISE_PROVISIONAL`. Again a valid `REFLECT` has no
legal `CURATE` result.

Make observation identity, not arbitrary event-ID novelty, the trigger: require
at least one newly represented complete `block_id` observation (or matched
pair/sequence unit) before `REVISE`. Also freeze the exact allowed citation set
per proposition kind and reject extraneous event IDs, or explicitly allow and
classify same-status evidence enrichment. Mirror the selected rule in the
visible schema and add a sealed within-block-novel-ID counterexample fixture.

### 3. `CITED_EVENT_AND_RECORD_JSONL_OR_EMPTY` has no exact construction law

The v5 receipt repair defines the wrapper and hash correctly, but not the exact
set and order of records placed into the `CURATE` placeholder. This matters
when a live same-key record exists in the immutable store but was not returned
by `REFLECT`'s top-four retrieval. Such a `REFLECT` may still be semantically
valid: `related_memory_ids` is defined as all **displayed** same-key records,
which is empty in this case. Operation selection, however, consults the full
immutable store and may prescribe `REVISE` or `SUPERSEDE`. `CURATE` then needs
the undisplayed record's opaque ID, exact bytes, and receipt hash.

The headline says `CURATE` receives cited source events and "currently related
records," while the byte contract names a placeholder but never defines
whether it means reflection-listed records, every full-store same-key record
consulted by operation selection, process-link candidates, or some union; nor
does it freeze a total order for a same-key record that had no retrieval rank.
Two conforming implementations can therefore render different bytes, and one
can reproduce the original unavailable-hash failure.

Define the placeholder as an exact deterministic union. At minimum it must
include complete blocks for every cited event, every live same-key record
consulted by operation selection, and every source/target candidate needed by
the deterministic process-link rule, all as exact receipts where applicable.
Specify deduplication, precedence/order, and what `INPUT_OVERFLOW` does before
the model call. Include a certificate fixture where the current same-key
record was absent from prior retrieval but is surfaced for `CURATE`.

## Fresh attack results that pass

- **Store uniqueness:** With the existing one-live-record-per-semantic-key
  invariant and pre-call conflict check, I found no cross-item path that can
  commit two live records under one key or mutate one record twice. Hash/ID
  collisions with nonidentical bytes reject.
- **Exception direction:** Basis and direction are actor-visible. Same-key
  opposite direction cannot silently coexist; the present design instead
  declines a different-signature replacement unless the old record is already
  contradicted.
- **Certificate malformed accounting:** Empty/parse-invalid/top-level-invalid,
  invalid element, wrong class, field-wrong, extra, duplicate, missing, and
  zero-denominator cases all have an explicit confusion-count destination.
  Macro-F1 is the unweighted mean of eight defined class F1 values, and the
  reusable-record gold set is exact and isolated by case.
- **Gold firewall:** A gold-different but contract-valid reflection/delta can
  alter only that fixture's temporary store and is scored after commit; gold
  cannot select or veto the store transition.
- **Prompt/merger parity on the v5 repairs:** Record receipt hashes,
  multi-item conflict rejection, unique scope, exception-basis precedence,
  process block consumption/order, derived status/guidance, supersession, and
  gold-free execution are represented consistently, aside from the blockers
  above.
- **Topology:** There is exactly one frozen parent and one parented child per
  dyad. `U` is an isolated counterfactual branch; roots are sealed
  replications. There is no classroom, cohort, peer exchange, teacher
  ensemble, population learning, shared memory, or post-deletion parent edge.
- **`R0` fairness:** All five services retain the same model-call budget,
  context, tools/files/skills, DREAM opportunities, public outcomes, and an
  isolated evolving `ACTIVE_TEXT_FIXED` mechanism. `R0` is correctly called a
  frozen-parameter active-memory reference; `P1-R0` is a full-package effect,
  while parenting causality is confined to the P/U factorial.

## Arithmetic and receipt audit

The hard active-memory arithmetic recalculates:

- updater calls: `5*48*2 = 480`;
- updater output tokens: `240*(512+384) = 215,040`;
- total calls: `576+24+24+12+2,880+480+15+1,280 = 5,291/root`;
- total output tokens: `972,544/root`;
- updater input tokens: `240*(10,240+6,144) = 3,932,160/root`;
- actor/probe returned-memory tokens:
  `(2,880+1,280)*1,024 = 4,259,840/root`;
- combined active-memory input: `8,192,000/root`;
- query embeddings: `2,880+1,280+240 = 4,400/root`;
- changed-record embeddings: at most `240*4 = 960/root`;
- persistent lexical work under the no-probe-write rule: at most 2,880 raw
  blocks plus 960 record insertions and 960 removals = 4,800 physical
  mutations/root.

The 20- and 32-confirmation-route call/token/fit totals and the optional
descriptive comparator totals also recalculate exactly. Receipt wrappers are
inside the existing updater document partitions, not additional unbudgeted
retrievals or embeddings.

The headline's no-probe-return-to-life rule implies zero persistent probe
ledger/store/index writes, which the lexical total needs. The supporting
contract still says broadly that every dispatched deployment action can
create a raw-block insertion before calculating only wake actions. Keep the
zero-persistent-probe-write behavior as a mandatory golden fixture and make
the contract sentence explicit in the next byte repair; this is not a fourth
architecture blocker because the headline already forbids probe re-entry.

## Pinned-tokenizer fit

No tokenizer or model was called. The source-bound compact schema is currently
10,041 UTF-8 bytes, 953 whitespace-delimited words, 24 lines, and has exactly
one terminal U+000A. Those byte counts do not establish pinned-tokenizer fit or
overflow.

The consequence is now literal and correct: before any updater execution, the
pinned receipt must show the complete fixed system/schema/calibration/header/
chat-template bytes fit the 4,096-token fixed partition; otherwise this
protocol version is `NO-GO`, cannot borrow from evidence partitions, cannot
truncate/summarize laws, and cannot spend roots. That later gated tokenizer
measurement remains necessary but is not authorized by this audit.

## Nonblocking design notes

- A supported `SCOPE_EXCEPTION` has no ordinary contradiction path and a
  reverse same-key signature cannot supersede it until it is contradicted.
  This is deterministic, but it can make an early exception effectively
  irreversible. Treat that as a prospective semantic choice, not an accidental
  implementation behavior.
- The reflection-ID hash phrase combines canonical item bytes, U+000A, and the
  "canonical program_event_id" but does not say whether the latter means raw
  normalized ID UTF-8 or a canonical JSON string. It does not affect any
  model-emitted cryptographic receipt, but golden fixtures should bind those
  exact bytes before implementation.
- Fixed instruction/schema accounting appears conservative: the 4,096 fixed
  partition names chat-template/boundary bytes while the surrounding cap also
  reserves boundary capacity. Golden tokenizer receipts should assign every
  token to exactly one partition so conservative double reservation cannot
  become implementation-dependent packing.

## Disposition

Do not promote `ACTIVE_TEXT_FIXED` as a validated strong baseline and do not
spend scientific roots from these bytes. Close the first-seen-contradiction
status, replace event-ID novelty with an exact observation-level revision law,
and bind the complete `CURATE` evidence/receipt set and ordering. Extend the
certificate with all three counterexamples, mirror every model-actionable rule
into the source-bound prompt schema, regenerate bindings, and obtain another
fresh independent byte audit. The experiment topology, statistics, root plan,
resource envelope, and public `P1` versus `R0` story do not need to change.

## Audited hashes

- `AGENTS.md`: `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e`
- headline plan: `c59297615724791c84b0e4d9d712a69403cb39a467745d6a29408b560573fd5f`
- active-text contract: `d2ed045d3be9f0f5f94a871a0cf027b99015ca6d35c88027d2104c7d987d2ef0`
- model-visible prompt schema: `1cb5c6253890839ce6388bf88107ddef8abe38bb99bdba3baa955dbbb4a30a5c`
- scope proposal: `466319fa741a583f2cb9cf1dd6e01fd255877feae5818ea7697e3fab1e17dc75`
- prior closure audit v5: `28339bb997f7a5a7e22fd4603427d5d09d1f6107d4eb9ca57e00004818c002f1`

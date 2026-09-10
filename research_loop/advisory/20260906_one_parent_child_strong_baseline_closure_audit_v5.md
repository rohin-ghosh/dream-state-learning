# One-parent/one-child strong-baseline closure audit v5

Date: 2026-09-06

Status: fresh independent read-only audit of the current proposal bytes after
the v4 repairs. This advisory changes no candidate byte and authorizes no
implementation, model/tokenizer call, benchmark generation, adapter operation,
external call, or GPU use.

## Verdict

**REVISE.** The current bytes repair nearly all of v4's named defects. For a
single noninteracting reflection item, operation choice is now deterministic;
the one-live-record-per-semantic-key invariant is explicit; exception direction
and ordinary counter-scope membership are typed; malformed scoring is total;
certificate cases use isolated two-call stores; the resource arithmetic
recalculates; the active baseline remains fairly and honestly framed; and the
one-parent/no-classroom topology is intact.

Four exact closure blockers remain. First, `CURATE` must emit current-record
SHA-256 values that are neither defined byte-for-byte nor supplied in its
input. Second, a valid multi-item `REFLECT` can prescribe two mutations of the
same memory, or a mutation of a record created earlier in the same call,
contradicting the one-delta-per-memory law and requiring an unavailable
intermediate hash. Third, one set of public exception evidence can still
legally derive two different `exception_basis` values. Fourth, the certificate
does not state whether a contract-valid but gold-different execution commits;
the gold answer must never participate in the store transition.

No architecture, estimand, root-count, active-memory fairness, or resource-
envelope redesign is required to close these points.

## Disposition of every v4 blocker

1. **Store invariant and operation selection — CLOSED for one independent
   item, OPEN for multi-item calls.** `ADD` now requires no live same-key
   record; `REVISE` preserves the same key/signature; `SUPERSEDE` requires a
   contradicted same-key record and a newly provisional/supported different
   signature; `LINK` has a public directional rule; and the one-live-record
   invariant is checked after each temporary transition. The remaining
   multi-item counterexample is Blocker 2 below.
2. **Exception direction and counter-scope membership — MOSTLY CLOSED.** The
   proposition and semantic key now preserve basis, local bin, and external
   bin, so local-valid/external-invalid is no longer byte-identical to its
   reverse. `PROGRAM`, `PUBLIC_FEATURE`, and `CROSS_PROGRAM` counter
   membership are executable and apply to every block in a pair/sequence.
   The remaining dual-basis derivation is Blocker 3 below.
3. **Certificate malformed accounting — CLOSED.** A malformed top level gets
   exactly one class-allocated false-positive attempt plus the missing-gold
   false negative. Every invalid element is assigned either to its uniquely
   identified attempted class or the fixture's gold class. The eight classes,
   per-class confusion equations, macro-F1, zero-denominator rule, and exact
   reusable-record gold set are explicit.
4. **Certificate dependency and isolation — MOSTLY CLOSED.** Each fixture has
   its own presealed temporary store; invalid `REFLECT` skips `CURATE`; only the
   accepted model-produced reflection can feed `CURATE`; and recall is read
   from that fixture's post-commit store. The remaining gold-versus-contract
   commit ambiguity is Blocker 4 below.
5. **Resource arithmetic — CLOSED.** The hard counts independently recalculate
   to 5,291 calls, 972,544 output tokens, 4,400 query embeddings, at most 960
   changed-record embeddings, 3,840 BM25 inserts plus 960 removals, and
   8,192,000 active-memory input tokens per root. The 20/32 confirmation-route
   totals and the optional comparator totals also recalculate exactly.
6. **Historical optional comparator — CLOSED.** It is post-headline,
   descriptive-only, bound to a content-addressed historical `P0` snapshot,
   excluded from root selection and powered superiority, and correctly
   described as a bounded style comparator rather than LEAFE reproduction.
7. **Active-baseline fairness — CLOSED.** `R0/U0/U1/P0/P1` receive the same
   updater, retrieval, context, tools, files, clocks, task opportunities, and
   isolated evolving textual store. The proposal correctly treats
   `P1-R0` as a full-package comparison and reserves parenting causality for
   the registered P/U interaction. On-policy store-content differences are
   explicitly total-effect mediators, not matching variables.
8. **One-parent topology — CLOSED.** Exactly one frozen parent has one closed
   childhood correction channel to the parented child. U is a sealed
   counterfactual branch, not a peer; roots are replications; and no classroom,
   cohort, exchange, ensemble, population, shared memory, or post-deletion
   parent edge exists.

## Exact blockers

### 1. Required current-record hashes are undefined and unavailable to the model

`REVISE`, `SUPERSEDE`, and `LINK` require exact
`prior_*_sha256` fields. The contract says only that exact current hashes are
required. It does not define whether a current record hash covers canonical
record bytes with or without a terminal U+000A (or any other exact byte
domain). More importantly, `CURATE_USER` supplies each prior/cited item as a
bare canonical `RECORD` or `LEDGER_EVENT_BLOCK`; `RECORD` has no
`record_sha256` field or containing receipt. The updater has no tools. It is
therefore asked to invent a 64-hex digest that is absent from its visible
input, making every non-ADD record mutation practically uncallable even if the
model otherwise identifies the exact legal operation.

Bind one hash domain, for example SHA-256 over the canonical complete current
`RECORD` bytes with explicitly stated newline treatment, and put the exact
digest beside every displayed record in a closed model-visible wrapper. Mirror
that wrapper and rule into the prompt schema and account for its partition
tokens. Alternatively remove model-emitted hashes and let the deterministic
merger bind them, but do not leave cryptographic computation implicit.

### 2. Valid multi-item REFLECT outputs can have no legal CURATE output

The operation law processes up to four valid reflection items against one
evolving temporary store, while a `CURATE` object permits at most one delta to
mutate a given memory ID. Consider an initial live record `R` and two otherwise
valid same-key/same-signature reflection items, each citing a different new
support observation. Both items legally list the same displayed `R` in
`related_memory_ids`. Item 1 prescribes `REVISE(R)`; after that temporary
transition, item 2 also prescribes `REVISE(R)`. The required complete delta
list therefore contains two mutations of `R`, which the same contract rejects.
The second delta would additionally need the hash of the intermediate record,
which was not in the one-shot `CURATE` input.

An empty-store variant is `ADD` followed by `REVISE` of the just-created
record; the model sees neither the assigned ID nor the intermediate current
hash. Different process items can similarly prescribe multiple `LINK`
mutations of one source. Thus this is not merely a low-probability model error:
the accepted `REFLECT` language contains inputs for which no accepted
`CURATE` serialization exists.

Add a deterministic call-level admissibility law before `CURATE`: the full
prescribed list must be derivable from the immutable pre-call store, must have
pairwise-disjoint mutated/created memory IDs, and no delta may consume an ID or
hash created by another item in the same call. Reject a `REFLECT` that violates
that law, or change the protocol so the merger—not the model—executes dependent
temporary transitions. Copy the chosen rule into the visible schema and add
multi-item certificate fixtures.

### 3. `SCOPE_EXCEPTION` does not deterministically choose its basis

A local support set can be both `VALID` and strictly score-positive while an
external counter set is both `INVALID` and strictly score-negative. The same
public blocks then satisfy both `exception_basis=VALIDITY` and
`exception_basis=SCORE_SIGN`. The contract calls this the "chosen" basis and
the visible schema uses `VALIDITY|SCORE_SIGN`, but neither gives precedence.
Both outputs pass the stated bins and produce different semantic keys, so the
claim that every semantic field is mechanically derived is false for this
case.

Freeze a public precedence rule (for example, choose `VALIDITY` whenever the
validity bins are opposite; otherwise use `SCORE_SIGN`) or reject evidence
that supports both bases. Apply the same law in the merger, visible schema, and
sealed certificate generator.

### 4. Certificate store commit must be independent of the gold answer

The certificate correctly passes the model's accepted `REFLECT` into
`CURATE`, but then says only an exact schema/semantic/operation-valid object
commits and that an "invalid or mismatched output" commits nothing. In this
certificate paragraph, `mismatched` can mean either mismatch to the operation
prescribed by the accepted model reflection/current store or mismatch to the
fixture's gold unit. Those are not equivalent when the model emits a different
but contract-valid reflection. Conditioning commit on gold equality would
turn the offline answer key into an execution edge and would not measure the
actual updater pipeline.

State explicitly that the commit validator has no access to certificate gold:
it commits iff the `CURATE` object is valid under the accepted model-produced
`REFLECT` and that case's pre-call store. Gold is consulted only after raw
outputs and the resulting post-commit store are sealed. A contract-valid
gold-different path must commit and score as predicted-versus-gold; only a
mismatch to the deterministic prescribed-delta list rejects the transition.

## Prompt parity and fixed-partition inspection

The current source-bound prompt schema is 9,536 UTF-8 bytes, 872
whitespace-delimited words, 23 lines, and has exactly one terminal U+000A. It
now exposes the v4 repairs for scope precedence, counter membership, process
partitioning, exception direction/status, derived guidance, operation order,
and status transitions. It does not expose a usable record-hash receipt, a
multi-item conflict rule, or a deterministic exception-basis precedence,
because the repository contract does not yet contain those laws either.

No tokenizer was called in this proposal-only audit. The proposal's complete-
schema requirement, exact 4,096-token fixed partitions for both updater calls,
and hard total caps make the later pinned-tokenizer measurement a genuine
go/no-go rather than permission to omit visible laws. Before implementation,
make the already-implied consequence literal: if the complete system message,
schema, calibration line, and fixed template bytes exceed the 4,096-token
partition, that protocol version is `INPUT_OVERFLOW`/NO-GO; it may not borrow
from evidence partitions, truncate the schema, or silently summarize a law.
This audit makes no claim that the current 9,536 bytes fit.

## Nonblocking notes

- The direction fields fixed v4's canonical collision, but an exception with
  the later reverse direction has a different semantic key and can remain live
  beside the earlier exception forever. That may be desirable historical
  evidence, but the actor receives two incompatible `SUPPORTED` directions.
  Decide prospectively whether such reversal should trigger cross-key
  supersession or remain an explicitly reported conflicting pair.
- The resource count is sound under the Section-11 rule that probe outputs and
  memory never re-enter life: probe actions therefore create no persistent
  raw-event-block/index insertions. Make that zero-write probe behavior an
  explicit implementation fixture so the 2,880 raw-block ceiling cannot be
  reinterpreted.
- Requiring the model to reproduce a deterministic merger's complete delta is
  a demanding strength test, but it is scientifically acceptable once every
  required opaque receipt is visible and every valid `REFLECT` has one
  representable legal result. The once-only empirical gate can then reject a
  weak updater honestly.

## Disposition

Do not promote `ACTIVE_TEXT_FIXED` as a validated strong baseline and do not
spend scientific roots from these bytes. Define and expose current-record hash
receipts; close or reject dependent multi-item transitions; totalize exception
basis; and make certificate commits contract-validity-only. Mirror every
model-actionable repair into the source-bound prompt schema, extend the sealed
certificate generator with the counterexamples above, regenerate bindings,
and obtain one more fresh independent audit. The headline architecture and
one-parent experiment do not need to change.

## Audited hashes

- `AGENTS.md`: `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e`
- headline plan: `f923c3c6dfe5f188b6af31e61443a7a454e53b33b2ded0472baf2bf2f9602798`
- active-text contract: `e14d7fcecdf775532481f15635843ad7cd5a2b046090ce1f8627e3788546e349`
- model-visible prompt schema: `574de628611225e914d5238640ece7d30d001ca3175bf2f5f8113d1ffecad538`
- scope proposal: `466319fa741a583f2cb9cf1dd6e01fd255877feae5818ea7697e3fab1e17dc75`
- prior closure audit v4: `95bac77e1e63733247db609a0d11410287ff9f60fc23c9d3afb51c2bacd77b33`

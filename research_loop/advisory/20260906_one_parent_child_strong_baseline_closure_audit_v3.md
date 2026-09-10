# One-parent/one-child strong-baseline closure audit v3

Date: 2026-09-06

Status: fresh independent read-only closure audit of the current proposal bytes.
This advisory changes no candidate bytes and authorizes no implementation,
model/tokenizer call, benchmark, adapter operation, GPU use, or scientific
claim.

## Verdict

**REVISE.** The stale-link rule, physical BM25 insert/remove accounting,
historical LEAFE snapshot, 960 live-record embedding ceiling, and one-parent
topology now close. The canonicalizer boundary and several of the formerly
partial semantic rules also close. The candidate still does not define an
executable strong baseline: the actual model-visible protocol lacks a frozen
calibration value and omits rejection laws used by the merger, several legal
evidence sets still have multiple or undefined semantic results, and the
certificate assigns zero or unallocated false units to some nonempty malformed
outputs.

## Closure of the v2 blockers

1. **Complete visible protocol / canonicalizer boundary / frozen calibration
   value — PARTIAL.** The raw-response boundary now passes: key order is
   unrestricted, duplicate keys reject, and accepted JSON is canonicalized
   before schema, size, hash, and semantic validation. The 5,579-byte schema
   file ends in exactly one U+000A and its placement in both user messages is
   deterministic. The value and rendering of `CALIBRATION_THRESHOLD_PPM` are
   not frozen, however, and the visible schema remains a summary rather than
   the complete rejection protocol.
2. **Total, single-valued support/relation/tuple/kind/status laws — PARTIAL.**
   Every proposition now needs positive complete support; the overlapping
   `SCORE_EFFECT` relations are removed; `ACTION_CONTRAST` has a unique
   same-program, same-starting-state pair rule; guidance and
   `REFLECT.kind` have explicit precedence; and the ordinary derived-status
   rule is single-valued. Scope, process tuples, modal outcomes, scope
   exceptions, and two status/transition statements remain unclosed.
3. **Executable certificate gold and malformed denominators — NOT CLOSED.**
   The ADD/REVISE/SUPERSEDE/LINK fixture discriminators and ordinary per-item
   scoring are useful repairs, but some nonempty malformed outputs receive no
   false unit and `MALFORMED_CURATE` is not allocated to the separately required
   record-bearing-versus-LINK precision denominators. The registered macro-F1
   gate also still has no executable class/confusion-matrix definition.
4. **Stale links and BM25 insert/remove accounting — CLOSED.** A link whose
   target later disappears or becomes `SUPERSEDED` is retained only as audit
   provenance, contributes no expanded document, and is not redirected.
   Record deltas are separately bounded by at most 960 insertions and 960
   removals/root; adding at most 2,880 event-block insertions yields 3,840
   insertions, 960 removals, and 4,800 physical BM25 mutations/root. This is
   consistent with the headline. The dense ceiling remains 960 live-record
   embeddings/root.
5. **LEAFE historical snapshot — CLOSED.** The later selector loads the
   earliest eligible content-addressed snapshot of checkpoint, rendered
   context/ledger prefix, environment, store, both indices, query fields,
   clock/budget, RNG counters, and source/config hashes. Diagnosis, recovery,
   rollback, and retrieval therefore cannot see later `P0` state. Its stated
   call, token, query, returned-memory, and fit arithmetic recalculates.
6. **One-parent topology — CLOSED.** There is one frozen parent and one closed
   childhood correction channel to the parented child, followed by a deletion
   firewall. `U` is an isolated causal counterfactual, `R0` is a fit-free
   replication, and roots/services share no store. The updater and optional
   comparator create no classroom, peer, ensemble, population-learning, or
   post-deletion parent edge. The scope proposal preserves this topology and
   remains proposal/CPU-only after any later ratification.

## Exact blockers

### 1. The actual updater still cannot see one complete, frozen protocol

The exact prompt inserts
`CALIBRATION_THRESHOLD_PPM=` followed by a value described only as “the one
nonnegative integer frozen on development-only data.” No integer, deterministic
selection function, or canonical decimal rendering is bound by the audited
bytes. Consequently the prediction-bias bins, certificate gold, and extracted
fully instantiated prompt hash are not fixed. Bind the integer (and its exact
ASCII representation) or bind a deterministic, source-hashed development
selection artifact before calling these bytes exact.

The injected schema file also omits merger laws that the model is expected to
satisfy: the complete per-kind object/null/outcome constraints, per-kind
counterevidence bins, the detailed scope and scope-exception construction,
process membership/rejection rules, supersession restrictions, and several
stored-record transition conditions appear only in the repository contract.
The updater is explicitly denied repository access. Either put every
model-actionable rejection law into the exact visible payload or narrow the
merger to the protocol that is actually shown. After that repair, recheck the
2,048-token fixed-schema partitions under the pinned tokenizer and regenerate
the literal-byte hashes and golden prompts.

### 2. The semantic function is not total and single-valued

The following are counterexamples under the current text:

- **Scope is not derived uniquely.** One support observation in one program
  whose public features contain `a` and `b` satisfies `PROGRAM/[program]`,
  `PUBLIC_FEATURE/[a]`, `PUBLIC_FEATURE/[b]`, and
  `PUBLIC_FEATURE/[a,b]`. Multiple-program evidence can likewise satisfy many
  subsets of the common feature intersection as well as `CROSS_PROGRAM`.
  Specify level precedence and the exact key function (for example, an exact
  maximal intersection rule) rather than saying only that named keys are
  shared.
- **Process tuples are not closed.** `PROCESS_ASSOCIATION` does not say that
  every cited support/counterevidence block must participate in exactly one
  accepted sequence, how unmatched cited blocks are rejected, or exactly
  which terminal outcome belongs to the one-block (`object=null`) versus
  two-block antecedent. Its modal tie order omits `INVALID`, although public
  terminal outcomes and the legal non-null proposition outcome include it.
  Thus both tuple membership/status counts and some modal results are
  undefined.
- **Scope exceptions are not a unique tuple.** The object family is null
  “unless it names the contrasting action family present in every cited
  contrast event,” but no `contrast event` is defined and the rule does not
  derive null versus a particular different family. Nor does it uniquely pair
  the distinct scopes. In addition, an exception necessarily contains
  counterevidence, so the global status law makes every admitted
  `EXCEPTION/CONTRADICTS` record `CONTRADICTED` forever. That is single-valued
  but semantically reverses whether the exception proposition itself is
  supported and weakens the claimed evidence-responsive baseline.
- **Status prose contradicts the derived law.** Section 4 says `SUPPORTED`
  needs at least two supporting *events*, while one complete observation
  already needs an action and terminal event; Section 5 and the visible schema
  require two complete support *observations*. More directly, Section 4 says
  `SUPERSEDE` creates only a `PROVISIONAL` or `SUPPORTED` replacement, while
  the general evidence-derived law and visible schema allow a replacement
  with counterevidence, which deterministically has status `CONTRADICTED`.
  Forbid that evidence shape or align the legal replacement statuses.

`ACTION_CONTRAST` pairing, the repaired `SCORE_EFFECT` sign rule, positive
support minimum, guidance mapping, memory-type mapping, and `REFLECT.kind`
precedence pass independently of these failures.

### 3. The once-only certificate still has malformed-output holes

The rule gives one false unit to a parse failure or a top level without the
required array, then counts array elements. A nonempty parsed CURATE response
with `"deltas":[]` is invalid under the one-to-four cardinality law but has a
required array and no element, so it contributes zero false units. A parsed
zero-item REFLECT response with an invalid top-level `schema_version`,
`program_event_id`, unknown top-level field, or other top-level
violation has the same zero-unit hole. State explicitly when top-level
invalidity produces a false unit and how it combines with element units.

Further, a `MALFORMED_CURATE` unit is not assigned to either of the separately
thresholded record-bearing CURATE and LINK provenance denominators. For
example, parse failures on every sealed LINK case can yield LINK recall zero
while leaving the advertised LINK precision denominator without those false
attempts. Bind malformed units to the sealed requested/gold class (or define
another exact allocation) and state the per-class and micro denominators.

Finally, the headline still requires `.85 macro-F1 over typed update/status
operations`, while the supporting contract merely says that this remains an
additional gate. It does not enumerate the operation/status classes, define
the unit when operation and status disagree, or specify how NOOP, malformed,
duplicate, and omitted units enter each confusion matrix. The reusable-record
recall gate should likewise identify its exact gold-unit set. Repair these
functions and generate a new sealed certificate version only after the
semantic function above is unique.

## Nonblocking notes

- The actor renderer now accepts complete canonical live records and complete
  eligible lexical-only event blocks; the prior records-only/raw-block
  contradiction remains closed.
- Stored array/cardinality/complete-record bounds, atomic overflow failure,
  one-delta-per-memory, no retry/reindex, and tombstone-free supersession
  support the 960 dense-document ceiling.
- The main ceilings recalculate to 5,291 calls, 972,544 output tokens, 4,400
  query embeddings, 7,208,960 active-memory input tokens, and 12 fits/root.
  The optional comparator recalculates to 160 calls, 45,056 output tokens,
  589,824 diagnosis/recovery input tokens, 160 queries, 151,552 returned
  memory tokens, and one fit/root.
- Historical snapshot persistent bytes remain receipted rather than hard
  capped. As in v2, this does not invalidate the registered call/token/fit
  ceilings, but an implementation claiming an all-in storage envelope should
  prebind a snapshot-storage ceiling.
- The query sanitizer correctly performs NFKC before delimiter/newline
  replacement, and event blocks add no dense embedding work.
- The contract should eventually bind `reflection_id` construction/uniqueness;
  this is not needed to decide the present verdict because stronger semantic
  and certificate blockers already reject promotion.

## Disposition

Do not promote `ACTIVE_TEXT_FIXED` as a validated strong baseline and do not
spend scientific roots from these bytes. Repair the three blockers, regenerate
the exact prompt/contract hashes and prospective certificate fixtures, and
obtain a fresh source-bound independent approval. No change to the one-parent
topology, LEAFE schedule, headline estimands, or registered root-count rule is
required.

## Audited hashes

- `AGENTS.md`: `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e`
- headline plan: `98dbbc64f5053c64af6348492c0effc1cee3541cc8a6ff2af01caa0be183ac49`
- active-text contract: `06f05152f1408d763cf9db8cf02ce4af3f1d5302075a29d6c7865022f5d28d45`
- model-visible prompt schema: `455eb8b24ef504da1b3e07132420c9bd4d7221a3231dc02e1a214d9b1154c9af`
- scope proposal: `466319fa741a583f2cb9cf1dd6e01fd255877feae5818ea7697e3fab1e17dc75`
- prior repair re-audit v1: `15950409c9c65e268f3314971fa9841d3ff7f189b9203054b7ac87076c5635c0`
- prior byte re-audit v2: `380f63343bf2e7cc8d7d8d2a4b4aec79d1ec6b194f3d520a615186c26f6ec152`

# PCFL V10 registry, rendering, and claim exact repair v1

Date: 2026-09-10  
Status: source-only advisory; no preparation, implementation, materialization, model execution, scientific execution, or claim authorization

## 0. Binding disposition

This advisory closes only the V9 consensus items `D-V9-REGISTRY-CLOSURE`,
`D-V9-ALGEBRA-PRIOR`, `D-V9-PREASSEMBLED-PATH`,
`D-V9-RENDERED-BRANCH-BOUNDARY`, and `D-V9-CLAUSE-DISPOSITIONS` at the
source-contract level. It does not close other V9 blockers by implication.

The V9 eight-row acceptance list was a lossy summary. An umbrella row may
coordinate tests, but may not replace, alias, waive, or compensate for a
named test below. Each active test has its own acceptance predicate, positive
fixture set, reject/mutation fixture set, evidence artifact, and failure or
claim-withdrawal disposition. A future exact source proposal must copy those
fields into individually addressable `AcceptanceTestSpec` records and must
emit a separate terminal receipt for every record.

Nothing here changes the frozen scientific envelope:

```text
conditions                         = 18
charged call slots per root        = 501
maximum charged tokens per root    = 148224
roots                              = 64 (32 DEV, 16 CONFIRMATION, 16 RESERVE)
maximum charged tokens, 64 roots   = 9486336
```

No condition, phase, endpoint, model call, retry, root, token allowance,
model, tokenizer, or scientific claim is added. Tests in this advisory are
model-free source/checker obligations or reducers over already authorized
future receipts. They authorize no execution.

## 1. Closed acceptance-test registry

### 1.1 Registry law

An active record has this exact shape:

```text
AcceptanceTestSpec = {
  test_id,
  kind,
  required_before,
  acceptance,
  positive_fixture_ids[],
  reject_or_mutation_fixture_ids[],
  evidence_artifact,
  failure_disposition,
  claim_withdrawal
}
```

The future registry validator must enforce all of the following:

1. Active inherited IDs are exactly `-00..-19` and `-23..-28`; `-20..-22`
   are not silently reused. This advisory adds `-30..-33`. Every active ID
   occurs once as a full record and once as a terminal receipt.
2. `MTEXTV4-DELAYED-BASELINE-OUTCOME-DESCENDANT-29` and
   `M0V4-V7-GUARD-EXCEPTION-NONEXPOSURE-34` are reserved active V10 IDs whose
   exact definitions must come from their separately reviewed repairs. They
   may not be represented by `-28`, `-01`, or another umbrella. A combined
   V10 proposal is incomplete until it contains their full records.
3. `FUTURE-PCFL-MULTITOPOLOGY-GENERALIZATION-21`,
   `FUTURE-PCFL-ONLINE-ACTION-OUTCOME-WRITE-ACTION-22`,
   `FUTURE-PCFL-TEXT-LORA-MATCHED-TRANSPORT-35`,
   `FUTURE-PCFL-RECALL-COMPOSITION-PLANNING-DECOMPOSITION-36`, and
   `FUTURE-PCFL-LONGITUDINAL-ACTIVE-TEXT-PLATEAU-37` are
   `DEFERRED_UNAUTHORIZED`, not current assay tests. They receive no call,
   endpoint, or evidence slot and block the associated claims.
4. The obsolete draft name `MTEXTV4-RESOURCE-FACTORIAL-19` is not a second
   active test. The reviewed replacement is
   `MTEXTV4-BASELINE-PUBLIC-PROJECTION-AND-RESET-19`; resource-factorial
   requirements remain separately tested by `-23..-25`.
5. A coordinator such as `M0V5-HANDOFF-DELAYED-VISIBILITY-CLOSURE-28` may
   require other receipts, but cannot count as their receipt. Shared code or
   a shared evidence bundle never merges acceptance predicates.
6. Missing, duplicate, renamed, aliased, umbrella-only, skipped, or
   nonterminal records make the proposal/assay `INCOMPLETE`. A failed
   invariant makes it `INVALID`. Neither state is scientific zero.

### 1.2 Restored inherited records

In the tables below, “withdrawal” is additional to the global rule that an
instrument-integrity failure supports no scientific clause.

| ID | Exact acceptance and positive fixtures | Reject/mutation fixtures | Evidence artifact; failure/withdrawal |
|---|---|---|---|
| `M0V4-EXACT-SOURCE-RATIFIABILITY-00` | Every proposed source byte, schema, constant, fixture ID, test, dependency, and output path is enumerated and hash-bound before any later preparation. Positive: exact closed manifest and byte-identical re-read. | Unlisted file/dependency, glob or directory grant, mutable external input, generated or executable content, hash/path drift, materialization attempt. | `ExactSourceRatifiabilityReceiptV1`; any mutation rejects source ratification and leaves all claims unauthorized. |
| `M0V4-ZERO-V7-RUNTIME-REUSE-01` | Closed path/module/artifact/provenance/interface/capability deny predicates reject V7 runtime reuse while an independently derived coincident ordinary scalar is accepted. | V7 path/import/module/subprocess, copied whole artifact or distinctive interface, V7 provenance parent, serialized/cache/env exposure, actor-visible V7 metadata, catch/fallback that exposes V7. | `ZeroV7FirewallReceiptV1`; failure invalidates clean-room status and all scientific clauses. |
| `M0V4-DISJOINT-CHECKER-AND-MUTATION-02` | Two independently authored checkers agree on all registered positive and negative fixtures without importing one another or a shared outcome-deciding helper. | Shared decision code/table, checker-to-checker import, expected-answer lookup, one checker absent, any disagreement, mutation corpus not exhaustive. | `DisjointCheckerAgreementReceiptV1` plus per-fixture verdicts; failure invalidates the affected contract and assay. |
| `M0V4-ACTOR-NONORACLE-03` | Actor-visible bytes are a pure function of allowlisted public state and carrier grants; private truth, answer, score, split, condition secret, oracle, `h`, future event, and checker state are absent. Positive: paired worlds with identical public projection render identically. | Flip each private field singly and jointly; inspect prompt, tools, errors, padding, cache/session IDs, lengths, ordering, timing class, and exception text. | `ActorNonoracleProjectionReceiptV1`; leakage invalidates every behavioral and mechanistic clause. |
| `M0V4-BUNDLED-READER-READ-CUT-04` | Reader return is one frozen, capability-checked bundle; successful READ consumes its registered charge and closes at the first world relation attempt. READ-cut makes otherwise identical carrier content unavailable. | Partial/unmetered return, post-action read, reopened reader, forged/foreign handle, cursor escape, hidden prefetch, direct backing-store access, READ-cut still returning content. | `BundledReaderCutReceiptV1`; failure invalidates supplied-memory attribution. |
| `M0V4-VISIBILITY-RESET-NONINTERFERENCE-05` | Every phase begins from its registered public cut; sterile reset destroys non-entitled scratch, cache, session, reader-open, repeat, model/conversation, and private state while retaining only named public/CAS descendants. | Carry phase transcript, model/session/cache key, hidden reader state, branch scratch, pre-reset repeat count, private score/`h`, or U state into D; cross-condition/root contamination. | `VisibilityResetNoninterferenceReceiptV1`; failure invalidates the affected assay and all delayed claims. |
| `M0V4-PROVENANCE-TRANSFORM-DAG-06` | Every released carrier atom/link has complete canonical parents, registered transform, finite acyclic lineage, independent support where required, and no private/actor/model-generated source. | Missing/foreign/postdated parent, cycle, self-support, alias duplicate, unsupported link, outcome-changing discretionary transform, synthetic evidence laundering. | `ProvenanceTransformDagReceiptV1`; failure invalidates carrier-grounding and connected-memory clauses. |
| `M0V4-CAS-TWO-FREEZE-DURABILITY-07` | First freeze seals source/instrument objects; second freeze seals future execution outputs. Content-addressed bytes remain immutable and independently rehashable across the boundary; no output is a parent of a first-freeze object. | Mutable object, overwritten hash, same hash/different bytes, output-to-source edge, missing durability receipt, nondeterministic re-read, temporary-only evidence. | `CasTwoFreezeDurabilityReceiptV1`; failure makes the proposal/assay incomplete or invalid and bars every claim. |
| `M0V4-CPU-CONFORMANCE-08` | All authorized deterministic preparation/checker/reducer operations are CPU-only, deterministic under the frozen environment, and byte-identical across two permitted conformance runs. | GPU/accelerator use, model/tokenizer call, network input, nondeterministic order/seed, platform-dependent serialization, hidden concurrency. | `CpuConformanceReceiptV1`; failure bars preparation acceptance and all downstream claims. This advisory does not run the test. |
| `MTEXTV4-RENDERED-BOUNDARY-09` | The complete actor-visible system/user/chat-template/tool/parser boundary is reconstructed and hashed from allowlisted public inputs for every legal mode, phase, and terminal; it additionally requires the distinct `-31`, `-32`, and `-33` receipts. | Any private/abandoned-branch byte, protocol mismatch, hidden repeat state, prompt/parser disagreement, unregistered template/tool field, future handle, length/order/padding channel. | `RenderedBoundaryReceiptV1`; failure invalidates every scientific assay. The three dependency receipts are not replaced by this one. |
| `MTEXTV4-ROSTER-ENDPOINT-RESOURCE-10` | Exact 18-condition roster, legal phase projections, endpoint applicability, 501 charged slots/root, 148,224 tokens/root, 64-root split, and per-arm resource fields agree across source, schema, plan, and reducers. | Added/dropped/renamed condition, endpoint borrowing, slot/token drift, reserve rescue, hidden retry/call, uncharged arm, inconsistent projection. | `RosterEndpointResourceReceiptV1`; failure makes the assay invalid/incomplete and withdraws all claims. |
| `MTEXTV4-CONFIRMATION-CLAIM-GATE-11` | Only a complete, sealed, fixed-model/fixed-topology confirmation census under frozen source, rendering, resources, receipts, noncompensatory gates, and independent review can reach claim review. Positive: all 16 confirmation twin blocks complete with no DEV/reserve substitution. | Claim from source work, DEV, partial cells, reserve, retries, pooled averages, missing invariant, future/deferred mechanism, or unhashed output. | `ConfirmationClaimGateReceiptV1`; failure leaves every empirical claim unauthorized. |
| `M0V5-SOURCE-AUTHORING-VS-PREPARATION-AUTHORITY-12` | A human grant names only inert source/spec/checker/test paths and the nonauthoritative manifest; source authoring neither imports nor executes authored content and grants no preparation authority. | Unlisted path, executable import, fixture/root/data generation, interpreter invocation, dependency acquisition, benchmark/model/tokenizer run, training/GPU/release action. | `SourceAuthoringGrantV1` plus closed authoring-plan receipt; failure stops authoring and authorizes nothing downstream. |
| `M0V5-DELAYED-ENTRY-OUTCOME-DESCENDANT-13` | After sterile reset D can receive only the named old entry and named `a19/l06` outcome-descendant content through its registered public lineage; hashes and parents are exact. | Any U transcript/belief/action, private outcome, alternate descendant, hidden summary, condition/root leak, mutable or absent lineage, extra reset survivor. | `DelayedEntryOutcomeDescendantReceiptV1`; failure invalidates D and withdraws delayed-carrier specificity. |
| `MTEXTV4-TARGET-ONLY-ALGEBRA-DECODING-14` | The exact section-2 decoder goldens pass for all 32 `k`, and every applicable confirmation shortcut count for target-only, no-memory, and passive-signature is at most 5. | Wrong alias parse/XOR/path, decoder reads forbidden state, missing/malformed receipt, count above 5, padding keyed to truth/answer. | `AlgebraPriorReceiptV1`; failure withdraws connected specificity for the affected route endpoint, and D failure also withdraws delayed-carrier specificity. |
| `M0V4-PRODUCER-SCORER-ANSWER-NEUTRALITY-15` | Exact producer, query, reader, path-order, score-label, and scorer-absence swaps leave all upstream bytes/actions invariant; all six registered minimum paths score symmetrically. It additionally requires `-30`. | Goal/answer/scorer field admitted by producer, changed candidate order, answer/rank in row/cursor/padding, scorer changes rendering/action, reference path privileged, preassembled path carrier. | `ProducerQueryScorerNeutralityReceiptV1` plus distinct `LocalEdgeReceiptV1`; failure invalidates the instrument and connected-memory attribution. |
| `MTEXTV4-BRIDGE-TWIN-TRACE-EQUIVALENCE-16` | Exact raw terminal law, canonical trace equivalence, bridge behavior change, decisive-C first-action twin switch, same-root/same-`h` conjunction, and twin-minimum numerator conform. | Text-only difference, alternate valid path treated unequal, post-terminal action, wrong state/action, A compensates B, one `h` compensates twin, borrowed trace/receipt. | `BridgeTwinNormalizedTraceReceiptV1`; failure withdraws connected-path specificity or invalidates the assay when structural. |
| `MTEXTV4-CONDITION-PHASE-ENDPOINT-APPLICABILITY-17` | Every condition/phase/endpoint is typed exactly `0|1` or `NA`; observed behavioral failures remain applicable zeros; `NOT_REACHED` is call padding only; every value comes from its own receipt. | NA/zero substitution, foreign condition/phase/root/`h`, AUTH fallback, copied score, synthesized full-sequence/retention value, gate-required NA, averaging other than twin minimum. | `EndpointApplicabilityReceiptV1`; structural failure invalidates the assay; valid zeros remain negative evidence. |
| `MTEXTV4-CLAUSE-SPECIFIC-NEGATIVE-DISPOSITION-18` | Every allowed clause maps to exact noncompensatory gates and a clause-specific negative/invalid/withdrawal outcome as in section 5; deferred clauses are unconditionally withdrawn. | Global pass label, optional gate rescuing mandatory miss, pooled compensation, invalidity called zero, shortcut averaged away, retention/learning/generalization wording. | `ClauseDispositionReceiptV1`; failure bars claim release; a valid gate miss withdraws only the mapped clause plus any conjunction requiring it. |
| `MTEXTV4-BASELINE-PUBLIC-PROJECTION-AND-RESET-19` | Seven legal mode/protocol pairs, typed public projection, deterministic RAG/null semantics, saturated repeat, reset destruction, and per-arm charging match independent goldens. | Mode/protocol conflation, private-field projection, hidden retrieval, nonliteral null, unstable BM25/tie order, repeat leakage, reset survivor, uncharged baseline work. | `BaselineProjectionResetReceiptV1`; failure invalidates affected contrasts and withdraws practical-baseline language; it cannot rescue a mechanism clause. |
| `MTEXTV4-ROSTER-SLOT-ENVELOPE-23` | All 18 rows and phase projections sum exactly to 501 slots and 148,224 tokens/root, with exact 64-root/split totals and `NOT_REACHED` partition. | Any added/removed/renamed slot, allowance drift, early terminal deleting a charged slot, retry/reserve substitution, sentinel counted as endpoint. | `RosterSlotEnvelopeReceiptV1`; failure invalidates resource comparability and all claims. |
| `MTEXTV4-PER-ARM-CHARGED-RESOURCE-VECTOR-24` | Each arm reports the full registered vector for preprocessing, index/graph, reader return, calls/tokens, temporary/deleted artifacts, concurrency, accelerator, and network fields, including zero-valued fields. | Omitted factor, aggregate-only total, work charged to another arm, deleted temp work absent, missing zero, GPU/network/concurrent unattributable work. | `PerArmChargedResourceVectorReceiptV1`; failure invalidates the arm and withdraws practical/efficiency comparisons. |
| `MTEXTV4-RESOURCE-METER-NONOMISSION-25` | Independent meters reconcile every resource event to one arm and root, with no negative, duplicate, unowned, or unmetered event. | Hidden preprocessing/index/read, cached work, temp deletion, retry, background/concurrent process, GPU/network use, mismatch between meter and receipt. | `ResourceMeterNonomissionReceiptV1`; failure invalidates affected assays and every practical/efficiency clause. |
| `M0V4-PROVENANCE-FINITE-ORDER-26` | Full finite position table, exact seven-pair order, post-alias canonical IDs, complete roots, later independent support, and legal root-deduplicated diamonds match positive fixtures. | Pair/order drift, alias-before/after mismatch, incomplete roots, support earlier than claim, duplicate-root support, unregistered diamond, nondeterministic tie. | `ProvenanceFiniteOrderReceiptV1`; failure invalidates grounded carrier and connection evidence. |
| `M0V4-PROVENANCE-REVOCATION-CYCLE-27` | Contradiction precedence, permanent revocation, cycle rejection, and batch atomicity match both checkers; rejected batches change no state. | Revived revoked item, partial batch commit, cycle admitted through alias/diamond, order-dependent contradiction, unsupported derived item. | `ProvenanceRevocationCycleReceiptV1`; failure invalidates all carrier-derived evidence. |
| `M0V5-HANDOFF-DELAYED-VISIBILITY-CLOSURE-28` | All public/private handoff, delayed-entitlement, rendered-leakage, reset, and lineage receipts are present and jointly pass. | Any missing dependency receipt; mutation of private route/condition/truth/score/oracle/model/session/V7 field affects actor-visible state; delayed entitlement exceeds the named lineage. | `HandoffDelayedVisibilityClosureReceiptV1`; failure invalidates the assay. This conjunction never replaces `-01`, `-03`, `-05`, `-09`, `-13`, `-29`, `-31`, `-32`, `-33`, or `-34`. |

### 1.3 New exact records required by this repair

| ID | Exact acceptance and positive fixtures | Reject/mutation fixtures | Evidence artifact; failure/withdrawal |
|---|---|---|---|
| `M0V4-LOCAL-EDGE-NO-PREASSEMBLED-PATH-30` | Section 3's carrier grammar accepts only one-step atoms and adjacent public-auth links; both legitimate A/B alternatives remain discoverable only through sequential local reads, within the unchanged budget. | Whole path/route/plan/script/answer, goal-to-path table, preferred parent path, transitive edge, multi-handle sequence, target-indexed cursor map, full-path return, padding/order encoding. | `LocalEdgeNoPreassembledPathReceiptV1`; failure invalidates the memory instrument and withdraws composition/connected-path language. |
| `MTEXTV4-ABANDONED-BRANCH-NONRELEASE-31` | Section 4.1 paired executions with identical allowlisted join projection render byte/token/tool/parser-identically from join onward despite exhaustive abandoned-branch mutations. | Mutate branch scratch/plan/belief/read/command/tool return/failure/timing/handle/padding/cache/session and observe any later difference. | `AbandonedBranchNonreleaseReceiptV1`; failure is actor leakage and invalidates every scientific clause. |
| `MTEXTV4-REPEAT-STATE-POLICY-VISIBILITY-32` | Section 4.2 produces visible saturated sequences `[1,2,3,3,3,3,3,3]`, binds the same value into fingerprints, resets by reader identity, and conforms in common/blocked/passive/RAG modes. | Omit/hide repeat, expose 4..8, fingerprint mismatch, share counters across reader/root/phase/condition, survive reset, count failed/foreign read. | `RepeatStatePolicyVisibilityReceiptV1`; failure invalidates memory-mechanism and rendered-boundary claims. |
| `MTEXTV4-PROMPT-PROTOCOL-SCHEMA-CROSSPRODUCT-33` | Every legal mode/protocol/phase/stage command has the exact advertised prompt fragment and parser result; every illegal cross-product member is rejected consistently. | Protocol/mode mismatch, READ under NONE, args to `RAG_READ`, U relation, wrong-stage commit, future handle, unadvertised command, prompt/parser/schema disagreement. | `PromptProtocolSchemaCrossproductReceiptV1`; failure invalidates the affected condition and the overall assay if confirmation completeness is lost. |

## 2. Exact algebra-prior falsifier (`-14`)

### 2.1 Model-free decoder

The registered decoder reads only the released start alias, released target
alias/goal label, and fixed relation catalog. It may not read a carrier,
reader return, public event ledger, hidden `h`, condition, split, score,
expected answer, semantic ID, or checker oracle.

Parse `node_alias(S) = "n" + lower_hex2(k)`, set `m = k mod 16`, and define:

```text
rho(j,k) = "r" + lower_hex2(j XOR m)

ALG_A_0(k) = [rho(0,k), rho(1,k), rho(4,k), rho(5,k)]
ALG_A_1(k) = [rho(2,k), rho(3,k), rho(4,k), rho(5,k)]
ALG_B_0(k) = [rho(0,k), rho(1,k), rho(4,k), rho(6,k)]
ALG_B_1(k) = [rho(2,k), rho(3,k), rho(4,k), rho(6,k)]

ALG_D_guess(q,upper,k) = [rho(0,k), rho(1,k), rho(4,k), rho(7+q,k)]
ALG_D_guess(q,lower,k) = [rho(2,k), rho(3,k), rho(4,k), rho(7+q,k)]
q in {0,1}, selected without reading h
```

The positive golden corpus is the Cartesian product of all 32 `k`, goals A
and B, and both upper/lower alternatives. Each A/B path must execute in the
fixture world and score successful without memory. For each D paired world,
the fixed `q` decoder must have twin-minimum success exactly zero: it cannot
read `h`, the four-relation route uses the entire relation budget, and it
cannot try both `rho(7,k)` and `rho(8,k)`.

Reject fixtures are: bad `k` parse; using `k` rather than `k mod 16`; addition
instead of XOR; swapped `rho(5)`/`rho(6)`; omission of either parent path;
any read of `h`, carrier, ledger, score, oracle, or expected answer; a fifth
relation attempt; or any D twin-minimum above zero. These deterministic
goldens prove a fixed-topology bypass exists; they are not model evidence and
add no condition or call.

### 2.2 Existing-call matched probes and acceptance

`TARGET_ONLY_ANSWER_PRIOR_TAPE` is the pure one-call-per-phase probe. Its path
and delayed renderings match the registered system/template version, phase
start, released goal, relation catalog, command schema, four relation
opportunities, terminal rule, and output allowance, but contain no memory,
handle, static context, retrieval, path rank, answer, or score. Any inert
padding is frozen and independent of root truth, goal answer, condition,
split, score, and model output.

`NO_MEMORY_RECURRENT` matches AUTH's recurrent opportunities, public
state/outcome feedback, action/read budgets, parser, and output allowances;
each memory dispatch returns the same fixed identity-null/no-grant envelope
without lookup. `PASSIVE_SIGNATURE_RECURRENT` retains its reviewed passive
signature behavior. None is mislabeled interface-identical to AUTH.

For each
`e in {task_success_A, task_success_B, two_goal_task_success,
delayed_task_success}` and
`c in {TARGET_ONLY_ANSWER_PRIOR_TAPE, NO_MEMORY_RECURRENT,
PASSIVE_SIGNATURE_RECURRENT}`, compute only from existing future receipts:

```text
shortcut_count(e,c) = sum_{k in CONFIRMATION} min_{h in {0,1}} e(k,h,c)
accept iff shortcut_count(e,c) <= 5
```

Every applicable pair must have 32 Boolean same-cell receipts and a terminal
reducer receipt. `NA`, missing/duplicate/foreign receipt, invalid rendering,
or borrowed value cannot satisfy the bound. A count greater than 5 is a
`SHORTCUT_BREACH(e,c)` and is noncompensatory: it withdraws connected-memory
specificity for the corresponding path/two-goal clause; a delayed breach also
withdraws supplied-delayed-carrier specificity. Report every count and the
decoder goldens even when another contrast passes.

### 2.3 Producer, query, reader, and scorer swaps (`-15`)

Carrier production and index construction have exactly these inputs:

```text
(instrument_version, k, h, public primitive events, frozen slot map,
 registered transform, phase cut)
```

For an old path carrier, `h` may affect only root-public rows allowed by the
paired-world law; it never selects a path or answer. There is no parameter or
ambient capability for released goal, expected path, reference script, task
score, answer score, model output, condition display name, split, dispatch
order, scorer, or oracle. Goal release and scorer construction occur only
after carrier/index hashes are sealed. The reader is exactly a pure function
of `(carrier_sha256, anchor, cursor, reader_open, repeat_state)`. The scorer
receives a sealed trace only after its final receipt and has no edge to the
producer, index, renderer, reader, parser, controller, request, or action.

For every root, transform, applicable phase, public-capability anchor, and
legal/one-past cursor, the separately identified swaps are:

| Fixture ID | Held fixed | Swap/mutation | Exact acceptance |
|---|---|---|---|
| `PQS-PRODUCER-GOAL` | primitive events, slots, transform, cut | A/B/D released goal and target | carrier/index bytes, handles, row order, candidate order identical |
| `PQS-PRODUCER-ANSWER` | all producer inputs | expected answer, preferred path, reference-script choice | fields rejected; sealed bytes remain identical |
| `PQS-READER-GOAL` | carrier/index, anchor, cursor, open/repeat | goal and target | return bytes and grants identical |
| `PQS-READER-SCORE` | carrier/index and complete query agenda | task/path/answer score, split, oracle | return bytes and order identical |
| `PQS-PATH-ORDER` | carrier/index and trace | scorer lists upper/lower vs lower/upper | producer/reader/render bytes and score identical |
| `PQS-SCORE-LABEL` | carrier/index, render, trace | correct vs deliberately wrong private label | no upstream byte/action changes; only private score changes or rejects |
| `PQS-SCORER-ABSENCE` | complete unscored receipt | delete/corrupt scorer or oracle | no re-execution or changed request/action; assay becomes invalid/incomplete |

The checker-only query agenda is the lexicographically sorted Cartesian
product of public-capability anchors and legal/one-past cursors. A model may
still choose a goal-conditioned sequence of legal reads; that behavior is not
producer leakage. No row, slot, cursor, padding, candidate, or return order
may encode goal, answer, score, path-equivalence rank, or reference rank.

Positive scorer fixtures are the six minimum paths, accepted under both list
orders when their atoms/links were previously returned and cited:

```text
A: [p0,p1,p4,p5]  [p2,p3,p4,p5]
B: [p0,p1,p4,p6]  [p2,p3,p4,p6]
D: [p0,p1,p4,nh]  [p2,p3,p4,nh]
```

Reject fixtures are answer-only traces, only the reference parent path, a
copied final answer, omitted bridge, cyclic/post-action dependencies, wrong
terminal, unchanged TWIN terminal action, and every section-3 preassembled-
path mutation. `ProducerQueryScorerNeutralityReceiptV1` contains every swap
input hash, both output hashes, scorer verdicts, and the separate `-30`
receipt hash. Any failed swap or asymmetric legal-path score invalidates the
instrument before model execution.

## 3. Local-edge grammar and no-preassembled-path falsifier (`-30`)

Goal blindness is necessary but insufficient: a goal-blind producer could
still expose every route and answer. The carrier representation is therefore
closed by grammar, not intention.

An actor-visible carrier item is exactly one of:

```text
PublicAtomV4(atom_handle, public_atom_payload)          # one STEP atom
PublicAuthLinkV4(link_handle, left_atom_handle,
                 right_atom_handle, public_link_payload) # one adjacent pair
```

Each `PublicAtomV4` denotes one primitive STEP event. Each
`PublicAuthLinkV4` joins exactly two adjacent atoms under the frozen provenance
registry. It may not be transitive. One reader return contains at most one
atom and one incident local link plus, if required to interpret that link,
the opposite endpoint atom. It contains no ordered sequence of three or more
atom handles, no sequence of two or more link handles, and no recursive
carrier. Cursor and handle syntax is canonical and independent of target,
answer, route rank, or scorer order.

Forbidden fields and encodings include `route`, `path`, `plan`, `script`,
`answer`, `goal_to_path`, `parent_path`, `next_steps`, `agenda`, a target-
indexed cursor map, transitive `p0->p4` style links, a full-path memory return,
and answer/route information encoded through item order, duplicate count,
padding, length, alias choice, cursor gaps, or handle bits. The restriction is
on explicit preassembly: the set of lawful local atoms and links may of course
support reconstruction by successive authorized reads; otherwise the assay
would not test connected use.

Positive fixtures contain the authentic local atoms and adjacent links for
both upper and lower A/B alternatives. Sequential legal reads must make each
alternative constructible within the unchanged read/action budget, and the
scorer must accept both enumeration orders. Reject/mutation fixtures inject:

1. a bundle containing all A, B, or D scripts;
2. a goal-to-path or answer table despite goal-blind production;
3. only a reference script's preferred parent path;
4. a transitive link, ordered multi-handle route, target-indexed cursor, or
   `next` pointer that walks a frozen solution;
5. a reader return containing a full path; or
6. route/answer bits in padding, order, length, duplicates, aliases, handles,
   errors, or cache keys.

Both independent checkers must reject every mutation and must additionally
prove, for every positive object, local adjacency, maximum return arity, and
absence of forbidden semantic fields and covert representation channels.
Failure invalidates the instrument before model execution; it withdraws all
claims of recalled-link composition or connected-memory construction.

## 4. Rendered branch-boundary closure (`-31..-33`)

### 4.1 Abandoned-branch nonrelease (`-31`)

For every branch/join site, construct paired model-free rendering fixtures
whose active branch, registered public events, entitled carrier projection,
public world state, repeat state, and terminal status at join are identical.
Mutate only abandoned-branch scratch, plan, belief, reads, commands, tool
returns, failures/exceptions, timing bucket, sibling handles, padding,
temporary objects, cache keys, session IDs, and private scorer/oracle data.

Acceptance requires byte identity from the join through terminal for:

```text
rendered system bytes
rendered user bytes
chat-template bytes
token IDs and attention/tool boundary IDs
tool advertisements and envelopes
parser state and accepted-command set
public cache/fingerprint inputs
```

It also requires no abandoned-branch object or receipt as a provenance parent
of the active branch, join, later render, or score. Positive fixtures cover A
upper/lower, B upper/lower, D terminal alternatives, correct/wrong finish,
abstain, budget exhaustion, and output-invalid terminals. Any changed byte,
token, ordering, length, error, handle, cache/fingerprint, parser decision, or
parent edge rejects. This is separate from generic actor nonoracle and cannot
be discharged by an allowlist assertion.

### 4.2 Repeat-state policy visibility (`-32`)

For one reader identity with eight successful returns, actor-visible
`repeat_count` is exactly:

```text
[1, 2, 3, 3, 3, 3, 3, 3]
repeat_count = min(3, 1 + n_prior_successful_returns_for_this_identity)
```

The exact saturated value must be present in every applicable return and must
be the value bound into the returned-object fingerprint. Counters are keyed
by `(root, condition, phase, reader identity)`; they are not shared across
identities and are destroyed by the registered reset. Rejected, malformed,
foreign, and `NOT_REACHED` requests do not increment the counter.

Positive goldens cover common/anchor, blocked/blocked-anchor,
passive/passive-null-anchor, and RAG/RAG-auto reader identities, two
independent identities, and reset/restart. Reject fixtures cover omitted or
hidden repeat state, unsaturated values 4 through 8, visible/fingerprint
mismatch, cross-identity/root/phase/condition sharing, reset survival, and an
increment on a failed or foreign read. Failure invalidates rendered-boundary
integrity and every memory-mechanism clause; it is not a behavioral zero.

### 4.3 Prompt/protocol/schema cross-product (`-33`)

The legal mode/protocol set is closed:

| Mode | Protocol |
|---|---|
| `COMMON` | `ANCHOR` |
| `BLOCKED` | `BLOCKED_ANCHOR` |
| `PASSIVE` | `PASSIVE_NULL_ANCHOR` |
| `RAW_STATIC` | `NONE` |
| `RAG` | `RAG_AUTO` |
| `NATIVE` | `NONE` |
| `NO_MEMORY` | `NONE` |

For P and D, enumerate relation, finish, and abstain stages plus each legal
memory form when the protocol admits one. For U, enumerate experiment
commands `e0..e3`, abstain, then commit `c0`/`c1`/abstain at the legal stage;
U admits no relation command. The target-only tape uses the blocked/open-loop
P/D projection. AUTH-no-feedback uses the common open-loop projection and
may expose no future handle. All legal commands are members of the frozen
`PCFL_COMMAND_V4` tagged union.

For every legal `(mode, protocol, phase, stage, command)` fixture, the exact
prompt fragment advertises the command once, the serialized command validates
against its schema, and the parser accepts it with the same semantics. Every
other cross-product member is rejected by prompt construction, schema, and
parser consistently. The reject corpus includes protocol/mode mismatch, READ
under `NONE`, arguments to `RAG_READ`, a relation in U, commit before/after its
stage, memory use after reader close, a future-handle tape, unadvertised or
unknown command, and any prompt/schema/parser disagreement.

The evidence artifact is a fully rendered table containing source fragment
hash, system/user/template byte hashes, token-ID hash, tool-envelope hash,
schema verdict, parser verdict, and normalized command/result for every
fixture. No model call is part of this test. One mismatch rejects the
applicable condition; missing confirmation completeness invalidates the
assay.

### 4.4 Raw trace, normalization, and terminal closure (`-16`)

A raw trace starts at the registered public phase state, records every charged
world relation attempt in order as
`(pre_state, semantic_relation, public_outcome, post_state)`, then records
exactly one terminal. Reads, plans, citations, scratch, calls, timing,
padding, and receipt IDs are not world actions. The terminal is the first of:

```text
FINISH_OK(goal)       finish at released target
WRONG_FINISH(state)   finish elsewhere; ordinary behavioral zero
ABSTAIN(state)        ordinary behavioral zero
BUDGET_EXHAUSTED      four relation attempts without FINISH_OK
OUTPUT_INVALID(code)  registered parse/size failure; behavioral zero
```

Finish, wrong finish, and abstain terminate immediately. `NO_EFFECT` is
nonterminal, consumes one relation attempt, and closes the reader if it is the
first relation attempt. If the fourth relation attempt leaves no correct
finish opportunity, append `BUDGET_EXHAUSTED`. Later unissued call slots are
`NOT_REACHED` padding, never actions or endpoints. Illegal/private commands,
foreign/missing receipts, controller exceptions, or scorer/oracle leaks are
instrument faults, not terminals.

Canonicalization discards `NO_EFFECT` from the effective-move skeleton while
retaining its charged-budget consequence and terminal. State-changing old
relations map exactly:

```text
p0 or p2 -> LEG_1
p1 or p3 -> LEG_2
p4       -> BRIDGE
p5       -> TERMINAL_RELATION_R05(destination_role)
p6       -> TERMINAL_RELATION_R06(destination_role)
nh       -> TERMINAL_RELATION_R07_OR_R08(destination_role)
other    -> OTHER_EFFECTIVE(pre_role, relation, post_role)
```

Upper and lower paths are equivalent for goal `g` exactly when both normalize
to `(LEG_1, LEG_2, BRIDGE, TERMINAL_RELATION_TO(g), FINISH_OK(g))`. The
terminal semantic ID may differ only under the registered TWIN binding.
`bridge_behavior_change_g=1` iff AUTH is a successful connected constructive
use in that equivalence class and BRIDGE_CUT is not. A text/action-string
difference alone is insufficient.

The decisive state is public node `C`, reached by
`(LEG_1,LEG_2,BRIDGE)` before any terminal. AUTH terminals are A=`R05`,
B=`R06`; TWIN terminals are A=`R06`, B=`R05`.
`twin_terminal_switch_g=1` iff both arms reach C, AUTH's first relation from C
is its registered AUTH terminal, and TWIN's first relation from C is its
registered TWIN terminal. Any earlier finish, abstain, no-effect,
output-invalid/budget terminal, old AUTH action, or other first relation makes
it zero.

Per `(k,h)`, not pooled:

```text
bridge_pair = bridge_behavior_change_A & bridge_behavior_change_B
twin_pair   = twin_terminal_switch_A & twin_terminal_switch_B
connected_trace_dependence =
  connected_two_goal_use(AUTH)
  & trace_support_integrity_A(AUTH)
  & trace_support_integrity_B(AUTH)
  & bridge_pair & twin_pair
```

The confirmation numerator is
`sum_k min_h connected_trace_dependence(k,h)` and must be at least 12 of 16.
Deleting all registered supporting atoms/links must invalidate each cited
constructive trace. Neither goal nor one twin compensates for its mate.
Positive fixtures include both valid parent paths for both goals and the
registered TWIN switch. Reject fixtures include every other terminal, missing
bridge/support, post-terminal action, text-only changes, wrong decisive state,
wrong first terminal relation, cross-root/phase receipt, and pooled or
single-goal compensation. Evidence is
`BridgeTwinNormalizedTraceReceiptV1`; a structural mismatch invalidates the
assay, while a complete Boolean miss withdraws connected-path specificity.

## 5. Exact applicability and clause dispositions (`-17`, `-18`)

### 5.1 Closed condition-by-phase-by-endpoint matrix

The abbreviations expand to all same-condition scalars in the inherited
endpoint contract: `PB` path behavior for the named A/B phase; `PM` path
connected-mechanism family; `UI` uncertainty/information/acquisition family;
`DB` delayed behavior; `DM` delayed connected-carrier family; `2B` two-goal
task success; `2M` connected two-goal use; `F/R` full-sequence task,
retention, acquisition-to-delayed-use, and online learning. There is no
unlisted same-condition endpoint.

| Condition | A.PB | A.PM | B.PB | B.PM | U.UI | D.DB | D.DM | 2B | 2M | F/R |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `AUTH_RECURRENT` | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | NA |
| `AUTH_SCRATCH_OFF` | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | NA |
| `ATOMS_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `DERANGED_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `REACHOUT_OFF_RECURRENT` | 0\|1 | 0\|1 | 0\|1 | 0\|1 | NA | 0\|1 | 0\|1 | 0\|1 | 0\|1 | NA |
| `NO_MEMORY_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `PASSIVE_SIGNATURE_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `RAW_CONTEXT_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `RAG_RAW_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `NATIVE_GRAPH_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `BRIDGE_CUT_RECURRENT` | 0\|1 | 0\|1 | 0\|1 | 0\|1 | NA | NA | NA | 0\|1 | 0\|1 | NA |
| `TWIN_REDIRECT_RECURRENT` | 0\|1 | 0\|1 | 0\|1 | 0\|1 | NA | NA | NA | 0\|1 | 0\|1 | NA |
| `UNCERTAINTY_SHAM_RECURRENT` | NA | NA | NA | NA | 0\|1 | NA | NA | NA | NA | NA |
| `OLD_CUT_RECURRENT` | NA | NA | NA | NA | NA | 0\|1 | 0\|1 | NA | NA | NA |
| `NEW_CUT_RECURRENT` | NA | NA | NA | NA | NA | 0\|1 | 0\|1 | NA | NA | NA |
| `NO_PERSIST_NEW_RECURRENT` | NA | NA | NA | NA | NA | 0\|1 | 0\|1 | NA | NA | NA |
| `TARGET_ONLY_ANSWER_PRIOR_TAPE` | 0\|1 | NA | 0\|1 | NA | 0\|1 | 0\|1 | NA | 0\|1 | NA | NA |
| `AUTH_NO_FEEDBACK_TAPE` | 0\|1 | NA | 0\|1 | NA | 0\|1 | 0\|1 | NA | 0\|1 | NA | NA |

Cross-condition bridge/twin, shortcut, cut, and best-text scalars are derived
only from their exact named same-cell inputs. They are not row fields.
Baseline diagnostics cannot populate `PM`, `DM`, or `2M`.

Each endpoint record binds
`(root_id,k,h,condition,phase,endpoint_id,applicability,value,
phase_receipt_sha256,trace_sha256,scorer_sha256)`. A `0|1` cell requires an
integer Boolean from its own receipt. An `NA` cell requires literal `NA` and
null-sentinel receipt hashes. `WRONG_FINISH`, `ABSTAIN`, `BUDGET_EXHAUSTED`,
and registered `OUTPUT_INVALID` remain applicable and score zeros wherever
the success predicate is unsatisfied. `NOT_REACHED` is only an unissued
post-terminal call-slot sentinel; it is never an endpoint. Foreign root,
condition, phase, `h`, AUTH fallback, cached/copied score, and imputation are
rejected. `2B` and `2M` are Boolean only when both same-condition operands are
Boolean. `F/R` is always `NA`. Twin reduction is only
`min(e(k,0,c),e(k,1,c))`; no pooling or compensation exists.

### 5.2 Gate registry

Every count is over the 16 CONFIRMATION `k` blocks after twin minimum.
Required cells must be complete Booleans and terminally receipted.

```text
G0 INSTRUMENT_VALID
  All required source, handoff, rendering (-09,-31,-32,-33), local-edge
  (-30), delayed entitlement, producer/query/scorer, reset/session, CAS,
  provenance, receipt, applicability, and resource invariants pass; the
  confirmation registry is complete.

G1 AUTH_HEADROOM
  count(two_goal_task_success, AUTH_RECURRENT) >= 12
  count(delayed_task_success, AUTH_RECURRENT) >= 12

G2 CONNECTED_BENEFIT
  for c in {ATOMS_RECURRENT, DERANGED_RECURRENT,
            BRIDGE_CUT_RECURRENT, REACHOUT_OFF_RECURRENT}:
    count(two_goal_task_success, AUTH_RECURRENT)
      - count(two_goal_task_success, c) >= 4
  count(connected_two_goal_use, AUTH_RECURRENT) >= 12
  count(connected_trace_dependence) >= 12

G3 PUBLIC_CALIBRATION
  for e in {separating_choice, realized_information,
            belief_revision, acquisition_success}:
    count(e, AUTH_RECURRENT) >= 12
  for e in {realized_information, belief_revision, acquisition_success}:
    count(e, UNCERTAINTY_SHAM_RECURRENT) <= 4
  count(acquisition_success, AUTH_RECURRENT)
    - count(acquisition_success, UNCERTAINTY_SHAM_RECURRENT) >= 8

G4 DELAYED_CARRIER
  count(delayed_connected_integration, AUTH_RECURRENT) >= 12
  for c in {OLD_CUT_RECURRENT, NEW_CUT_RECURRENT,
            NO_PERSIST_NEW_RECURRENT}:
    count(delayed_task_success, c) <= 4
    count(delayed_task_success, AUTH_RECURRENT)
      - count(delayed_task_success, c) >= 8

G5 SHORTCUT_PATH
  every section-2 count for task_success_A, task_success_B, and
  two_goal_task_success is <= 5

G6 SHORTCUT_DELAYED
  every section-2 delayed_task_success count is <= 5

G7 ZERO_NET_ATOMS
  for e in {task_success_A, task_success_B, two_goal_task_success,
            plan_valid_A, plan_valid_B, first_action_correct_A,
            first_action_correct_B, plan_execution_consistent_A,
            plan_execution_consistent_B, delayed_task_success,
            delayed_plan_valid, delayed_first_action_correct,
            delayed_plan_execution_consistent}:
    count(e, AUTH_RECURRENT) - count(e, ATOMS_RECURRENT) >= 0

G8 BEST_TEXT (optional)
  for e in {two_goal_task_success, delayed_task_success}:
    sum_k [b_e(k,AUTH_RECURRENT)
           - max(b_e(k,RAW_CONTEXT_RECURRENT),
                 b_e(k,RAG_RAW_RECURRENT))] >= 1
  and zero net AUTH loss to that root-wise maximum on every other endpoint
  in G7. NATIVE_GRAPH_RECURRENT is a reported ceiling and is not in the max.

G9 CARRIED_SCRATCH
  count(acquisition_success, AUTH_RECURRENT)
    - count(acquisition_success, AUTH_SCRATCH_OFF) >= 4
  count(delayed_task_success, AUTH_RECURRENT)
    - count(delayed_task_success, AUTH_SCRATCH_OFF) >= 4
  and AUTH_RECURRENT has zero net loss to AUTH_SCRATCH_OFF on every other
  mutually applicable PB, UI, DB, 2B endpoint.

G10 WITHIN_PHASE_FEEDBACK
  count(acquisition_success, AUTH_SCRATCH_OFF)
    - count(acquisition_success, AUTH_NO_FEEDBACK_TAPE) >= 4
  count(delayed_task_success, AUTH_SCRATCH_OFF)
    - count(delayed_task_success, AUTH_NO_FEEDBACK_TAPE) >= 4
  and AUTH_SCRATCH_OFF has zero net loss to AUTH_NO_FEEDBACK_TAPE on every
  other mutually applicable PB, UI, DB, 2B endpoint.
```

`G9` supports only explicit carried structured scratch under recurrent
feedback. `G10` includes repeated interaction and within-phase public outcome
feedback; it is not pure recurrence, DREAM recurrence, or U-to-D retention.
No optional or other-endpoint success compensates for a failed named gate.

### 5.3 Clause-to-gate and withdrawal matrix

| Claim clause | Exact gate | Complete valid miss | Integrity/missing evidence | Forbidden interpretation |
|---|---|---|---|---|
| Supplied connected memory supported two goal-dependent route constructions. | `G0 & G1(two-goal) & G2 & G5 & G7`; report AUTH constructive-use and bridge/twin numerators. | Withdraw connected-memory specificity and the combined maximum statement; retain exact task/intervention counts as bounded negative or mixed evidence. | `INVALID`/`INCOMPLETE`; no scientific clause. | No DREAM authorship, spontaneous connection creation, or general composition claim. |
| Calibrated public evidence supported separating choice and belief revision. | `G0 & G3`, using only public-calibration U endpoints. | Withdraw only calibration plus the combined maximum statement; it neither rescues nor defeats path evidence. | `INVALID`/`INCOMPLETE`; no calibration clause. | Do not call calibration DREAM, memory causality, learning, or U-to-D retention. |
| A supplied old-plus-new carrier supported delayed task completion and connected integration after sterile reset. | `G0 & G1(delayed) & G4 & G6 & applicable G7`, including exact reset/entry/descendant receipts. | Withdraw delayed-carrier specificity and the combined maximum statement. | `INVALID`/`INCOMPLETE`; no delayed clause. | Even on pass, no retention, acquisition-to-use, self-write, or online learning. |
| AUTH practically outperformed the strongest honest unstructured textual-memory baseline. | All mandatory gates needed by the named endpoint plus `G8` and complete per-arm resource receipts. | Withdraw practical-superiority and efficiency language only; RAW/RAG success is an honest alternative. | Invalid comparison; no practical claim. | It neither rescues nor defeats core mechanism clauses by itself. |
| Carried structured scratch improved behavior. | `G0 & G9`, exact same endpoints and zero-net contrasts. | Withdraw carried-scratch benefit only. | Invalid comparison; no scratch claim. | No recurrence necessity, persistence, SLEEP, retention, or learning. |
| Closed-loop within-phase feedback improved behavior. | `G0 & G10`, exact terminal and resource receipts. | Withdraw feedback-benefit language only. | Invalid comparison; no feedback claim. | A pass is not pure recurrence and proves no U-to-D retention. |

A semantic, source, producer/query/scorer, local-edge, provenance, render,
handoff, reset, session, CAS, receipt, applicability, or resource-integrity
breach is `INVALID`, not zero. Missing/duplicate/nonterminal evidence is
`INCOMPLETE`, not zero. A complete valid gate miss is retained negative
evidence and is never dropped, rerun, reserve-replaced, or compensated. A
shortcut breach is a specificity failure, never a baseline result to average
away. `NA`, zero, and `NOT_REACHED` remain disjoint.

The following remain unconditionally withdrawn: DREAM connection authorship
or re-expression, SLEEP validation, LoRA storage/transport, model-authored
persistent write, retention, acquisition-to-delayed use, online learning,
continued-life improvement, accumulation, compression, parenting,
recall/composition/planning decomposition, topology/model/population
generalization, longitudinal plateau, baseline saturation, and complete-
organism or flywheel behavior.

Only if all three mandatory rows pass may a later independent claim review
consider this maximum wording:

> In one fixed finite topology under one exact frozen text policy, supplied
> grounded atom-plus-connection memory supported two goal-dependent route
> constructions under registered connection and binding interventions;
> separately, calibrated public evidence supported separating choice and
> belief revision; and a model-independent supplied old-plus-new carrier
> supported delayed task completion and connected integration after sterile
> reset.

Optional practical, scratch, and feedback sentences require their own rows.

## 6. Required future evidence bundle

A later, separately authorized source proposal can close these five V9 items
only by providing, before the indicated boundary:

```text
RegistryClosureReceiptV1                 before implementation
AlgebraPriorReceiptV1                    before model execution
LocalEdgeNoPreassembledPathReceiptV1     before model execution
AbandonedBranchNonreleaseReceiptV1       before model execution
RepeatStatePolicyVisibilityReceiptV1     before model execution
PromptProtocolSchemaCrossproductReceiptV1 before model execution
EndpointApplicabilityReceiptV1           before reduction
ClauseDispositionReceiptV1               before scientific claim
```

Every receipt binds source-manifest hash, test-spec hash, checker identities,
complete fixture-ID set, per-fixture verdicts, and artifact hashes. Acceptance
requires all positive fixtures accepted, all negative/mutation fixtures
rejected for the registered reason, two-checker agreement where required, and
no missing fixture. This advisory itself creates none of those receipts.

## 7. Source basis and authority boundary

This repair is derived from the following exact source bytes:

| Source | SHA-256 |
|---|---|
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v9/consensus.json` | `9e2066e1782a627e3fab15e179f1e15c33dc829b51076dbdd52556c5053176cf` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v9/critique.json` | `e92e461fe8e37ed22353ffdefe0929afb98e1d59bb62643d138093a95ffbd4a5` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v9/change.json` | `bada525623c094914e41c60048a2e4714e1912c1202e5e889b2bf28f9992a0fc` |
| `research_loop/plans/pcfl_m0_mtext_exact_v9_source_authoring_candidate.md` | `8a47d30909e0e171fe6dc1d6f92640fb7ed6d2bdab6642cabe57f91a5d549f59` |
| `research_loop/advisory/20260910_pcfl_v4_governance_packet_audit_v1.md` | `0b11febe8abadc4d2c9bddfdf87ad269d5fb209e438e83352153a18d9c891a7c` |
| `research_loop/advisory/20260910_pcfl_v5_authority_handoff_delayed_v7_source_repair_v1.md` | `ae74fae9516fba5a699514674fd2299ec3130eca7814be723ccc5717258fcb2a` |
| `research_loop/advisory/20260910_pcfl_v5_endpoints_claims_exact_repair_v1.md` | `bfc4ae363a47f9825193e0783ef6d5f9f84b4741a6c73a3effad1d9140ea9ec4` |
| `research_loop/advisory/20260910_pcfl_v5_provenance_resource_repair_v1.md` | `96b3dcd1b60f484ae1983a91f00fd5abfe60fadf297876d837cfd32eb830b504` |
| `research_loop/advisory/20260910_pcfl_v5_packet_preflight_fresh_audit_v1.md` | `c85ab9b83e849b84353653611c97596dd4001b257a0423c8f30bdfef07ba9005` |
| `research_loop/advisory/20260910_pcfl_v6_baseline_projection_preflight_repair_v1.md` | `12960868a1cafb820e33600482866a6387538280e8baeb698d59c8a4072d44ee` |
| `research_loop/advisory/20260910_pcfl_v6_packet_preflight_fresh_audit_v1.md` | `69910384ead946bfb407eda8d79963c3e98918f5873be6b09b339483d65924f6` |
| `research_loop/advisory/20260910_pcfl_v7_baseline_projection_exact_closure_v1.md` | `6ca612e41e3462ca6997cabcd089439a8d24be06ca7d37b5e29183ec362dd272` |
| `research_loop/advisory/20260910_pcfl_v7_packet_preflight_fresh_audit_v1.md` | `88a1deeb8c2ecaef1370c7206b35419cccadb114c280feffcf84faa15f513ec6` |
| `research_loop/advisory/20260910_pcfl_v8_repeat_null_exact_closure_v1.md` | `5c5321a7d208830a4f1c2fd5b04669ca56207e6403d57a68483954fe2057d597` |
| `research_loop/advisory/20260910_pcfl_v8_packet_preflight_fresh_audit_v1.md` | `e755fe6474f4a8303b96eb7a2073890507d492acc932e68e1b74b067a2c25828` |
| `research_loop/advisory/20260910_pcfl_v9_binding_boundary_exact_closure_v1.md` | `a430f512c7bb987dd959be7a97edd6b83c58c4b205bdb32f9ad63697cd1a972d` |
| `research_loop/advisory/20260910_pcfl_v9_packet_preflight_fresh_audit_v1.md` | `418ffad01c6016ca1388f1bd8eac4d75c192feb113b3439d66219753b2e1e403` |

A citation is not an execution grant.

This file is advisory text only. It does not authorize source-plan rewriting,
preparation-source authoring, implementation, deterministic materialization,
fixture/root/data generation, benchmark/model/tokenizer execution, training,
LoRA/adapter/checkpoint work, parenting, GPU use, resource acquisition,
scientific execution, claim, release, or submission.

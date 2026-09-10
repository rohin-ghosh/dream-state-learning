# One-parent/one-child strong-baseline byte re-audit v2

Date: 2026-09-06

Status: fresh independent read-only re-audit of the second repaired candidate.
This advisory changes no candidate bytes and authorizes no implementation,
model/tokenizer call, benchmark, adapter operation, GPU use, or scientific
claim.

## Verdict

**REVISE.** The second repair closes the earlier raw-event/actor-render gap,
closes the 960 live-record embedding bound, and gives the retrospective LEAFE
branch an adequate prospective historical snapshot. Its call, token, query,
and fit arithmetic also remains correct. The candidate still cannot earn the
word **strong**, however, because the model-visible schema is not the complete
protocol the prompt says it is, the advertised total semantic recomputation
has undefined or multiply legal cases, and the certificate cannot assign all
of its stated gold units and malformed-output denominators mechanically. Two
narrow index/link rules also remain unclosed.

## Requested checks

1. **Exact prompt bytes and dynamic renders — BYTE LAYOUT PASS; VISIBLE
   PROTOCOL REVISE.**

   - `active_text_fixed_prompt_schema_v1.txt` is 3,737 bytes and ends in
     exactly one U+000A. The declared system message and both completed user
     messages have no terminal newline.
   - The concatenations are deterministic. Because every nonempty JSONL item
     already ends in U+000A and the following section literal begins with
     U+000A, a nonempty JSONL section deliberately leaves one blank line before
     the next header; `(empty)` leaves none. The contract is exact about this
     distinction. Dynamic values have closed JSON object shapes and ordinary
     JSON escaping, and complete objects are not escaped a second time.
   - The visible schema is nevertheless not the complete callable protocol
     asserted in Section 6. It omits the `PUBLIC_CAUSAL_EVENT` and event-block
     field laws, all per-kind evidence recomputation rules, median/tie laws,
     the calibration threshold, and the canonical JSON key-order/escaping
     rules. The updater has no repository access, so it cannot infer those
     rejection rules. The displayed return objects also begin
     `schema_version, program_event_id, ...`, whereas Section 1 requires every
     protocol object's keys to be lexicographically sorted. Either model
     output is parsed and canonicalized before byte validation—in which case
     that boundary must be stated—or the visible examples/instructions are
     incompatible with the canonical-byte rule.

2. **Raw event-block retrieval and actor insertion — PASS, subject to the
   stale-link blocker below.** A block now has an exact closed shape, ID,
   eligibility boundary, size cap, lexical-only index role, and complete-item
   packing rule. The actor renderer accepts both canonical live records and
   canonical event blocks inside one exact three-line wrapper, so the old
   records-only insertion contradiction is gone. Updater-side prior retrieval
   uses the same document types coherently.

3. **Total semantic recomputation and certificate denominator — REVISE.**
   The new text is substantially stronger, but it is not total or uniquely
   executable:

   - `PROVISIONAL` and `CONTRADICTED` records have no positive-support minimum.
     A legal nonempty evidence union can therefore have zero support events,
     while scope derivation, modal outcome, medians, and paired comparisons
     are defined from support. Several proposition kinds then have no result.
   - `SCORE_EFFECT` first says a positive median deterministically yields
     `POSITIVE`, then also permits `NONNEGATIVE` whenever all deltas are
     nonnegative and one is positive. Such evidence can satisfy both rules, so
     relation is not unique.
   - The new block-observation rule now closes action-to-outcome/score and
     within-block prediction linking. It does not define how two distinct
     blocks are paired when multiple subject/object blocks share a starting
     state for `ACTION_CONTRAST`, or how blocks are grouped into the sequences
     required by `PROCESS_ASSOCIATION`. Moreover, the generic counterevidence
     rule says every counterevidence event matches the subject family, which
     is incompatible with a contrast counter-pair containing the object
     family.
   - Status is constrained by a transition table but not derived. For example,
     an otherwise identical two-support `ADD` may legally be `PROVISIONAL` or
     `SUPPORTED`. `REFLECT.kind` is likewise not mechanically mapped from the
     evidence. The certificate nonetheless requires status/operation units to
     equal a mechanically recomputed gold unit.
   - A nonempty malformed response contributes one false unit of its
     "attempted operation class", but no rule assigns a class when the JSON or
     `op` is unparseable, or resolves a malformed response that appears to
     attempt multiple classes. Consequently that denominator is not defined
     for every possible sealed output.

   Missing guidance, `NOOP`-dropped `REFLECT` items, empty outputs, duplicates,
   zero emitted-class denominators, and false negatives are now handled
   correctly. Those repairs pass once the underlying gold-unit and malformed-
   class functions are made total.

4. **Stored-record and dense-embedding ceiling — PASS.** Stored support,
   counterevidence, link, scope, and complete-record sizes are bounded, and an
   oversize transition fails atomically. `ADD`, `REVISE`, and `LINK` each
   embed at most one live record. `SUPERSEDE` removes the old document without
   embedding a tombstone and embeds only its replacement. The per-call
   one-mutation-per-memory rule, four-delta ceiling, transaction/no-retry law,
   and 240 update points therefore justify at most `240*4 = 960` newly embedded
   or re-embedded live records/root.

5. **LEAFE historical visibility and budgets — PASS.** Before live `P0`
   advances, every candidate branch point seals checkpoint, rendered
   context/ledger prefix, environment, active store and both indices, query
   fields, clock/budget, RNG counters, and source/config hashes. The later
   selector loads only the earliest eligible snapshot, so diagnosis,
   recovery, rollback, and retrieval cannot see later `P0` events or terminal
   memory. Snapshot creation is read-only with respect to the live service.

   The optional arithmetic recalculates:

   ```text
   input: 48*(8,192+4,096) = 589,824
   returned memory: 48*1,024 + 48*768 + 64*1,024 = 151,552
   queries: 48 + 48 + 64 = 160
   calls/output: 160 / 45,056
   added fits: 1/root
   N=20: 141,726 calls; 26,457,600 output; 356 fits incl. canary
   N=32: 207,138 calls; 38,668,800 output; 512 fits incl. canary
   ```

   It remains descriptive-only, begins after immutable headline artifacts,
   and is absent from root selection and powered claims. The main 5,291-call,
   972,544-output, 4,400-query, 7,208,960 active-input, and 12-fit/root ceilings
   also recalculate.

6. **One-parent topology — PASS.** Exactly one frozen parent has one closed
   childhood correction edge to the parented child and no post-deletion edge.
   `U` is an isolated counterfactual branch; `R0` is a fit-free replication;
   services and roots share no store. The active-text updater, optional
   comparator, and statistical replications introduce no classroom, peer,
   ensemble, or population-learning edge. The scope proposal preserves these
   restrictions and remains proposal/CPU-only after any later exact
   ratification.

## Exact blockers

1. **Bind the actual model-visible protocol.** Put the canonical-output rule,
   public event/block schemas, complete per-kind evidence/status laws, and all
   required frozen parameters into the exact prompt bytes, or define an exact
   source-bound instruction payload that is inserted on every call. Align the
   displayed output ordering with the parser/canonicalizer boundary.
2. **Make semantic recomputation total and single-valued.** Define minimum
   support for every kind/status; remove the `POSITIVE`/`NONNEGATIVE` overlap;
   define cross-block tuple construction for contrast and process evidence;
   reconcile the counterevidence-family rule; and derive `REFLECT.kind` and
   record status uniquely from public bytes and prior state.
3. **Finish the certificate function.** Define gold operation/status units
   from the repaired total merger and map every nonempty malformed byte string
   to an exact false-unit class/count, including unparseable and multi-attempt
   outputs. Then regenerate the prospective certificate fixtures rather than
   interpreting the current cases after scoring.
4. **Close superseded-link expansion and BM25 mutation accounting.** A source
   can legally link to a live target that is later superseded. Current one-hop
   expansion does not say to filter, redirect, or reject that stale link, so it
   can conflict with "only current ... not SUPERSEDED are searchable." Also,
   one `SUPERSEDE` removes one BM25 document and inserts a different-ID
   document. If physical insert/delete operations are what "BM25 index
   mutations" means, four supersessions are eight operations/program and
   1,920/root, not 960. Define a live-target filter/redirect law and separately
   bound replacements, inserts, and removals (the 960 dense-embedding ceiling
   itself does not change).

## Nonblocking findings

- The query sanitizer now applies NFKC before newline/delimiter replacement;
  the earlier compatibility-character escape is closed.
- Complete raw event blocks are bounded and lexical-only, so they add no
  uncounted dense document embeddings.
- Snapshot storage/index bytes are receipted but not given a hard byte ceiling.
  This does not change the stated call/token/fit arithmetic, but the later
  implementation resource manifest should bind a storage ceiling if it calls
  itself all-in.
- `R0` remains correctly described as a frozen-parameter active-memory
  reference, and no optional-comparator result is promoted to a named-method
  or powered superiority claim.

## Disposition

Do not promote `ACTIVE_TEXT_FIXED` as a validated strong baseline and do not
spend scientific roots from these bytes. Repair the four narrow contract
edges, regenerate hashes and fresh sealed certificate cases, and obtain a new
source-bound independent approval. No topology, headline estimand, root-count
rule, or LEAFE schedule change is required.

## Audited current hashes

- `AGENTS.md`: `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e`
- headline plan: `fd9234f66c657f62dff8ad0c29efe52d432511d52fd3f2635da5e2e9d6b4b386`
- active-text contract: `3650e09fce098db77bc942ab7b92e8b9106865f78b459c849ce0e1065d855dcf`
- model-visible prompt schema: `b2fb9fc90392faa5fee8d2533e456c91bec17ba7ba2a5408b7279ae34ced8631`
- scope proposal: `466319fa741a583f2cb9cf1dd6e01fd255877feae5818ea7697e3fab1e17dc75`
- prior integrated audit: `2e787b059992d0861f0d71d3f4924a3c8e0a355373f6d7573365683f8c9fc0d8`
- prior repair re-audit: `15950409c9c65e268f3314971fa9841d3ff7f189b9203054b7ac87076c5635c0`

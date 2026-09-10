# PCFL V4 minimal-science adjudication — fresh v1

Date: 2026-09-10

Status: **source-only adjudication recommendation; REWORK; not ratified and
not executable**. This document authorizes no implementation, preparation
source creation, materialization, fixture generation, CPU benchmark run,
model/tokenizer call, GPU use, training, adapter/checkpoint operation, claim,
release, or submission.

## 0. Decision

Build one integrated `PCFL_M0_THIN_V4` source contract and one separately
gated `PCFL_MTEXT_SUPPLIED_V4` contract. Do not treat the three V3 repair
advisories as an amendment stack.

The smallest scientifically valid selection is:

- clean-room M0 with zero FeltCraft V7 runtime reuse;
- all 64 `(k,h)` roots as a Boolean CPU engineering census;
- an 18-condition M-TEXT roster, deleting model-executed `TRUTHFUL_NULL`;
- an eight-read forward bundled reader with a first-action read cut;
- substrate-neutral task endpoints separated from carrier-specific trace
  diagnostics;
- a supplied, model-independent delayed-entry checkpoint, so acquisition and
  delayed use are separate factorial assays and no retention claim is made;
- exact finite-census rates with no sampling uncertainty;
- the balanced explicit 16/32/16 root split below;
- per-file CAS and immutable reference receipts; and
- a human-ratified two-freeze exception: source first, actual bytes second.

This resolves the reviewed source conflicts, but it is not itself the exact
patch/source bundle required for ratification. The next artifact must contain
the consolidated V4 schemas, tables, inert preparation patch bytes, hashes,
and tests.

## 1. M0 V4 contract selected

V4 must version-separate every public and hash identity from V3. Use wire
`v:4`, instrument `PCFL_M0_THIN_V4`, and `...-v4\0` hash domains. A V3 object
must fail under a V4 loader.

Retain the 64-root algebra, two goal paths, bridge, target/nuisance experiment
construction, provenance rules, raw-versus-credited outcomes, and isolated
forks. Amend M0 itself—not a later renderer—with all of the following:

1. checker-only semantic IDs and fixed public handles `a00..a19` and
   `l00..l06` are separate types; semantic/root/support hashes never enter an
   actor projection or dependency;
2. the fixed path `action_catalog` is all sixteen relation aliases plus
   `finish` and `abstain`; it is not a legality oracle;
3. a catalogued non-outgoing relation is a charged, evidence-false
   `NO_EFFECT`; premature `FINISH` is ordinary `WRONG_FINISH`; neither
   invalidates the instrument;
4. path and delayed phases have eight reads, four relation attempts, and one
   uncharged terminal opportunity; the first relation attempt, including
   `NO_EFFECT`, closes the reader;
5. use `c0/c1`, `finish`, and `abstain` consistently in schemas, prompts,
   parsers, goldens, and receipts;
6. add the `NO_PERSIST_NEW` transform to M0 fixtures and conformance tests;
7. give SYNTH proposals a total logical coordinate that places old proposals
   after event 24/before 25 and new proposals after 41/before 42; and
8. freeze a checkpoint DAG; controls never serialize through a sibling's
   model trajectory.

`HandoffPublicV4` is the immutable semantic payload. A private
`MTextHandoffV4` names its digest and exact M0 freeze ID plus routing and
renderer bindings. Only the verified public projection reaches the reader or
renderer. Static phase starts are frozen inputs; model-dependent views and
call handoffs are dynamic content-addressed receipts, not pre-materialized
goldens.

## 2. Exact eight-read reader

`MemoryReturnV4` has one typed atom slot, one typed link slot, an explicit
sorted `grants` set, and a fixed outer size. `grants` is the sole way an atom
or link becomes a capability. Node aliases merely printed inside a returned
row do not become READ anchors.

The pure reader may inspect only `(carrier, anchor, cursor, reader_open,
repeat_state)`:

- `NODE(n)`: select incident non-null STEP atoms in public atom-handle order;
  return one atom and grant only its handle.
- `ATOM(a)`: select readable AUTH links with `left==a` in public link-handle
  order; bundle the selected link and its right-endpoint atom and grant both.
- `LINK(l)`: cursor 0 or 1 bundles the link with its selected endpoint atom;
  other cursors are `NOT_FOUND`.
- absent candidates are fixed-size `NOT_FOUND`; after the read cut they are
  fixed-size `BLOCKED`; `REACHOUT_OFF` blocks ATOM/LINK dispatch without
  index access.

Starting with either `p0` or `p2`, a complete four-edge goal path needs at
most five reads: one `NODE(S)`, one next-edge bundle, one bridge bundle, and
at most two terminal bundles at `p4`. The eight-read budget therefore has
three spare reads. Exhaustive goldens must prove this for both goals, all 64
roots, both probe orders, every handle rotation, and every intervention.

In `ATOMS`, start/target NODE reads cannot grant `p1`, `p3`, `p4`, or any
link; printed node fields grant nothing; and the first world attempt closes
reads. Exhaustive capability closure must prove that ATOMS cannot crawl.

The repeat fingerprint/count/block state remains public: first dispatch,
one idempotent replay, third identical non-progressing command blocked; every
fork/reset clears it.

## 3. Truthful null disposed

Delete `TRUTHFUL_NULL_RECURRENT` from M-TEXT. It is scientifically redundant
and its V3 endpoint-preserving form leaks authentic adjacency.

M0 may retain only a conformance-only explicit-empty response. For every
legal ATOM anchor, cursor zero returns the same query-local `EMPTY` sentinel:
null handle, null endpoints, no semantic ID, no evidence, no grants; higher
cursors return `NOT_FOUND`. It is independent of authentic degree, cannot be
cited, and cannot be a LINK anchor. It has the same fixed outer response size
as other reader outcomes. It is not an M-TEXT condition and adds no model
calls.

## 4. Exact M-TEXT condition and phase roster

Let `P=A+B` (26 recurrent request slots), `U=uncertainty/acquisition` (4), and
`D=delayed` (13). The exact 18 conditions are:

| MTextCondition | Phases | Maximum slots/root |
|---|---:|---:|
| `AUTH_RECURRENT` | P+U+D | 43 |
| `ATOMS_RECURRENT` | P+D | 39 |
| `DERANGED_RECURRENT` | P+D | 39 |
| `BRIDGE_CUT_RECURRENT` | P | 26 |
| `TWIN_REDIRECT_RECURRENT` | P | 26 |
| `UNCERTAINTY_SHAM_RECURRENT` | U | 4 |
| `REACHOUT_OFF_RECURRENT` | P+D | 39 |
| `OLD_CUT_RECURRENT` | D | 13 |
| `NEW_CUT_RECURRENT` | D | 13 |
| `NO_PERSIST_NEW_RECURRENT` | D | 13 |
| `NO_MEMORY_RECURRENT` | P+D | 39 |
| `TARGET_ONLY_ANSWER_PRIOR_TAPE` | four phase calls | 4 |
| `PASSIVE_SIGNATURE_RECURRENT` | P+D | 39 |
| `RAW_CONTEXT_RECURRENT` | P+D | 39 |
| `RAG_RAW_RECURRENT` | P+D | 39 |
| `NATIVE_GRAPH_RECURRENT` | P+D | 39 |
| `AUTH_SCRATCH_OFF` | P+U+D | 43 |
| `AUTH_NO_FEEDBACK_TAPE` | four phase calls | 4 |

Unexecuted phase fields are `NA`, never zero or inherited model outcomes.
`M0ConformanceCell`, `MTextCondition`, and `MTextCheckpoint` are disjoint
types and manifests; there is no positional `x19` handoff array.

## 5. Delayed-entry semantics selected

Use one model-independent `DELAYED_ENTRY(k,h)` fixture per root, derived from
the frozen public old evidence plus a correctly admitted supplied new fact.
Every D phase is an isolated fork of that same entry. `OLD_CUT`, `NEW_CUT`,
and `NO_PERSIST_NEW` are applied only at that fork. `AUTH` D does not consume
the model's U output, even when both appear under the same condition label.

This factorial choice is why the smaller roster is valid. It also fixes the
claim boundary:

- U measures experiment choice, public-outcome use, revision, and commit;
- D measures use of a supplied persistent old-plus-new carrier after reset;
- no endpoint joins U success to D success;
- no result is called retention, online acquisition-to-use, or a learned
  write; and
- abbreviated D conditions mark acquisition and retention fields `NA`.

At D reset, carrier arms destroy messages, scratch, plans, beliefs, raw
events, calls, returns, workspaces, capabilities, repeat state, joins,
sessions, KV/prefix/application caches, filenames, timing, ordering, errors,
and condition metadata. Only the immutable root and condition-appropriate
carrier remain. Raw-context, RAG, and native-graph arms retain their declared
alternative external memory and are expressly excluded from the carrier
sole-channel conclusion.

## 6. Endpoints and reduction

Every endpoint is `0|1|NA`, with a frozen phase-applicability matrix.

Substrate-neutral endpoints, used for every baseline and shortcut contrast,
are `task_A`, `task_B`, `plan_A`, `plan_B`,
`two_goal_task_success=task_A & task_B`, and `delayed_task_success`. They
depend on public state/action behavior, not possession of an AUTH citation.

Carrier-mechanism diagnostics are separate: probe-local returned-atom/link
access, public-ID reuse, `constructive_A/B`, `connected_constructive_use`,
and `delayed_connected_use`. They are scored only where their substrate is
defined and never make ATOMS, no-memory, raw, or RAG lose by construction.

Cross-condition quantities are derived block endpoints, not fields inside
AUTH:

- `connected_policy_dependence`: AUTH succeeds constructively, bridge cut
  changes task behavior, and twin redirect produces the registered
  content-correct terminal switch;
- `delayed_carrier_dependence`: AUTH D succeeds while each old cut, new cut,
  and no-persist intervention changes/fails delayed task behavior; and
- `best_text_delta(e)`: with `b_e(k,c)=min_h e(k,h,c)`, compare AUTH to
  `max(b_e(k,RAW_CONTEXT),b_e(k,RAG_RAW))` root by root. Native graph is a
  ceiling, not part of this max.

Information endpoints remain separate: `separating_choice`,
`realized_information`, `belief_revision`, `raw_acquisition`, and
`acquisition_credit`. Chance-correct sham commits remain raw successes but
receive zero credit when target information/revision is absent.

The DEV headroom gate is AUTH `two_goal_task_success` and
`delayed_task_success >=6/8`, with NO_MEMORY `<=4/8` on both. Confirmation is
the following AND, using the sixteen twin blocks:

- AUTH two-goal and delayed task success are each at least `12/16`;
- AUTH exceeds ATOMS, DERANGED, BRIDGE_CUT, and REACHOUT_OFF by at least
  `4/16` on two-goal task success;
- AUTH connected constructive use and derived connected-policy dependence
  are each at least `12/16`;
- OLD_CUT, NEW_CUT, and NO_PERSIST_NEW delayed task success are each at most
  `4/16`, and AUTH exceeds each by at least `8/16`;
- NO_MEMORY, TARGET_ONLY, and PASSIVE_SIGNATURE are each at most `5/16` on
  every applicable task endpoint;
- AUTH separating choice, realized information, belief revision, and
  acquisition credit are each at least `12/16`; SHAM realized information,
  belief revision, and acquisition credit are each at most `4/16`, with an
  AUTH acquisition-credit advantage of at least `8/16`; and
- AUTH has zero net lost block versus ATOMS on substrate-neutral task and
  plan endpoints.

The written `-0.05` adverse rule is exactly **zero net lost block** on this
16-block lattice and must be implemented as an integer sum `>=0`, not as a
five-point tolerance.

## 7. Recurrence controls disposed

`AUTH_SCRATCH_OFF` is the matched explicit-state ablation: same successive
public outcomes and recurrent calls, but empty `prior_scratch` and ignored
prior belief/plan. An AUTH advantage can support only an explicit carried-
scratch benefit.

`AUTH_NO_FEEDBACK_TAPE` is renamed from `AUTH_ONE_SHOT_TAPE`. It is one call
per phase, generated before any within-phase outcome. Its typed U tape may
name an experiment followed by one fixed `c0/c1/abstain`, with controller
stage validation; future returned handles may not appear in dependencies.
It is an open-loop lower bound for feedback, not an equal-interface scratch
or recurrence ablation.

Both tapes receive the same maximum generated-token opportunity as their
recurrent phases, but input tokens, schema overhead, calls, feedback, latency,
and compute are intentionally unequal and must be reported. Report separate
`carried_scratch_benefit` and `closed_loop_feedback_benefit`; do not make a
single “recurrence necessity” claim from their conjunction. Either optional
benefit requires an AUTH advantage of at least `4/16` over its named control
on both acquisition credit and delayed task success, with zero net loss on
two-goal task success.

## 8. Uncertainty claim

The public `Uncertainty` table exposes candidate counts directly, so its U
assay does not identify connected-memory use. Keep it because it cleanly tests
separating choice, use of an ordinary public outcome, revision, and commit
against `UNCERTAINTY_SHAM`. Describe it only as use of calibrated public
evidence. Do not attach it to the connected-row mechanism or delayed carrier
chain.

## 9. Sizes and rendered boundary

Discard the V3 131,072-byte `FiniteView` and 262,144-byte rendered-handoff
assumption. For every V4 public type, source preparation computes the smallest
256-byte multiple that contains the exhaustive maximum canonical unpadded
record. The resulting numeric bounds and goldens must be present at the
second byte freeze; no renderer may choose them later.

Hard source caps are: row `<=2,048` bytes, `MemoryReturn<=4,096`,
`GoalsComplete<=12,288`, `FiniteView<=16,384`, carrier `<=32,768`, and
`HandoffPublic<=65,536`. `HandoffPublic` is not rendered wholesale. If the
no-choice derivation exceeds a cap, preparation fails and the source must be
redeliberated.

Every fully rendered model call, including raw and native baselines, must
have at most 65,536 input UTF-8 bytes, 8,192 input tokens, and 16,384 total
input-plus-allowed-output tokens, with no truncation. Recurrent decoded output
is at most 2,048 bytes/256 tokens. One-shot path output is at most 26,624
bytes/3,328 tokens; one-shot U output is at most 8,192 bytes/1,024 tokens.

Matched carrier contrasts must have equal schema, record/slot count, UTF-8
bytes, frozen-tokenizer token count, request slots, read/action opportunity,
and output ceilings. Token IDs should differ because content is the
intervention. Equality must be exhaustively certified, not achieved by
performance-guided padding search.

## 10. Split and uncertainty

Freeze this balanced algebraic split before any rendering:

```text
DEV k:          0, 6, 8, 14, 17, 23, 25, 31
CONFIRMATION k: 1, 3, 5, 7, 9, 11, 13, 15,
                16, 18, 20, 22, 24, 26, 28, 30
RESERVE k:      2, 4, 10, 12, 19, 21, 27, 29
```

Both `h` twins stay together. M0 checks all 64 roots; M-TEXT has 8 DEV, 16
confirmation, and 8 reserve presentation blocks. DEV is protocol selection,
confirmation is one frozen-model/one-topology finite census, and reserve is
only a post-confirmation robustness follow-up under new authority—not a
replacement replication.

Scientific uncertainty is `none`: report exact numerators, denominators, and
paired differences. No p-values, confidence intervals, bootstrap, standard
errors, multiplicity correction, or population/topology-generalization
language is permitted.

## 11. CAS, authority, and two freezes

Select zero V7 runtime reuse and the authority repair's per-file CAS. The V7
reuse manifest is exactly `{"v":1,"dependency":"FELTCRAFT_SYMBOLIC_KERNEL_V7","reused_primitives":[]}`.

The V4 CAS manifest is a closed governance object:

```text
{v:4, kind:"PCFL_M0_CAS_MANIFEST",
 entries:[{path:NFC-relative-path,size:u64,sha256:hex64}, ...]}
```

It contains no self root. Entries are unique and sorted by raw UTF-8 path.
Each root row is `u32be(path_byte_length) || path_utf8 || u64be(size) ||
sha256_raw32`; the manifest root is SHA-256 of
`"PCFL-M0-MANIFEST-v4\0"` plus the concatenated rows. Payload objects live at
`objects/sha256/<2>/<62>`; the JCS+LF manifest lives at its root-named path.
No overwrite, symlink, mutable latest/current pointer, directory promotion,
or result-based retry has authority.

Avoid ratification self-reference: compute `pre_authority_root` from frozen
spec/source/schema/runtime/governance inputs excluding human ratification;
the human preparation object names that root and scope; then compute
`preparation_input_root` from the pre-authority root plus ratification hash.

Adopt the two-freeze exception explicitly:

1. human ratifies exact inert preparation/materializer/two-checker source,
   runtime, paths, limits, and zero-choice CPU execution;
2. deterministic no-RNG/no-search preparation produces candidate CAS bytes;
3. disjoint constructive and axiomatic checkers plus mutations run;
4. pre/post hashes and a terminal candidate receipt freeze the attempt;
5. fresh review examines exact source and output; and
6. a second human decision freezes the exact manifest/reference receipt.

Only then may a separate M0 implementation change consume that freeze ID.
M0 CPU passage remains `DEV_NONCLAIM`; H0/M-TEXT, DEV, confirmation, and a
claim each require later exact gates.

## 12. Resource ledger and arithmetic

Under the 18-condition phase roster:

```text
maximum request slots/root
  = 2*43 + 8*39 + 2*26 + 1*4 + 3*13 + 2*4
  = 501

allowed generated tokens/root
  = 2*11,008 + 8*9,984 + 2*6,656 + 1*1,024
    + 3*3,328 + 2*11,008
  = 148,224

48 DEV+confirmation roots: 24,048 slots; 7,114,752 tokens
+ 24 deterministic sentinels: 24,072 slots; 7,120,896 tokens
maximum input-token envelope: 24,072 * 8,192 = 197,197,824
```

These are slots/ceilings, not promised emitted calls. Every unissued suffix is
sealed `NOT_REACHED`; actual emitted/completed/failed calls and actual tokens
are reported separately. No timing probe exists outside the 24 sentinels.

Require physical A40-class hardware rather than an undefined “A40
equivalent”: at most eight concurrently and 192 actual A40 GPU-hours across
DEV plus confirmation. Use separately paused active-execution clocks of at
most 16 hours for DEV and 32 hours for confirmation; review and human-
approval latency is outside those clocks. Retain 500 GiB artifact and USD
0.00 external-spend ceilings. Any ceiling hit yields `INCOMPLETE`; no root or
condition is pruned, replaced, or retried.

For every arm report stored bytes/tokens by substrate, index/materializer CPU
and RSS, model slots/emissions/failures, input/allowed/actual output tokens,
reader calls/returns, world actions, GPU-seconds, wall time, peak host/device
memory, artifact bytes, and spend. Claim resource matching only for the exact
matched exposure vector; raw, RAG, native, recurrent, and tape costs are
reported, not pretended equal.

## 13. Maximum claim and negative dispositions

If every corrected noncompensatory confirmation gate passes, the maximum
combined claim is:

> For one frozen 7B model on one registered finite topology, supplied
> atom-plus-authenticated-connection memory causally improved two-goal task
> behavior under paired connection interventions; calibrated public evidence
> supported separating choice and revision; and a supplied persistent
> old-plus-new carrier supported delayed task behavior after a sterile reset.

This is a within-suite conditional mechanism result. It is not DREAM/SLEEP
authorship, a learned write, retention of the model's own acquisition, online
learning, LoRA transport, accumulation, compression, parenting, lifetime
improvement, population generalization, or a flywheel.

If AUTH does not beat raw context and RAG by the registered root-wise formula,
make no practical-superiority or efficiency claim. Native graph is reported
only as a ceiling. If scratch-off matches AUTH, make no carried-scratch claim;
if no-feedback tape matches AUTH, make no closed-loop-feedback claim. Any
instrument, prefix, reset, session, oracle, CAS, or renderer failure makes the
assay invalid rather than negative. A complete confirmation miss is retained
as negative evidence; reserve cannot erase it.

## 14. Source provenance

This recommendation was formed after complete reads of the controlling files
at these SHA-256 values:

```text
AGENTS.md                                                        1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e
chg_20260910_pcfl_m0_mtext_bound_v2/consensus.json                d1eabe9da3bc4250e4ba08c458086f8e3f4f5f1e7808e4b3c6a0785243c96aa2
20260910_pcfl_m0_exact_contract_repair_fresh_v1.md                b7329f6c89253a5d627751c0135a0f1aab6caff89d5d1d12dc2eba9ef08c3297
20260910_pcfl_mtext_supplied_exact_contract_repair_fresh_v1.md    73866889087937617ad3341ea409ccf1cc9207aaded8c416e704debbe0430947
20260910_pcfl_authority_durability_exact_repair_fresh_v1.md       0bf15abd49a21ef913f5dab05ec3461ead070b9aacf87c3f267981615b67eb6e
20260910_pcfl_v3_repairs_adversarial_cross_critique_v1.md         510021974a869db77e724e16ada919e161f023c1e5d0fdfd35d43f2c406baa69
20260910_pcfl_m0_semantic_consistency_fresh_audit_v1.md           5d36fb3a6154e05b6c6143985131cbdc4417f19f7416c6c355a642db4163e704
20260910_pcfl_mtext_arithmetic_and_consistency_fresh_audit_v1.md  1208b8e2661572addcee3b7e4372f99ee38e570208f96c4ab7eaa32b18b928e4
```

Recommendation: **adopt these selections as the sole basis for a compact,
integrated V4 source proposal; do not implement or execute from this advisory.**

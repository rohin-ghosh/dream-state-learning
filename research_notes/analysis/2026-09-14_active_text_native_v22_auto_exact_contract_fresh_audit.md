# Fresh exact-contract audit: ACTIVE_TEXT_NATIVE-v2.2-AUTO

**Date:** 2026-09-14 PT  
**Role:** fresh adversarial proposal/source-readiness reviewer  
**Object:** proposal commit
`09456711ea0c2365101353bf0dd369896bdefd74`, file
`research_notes/analysis/2026-09-14_active_text_native_v22_auto_exact_contract.md`,
verified SHA-256
`f487ac47df6b6475fec2599e6b4a2badf54212840ff9bfe470d6fe54a7e9920b`.

This was a repository, contract, and integer-arithmetic audit only. I did not
edit source, materialize a root or registry, invoke a tokenizer or model, fit
or mount an adapter, inspect scientific results, or use a GPU. I did not rely
on the proposal's Section 13 self-audit as evidence.

## Verdict

**REWORK. Do not promote these exact bytes to `GO_CPU_SOURCE`.**

V2.2 successfully closes most of the v2.1 review's substantive design
problems. It root-binds evidence identities, totalizes rejected attempts,
defines task-local THINK receipts, corrects branch-local RAW parity, combines
the certificate and RS8 roots consistently, publishes a later-lifetime common
wire, includes acquisition/formation calls in the printed inference totals,
and replaces the invalid child-LINK intervention with a public-event
intervention. The named baseline is strong and scientifically honest: it is
automatic, target-blind at its declared API, branch-local, maximum-load gated,
and invalidated rather than scored as a DLT win.

The exact bytes nevertheless still leave source authors choices in five
places:

1. referenced registries/manifests do not have a total schema/type map;
2. the “exact TSJ compatibility” adapter omits the current TSJ scheduled
   `PROBE TS3P_...` action and does not totalize TSJ handle/provenance admission;
3. regex termination, Unicode normalization/lowercasing, and `math.log` depend
   on an unbound runtime, while MMR has no empty-selected-set value; and
4. the public-task projection and total P5 resource ledger remain incompletely
   closed: retrieval omits arbitrary `public_task` bytes without the v2.1
   audit's required sufficiency proof, and “Primary total” excludes the DLT
   optimizer schedule without bounding that excluded work in this contract;
   and
5. BRIDGE_EVENT's path IDs and collapsed-arc deletion bytes are not total.

These are exactness/integration repairs, not a request to redesign retrieval,
increase access, restore supplied addressing, or change the scientific claim.

```text
REWORK_ATN_V22       = TRUE
GO_CPU_SOURCE        = FALSE
GO_CPU_TEST          = FALSE_EXCEPT_NONNORMATIVE_SCRATCH
GO_MATERIALIZE       = FALSE
GO_TOKENIZER_MODEL   = FALSE
GO_GPU_OR_CLAIM      = FALSE
```

## 1. Eleven-item acceptance audit

| # | acceptance item | disposition | fresh finding |
|---:|---|---|---|
| 1 | root-salted EV/IN; inherited DOC binding | **PASS** | `root_salt` is in both EV and IN preimages; DOC hashes the resulting source ID. Branch is deliberately absent, preserving same-root paired identity. |
| 2 | total source/status/reason for every attempt | **PASS** | Full parses resolve receipt occurrences literally, rejected rows retain all successful resolutions in order, malformed/no-resolution rows use `[]`, acceptance requires distinct 1/2/8 sources, and the precedence table has a finite public vocabulary. `MODEL_INCONSISTENT` discloses no correction. |
| 3 | public transition parser and independent allow/deny goldens | **PASS** | The PCFL-L action/outcome grammar, chronology checks, null behavior, ambiguity stop, no-world-object rule, and attack roster are definite. The separate TSJ compatibility defect is item 7. |
| 4 | task-local THINK receipt IDs | **PASS** | TASK and TH preimages, call range, response hash, and kept/dropped receipt use are explicit. Call 17 cannot produce a retained THINK. |
| 5 | singular floats/tokens/PPR/MMR/packing | **REWORK, narrow** | Written binary64 operation order, summation order, Jaccard conversion, complete-row packing, and most ties are closed. The executable regex/Unicode/libm runtime is not bound, and `max_similarity` is undefined when no positive RAW row is selected but a positive interpretation row exists. |
| 6 | same RAW machinery, branch-local contents | **PASS** | Section 7.2 uses byte-identical schema/clock/query/BM25/packing/budget while expressly allowing post-fork ledger divergence. DLT/SF use their own RAW only; ATN uses its own RAW plus interpretations in one envelope. |
| 7 | one actual common PCFL-L wire plus current-interface compatibility | **REWORK, narrow** | The later-lifetime dialect is unambiguously distinct from Stage2A and TSJ and common to all three longitudinal arms. The TSJ adapter is not yet field-total, and its “one framing LF” wording disagrees with TSJ's removal of *at most* one terminal LF. |
| 8 | certificate/RS8 root overlap stated once | **PASS** | The four certificate roots are exactly the reusable/RS8 roots; DEV, PROFILE, WRITER_SCALE, CERTIFICATE_PLUS_RS8, and LIFETIME are disjoint classes. Authentic TSJ roots contribute no observation. |
| 9 | load/cut/lifetime/TSJ schemas and hashes before stage open | **REWORK** | Top-level record shapes exist, but several referenced manifests have no assigned or sufficient row schema, and several mandatory sentinel values/commitment laws are not specified. A conforming author still must invent bytes. |
| 10 | acquisition/formation and evaluation work bounded and reported | **PASS in checklist scope** | All displayed acquisition/formation and scored-evaluation generation/retrieval/input products reproduce and are summed. Separately, “Primary total” should be relabeled because the DLT optimizer schedule is excluded and unbounded in this memo. |
| 11 | prospective public-path BRIDGE_EVENT necessity | **PASS in scientific target; REWORK for byte closure** | A raw witnessed event, not child LINK, is the necessary object for this baseline. The public-only all-path/deletion proof is prospective and target-faithful. Path-ID construction and the unique-arc case for a self-loop are not exact in the manifest/graph bytes. |

Items 5, 7, 9, and the exact-byte portion of 11 are not all yes.
Under the v2.1 acceptance rule, the proposal therefore remains `REWORK`.

## 2. Smallest blocking repairs

### R1. Make every registry reference machine-total

Section 9.1 says every referenced manifest is a JCS array of “one of” eight row
shapes, but it never assigns each hash field to one row type. More importantly,
the following referenced objects have no sufficient printed row shape:

- `fork_manifest_sha256`;
- `module_manifest_sha256`;
- `exam_manifest_sha256` as distinct from a generic TASK list;
- `potential_outcome_tape_sha256`;
- `truthful_twin_manifest_sha256`;
- the opportunity **type-marginal** registry invoked in Section 9.2; and
- the opportunity-to-event/attempt/block join claimed in Section 9.2.

For example, no printed row records a module's information stratum, selected
NEW/expansion status, RS8 source status, or the MODEL-for-LINK type
substitution. OPPORTUNITY records a stage and kind but not all of those
properties. No printed row defines the action-contingent potential-outcome
tape. A future file hash makes arbitrary bytes immutable; it does not make
their semantics or schema exact.

There are also no exact empty/null encodings for the mandatory
`action_hex/outcome_hex/formation_hex` and expected-body fields in a
WIRE_GOLDEN case that exercises only one surface, no mapping from registry
`kind` to the permitted entry shape, and no formula distinguishing seed
commitments from the `root_salt_commitment`. The proposal's “no optional key”
rule makes these missing sentinels blocking rather than harmless.

Minimal repair: print a table mapping every top-level registry `kind` and every
referenced `*_sha256` field to exactly one homogeneous manifest row schema;
add only the missing FORK/MODULE/POTENTIAL_OUTCOME/TYPE_ASSIGNMENT/JOIN fields;
define mandatory null/empty encodings and all commitment preimages. Bind the
proposal SHA above as `contract_sha256`. Do not add semantic fields to files
visible to the runtime.

### R2. Finish the TSJ adapter rather than calling a partial adapter exact

The proposal correctly identifies current TSJ `STEP`, four-line
`PUBLIC_OUTCOME`, EVENT, and LINK syntax, and both cited TSJ file hashes are
correct. It misses a second current TSJ action surface. The imported TSJ-v2
formation contract, retained by TSJ-v3/v4, defines NEW formation as:

```text
PROBE TS3P_[A-Z2-7]{12}
```

with the same public four-line outcome. TSJ-v3 calls this a goal-neutral NEW
PROBE, and its exact NEW formation count includes two PROBE calls. V2.2 accepts
only `STEP` and then says every other TSJ action is rejected. Thus its boundary
cannot reproduce all authentic TSJ OLD+NEW event bodies.

The adapter also needs one explicit total rule for:

- zero versus one terminal framing LF, matching TSJ's “remove at most one”;
- root-local and unused TS3E/TS3L handles;
- root-local TS3V surface handles and whether admission consumes only the
  already-public TSJ admission result or revalidates private provenance; and
- the status/reason/source-event body emitted for every rejected TSJ EVENT or
  LINK, not only the zero/multiple tuple case.

Minimal repair: add anchored `PROBE (TS3P_...)`, verify its port against the
same outcome PORT, source only SOURCE from that outcome, and extend the golden
roster with valid/malformed NEW PROBE plus altered/unknown/duplicate
TS3E/TS3L/TS3V cases. If the adapter consumes already-admitted TSJ rows rather
than raw row attempts, say so and bind the admission receipt as an input; do
not silently consult private provenance to create an edge.

### R3. Bind the executable byte/math runtime and close empty-first MMR

The proposal uses `\z` in every new regex without naming a regex engine. The
current repository's Python 3.9 `re` rejects `\z`; current Stage2A uses
`fullmatch`, and the current TSJ contract prints `\Z`. A source author must
currently choose an engine or translate the pattern. Likewise Unicode NFKC and
lowercasing depend on the Unicode database version, while `math.log` depends on
the Python/libm runtime and is not guaranteed by IEEE-754 alone. The proposal
mentions a sealed runtime but gives no runtime/image/Unicode/libm digest field
or P1 binding rule. A finite golden roster does not cover every legal Unicode
document or every possible BM25 `(N,df)` pair.

Separately, packing defines MMR using `max_similarity` only after a preferred
positive RAW row is selected. A legal query may have positive BM25 only on an
interpretation row. The selected set is then empty and the maximum has no
defined value.

Minimal repair: use byte `fullmatch` or name and hash the regex engine; bind the
runtime image, Unicode database, JCS implementation, and libm (or a specified
correctly-rounded log implementation) before P1 promotion; and define
`max_similarity=+0.0` for an empty selected set. Add a golden with no
positive/fitting RAW row and a positive interpretation row.

### R4. Close the target-blind task projection and the excluded DLT work

The retriever receives objective, state, and accepted THINK but not
`public_task`. That can be a valid frozen projection, and it is not direct
answer leakage. However, `public_task` is otherwise arbitrary length-framed
UTF-8 visible to the actor, while the proposal supplies neither its field
schema nor the v2.1 audit's required proof that omitted bytes do not contain
the only public target identifier needed for retrieval. Future hashing alone
cannot prevent a source generator from placing a candidate, route hint, or
retrieval-critical identity there before the answer-custody file opens.

Minimal repair without changing retrieval: define the allowed public-task
projection and require an independent pre-execution check that every public
identifier/lexeme permitted to select evidence is already in objective/state,
that candidate/answer/cut fields are absent, and that mutating custody-only
answers before task rendering cannot change any actor-visible task byte.
Alternatively include the complete target-blind public-task projection in the
automatic query; that would be an algorithm change and is not required for the
smaller repair.

The generation arithmetic itself is correct, but P5's “Primary total” is only
an inference/material-generation total. It explicitly adds “plus the
separately bound DLT optimizer schedule,” while neither Section 9's
LIFETIME_ROOT nor Section 11 binds that schedule, its optimizer updates/tokens,
or a profile-derived hard reservation. The imported source plan has two
possible mechanically gated scale laws and gives 16-lineage ceilings, but this
memo does not select/bind the applicable ledger or add it to a stage cap.

Minimal repair: relabel the printed sums as actor inference/material totals,
add an `optimizer_manifest_sha256` (or exact existing-manifest assignment),
bind FULL versus qualified ONE_EPOCH_SCALE before lifetime roots, and state a
separate update/token/A40-hour hard cap. The actor arithmetic need not change.

### R5. Make the BRIDGE_EVENT bytes agree with the graph law

The conceptual intervention is correct. Two byte details remain:

1. define `path_id` from the ordered event-ID sequence, because
   `all_path_ids_sha256` currently hashes a list whose `path_id` string has no
   construction law; and
2. replace “its six incidence arcs” with “the set of unique incidence arcs.”
   The parser does not forbid `source==destination`, and the graph says
   duplicate arcs collapse; such an event has four, not six, unique arcs.

Alternatively forbid self-loops prospectively in certificate roots and prove
that fact in BRIDGE_PROOF. The first repair is more general and leaves the
scientific intervention unchanged.

## 3. Current wire/source cross-check

The proposal is right not to identify the later PCFL-L dialect with current
Stage2A. Current `organism_v6/composition_birth_stage2a.py` uses:

```text
M2AN_/M2AQ_/M2AE_/M2AI_/M2AP_/M2AR_  with 12 base32 characters
THINK KEEP | THINK REVISE | READ INDEX | READ RELATION | STEP | STOP
```

and its checked-in source still reports `PARTIAL_SOURCE_ONLY`. The later
PCFL-L `PCL*` grammar has no READ and is correctly presented as a new common
lifetime transport, not a transparent alias of Stage2A. Stage2A's newer v6
typed-boundary memo also remains a pending native-admission integration; v2.2
does not improperly import that pending result.

The TSJ contract hashes quoted by v2.2 reproduce exactly:

```text
TSJ-v4 source contract  57cdeb290573acb4edf68a1a4c1cbf12ae64eee6f0dc31730cc264cc79ae848a
TSJ-v4 fresh audit      81fe33eeb333dcdb9e0dc3acaff6955804e7b06bc5faa0261785c47ff19f0ee8
```

Current TSJ's actor grammar is THINK/READ/STEP/STOP, but its separate authentic
NEW formation path is PROBE. That distinction is exactly why R2 is required.
The checked-in TSJ v4 files presently implement deterministic ledgers/checkers,
not the authentic actor/formation runtime or completion receipt; v2.2 correctly
keeps that receipt as a later prerequisite rather than claiming it exists.

## 4. Leakage, query, and strong-baseline attacks

### Retriever and hidden-solver leakage

**Pass after R1/R4 closure.** At invocation time the retriever allowlist omits
answer, candidate, route, cut, condition, adapter, hidden world, evaluator,
report, and certificate files. OIDs expose equality only. Transitions come
from anchored public action/outcome bytes, never a world transition object.
Interpretations cannot add topology; MODEL is lexical only. FULL and EXACT are
public projections, and the same-history descendant receives public DLT events
and interpretations but no DREAM prose, adapter state, replay, latent
propositions, answers, or evaluator output.

The remaining risk is construction-time, not invocation-time: opaque
`public_task` and under-specified manifests can encode information before the
runtime allowlist applies. R1/R4 close that seam. The sealed generator oracle
may certify custody truth but must not be callable by actor/query/index code.

### Automatic query and access sensitivity

The core query design passes. It uses current objective/state and prior valid
task-local THINK bytes, binary query TF, whole-THINK suffix retention, exact
1,024/2,048 caps, and no query writer, retry, model reflector, candidate, or
final action. THINK IDs make kept/dropped receipts auditable. The query is
ephemeral and cannot become a lifelong document.

The B16384 condition changes only per-return/cumulative returned-memory access
from `512/8192` to `1024/16384` before the same first 16 calls. It adds no q32,
call 17, THINK, query, retry, or generated token. Because retrieved bytes may
change later THINK history, “same-turn total-access sensitivity” is the right
description. Four-root flatness is correctly not called saturation.

### Branch-local RAW parity and total-system role

This repair is complete. All on-policy arms use the same raw ledger schema,
visibility clock, automatic query projection, BM25 implementation, complete-row
packing, and q16/B8192 envelope. Their actual ledgers are branch-local and may
diverge after the fork. DLT and SLEEP_FROZEN rank only their own raw evidence;
ATN gets no second raw call or budget. The comparison is therefore a fair
total-system comparison, not identical-information or pure-carrier evidence.

The certificate gates also preserve the strong-opponent role: maximum-load
stores, FULL/EXACT headroom, necessary-bundle recall, truthful redirection,
wrong-root/irrelevant controls, reusable-stratum success, and the rule that an
ATN failure is `BASELINE_INVALID` rather than a DLT win. A passing text win or
tie remains reportable.

## 5. BRIDGE_EVENT necessity ruling

**BRIDGE_EVENT is necessary; restoring child-LINK would be a scientific
error.** `AUTO_WITNESSED_GRAPH` deliberately ignores child LINK documents and
derives connectivity from public RAW transitions. Deleting a LINK would
therefore test DLT's compiler object, not this opponent's causal evidence.

The v2.2 proof has the right structure: parse only prior public bytes, enumerate
all simple directed public source-to-goal witness paths, require the event on
every one, rule out duplicate real dispatches, remove the RAW document plus all
citing interpretations and incidence arcs, require zero remaining successful
public witness paths, and keep task/non-descendant public bytes fixed. It also
correctly prevents favorable reselection after failure.

R5 is only byte closure. It does not weaken the required prospective public
necessity proof. Child-LINK deletion should remain a separate DLT mechanism
test, not return to this ATN certificate.

## 6. Independent arithmetic reproduction

The proposal's integer products reproduce exactly. “Returned” below follows
the proposal's convention: direct FULL/EXACT mounts and NONE_SHAM prompt bytes
are input, not returned-retrieval tokens.

```text
one 680-task material branch
  calls                       680*17 = 11,560
  generated                680*2,048 = 1,392,640
  returned                 680*8,192 = 5,570,560
  max input             11,560*32,512 = 375,838,720

P4 material, four roots
  tasks                         4*680 = 2,720
  calls                       2,720*17 = 46,240
  generated                2,720*2,048 = 5,570,560
  returned                 2,720*8,192 = 22,282,240
  input                    46,240*32,512 = 1,503,354,880

P4 evaluation with B16384
  tasks                        10*64 = 640
  calls                       640*17 = 10,880
  generated                640*2,048 = 1,310,720
  returned   6*64*8,192+64*16,384 = 4,194,304

P4 total with B16384
  tasks                    2,720+640 = 3,360
  calls                 46,240+10,880 = 57,120
  generated        5,570,560+1,310,720 = 6,881,280
  returned        22,282,240+4,194,304 = 26,476,544
  input                    57,120*32,512 = 1,857,085,440

P4 total without B16384
  tasks                              = 3,296
  calls                              = 56,032
  generated                          = 6,750,208
  returned                           = 25,427,968
  input                    56,032*32,512 = 1,821,712,384

P5 material
  tasks                    16*3*680 = 32,640
  calls                  32,640*17 = 554,880
  generated           32,640*2,048 = 66,846,720
  returned            32,640*8,192 = 267,386,880
  input               554,880*32,512 = 18,040,258,560

P5 three on-policy evaluation views
  tasks                   3*3,200 = 9,600
  calls                    9,600*17 = 163,200
  generated             9,600*2,048 = 19,660,800
  returned              9,600*8,192 = 78,643,200

P5 actor/material primary total
  tasks                              = 42,240
  calls                              = 718,080
  generated                          = 86,507,520
  returned                           = 346,030,080
  input                   718,080*32,512 = 23,346,216,960

fixed-DLT-history addition
  tasks                              = 3,200
  calls                              = 54,400
  generated                          = 6,553,600
  returned                           = 26,214,400
  input                    54,400*32,512 = 1,768,652,800

actor/material total after fixed history
  calls                              = 772,480
  generated                          = 93,061,120
  returned                           = 372,244,480
  input                   772,480*32,512 = 25,114,869,760

P6 material
  tasks                    16*2*164 = 5,248
  calls                      5,248*17 = 89,216
  generated               5,248*2,048 = 10,747,904
  returned                5,248*8,192 = 42,991,616
  input                    89,216*32,512 = 2,900,590,592

P6 total including two cuts and terminal B16384
  tasks                              = 7,168
  calls                              = 121,856
  generated                          = 14,680,064
  returned                           = 63,963,136
  input                   121,856*32,512 = 3,961,782,272
```

The P3 `3*3*2*3=54` calls per bandwidth and 108/27,648 two-bandwidth maximum
also reproduce. The tenths-of-an-hour formula
`ceil(1.5*calls*t/360)/10` correctly rounds seconds upward to 0.1 A40-hour.
The issue in R4 is omission/labeling of DLT optimizer work, not a multiplication
error in any displayed actor total.

The utility, five-cut trapezoid AUC, root-paired mean/sample-SD order,
one-sided `t_15=1.7530503556925547`, and four-family 90% Bonferroni critical
value `2.4898797034798896` are internally consistent with the stated tests.

## 7. Claim firewall and final disposition

The firewall passes. P4 can establish only source-faithful usability of this
named opponent on four excluded roots. Positive on-policy P5 can establish
only a finite-PCFL total-system result conditional on the fixed child. The
gated fixed-history result is explicitly a conditional system/access contrast,
not a carrier or DREAM effect. Only P6 can license a practical local plateau,
and no stage licenses universal saturation, physical compression, recurrence,
parenting, learned retrieval, open-world discovery, or general continual
learning.

The smallest successor is a v2.2.1 documentation patch implementing R1--R5.
It need not change q16/B8192, the B16384 sensitivity, event-incidence graph,
retrieval coefficients, longitudinal arms, root counts, scientific gates, or
claim language. Fresh review should then rerun the same eleven-item checklist
over the new exact bytes.

## Evidence inspected

- `AGENTS.md`
- `research_notes/analysis/2026-09-14_active_text_native_v22_auto_exact_contract.md`
- `research_notes/analysis/2026-09-14_active_text_native_v21_auto_exact_contract_fresh_audit.md`
- `research_notes/analysis/2026-09-13_active_text_native_v21_auto_exact_contract_draft.md`
- `research_notes/analysis/2026-09-13_pcfl_dev_to_paper_grade_successor.md`
- `research_notes/analysis/2026-09-13_two_sleep_own_experience_junction_binding_v2.md`
- `research_notes/analysis/2026-09-13_two_sleep_own_experience_junction_source_contract_v3.md`
- `research_notes/analysis/2026-09-13_two_sleep_own_experience_junction_source_contract_v4.md`
- `research_notes/analysis/2026-09-13_two_sleep_own_experience_junction_v4_fresh_source_readiness_audit.md`
- `research_notes/analysis/2026-09-13_m_combine4_stage2a_binding_successor_v5.md`
- `research_notes/analysis/2026-09-13_m_combine4_stage2a_v5_fresh_cpu_source_readiness_audit.md`
- `research_notes/analysis/2026-09-14_stage2a_binding_successor_v6_typed_boundary.md`
- `organism_v6/composition_birth_stage2a.py`
- `organism_v6/two_sleep_junction_v4_ledger.py`
- `organism_v6/two_sleep_junction_v4_ledger_checker.py`

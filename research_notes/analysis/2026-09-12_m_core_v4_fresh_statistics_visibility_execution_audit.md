# Fresh statistics, visibility, and execution audit of M-core v4

Date: 2026-09-12 UTC

Scope: independent read-only review of the complete
`2026-09-12_m_core_exact_two_cycle_design_v4.md` against both complete v3
audits. I treated every future package, schema, receipt, materializer, checker,
reader, and model result as a requirement rather than existing evidence. I did
not inspect or change builder code, coordination, jobs, GPU state, models, or
the v4 design.

## Verdict: REWORK before Stage 0 implementation, TEXT, or any fit

V4 correctly repairs most of the *conceptual* v3 defects without adding a
trained arm: it separates the availability theorem from neural-reader gates,
demotes raw wrong-root, adds the live source-read intervention, makes the S1
and S2 training streams common within matched triplets, defines an honest PAD
projection, claims schedule balance only in expectation, separates audit
labels from the public trace, and removes both the global-minimality and
generic-duration claims.

It is not yet the exact executable contract it calls itself. The remaining
blockers are closed-object and probability-law defects, not requests for more
fits. In particular, the package hash does not bind the package, several
purportedly exact schemas and state transitions are missing or inconsistent,
one hashed master seed does not establish exact iid roots, the inference-RNG
and padding equivalence laws are not fully instantiated, and actual cost omits
failed or partial fit time.

## Disposition by requested area

| Area | Disposition | Reason |
|---|---|---|
| Deterministic materialization | **REWORK** | Candidate-alias generation/rejection, accepted-root indexing, typed hash inputs, and the candidate-order permutation `sigma` are not in one complete draw law. |
| Exact public/private schemas | **REWORK** | The displayed records are pseudotypes with unresolved referenced types and a name mismatch; child, training, control, manifest, receipt, and full audit schemas are absent. |
| Formal READ theorem | **PASS WITH GRAPH REPAIR** | Availability-respecting safety and canonical-return construction are now separated correctly, but the underlying phase/state/action machine is not closed. |
| PAD/RPC observable equivalence | **REWORK** | The transducer has the right suspension/overrun semantics, but no exact serialized target length, padding construction, or full observable equality predicate is given. |
| Training RNG/device matching | **PASS WITH ENCODING FIX** | Matched triplets share realized streams and one device/image, with randomized order; `TRAIN_RNG` still needs typed byte encodings in the package. |
| Actor/inference RNG matching | **REWORK** | `episode_role` and the common-draw pairing relation are undefined and can silently reintroduce condition-specific draws; the actor tokenizer/template/runtime binding is absent. |
| Schedule law | **PASS CONDITIONAL ON ROOT LAW** | Independent root-level order/device draws and balance-in-expectation wording are correct; no exact within-root device balance is claimed. |
| Source/DREAM/PAD interventions | **PASS WITH SCHEMA CLOSURE** | The derangements and PAD comparison preserve the intended estimands, and `SOURCE_READ_SWAP_C` closes the live source-to-action-to-admission bridge. |
| Wrong-root disposition | **PASS** | `RAW_WRONG_ROOT` is honestly unmatched, descriptive, and absent from `F_r`, `R_r`, and causal claims. |
| Statistics and binomial arithmetic | **PASS CONDITIONAL ON INDEPENDENCE** | The sign estimands, fixed sequence, cutoff, p-value, and interval arithmetic are correct under independent root indicators. |
| Stopping and claim logic | **PASS WITH FAILURE-TAXONOMY FIX** | DEV/CONF separation and adverse filling are sound, but root-local versus global failure classification is not frozen tightly enough to prevent outcome-dependent invalidation. |
| Root independence | **REWORK** | Domain-separated SHA-256 outputs from one fixed 32-byte seed are computational pseudorandom, not an exact proof that the 16 root indicators are iid. |
| Actual cost accounting | **REWORK** | Summing only `completed fits` excludes device time consumed by crashed, timed-out, or aborted attempts. |
| Fit counts | **PASS** | At most 3 S1 + 3 S2 fits/root gives DEV 48, CONF 96, and combined 144, excluding W*/reader qualification and TEXT. |
| Package/checker completeness | **REWORK** | `protocol_sha256` binds only one file, not the package tree or checker/materializer/runtime bytes, and the checker has no closed receipt/failure schema. |

## Claim-blocking findings and minimal zero-fit repairs

### B1. The content address and schemas do not close the package

The path `m_core_v4/<protocol_sha256>/` authenticates only
`protocol.json` unless that object transitively commits to every other byte.
V4 does not require such a file table or Merkle root. An adversarially simple
counterexample is to replace `reader_binding.json`, a schema, a manifest, or a
receipt while leaving `protocol.json` untouched: the advertised package path
and CLI `--protocol-sha256` remain unchanged although the experiment changes.
The materializer and checker source and their CPU runtime/image are not bound
either.

The schema prose is also not a complete substitute for the promised RFC 8785
JSON Schemas. `PublicReadEvent`, `PublicDeclaration`, `PublicMenu`,
`DecodeConfig`, and `PublicCompilerDecision` are referenced but not fully
defined; the only compiler result defined is named `CompilerDecision`.
`AuditEnvelope` is a field list, not a closed schema. Child A1/A2 inputs,
training/deck objects, controls, manifests, receipts, failure codes, and raw
blob indexes have no displayed closed schema. `ActorEpisodeInput` permits only
phases B/C/D even though exact child and C-probe executions are part of the
claim. The text says four disjoint capabilities while the matrix exposes five
actors including audit. These gaps permit mutually incompatible packages to
claim conformance.

Minimal repair:

1. Add a canonical `package_manifest.json` listing path, byte length, and
   SHA-256 for every package file except itself, including materializer,
   checker, dependency lock, and sterile CPU runtime/image. Address the tree by
   the hash of that manifest and have both commands reject any unlisted,
   missing, or mismatched byte.
2. Commit actual `additionalProperties:false` schemas for every referenced
   type and every child/public/compiler/training/control/audit/manifest/receipt
   object. Resolve `PublicCompilerDecision` versus `CompilerDecision`, define
   all enum values and integer/hex-float widths, and bind blobs by length and
   digest.
3. Make the checker emit one closed receipt containing the package-tree hash,
   executable/runtime hashes, every subcheck result, and an exhaustive failure
   code. This is a zero-fit package repair.

### B2. The deterministic draw law is not complete, and it does not prove iid roots

Section 4.5 introduces a pre-role random base permutation `sigma`, but the
ordered root-materialization list in Section 1.2 never draws it even though it
says no unlisted draw exists. Alias allocation names per-class domains without
defining the candidate byte enumeration, counter initialization, collision
rule, tokenizer-shape predicate, pool exhaustion behavior, or the mapping from
rejected candidates/roots to the fixed TEXT/DEV/CONF indexes. Calls such as
`H("root-nonce",master_seed,cohort,index)` and
`H("train-rng",protocol_sha256,root_handle,stage,stream,step_or_slot)` do not
give byte encodings for all non-byte parts. The CLI accepts a master seed even
though the package is also said to bind it, without an explicit equality
failure.

Separately, domain separation is not statistical independence. All root
objects are deterministic functions of one fixed 256-bit value. Treating
SHA-256 as a random oracle may be a reasonable computational assumption, but
it does not make the exact iid-binomial statement a theorem. As an adversarial
probability example, 16 indicators can each have marginal success probability
one half while all equal one common seed bit; then `K=16` occurs with
probability one half, not `2^-16`. Different domain strings do not by
themselves rule out dependence of downstream indicators.

Minimal repair:

- Publish a typed byte codec for every hash part, every domain/counter, the
  complete alias candidate/rejection/collision algorithm, fixed manifest-index
  rule, and an explicit `sigma` draw at a named point. Require CLI seed equality
  with the bound seed.
- For exact binomial language, bind independently sampled root seeds from a
  registered pre-outcome entropy transcript and state the independent-root
  sampling assumption over the scientific units and all root-local streams.
  If the single-seed SHA construction is retained, label independence as a
  cryptographic/random-oracle assumption rather than an exact consequence of
  the generator. A checker can verify the draw transcript but cannot prove a
  false iid theorem from domain separation.

### B3. The phase/state/action machine is internally incomplete

The hidden-state roster omits `X` and the dead PAD/source states later used by
the transitions. More importantly, state `C` is assigned 32 terminal-family
actions `t_0..t_31` and 32 outcome-family actions `n_0..n_31`, while the actor
is promised exactly 32 action surfaces at each state. Unless the two families
alias, there are 64 actions; if they alias, one action has two incompatible
successors. The intended phase-dependent meaning is inferable, but it is not
present in the stated transition relation. Two implementations can therefore
materialize different legal machines and both point to the prose.

The earlier v3 action-budget hole also remains. `PublicGoal` requires an
`action_budget`, while G_A/G_B/G_D and Section 4.3 specify only READ budgets.
The four destroyed C source-label probes define labels but not a canonical
probe trace, action/return success predicate, or endpoint transition. Thus
`Y_C` is algebraically clear but not mechanically scorable from the displayed
public machine.

Minimal repair: phase-lift the graph (for example `C_B` and `C_D`) or publish
an exact phase-indexed action roster, include `X` and every absorbing state,
and give exactly 32 surfaces and one successor for every phase/state/action.
Bind B/C/D/ATOMS action budgets (the constructive traces require B=4 actions,
D=3, and live C=1 dispatch) and publish the full C-probe trace and binary
scorer. Rerun only the zero-fit BFS/checker certificates.

### B4. RPC bytes and inference common random numbers remain underbound

The suspended RPC and “actor never resumes after overrun” rule correctly
eliminate the important timing branch. But `MemoryReturn.fixed_pad_b64u` is
merely nullable; there is no registered total serialized length, pad-byte
derivation, encoding equation, or equality predicate over FOUND, MISS,
BLOCKED, cut, swap, and no-carrier paths. A conforming implementation could
use one constant short pad and leak result class or row length through byte
count while still releasing at `t+DELTA`. `reader_binding.json` is said to bind
the release rule, but the package checklist never states the complete
observable transcript comparison it must certify.

Training common random numbers are substantially fixed. Inference common
random numbers are not: draws are keyed by an undefined `episode_role`, and
“compared inference cells receive common draws” supplies no exact equivalence
classes. Setting `episode_role` to the condition/control ID would reproduce the
v3 defect while literally excluding a separate `condition` argument. The
clean actor's tokenizer, chat template/renderer, inference engine, software
image, and deterministic-decoding implementation are also not bound by the
displayed actor schema.

Minimal repair: publish the exact target byte length and deterministic padding
function for every RPC class, plus a machine-readable allowed-difference map
over the complete actor-observable transcript and fake-clock/overrun cases.
Add an `inference_rng_family_id` table that places every matched contrast and
h twin in the same family, encode every token draw/counter exactly, and receipt
the draw ledger. Bind the actor tokenizer/template/runtime/image beside its
model and decode configuration. These changes add no fit.

### B5. Global invalidation and actual device cost need closed accounting rules

Adverse filling of root-local failures is correct. The exception for a
“global instrument invalidation” is necessary but currently judgmental:
“shared” and “demonstrably root-local” have no presealed failure-code map.
After seeing results, classifying a weak device/service episode as global
rather than root-local could discard an unfavorable confirmation cohort.

The measured-cost equation is not actual cost as written:

```text
C_train_actual = sum over completed fits f measured_device_seconds(f).
```

A fit that consumes device time and then crashes, times out, or is aborted is
not completed, so its seconds disappear. This can understate cost even though
the scientific cell is correctly adverse-filled. The measurement clock and
start/stop boundaries are also not defined.

Minimal repair: freeze an exhaustive failure taxonomy before confirmation.
Each code must map either to one root zero or to a terminal whole-program
`NO_CLAIM`; global invalidation must not silently authorize replacement roots,
a fresh seed, or a replay under the same protocol.

Define actual training device cost as the sum of occupied device-seconds over
**every launched fit attempt**, including completed, failed, timed-out, and
aborted attempts, with monotonic-clock source and allocation/start/stop
boundaries bound in the receipt schema. Keep qualification, inference, reset,
validation, serialization, queue, and startup costs in their already separate
ledgers.

## Independent arithmetic and stopping verification

For `n=16`,

```text
sum_{j=12}^{16} C(16,j) = 2517
2517 / 65536 = 0.0384063720703125
sum_{j=11}^{16} C(16,j) = 6885
6885 / 65536 = 0.1050567626953125
```

Therefore 12 is the first rejecting count at one-sided `.05`. The stated
one-sided Clopper--Pearson lower endpoint
`Beta^-1(.05;12,5) = 0.5156035789...` is correct. Fixed-sequence testing in
the order `S -> M -> U -> W -> R` strongly controls FWER provided each root
test is valid; dependence among the five co-primary p-values is harmless.
The unresolved dependence is across roots, addressed in B2.

The staging arithmetic is also correct. D1/D2 consume at most 12 fits after
both triplets; all eight DEV roots consume at most 48; 16 confirmation roots
consume at most 96; total M fits are at most 144. Skipped S2 cells remaining
zeros, no confirmation extension, and no early-success stop preserve the
denominators. These maxima exclude W*/reader qualification and TEXT, exactly
as v4 states.

## Promotion condition

After B1--B5 are repaired and the resulting content-addressed package plus
independent checker actually exists and passes, no additional trained
condition is required. Until then, v4 should remain a design candidate: do
not begin TEXT, reader acceptance, or any M fit, and do not attach exact-iid,
exact-byte, or measured-actual-cost claims to it.

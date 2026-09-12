# Fresh statistics, visibility, and execution audit of M-core v5

Date: 2026-09-12 UTC

Scope: fresh-context, read-only review of the complete
`2026-09-12_m_core_exact_two_cycle_design_v5.md` and the repository operating
contract. I treated the materializer, package, checker, schemas, receipts,
TEXT results, reader acceptance, and model results as future requirements, not
as evidence. I did not inspect or modify builder code, coordination, jobs,
models, checkpoints, GPU state, or leases, and I ran no model, GPU, or
scientific job.

## Verdict: REWORK before Stage 0, TEXT, reader acceptance, or any fit

V5 closes most of the substantive v4 defects. In particular, it gives the
source control a truthful tie rather than a privileged label; gates every
subtracted control; binds an immutable package by a non-self-referential file
table and Merkle root; separates public pair handles from audit episode IDs;
phase-lifts B and D; fixes action budgets; specifies fixed-size suspended
RPCs; enumerates inference RNG families; adverse-fills invalid roots; counts
launched rather than only completed fits; and retains a valid six-carrier
maximum.

The design is not yet the closed executable contract it says it is. One
compiler cannot perform its required decision from its allowed input. The
normative schema catalog omits many package and result objects, including the
receipts needed to establish common optimization, root outcomes, stops, and
cost. Two registered controls and the S1 stopping rule are not defined in the
machine. Finally, independent entropy calls alone do not make indicators that
include physical execution failures independent, and the registered
Clopper--Pearson expression is undefined at a possible result. These are
zero-fit specification repairs; they require no seventh condition or model
execution.

## Audit disposition

| Area | Disposition | Finding |
|---|---|---|
| Package hashing and canonical bytes | **PASS in construction; REWORK in schema closure** | The file-table/Merkle/JCS construction is non-circular and reproducible, but many listed JSON members have no normative schema and one required RPC map has a different filename from the whitelist. |
| Generator and root entropy | **REWORK** | Separate pre-outcome CSPRNG calls plus root-local hashing are the right law, but the seed-commitment function, complete counter advancement/domain roster, and package-wide alias-collision allocation are not closed. |
| Actor/scorer visibility | **PASS conditional on package ACL receipts** | Hidden bits, condition, derivations, device, and order are absent from actor/scorer objects; pair identity and RNG-family repairs are sound. The missing closed binding/ACL schemas prevent this from being checked as written. |
| Compiler visibility | **REWORK** | `NEW_ROW_ADMISSION` must recover the authentic source-preferred family and validate family membership, but its closed input contains neither the authentic source view, source-choice event, nor public menu. |
| State graph and budgets | **PASS for B/C/D; REWORK for registered controls** | The phase-lifted successful machine and B=4, C-probe=1, C-live=2, D=3 action budgets are coherent. `CATALOG_NO_GOAL_NO_CARRIER` is illegal under the B semantic schema, and `NO_SLEEP2` has no carrier/availability/trace definition. |
| Formal reader theorem | **PASS conditional on actual tables** | The availability theorem is correctly separated from neural acceptance; FULL=3 versus ATOMS=4 and FULL_NEW=2 follow from the stated graph. The promised transition, availability, candidate, and canonical-return tables are not schema-closed artifacts yet. |
| RPC bytes and timing | **PASS in mechanism; REWORK in receipt closure** | 7-byte magic + 4-byte length + payload + SHAKE pad correctly totals 16384, release is at one logical tick, and overrun has no branchable continuation. The observable-map filename and missing closed fake-clock/transcript receipt prevent literal package conformance. |
| Matched optimization nuisance | **PASS in rule; REWORK in evidence type** | Same device, sterile sequential processes, common stage-keyed streams, bit-identical work, and semantic bitmaps are the right requirements. No closed receipt represents the required optimizer, RNG-counter, kernel, health, and pairwise-work conjunction. |
| Matched inference nuisance | **PASS** | Literal condition-free families, counter-zero resets, token ledgers, and C post-dispatch cloning close the v4 common-random-number defect, conditional on the actor binding and ledger actually being schema-bound. |
| TEXT stopping | **PASS** | The 4-root decision and conditional extension to eight roots are deterministic, retain failed roots, and do not enter confirmation evidence. |
| DEV/CONF stopping | **REWORK** | The phrases “frozen S1 gate,” “S1 kill ... if both pass,” and “frozen S1 futility” do not define one Boolean from receipts, so two conforming schedulers can launch different S2 fits. |
| Binomial/FWER arithmetic | **PASS conditional on a repaired joint law** | The 12/16 cutoff and `2517/65536` tail are correct; fixed-sequence testing controls FWER if each p-value is valid. The present execution-level independence premise is incomplete, and the interval formula needs a K=0 case. |
| Invalid-root handling | **PASS in scientific direction; REWORK in aggregation receipt** | Root failures remain zeros with no retry/replacement, invalid controls cannot manufacture contrasts, and global failures suppress the cohort. There is no closed root-result object that records gates, indicators, skipped cells, and the one terminal classification. |
| Fit maxima | **PASS** | Three S1 plus three S2 fits give DEV <=48, CONF <=96, and combined <=144, excluding TEXT and qualification as stated. |
| Cost accounting | **PASS in equation; REWORK in materialization** | Launched crashes/timeouts/aborts are now charged. CPU, queue, reset, serialization, cost-summary, ownership, and non-overlap receipts are absent, and bundle granularity is inconsistent with the six-attempt array unless one bundle per root is explicitly required. |

## Minimum zero-fit blockers and exact repairs

### B1. `NEW_ROW_ADMISSION` violates its own capability boundary

The required decision is not a function of the closed `CompilerInput`.
Sections 3.4 and 5.3 require the NEW compiler to reconstruct the authentic
source-preferred family, verify that the source choice and dispatch selected
that family, enumerate the h posterior, and reject the nuisance family. But
Section 12 requires a NEW input to contain only `declaration`, `dispatch`, and
`public_outcome` (plus a root-independent `public_task_law`). Those objects
carry only handles and a menu hash:

- neither the cited source row nor the original authentic source bundle is in
  the input;
- the source-choice event itself is not in the input, only its handle;
- the `PublicMenu` is not in the input, only its hash; and
- a root-independent law cannot map root-allocated L/R/E handles or recover
  the root-specific b orientation.

Consequently the compiler cannot distinguish an authentic informative-family
dispatch from the hit-matched `SOURCE_READ_SWAP_C` nuisance dispatch without
an undeclared lookup or hidden b/role access. This defeats both exact
implementability and the most important live source intervention.

Minimal repair: extend the NEW-only compiler variant with the canonical
authentic `SourceEvidenceView`, the actual `MemoryAuthorizedActionEvent` for
the source choice, and the canonical `PublicMenu` (or an equivalently complete
public event prefix). Require exact handle/hash linkage among those objects,
the declaration, and dispatch. Keep b, roles, expected admission, donor map,
condition, and endpoint unavailable. Add all 32 Stage-0 fixtures and the live
authentic/swap prefix receipts against this exact input. No fit is involved.

### B2. The generator/package/result type system is not closed

Section 1.2 says Section 12 is the normative actual schema catalog for every
object. It is not. The package whitelist contains JSON objects for
`root_generator`, alias/action/candidate rosters, availability and transition
tables, canaries, the RPC machine, controls, order/schedule tables,
allowed-difference maps, canonical returns, and W*/reader/actor bindings, but
Section 12 defines none of their root types. Therefore
`schema_catalog.json`, described as the exact extraction of that appendix,
cannot validate the very members on which the checker and theorem depend.

The generator is underclosed in three independently reproducibility-relevant
places as a result:

1. `root_seed_commitment` has no byte equation relating it to the 32 seed
   bytes;
2. rejection sampling does not literally state when its per-domain counter is
   advanced, and the alias-class/event-stratum domain strings and iteration
   order are not enumerated in the normative text; and
3. “no collision across the entire package” is not reconciled with each root
   independently permuting the same finite alias pool and with the ban on
   root rejection. The contract must either define handle reuse as legal and
   scope every lookup, or define a deterministic disjoint allocation that
   does not outcome-filter roots.

There is also a literal member-name mismatch: Section 6.4 requires
`rpc_observable_allowed_diff.json`, while the exhaustive manifest list permits
only `allowed_difference_maps.json`. An implementation that creates the named
RPC file is rejected as extra; one that omits it lacks the named artifact.

Result typing is thinner still. No closed object records a root's component
gates, valid contrasts, binary indicators, skipped cells, final failure,
stopping decision, p-value, confidence bound, cost summary, compiler-prefix
comparison, BFS certificate, or fake-clock result. `AuditEnvelope` replaces
several of these with unconstrained `BLOB`s, which binds bytes but does not
make their required fields mechanically checkable. `TrainingTensorReceipt`
does not contain the pairwise optimizer initialization, all RNG counters,
kernel flags, device-health equality, or aggregate work receipt required by
Section 7.1.

Minimal repair: add closed Draft-2020-12 schemas and semantic constraints for
every listed package member and every required evidence/result type; use one
manifest-listed allowed-difference filename; define the commitment, counter,
domain, iteration, and collision/allocation laws; and add typed receipts for
root aggregation, prefix/ACL/RNG/work comparisons, theorem/fake-clock checks,
statistics, stops, and cost. Opaque evidence blobs may carry raw data, but a
closed typed object must expose every field on which a gate relies.

### B3. The control roster and staged execution law are incomplete

Two registered controls cannot be executed from the current closed machine.

`CATALOG_NO_GOAL_NO_CARRIER` is in `ControlReceipt`, the B RNG family, and the
noncompensatory R conjunction. Its name and Section 4.2 require no goal, while
the Section-12 semantic law requires every B `ActorEpisodeInput` to have its
matching non-null B goal. There is no goal-neutral public type or separate
control phase. Calling the cell “descriptive” does not cure the contradiction
because R still requires every named control and carrier-free cell to
complete.

`NO_SLEEP2` is also in the control roster, D RNG family, and R, but no section
defines its mounted carrier, availability set, two READ returns, expected
endpoint failure, or allowed-difference relation. The likely interpretation
is FULL_OLD with the old link present and the NEW request returning charged
MISS, but that is not stated and is not interchangeable with a no-carrier or
PAD cell.

The same incompleteness affects scheduling. “Only after the frozen S1 gate,”
the D1/D2 “S1 kill,” and confirmation “S1 futility” never identify the exact
Boolean predicate over S1 receipts. This affects which S2 fits are launched,
which attempts appear in cost, and when `I_W` and `I_R` become zero. It cannot
be chosen after observing S1 outcomes.

Minimal repair: either remove the no-goal descriptive diagnostic from every
normative roster/gate or add a legal goal-neutral input/phase and exact trace;
define `NO_SLEEP2` as one exact mounted-carrier availability intervention;
and publish one presealed `Q_S1` Boolean with its receipt inputs. State
explicitly that DEV launches both D1/D2 S2 triplets iff
`Q_S1(D1) & Q_S1(D2)`, and define the exact full-kill predicate that permits
D3..D8. For CONF, state that root r launches S2 iff `Q_S1(r)=1`; otherwise its
downstream indicators are zero without an attempt.

### B4. Exact-binomial validity needs the complete outcome independence law

The entropy repair is necessary but not sufficient for the stated exact
Binomial(16,.5) reference. Independent uniform root seeds make deterministic
root-generated fixtures independent. The tested indicators also incorporate
fit crashes, RPC overruns, interface/non-harm failures, device-local failures,
and other execution events that the contract does not require to be
deterministic functions of only the corresponding root seed or independent
root-local random sources. `ROOT_LOCAL_DEVICE` explicitly permits such an
event. Merely classifying a shared disturbance as root-local does not make it
independent.

For example, a common unrecorded device-health bit could make all otherwise
null roots succeed together or make them all zero. Each marginal success
probability could be one half while `Pr(K=16)=1/2`, not `2^-16`. Adverse
filling protects against a single failed root but does not repair dependence
of the root indicators. `GLOBAL_SHARED_STATE` helps only if every shared cause
is detected and globally terminates before testing; the current closed
receipts cannot establish that.

Minimal repair: make the confirmatory assumption explicit over the **complete
root indicators**, not only entropy and PRNG streams. Conditional on immutable
common assets, every actor/reader/training/failure input to root r must be a
measurable function only of its independently sampled seed and explicitly
independent root-local execution noise; any cross-root or uncertain-boundary
execution cause must be a presealed global no-test event. Receipt the isolation
predicate. If that assumption cannot be defended, replace the exact-binomial
claim with an analysis valid for the actual dependence; hashing cannot prove
it.

The arithmetic itself is correct:

```text
sum_{j=12}^{16} C(16,j) = 2517
2517 / 65536 = 0.0384063720703125
sum_{j=11}^{16} C(16,j) = 6885
6885 / 65536 = 0.1050567626953125
```

Thus 12 is the first rejecting count at one-sided alpha .05, and fixed
sequence `S -> M -> U -> W -> R` controls FWER without assumptions about
dependence among the five valid p-values. The registered one-sided 95%
Clopper--Pearson lower endpoint must, however, be piecewise:

```text
L(K)=0                              if K=0
L(K)=Beta^-1(.05; K, 17-K)          if 1<=K<=16.
```

The present expression is undefined at the possible outcome K=0. This is a
reporting/specification repair, not a change to the 12/16 decision.

### B5. The cost rule has no non-overlapping, complete result representation

The revised numerator is scientifically honest: it includes every launched
fit attempt through release, including crash, timeout, and abort. The closed
result types cannot yet produce the promised complete ledger. There is no CPU
interval type for materializer/compiler/checker work, no queue/reset/
serialization interval type, no ownership-ambiguity or cost-validity record,
and no typed aggregate by status/deck/device/image. `ExecutionAttemptReceipt`
can represent only device intervals for actor, reader, or qualification.

The granularity is also unresolved. The only `ResultBundleManifest` permits
at most six fit attempts, which is correct for one root, while the documented
materializer/checker interface consumes a cohort directory and the prose
speaks of one result bundle. A DEV or CONF cohort bundle needs up to 48 or 96
attempts. If bundles are per root, the design needs a cohort index manifest
that binds all root bundles, roots with zero attempts, stopping decisions, and
the cohort statistics.

Finally, summing actor and reader “exclusive device-allocation intervals” is
valid only if they are disjoint allocations. If an actor interval remains
open while its reader uses the same reserved device, naïve summation
double-counts device occupancy. The checker needs either disjoint transfer
intervals or a union-by-device rule, plus a rule for shared versus separately
leased devices.

Minimal repair: choose and schema-bind root and cohort result-bundle
granularity; raise attempt cardinalities at the cohort level or add a cohort
index; add all CPU/non-fit/cost-summary receipts; and define device cost as
the union of validated exclusive allocation intervals per device (or prove
pairwise non-overlap before summing). Reconcile a missing release boundary
with the failure taxonomy: say explicitly whether it is `GLOBAL_UNKNOWN` and
therefore no scientific test, or only a separately typed invalid cost report.

## What is already scientifically sound

Conditional on the zero-fit repairs and actual passing artifacts, the narrow
claim is supportable. The source tie is truthful and hit-matched; the live
source-read swap is the right intervention once its compiler inputs are
fixed; the selected DREAM link remains necessary in the phase-lifted graph;
FULL and ATOMS have the claimed 3-versus-4 READ separation; the D path needs
both the preserved old two-action link and the post-outcome h row; separate
cuts and legal payload swaps make D specificity noncompensatory; PAD matches
S2 training work without exposing a public new row; and invalid subtracted
controls cannot create favorable signs.

The six trained carriers per complete root, 48-fit DEV maximum, 96-fit CONF
maximum, and 144 combined maximum are all arithmetically correct. No blocker
above calls for another fitted arm. They call for an executable public-input
compiler, closed package/result schemas, exact controls and stops, a complete
independence premise, and a materializable non-overlapping cost ledger.

## Promotion condition

Do not begin Stage 0, TEXT, reader acceptance, or fitting under v5 as written.
After B1--B5 are repaired, build the immutable package and independently
implemented checker, reproduce the complete materialization byte-for-byte,
and require every zero-fit schema/generator/ACL/BFS/RPC/prefix/work/cost check
to pass. Only those actual receipts—not this design memo—can promote the
protocol to execution.

# PCFL-Active-Stream repaired-proposal re-audit

Date: 2026-09-02

Status: **read-only advisory only**. This memo does not edit or ratify the
proposal, initialize or approve deliberation, authorize implementation or CPU/GPU
science, release a claim, or create successor authority.

For compactness, bare proposal filenames below are rooted at
`research_loop/changes/chg_20260902_pcfl_active_stream_paper_target_v1/`.

## Verdict

**REWORK**

The repaired bundle closes most of the two bound audits' operational objections,
but it is not yet internally coherent enough to ratify as the scientific design.
The strongest remaining issues are not requests for more evidence from an
unimplemented system. They are contradictions or gaps in the prospective
construct, estimands, and gates that can be repaired in the specification now.

## Blocking issues

### 1. The representation-neutral target contract still collapses to bounded recurrent KV, while another contract defines success as requiring SELF

The ordinary world remains a collection of independent finite permutations:
thirteen fresh mappings per cohort, with persistent family labels
(`experiment_contract.md:31-47`). Ordinary D4 requires four life-specific
bindings (`experiment_contract.md:63-72,122-126`). The stable source design is
even more explicit that a target exposes at most six constant-degree anchors and
permits six one-atom reads independent of lifetime
(`research_notes/48_pcfl_stream_and_schema_design_v0.md:74-88`). Thus ordinary
NEW/OLD/CROSS tests accumulation and use of a finite causal table, not an escape
from finite KV.

The new integrative target is stronger, but only changes independent/nonadaptive
lookup into a constant-depth recurrent lookup. It rejects one event, four
independent lookups, and a nonadaptive precommit, then requires a read-dependent
query/path DAG (`experiment_contract.md:110-120`). The known-good recurrent KV
condition has the same finite atom store and cap and is expressly allowed to
condition later reads on earlier returns (`compiler_memory_contract.md:121-130`).
Stage A is supposed to certify that recurrent route while stopping only when the
nonadaptive route solves (`stage_gate_and_test_manifest.md:62-72`).

But the memory contract separately says the same integrative targets *require a
model-owned semantic relation* (`compiler_memory_contract.md:112-119`). A target
cannot be representation-neutral and simultaneously require the primary
representation by definition. Nor is the disposition for recurrent constant-cost
KV coherent: the resource contract says a native exact/linked reduction to
constant-cost KV stops the experiential-reasoning claim
(`baseline_and_resource_manifest.md:117-121`), while the A0 gate permits a
successful constant-budget recurrent KV route and merely asks SELF to beat it
later.

Repair required: define success solely in world/action terms, independent of
record type. Specify one exact reader/controller budget for RAW, witness-KV,
MECH, linked/rolling, and SELF, and state unambiguously what happens if the
recurrent known-good KV or faithful linked store solves at constant target-time
work. Either narrow the result to finite causal-map compilation/use, or add a
prospective target where local atomic memory is information-theoretically
insufficient. Do not make a `SELF_SEMANTIC` record a construct prerequisite.

### 2. The exact cognition freeze has a direct contradictory permission

The statistics contract says the eight DEV roots "may freeze prompts, compiler
policy, [and] reader budgets" (`statistics_and_claim_contract.md:12-14`). In
contrast, the compiler contract requires the prompt/DSL/model/reader/cut bytes to
freeze before the first Stage-B model call and invalidates DEV after any change
(`compiler_memory_contract.md:18-28`); the resource contract says the same bytes
are frozen at A2 before B0 and cannot be rewritten by DEV
(`baseline_and_resource_manifest.md:35-41`); and A2 repeats the prohibition
(`stage_gate_and_test_manifest.md:92-102`).

This is material, not editorial: target blindness and model ownership depend on
whether DEV can shape the compiler or reader. Repair required: make every
contract say that A2 freezes cognition before B0; DEV may select only the two
already frozen AS-EXT candidates and the predeclared resource/go/calibration/stop
disposition. Any cognition change must invalidate and restart DEV.

### 3. P3 can certify “retention” when SELF never acquired the old knowledge

P3 is only
`Y[SELF,M_6L,T_OLD_6] - Y[SELF,M_acq,T_OLD_6]` with a `-0.05`
noninferiority margin (`statistics_and_claim_contract.md:160-174`). The Stage-B
gate likewise requires only that old value not fall by more than `.10`
(`stage_gate_and_test_manifest.md:136-137`). Therefore `0 at acquisition -> 0 at
6L` passes retention. Nothing in P3 requires nontrivial first-acquisition value,
supported decisive mappings, or current absolute value on those same OLD rows,
yet C3 says early mappings were retained
(`statistics_and_claim_contract.md:241-254`).

Repair required: condition retention credit prospectively on demonstrated
acquisition of the exact preassigned old target/bindings, without dropping failed
roots, and add a registered absolute-value or above-floor requirement at
`M_acq` and 6L. If failed acquisition remains zero in the population estimand, it
must make the joint continual-learning claim fail rather than make
noninferiority easier.

### 4. Twenty-four roots are powered endpoint-by-endpoint, not for the declared intersection decision

The claim requires all four primary families to pass
(`statistics_and_claim_contract.md:114-118`), but the planning table requires
only `.80` power for each individual contrast
(`statistics_and_claim_contract.md:43-57,68-75`). At the boundary values actually
specified (`n=24`, effect/NI distance `.20`, SD `.30`, one-sided Bonferroni
`.0125`), the individual noncentral-t power is only about `.801`; this says
nothing sufficient about the probability that all four tests pass. That joint
probability depends on their covariance and can be much lower. P1 also carries
additional mandatory component-direction gates
(`statistics_and_claim_contract.md:129-142`), further lowering end-to-end design
power.

The four separate 95% SD upper bounds are not made simultaneous, and the
"distributional diagnostic" that can relabel Stage C calibration-only is not
defined (`statistics_and_claim_contract.md:43-57`). This is especially important
for the non-smooth rootwise minimum in P1 and maximum in P4.

Repair required: power the complete frozen intersection decision, including all
mandatory gates, under a predeclared covariance/worst-case model or an exact
prospective simulation; alternatively describe 24 roots honestly as four
individually powered endpoints without calling the conjunction an 80%-powered
confirmation. Freeze an executable distributional diagnostic and simultaneous
variance-uncertainty rule before DEV outputs.

### 5. P1's test statistic does not itself establish the claimed full mediation chain

`MED_w` contains only later integrative-target value, and `FLYWHEEL_RECON_w` is
the minimum of that terminal contrast and representation/cut contrasts
(`mediation_contract.md:263-294`). Probe direction, information gain, newly
supported evidence, delta readability, and working-path completion are measured
(`mediation_contract.md:210-224`) but enter P1 only as component point-direction
gates, explicitly not as tests (`statistics_and_claim_contract.md:129-142`). A
positive but noise-sized sample sign can therefore satisfy a claimed causal link
without inferential support, while the confirmatory sentence says memory
*changed* the probe, evidence, delta, and later action
(`experiment_contract.md:269-281`).

The prose that an earlier-link failure prevents mediation credit
(`mediation_contract.md:222-224`) does not define whether or how `Y`, `MED_w`, or
the assigned root summary is zeroed. Repair required: define an exact
failure-inclusive, root-level chain-complete estimand (or a predeclared joint
causal-mediation test) in which every claimed link has a nonzero effect criterion
and failed links cannot leave terminal `Y` credited. Recompute the joint power
after doing so.

### 6. The MECH DEV gate and the required common-history margin have potentially incompatible scopes

Stage B requires `AS-MECH >= .90` wherever public support opportunities are
complete (`stage_gate_and_test_manifest.md:119-123`). P1 defines one of its
minimum components as generic SELF minus the strongest common-history non-SELF
condition, including MECH (`mediation_contract.md:274-290`), and requires the P1
mean to be at least `.20` (`statistics_and_claim_contract.md:129-140`). Since raw
target value is bounded by one, if the `.90` MECH gate applies to the supported
common-history integrative rows, the SELF-minus-MECH component is at most `.10`
and P1 is mathematically unable to pass.

Repair required: state exactly which rows and denominator the `.90` MECH gate
uses. If it includes the common-history integrative target, change the
incompatible threshold/estimand. If it applies only to ordinary witnessed-atom
coverage rows, say so in every gate and keep those rows distinct from the
integrative compiler contrast.

## Findings that pass this re-audit

1. **Manifest and source bindings.** Every SHA-256 in `bundle_manifest.json`
   matches the current file bytes. Every `change.json.context_files` SHA also
   matches. The workflow and change IDs, directive, workspace/output directory,
   and effective context set agree: the workflow lists 29 `context_files` and
   separately binds the one directive, exactly covering the change's 30 source
   files (`bundle_manifest.json:4-62`; `change.json:9-159`;
   `research_loop/workflows/pcfl_active_stream_paper_target_v1.deliberation.json:5-42`).
   No intake state or deliberation run directory exists.
2. **Authority closure.** The scope permits only the named non-scientific
   architecture-deliberation role calls through `human_required` and forbids
   implementation, CPU/GPU science, training, claims, and inferred ratification
   (`scope_proposal.json:4-20`; `change.json:491-500`). The workflow configures
   distinct advocate/systems/benchmark/critique/consensus roles and creates no
   automatic authority (`research_loop/workflows/pcfl_active_stream_paper_target_v1.deliberation.json:43-109`).
3. **Fork and intervention mechanics.** The repair now runs all three treatments
   on both sides at every post-native checkpoint, balances opaque labels/order,
   includes failures, unmounts the assigned object, and rebuilds later memory
   from authentic prior plus public-event delta (`mediation_contract.md:39-80,
   196-224`). Binding-only, same-probe twin-outcome, RAW/action/witness/SELF, and
   prospective semantic/sham cuts are materially stronger than the original
   design (`mediation_contract.md:130-182,226-260`;
   `compiler_memory_contract.md:132-164`).
4. **Information visibility.** The component-level matrix separates assigner,
   actor, resetter, delta compiler, installer, evaluator, scorer, and selector;
   ephemeral goal-derived queries and post-fork survivor rules are explicit
   (`visibility_taint_reset_contract.md:25-75,100-137`). This disposes the prior
   combined-component contradiction prospectively, subject to later mutation
   tests.
5. **Baseline envelope.** P4 now uses the rootwise maximum of RAG, frozen AS-EXT,
   and MECH, while the byte-identical common-history sentinel includes raw RAG,
   both KV readers, MECH, linked, rolling, generic SELF, and a separately labeled
   class-informed ceiling (`statistics_and_claim_contract.md:176-199`;
   `experiment_contract.md:208-225`). This is the right architecture for testing
   whether generic SELF adds value; the unresolved problem is the target/reader
   definition in blocker 1, not omission of the requested competitors.
6. **Exact roster.** The 908 rows per root reconcile exactly: 768 ordinary
   current-snapshot rows + 36 lagged NEW + 12 first-acquisition OLD + 36
   mediation-clone integrative + 24 additional 3L lanes + 32 common-history
   rows. The intact 3L AUTH lane is correctly not double-counted
   (`baseline_and_resource_manifest.md:75-87`;
   `statistics_and_claim_contract.md:77-84`). The 18 exploration clones and six
   binding-only diagnostic actions are separate nested operations.
7. **Deadline honesty.** The proposal explicitly removes 24-root confirmation
   from the September 25 evidence path and permits only construct plus
   failure-inclusive eight-root DEV labeled nonconfirmatory; it forbids P1-P4,
   superiority, noninferiority, plateau, and continual-learning claims in that
   submission (`baseline_and_resource_manifest.md:130-153`). The dated path has
   hard fleet/cost/projection stops and a design-only fallback
   (`baseline_and_resource_manifest.md:155-201`). This is honest, although an
   eight-root DEV/design paper remains a weak main-track empirical accept case.

## Strongest accept case

After the six specification repairs, the work could be accepted as a narrow
causal systems/benchmark paper. Its distinctive contribution would not be a new
memory substrate or higher-order schema discovery. It would be the unusually
well-controlled pulse

```text
randomized memory -> information-seeking action -> public outcome
-> treatment unmount -> target-blind model-owned delta -> later sterile action
```

combined with common-history representation controls, matched-action outcome
intervention, binding-only intervention, semantic/sham lesions, failure-inclusive
roots, and strict authority/claim boundaries. If generic SELF beats the strongest
raw/witness/mechanical/linked/rolling common-history condition on a
representation-neutral integrative target, and the complete powered causal chain
passes on fresh roots, that is a credible finite synthetic result. The proposal
correctly disclaims generic SOTA, learned controller, compression, naturalistic
development, unbounded learning, and a Paper-1 LoRA result
(`experiment_contract.md:24-27,267-301`).

## Strongest reject case

The simpler account remains live: a frozen, hand-prompted pretrained controller
stores or derives a small independent map under persistent labels, then uses a
bounded adaptive index to fetch the needed entries and compose a legal action.
SELF may merely precompute one recurrent join with extra offline model calls. If
the target itself requires a SELF record, or the witness/linked controller is
artificially prevented from performing the same finite recurrent computation, a
SELF win is circular rather than evidence for model-owned experiential
structure. Even a clean result is not the full Dream-LoRA-Think thesis because
the controller is frozen and LoRA is deferred. For September 25, construct plus
eight DEV roots can support a transparent design/pilot paper or a useful null,
not a confirmed continual-learning claim.

## Deliberation initialization ruling

**Authority/source safety: YES, with a strict qualification.** The hashes,
effective source bindings, proposal-only scope, configured roles, and absent run
state make it safe to initialize the bound workflow *as a non-authorizing
deliberation that may return REWORK*. Initialization itself must not be described
as approval and must stop at `human_required`.

**Scientific approval readiness: NO.** The exact bytes should not be presented
to the human owner as an approval-ready consensus until the six blockers above
are dispositioned. If formal deliberation is initialized before repair, these
issues must be treated as live objections, and any consensus that does not
resolve each one should end `rework`, not `human_required` for ratification.

## Exact audited top-level hashes

- `change.json`:
  `55295d76661f350a5537b47d0c6533fd656c9565037a491e755bbfb65b04f8b1`
- `bundle_manifest.json`:
  `899760339d0400ec0ee3db864b35cdca01b4408c9dae30ee319409131fcf4bb0`
- `research_loop/workflows/pcfl_active_stream_paper_target_v1.deliberation.json`:
  `8280eac97bea73c1a34cca9277b821d9565148a6b66f3fe03217d24bfaad5e81`


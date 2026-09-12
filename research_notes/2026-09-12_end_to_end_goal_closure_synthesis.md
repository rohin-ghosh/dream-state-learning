# End-to-end goal closure synthesis

Date: 2026-09-12 UTC

Status: watcher-side scientific synthesis only. It does not authorize or
modify source, model/tokenizer execution, training, adapters, GPU jobs,
parenting, claims, release, or submission. Astra's separate standing builder
authority in `AGENTS.md` remains unchanged.

## The simple picture

The organism is still only three operations:

1. **THINK:** the child reasons, acts, observes outcomes, and authors candidate
   memories and connections.
2. **DREAM:** the child manages and distills its active context.
3. **SLEEP:** offline replay/paraphrasing renders committed public experience,
   a provenance gate admits grounded records, cumulative replay constructs the
   corpus, and a conservative write puts it into LoRA.

The experimental ladder below is not extra cognition. It is how we prevent a
test from passing when the writer learned a global habit, the compiler supplied
the answer, a reader did the reasoning, or a longer life merely repeated the
same programs.

## Current diagnosis

No full thesis clause is paper-proven. The immediate source failure is sharper
than a generic memory problem: the two node audit files collectively contain
31 life records (17 on node 1 and 14 on node 2), 25 with 32 sleeps and 26 with
at least 31 sleeps. Every record reports
`A_final4_hi=A_final4_lo=0`. Maximum high-threshold admission is 2.53%. These
artifacts include incomplete lives, so they are a mechanism diagnostic rather
than a population estimate, but they agree with the completion-qualified
handoff result: the old tick asks for NOTE before ACT/outcome, so the child does
not naturally leave grounded post-outcome learning records.

Authoritative files:

- `research_notes/analysis/out/node1/articulation_lives.json`
- `research_notes/analysis/out/node2/articulation_lives.json`
- `research_notes/HANDOFF_2026-09-12.md`

The completed evidence otherwise says:

- LoRA writes alter behavior and lower loss on training-like rows.
- Legacy cell A transports the supplied fixed routine; no non-routine writer
  has qualified.
- Current owner-binding fits contain an association component but spill too
  broadly.
- G4h/G4k and the branch-depth work are useful supplied/scaffolded ceilings,
  not autonomous connected learning or traversal.
- No completed run establishes a positive increasing-lifetime slope.
- The static brief is a carrier diagnostic, not a strong evolving memory
  baseline.

Two fresh writer diagnostics sharpen this further. On the same bank-0 F
corpus, four optimizer seeds produce target completion from `.258` to `.874`;
one new seed raises the target from `.260` to `.685` while also raising the
wrong relation from `.258` to `.669`, and another is nearly null. Two D32/CF
fits likewise raise the target (`.230 -> .790/.736`) but also raise the wrong
relation (`.239 -> .720/.627`). Thus the current writer can install a broad
action habit, but selective conditional binding remains unproved.

The matched lower-learning-rate follow-up closes the simplest heat
explanation. Holding the 12,924-row oracle corpus, rank 8, seed 2, three
epochs, 9,693 steps, and 1,313 native cues fixed, the historical `1e-4`, new
`3e-5`, and new `1e-5` fits have `I_d_frame` respectively `1.921`, `3.078`,
and `1.140`, all with positive paired-owner lower bounds. Their frame spills
are `.416`, `.394`, and `.296` against the same `.03` ceiling, and all are
still labeled `frame-habit`; both new fits also drive control abstention nearly
to zero. Lower heat weakens the same broad habit rather than revealing a
selective regime. Park LR-only sweeps and change the conditional
material/representation. Exact independent audit:
`research_notes/analysis/2026-09-12_lower_lr_writer_terminal_audit.md`.

The matched prefix-mask diagnostic closes the simplest response-only-loss
repair as instantiated here. With the same bank, optimizer seed, rank,
learning rate, 9,693 steps, 749,985 input-token passes, and 1,313 evaluation
cues, masking the prompt/context labels reduced frame spill from `.416` to
`.202`, but it also reduced `I_d_frame` from `1.921` to `.015` and moved the
dose-16 correct conditional probability from `.260` OFF to only `.251` ON.
The owner-bootstrap interval includes zero, and `.202` spill is still 6.73
times the unchanged `.03` ceiling. Thus the prompt-side labels were
carrying both useful acquisition and unwanted global habit; removing them did
not reveal a selective writer. This falsifies this exact conservative mask,
not response-only SFT in general: it also reduced supervised-token passes from
711,213 to 422,925 and omitted 5,376 boundary-crossing ` Owner` tokens. Park
mask-only sweeps. The next writer test must manipulate semantic conditional
structure and, if used, an explicit frozen-OFF preservation objective rather
than merely deleting supervision. Exact terminal memo:
`research_notes/astra_memos/ASTRA_PREFIX_MASK_TERMINAL_2026-09-12.md`;
independent raw-cue recomputation:
`research_notes/analysis/2026-09-12_prefix_mask_terminal_independent_audit.md`.
The latter also found a receipt-checking portability seam: Python 3.9
reproduces every decision and metric, but the reducer's exact float comparison
marks the report invalid over a `2.78e-17` representation difference. Replace
that check with a predeclared numerical tolerance before paper-grade replay;
it does not change this result.

A separate external-oracle mini-Sudoku diagnostic gives the complementary
positive direction. Across three independently initialized adapter-training
seeds, OFF solved `0/16` boards every time; adapters trained on the same 32
correct prompt-solution pairs solved `2/16`, `3/16`, and `5/16`; matched
equal-target-marginal cyclic wrong-board adapters solved `0/16`, `1/16`, and
`0/16`. The seed-level difference-in-differences in exact solves was therefore
`+2`, `+2`, and `+5`. Mean native partial-score useful-minus-corrupt differences
were `.297`, `.357`, and `.407`. Both new seeds pass the result-blind rule that
useful must improve over OFF and beat corrupt by at least one exact solve.

Four evaluation solution grids overlap training, and one (`1900055`) is among
the new useful solves; excluding that ID leaves useful exact counts `2/16`,
`2/16`, and `4/16` versus corrupt `0/16`, `1/16`, and `0/16`, so the directional
result does not depend on the overlap. Material, budgets, episode IDs, model
pins, probe settings, and OFF outputs match across seeds; seeds 1 and 2 ran the
two material arms sequentially on the same respective GPU. This supports only
**repeatable directional material transfer at this 16-board resolution**:
correct content changes later first actions beyond common ACT/full-grid format
learning. Absolute success is still weak, the material is external-oracle
rather than child-authored, the panel is reused across optimizer seeds, and
the three seeds are the replication units—not 48 independent trials. It is not
a selective writer, sleep, parenting, or generalization result. Exact builder
capsule:
`research_notes/astra_memos/ASTRA_BEHAVIOR_REPLICATION_TERMINAL_2026-09-12.md`;
independent terminal audits:
`research_notes/astra_memos/receipts_20260912/astra_replication_claim_review_20260912.md`
and
`research_notes/analysis/2026-09-12_mini_sudoku_three_seed_terminal_watcher_audit.md`.

The first frozen V10R1 W0 execution remains a zero-step infrastructure
`NONREPORTABLE_ABORT`: Triton's first native build could not find Python.h.
A prospective native-build repair then sealed compiler/header/Triton evidence,
passed 60 node tests, and launched a genuinely new root under the first
controller's original deadline while leaving that failed root untouched.
Attempt 2 completed all four clean-base 256-step fits and all 1,504 evaluation
requests, but it still does not answer W0. Its positive oracle control is
invalid: all 256 oracle outputs consumed 32 tokens without EOS, were marked
truncated, and parsed to no action, yielding `oracle_BA=0` in every cell.
Separately, terminal replay fails because `launcher.out` was sealed as empty
and then changed when the controller wrote its returned report to stdout.

The fitted cells descriptively also fail per-key optimization, selective
binding, spill/locality, and aggregate interface gates; oracle failure did not
cause those values. But the failed positive control and failed official replay
make them non-promotable: attempt 2 is neither a W0 pass nor a reportable
negative. Preserve both roots. Exact audits:
`research_notes/analysis/2026-09-12_v10r1_w0_terminal_infrastructure_abort_audit.md`
and
`research_notes/analysis/2026-09-12_v10r1_w0_attempt2_terminal_assay_and_seal_failure_audit.md`.

Two bounded OFF-only development diagnostics then isolated another upstream
problem without repairing W0. On the 64 already-inspected calibration items,
only Qwen chat rendering plus an explicit one-line response contract restored
the motor interface: `61/64` outputs were valid and `45/64` correct. Chat alone,
raw plus the same explicit contract, and raw generation extended to 256 tokens
all produced zero valid outputs. Removing the other 15 table rows did not
restore faithful use of the supplied relation: the replayed single-row
diagnostic produced `58/64` valid but only `32/64` correct outputs, with `58`
literal `ACT: a1` responses and six incomplete `ACT: a` responses. Thus table
search is not the sole remaining defect; the surface did not actually make the
model follow the supplied row. The single-row run reuses development items,
lacks candidate scoring, and is explicitly non-qualifying. It cannot release a
fit or substitute for the inherited oracle gate.

A final development-only instruction variant then exposed a much narrower
failure. It told the model explicitly to copy the action from the one supplied
row. Strictly, it still failed: only `32/64` outputs were valid and correct.
But the confusion was perfectly target-conditional: all 32 `a1` rows produced
exactly `ACT: a1`, while all 32 `a0` rows produced `ACT: a a` (31) or
`ACT: a` (1), with zero truncations. This is strong diagnostic evidence that
the child was conditioning on the supplied row while the artificial `a0`
generation surface failed asymmetrically. It is not a qualified oracle pass,
but it changes the next action from more prompt search to a carrier/interface
repair: score both complete candidates and test balanced, base-executable
action names under complementary maps.

The next fit-eligibility control must therefore use fresh opaque identifiers
and forms, one answer row per held query, the calibrated chat boundary, an
explicit non-answer-bearing instruction to follow the supplied row, balanced
base-executable action names, and both strict generation and two-candidate
scoring. Per root-map, each modality must reach at least `15/16`; aggregate
strict validity must reach `61/64`, with zero truncation or multiple actions
and complementary-map redirection. Until that fresh canary passes, no V10R2
writer fit is eligible. Exact watcher audit:
`research_notes/analysis/2026-09-12_exact_row_positive_carrier_gate_audit.md`.

The terminal B0 scout established one uninterrupted quarantined plumbing path:
exact ACT-before-record joins, a 66-item child-body-only fit, save, canary,
adapter reload, probes, and terminal exit. It did not acquire the intended
first-person record behavior: only 1/66 admitted B records was first-person and
post-neutral articulation was zero both on and off. It also exposed two
independent pairing failures. First, model-visible wall-clock seconds differ
across arms: the first generations match byte-for-byte, then `alive 27s`
versus `alive 26s` changes the prompt before the write and the trajectories
split. Second, even the same frozen base, identical prompt bytes and identical
explicit seed produced different output bytes in a neutral replay. Thus the
runtime's explicit seeding is not demonstrated byte-replay-deterministic.
Paper-grade paired runs must freeze/remove runtime text and either certify
byte-replay-deterministic inference or use an immutable exogenous tape, with
prompt/output hashes checked at every paired step. Exact evidence:
`research_notes/2026-09-12_b0_attempt2_terminal_audit.md`.

The subsequent fixed-lesson P0 material scout completed all 64 paired
Reasoning Gym schedules in both arms, with unchanged local base hashes and no
execution failure. It generated abundant public experience: the lesson arm
recorded 1,903 measured actions and 1,913 post-outcome continuations; sham
recorded 1,627 and 1,632. Yet the strict source judge admitted zero grounded
child records in either arm. `missing-first-person-action` accounted for
1,812 lesson and 1,556 sham rejections. Across schedules the lesson caused
4.31 more measured actions per episode, while its mean best displayed score
was only `.0209` higher (lesson higher on 14 schedules, sham on 13, 37 tied).
The frozen writer preparation therefore returned
`PAIRED_SKIP_INSUFFICIENT_MATERIAL` and ran zero optimizer steps.

This is a failure of the exact static lesson -> child transcription path, not
a failure of grounded action--outcome experience itself. Both ledgers retain
the executed actions and public outcomes needed by S. The next parenting test
should ask whether adaptive, target-blind process diagnosis changes a child's
own plan and later action (`P0-COACH`); it should not make brittle first-person
record syntax the intelligence claim. The S writer should continue to use
mechanically joined public events, with child reflections as optional grounded
enrichment rather than a prerequisite for factual experience.

A terminal coached source-replay diagnostic then made that boundary sharper.
For the first four measured actions in every one of the 64 schedules per arm,
the frozen base was shown the exact historical post-outcome prompt plus an
explicit instruction to quote the submitted action and displayed score in a
short first-person record. All `512/512` requests completed, but the unchanged
judge admitted `0/256` lesson and `0/256` sham outputs. The lesson rejection
counts were 233 missing-first-person action, 15 unsupported first-person
context, seven unsupported reference-answer claims, and one action mismatch;
the sham counts were 249, five, and two respectively. Representative outputs
continued task-level strategy narration and sometimes proposed a new `ACT`
instead of recording the supplied event. No output echoed the coach. The run
performed no new world action and no training.

This closes further NOTE-format prompt search for the current route. It does
not imply that the child ignored outcomes or that SLEEP lacks an authentic
source: the authoritative action and public outcome already exist in the
ledger. It establishes only that even direct coaching did not make this model
reliably serialize those events into the preregistered prose form under the
historical contexts. No adapter may be fit from this replay, and no later
factual S gate should depend on child-authored transcription. Parenting is
therefore evaluated through changed plans and authoritative actions, while
SLEEP receives mechanically joined events and treats faithful reflection as
optional enrichment.

The bounded historical raw-wake fork is terminal and closes that engineering
bridge as a useful route. It fit 32 exact child continuations generated under
the old fixed lesson and 32 corresponding continuations generated under the
active sham, removed teacher text from the zero-loss context, and probed both
adapters after parent removal. All four OFF/ON conditions solved `0/16`
mini-Sudoku boards. The common OFF partial-score mean was `.1125`; lesson ON
fell to `.0475` and sham ON to `.01055`. The positive difference-of-gains
(`+.03695`) means only that lesson material degraded less than sham material;
neither improved on OFF.

This is a one-seed package-utility negative, not a general negative parenting
result. `63/64` selected continuations were pre-feedback, only two lesson and
three sham chunks contained an accepted action, all ten selected mini-Sudoku
chunks were unsolved, teacher dose differed (`203` versus `158` tokens), and
supervised target passes differed (`12,867` versus `16,080`). The current
action outcome was not a training target. Do not repeat this historical
package without a new informative hypothesis. It cannot establish
experiential action--outcome learning, DREAM/SLEEP compilation, isolated
parenting, or repeatability. Terminal memo:
`research_notes/astra_memos/ASTRA_RAW_WAKE_FORK_TERMINAL_2026-09-12.md`;
result-blind design audit:
`research_notes/analysis/2026-09-12_p0_raw_wake_material_fit_probe_audit.md`;
independent terminal recomputation:
`research_notes/analysis/2026-09-12_p0_raw_wake_fork_terminal_watcher_audit.md`.

Before another parenting-derived fit, first establish that an answer-free
process lesson helps while it is visible. The cheapest scout compares the
fixed `FORM_CHECK -> CONSTRAINT_LEDGER` card with a token- and opportunity-
matched sham on the same first-action mini-Sudoku tasks, while a separately
frozen no-teacher run locates both arms relative to ordinary behavior. Report
native first-action score/solves and direct visible-constraint diagnostics;
thought length or lesson imitation is never success. Without the no-teacher
anchor, `process > sham` can again mean only that sham harmed more. Even a
positive result establishes immediate static instruction utility, not adaptive
parenting, internalization, or SLEEP. Prospective watcher audit:
`research_notes/analysis/2026-09-12_static_parent_competency_watcher_audit.md`.

That exact static comparison is now terminal (`SEQ-077`) and its primary
endpoint is null: process and sham each solved `1/16` boards on the first
action. The process card produced more syntactically valid full-grid actions
(`7/16` versus `4/16`) and a higher zero-filled partial score (`.19258` versus
`.11875`), with exactly matched 97-token packages and nearly matched generated
tokens (`1,079` versus `1,068`). This is a bounded teacher-present format
signal, not useful-teaching evidence. Independent grid review found that all
three extra complete-format outputs still violated puzzle constraints; the
gain was completion/marker placement, not constraint checking. A later
explicitly post-hoc no-teacher anchor scored `0/16`, strict format `3/16`, and
zero-filled mean `.08438`, versus process `1/16`, `7/16`, `.19258` and sham
`1/16`, `4/16`, `.11875`. It used a prompt shorter by 97 tokens per question,
so it is descriptive only. Both teacher arms sitting above that anchor does not
isolate the process lesson, and the process-versus-sham primary tie remains.
Therefore the visible-lesson utility gate remains unpassed: do not fit this
card into a child
or scale it into childhood. A new lesson earns a parenting fit only by
improving a prospectively frozen useful action/constraint endpoint relative to
both matched sham and no-teacher, without sham damage manufacturing the
contrast. Terminal builder memo:
`research_notes/astra_memos/ASTRA_STATIC_COMPETENCY_TERMINAL_2026-09-12.md`;
anchor memo:
`research_notes/astra_memos/ASTRA_NO_TEACHER_TERMINAL_2026-09-12.md`.

## One ordered evidence ladder

These labels localize failures; they are not seven independently powered
paper claims. The minimum decisive paper program is only three studies:

1. qualify one selective conditional writer (`W0`), with `W1` reduced to one
   old/new coexistence canary;
2. run one two-cycle `M-core` study that combines an authentic child
   action--public-outcome source, a necessary pre-blueprint child DREAM
   organization decision, and SLEEP-dependent delayed old-plus-new action;
   use standalone `S` only as a one-to-three-root feasibility gate; and
3. run one five-branch `L-core` lifetime study (`P-RUN`, `P-FROZEN`,
   `N-RUN`, `N-FROZEN`, `P-TEXT`), where `N` is the matched no-teacher child;
   active sham remains only in upstream lesson qualification.

Compression remains a downstream semantic rate--distortion endpoint after
connected utility, not a prerequisite for starting M/L. Detailed W/S/M
subgates below remain valuable falsifiers and receipts, but they should not
multiply into separate confirmation populations unless a stronger adjective
is still worth its compute. Independent minimum-program audit:
`research_notes/analysis/2026-09-12_think_dream_sleep_minimum_decisive_program_audit.md`.

### W0 — selective supplied writer

V10R1 did not close this gate: attempt 1 was a zero-step infrastructure abort,
and attempt 2 has both an invalid positive oracle and a self-invalidating
terminal seal. The completed interface and single-row development diagnostics
diagnose the response surface but cannot promote either attempt. Any later
V10R2 must remain a prospectively frozen assay/evidence repair with the
training recipe and
thresholds unchanged. It still asks only whether one fixed rank-8 writer
recipe, evaluated through four root-map adapter fits, can carry several
conditional native actions under held renderings without converting them into
a global habit or damaging the ACT interface.

The next eligible W0 experiment is the fresh semantic-action V10R2 `Q0`, not a
frame-memory repair. Its exact-row OFF carrier first tests direct copying and
full-candidate preference between two real organism actions, `-mem2reg` and
`-gvn`, on four fresh root-map cells. Every cell must independently reach
15/16 correct in both generation and scoring, with the frozen validity,
redirection, native-interface, custody, and replay conjunction. Failure seals
an assay-invalid zero-fit result. Only a complete carrier pass automatically
releases exactly four new clean-base canonical-query fits. All four fitted
cells must then pass W0 conjunctively; roots/maps are not independent learners
and cannot be pooled or majority-voted.

If that canonical semantic W0 fails, classify it before choosing a repair.
Use semantic cross-view `X0` only for exact-train storage with failed fresh-form
extraction. Use an additive frozen-OFF KL anchor, trained on a bank disjoint
from every locality evaluation prompt, only when acquisition/extraction works
but held locality fails. Run the repaired rank-8 `Q0/X0/QA/XA` 2x2 only if
both defects remain. Save step 128 and 256 from the same fits and keep exact-
train scoring, fresh-held scoring, strict generation, and spill/wrong-root
panels separate so the outcome is labeled `STORAGE_FAIL`,
`STORED_NOT_EXTRACTABLE`, `EXTRACTABLE_INTERFACE_FAIL`, or
`SELECTIVE_BINDING_WITH_SPILL` rather than a generic writer failure. The old
factorial draft is not executable unchanged: it contains stale artificial
targets, an unresolved request denominator, anchor/evaluation overlap, and a
memory-gradient multiplier that confounds preservation with lower
acquisition. Current decision audit:
`research_notes/analysis/2026-09-12_selective_writer_next_experiment_audit.md`.

The negative prefix-mask result is not a fifth recipe arm. It is evidence that
lowering prompt-side supervision alone trades away acquisition before it
solves locality. The later conditional treatments ask higher-information
questions only after canonical W0 localizes the defect: whether the same
relation is extractable across semantic views, and whether preserving the
frozen base distribution outside the keyed condition prevents a learned
relation from becoming a global action habit.

A pass establishes supervised seen-key conditional-policy carriage only.

### W1 — cumulative-replay coexistence

If W0 passes, fit identity-disjoint NEW-only banks and clean-base cumulative
`OLD+NEW` replay banks. Apply the symmetric OLD and NEW `KMG`, per-key,
generated-BA, interface, and per-key orthogonality rules already frozen in
`2026-09-11_decisive_evidence_path.md` Section 3.

This tests whether two supervised banks can be reconstructed together. It is
not sequential or unrehearsed retention.

### S — authentic action/outcome source

Do not use the success-selected final `ACT` from the old lived-mirror assay:
situation alone predicts that target, so the writer can ignore the outcome.
The smallest repaired source admits a balanced subset of the child's actual
initial actions and public outcomes under opaque situations, then SLEEP renders
only two reversible views:

```text
situation + executed action -> public outcome
situation + desired outcome -> executed action
```

Pair TRUE with `OUTCOME_SHUFFLED` over exactly the same event identities,
actions, surfaces, target marginals, dose, seed, and node. Within each
situation, shuffle only outcome donors so action and outcome become independent
while their counts remain fixed. Require authentic child coverage of both
actions before admission; do not force or synthesize a missing action. Both
held forward prediction and inverse native-action use must beat SHUFFLED while
passing GOLD/TEXT validity, interface, non-harm, spill, and wrong-root gates.
The exact proposed geometry and stop rules are in
`research_notes/analysis/2026-09-12_s_authentic_action_outcome_source_design_audit.md`.

Three disjoint roots are only a feasibility block: even 3/3 positive has
one-sided sign probability `1/8=.125`. A paper-facing source claim needs the
same frozen assay on eight roots, with at least 7/8 joint-positive
forward/inverse contrasts (`9/256=.0352`). A pass says that preserving the
within-event public-outcome binding improved seen-situation relation use and
later goal-conditioned action. It does not yet say the child discovered a
credit rule or formed connected knowledge.

### M — two-cycle connected relay

Use a smaller successor to Learned-PCFL V5, after CPU root proofs and exact-
text DEV:

```text
child actions -> public outcomes -> grounded old atoms
child proposes a two-atom link -> a public co-use action verifies necessity
SLEEP-1 -> sterile reset
starts identical in every non-goal field; goal bytes differ -> different paths/actions
old memory selects which experiment is informative
child precommits two hypotheses and an outcome-to-row map -> acts -> outcome
SLEEP-2 writes one cumulative old+new adapter -> sterile reset
delayed goal requires exactly one old and the new row
```

The connection proposal must precede visibility of the support-action handle,
menu, arguments, or later goal; otherwise the interface supplies the relation
the child appears to discover. Every positive read must also carry a byte-exact
receipt from training row through mounted carrier and raw reader output to
actor-visible bytes. Run actor/reader without the oracle, generator, theorem,
compiler receipts, hidden truth, scorer, or expected trace in their process;
use more exchangeable first-read candidates than the read budget; and require
catalog-order/surface invariance plus semantic-twin redirection. Phase C needs
two equally supported old relations that imply different maximum-information
actions, so the query, experiment, selected outcome row, and delayed action all
redirect with old content. Exact adversarial review:
`research_notes/analysis/2026-09-12_connected_relay_scaffolding_adversarial_review.md`.

The compiler may select a precommitted branch after the outcome and verify a
pre-outcome child link proposal. It may not originate or repair either. The
first exact M draft failed independent review before spending a GPU-hour: it
tested cue polarity rather than a crossed action--outcome contingency, exposed
useful DREAM links through endpoint syntax, omitted a truthful outcome
carrier, allowed nuisance coincidence to masquerade as a correct write, and
lacked an equal-work second-SLEEP control. That draft is superseded.

The repaired v2 candidate stages six fits per successful root:

```text
SLEEP-1, run first
  FULL_OLD
  SOURCE_DERANGED_OLD
  DREAM_DERANGED_OLD

SLEEP-2, only after every S1 gate passes
  FULL_NEW_h0
  FULL_NEW_h1
  FULL_OLD_PLUS_PAD
```

`FULL_OLD` is written from the child's authentic repeated actions and public
outcomes plus its pre-blueprint link choices. `SOURCE_DERANGED_OLD` preserves
the same actions and global outcome counts but makes action and outcome
independent within one opaque situation. `DREAM_DERANGED_OLD` preserves every
authentic source row but binding-swaps the child's two admitted links into
schema-, hit-, and dose-matched wrong links. Source is therefore identified at
Phase C and DREAM at Phase B; neither corrupt arm is spuriously required to
fail the later chain.

The DREAM choice is now eight endpoint-, type-, degree-, age-, frequency-, and
joint-success-matched lanes. Only earlier joint-versus-single-component public
evidence distinguishes the two necessary links. Report the child against
endpoint-join, frequency/recency, exact `1/28` random selection, and a declared
CPU necessity ceiling. This can support child-emitted, experience-conditioned
organization; call it DREAM intelligence only if it beats every frozen
non-oracle policy.

The two truthful public outcomes are potential-outcome twins inside one
independent root and receive separate cumulative S2 carriers.
`FULL_OLD_PLUS_PAD` is a clean-base, same-initialization/data-order/dose second
fit with no new row. The actor sees only typed queries over public anchors; a
fixed 32-candidate recognition bank remains inside the reader. A four-read
atoms-only exact-text ceiling shows that the atoms contain the answer while
the child link saves one of the three allowed reads. The admission truth table
forbids nuisance outcomes from creating a row even when their bit happens to
equal the hidden target.

This v2 closes the previous findings on paper but remains a **candidate pending
fresh independent re-audit and CPU/exact-text closure**, not permission to
fit. Canonical candidate:
`research_notes/analysis/2026-09-12_m_core_minimal_exact_two_cycle_design_v2.md`.
Prior audit:
`research_notes/analysis/2026-09-12_m_core_revised_three_condition_adversarial_audit.md`.

Release three endpoints separately:

- **M-E2 connected carriage:** both atoms are mechanically necessary; authentic
  link beats binding-matched DREAM derangement and same-build read permutation, with off,
  wrong-life, spill, and interface controls.
- **M-E4 goal traversal:** two incompatible goals over identical public starts
  change the first relevant query, complete path, and action; cuts remove value
  and truthful twins redirect it.
- **M-E5 expansion:** the authentic crossed signal changes the information-seeking action;
  the public outcome selects a precommitted new row; one cumulative adapter
  retains old content and later uses old+new together. No-write, matched sham,
  old-cut, reachout-off, adapter-off, and wrong-life must remove authentic
  value. The two separately fitted truthful outcome twins must redirect the
  written row and delayed action. `SOURCE_DERANGED_OLD` must reduce the
  counterbalanced inverse-action endpoint while leaving Phase-B path traversal
  intact; it is not rebuilt at S2 and is not required to fail the final chain.

The typed four-read/read-only-LoRA condition is a mechanistic ceiling. Before
M-DEV, separately freeze a native-policy endpoint using the same adapters and
only ordinary legal memory-query/action APIs, including its exact API, budget,
visibility, parser, and success rule. It is an external-validity endpoint, not
a hidden post-hoc gate. Typed success supports a bounded mechanism relay;
reserve the word **agentic** for a separately passing native endpoint.

Do not infer causality from an arbitrary full-chain success rate. Keep the
failure-inclusive CHAIN conjunction and exact interval as descriptive
reliability. The primary source endpoint is the paired root contrast at Phase
C:

```text
FULL_OLD -> authentic crossed source contingency -> inverse action
versus
SOURCE_DERANGED_OLD -> within-situation independent outcomes -> inverse action
```

Expansion is identified separately by truthful `FULL_NEW_h0/h1` versus the
matched `FULL_OLD_PLUS_PAD`, plus old/new cuts. Randomize hidden assignment and
order and use exact paired inference. The staged minimum is CPU/theorem and
exact-text closure, a two-root S1 kill (**6 fits**), a two-root S2 kill only if
S1 passes (**12 cumulative fits**), eight total DEV roots (**48 maximum**),
then one fresh 16-root confirmation (**96 maximum**) only if every
noncompensatory gate survives. Worst-case DEV plus confirmation is 144 fits;
the provisional all-in estimate is `28--60` A40-hours, to be replaced by
measured exact-deck time. A bad source/DREAM design should die in the S1-only
kill below roughly three A40-hours. DEV is never pooled with confirmation;
roots--not twins, fits, goals, or checkpoints--are the independent units, and
failed roots remain adverse zeros rather than being retried or replaced.

### L — increasing-lifetime learning

Use independently raised randomized childhood roots. Historical RP/R2 adults
cannot identify parenting because their childhood packages were not matched.
After deleting the parent, nursery context, stores, indexes, embeddings,
caches, and query state, begin with four deployment branches per root:

- `P-RUN`: parented adult, gated SLEEP continues;
- `P-FROZEN`: matched parented adult, shadow sleeps, no weight promotion;
- `N-RUN`: matched no-teacher adult, gated SLEEP continues;
- `N-FROZEN`: the same no-teacher adult, shadow sleeps only.

At examination cut `Tj`, let `V_c(Tj)` be the fixed equal-weight value for
condition `c`. Define entry-adjusted cumulative value as the time-normalized
trapezoidal AUC of `V_c(Tj)-V_c(T0)` over all seven cuts. The root-level
primary interaction is

```text
D = (AUC[P-RUN] - AUC[P-FROZEN])
  - (AUC[N-RUN] - AUC[N-FROZEN]).
```

This first release is a bounded parenting-by-SLEEP interaction. Test in fixed
order: `P-RUN>P-FROZEN`, then `D>0`. The first rule prevents a positive
interaction caused only by SLEEP harming untaught children. Neither predicate
alone establishes improvement with increasing lifetime.

Use source-disjoint information cohorts rather than repeated visits to a fixed
12-program panel. Preconstruct seven equated parallel exam forms and rotate
their checkpoint assignment across root blocks under a frozen balanced
schedule; every branch within one root receives the same form at a cut. The
primary lifetime clock is exogenous exposure (scheduled information cohorts,
episodes, or action opportunities), never accepted writes or qualified
updates, because acceptance is itself changed by treatment. Accepted-write
count remains a secondary dose diagnostic.

L-DEV runs all five branches, including the prequalified `P-TEXT`, and may
select the horizon from `{128,192,256}` and the plateau anchor from a finite
declared early-cut set using form reliability, task headroom, baseline
behavior, and retention feasibility—not the largest observed treatment
effect. The horizon, anchor, all seven cuts, form rotation, and every endpoint
freeze before confirmation identities exist. At least two baseline increments
precede the anchor and at least three checkpoints follow it. Confirmation also
runs all five branches concurrently on every root; adding `P-TEXT` only after
seeing favorable `P-RUN` roots would condition the comparison on the result
and confound it with calendar/order. The compute-saving alternative is a new
independent baseline-confirmation cohort, not a late branch on selected roots.
Children/root blocks are the independent units; checkpoints, programs, decode
seeds, branches, and adapters are nested observations.

Measure two distinct retention endpoints: inherited childhood-skill retention
on an untouched panel, and retention of a fixed early-deployment information
cohort after later identity-disjoint writes. The second endpoint is eligible
only if that cohort first clears a frozen acquisition floor. Writer rejection
remains an adverse intention-to-treat result: keep the previous adapter and
continue rather than retrying until pass.

Release **increasing-lifetime improvement** only if all of the following
noncompensatory predicates pass under their frozen margins:

- positive absolute late `P-RUN` slope after the plateau anchor;
- positive `P-RUN` anchor-to-terminal gain;
- positive late-slope advantage over the qualified evolving-text baseline;
- childhood-skill noninferiority;
- acquired early-deployment knowledge noninferiority; and
- terminal practical superiority over the baseline.

A positive AUC interaction with a failed late-life conjunction remains only a
parenting-by-SLEEP result; it may reflect a transient bump or slower decline.

The strong parent is allowed to adapt throughout one child's childhood using
a persistent root-local child record; it is not reset between lessons. For
independent confirmation roots, however, start the same frozen strongest
teacher/pedagogy snapshot in a fresh provider session with an empty private
record. Otherwise launch order and earlier children change later treatments,
and the parent—not the child block—becomes the replication unit. A one-time
parametric bootstrap is a distinct pre-child intervention and is omitted from
the minimum unless feasibility requires it; if used, it must be identical in
P and N and the lifetime claim becomes conditional on that bootstrap.
Deployment SLEEP must extend the sealed adult adapter without retaining a
hidden childhood text store. Full clean-lineage audit:
`research_notes/analysis/2026-09-12_clean_one_parent_lcore_watcher_audit.md`.
The control-resolution addendum supersedes that audit's SHAM recommendation:
`research_notes/analysis/2026-09-12_lcore_sham_vs_regular_control_addendum.md`.
Use targeted lesson versus active sham versus no-teacher only to qualify one
lesson before childhood. The final no-teacher pair estimates the total exact
parenting package; it does not isolate one correction sentence. A secondary
sterile raw-base exam may locate absolute level but does not enter `D`.

No exact confirmation root count is currently defensible. Repeated cuts reduce
measurement error inside a root but do not increase learner `N`. Before
outcome-bearing DEV, freeze practical superiority/noninferiority margins,
alpha, desired joint power, failure rules, batch size, and a hard resource
cap. Size confirmation from root-level nuisance variance/covariance under a
blinded mean-free internal-pilot rule, increasing only in frozen batches. If
the required precision exceeds the cap, report `NOT_ESTABLISHED`; do not turn
episodes or checkpoints into pseudo-replicates. Full statistical audit:
`research_notes/analysis/2026-09-12_lifetime_statistics_watcher_audit.md`.

### B — strong evolving text baseline

Before any `P-RUN` result exists, seal the entire `P-TEXT` branch:
implementation, roots, tapes, updater, retrieval policy, resource budgets, and
endpoints. It starts from the same parented adult checkpoint, keeps the
childhood LoRA frozen, begins with an empty text store, and uses a prequalified
public-only evolving updater plus target-blind retrieval over its own eligible
experience. Run it concurrently with the other four branches on every
confirmation root. If compute requires conditional execution, use a new
independent baseline-confirmation cohort after the factorial gate; do not attach
ordinary intervals to a late branch on favorable selected roots.

`P-RUN>P-TEXT` is a whole-system on-policy comparison, not proof that LoRA is a
better carrier. Carrier comparison remains `TEXT_SAME_SEMANTICS`. Do not say
the text baseline saturated unless late change is equivalent inside a frozen
band while oracle headroom remains and doubling its retrieval budget also
falls inside that band. A paper-facing baseline result is conjunctive: baseline
validity, any claimed plateau/headroom, positive learner late slope, slope
advantage, retained old competence, and a terminal practical margin must all
pass.

Only these two text objects need powered paper-facing endpoints. Recency, raw
BM25/RAG, static brief, and an evolving-RAG candidate belong in a disjoint DEV
qualification roster, not as separate lifetime arms. Match public opportunity,
actor tokens, action opportunities, randomness addresses, and checkpoint cuts;
report input tokens, retrieval work, storage, latency, fits, and energy rather
than claiming equal compute. The native text branch should expose at most one
query and 1,024 returned tokens per continuation, with a separately forked
2,048-token sensitivity required only for the word **saturated**. Full audit:
`research_notes/analysis/2026-09-12_baseline_compression_full_paper_watcher_audit.md`.

### C — compression stays downstream

No W/S/M/L pass implies physical or semantic compression. Do not use shorter
DREAM prose as the metric. The already-closed rate--distortion design begins
with the zero-model same-denotation crossover and is run only after connected
utility qualifies. This keeps compression in the objective without making it
an upstream blocker for action/outcome learning.

At the current roughly 80.8 MB rank-8 adapter size, the experiment cannot
honestly claim physical storage compression. The bounded downstream endpoint
is instead prospective **semantic-code compression**: charge the selected
schema, decoder, index, metadata, and residuals; require byte-exact round trip;
beat both packed same-denotation text and its ordinary-codec version at two
later loads; and preserve the already-qualified connected utility. A failure
removes only the compression clause, not W/S/M/L.

## Reuse instead of another giant experiment

The missing bridge between the two-cycle relay and the lifetime study is
successive writes in one living lineage. Put two predeclared expansion cycles
into the lifetime study's open-plumbing DEV root, using the same frozen
compiler/writer/read policy and a task schema compatible with L:

1. complete cycle 1 and test its delayed goal;
2. perform an unrelated identity-disjoint write and re-test old carriage;
3. complete cycle 2 and test a goal requiring old plus new content; and
4. after cycle 1 and at terminal, create sterile descendants with adapter-off,
   cyclic wrong-root, and outcome-deranged mounts.

This reuses the lifetime infrastructure and adds mostly inference only when
both writes already belong to the lifetime schedule. It can show
repeated transactional carriage and personal-content dependence. It still
does not show that connected traversal mediates the lifetime slope; omit that
mediation claim unless a separate link-specific lifetime intervention is run.

## Maximum combined claim if every stage passes

The strongest honest result would be:

> In this finite benchmark, a child converted its own public action outcomes
> into grounded and functionally connected LoRA-carried records, used the same
> carrier differently under different goals, selected an informative action,
> incorporated its outcome into a cumulative old-plus-new write, and later
> used the new relation with older knowledge. Across independently raised
> randomized childhood roots, continued gated consolidation then produced a
> positive entry-adjusted cumulative-value interaction in parented adults
> relative to their frozen twins and matched untaught siblings. Under the
> separately frozen late-life release, the parented running learner improved
> absolutely after the plateau anchor, retained early competence, and exceeded
> the exact qualified evolving-text configuration in late slope and terminal
> practical value over the measured horizon.

Even this does not establish graph geometry inside weights, physical
compression, indefinite improvement, equal-compute optimality, universal
parenting efficacy, population generality, or transfer beyond the tested
model, children, and task families.

## Immediate information-efficient order

1. Let the exact inherited pretest roots `R2_B_seed1`, `R2_B_seed3`,
   `R2_B_seed4`, `R4_B_seed601`, and `RP_B_seed400` under
   `/localhome/local-rohing/v6_out/pretest_write_ab/` finish unchanged. Consume
   only terminal `summary.json`; do not restart or promote partial panels.
2. Preserve both failed V10R1 roots and every development diagnostic. Run the
   fresh semantic-action exact-row generation-plus-scoring carrier; fit
   nothing if it fails. If it passes, run exactly four canonical `Q0` V10R2
   fits. Route any failure by storage/extraction/locality subtype, and run at
   most the one bounded repaired writer screen above. W1 is eligible only
   after a sealed/replayed W0 pass.
3. Run one old/new cumulative-replay coexistence canary. It is a waste-prevention
   gate for M, not a separate powered paper result.
4. Repair M-core's crossed source law, evidence-only DREAM decision,
   reader-observability theorem, outcome-twin S2 carrier, nuisance/admission
   truth table, and matched old+pad S2 control. Close those on CPU and four
   exact-text roots. Then run two LoRA roots S1-first; fit S2 only for roots
   that pass the prospectively frozen S1 gates. Reuse artifacts for adapter-off,
   wrong-life, row cuts, semantic twins, catalog permutations, and other valid
   inference-only interventions. This integrates authentic action--outcome
   evidence into the end-to-end mechanism without funding a separate source
   population.
5. Only if both M-core kill roots have the predeclared direction and every
   noncompensatory trace gate passes, freeze M and run one fresh jointly powered
   confirmation cohort. Qualify the single evolving-text system in DEV.
6. In parallel, run the no-write `P0-COACH` adaptive-parent test on fresh
   homologous tasks. Only the child's own plan reaches the apply task; no
   parent text or answer does. Do not retry the failed static record lesson by
   increasing LoRA heat, because no eligible record reached the writer.
7. While M is unresolved, rehearse only CPU/open five-branch lifetime plumbing,
   equated form rotation, retention panels, and the two-cycle bridge. Then run
   one five-branch L-DEV and one fresh confirmation cohort under the blinded
   root-level sizing rule.
8. Run semantic rate--distortion only after connected utility is established;
   do not put physical compression or the word `saturated` on the critical
   path.

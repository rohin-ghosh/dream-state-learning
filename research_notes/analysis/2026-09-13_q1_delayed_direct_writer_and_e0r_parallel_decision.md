# Q1 after Q0: test delayed conditional formation, while E0-r tests the carrier

**Date:** 2026-09-13 UTC  
**Role:** fresh independent writer-design review  
**Scope:** research-note design only. I did not edit builder code, inspect or
alter a live job, run a model/tokenizer, train an adapter, or touch a GPU.

## Decision

The smallest defensible **direct Q0 successor** is the independently proposed
`Q0-FULLDOSE-v2`, which I refer to below as `Q1_DELAYED_DIRECT` to keep its
scientific namespace separate from Q0:

1. preallocate three untouched opaque roots before any new output;
2. on every root, run complementary pairwise `P_AUTH` and `P_DERANGED` to the
   full 128-update dose; and
3. retain all three results regardless of the first root's outcome.

Keep Q0's pairwise common-prefix loss, rank, learning rate, dose, panels, and
final gates. Change one thing: **the update-one four-item monotonicity test is
diagnostic, not an efficacy stop**. No scientific conclusion is taken before
the full dose. This is a new contract on new roots, never a repair, completion,
rerun, or pass of Q0 root 1.

In parallel, run the already designed `E0-r` fixed-rendered EVENT carrier with
ordinary response-masked causal-LM loss. Q1 and E0-r are not competing versions
of one claim:

- Q1 asks whether ordinary multi-step LoRA optimization can eventually form a
  finite input-conditional action policy despite a locally conflicting first
  update.
- E0-r asks whether a factored, goal-blind memory process can store and
  candidate-freely emit complete event records that a clean actor can use.

The direct experiment is exactly six planned fits across three paired roots.
The already observed unary update is retained as a diagnostic, but no new
unary fit is needed: its “failure” is explained by the same loss geometry, and
the two-map XOR endpoint is a stronger test of opaque-tool conditioning.
E0-r is two fits on one excluded root. With idle devices,
parallel execution gives both the objective diagnosis and the representation
diagnosis without serializing the paper path.

## What Q0 actually diagnosed

Q0 did not observe a completed direct writer. It observed one optimizer update
per arm. The sealed first quartet had initial legal-action margins

```text
d = z_mem2reg - z_gvn
  = [5.6310, 7.2858, 4.9575, 5.4008].
```

The pairwise logistic loss derivative magnitude for row `i` is
`sigmoid(-s_i d_i)`. Applying the registered maps gives:

| arm | signs | derivative magnitudes, in row order | almost all update weight lands on |
|---|---|---|---|
| AUTH | `[+,-,-,+]` | `.00357, .99932, .99302, .00449` | rows 2 and 3 |
| DERANGED | `[-,+,+,-]` | `.99643, .00068, .00698, .99551` | rows 1 and 4 |
| UNARY | `[+,+,-,-]` | `.00357, .00068, .99302, .99551` | rows 3 and 4 |

This is ordinary hard-example prioritization. The base already strongly chose
`mem2reg` on every row. Rows whose target was `mem2reg` therefore contributed
almost no loss; rows whose target was `gvn` contributed nearly all of it.

The AUTH signed-gradient Gram matrix confirms the consequence. Combining it
with the actual logistic derivative magnitudes above gives first-order signed
directions proportional to

```text
AUTH:     [-5158.48, +5332.57, +6334.11, -5394.95]
DERANGED: [+4869.02, -4865.30, -5680.92, +5105.48]
UNARY:    [-4909.09, -4987.51, +6745.52, +5888.49].
```

The common factor of one quarter and learning-rate sign do not affect these
signs. Thus the deterministic loss gradient itself is expected to help two
rows and hurt two at update one. This reproduces the observed `2/4` projection
pattern without appealing to insufficient rank, a bad learning rate, opaque
identifiers, numerical error, or LoRA dropout. DERANGED moves the complementary
hard pair; unary moves its two initially wrong rows. The unary `2/4` result is
therefore **not evidence that opaque tools cannot be learned**. It is another
one-update result under the same saturated loss geometry.

The canary was valid for its registered question—whether the very first
sampled update improves every conditional margin simultaneously—and Q0
correctly failed it. But that question is stronger than whether a nonlinear
LoRA fit can form the conditional mapping after repeated updates. Standard
zero-B LoRA initialization makes the distinction still more important: the
first update changes the initially active factor; later updates can change both
factors and hence the conditional feature geometry. Q0 never measured that
later regime.

This diagnosis is why Q1 changes the lifecycle rather than sweeping a scalar.

## Why not change to ordinary CE on the same direct ACT target?

Do not spend a fit on a `P` versus full-vocabulary `V` objective comparison on
this action surface. Q0 already measured the relevant initialization:

- legal branch mass `M` had minimum `.9999518`, median `.9999956`, maximum
  `.9999992`;
- median `norm(g_V-g_P)/norm(g_P)` was `.0126`; and
- median cosine between the gradients was `.9999229`.

Since `L_V-L_P=-log M`, vocabulary CE on the divergent action token has almost
the same gradient as pairwise CE here. It does not repair the hard-example
conflict.

Full-response masked CE over `ACT: ...` would additionally train shared
syntax, suffix, and EOS tokens. Earlier repository results show that such
shared response-language pressure readily installs global action dialects and
fixed routines. That is the failure Q0's common-prefix pairwise objective was
introduced to avoid. Reintroducing it after Q0 would be a low-information
regression, not a principled successor.

Pairwise/contrastive training remains the cleanest direct-action objective.
What Q0 did not test is whether it works after the representation has time to
move.

## Why not gradient surgery now?

The failed AUTH quartet does admit a positive reweighting. Solving
`G a = 1` and normalizing gives approximately

```text
a = [.3002, .2951, .1888, .2160],
```

for which all four first-order signed dots are `+111.80`. This proves the
first-step conflict is not geometrically impossible. It does **not** justify
using those weights: they were derived after inspecting one failed quartet.

An online max-min/MGDA or PCGrad writer could compute such weights on every
quartet, but then the update-one canary would partly be guaranteed by the
optimizer that reads the same gradients. It adds four-gradient cost and a new
algorithm before ordinary multi-step learning has been tested. Keep this as a
prospective successor only if Q1 reaches full dose, reduces its training loss,
and still fails exact conditional acquisition. If used later, allocate fresh
roots and judge only final exact/held/locality behavior, not its constructed
first-step direction.

Likewise, dropout zero, higher rank, higher learning rate, or more dose are not
the first revision. None directly follows from the signed-gradient diagnosis,
and scalar magnitude changes cannot rotate a first-order direction whose signs
are wrong on two rows.

The newer suggestion to transplant the SEQ-113 `3e-4`/320-update recipe is
plausible as a later dose escalation, but it should not be the first successor.
SEQ-113 used a warm-started, full-response, interleaved memory-plus-habit
corpus; Q0 uses fresh zero-B adapters and a decision-token pairwise objective.
Copying only its learning rate and update count changes two scalar knobs while
discarding the batch/corpus conditions under which they worked. SEQ-120 is
encouraging—its authored full-response fit produced complementary conditional
policies, including `32/32` PROSPECT in each map—but it still failed its full
conjunction and is not an objective-matched dose calibration for Q0.

Therefore use the already registered 128-update endpoint first. If all three
Q1 roots show a still-improving, non-saturated exact-acquisition curve at
update 128, that curve can prospectively motivate one longer-dose successor.
If the curve saturates in the wrong policy or spills, more heat is not the
inference.

## Q1_DELAYED_DIRECT: exact experiment

### Prospective roots and states

Before model load, allocate three opaque roots and their optimizer seeds from
one output-blind manifest. The already written Astra proposal chooses
identifier seeds `501/502/503` and optimizer seeds `1/2/3`; those are valid if
they were sealed before any corresponding output. None may reuse Q0 root 1,
its inspected identifiers, a fitted state, or a selected checkpoint.

Every root runs the same two fresh states:

1. `P_AUTH`: the registered tool-by-mode XOR map for all 128 updates; and
2. `P_DERANGED`: its exact complementary map, independently for all 128
   updates.

Use one contemporary `OFF` per root and fresh reloads for every read. Do not
stop roots 2/3 because root 1 fails and do not call them success-conditioned
confirmations. This is a failure-inclusive three-paired-root classification.

### Frozen writer recipe

Retain from Q0:

- `Qwen/Qwen2.5-7B-Instruct@a09a354...` with its full file inventory;
- rank 8, alpha 16, dropout `.05`, all seven projection families;
- zero-B initialization, BF16 base/forwards, FP32 LoRA/gradients/optimizer;
- AdamW `3e-5`, betas `(.9,.999)`, epsilon `1e-8`, weight decay `.01`, no
  scheduler/clipping/TF32/checkpointing;
- natural maximal token-common prefixes ending at `ACT: -`;
- mean four-row pairwise loss per update;
- 32 target-free quartets repeated through 128 updates, or 32 presentations
  per key;
- identical initialization, schedule, input, optimizer, and RNG receipts for
  causally paired states; and
- the exact, held, locality, wrong-root, and native-copy panels.

The only scientific lifecycle change is that an efficacy miss at update one
does not stop a fit. Save and read margin-only checkpoints at updates
`1, 4, 8, 16, 32, 64, 128`; run strict generation and all expensive panels at
128. These checkpoints test the registered hypothesis that conditional
directions emerge after the first optimizer step; they are not selectable.

At update one, preserve the same raw per-row gradients, Gram matrix, actual
delta, observed margins, and FP64 bounds. Gate only integrity: correct source,
mask, update, state, counts, finite arithmetic, exact replay, and lifecycle.
Report the number of per-row directions improved, the mean pairwise loss
change, and whether any initially correct action crossed the decision
boundary. Do not require `4/4`, average it into the endpoint, or use it to
choose a checkpoint.

### Endpoint gates

For each of `P_AUTH` and `P_DERANGED` on every root, preserve the complete Q0
final gates:

- exact: `>=116/128`, class recalls `>=56/64`, validity `>=122/128`, zero
  multiple actions, at least `14/16` key-mode cells at `>=7/8`, and positive
  median ON-minus-OFF signed gain in each target class;
- held: `>=52/64`, class recalls `>=24/32`, validity `>=61/64`, zero multiple
  actions, and at least `12/16` key-mode cells with positive median signed
  gain;
- complementary double-correct flips: `>=112/128` exact and `>=48/64` held;
- native copy `8/8`; and
- for missing-mode (`n=8`), unsupported-mode (`n=8`), neighbor-ID (`n=16`),
  and wrong-root (`n=64`) separately: mean itemwise `|delta q|<=.05`, mean
  itemwise `|delta M|<=.05`, no item above `.10`, mean legality change
  `<=.05`, and mean strict action-identity change `<=.05`; the discrete
  action-change counts are `0,0,0,<=3`, respectively, and mutually opposite
  AUTH/DERANGED wrong-root outputs are `<=3/64`.

No mean across maps, roots, or gates can compensate for a miss.

### Three-root classification and labels

All three roots are planned before outputs and all three run. Each root must
independently pass the same complete two-map conjunction. Report three paired
instances whose root and optimizer seed vary together—not three isolated
estimates of either source of variance and not three IID prompt-level
replications.

Use labels that cannot rewrite Q0 history:

- `Q1_DELAYED_XOR_EXACT_FAIL`;
- `Q1_DELAYED_XOR_HELD_FAIL`;
- `Q1_DELAYED_XOR_SPILL_OR_INTERFACE_FAIL`;
- `Q1_ROOT_DELAYED_DIRECT_PASS`; and
- only if all three planned roots pass,
  `Q1_DELAYED_DIRECT_3ROOT_PASS`.

Every Q1 report must carry Q0's permanent label
`EARLY_XOR_QUARTET_STOP_AUTH` as prior motivation, not as a state Q1 repairs.
A Q1 pass supports only supervised finite complementary conditional action
binding after repeated updates. It is not evidence of own-experience learning,
SLEEP, semantic memory, connection, retention, parenting, or lifetime
improvement.

## E0-r in parallel: the paper-relevant representation test

Run E0-r under the provenance-adjudicated name
`DEV_E0R_FIXED_RENDERED_EVENT_CARRIER`, not “own-experience learning.” Its
payload is endogenous (child action, public outcome), but its canonical EVENT
serialization is exogenous.

Keep the already adjudicated two full-dose arms:

- `RENDERED_AUTH`; and
- `RENDERED_OUTCOME_SWAP`, changing only within-scene outcome bindings.

Keep `OFF`, exact text, and fresh-process unmounted `SHADOW` as zero-fit
controls. Use 16 live, 16 trained-negative, and 16 evaluation-only negative
addresses; four request views; 32 presentations per trained address; 256
updates and 1,024 natural-row forwards per fitted arm; rank 8; and ordinary
equal-length, token-mean response-masked causal-LM loss. Complete both fits
unless integrity fails. First-update field geometry is diagnostic only.

The exact E0-r gates remain:

- `>=29/32` exact complete rows across two seen renderers and `>=14/16` on
  the held renderer, with validity `>=31/32` and `>=15/16` and each action and
  outcome class `>=7/8` held;
- AUTH/SWAP both correct with opposite outcome fields on `>=14/16`, and AUTH
  at least `.20` above OFF held semantic correctness;
- exact `MISS >=15/16` separately on trained-negative and never-trained
  negative handles in both fitted states;
- clean-actor own-map actions `>=14/16`, `>=7/8` per action, at least `13/16`
  AUTH/SWAP action flips, and AUTH at least `.20` above OFF authentic balanced
  accuracy; and
- fresh clean actor, goal-blind memory worker, and byte-matched OFF/SHADOW
  sterility.

E0-r has a two-hour A40 ceiling. It does not enter a child lineage and needs no
replication: it is the excluded carrier ceiling that decides whether M is
worth its ten development fits.

## Joint interpretation and route to M

| Q1 delayed direct | E0-r event carrier | interpretation and next action |
|---|---|---|
| pass | pass | Both direct conditional policy and factored event carriage work. Use EVENT, not ACT, in M because M needs facts and links; keep Q1 as a writer-mechanism result/ablation. |
| fail | pass | The representation factorization mattered: the same broad LoRA class can carry addressed events behind a clean actor even though direct conditional action binding failed. Advance to M on EVENT. |
| pass | fail | Direct policy formation works, but semantic row generation/absence/reader use is the bottleneck. Repair the named E0-r layer prospectively before M; do not substitute Q1 actions for connected knowledge. |
| fail | fail | Neither declared route is ready. Use the terminal subtype to propose a new representation or reader; do not random-sweep rank/LR/dose and do not jump to M. |

After an E0-r pass, freeze its EVENT grammar, reader, writer, and actor
interface. Run the already specified zero-fit four-root route/text closure,
then two M development roots. The claim-bearing M lineage must restore
child-authored semantic EVENT formation **and** child-authored LINK formation;
the fixed E0-r renderer may remain only as a ceiling/control. M must then show
goal-conditioned traversal, an information-seeking action, a second SLEEP,
OLD+NEW reuse, and the matched link/outcome/wrong-life controls before any
connected or expanding experiential-knowledge claim.

Rohin's “no negative paper” direction changes campaign policy, not the meaning
of a frozen result. A failed Q1 or E0-r ends that exact declared recipe. It
does not end the project: the next recipe is newly named, frozen before its own
outputs, and motivated by the failed layer. That is iterative experimental
development rather than post-hoc relabeling.

## Cost and stopping

Q1 plans exactly six fits: two maps x three roots, `768` optimizer updates and
`3,072` natural training-row forwards. The current Astra proposal uses a
conservative 10,800-second per-root controller ceiling, so the hard maximum is
`9 A40-hours`; parallel roots bound model-execution wall time near three hours.
That is a ceiling, not expected busy time—the original Q0 root spent about 23
minutes on audit/OFF plus three one-update fits, and earlier completed writer
fits were much shorter than the ceiling. Report actual reserved, controller,
worker, and GPU-busy clocks separately.

Do not efficacy-stop any allocated root or map. Rerun unchanged bytes only for
an integrity/runtime failure, never an efficacy miss. A valid failed root stays
in the three-root denominator. This costs one extra failed pair in the worst
case but removes success-conditioned replication and gives the failure pattern
the user explicitly asked us to learn from.

E0-r remains two full fits / at most `2.0 A40-hours`. Run it concurrently with
Q1 on a different device. The conservative combined ceiling is therefore
`11 A40-hours`, with about three hours of wall time if all four roots have
separate devices. This is still much cheaper and more diagnostic than placing
ten M fits behind an unknown atomic carrier.

No objective, rank, learning-rate, dose, renderer, seed, checkpoint, or
threshold selection follows within either frozen contract. A result-specific
successor is allowed only as a newly declared experiment with the earlier
terminal visible.

## Evidence inspected

- `research_notes/analysis/2026-09-13_q0_root1_attempt2_terminal_independent_audit.md`;
- `research_notes/astra_memos/ASTRA_Q0_FIRST_UPDATE_STOP_2026-09-13.md`;
- `research_notes/astra_memos/receipts_20260912/astra_q0_attempt2_bounded_review_20260913.md`;
- the sealed/replayed first-quartet scalar and Gram records summarized in those
  files;
- `research_notes/analysis/2026-09-12_pairwise_binding_falsifier_adjudication.md`;
- `research_notes/analysis/2026-09-12_q0_pairwise_falsifier_mathematical_redteam.md`;
- `research_notes/analysis/2026-09-13_conditional_writer_route_decision_memo.md`;
- `research_notes/analysis/2026-09-13_post_q0_failure_endogenous_event_row_gate.md`;
- `research_notes/analysis/2026-09-13_e0_addressed_event_row_builder_handoff.md`;
- `research_notes/analysis/2026-09-13_e0_value_redteam_and_minimum_carrier_gate.md`;
- `research_notes/analysis/2026-09-13_e0r_provenance_thinker_compiler_adjudication.md`;
- `research_notes/analysis/2026-09-13_post_relay_minimum_decisive_benchmark_ladder.md`;
- `research_notes/analysis/2026-09-13_birth_terminal_raw_audit.md` (SEQ-120);
- `research_notes/astra_memos/receipts_20260912/astra_q0_revision_design_20260913.md`;
- `research_notes/THESIS_RAW_ROHIN_2026-09-11.md`, messages 30--31; and
- `research_loop/COORDINATION.md` through the 2026-09-13 04:33 UTC Rohin
  relay.

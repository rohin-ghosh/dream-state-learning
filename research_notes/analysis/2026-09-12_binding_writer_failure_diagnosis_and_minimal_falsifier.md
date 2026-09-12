# Why the writer learns the carrier but not the binding

**Date:** 2026-09-12
**Status:** independent scientific diagnosis and prospective experiment memo.
**Scope:** checked-in evidence plus a read-only inspection of the terminal
fundamental HF-parity result. This memo changes no builder source, launches no
job, and authorizes no claim or mechanism promotion.

## Decision

The leading diagnosis is **common-mode learning without input-conditional
separation**.

The present objectives give every example several mutually reinforcing things
to learn: enter the response dialect, emit `PREDICT` or `ACT`, terminate in the
right way, and put probability mass on a small answer class. The actual binding
is the small residual: different keys must push the same adapter toward
different answers. With balanced labels, any global answer-bias component of
that residual cancels; only covariance between the label and the key-specific
gradient can solve it. The current rank-8 fits reliably follow the large,
coherent common gradient and do not reliably follow that conditional residual.

This reading explains all three otherwise puzzling observations:

1. a global `PREDICT`-before-`ACT` order is perfect across three optimizer
   seeds;
2. legal-answer/candidate mass can rise by almost the maximum possible amount;
   and
3. exact key-conditioned accuracy remains at chance, often through a constant
   answer.

The evidence does **not** show that labels were dropped, that vLLM failed to
mount the adapter, that held wording alone hid a learned map, or that rank is
the first bottleneck. It also does not show that repetition is ineffective:
SEQ-101 increased token presentations but averaged the 16 copies inside the
same 80 optimizer updates, so it was not a 16-fold gradient-dose test.

The smallest informative intervention is a **three-fit, pair-balanced
common-prefix test** on one existing semantic root:

- `V_AUTH`: full-vocabulary one-token CE on the authentic map;
- `P_AUTH`: two-legal-action pairwise CE on the same authentic map;
- `P_DERANGED`: pairwise CE on the exact complementary map;
- one shared `OFF` readout, requiring no fit.

Every optimizer update contains a matched same-tool/same-template `m0/m1`
pair whose correct actions are opposite. The model sees no gold action or
future target tokens in its input. A fail-fast two-update canary first requires
the two prompts' raw action log-odds to move in opposite correct directions.
This is the minimum test that can distinguish a conditional update from a
global action prior.

## The evidence, reduced to the decisive contrasts

### 1. The level-zero behavior is one coherent convention

In SEQ-098/099 the teaching adapter emitted `PREDICT` before `ACT` on `32/32`
development additions for optimizer seeds 0, 1, and 2; every matched control
emitted it on `0/32`. Arithmetic action correctness was already `32/32` in all
states. The adapter therefore did not learn addition. It installed a response
order that was identical across all 64 arithmetic training cases.

The exposure geometry is strongly favorable to that habit. Per epoch, the
fundamental corpus contains 880 supervised arithmetic tokens and 32 memory
tokens, including EOS. The order convention occurs in 64 arithmetic responses
per epoch, hence 256 row presentations over four epochs. An individual
device--color binding occurs once per epoch, hence only four optimizer
encounters. The common order gradient is repeated across different sums and
contexts; each color fact is a different arbitrary association.

This is precisely the kind of regularity a shared low-rank update should learn
first. It is level-zero disposition carriage, not evidence that behavior and
memory require different adapters.

### 2. The fundamental adapter learns the invariant target and not the keyed one

The seed-0 exact-training-form diagnostic already ruled out a held-paraphrase-
only explanation: teach and task-only adapters each answered `red` for all 16
byte-matched training questions and scored `4/16`, exactly the four red labels.

The newer terminal HF parity run at
`/localhome/local-rohing/astra_diagnostics/astra_fundamental_hf_parity_20260912_attempt1`
closes the most important execution alternative for that low-dose teach
adapter:

- HF and the already captured vLLM output agree on the top color for `16/16`
  exact training prefixes;
- both select `red` for all 16;
- the gold color is top-1 on `4/16`;
- mean gold-color NLL is `1.5662938431`, for geometric-mean gold probability
  `exp(-1.5663) ~= 0.209`;
- mean EOS NLL is `0.0002199387`, or about `0.99978` probability;
- the maximum HF reported-loss disagreement is `5.40e-7` and the maximum
  prefix-only versus full-item logit disagreement at the color position is
  exactly zero;
- 32 forwards were made, with zero optimizer steps and zero new vLLM calls.

Each memory response has two supervised tokens: the varying color and the
constant EOS. The adapter learned the constant part essentially perfectly and
did not learn which color belongs to which device. This is the cleanest direct
evidence for common-mode domination. It is not a backend, target-shift, or
generation-parser story.

The result is for the original seed-0 low-dose adapter. It must not be silently
applied to SEQ-101's repeated checkpoints.

### 3. SEQ-101 tested packaging and stochastic averaging, not 16x learning dose

SEQ-101 put 16 copies of every original row either in separate short sequences
or one continuous sequence and reported 16x input/target token presentations.
Both layouts nevertheless made exactly 80 optimizer updates. The trainer uses
the model's mean token loss and then divides by gradient accumulation.

In the short layout, identical copies are averaged across microbatches before
one update. In the long layout, the 16 occurrences are averaged within the
sequence loss; later occurrences can also attend to earlier gold answers. Thus
the experiment validly shows:

- reset versus continuous-context packaging made no observable difference;
- averaging more dropout realizations of the same row did not rescue binding;
- the global response-order habit remained perfect.

It does **not** show that 16 distinct replay updates per binding fail. The
near-zero long-row loss is especially non-diagnostic because 15 later copies
can exploit prior gold tokens, and the reported final scalar was from an
arithmetic microbatch rather than a memory-only post-fit loss.

### 4. Semantic Q0 isolates the same failure at a more favorable exposure

Semantic Q0 is more diagnostic than the device toy because every one of its 128
training rows is about the conditional policy. Each of 16 `(tool, mode)` keys
appears in eight training templates, replayed for two epochs: 16 row encounters
per key. Labels are exactly balanced globally and within slot, mode, stratum,
template, and their registered combinations. W+ and W- are exact complementary
maps on identical prompt bytes.

The native action carrier is not the problem. With the one applicable mapping
row supplied in context, the frozen base passed all `64/64` semantic items by
greedy generation and scoring, all `32/32` complementary swaps, and all 16 copy
canaries.

Yet after four fresh rank-8 Q0 fits, held mapping accuracy was only
`37/64`, `33/64`, `32/64`, and `34/64`. More decisively, the no-new-fit exact
training-row probe remained near chance:

| cell | exact-row strict generation | dominant generated action |
|---|---:|---:|
| root 0 / W+ | 68/128 | 104/128 one action |
| root 0 / W- | 68/128 | 124/128 one action |
| root 1 / W+ | 64/128 | 128/128 one action |
| root 1 / W- | 63/128 | 113/128 one action |

The repaired fixed-shape score choices were likewise `60/128`, `63/128`,
`63/128`, and `67/128`. Therefore this is not principally an unseen-template
extraction gap. The trained map is not usable even on its own exact prompts.

At the same time, the adapters made the two complete native action candidates
nearly exhaustive across owner and spill prompts. The repaired report's coarse
three-category mass shift is about `.978--.999`, while strict mapping accuracy
stays near half. The original full-sequence target scores rose by roughly
`26` nats. Those numbers measure entry into the legal `ACT:`/termination
carrier, not selection of the correct member conditional on the key.

SEQ-089 makes the distinction still sharper. Keeping only the first divergent
action token as a full-vocabulary CE target did not help: both the reproduced
full-response control and decision-only fit emitted `-gvn` on all `128/128`
exact prompts and scored `64/128`; their final teacher-forced margin signs
agreed on all 128. The decision-only adapter moved substantially (`L2` update
norm `1.433`) and had mean one-token loss `1.064`, so this is not a no-update
failure. Removing the shared suffix was insufficient.

The old unequal-length BF16 candidate scorer did have a real numerical
sequence-shape defect. Equal future padding repaired the probability
invariants. That defect invalidates the old NLL/TV interpretation, but it does
not rescue the strict greedy-generation null or the exact-row null.

## Mechanistic decomposition

Let the two legal action-token logits after a common prefix be

`d(x) = z_mem2reg(x) - z_gvn(x)`

and let `s_i` be `+1` when `mem2reg` is correct and `-1` otherwise. A binding
requires positive signed margin `s_i d(x_i)` for both classes.

A parameter direction that adds the same global bias to `d` for every prompt
cannot solve a balanced dataset: `sum_i s_i = 0`. The useful gradient is the
input-dependent term `sum_i s_i J(x_i)`, where `J(x_i)` is the action-margin
Jacobian for that key. If the key-conditioned Jacobians are weak, very similar,
or approximately additive while the label is an XOR interaction, this residual
is small and mutually interfering. Meanwhile the gradients for common syntax,
legal answer class, and EOS agree across almost every row and accumulate.

The empirical signature is exactly what follows:

- strong output-class mass and perfect syntax;
- a global answer/action preference whose direction may vary by optimizer seed
  or row-order basin;
- chance accuracy under balanced labels;
- no complementary W+/W- redirection.

### Factors distinguished

| candidate explanation | current disposition |
|---|---|
| **Missing or masked gold labels** | **Disfavored.** Native audits found all color/action targets, correct causal shifts, zero drops/truncation, and finite updates. The HF item/prefix equality check is exact. |
| **Adapter not loaded / HF-vLLM mismatch** | **Ruled out for the original fundamental seed-0 teach case.** HF and vLLM agree `16/16`. Semantic Q0 trains and reads through fresh HF/PEFT loads with tensor identity checks. |
| **Held wording/readout mismatch** | **Ruled out as the sole cause.** Both fundamental seed 0 and semantic Q0 remain at the marginal on exact training prompts. Held-form extractability remains an additional later requirement. |
| **Common nondecision-token gradients** | **Real but insufficient.** Constant EOS and carrier syntax are learned strongly, yet SEQ-089's decision-only objective still learns the same constant action. |
| **Full-vocabulary competition at the branch token** | **Still open and directly testable.** One-token CE must raise the correct token against the whole vocabulary; a two-action loss optimizes only the decision that matters. |
| **Balanced-label cancellation** | **A diagnostic property, not a dataset bug.** It prevents an answer marginal from passing. The writer must create input-selective gradients; unbalancing labels would only make the shortcut easier. |
| **Opaque-key representation / XOR geometry** | **Leading residual alternative.** Q0 identifiers share a prefix and split into ordinary subtokens; its target is `orientation(tool) XOR mode XOR map`. If the initial LoRA tangent represents tool and mode mostly additively, the required interaction is much harder than a global habit. The positive in-context carrier does not prove the gradient can write this interaction. |
| **Insufficient optimizer dose** | **Plausible for device/color; unresolved for Q0.** The low-dose device fact gets four update encounters. SEQ-101 did not multiply its loss coefficient. Q0 gives 16 encounters/key, but no proper conditional dose curve. |
| **Rank/capacity** | **Not leading, not ruled out.** Rank 8 clearly has enough capacity to change behavior and saturate the carrier. Prior rank-32 completion-frame cells did not rescue locality and often hurt. But no experiment yet proves rank 8 can express this opaque XOR map. Test local separation before a rank sweep. |
| **Optimizer seed/order** | **Modifier, not sufficient explanation.** Prior canonical-frame writers are strongly seed-sensitive; Q0's constant action varies by cell. A paired complement test must use bound initial tensors/order/RNG and cannot select the lucky seed. |

The Physics-of-LMs extractability result is relevant only after keeping these
stages separate. Diverse biographies and use-shaped views can make stored
knowledge extractable under new queries. Here Q0 already uses eight lexical
views per key and still fails its exact views. More paraphrases are therefore
not the next causal intervention. If exact storage passes and held views fail,
then cross-view rendering becomes the identified remedy.

## Smallest 1--3 fit intervention

### Material: reuse one frozen Q0 root, not a new easy task

Use root 1's existing 128 training prompt bytes and its two complementary maps.
No carrier row, answer, candidate list, parent text, explanation, or future gold
token enters the model input. For every `(slot, template)`, pair its `m0` and
`m1` prompts; the correct actions are opposite under each map. Verify the two
prompts have equal token length and end at the identical response position just
before the first divergent action token.

Do **not** replace opaque keys with semantic names or remove the XOR in this
experiment. That would make a positive easier while failing to diagnose the
current writer.

### Three fresh fit cells

All cells start from the same exact frozen base and bitwise-identical standard
rank-8 LoRA initialization; alpha 16, dropout `.05`, the same seven projection
families, AdamW settings, deterministic environment, and one presealed pair
order. Every optimizer update consumes one matched two-prompt pair.

1. **`V_AUTH`** uses full-vocabulary one-token CE for the authentic gold branch
   token on both prompts.
2. **`P_AUTH`** uses binary pairwise CE formed in FP32 from the same two logits:
   `softplus(-s_i * d(x_i))`, averaged over the opposite-label pair.
3. **`P_DERANGED`** uses the identical pairwise objective on the exact
   complementary W- targets. Prompt bytes, pair order, label counts, token
   counts, and every nuisance marginal are identical to `P_AUTH`.

`OFF` is one shared no-fit state evaluated on the same requests. It is not a
fourth training cell. The historical Q0 and SEQ-089 outputs remain context, not
a silently substituted contemporary control.

Use four passes over 64 pairs, hence 256 optimizer updates per fit. Save fixed
checkpoints after 64, 128, and 256 updates. Those checkpoints correspond to
8, 16, and 32 row presentations per `(tool, mode)` key and provide a dose curve
without extra fits. This doubles the maximum Q0 row exposure but keeps all three
new fits exactly matched; it is a capability/localization experiment, not a
single-factor replication of Q0.

### Fail-fast local-separation canary

The first two pair updates are the first two entries of the presealed training
schedule, not extra selected examples. Before any update, evaluate both prompts
in each pair repeatedly with dropout off and define numerical floor `epsilon`
as the maximum repeated raw-logit spread.

After each actual AdamW update, require:

- the W+ `m0` prompt's raw `d` moves in its correct direction by more than
  `epsilon`;
- its matched W+ `m1` prompt moves in the opposite correct direction by more
  than `epsilon`;
- the complementary cell reverses both directions; and
- no input, target, tensor, optimizer, RNG, or dtype receipt differs outside
  the declared loss/map intervention.

If either pairwise cell cannot do this, stop before the remaining full fits.
That is `LOCAL_CONDITIONAL_GRADIENT_FAILURE`, not chance accuracy. It says the
current rank-8/key/objective tangent cannot even take a two-example conditional
step and makes more epochs or paraphrases low-information.

### Readout: separate carrier mass from binding

At every saved checkpoint, with a fresh reload and dropout off, report:

1. **legal-class mass:** probability entering the two registered action
   branches; diagnostic only;
2. **binding margin:** `s_i d(x_i)` and ON-minus-OFF signed-margin gain;
3. **map redirection:** on identical prompts, whether `P_AUTH` and
   `P_DERANGED` flip to their own complementary targets;
4. **strict generation:** no forced action prefix, no candidate answer in
   context, no retry;
5. **locality/interface:** missing mode, unsupported mode, neighboring ID,
   wrong root, and the eight native copy canaries.

Use direct FP32 next-token logits from one common prefix for the margin and
binary probability. Do not reuse unequal-length full-candidate BF16 scoring.
Candidate mass can never compensate for an incorrect signed margin.

### Noncompensatory qualification

Require both pairwise maps independently; `P_AUTH` alone can never pass.

**Exact-form acquisition:**

- each pairwise map has strict generated BA at least `.90` on all 128 training
  prompts and both action recalls at least `.875`;
- at least 14 of 16 `(tool, mode)` keys are correct on at least 7 of their 8
  training templates;
- at least 112/128 identical prompts are double-correct and flip between
  `P_AUTH` and `P_DERANGED`;
- median signed ON-minus-OFF margin gain is positive in both target classes.

**Held-form extraction:**

- strict BA at least `.80` on the 64 pre-existing held templates, with each
  action recall at least `.75`;
- at least 48/64 held prompts are double-correct complementary flips;
- at least 12/16 keys have positive median signed margin on held forms.

**Scope and interface:**

- strict validity at least `.95`, zero multiple actions, and native copy
  `8/8` in OFF and all fitted states;
- no spill family exceeds `.05` mean two-action TV from OFF or `.05` absolute
  legal-action-rate change;
- wrong-root action redirection remains at its OFF reference rather than
  following either fitted map.

These are development gates. Passing them establishes a supervised
conditional native-action writer on this finite synthetic surface, not
parenting, lived SLEEP, retention, general intelligence, or H1/H2.

## Outcome interpretation

| outcome | diagnosis |
|---|---|
| Pairwise canary fails | The current key/rank tangent cannot make even a local opposite-direction update. Test a simpler unary/single-token key or one rank-32 canary before any full new writer family; do not add dose. |
| Canary passes; all three full fits fail exact acquisition | Local separation exists, but multi-key interference/optimizer dynamics erase it. Inspect the 64/128/256 curve and per-pair gradient conflict; do not call it extractability. |
| `P_AUTH` passes, `P_DERANGED` fails | Base/map/seed alignment or an uncontrolled shortcut; no writer. |
| Both pairwise maps pass, `V_AUTH` fails | Direct evidence that within-action contrast, rather than all-vocabulary CE, was necessary in this instance. |
| Both pairwise maps and `V_AUTH` pass | Pair-balanced common-prefix training and/or the added dose fixed acquisition; pairwise loss is not shown necessary. |
| Exact forms pass, held forms fail | `STORED_NOT_EXTRACTABLE`; now test diverse semantic views at fixed dose. |
| Exact and held pass, spill fails | Conditional association exists but is not a usable scoped memory writer. Test routing/anchors, not rank. |
| Exact, held, complementary redirection, interface, and spill all pass | Freeze this conditional writer primitive and use it unchanged in the first grounded action--outcome relay. |

This experiment is deliberately harder than teaching a second global marker
order. It asks the smallest question the paper actually needs answered: can one
LoRA move opposite actions in opposite directions **because the input state is
different**, while the base model, answer marginals, and syntax are held fixed?

## Evidence basis

- `research_notes/astra_memos/ASTRA_FUNDAMENTAL_SEED0_TERMINAL_2026-09-12.md`
- `research_notes/astra_memos/ASTRA_FUNDAMENTAL_REPLICATION_TERMINAL_2026-09-12.md`
- `research_notes/astra_memos/ASTRA_FUNDAMENTAL_MEMORY_TRAINPROMPT_TERMINAL_2026-09-12.md`
- `research_notes/astra_memos/ASTRA_FUNDAMENTAL_REPETITION_TERMINAL_2026-09-12.md`
- `research_notes/analysis/2026-09-12_repetition_dose_normalization_correction.md`
- terminal remote `astra_fundamental_hf_parity_20260912_attempt1/main_summary.json`
- `research_notes/astra_memos/ASTRA_SEMANTIC_CARRIER_TERMINAL_2026-09-12.md`
- `research_notes/astra_memos/ASTRA_SEMANTIC_WRITER_TERMINAL_2026-09-12.md`
- `research_notes/astra_memos/ASTRA_SEMANTIC_RESCORE_TERMINAL_2026-09-12.md`
- `research_notes/analysis/2026-09-12_semantic_w0_common_mode_terminal_reduction.md`
- `research_notes/analysis/2026-09-12_semantic_objective_terminal_reduction.md`
- `research_notes/analysis/2026-09-12_semantic_objective_terminal_fresh_postaudit.md`
- `research_notes/analysis/2026-09-12_pairwise_writer_path_fresh_audit.md`
- `research_notes/analysis/2026-09-12_lower_lr_writer_terminal_audit.md`
- `research_notes/analysis/2026-09-12_writer_sleep_evidence_chain_audit.md`
- `research_notes/analysis/2026-09-12_first_eleven_writer_pretest_cumulative_audit.md`
- `research_notes/analysis/2026-09-12_post_v10r2_writer_recipe_factorial.md`
- `research_notes/IDEAS.md` entries on Allen-Zhu and Li, knowledge storage,
  extraction, multiplicity, and stable-key rendering
- `organism_v6/fundamental_teaching_corpus.py`
- `organism_v6/fundamental_repetition_corpus.py`
- `organism_v6/semantic_writer_diagnostic.py`
- `organism_v6/multikey_writer_gateway_simple.py`

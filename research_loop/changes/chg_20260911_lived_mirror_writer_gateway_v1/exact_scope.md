# Lived mirror writer gateway — exact implementation scope v1

**Change ID:** `chg_20260911_lived_mirror_writer_gateway_v1`  
**State:** proposed; these bytes authorize implementation and CPU/fault tests
only after exact human ratification. Model calls, training, and GPU execution
require a later immutable execution manifest, two independent PASS reviews,
and separate human ratification.  
**Purpose:** cheaply test whether one mechanically rendered, target-masked
write can carry a child's grounded endpoint policy before paying for full
writer qualification. This is not C11, a clean child, a parenting test, or a
paper root. The only files authorized for implementation are
`organism_v6/lived_mirror_gateway.py`,
`organism_v6/scout_quarantine.py`,
`tests/test_lived_mirror_gateway.py`, and
`tests/test_scout_quarantine.py`, plus proposal/review artifacts inside this
change directory. Implementation may neither modify nor invoke live-child,
parent, CompilerGym, PCFL, C11, model, tokenizer, trainer, or GPU components.

## 1. Fixed question and claim

After a frozen child acts in a two-action world, observes the public outcome,
and authors a correct final action, can a target-masked write make the same
frozen child follow that world's two-situation policy after all lived context
is removed?

A full pass permits only this reading:

> In one paired micro-world, opposed success-filtered, child-grounded
> action--outcome corpora produced mapping-specific adapter behavior that
> carried the child's final endpoint policy into later actions under unseen
> prompt templates.

It does not show that outcome tokens or intermediate reasoning were causally
necessary. It does not independently falsify or qualify the writer, and it
does not qualify any developmental lineage.

## 2. Scout isolation and immutable plan

All generated material, corpora, weights, reads, and reports must live beneath
a unique, fail-if-exists, realpath-resolved
`SCOUT_ROOT/chg_20260911_lived_mirror_writer_gateway_v1/<run_id>`. The run root
must be disjoint from every child, parent, CompilerGym, PCFL, and C11 root.
Read/write allowlists, symlink refusal, and outside-root write refusal are
tested before execution. No artifact or weight from this gateway may enter a
child or final experiment; only the generic recipe may later be proposed for
promotion.

Before any model output, one immutable plan binds the scope hash; source,
compiler, trainer, evaluator, parser, scorer, retriever, and dependency bytes;
exact model/tokenizer revisions; opaque token bytes; all source and report
prompt hashes; seed derivations; counts; expanded arguments; forbidden roots;
and the execution budget. Scientific report bytes are sealed from the D0
process but authored and hashed before D0 begins.

Every admitted row retains immutable source-case, child-action, public-
outcome, final-action, renderer, and target hashes. Each stage uses
`PLANNED -> RUNNING -> COMMITTED|FAILED` markers; only infrastructure failures
may retry under identical bytes. Terminal closure writes a self-excluding
inventory exactly once. A materialized count or hash mismatch is `NOT_RUN`.

Use separate fail-if-exists subroots `D0/` and `SCIENTIFIC/`. Cross-reads are
refused. `D0/` holds one permanently development-only paired identity
`D0+/D0-`; `SCIENTIFIC/` holds one paired identity `M+/M-`. D0 uses disjoint situation tokens, action
tokens, source surfaces, case identities, and report surfaces. It may share
only algorithms and the proposed recipe. No D0 artifact, prompt, identity, or
output transfers; only the scalar preflight verdict and timing estimate
transfer. Terminal inventory hashes are registered in the scout quarantine
deny artifact; the reusable helper exposes a refusal check, and CPU fixtures
prove it rejects every registered path and hash descendant. Any later clean-
child or C11 manifest must bind and invoke that helper. This scope tests the
helper but does not modify those live loaders.

## 3. Lived source phase

Within each pair, both worlds use the same frozen base child, system prompt,
two visible situation tokens, two visible legal action tokens, 12 provenance-
only case IDs per situation, opportunity schedule, decoding settings, and
common-random seeds. Case IDs never appear in model-visible text. The legal
action vocabulary is visible, but no ordered, recommended, or demonstrated
action is visible. The only intervention is the hidden mapping:

- plus world: `s0 -> a0`, `s1 -> a1`;
- minus world: `s0 -> a1`, `s1 -> a0`.

For each case the child sees a source surface containing the situation,
chooses one strict action, receives its binary public world outcome, and then
authors one strict final action for the next occurrence of that situation. No
correct action, hidden mapping, worked example, reflection, parent advice, or
evaluator-authored answer is supplied. All attempts, invalid actions, outcomes,
and final actions are preserved.

Admission is explicitly success-conditioned and tests only this end-to-end
source-plus-writer package. Provenance case `j` is globally eligible only when
both worlds' final actions are correct for both situations. Admit the same
lowest eight globally eligible IDs for both situations. Fewer than eight is
`SOURCE_INVALID`; do not top up, replace, or select separately by situation or
world. Publish all 48 scientific source trajectories and the 12-case global
eligibility vector.

Before training, each world must therefore contain exactly 16 admitted final
actions, balanced eight `a0` and eight `a1`. Across the complete 24 source
trajectories per world, the initial actions must populate every cell of the
`action x public-outcome` 2x2 table at least once; exact counts are reported.
Every admitted row needs a complete provenance chain. Otherwise stop as
`SOURCE_INVALID`.

A byte-level visibility scan covers the system prompt, source prompts,
compiler, interface canary, and report prompts. It must prove that no concrete
action example, situation-to-action statement, correctness/admission bit,
world-sign label, hidden mapping, report identity/template, or historical LLVM
routine reaches model-visible bytes outside authoritative lived rows and
explicitly labeled diagnostic TEXT/GOLD controls.

## 4. Compile and write

For every admitted case, compile exactly eight ordered, predeclared native-
style surface renderings. The masked context contains the situation, the
child's initial action, and the public outcome. The child-authored final action
appears exactly once, solely as the terminal supervised target
`ACT: <ACTION>`; it never appears in masked context. No parent, evaluator,
correctness bit, admission flag, report text, separately supplied correct
action, hidden mapping, evaluator label, or evaluator-authored replacement
target enters model-visible training bytes. The correctness-selected,
child-authored final action is answer-bearing by design and is the sole
supervised target. Correctness and admission metadata are removed before the
authoritative compiler-input rows are written. Each complete post-chat-
template encoded sequence, including masked context, target, and EOS, is at
most 256 tokens even though trainer `max_len` is 2048.

The two world corpora must have identical item count, target-token multiset,
surface index, tokenizer-counted context and target lengths, supervised
positions, EOS count, optimizer steps, initialization/dropout seed, and node.
A CPU receipt proves every equality before fitting.

Train the plus and minus adapters independently from the same locally cached
frozen `Qwen/Qwen2.5-7B-Instruct` revision using the standalone unpacked,
chat-templated, target-masked trainer: all-projection LoRA rank 8, alpha 16,
dropout 0.05, AdamW `3e-5`, two epochs, batch size 1, maximum length 2048,
EOS on, no packing, no SVD initialization. Each fit starts from the frozen
base, never from another adapter.

Each pair contains `2 worlds x 16 admitted cases x 8 renderings = 256`
training items and at most
`2 x 16 x 8 x 256 x 2 = 131,072` token-passes. D0 and the scientific pair
together contain exactly four fits and at most 262,144 token-passes. The CPU
receipt and execution manifest bind exact post-collate supervised and total
token-pass counts.

## 5. Result-blind D0 preflight

D0 repeats the full source, compile, and two-fit path at the fixed eight-
rendering dose. Before any D0 model output, the complete scientific evaluation
is already hash-bound and sealed. D0 may expose only:

- median held-form supervised-token NLL reduction, which must be at least
  `0.50` nat in both worlds;
- absolute difference in mean NLL reduction, which must be at most `0.25`
  nat;
- strict action validity;
- the fixed interface, proliferation, and generic non-harm canaries below;
- wall time, throughput, and resource use.

D0 may not compute or expose binding accuracy, mapping preference, spill,
GOLD, TEXT, or scientific report output. A failed D0 stops the run. Any code,
prompt, or recipe change burns D0 and requires a new bound development pair.
The first D0 fit is also the only throughput smoke: after it commits, its
timing and load overhead project the remaining three fits and all bound
generation. If the conservative total exceeds the cap, stop result-blind as
`NOT_RUN`; no fifth fit or separate smoke identity exists.

## 6. Interface, proliferation, and fit canaries

For D0 and the scientific pair, evaluate each fitted adapter and one shared
OFF base per pair on eight fixed, non-report, wake-like multi-turn tasks (four
per situation) using the real free-flow interface, four ticks, and at most 400
generated tokens per task. Also evaluate 16 fixed generic-action tasks per
condition at at most 64 new tokens. A dedicated held-form action set has 16
fixed single-turn prompts per condition (eight per situation), at most 12
generated tokens, disjoint from train, primary-report, multi-turn, and generic
prompts. Held-NLL evaluation uses 16 further fixed forms per adapter (eight per
situation), also disjoint from every training and generation form. All
prompts, decoding, parser, task values, seeds, and reducers are bound in the
execution manifest.

Each fitted adapter must have:

- median per-key held-form target NLL reduction at least `0.50` nat;
- pairwise difference in mean NLL reduction at most `0.25` nat;
- strict `ACT:` validity on the dedicated held-form action set at least `0.95`
  overall and `0.90` per situation;
- zero zero-ACT, empty, or DONE-first multi-turn tasks;
- balanced-mean authoritative ACT rows per task no greater than
  `max(OFF + 1, 1.5 x OFF)`;
- balanced-mean continuation tokens per task no greater than
  `max(OFF + 32, 1.5 x OFF)`; and
- generic-action score at least `OFF - 0.05`.

No lower thought-count or token-count bound is used: a concise adapter is
allowed when it still acts and preserves task value. If OFF has zero ACT rows
or tokens, the additive bound controls. Canary failure is `interface-invalid`
and prevents scientific reads; it is never counted as low task performance.

## 7. Frozen scientific reads

The primary panel contains four source-disjoint prompt templates for each
situation and two common-random replicates: 16 prompts per condition. No case
ID is model-visible, so every primary item tests the two-situation policy under
an unseen surface. Invalid outputs score zero. Average replicates, then prompt
forms, then situations equally.

Generate the primary panel under seven conditions: `OFF`, plus adapter, minus
adapter, plus-store TEXT, minus-store TEXT, plus-row GOLD, and minus-row GOLD.
This is exactly 112 primary generation calls. OFF and both adapter prompts
contain no history, answer, candidates, retrieved text, or routine example.
TEXT and GOLD explicitly contain raw lived experience, including a child final
action. The deterministic GOLD row for a situation is the lowest admitted
provenance ID. Every condition is scored against both mappings.

TEXT is a same-ledger text-carrier diagnostic, not automatically a strong
agent-memory baseline. Its fixed candidate-blind lexical retriever uses only
the visible situation as query. Query construction, top-k, scoring, tie-break,
row rendering, token budget, and miss behavior are bound before D0. Report
recall@k, citation validity, and balanced accuracy. It earns the label
`strong within-assay text carrier` only if recall and citation validity are
both 1.00, `BA_TEXT+^M+` and `BA_TEXT-^M-` are each at least 0.85 and within
0.05 of their same-sign GOLD value, and the store-swap contrast
`0.5 * [(BA_TEXT+^M+ - BA_TEXT-^M+) +
(BA_TEXT-^M- - BA_TEXT+^M-)]` is at least 0.50.

The exact GOLD gates are `BA_GOLD+^M+ >= 0.85` and
`BA_GOLD-^M- >= 0.85`; otherwise the assay is invalid. The
complete condition-blind deterministic routine set is `always a0` and
`always a1`; report both before opening adapter outputs.

Spill controls contain 16 new situation tokens outside `s0/s1`, 16 wrong-
relation prompts using `s0/s1`, and 16 no-situation prompts. They do not
include new instances of `s0/s1`, because those are expected policy
generalization rather than spill. OFF and both adapters receive every control
under two common-random replicates: exactly 288 control generation calls.
For each control family and adapter, report paired generated-action change
from OFF and teacher-forced total-variation distance after normalizing over
the two legal action continuations. Each mean must be at most 0.05.

## 8. Decision and precedence

Let `BA_z^M` be the balanced accuracy of condition `z` against mapping `M`.
Define:

`tau_lived = 0.5 * [(BA_W+^M+ - BA_W-^M+) + (BA_W-^M- - BA_W+^M-)]`

and the mirrored base-relative gain:

`g_lived = 0.5 * [(BA_W+^M+ - BA_OFF^M+) + (BA_W-^M- - BA_OFF^M-)]`.

Also define directional cross-adapter contrasts
`d_plus = BA_W+^M+ - BA_W-^M+` and
`d_minus = BA_W-^M- - BA_W+^M-`. Separate per-world OFF-gain gates are not
used: because the mappings are exact reversals, an arbitrary OFF prior may
already be at ceiling in one world and floor in the other. Requiring an
increase over OFF in both worlds would reject perfect symmetric carriage.

For primary-panel condition `z`, let `p_z` be the balanced generated
distribution over `{a0, a1, INVALID}` and define
`TV_z = 0.5 * sum_k |p_z(k) - p_OFF(k)|`. A `common marginal shift` requires
`TV_W+ >= 0.10`, `TV_W- >= 0.10`, and
`0.5 * sum_k |p_W+(k) - p_W-(k)| <= 0.05`.

The gateway passes only if:

- `BA_W+^M+ >= 0.75` and `BA_W-^M- >= 0.75`;
- `g_lived >= 0.20`;
- `tau_lived >= 0.50`;
- `d_plus >= 0.50` and `d_minus >= 0.50`;
- each own-world adapter beats the best condition-blind routine by at least
  `0.20`;
- every source, fit, interface, generic non-harm, GOLD, and spill gate passes.

Decision precedence is fixed: source failure -> `SOURCE_INVALID`; held-NLL
failure or held-NLL pair asymmetry -> `optimization-inconclusive`;
interface/non-harm failure -> `interface-invalid` with no scientific read;
GOLD failure -> `assay-invalid`; every non-spill primary gate passing with a
spill failure -> `conditional association mixed with broad habit`; common
marginal shift with either directional reversal gate failing -> `broad habit`;
the full conjunction -> `child-grounded endpoint-policy carriage`; every
other valid completed failure -> `gateway-negative`.

One gateway pair is a development spending gate, not a root-level uncertainty
estimate. Its failure does not independently reject the writer. There is no
efficacy-driven dose, threshold, arm, prompt, or identity change after outputs
are opened. Preserve every failure.

## 9. Workload gate and next stage

The maximum workload is four fits, 96 D0 source action generations, 96
scientific source action generations, 112 primary generations, 288 spill-
control generations, 48 multi-turn canary tasks, 96 generic non-harm tasks,
and 96 held-form action generations. The multi-turn, generic, and held-form
counts use one shared OFF plus two adapters per pair. Source generations are
capped at 32 new tokens, primary/control/held-form action generations at 12,
multi-turn tasks at 400 total generated tokens, and generic tasks at 64.

Mandatory teacher-forced work is also inside the cap. Held-NLL scoring uses
`2 pairs x 2 world-target sets x 16 sequences x 2 scoring conditions
(OFF and own adapter) = 128` complete sequence evaluations. D0 computes no
spill. Scientific spill TV scoring uses
`1 pair x 48 controls x 2 legal continuations x 3 conditions
(OFF, plus adapter, minus adapter) = 288` complete sequence evaluations.
Every teacher-forced sequence is capped at 256 post-template tokens, for at
most 416 sequence evaluations and 106,496 teacher-forced token-passes. These
counts and actual encoded totals are bound before execution and included in
the eight-hour projection.

The execution manifest binds conservative prior training and inference
throughput values, the projection formula, fixed workload, and eight-hour cap.
After the first D0 fit, append an immutable throughput/load receipt and
recompute the projection for the remaining three fits and all generations. If
prior receipts do not conservatively bind inference throughput, that D0
receipt also includes one fixed result-blind inference-throughput probe. If
the projected total exceeds eight A40-equivalent GPU-hours, stop result-blind
as `NOT_RUN`. No separate smoke identity or fifth fit exists, and the workload
may not be silently thinned.

A gateway pass permits preparation—not execution—of the separately ratified
six-bank true/permuted writer qualification. Only a full repeated-root plus
cumulative-interference pass may qualify a frozen writer recipe for a clean
parenting or deployment lineage.

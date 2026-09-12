# Post-V10R2 writer-recipe factorial

Date: 2026-09-12 UTC  
Status: prospective, docs-only recommendation. This note changes no builder
source, benchmark, model, adapter, run artifact, job, process, node, or GPU
reservation and authorizes no execution or claim.

## Decision

If a fresh V10R2 first establishes a valid common response interface and an
exact-row positive-carrier ceiling **and its unchanged writer does not already
pass W0**, the smallest high-information writer follow-up is a paired
**2 x 2** at rank 8:

| arm | eight memory renderings per key | scope-preserving base anchor |
|---|---|---|
| `Q0` | eight lexical query paraphrases | absent |
| `QA` | eight lexical query paraphrases | present |
| `X0` | query + declarative + contrast + structured views | absent |
| `XA` | query + declarative + contrast + structured views | present |

Every arm sees the same 16 meanings per root-map, eight memory rows per
meaning per epoch, target bytes, semantic key order, two complementary maps,
two disjoint roots, optimizer, seed within root, and rank-8 all-layer LoRA.
Save the same fit at step 128 and step 256. Those checkpoints compare eight
versus sixteen exposures per meaning without another fit.

This experiment deliberately does **not** sweep rank. Attempt 2 already shows
that rank 8 can fit the supervised stream: across its four fits, mean loss in
the first 32 steps was `6.3673 / 6.4132 / 6.9646 / 6.8362`, while the final
32-step means were `0.1185 / 0.1286 / 0.1247 / 0.1219`. Yet fresh held-form
candidate balanced accuracy was only about `.406--.516`, each held template
8--11 remained about `.25--.5625`, and the complementary direction was
correct for exactly `8/16` keys per root. Meanwhile maximum spill TV was
`.265--.622`. The immediate ambiguity is therefore **how a fitted relation is
encoded and scoped**, not whether rank 8 has enough parameters to reproduce
128 short rows.

The screen is recipe development, not paper confirmation. Any selected recipe
must subsequently rerun W0 on fresh source-disjoint roots before it supports a
writer claim.

## New response-calibration consequence

The bounded development calibration now sharpens what “valid V10R2” must
mean. `chat + explicit contract + 32 tokens` produced `61/64` strictly valid
outputs but only `45/64` correct actions. Every raw rendering failed, and the
raw 256-token condition still truncated. The old oracle therefore conflated:

1. using the declared chat/action response interface; and
2. searching a 16-row in-context map for the relevant row.

Before any new fit, run a fresh **exact-row positive-carrier canary**. For each
fresh held query, place only its one correct `(tool, mode) -> ACT` row in the
memory slot, use the single-user-message Qwen chat template, append the
non-target-revealing explicit complete-output contract, and require both
strict generation and full-candidate scoring. Per root-map require generated
and scored BA `>= .90`, strict validity `>= .95`, zero multiple ACT, and
unrelated native exact `8/8`. Use fresh identifiers/forms absent from the
five-condition calibration. Failure is `ASSAY_INVALID` with zero fits.

Keep the 16-row table as a separately named `TEXT_TABLE_SEARCH` diagnostic.
It measures multi-row lookup and may matter for the strong text baseline, but
it must not stand in for output-interface validity or exact-row carrier
headroom. An exact-row pass plus table failure says that automatic selection
is necessary here; exact-row failure invalidates every writer inference.

**Renderer decision:** if and only if that fresh exact-row canary passes, use
the Qwen chat template plus explicit output contract symmetrically in every
training context, scoring prefix, owner generation, spill prompt, and carrier
control. Do not fit on raw text and evaluate through chat, or add the contract
only at evaluation. Development evidence rules raw rendering out for the next
fit; it does not itself certify chat on new material.

## Why these two factors

The present corpus has lexical diversity but only one semantic geometry:

```text
tool + mode -> question -> ACT
```

Each key appears under eight query phrasings and the identical set is replayed
for a second epoch. Near-zero loss can therefore mean that the adapter learned
eight completion routes without binding the value to the full `(tool, mode)`
key in a form recoverable from a ninth route. The exact complementary failure
and the absence of a standout held template are more consistent with a
key-binding/extraction problem than one bad held wording.

Allen-Zhu and Li distinguish fitting training sentences from making their
knowledge extractable. In their controlled biography setting, five diverse
biographies plus permutation moved downstream QA accuracy from `9.7%` to
`96.6%`; increasing multiplicity or permutation generally helped, whereas a
single permutation without multiplicity could hurt. Their mechanistic reading
is that varied expressions and orderings attach attributes more directly to
the entity key instead of incidental neighboring text. They also find that
mixing extraction-shaped QA data into learning can change how knowledge is
stored. See [Physics of Language Models: Part 3.1, Knowledge Storage and
Extraction](https://arxiv.org/abs/2309.14316), especially Results 1--4.

That paper is a design prior, not evidence about Qwen2.5-7B LoRA: it mostly
pretrains much smaller models from scratch on 100,000 biographies. The narrow
transferable prediction is that **diversifying semantic access routes while
repeating the complete key** can shrink the exact-form-to-held-form extraction
gap. Merely showing the same query more often is not the same treatment.

The repository's write-swarm points in the same direction but is weaker: in an
offline `n=2`, dose-confounded screen, plain writing scored `.466`,
paraphrase `.496`, replay-mix `.494`, and both `.489`, with base around
`.485--.494`. It suggests that enrichment and replay may remove harm or
variance, not that either already produced selective memory. The factorial
below turns that directional observation into separable tests:

- `X-Q` asks whether cross-view rendering improves fresh-form extraction at
  fixed fact count and exposure.
- `A-0` asks whether a base-behavior anchor reduces spill at fixed memory
  exposure.
- the interaction asks whether extractability and locality can coexist rather
  than trading off.

## Frozen memory-view treatment

Both view conditions contain one byte-identical canonical direct-query form
per key. This supplies a common exact-train-form diagnostic. `Q` uses that form
plus seven ordinary query paraphrases. `X` uses the canonical form plus seven
different access routes:

1. direct query, key ordered as tool then mode;
2. direct query, key ordered as mode then tool;
3. declarative/cloze completion ("the action stored for this full key is");
4. a compact typed record with separate tool, mode, and action fields;
5. within-tool contrast naming the current mode and the other mode, without
   revealing either answer;
6. within-mode contrast naming the current tool and a presealed decoy tool,
   without revealing either answer;
7. a repeated-full-key recall form that names `(tool, mode)` twice; and
8. an explicit two-candidate choice with both candidate orders balanced.

Every route is one user-message body, ends at the exact same Qwen assistant
generation boundary, and has only
`ACT: a0\n` or `ACT: a1\n` plus EOS as the loss-bearing target. Parent prose,
reasoning text, summaries, oracle tables, hidden truth, and a compiler-written
explanation remain absent. The explicit response-contract bytes certified by
the exact-row canary appear identically in every route and evaluation. Chat
special tokens are added exactly once; raw/chat mixing or duplicate assistant
tokens fail tokenizer preflight.

The decoy relation, candidate order, template, mode, stratum, and every
declared combination of nuisance fields must have a maximum shortcut accuracy
of exactly `1/2` within each map. Each prompt must contain the complete owner
key, and changing the map may change only the target, never prompt bytes.
The two maps remain exact complements.

This is not eight extra copies. It is still exactly 128 memory rows per
root-map per epoch:

```text
16 meanings x 8 views = 128 rows
step 128 checkpoint   = 8 exposures/meaning
step 256 checkpoint   = 16 exposures/meaning
```

Use a presealed balanced semantic-key order for epoch 1 and an independently
presealed balanced permutation for epoch 2, identically across all four arms.
Do not group all rows for one key or all rows of one view together.

## Frozen locality treatment

`A` is a targeted base-behavior constraint, not generic web-text replay and
not another source of task knowledge. Before fitting, use the valid V10R2 OFF
surface to seal the frozen base distribution on the existing per-root scope
panel:

- 8 missing-mode prompts;
- 8 unsupported-mode prompts;
- 16 neighboring-identifier prompts; and
- 8 unrelated native-interface prompts.

No owner prompt, held owner answer, complementary-map label, oracle table, or
other root enters this anchor bank. The exact same anchor bank is used for the
two complementary maps of its root. A cyclic wrong-root panel remains held
out and is never anchored.

At each memory update in `A`, pair the memory loss with the next anchor in a
fixed cycle and optimize

```text
L = 0.8 * L_memory + 0.2 * L_anchor
```

where both terms are token-mean normalized. `L_anchor` is teacher-to-student
KL from frozen OFF logits to adapter-on logits along the complete, sealed OFF
continuation, including EOS. The teacher logits and continuation are produced
once before any fit and hash-bound. At clean LoRA initialization the anchor
has zero divergence; it penalizes only movement away from the base on
out-of-scope prompts. The target remains the base distribution, rather than a
researcher-invented action or a sampled pseudo-label.

`0` has no anchor gradient. It retains the identical memory rows, 128/256
memory updates, optimizer, and checkpoints. Report the extra forward-pass
cost honestly; do not reduce memory exposure to fake equal compute. This
isolates the information treatment while keeping the quantity of supervised
experience constant.

Why KL rather than hard replay targets: hard targets would sharpen an
arbitrary base completion and could itself change entropy or syntax. The gate
we need is distributional locality relative to OFF, so the corresponding
constraint is a distributional one. Why a targeted 20% bank rather than broad
generic replay: the current failure is already measured on these four scope
families, and a small exact bank gives substantially more information per
token than an unbounded instruction mixture.

## Rank, exposure, and optimizer decisions

Keep these fixed:

- rank `8`, alpha `16`, dropout `.05`;
- all 28 layers and the existing q/k/v/o plus MLP projections;
- AdamW, learning rate `3e-5`, batch size 1 for the memory row;
- response-only/context-masked loss;
- bfloat16/eager/deterministic settings and one clean-base fit per cell;
- no warm start, adapter merge, seed search, best retry, or SVD init.

Save step 128 and step 256 from the same deterministic fit. Do not add a third
epoch: the attempt-2 second-epoch mean loss was already about `.133--.142`, and
its final 32 steps about `.12`. More identical repetition is more likely to
amplify the global ACT habit than resolve the observed extraction gap.

Do not add rank 16 in this screen. A higher-rank arm is warranted only after a
rank-8 multi-view recipe passes exact-form storage and locality but remains
uniformly just below the held extraction thresholds. If exact-form storage
passes and held extraction fails, capacity is not the identified failure. If
exact-form storage itself fails for `X`, first inspect view-specific loss and
the 128/256 dose comparison; only a dose-limited failure justifies more
exposure.

## Panels that separate the four questions

All prompts use fresh opaque identities and held literals disjoint from the
attempt-2, development-calibration, and V10R2 confirmation material. OFF is
evaluated once per root.
Each saved adapter checkpoint is evaluated in a fresh process.

### 1. Exact-train-form storage

For every one of the 16 keys, score both candidates on the byte-identical
canonical query form that appeared in both `Q` and `X`. Also retain the
teacher-forced loss over all 128 actual training rows and view-specific loss
by view type.

This panel answers: **can the adapter recover the supervised relation through
a surface on which it was actually trained?** It prevents near-zero streaming
loss from being mistaken for accessible storage.

### 2. Fresh-held-form extraction

For every key, score both candidates on four newly frozen query forms that
occur in no training arm. None may be a lexical substitution of the response
contract or one of the eight `X` forms. Preserve the existing balanced
strata, complements, and shortcut audit.

This panel answers: **does the exact same relation survive a new access
route?** Report both absolute held metrics and two extraction gaps:

```text
exact-train choice BA - fresh-held choice BA
median exact-train key gain - median fresh-held key gain
```

A writer that passes storage and fails this panel is `STORED_NOT_EXTRACTABLE`,
not an optimization failure.

### 3. Native interface

Only recipe/checkpoint cells that pass score-based storage and extraction
advance to free generation. Generate on the 64 fresh-held owner prompts, one
canonical exact-train form per key, and the eight unrelated native-interface
prompts. Keep the strict complete-output parser, no substring rescue, no
retry, and fail-closed truncation.

This panel answers: **can extracted preference reach the declared ACT motor
surface without breaking unrelated native actions?** A score pass plus a
generation failure is `EXTRACTABLE_INTERFACE_FAIL`.

### 4. Locality

On missing, unsupported, neighboring, and unrelated prompts, measure full
candidate probability TV and legal-ACT-rate change from OFF. Also mount each
root adapter on the other root's 64 held prompts, with no anchor exposure, and
measure the same quantities. The other-root target is never used in fitting
or selection.

This panel answers: **did the relation remain scoped to its owner keys, or did
the adapter create a global action dialect/habit?** A storage/extraction/
interface pass with failed scope is `SELECTIVE_BINDING_WITH_SPILL`, not a
memory pass.

## Exact noncompensatory gates

Apply these per root-map and require both maps in both roots unless a label
explicitly says otherwise.

### `STORAGE_OK`

- exact-train candidate-choice BA `>= .95` over the 16 common forms;
- all `16/16` keys have median target NLL gain over OFF `>= .50 nat` on their
  actual train views;
- no view type has candidate-choice BA below `.875`; and
- fit is finite, complete, and the saved checkpoint exactly replays.

Low training loss alone is logged but cannot pass this gate.

### `EXTRACTION_OK`

Use the existing W0 score-based thresholds on fresh forms:

- candidate-choice BA `>= .80`;
- each stratum accuracy `>= .75`;
- gain over OFF `>= .20`;
- own-map minus opposite-map BA `>= .50`;
- all `16/16` keys have median target NLL gain `>= .50 nat`;
- at least `12/16` keys, including `6/8` in each stratum, have median
  own-target margin `>= .50 nat`; and
- complementary-map mean-gain asymmetry `<= .25 nat`.

### `INTERFACE_OK`

- strict fresh-held generated BA `>= .80`;
- exact legal-output validity `>= .95` overall and `>= .875` per stratum;
- zero multiple-ACT outputs;
- unrelated native interface is exact `8/8` for OFF and the adapter; and
- no truncation/substring/retry reinterpretation is permitted.

### `LOCALITY_OK`

- in each of missing, unsupported, neighboring, and unrelated families,
  mean binary candidate TV from OFF `<= .05`;
- absolute legal-ACT-rate change in every family `<= .05`;
- cyclic wrong-root mean candidate TV and legal-ACT-rate change each
  `<= .05`; and
- all fixed-denominator panel rows are present exactly once.

The ordered label is:

```text
invalid common response assay     -> ASSAY_INVALID (zero fits should launch)
not STORAGE_OK                     -> STORAGE_FAIL
STORAGE_OK, not EXTRACTION_OK      -> STORED_NOT_EXTRACTABLE
score gates pass, interface fails  -> EXTRACTABLE_INTERFACE_FAIL
all above pass, locality fails     -> SELECTIVE_BINDING_WITH_SPILL
all four gates pass                -> WRITER_RECIPE_GATEWAY_PASS
```

No average may compensate for a failed key, stratum, map, root, interface, or
scope family.

## Factor and dose decisions

The absolute gate decides whether any recipe is usable. The paired contrasts
decide what was learned from the screen:

- **Cross-view supported:** at the same anchor state and checkpoint, `X-Q`
  improves fresh-held candidate BA by at least `.10` in at least `7/8`
  root-map-anchor comparisons, has positive median improvement at both roots,
  retains `STORAGE_OK`, and worsens no scope-family TV by more than `.05`.
- **Anchor supported:** at the same view state and checkpoint, `A-0` reduces
  the maximum scope-family TV by at least `.10` in at least `7/8`
  root-map-view comparisons, retains `STORAGE_OK`, and reduces fresh-held BA
  by no more than `.05` in every root-map.
- **Coexistence:** only `XA` (or another absolute-pass cell) demonstrates that
  extraction and locality coexist. Opposite main effects without an absolute
  pass establish a tradeoff, not a solved writer.
- **Dose:** prefer step 128 if it passes all absolute gates. Otherwise use
  step 256 only if it newly passes a gate or raises fresh-held BA by at least
  `.05` without increasing any maximum scope TV by more than `.05` or losing
  interface validity. If step 256 only lowers training loss, eight exposures
  per meaning are enough and the second epoch is rejected.

These effect rules are development decisions, not p-values. Roots and maps
are nested repeated measurements, not eight independent scientific units.
The chosen cell is frozen before fresh W0 confirmation roots exist.

## Execution funnel and estimated cost

1. **Prerequisite:** run the V10R2 OFF-first exact-row positive-carrier and
   interface canary under chat + explicit contract. A failure launches zero
   recipe fits. Retain the 16-row table as `TEXT_TABLE_SEARCH`, not the sole
   carrier/interface oracle. If V10R2's unchanged writer already achieves
   `MULTIKEY_BINDING_PASS`, skip this grid and proceed to W1.
2. **Fit/score screen:** 4 arms x 2 roots x 2 maps = 16 clean-base rank-8
   fits, each yielding step-128 and step-256 adapters. Score the common exact
   form, fresh-held forms, four scope families, and cyclic wrong-root panel.
3. **Promotion generation:** free-generate only for cells that pass both
   score-based storage and extraction. If more than two recipe/checkpoint
   cells qualify, promote the two with smallest maximum scope TV, breaking
   ties by smaller extraction gap, then step 128, then a presealed arm order.
4. **Stop:** if no cell passes score-based extraction, do not spend on native
   generation, rank 16, a third epoch, or W1. The labels already identify the
   next defect.
5. **Fresh confirmation:** if a recipe passes the development gateway, bind
   it unchanged and rerun W0 on fresh roots. Only that run can qualify W1.

Attempt 2 consumed `.4718` A40-hours for four 256-step fits plus 1,504
requests. Its fit workers themselves used about `.126` A40-hours. Scaling the
fit portion to 16 costs about `.50` A40-hours. With only 16 common exact-form
scores, 64 held scores, 32 binary scope scores, and 64 wrong-root scores per
checkpoint, the two-checkpoint score screen is approximately 5,600 adapter
requests plus shared OFF requests; promotion adds at most roughly 700 strict
generations. A conservative cap is **2.5 A40-hours** for the development grid,
or **3.0** including custody/reload margin. Parallel GPUs reduce wall time but
not the reported A40-hours.

This is substantially more informative than a rank or epoch sweep: one run
can distinguish fitted-but-inaccessible relations, accessible-but-unemitted
relations, emitted-but-global habits, and selective conditional actions.

## Interpretation boundary

A development pass selects a supervised supplied-memory writer recipe. A
fresh W0 pass would show only seen-key conditional action carriage under this
engineered grammar. Neither result establishes authentic child experience,
outcome binding, cumulative replay retention, connected memories, DREAM,
parenting, increasing-lifetime improvement, H1/H2, or the whole organism.

The next ladder remains unchanged:

```text
valid response interface
  -> selective supplied writer (fresh W0)
  -> two-bank cumulative replay (W1)
  -> authentic action/outcome source (S)
  -> connected relay/traversal/expansion (M)
  -> increasing-lifetime learning and strong evolving-text baseline (L/B)
```

## Evidence inspected

- `AGENTS.md`
- `organism_v6/multikey_writer_gateway_simple.py`
- `research_notes/analysis/2026-09-12_v10r1_w0_attempt2_terminal_assay_and_seal_failure_audit.md`
- `research_notes/analysis/2026-09-12_v10r2_smallest_successor_adversarial_audit.md`
- `research_notes/analysis/2026-09-12_writer_sleep_evidence_chain_audit.md`
- `research_notes/EVIDENCE_TABLES.md`
- `research_notes/IDEAS.md` entries on augmentation, storage/extraction, and
  writer post-training tricks
- exact read-only node-3 attempt-2 step logs for the four first/last-32 loss
  means quoted above
- Allen-Zhu and Li, *Physics of Language Models: Part 3.1* (arXiv:2309.14316,
  v3)

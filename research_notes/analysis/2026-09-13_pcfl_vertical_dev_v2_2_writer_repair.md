# PCFL vertical DEV v2.2: minimal writer repair and release delta

**Date:** 2026-09-13 UTC
**Status:** prospective design delta only; no source, fixture, model, tokenizer,
adapter, job, or GPU execution
**Base protocol:** `2026-09-13_pcfl_vertical_dev_v2_synthesis.md` v2.1
**Independent inputs:** `2026-09-13_pcfl_vertical_v21_writer_fit_audit.md`
and `2026-09-13_full_objective_evidence_and_pcfl_redteam.md`

## 0. Ruling

PCFL remains the critical path. Preserve its world, visibility, child-authorship
boundary, two-SLEEP chronology, fitted scientific arms, native and modular
endpoints, stage order, custody, and stopping rules. Change only the writer
construction and the meaning of a connected-memory pass.

The v2.1 loss-active synthetic PAD targets are removed. They are not neutral:
ATOMS and OLD_REPLAY receive more of them than AUTH and FULL, so a treatment
difference could be caused by unequal synthetic-dialect gradients. In the
authentic arms, every one of the twenty loss-active slots is now an exact
child-authored memory block, either its first registered occurrence or a
prospectively selected exact replay. `EVENT_TWIN` and `LINK_PERMUTE` retain
only their predeclared control-valid derivative blocks at the treatment
positions; those blocks are not described as child-authored. Their replay
fillers repeat the corresponding registered authentic or derivative block
exactly. Ordinary post-EOS tensor padding remains masked from attention and
loss.

One excluded disposable root qualifies the learning rate before either DEV
root is opened. Rank stays 8. There is no rank, epoch, checkpoint, or prompt
sweep.

```text
authentic child rows
  -> exact provenance-bound replay + varied addressed wrappers
  -> source-diverse fixed batches
  -> LOW writer qualification; HIGH only if LOW fails
  -> two untouched DEV roots with the selected recipe unchanged
```

## 1. Exact supersession boundary

This memo supersedes only:

- v2.1 Section 10's loss-active PAD construction and exact active-target-token
  equality;
- the PAD entries in Sections 11.1 and 11.2;
- random-only training order where it conflicts with the source-diverse batch
  invariant below;
- the 14-fit/2,800-update/17-A40-hour maximum, which becomes a conditional
  15--16-fit/3,000--3,200-update/20-A40-hour maximum after qualification
  readout is charged explicitly; and
- any interpretation under which `EVENT_COMPOSITION_ONLY` satisfies the
  objective's connected-knowledge claim.

All other v2.1 text and the prospective binding register remain controlling.
If a source implementation cannot preserve that boundary, stop before
materialization rather than silently redesigning PCFL.

## 2. Twenty admitted slots per arm

The original semantic and predeclared control query-response blocks retain
their bytes, requests, grouping, and addresses. In an authentic arm, a replay
slot repeats one already-admitted exact child block under its same registered
memory request. In a synthetic control arm, it repeats the exact registered
authentic or control-valid derivative block named below. No replay creates a
new address, semantic row, derivative, or target. Replay indices are selected
by the fixed algorithm in Section 2.1 before any model result is inspected.

| arm | first registered semantic/control blocks | exact replay blocks | total |
|---|---:|---:|---:|
| `S1_AUTH` | 17 | 3 balanced authentic EVENT replays | 20 |
| `S1_ATOMS` | 14 | 6 balanced authentic EVENT replays | 20 |
| `S1_EVENT_TWIN` | 17 | 3 balanced twin EVENT replays | 20 |
| `S1_LINK_PERMUTE` | 17 | 3 balanced authentic EVENT replays | 20 |
| `S2_FULL_R0` | 19 | 1 balanced authentic OLD EVENT replay | 20 |
| `S2_FULL_R1` | 19 | 1 balanced authentic OLD EVENT replay | 20 |
| `S2_OLD_REPLAY` | 17 | 2 balanced authentic OLD EVENT + 1 balanced authentic OLD LINK replay | 20 |

The twin and permuted arms remain quarantined controls. A replay never changes
the lineage status of its source block.

### 2.1 Output-blind replay selection

For each EVENT or LINK quota in the table, list eligible registered response
blocks by already-frozen structural slot, not opaque spelling or generated
bytes. Replay sources are distinct within a quota; there are enough eligible
blocks, so sampling with replacement is forbidden. Each block carries its
registered support-row identities and exact response-span hash.

Replay selection is the following finite algorithm:

1. Rotate the eligible structural-slot list by the SHA-256 digest interpreted
   as one unsigned big-endian integer modulo `len(list)`.
2. Enumerate all required-size subsets in lexicographic order under that
   rotated list.
3. For each subset, count total first-occurrence plus replay appearances of
   every eligible support row.
4. Select the subset minimizing, in order: the maximum-minus-minimum support-
   row count; the sum of squared deviations from the mean count; and the tuple
   of rotated structural ranks.

The domain is `(root_skeleton_hash, stage, comparison_family, row_type,
"replay")`, not the individual arm, wherever arms have a predeclared
structural counterpart map. The S1 comparison family is one four-arm family:
AUTH, EVENT_TWIN, and LINK_PERMUTE use the same three corresponding EVENT
positions, and ATOMS uses those same three before selecting its three extras
under the domain suffix `"atoms_extra"` with the common appearances already
counted. The S2 comparison family is one three-arm family: both FULL arms and
OLD_REPLAY share the first OLD EVENT position; OLD_REPLAY then selects one
additional OLD EVENT and one OLD LINK under type-specific suffixes. Exact
comparison-family labels and the counterpart map are frozen before
materialization.

`root_skeleton_hash` is bound before any native generation and excludes every
child-authored or derivative byte; using a post-formation manifest hash as a
pseudorandom seed is forbidden because it would make selection a function of
model output. Selection may depend on whether a required structural span was
admitted only in the fail-closed sense: if any required source span is absent,
formation has failed and no fit is materialized. It never depends on text,
loss, score, future goal, hidden bit, route, or model behavior. The algorithm,
exact subset enumeration, and counterpart mapping are unit-tested before any
native generation. The materialized manifest records each replay slot's source
span hash, derivative
status, support identities, total appearance counts, and byte-identity proof.

### 2.2 What is and is not dose matched

All arms retain exactly:

- 20 query-response slots;
- 8 frozen wrapper views per slot;
- 160 examples per epoch;
- batch size 4, 40 updates per epoch, 5 epochs;
- 200 optimizer updates; and
- the same response-only masking and final-checkpoint rule.

Active target-token totals are reported, not synthetically forced equal. LINK
and NEW treatments necessarily contain their additional truthful information.
Therefore AUTH-minus-ATOMS alone is a fixed-work systems contrast, not a pure
equal-token causal estimate. Connected-memory attribution requires the
triangulation in Section 6: AUTH utility over ATOMS plus the endpoint-specific
LINK_PERMUTE or critical-LINK-cut intervention. No trainable `MISS`, invented
irrelevant prose, fractional weight, duplicated wrapper, or loss-active
placebo may be introduced to equalize target tokens.

Right padding after EOS is permitted only with `attention_mask=0` and label
`-100`. The implementation must pass same-shape alternate-pad-token invariance
for every non-pad logit, supervised loss, and LoRA gradient before fitting.

## 3. Source-diverse fixed batch schedule

The v2.1 coupled epoch permutation is replaced by a prospectively materialized
schedule with these noncompensatory invariants:

1. no batch contains two wrapper views of the same query slot;
2. no batch contains two examples with the same registered source-span hash;
3. in S1, each batch contains at most one LINK-bearing example (there are 24
   LINK view-items, so exactly 24 of 40 batches contain one);
4. in S2, each batch contains at most one LINK-bearing example (after the
   Section 2 repair there are 32 LINK view-items, so exactly 32 of 40 batches
   contain one);
5. all S2 NEW-bearing view-items occupy distinct batches, each alongside three
   OLD/replay examples; the manifest records the frozen number of NEW-bearing
   query slots, proves that eight times this number is at most 40, and proves
   the one-NEW-item-per-batch assignment; and
6. corresponding structural slots occupy the same batch positions across
   paired arms under the counterpart map frozen in Section 2.1 whenever the
   treatment does not replace that position.

Materialization uses a deterministic lexicographic backtracking solver over
structural slot and wrapper IDs with a domain-separated frozen seed. It may
inspect only arm membership, row provenance identity, and OLD/NEW/EVENT/LINK
type. It may not inspect generated bytes, scores, opaque lexical order, future
answers, or fit behavior. The solver must satisfy every invariant exactly;
failure to find a solution is `VS_ASSAY_INVALID`, and random shuffling or
softening an invariant is not a fallback. Each epoch gets a separately
presealed valid schedule, and the exact schedules are coupled across the
calibration and DEV roots through the same structural algorithm.

The solver runs jointly over every arm in a comparison family. Within an arm,
candidate items are ordered by `(structural_slot, wrapper_id)`; indexed batch
positions are rotated by the SHA-256 digest of `(root_skeleton_hash, stage,
comparison_family, epoch_index, "batch")`, interpreted unsigned big-endian
modulo 40. Depth-first backtracking returns the first complete joint solution
in that order. There is no heuristic or implementation-dependent tie break.

This is the supported writer ingredient from the prior positive evidence:
distinct memories meet in training batches. It is not an assertion that this
schedule is biologically or globally optimal.

## 4. Disposable-root writer qualification

After the v2.1 CPU construct/ceiling checks and the disposable formation-only
root have frozen the grammar, use that root's exact admitted S1 AUTH rows to
materialize the final twenty-slot truthful-replay corpus. This root and every
derived adapter are permanently excluded from DEV, confirmation, parenting,
and paper-test lineages.

Run the following sequential rule once:

| fit | configuration | when run |
|---|---|---|
| `CAL_LOW` | rank 8, alpha 16, dropout .05, LR `3e-5`, 200 updates | always |
| `CAL_HIGH` | identical rows, masks, order, init/dropout RNG, optimizer fields, and 200 updates; LR `3e-4` only | only if LOW misses the writer gate while integrity remains valid |

The final checkpoint is the only selectable checkpoint. Diagnostic snapshots
at updates 0/40/80/120/160/200 may be stored but cannot be selected.

"Integrity remains valid" is narrow: corpus custody, masks, schedule,
checkpoint identity, finite execution, zero target truncation, and the frozen
readout roster must all be valid. A failure of any of those is an invalid run
and stops qualification; it does not license HIGH. HIGH is licensed only when
a valid LOW final checkpoint completes and misses one or more semantic,
locality, canary, or refusal thresholds below. LOW and HIGH use the same
presealed inference requests, sampling settings, and per-request seeds.

The writer gate is:

- EVENT local semantic exact at least 15/16 and strict exact at least 14/16;
- LINK local semantic and strict exact at least 7/8;
- at least 15/16 requests in the combined frozen unseen-address and wrong-root
  roster produce exact MISS or a registered non-row refusal, with zero usable
  false rows;
- the 40-item generic canary passes v2.1 Section 12.4; and
- finite loss/gradients, exact source custody, and zero target truncation.

Native ROUTE behavior and the ninth-wrapper diagnostic are recorded but do not
select the writer rate. They test cross-interface use, not addressed storage.

Select LOW if it passes. Otherwise select HIGH only if it passes. If both fail,
stop with `VS_WRITER_QUALIFICATION_FAIL`. Do not add a third heat, more updates,
rank 16, new wrappers, best-checkpoint selection, or a repaired corpus. Both
untouched DEV roots use the selected rate unchanged for S1 and S2.

## 5. Four diagnostic localizers

These diagnostics are collected for C0, CAL, and every final fitted state. They
cannot rescue a failed formation, carriage, locality, native, canary, or route
gate.

1. **Grammar/content NLL.** Report assistant target NLL separately for fixed
   grammar/separators/EOS tokens and opaque-field tokens (child-authored in
   authentic arms; predeclared derivative fields in synthetic controls).
2. **Correct-versus-wrong block margin.** Scorer-side only, compute the
   conditional log-probability of the correct complete registered block minus
   the best type- and row-count-matched wrong block, including EOS. No
   candidate enters a model prompt.
3. **Candidate-free confusion.** Map each raw READ generation to the exact
   registered block it emitted, if any; report the confusion matrix, unique
   output count, refusal, malformed, and false-row counts. One repeated legal
   memory is thereby visible as collapse rather than acquisition.
4. **Unseen wrapper.** Freeze a ninth truthful request wrapper before any
   generation and score every supported address once. It is diagnostic only;
   the eight trained wrappers remain the declared local API.

## 6. Connected-memory claim gate

An overall vertical can still terminate usefully as `EVENT_COMPOSITION_ONLY`:
exact child EVENTs were carried and composed under a goal. That result does not
satisfy the active objective's claim that compiled connections added value.

Connected labels are endpoint-specific. On each DEV root, every connected
label requires S1 AUTH to pass the applicable local, service, and native gates;
authentic LINK reads to pass; EVENT fidelity to remain matched under the
v2.1 arm-pair criterion; and AUTH to exceed ATOMS by at least 4/16 at the
same named endpoint. False-pointer redirection alone cannot substitute for
AUTH-over-ATOMS utility.

- `CONNECTED_MEMORY_SERVICE_DEV` additionally requires replacing the
  prospectively registered critical LINK return with MISS to reduce service
  success by at least 6/16 on that root.
- `CONNECTED_MEMORY_NATIVE_DEV` additionally requires LINK_PERMUTE to redirect
  native behavior to its prospectively registered false-pointer consequence
  on at least 12/16 cases and to reduce authentic native scoring by at least
  4/16 on that root.

The label is released only when the *same* endpoint-specific conjunction
passes on both DEV roots; service evidence on one root cannot be combined with
native evidence on the other. `CONNECTED_MEMORY_BOTH_DEV` requires both labels.
Every label also requires no grammar/content collapse, wrong-root leakage, or
canary failure. Because LINK text is derivable from EVENT content, even a pass
supports only the bounded claim that the compiled LINK organization added
usable value under the fixed read and work budget; it is not a claim of new
information creation.

For a later paper-grade connected claim, this mechanism must replicate under
the independent 16-root confirmation and its registered root-level interval;
two DEV roots are not population evidence.

## 7. Resource arithmetic

The scientific DEV remains 14 fits and 2,800 updates. Qualification adds one
mandatory and at most one conditional fit:

```text
minimum: 15 fits x 200 = 3,000 updates
maximum: 16 fits x 200 = 3,200 updates
```

At the existing 30 A40-minute fit cap, training rises from 7 to at most 8
aggregate A40-hours. The existing 10-hour formation/ceiling/DEV-inference cap
is unchanged, but it does not silently absorb the new qualification readouts.
Each CAL state receives a separate hard maximum of one aggregate A40-hour for
the frozen local, locality, canary, native, ninth-wrapper, and four-diagnostic
roster, executed once at the final checkpoint. The exact request/decode
inventory inherited from v2.1 plus Section 5 must be bound before
materialization; the time cap is not a substitute for that inventory.

The complete v2.2 maximum is therefore 19 aggregate A40-hours if LOW passes
and 20 if HIGH is validly launched. Formation, ceiling, qualification, and
per-root stages still stop cheaply at their first registered failure.

## 8. Release interpretation

A complete v2.2 DEV pass establishes only the bounded two-root mechanism in
the v2.1 claim contract, with the connected qualifier only if Section 6 passes.
It does not establish a lifetime curve, recurrence benefit, textual-memory
superiority, saturation, compression, parenting, or general-domain transfer.

If both roots pass unchanged, release the already-designed independent
confirmation/lifetime campaign. Bind its `FINAL_BATCH` equal-history/equal-dose
recurrence control before the first lifetime output, use an exogenous
opportunity clock rather than success-dependent episode count, and implement
the evolving `ACTIVE_LINKED_TEXT` baseline before claiming superiority.

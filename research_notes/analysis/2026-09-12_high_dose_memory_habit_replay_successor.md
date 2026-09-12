# Smallest decisive high-dose memory + habit-replay successor

**Date:** 2026-09-12  
**Status:** watcher-side design memo only. No builder code or GPU process was
changed or launched.  
**Predecessor:**
`2026-09-12_high_dose_memory_continuation_terminal_audit.md`.

## Ruling in one minute

Run one paired continuation per original teaching seed from the same
seed-matched parent adapter:

1. **MEM:** the completed memory-only objective, reproduced in the new paired
   trainer; and
2. **MEM+HABIT:** the identical memory stream plus one authentic old-habit
   replay microbatch at every optimizer update.

Both descendants get the same 16 device--colour bindings, 20 real encounters
per binding, 80 optimizer updates, rank 8 and LR `3e-4`. The replay descendant
does **not** concatenate habit rows into a larger ordinary batch. It computes
the memory and habit losses separately and optimizes

`J_t = L_memory,t + 1.0 * L_habit,t`.

There is no division by two and no mean across the union of their tokens.
Thus the coefficient on the memory objective remains exactly `1.0`, as in
MEM. Replay adds a retention gradient; it does not silently reduce the memory
gradient to approximately 13% of the update objective.

Run seed 0 first. Continue to seeds 1--2 only if MEM reproduces high-dose
memory acquisition and MEM+HABIT acquires memory while preserving the action
interface. Maximum new spend is six fits and their fixed readouts. A pass
qualifies immediate coexistence of one learned global interface and 16
arbitrary keyed bindings in one adapter under explicit replay. It is not
DREAM, experiential SLEEP, conditional cognition, or lifetime learning.

## Why this is now the right question

The completed high-dose continuation already answers the capacity question.
With 20 distinct optimizer encounters per binding, rank 8 recovered the map
at `14/16`, `16/16`, and `16/16` under both exact and held wording. It also
showed the retention failure cleanly: seeds 0 and 1 lost PREDICT-before-ACT
and correct ACT completely, while seed 2 preserved both.

The next uncertainty is therefore not whether rank 8 can store the map. It is
whether cumulative replay can protect an installed behavior while the same
map is acquired. Do not sweep rank, LR, epochs, paraphrases, or adapter
placement in this experiment. Varied views remain the proper later
compilation design; holding the exact memory rows fixed here is what isolates
habit replay from memory-corpus enrichment.

## Exact paired states

For each optimizer/root seed `s in {0,1,2}`, bind the original SEQ-098/099
**teaching** adapter for that same seed. Do not use a continuation, repetition,
two-habit, parenting, gym, or later-life descendant. Hash every parent file
before cloning it and after both descendants terminate. The parent must be
byte-unchanged and must freshly score:

- PREDICT-before-ACT with the correct prediction on `32/32` fixed arithmetic
  cases; and
- one correct ACT on `32/32`.

Clone those exact weights twice. Both use a newly initialized AdamW optimizer;
no optimizer moments, scheduler state, or prior gradients cross from the
parent. The only arm difference is the registered habit loss coefficient:

| state | memory coefficient | habit coefficient | new fit? |
|---|---:|---:|---|
| `PARENT` | -- | -- | no; lineage and pre-write readout |
| `MEM` | `1.0` | `0.0` | yes; matched memory-only reproduction |
| `MEM+HABIT` | `1.0` | `1.0` | yes; treatment |

The previously completed memory-only artifacts remain an external replication
and diagnosis. They do not replace the new paired MEM arm: using the same
two-stream-capable code, schedules and stateless dropout seeds closes the
possibility that a trainer-path or random-mask change is mistaken for replay.

No sham-parent, deranged-memory, extra-rank or lower-LR arm is needed. Those
answer different questions. Q0 AUTH/DERANGED remains the separate test of
conditional action selection and locality.

## Exact material and schedule

### Memory stream

Use the exact 16 native masked memory rows from the original teaching corpus:
one stable `device-NNN` key, its seeded arbitrary colour, the original single
user chat rendering, and only the one-colour response plus EOS under loss.
No arithmetic or habit target enters this stream.

Construct 20 deterministic permutations of the 16 rows. Each permutation is
one memory epoch and is divided into four batches of four. Therefore:

- optimizer updates: `20 * 4 = 80`;
- appearances of every binding in distinct updates: `20`;
- target tokens per memory batch: `4 rows * (1 colour + EOS) = 8`;
- memory target-token presentations: `16 * 2 * 20 = 640`.

The two arms use the identical row IDs in the identical batch at every update.

### Habit-replay stream

Use all 64 original teaching arithmetic rows and their original native
targets, `PREDICT: correct_sum` followed by `ACT: correct_sum`, plus EOS. The
rows already span different operands and sums. They contain no device key,
colour, memory answer, or evaluation case.

Construct five deterministic permutations of the 64 rows. Each is divided
into 16 batches of four and paired sequentially with the 80 memory updates.
Thus every optimizer update in MEM+HABIT receives four memory rows and four
habit rows, and every old habit row is replayed exactly five times:

- habit row presentations: `64 * 5 = 320`;
- habit stream batches: `80`;
- audited habit target-token presentations: `880 * 5 = 4,400`.

The habit schedule is fixed before model output. No high-loss example is
resampled, and no result-dependent row is added.

## Loss and update arithmetic

Let `T_M(t)` and `T_H(t)` be the nonmasked target-token positions in the two
microbatches at update `t`; context and padding labels remain `-100`. Compute
cross-entropy in FP32 accumulation as

```text
L_memory,t = sum_{j in T_M(t)} CE_j / |T_M(t)|
L_habit,t  = sum_{j in T_H(t)} CE_j / |T_H(t)|

MEM:       J_t = L_memory,t
MEM+HABIT: J_t = L_memory,t + 1.0 * L_habit,t
```

At each update: zero gradients once, run the memory forward/backward, run the
habit forward/backward only in MEM+HABIT, then take exactly one AdamW step.
Use no gradient accumulation divisor, no `/ 2`, no concatenated-token mean,
no dynamic loss weighting, no scheduler, and no clipping not present in the
predecessor. All remaining recipe fields are inherited exactly: frozen
Qwen2.5-7B-Instruct, LoRA rank 8 / alpha 16 / dropout `.05`, every registered
attention and MLP projection, BF16 model execution, target-only loss, batch
size four per stream, no packing, 20 memory epochs, LR `3e-4`, fresh optimizer.

Why separate averaging matters numerically: naive concatenation would expose
`640` memory target tokens beside `4,400` replay target tokens. A union-token
mean would give memory only `640 / 5,040 = 0.12698` of the total corpus-level
target mass. The registered objective keeps its coefficient at `1.0`. For
each memory target token, the cumulative explicit coefficient remains
`20 / 8 = 2.5`; for each two-token binding it is `5.0`, exactly as in MEM.

This controls the *specified loss coefficient*, not the resulting parameter
delta. AdamW and gradient interference are nonlinear; the claim must not say
that memory causes the same weight movement in both arms.

### Randomness pairing

Data permutations and dropout must be separate named streams. Before every
memory forward, enter a forked CPU/CUDA RNG context seeded by a deterministic
hash of `(experiment_id, seed, "memory", update)`. MEM and MEM+HABIT therefore
receive identical memory masks. Habit forwards use a different forked seed
derived from `(experiment_id, seed, "habit", update)` and cannot advance the
memory RNG stream. Record every derived seed. Model generation is temperature
zero under the already fixed readout request; optimizer seeds are never called
independent datasets.

## Required receipts

Before a fit can start, materialization must seal:

- frozen-base file inventory and configured/loaded identity;
- seed-matched parent adapter inventory and the exact SEQ-098/099 source;
- all 16 memory source-event IDs, 64 habit source-event IDs, row bytes and
  context/target span hashes;
- actual rendered token IDs, labels, EOS and pad IDs, per-row target counts,
  and proof of no split, truncation, packing, or loss-bearing padding;
- the complete 80-line update schedule naming the four memory and four habit
  IDs, both RNG seeds and both registered loss coefficients at each update;
- code hashes for materializer, trainer, loader, scorer and reducer; and
- fresh output roots disjoint from every parent and prior artifact.

During training, write one immutable record per update containing the row IDs,
target counts, `sum CE`, separately averaged `L_memory` and `L_habit`, `J_t`,
LR, coefficients, optimizer-step count, finite-status and RNG seeds. The final
manifest must show 80, and only 80, optimizer steps; each binding exactly 20
times; each habit row exactly five times; memory coefficient `1.0` at every
step in both arms. A small deterministic trainer test must fail implementations
that average the two losses or concatenate their tokens.

After serialization, reload each adapter in a fresh process. Bind the loaded
file inventory to every response. Rehash the base, parents, code and fitted
adapters after readout; seal raw requests/responses, reducer output, process
ownership and GPU release. Missing or malformed calls are not scientific
zeros, and partial artifacts never become a completed cell.

## Fixed readout and noncompensatory gates

Each new state receives exactly the predecessor's fixed 64 requests:

- 16 exact training-wording device queries;
- 16 held-wording queries over those same device keys; and
- 32 held arithmetic prompts from the established development panel.

No parent text, memory inventory, demonstration, history, retrieval result or
adapter-selection hint appears at readout. Preserve both strict generation and
candidate-normalized colour log odds, but the strict generation counts are the
gate.

For **every seed separately**, MEM+HABIT must satisfy all of:

1. exact keyed memory at least `14/16`;
2. held-wording keyed memory at least `14/16`;
3. valid one-colour answers at least `15/16` on each memory form;
4. exact correct `PREDICT -> ACT` adherence at least `30/32`;
5. one correct ACT at least `31/32`;
6. valid single PREDICT and single ACT each at least `31/32`; and
7. zero arithmetic outputs containing any of `blue|green|red|yellow`, with no
   repeated phase tag or memory/device phrase. This is the immediate
   interface-spill gate.

The strict adherence parser must be anchored to the entire response: the two
required lines in order, correct values, and no unregistered extra line. Do
not let a correct substring hide a colour monologue or private dialect.

The paired MEM cell in every seed must itself reach `>=14/16` exact and
`>=14/16` held memory; otherwise the pair did not reproduce the predecessor's
acquisition regime and cannot adjudicate replay. Its interface result is an
outcome, not a release prerequisite.

The primary qualification is **three of three MEM+HABIT roots passing every
gate**; means cannot compensate for a failed seed or endpoint. The stronger
causal statement that replay *rescued* reliability additionally requires the
new paired MEM cells to pass the full coexistence gate in at most one of three
seeds, matching the predecessor's qualitative `1/3` pattern. If MEM also
passes all three, report coexistence but not replay necessity. If MEM results
conflict materially with the completed memory-only run, report optimizer
instability and both runs; never discard either.

## Staging and stopping rules

1. Run the paired seed-0 MEM and MEM+HABIT cells first.
2. Stop before seeds 1--2 if either seed-0 cell fails memory acquisition,
   MEM+HABIT fails any interface gate, any material/identity/schedule receipt
   fails, or any loss/gradient is nonfinite.
3. If seed 0 clears, launch the four remaining cells unchanged. No
   result-conditioned change to coefficient, LR, rank, epochs, replay rows,
   order, parser or output cap is permitted.
4. A failed root fails the reliable-coexistence claim. Do not add epochs,
   select a checkpoint, choose the best seed, or average it away.
5. Once all three pairs are terminal, stop this line. Use the failure
   localization below rather than a broad sweep:
   - memory passes, habit fails: the registered replay objective is
     insufficient or conflicts with memory at this heat;
   - habit passes, memory fails: replay/gradient interaction prevented the
     already demonstrated binding acquisition;
   - both pass but colour appears on arithmetic: storage and interface remain
     nonlocal;
   - both pass in MEM without replay: the historical overwrite is unstable,
     so replay necessity is unshown.

## Resource ceiling

Maximum work is six fitted descendants, `6 * 80 = 480` optimizer updates.
Counting one stream-batch for MEM and two for MEM+HABIT gives at most 720
forward/backward stream-batches. The descendant readout is `6 * 64 = 384`
generations; the three parent pre-write checks add at most `3 * 32 = 96`, for
480 total calls and a `30,720` requested-output-token ceiling at 64 tokens each.
Use at most 120 aggregate A40-minutes including fitting, fresh reloads and
readout; no retries or replacement roots. A timeout or infrastructure failure
is missing evidence and may be rerun only from the unchanged presealed plan,
never with a scientific recipe change.

## Licensed and forbidden claims

If MEM+HABIT passes all three roots, the licensed sentence is:

> In a bounded authored continuation, separately weighted replay allowed one
> rank-8 adapter to retain an installed response interface while acquiring and
> extracting 16 arbitrary keyed bindings under changed query wording.

Only if the paired MEM contrast also meets the stronger criterion above may
the sentence add that explicit replay rescued coexistence relative to the
matched no-replay recipe across these three optimizer seeds.

This result would not establish long-delay retention, one-shot memory,
compression, varied-view compilation, locality to unexposed keys, conditional
action selection, reasoning improvement, parenting, child-authored experience,
DREAM, SLEEP, H1/H2, connected knowledge, traversal, expansion, lifetime
learning or superiority to a textual-memory baseline. It is a level-zero
continual-writer safety prerequisite. The next scientific writer gate remains
the repaired Q0 complementary conditional-action falsifier; the next
experience claim still begins only when a child action/outcome provenance edge
enters H1.

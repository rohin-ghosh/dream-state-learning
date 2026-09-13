# Staged successor: target-disjoint composition birth skill and personal-memory 2x2

**Date:** 2026-09-13 PT  
**Status:** documentation-only amendment; no source, material, benchmark,
model, tokenizer, adapter, process, GPU, or remote state changed  
**Amends:**
`research_notes/analysis/2026-09-13_target_disjoint_composition_birth_skill_2x2.md`
at `67dad540`  
**Audit basis:**
`research_notes/analysis/2026-09-13_target_disjoint_composition_birth_skill_2x2_fresh_audit.md`
at `c9fdf65a`

## Decision

Proceed only as a staged developmental program. The scientific estimand and
claim boundary in the original proposal survive. Its fixed `320`-update birth
dose and `800`-presentation personal dose do not.

Every expensive stage below begins only after the preceding component passes:

```text
material is valid
 -> exact-text actor interface works
 -> composition birth separates from active sham
 -> composition works with exact supplied facts
 -> one adapter can retain birth policy and exact personal facts
 -> one-seed DEV factorial has the intended shape
 -> clean three-seed confirmation
```

No stage opens, imports, hashes, reads, or trains on PCFL roots, prompts,
identifiers, traces, outputs, routes, or goal-braid instances. The allowed
shared surface is only the public typed interface specified in the original
proposal. The designer is not blind to the downstream missing capability;
the honest description remains **target-content/topology-disjoint skill
engineering**.

## Common frozen mechanics

- Base: the same exact Qwen2.5-7B-Instruct bytes and tokenizer in every arm.
- Adapter: one all-layer rank-8 LoRA, alpha 16, dropout `.05`, LR `3e-5`.
- Objective: response-only next-token loss; all task, teacher/card, service,
  world, and evaluator text is loss-masked.
- Batch: `4`; no stacking, averaging, or base merge.
- Actor grammar: the original static union of THINK, READ, STEP, and STOP;
  never enumerate task-local valid IDs in one arm.
- Full-task cap: `8` THINK, `12` READ, `8` STEP, `1` STOP, and `4,096`
  generated actor tokens; therefore at most `29` actor calls per rollout.
- Exact-text service: deterministic bytes or `MISS`; it incurs no model-reader
  call. Parametric READ: one separately prompted call to the same mounted
  adapter, capped at `512` generated tokens.
- One-turn command-card, canary, and formation calls are capped at `256`
  generated tokens.
- Formation uses exactly two child calls per admitted EVENT: one irreversible
  action call, then one post-outcome EVENT-commitment call.
- At every writer stage, `40M` means each unique registered memory block is
  presented exactly five times under each of eight W0--W7 training wrappers;
  W8 remains held out.
- C/S fit siblings use coupled initialization, optimizer, batch, dropout and
  decode tapes and exact per-batch supervised target-token totals.
- A malformed, unsupported, over-budget, or invalid turn terminates without
  repair. Every success requires verified arrival followed by exact STOP.

The static action language, limits, parser, world responses, and scorer are
identical across every behavioral arm.

## Stage 0 — deterministic material and arithmetic closure

Materialize no scored model output. Freeze five disjoint material domains:

1. tiny-interface DEV;
2. birth train;
3. birth dose-DEV;
4. untouched birth confirmation; and
5. writer-DEV plus later untouched release.

The birth train has exactly `1,024` supervised child-turn units from `256`
episodes. Because neither total divides evenly across three graph families,
bind the exact family allocation (for example `86/85/85` episodes), the
remainder rotation, and every unit's presentation count. C and S must match
READ/STEP/STOP counts, target lengths, batch slots, route lengths, goal side,
deep-swap state, and display order.

For every scored panel, execute—not merely assert—the exact deterministic
nulls: constant action, lexicographic action, first displayed row,
direct-goal, local outdegree, LINK-presence, action position, fixed READ
schedule, and fixed STOP depth. Each must be `<=1/2`; also enumerate their
predeclared pairwise combinations so two weak cues do not form one strong
shortcut. A scripted oracle must score perfectly.

Bind:

- concrete-identifier and text intersections (`0` across all domains);
- role-labelled canonical hashes of every scored decision core;
- rooted signatures around the first irreversible choice;
- route/depth/goal/action marginals; and
- decision-core motif overlap against the forbidden PCFL and GOAL-BRAID
  specifications without reading any sealed PCFL instance.

Generate once from fixed seeds. An overlap or balance failure invalidates the
material definition; do not resample until a lucky batch passes.

**GO:** all byte counts, balance tables, oracle results, null counts, overlap
checks, hashes, and manifests agree.  
**NO-GO:** any mismatch. No model call is then useful.

**Cost cap:** `0` fits, `0` optimizer updates, `0` model calls, `0` GPU work.

## Stage 1 — tiny 32-task exact-text causal-twin assay

Build `16` opaque causal twin pairs (`32` tasks) with two locally matched
two-hop corridors:

```text
A --p0--> B --p2--> C
A --p1--> D --p3--> E
```

One twin asks for `C`, the other for `E`. Port assignment, identifier
position, and display order are crossed. Only child-issued exact
`READ EVENTS_AT` requests reveal the next edges. The actor must READ, take
irreversible STEPs, compare CURRENT with expectation, and STOP. Use the
smaller cap `4` THINK, `3` READ, `2` STEP, `1` STOP, and `1,536` generated
tokens: at most `10` actor calls per task.

Run the frozen base only. This is an interface/headroom sentinel, not a broad
composition result.

**GO:** scripted oracle `32/32`; every deterministic null `<=16/32`; exact
service receipts and static-grammar accounting pass. Base performance is
recorded without a minimum.  
**RULING:** if base is `>=28/32`, the simple interface already composes; Stage
2 may still test the richer family, but a birth treatment has little claimable
headroom on this tiny assay.  
**NO-GO:** oracle, topology, service, parser, or null failure.

**Cost cap:** `0` fits, `0` updates, `32` rollouts, `320` actor calls,
`49,152` generated actor tokens, `0` model-reader calls.

## Stage 2 — one paired composition/sham birth, DEV-only dose choice

Use one development learner seed and the complete `1,024`-unit C/S corpora.
Start both births from identical base and LoRA initialization:

```text
endpoint D1: 256 updates x batch 4 = 1,024 presentations = 1 full pass
endpoint D2: continue the same optimizer/RNG tape to 512 total updates
             = 2,048 presentations = 2 full passes
```

At D1, evaluate base, C, and S on `32` rich dose-DEV tasks (`16` deep causal
twins), S on `32` fresh command-card tasks, and C/S on `16` generic actor
canaries each.

- If every acquisition gate below passes, select D1 and do not run D2.
- Otherwise, if custody is valid, losses are finite, target coupling is exact,
  and neither C nor S loses more than `2/16` generic canaries relative to
  base, continue **both** lineages to D2.
- D2 is terminal. If it fails, stop this version. Do not add heat, inspect the
  confirmation panel, weaken topology, force READ, or change rank.

At the selected endpoint require:

1. `C >=26/32` whole-chain successes;
2. `C-base >=8/32` and `C-S >=8/32` (if base or S exceeds `24/32`, this gate
   is mathematically impossible and the birth comparison stops);
3. `>=12/16` deep-swap twin pairs both correct;
4. useful autonomous READ before first STEP on `>=28/32` C tasks;
5. C strict typed validity `>=30/32`;
6. every predeclared eight-task stratum `>=6/8` and every deterministic null
   `<=16/32`;
7. S command-card transfer `>=29/32`; and
8. C and S generic actor canaries each `>=15/16`, with a gap `<=1/16`.

After C/S passes, fit one **birth-binding-deranged diagnostic** from the same
base at the selected dose. It preserves C's exact inputs, legal target
multiset, lengths, and batch tape but applies a fixed-point-free mapping from
the decisive deep relation to the legal next branch. On 32 dose-DEV tasks it
must emit its registered mapped first action on `>=24/32`, differ from C on
`>=24/32`, remain typed on `>=30/32`, and keep `>=15/16` canaries. This is a
diagnostic, not a fifth final cell.

**Maximum cost:** five training invocations (C/S D1, two continuations, one
deranged), `1,536` optimizer updates; `192` multi-step rollouts, `5,568`
actor calls plus `144` one-turn calls = `5,712` model calls; `823,296`
generated tokens; `0` model-reader calls. Passing at D1 reduces the fit and
evaluation cost.

## Stage 3 — exact-text component ceiling

Freeze the selected C birth. On `16` writer-DEV tasks (`8` causal twin
pairs) from a topology family absent from birth train and dose-DEV, expose all
needed facts through the exact passive text service while leaving cue choice,
READ order, STEPs, verification, and STOP to the actor.

Require:

- `>=14/16` exact whole chains;
- `>=7/8` twin pairs both correct;
- useful autonomous pre-STEP READ on `>=14/16`;
- strict typed validity `>=15/16`; and
- every deterministic null `<=8/16`.

**NO-GO:** any failure. Personal LoRA storage cannot repair a composition
policy that fails with perfect text memory.

**Cost cap:** `0` fits, `0` updates, `16` rollouts, `464` actor calls,
`65,536` generated tokens, `0` model-reader calls.

## Stage 4 — fourteen-block same-adapter writer sentinel

Using target-free presealed exploration, let the C child execute and commit
exactly `8` world-verified EVENTs. Compile exactly `14` unique registered
blocks: `8` `READ EVENT` and `6` `READ EVENTS_AT`. No goal, route, scorer,
teacher conclusion, or future action enters formation or SLEEP.

Continue one copy of the selected C adapter. Define the writer dose by block:

```text
M = 14 unique blocks
memory = 40M = 560 presentations
birth replay = max(1,024, 40M) = 1,024 presentations
total = 1,584 presentations / batch 4 = 396 updates
```

Each memory block appears exactly five times under each of eight W0--W7
training wrappers. Birth replay covers every one of the 1,024 birth units
exactly once. Use a fresh optimizer but the coupled frozen training recipe.

Before any behavior score, require:

1. all `14/14` blocks exact under W0 and independently `14/14` under unseen
   W8;
2. `14/14` unregistered matched addresses return strict `MISS` with no
   THINK/STEP spill;
3. on a fixed 16-task Stage-2 DEV subset, composition loses at most `1/16`
   from its birth checkpoint and remains typed on `>=15/16`;
4. generic actor canaries are `>=15/16`; and
5. interleaving actor canaries with the W8 reader calls changes neither
   result.

Failure is actor-reader coexistence or storage failure. Do not rescue it with
stacked adapters.

**Cost cap:** one fit, `396` updates; `16` formation calls, `16` canary calls,
`16` multi-step rollouts (`464` actor calls), and `42` reader calls = `538`
model calls; `95,232` generated tokens.

## Stage 5 — smallest interpretable one-seed DEV 2x2

Use one development learner seed and only `4` fresh graph lives, not 16.
Each life contributes `6` admitted EVENT blocks, `4` source-index blocks, and
four predeclared goal/deep-swap tasks. Thus:

```text
4 lives x (6 EVENT + 4 source blocks) = M=40 unique blocks
4 lives x 4 tasks = 16 tasks per evaluated child
```

Both C and S children execute the same presealed actions/outcomes and must
independently commit all `24` exact EVENTs. If either fails, record formation
failure and stop; do not backfill. All four later goals remain withheld until
formation, compilation, and fitting finish. Create three exactly matched
banks:

- authentic evaluated-life bank;
- foreign-life bank under disjoint concrete IDs (**active write/heat
  control**, never called no-write); and
- same-ID fixed-point-free binding-deranged bank.

Every continued descendant uses:

```text
memory = 40M = 1,600 presentations
birth replay = max(1,024, 40M) = 1,600 presentations
total = 3,200 / batch 4 = 800 updates
```

Birth replay presents all 1,024 units once plus a fixed balanced repeat of
576 units. Train five descendants: `S0 foreign`, `S1 authentic`, `C0 foreign`,
`C1 authentic`, and `CD same-ID deranged`. Preserve and score literal
zero-update S-birth and C-birth checkpoints.

### Storage/coexistence gates

- Every fitted bank is exact on `>=23/24` EVENT and `>=15/16` source blocks
  under W0 and independently W8 (`>=38/40` each wrapper).
- S1/C1 differ by no more than `1/40` at either wrapper.
- S0/C0 learn their foreign bank at the same gate and return `0/40` exact
  evaluated-life blocks; CD learns its assigned deranged bank at the same
  gate.
- C0, C1, and CD lose at most `1/16` on the fixed composition panel; S0/S1
  lose at most `1/16` on the command-card panel; every fit keeps `>=15/16`
  generic canaries.

### Development behavior gates

For successes `Yxy` out of 16:

```text
own-versus-foreign under C: C1-C0 >= 4
composition under own bank: C1-S1 >= 4
interaction: (C1-C0)-(S1-S0) >= 2
```

Also require `C1>=12/16`, at least three of four lives score `>=3/4`, useful
served READ before first STEP on `>=14/16`, and `1.0` selected-port legality.
C-birth-only and C0 must each be at least four successes below C1; their
difference may be at most `2/16`.

On eight preselected C1 tasks, replacing one indispensable registered block
with MISS must lose `>=4/8`; an equal-token irrelevant cut may lose `<=1/8`.
CD must redirect the registered first action on `>=6/8` causal pairs. These
are development gates, not paper statistics.

**Cost cap:** five fits, `4,000` updates; `176` multi-step rollouts (`5,104`
actor calls), `208` formation/canary/sham calls, and `1,632` reader calls =
`6,944` model calls; `1,609,728` generated tokens.

## Stage 6 — clean three-seed confirmation only after Stage 5 passes

Reset to clean identical base/LoRA starts. Freeze the selected D1 or D2 birth
dose, all generators, prompts, corpora, block schedules, thresholds, and RNG
tapes. Open the untouched birth-confirmation family only now.

Run the original three paired C/S birth qualification on `128` tasks per
child, preserving all original gates (`C>=104`, C-base and C-S `>=32`,
`48/64` twin pairs, `112/128` useful READ, `122/128` typed, S command card
`>=115/128`, stratum and null gates). Release every qualified learner seed;
never select one.

For each seed, form `16` untouched target-free graph lives. Each contributes
exactly `6` EVENT-address and `3` source-index blocks:

```text
M = 16 x 9 = 144 unique blocks per bank
memory = 40M = 5,760 presentations
birth replay = max(1,024, 40M) = 5,760 presentations
total = 11,520 / batch 4 = 2,880 updates per descendant
```

Birth replay gives every birth unit five presentations and a fixed balanced
sixth presentation to 640 units. Authentic, foreign, and deranged banks match
unique counts, source fanout, block cardinality, wrappers, identifier-token
lengths, target tokens, and batch tape.

Run the full `S0/S1/C0/C1` factorial (`12` personal fits), literal S/C birth-
only anchors, exact-text ceilings, storage/coexistence gates, wrong-life
mounts, and the original 32-task release gates. Only after the primary 2x2
passes all three seeds, train the three same-ID deranged terminal siblings and
run indispensable/irrelevant cuts.

Birth-only anchors have an empty registry and receive deterministic `MISS`
without a model-reader call. They are literal no-update diagnostics, not
write-heat-matched controls; S0/C0 foreign banks supply the latter.

The final estimands are named literally:

```text
evaluated-bank substitution under C: C1-C0
evaluated-bank substitution under S: S1-S0
composition effect with evaluated bank: C1-S1
composition effect with foreign bank: C0-S0
interaction: (C1-C0)-(S1-S0)
```

Keep the original behavior gates: `C1>=24/32`, `>=11/16` goal-twin life
pairs, `C1-C0>=8`, `C1-S1>=8`, interaction `>=4` with no negative seed,
`>=24/32` useful autonomous served READ, and legal STEPs only. Exact-text C
must be `>=28/32`; authentic S1/C1 storage must be matched; foreign and
same-ID banks must be demonstrably acquired; birth policy and generic actor
canaries must survive. Treat learner seeds as optimization robustness and
the 16 graph lives as the release-data units; nested goals are not IID.

### Exact full-confirmation resource cap

If D2 is selected:

- six birth fits: `6 x 512 = 3,072` updates;
- twelve primary personal fits: `12 x 2,880 = 34,560` updates;
- three post-positive deranged fits: `3 x 2,880 = 8,640` updates;
- **total: 21 fit jobs and at most 46,272 optimizer updates** (`37,632`
  before the post-positive deranged controls).

With every full-task rollout at the registered maximum, the complete plan,
including birth qualification, exact-text ceilings, post-sleep retention,
primary cells, both birth-only anchors, wrong-life mounts, cuts, and deranged
readout, contains at most:

| multi-step component | rollouts |
|---|---:|
| base plus six birth qualification states | 896 |
| three exact-text ceilings | 96 |
| C0/C1/CD post-sleep birth retention | 1,152 |
| four primary cells | 384 |
| S/C literal birth-only anchors | 192 |
| C wrong-life mounts | 96 |
| indispensable plus irrelevant cuts | 96 |
| same-ID deranged readout | 96 |
| **total** | **3,008** |

The one-turn count is `1,152` formation + `384` birth sham + `768`
post-sleep sham-retention + `672` canary calls = `2,976`. The model-reader
count is `2,784` exact-storage-gate calls plus `8,064` task READ maxima =
`10,848`: storage is `960` authentic + `1,344` foreign + `480` deranged;
task READs are `4,608` primary + `1,152` wrong-life + `1,152` cuts + `1,152`
deranged.

- `3,008` multi-step rollouts;
- `87,232` actor decision calls;
- `2,976` one-turn formation/sham/canary calls;
- `10,848` model-reader calls;
- **`101,056` model calls total**; and
- **`18,636,800` generated tokens total** under the bound actor (`4,096`),
  one-turn (`256`), and reader (`512`) caps.

These are hard work caps, not a wall-time forecast. Before Stage 6, Stage 5
must record measured training tokens/update, seconds/update, actor tokens/s,
reader tokens/s, engine-load time, and peak memory. A full GPU-hour estimate
is invalid without those measurements. At most 21 one-GPU fit jobs means at
least three fit waves under perfect eight-GPU parallelism, before evaluation
and reload overhead.

## Aggregate pre-confirmation cap and final ruling

If every development stage runs to its maximum, Stages 1--5 consume:

- `11` fit invocations and `5,932` optimizer updates;
- `13,978` model calls; and
- `2,642,944` generated tokens.

Most failure modes stop far earlier: Stage 1 costs no fit; Stage 3 costs no
fit; Stage 4 risks one `396`-update continuation; only a coherent one-seed
factorial unlocks the 46,272-update confirmation ceiling.

**Final recommendation: GO with this staged amendment.** A negative at a
bound stage has one local meaning. A positive final interaction can support
only the bounded claim that a target-disjoint inherited composition policy
enabled one fixed 7B child to cue, read, interpret, and act on separately
sleep-written own-life EVENT memories after active context was removed. PCFL,
parenting, recurrence, and lifetime improvement remain separate future tests.

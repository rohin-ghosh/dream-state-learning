# Astra fixed-coaching parenting DEV: independent terminal audit

**Date:** 2026-09-13 UTC  
**Role:** independent terminal auditor  
**Disposition:** execution/custody **PASS**; targeted in-context coaching
**positive**; child-record write and parent-free improvement **positive**;
parenting-specific persistence **not shown**  
**Scope:** read-only audit of all three finalized node-2 runs. No source,
fixture, model, tokenizer, adapter, job, or GPU state was changed.

## Verdict

The fixed process reminder did exactly steer the field it named while it was
present. Across the 48 apply opportunities, the coached child preserved the
pre-action `predicted` field and derived `relation` correctly in `48/48`
records, versus `38/48` under active-neutral contact. This targeted effect was
positive in every seed (`+2/+5/+3` on each of those fields). It is real
**transient coaching**, not yet learned parenting.

The stricter whole-record result was mixed: coached P versus neutral N
produced `16/14`, `16/11`, and `11/13` eligible apply records, or `43/48`
versus `38/48` pooled. In seed 2, coaching fixed all prediction/relation fields
but the child copied the executed `try` incorrectly in five records, so the
whole-record P-minus-N effect was `+2/+5/-2`. The child was steered
specifically, not made uniformly better.

After the record write and complete parent removal, P and N were **identical within every
seed** on fresh held record formation: `16/16`, `16/16`, and `13/16`, totaling
`45/48` for each arm. Their original parents scored `11/16`, `8/16`, and
`8/16`, totaling `27/48`. Thus writing admitted child records produced a large
parent-free gain (`+18/48`) in both arms, but the coaching-specific contrast
was exactly zero. This establishes a useful own-record write result; it does
not establish fixed-guidance amortization, adaptive parenting, or a mediated
parent -> child-record -> weight -> behavior effect.

## 1. Receipt custody and protocol fidelity

The frozen protocol is
`research_notes/astra_memos/ASTRA_PARENTED_RECORD_DEV_2026-09-13.md`, SHA-256
`bae29cfc48d9ae0922531d306bef1434bcc7296f2ae71a4ad6493da2a5dfb964`.
The archived runner and core pins independently match their plans:

- runner: `54cad8a6eeb5ae8af08213efe60f4c8047879991ca77f7a30d8be548659699f8`;
- core: `68ef29fcc162dbbf5fe1becf4c09b86ed5bc1f8a79e373276dd8ba3cda88e688`.

| seed | plan SHA-256 | completion SHA-256 | scores SHA-256 | collection-file SHA-256 |
|---:|---|---|---|---|
| 0 | `7bf29472f7290c7b5f856527b837689b0668f16b63a151198072c5e423c98455` | `edd8b4ff1756de1c60b51dfc76471ed3885b09cb559c8842eff5fd07a4f65ed4` | `643694aad203622f76b46d9eb0b1984c7ca62d95045122abaa36320a9b8a1ffd` | `7407b9bdab6b6f02355b655c404d4e1a01588168edab05d3c0051ddf8c8fc9f0` |
| 1 | `6e30c79caf85666f6db678c9765e93e33a595a200f0f598a01b5a2d516736d47` | `8433c8f302d91dd3b0de1cd1a576e1794418521f99ff396866839d10277facfe` | `3cf132571955e66777c7639e332269a0ccf662565027467a0a26467091c5f787` | `bd4390a693f70f439e3a3d71cc37a7882cae254f7792afa318be6d25c9cca665` |
| 2 | `c184ddb8a273da5472b18fae3f4f99915cbe53f7dd7c73826b112037f5303a96` | `cccbb4512cdf60236d00d8e056d37de1a3368724e9f064d693ec59a382007cc6` | `693187ae8958ad84c845d56b498fc5fc3b257f3466ba2526f5aed4ee759ae3ac` | `552085685ab98a300aeca2dd7f8b6240d7db3575db57bcad7e4a252704a5ab33` |

Direct checks found, for every seed:

- plan and completion bytes hash to the values in the collection;
- all nine expected native stages exited `0`, recorded
  `group_absent=true`, and recorded `gpu_vacant=true`;
- P and N forked the same `392`-tensor initialized state, and each fit's
  source state exactly equaled that initializer;
- both arms made all `16/16` apply wake calls, real world executions, and
  record calls per seed (`48/48` pooled per arm); pre-contact whole-record scores were matched within seed
  (`3/4`, `2/4`, `2/4` in both P and N);
- all admitted rows are unique DEV-apply child rows, with only the four record
  fields in their raw targets and the exact child target plus EOS supervised;
  and
- the P/N contact literals occur in formation artifacts but not in any
  dataset, training file, held request, or retention request. Parent and
  restatement text were therefore visible during childhood but not trained
  as targets and not present at deployment.

This is a faithful execution of the fixed author-coaching protocol. It is not
an adaptive-parent experiment: there were zero parent-model calls.

## 2. Childhood material and unequal write dose

| seed | P eligible/admitted | N eligible/admitted | P-minus-N | P updates | N updates |
|---:|---:|---:|---:|---:|---:|
| 0 | 16/16 | 14/16 | +2 | 128 | 112 |
| 1 | 16/16 | 11/16 | +5 | 128 | 88 |
| 2 | 11/16 | 13/16 | -2 | 88 | 104 |
| **pooled** | **43/48** | **38/48** | **+5** | **344** | **304** |

Every admitted row was presented eight times. Consequently, the experiment
contains the protocol's declared material-yield/dose imbalance: P received
`43` rows and `344` optimizer updates; N received `38` rows and `304` updates.
This is appropriate for asking whether coaching creates more writable child
material, but it is not an equal-data writer comparison. It prevents cleanly
attributing any later P/N difference to lesson semantics rather than amount or
composition of training. Here the later P/N difference is zero despite the
imbalance.

The source diversity is also narrow. Each apply arm used only two or three
distinct action triples. On held tasks, `32/48` P executions and `34/48` N
executions used a triple absent from that arm's apply set, but the receipts
correctly warn that new IDs/triples do not establish unseen rules or absence
of base-model knowledge.

## 3. Parent-free held formation

| seed | original | N after own-record write | P after own-record write | P-minus-N |
|---:|---:|---:|---:|---:|
| 0 | 11/16 | 16/16 | 16/16 | 0 |
| 1 | 8/16 | 16/16 | 16/16 | 0 |
| 2 | 8/16 | 13/16 | 13/16 | 0 |
| **pooled** | **27/48** | **45/48** | **45/48** | **0** |

Fieldwise, both written arms reached `48/48` on `observed`, `predicted`, and
`relation`, and `45/48` on `try`; the initial parents were `48/48`, `27/48`,
`27/48`, and `48/48`, respectively. The writer therefore transported the
selected correct record behavior beyond the parent/contact context. Neutral
experience alone was sufficient to reach the same endpoint, however.

The held panel is also nearly saturated after either fit (`45/48`), leaving
only three errors of headroom. The observed zero coaching contrast must not be
reported as evidence that parenting cannot persist or that P and N are
equivalent; this assay has little differential headroom after the neutral
write.

Exact canonical serialization did not follow semantic performance: pooled
strict counts were original `11/48`, N `0/48`, and P `4/48`. The outputs were
still semantically source-faithful/production-eligible. This distinguishes a
useful record skill from exact-byte style preservation.

## 4. Retention and canary

The original task-specific parent baseline was noncontemporaneous but bound
itemwise: `47/48`, `48/48`, and `48/48`, or `143/144` pooled.

| seed | N old task | P old task | N/P generic canary |
|---:|---:|---:|---:|
| 0 | 47/48 | 47/48 | 12/12, 12/12 |
| 1 | 47/48 | 47/48 | 12/12, 12/12 |
| 2 | 46/48 | 44/48 | 12/12, 12/12 |
| **pooled** | **140/144** | **138/144** | **36/36, 36/36** |

N lost `3/143` originally correct task items; P lost `5/143`, including four
in seed 2. Neither arm gained old items. The generic canary was perfect in all
six descendants, so it did not detect this task-specific interference. This
is interface preservation on the narrow canary, not no-harm certification.
The protocol intentionally used no own-source protective replay.

## 5. Work accounting and stored pass logic

Each seed used exactly `300` calls: `84` formation, `96` parent-free held, and
`120` retention. Across the cohort this is `900` child calls, zero parent
model calls, six fits, and `648` optimizer updates (`240/216/192` by seed), all
below the frozen caps.

The stored logic is internally correct but deliberately non-adjudicative:

- `automatic_pass=false` is hard-coded in the protocol, core, completion,
  collector, and every terminal score artifact;
- `scientific_pass=null` and `outcome_gate=null` are likewise preserved; and
- the collector explicitly promises never to set an efficacy gate or promote
  H1/H2.

Therefore `automatic_pass=false` does **not** mean a computed threshold failed.
It means this DEV run was prohibited from automatic promotion regardless of
outcome. The independent scientific reading is: targeted coaching worked only
in context; admitted child-record SLEEP caused parent-free improvement; the
parenting-specific benefit did not survive as a measurable contrast; and
task-specific retention was imperfect. CONF should remain untouched on the
basis of this experiment alone.

## 6. Claim boundary

This run supports the bounded statement:

> A fixed answer-free reminder reliably corrected the named prediction/outcome
> fields while present. Training only on world-admitted child records then
> improved fresh parent-free record formation, but an active-neutral child
> improved equally; no durable parenting-specific advantage was detected.

It does not show adaptive teaching, learned receptivity to parenting,
specific parent-to-weight mediation, generalization to unseen rules, exact or
paraphrase memory readback, connected memory, lifetime compounding, H1/H2, or
the whole Dream-LoRA-Think architecture.

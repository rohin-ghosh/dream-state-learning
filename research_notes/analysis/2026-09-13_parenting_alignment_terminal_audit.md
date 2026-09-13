# Fixed-lesson alignment DEV: independent terminal audit

**Date:** 2026-09-13 UTC  
**Disposition:** execution/custody **PASS**; registered feasibility vector
**FAIL**; semantic lesson restatement apparent but required process-state
transformation **not established**  
**Scope:** read-only audit of the three once-collected node-2 roots. No source,
fixture, model, tokenizer, adapter, job, or GPU state was changed or rerun.

## Verdict

The preregistered result is a clean null on the behavior the assay required.
Across all `48` tasks per arm, `PROCESS_USE`, `RECORD_FAITHFUL`, and
`FULL_MATERIAL` were `0/48` for ALIGNED, SWAPPED, and NO_PARENT. ALIGNED
therefore beat neither control, repetition produced no measurable improvement,
and no child record from this assay qualifies for a writer test.

That strict null needs one important qualification. The frozen RESTATE checker
accepted only `2/12` ALIGNED and `2/12` SWAPPED contacts, yet direct bounded
inspection of all 24 raw restatements found that every one appeared
semantically faithful to its delivered lesson. For example, “initial
prediction” and “subsequent observation” were rejected because the lexical
checker did not recognize them as the required prior/outcome scope. This makes
registered RESTATE an under-sensitive lexical readout, not evidence that the
child failed to understand the prose.

The downstream failure is nevertheless real under the frozen contract. None
of `144` task NOTES had an accepted state schema: the model usually copied the
whole public task or emitted a partial receipt and omitted a required field
(especially explicit `relation`). None of the `137` attempted records
preserved all required bindings across `address + source + event`. The child could
paraphrase the lesson, but it did not reliably convert it into the exact
task-state operation and record needed downstream.

There is post-hoc evidence of partial lesson-conditioned processing in two
roots: seed 0 compressed P state into a single receipt-shaped NOTE on `5/8`
ALIGNED tasks versus `0/8` SWAPPED and `0/8` NO_PARENT; seed 2 selected a
single latest receipt on `8/8` aligned C tasks versus `1/8` SWAPPED and `0/8`
NO_PARENT. Seed 1 copied the full task state on all `16/16` tasks in every arm.
These raw-shape observations help localize the bottleneck, but they were not
the registered score and cannot rescue the failed vector.

This experiment tests only immediate fixed-lesson alignment with the child's
restatement still in context. It contains no SLEEP, fitting, persistence,
adaptive parent, or parent-free test.

## Exact registered results

Each lesson arm had four contacts and 16 task opportunities; NO_PARENT had 16
task opportunities and no contacts.

| seed | arm | RESTATE | PROCESS_USE | EXECUTED | RECORD_FAITHFUL | FULL_MATERIAL |
|---:|---|---:|---:|---:|---:|---:|
| 0 | ALIGNED | 0/4 | 0/16 | 16/16 | 0/16 | 0/16 |
| 0 | SWAPPED | 0/4 | 0/16 | 13/16 | 0/16 | 0/16 |
| 0 | NO_PARENT | n/a | 0/16 | 16/16 | 0/16 | 0/16 |
| 1 | ALIGNED | 0/4 | 0/16 | 16/16 | 0/16 | 0/16 |
| 1 | SWAPPED | 0/4 | 0/16 | 15/16 | 0/16 | 0/16 |
| 1 | NO_PARENT | n/a | 0/16 | 16/16 | 0/16 | 0/16 |
| 2 | ALIGNED | 2/4 | 0/16 | 16/16 | 0/16 | 0/16 |
| 2 | SWAPPED | 2/4 | 0/16 | 14/16 | 0/16 | 0/16 |
| 2 | NO_PARENT | n/a | 0/16 | 15/16 | 0/16 | 0/16 |
| **pooled** | **ALIGNED** | **2/12** | **0/48** | **48/48** | **0/48** | **0/48** |
| **pooled** | **SWAPPED** | **2/12** | **0/48** | **42/48** | **0/48** | **0/48** |
| **pooled** | **NO_PARENT** | **n/a** | **0/48** | **47/48** | **0/48** | **0/48** |

All PROCESS_USE, RECORD_FAITHFUL, and FULL_MATERIAL strata below are zero; the
remaining component is typed execution.

| seed | arm | P execution | C execution | first delivery | second delivery |
|---:|---|---:|---:|---:|---:|
| 0 | ALIGNED | 8/8 | 8/8 | 8/8 | 8/8 |
| 0 | SWAPPED | 8/8 | 5/8 | 8/8 | 5/8 |
| 0 | NO_PARENT | 8/8 | 8/8 | 8/8 | 8/8 |
| 1 | ALIGNED | 8/8 | 8/8 | 8/8 | 8/8 |
| 1 | SWAPPED | 8/8 | 7/8 | 8/8 | 7/8 |
| 1 | NO_PARENT | 8/8 | 8/8 | 8/8 | 8/8 |
| 2 | ALIGNED | 8/8 | 8/8 | 8/8 | 8/8 |
| 2 | SWAPPED | 8/8 | 6/8 | 7/8 | 7/8 |
| 2 | NO_PARENT | 8/8 | 7/8 | 8/8 | 7/8 |
| **pooled** | **ALIGNED** | **24/24** | **24/24** | **24/24** | **24/24** |
| **pooled** | **SWAPPED** | **24/24** | **18/24** | **23/24** | **19/24** |
| **pooled** | **NO_PARENT** | **24/24** | **23/24** | **24/24** | **23/24** |

ALIGNED preserved the typed action interface better than SWAPPED, particularly
on C tasks. This is a secondary component result; the aligned package still
never produced the required process state.

Combining the three separately collected roots reproduces the prospective
feasibility vector:

- RESTATE at least `3/4` in two roots: **FAIL** (`0/3` roots).
- ALIGNED-minus-SWAPPED PROCESS_USE at least `+4/16` in two roots: **FAIL**
  (`0/3`; all differences zero).
- no ALIGNED-minus-SWAPPED root at or below `-4/16`: **PASS**.
- ALIGNED-minus-NO_PARENT PROCESS_USE at least `+2/16` in two roots: **FAIL**
  (`0/3`; all differences zero).
- no ALIGNED root more than `2/16` below NO_PARENT: **PASS**.
- second-delivery PROCESS_USE at least first-delivery in two roots: formally
  **PASS**, but vacuous (`0 == 0` in every root).
- at least eight ALIGNED FULL_MATERIAL rows in two roots: **FAIL** (`0/3`).

The full vector therefore fails. Each stored report correctly leaves its gate
incomplete because it contains only one of three roots; the all-root result
above is an independent exact recombination, not a stored promotion decision.

## Raw-output localization

The task-level outer JSON/action contract was largely preserved: wake format
and typed action were valid on `48/48` ALIGNED, `42/48` SWAPPED, and `47/48`
NO_PARENT tasks. However:

- accepted NOTE shape/content/canonical form was `0/144`;
- records were attempted on `48/48`, `42/48`, and `47/48` tasks respectively,
  but RECORD_FAITHFUL was zero throughout;
- a complete five-field event subobject appeared in `25/48` ALIGNED,
  `26/48` SWAPPED, and `10/48` NO_PARENT outputs, but frequently without the
  required address/source and sometimes with incorrect bindings; and
- exact canonical serialization was zero for every wake and record.

This separates three capabilities: the child could restate the advice in
natural language; sometimes changed which public state it surfaced; but could
not reliably express that state in the required structured operation or carry
it into a faithful full record. A future assay should calibrate a neutral,
task-family-independent expression interface before treatment, or freeze a
broader blinded semantic scorer prospectively. The current outputs must not be
rescored into a positive result after inspection.

## Custody, sources, and preparation

The frozen protocol is
`research_notes/astra_memos/ASTRA_PARENTING_ALIGNMENT_DEV_2026-09-13.md`,
SHA-256
`5c53d6aa850b3a3a409c255ab9b28ce3b090f7325f35688437e42a86b1cccce5`.
The runner, scorer core, and launcher custodian were pinned at
`712248f1fc86b026e68e9cfbc791d3b441c6ded53db82f7622f8f2cd2b8b8c2a`,
`71311d3d9add1f485289c6ee6824ef758393193ee05bcc088674d12697b11010`,
and `cb61e7f8e47af782ac25e6ace3cc9be67e7c25856b5863973dd1643630f065bc`.

| seed | plan SHA-256 | completion SHA-256 | report SHA-256 |
|---:|---|---|---|
| 0 | `f517e0a77bf4705f8a7aebf9ff4472da44838493b13fb8e592c64378134956c1` | `8333de4b4020aa16588a4400585a66d69bcc3b4e7d5781156f1b1d9482a88d2a` | `9b4be0ea07766f4363adadc6cb5d073bb14fc9d60db20a2c2cb28cfc774c4380` |
| 1 | `78b316e79e303b68ac326671f350c5e2735ada80ce2750d734406175d2f51535` | `c5fd2c1955222d79a8209f5056cdc67abc2fcc8cc2cdff107ef95b9228baaf86` | `f6f84ac9fce656da851213af5fe2fe08d0c65489b5f7dd4560cc697ae611de46` |
| 2 | `34079b169137d8e2fdbd16e1b5be902d216c974e84a2526632a3fa068d54649e` | `4b25e39e060f4746d87cfd010917fbf0779fb741a4bea9a7ebc507631c3f7991` | `2d182408dcf83abf2f97a40a08b97954c4f0a677a7ca4232e35735989b2ca612` |

Direct audit found:

- all arms within a seed used the same original pre-memory perception adapter;
  adapter tensor hashes were seed 0
  `8bfe8b9d647b58b064733ed24d8aaa97cd79d7012795232305838a23ac415432`,
  seed 1
  `c9700a2f46b36e64ce9e1845cd4601d3d0da086afbaba9efbc93012af936e0e2`,
  and seed 2
  `5d198acfc7bf2f2c552b6b180688bce5d7fe00b1afd2eea7d056fc44a2e505da`;
  no coaching or memory descendant initialized the assay;
- all nine cold arm stages exited `0`, recorded `group_absent=true` and
  `gpu_vacant=true`, and deterministic replay audits were consistent;
- all three preparations completed in `17.81--18.56` seconds, below the
  180-second bound; controllers completed in `576.37`, `777.75`, and `582.94`
  seconds, below 3,600 seconds; collectors completed in `5.58--5.68` seconds,
  below 180 seconds;
- each root has one `retry=false` collection claim, one immutable collected
  directory, matching report/collection hashes, and no failure artifact; and
- the two lesson arms had the same fixed lesson multiset (`172` tokenizer
  tokens); P and C were individually `42` and `44` tokens. Dynamic prompts
  were rendered and rechecked at collection.

The manifest reports `360` task IDs distinct from its explicit inventory of
known earlier IDs. Its own caveat is binding: this proves disjointness only
against the supplied known inventory, not universal unseen-exposure
certification. These are exposed DEV perception roots, not final clean
children.

The stored `native_identity_verified=false`, `automatic_pass=false`, and
`fit_authorized=false` values are deliberate hard-coded non-promotion
sentinels in the frozen core. They do not contradict the collector's separate
`native_capture_custody_checked=true` receipt. No fits, optimizer updates, or
adaptive parent-model calls occurred.

The arm contrast also remains package-level and narrow. ALIGNED and SWAPPED
match fixed lesson multisets but not realized outputs, contexts, or call counts;
NO_PARENT is not token-matched. The raw restatement remains in context, so the
assay does not separate restatement mediation from the delivered lesson. Its
public receipts were harness-provided earlier events, not experiences produced
by the current child. Seed order is counterbalanced only `2:1`, confounded with
learner root, and cannot support an order or repetition-learning claim.

## Work accounting and claim boundary

The run used `305` child calls (`108` ALIGNED, `102` SWAPPED, `95`
NO_PARENT), `122,881` prompt tokens, `37,116` output tokens, zero parent-model
calls, zero fits, and zero updates. The seven calls below the `312` ceiling are
exactly record calls withheld after invalid actions. All observed calls ended
normally. Summed native generation time was `1,470.65` seconds. Launcher start
through once-only collection was `583.32`, `784.75`, and `589.93` seconds,
totaling about `0.544` A40-hours—well below the five-hour allocation cap.

The only defensible registered conclusion is:

> In this three-root DEV assay, aligned answer-free process lessons did not
> produce the required structured state use or faithful child records more
> often than swapped lessons or no parent. The child semantically restated the
> lessons and showed limited post-hoc evidence of lesson-conditioned state
> selection, but the fixed expression/readout interface prevented a valid
> positive alignment result.

It does not test or support SLEEP, persistence after parent removal, adaptive
teaching, autonomous learning, connected memory, lifetime compounding, H1/H2,
or the Dream-LoRA-Think system.

# EVENT-retention-v2 runtime: fresh independent audit

Auditor: fresh Codex subagent, 2026-09-13 PT. Reviewed Astra helper commit
`71adf462cfdc17d94f95298e76949e08da38e410` read-only. I did not run a model,
tokenizer, fit, or GPU job and did not modify implementation. Verdict applies
to those exact committed bytes; later uncommitted helper edits are not part of
the reviewed source.

## Verdict

- **Initial three-seed `A200` acquisition screen: CONDITIONAL GO.** The source
  correctly binds the same authenticated A4/B4 bank to optimizer seeds 0/1/2,
  fits only A, reads fresh C0 and A200 in separate processes, preserves raw
  captures, and leaves qualification/promotion false. Before launch, commit the
  already-written test corrections and obtain one terminal green suite plus a
  sealed native preparation manifest.
- **All descendants / full retention assay: NO-GO.** One concrete warm-start
  receipt mismatch will reject normal descendants, and the full campaign and
  final reducer are not implemented. This does not invalidate an acquisition-
  only launch; it forbids claiming that the complete retention experiment is
  launch-ready.

## Blocking finding 1: real warm starts and the v2 validator disagree

`gpu/astra_pcfl_event_sequence_v2_fit.py::validate_warm_tensors` requires
`dtype_conversions` to contain **every** LoRA tensor and then indexes every
tensor in that map. But `organism_v6/train_adapter_v3.py::_warm_initialize`
records `dtype_conversions` **only when source and loaded dtypes differ**.
Therefore an ordinary same-dtype warm initialization (the likely fp32-to-fp32
PEFT path) produces an empty or partial map and is rejected after the fit.

The unit test misses the mismatch: it hand-constructs same-dtype conversion
entries for every tensor, a shape the production writer never emits. Repair by
making the validator accept the writer's sparse "actual conversions only"
receipt while still proving `initialized_state == source converted to the
loaded dtype`, or change the writer contract prospectively. Add an end-to-end
warm test that invokes the real `_warm_initialize` receipt path, not a
handwritten manifest.

Affected arms: `B200_NEW_DOSE`, `B400_FIXED_WORK`, and `REPLAY400`.
`CLEAN_CUM600` is cold but still cannot proceed until acquisition is qualified.

## Blocking finding 2: the complete campaign is intentionally absent

The committed campaign executes only nine acquisition stages:

```text
for seed 0,1,2: A200 fit -> C0 readout -> A200 readout
```

It ends at `ACQUISITION_CAPTURED_NOT_QUALIFIED`. It does not create the closed
acquisition request, call the raw reducer, write descendant inputs, run the four
descendants, read all final states, or reduce the paired vectors/contrasts.
The lower-level fit/readout APIs describe those states, but APIs are not a full
campaign. A full-assay GO needs outcome-independent orchestration that, for
each passing seed, launches all four branches regardless of B200 outcome and a
reducer that reports exact A/B vectors plus both predeclared replay contrasts.

## Exact acquisition gate: correct

The raw reducer recomputes strict correctness from captured response bytes and
requires `finish_reason == stop`; it does not accept a caller Boolean or repair
answers. Its primary W8 gate is exactly:

```text
C0:   A=0/4, B=0/4
A200: A=4/4, B=0/4
```

W0 remains descriptive and cannot substitute for W8. A failing seed has
undefined retention and withholds its own descendants without a dose rescue.
The reducer also rejoins model/base/material/source identities, the exact A200
fit, adapter mount bytes, process/GPU release, all sixteen raw calls, token
counts, sampling, and immutable inventories. This is strong raw-artifact
custody for the small DEV screen.

## Schedule and seed arithmetic: correct

Per optimizer seed, the material is:

| state | start | updates | presentations | per-fact lifetime exposure |
|---|---|---:|---:|---|
| `A200` | C0 | 200 | 800 A | A=200 |
| `B200_NEW_DOSE` | immutable A200 | 200 | 800 B | A=200, B=200 |
| `B400_FIXED_WORK` | immutable A200 | 400 | 1,600 B | A=200, B=400 |
| `REPLAY400` | immutable A200 | 400 | 800 A + 800 B | A=400, B=200 |
| `CLEAN_CUM600` | C0 | 600 | exact A200+REPLAY400 items | A=400, B=200 |

The three learner seeds alter optimizer/dropout initialization while using the
same eight facts. They are three optimization realizations, **not independent
worlds or fact banks**. At maximum the declared totals are 15 fits, 5,400
updates, 21,600 presentations, and 288 readout calls. The exact-item identity
of REPLAY400 versus CLEAN_CUM600 is correctly constructed; their difference is
the phase boundary/checkpoint/optimizer-RNG reset package, not replay alone.

## Leakage and claim boundary

No A200 item contains B, and the B=0/4 gate detects gross spill. Training uses
W0-W7 and reads W8, but W8 is an already exposed wrapper over the same singleton
addresses and target bytes. Thus this can establish exact format-assisted
availability/coexistence on one exposed DEV bank only. It cannot establish
unseen-fact generalization, autonomous DREAM selection, composition, LINK,
parenting, lifetime improvement, or C11 qualification. The source labels this
boundary correctly.

## Test evidence at the audited commit

The fit (20 tests), acquisition reducer (13), campaign/material/readout group
(27), and a repaired outer group (21) have green CPU logs. However, the exact
commit still contains three stale outer-test expectations; the helper worktree
changes those assertions and then obtains the 21-test pass. Because those test
repairs are uncommitted, commit `71adf462` is not itself a terminal green
snapshot. More importantly, none of the green tests exercises a real warm
writer receipt: the warm manifest is synthetic, which is why blocker 1 passed
the suite.

## Minimal closure

1. Align `dtype_conversions` writer/validator semantics and add a real receipt-
   shape regression over a warm A200 child.
2. Commit the outer-test repairs and rerun the source-pinned CPU suites to a
   terminal summary.
3. For acquisition-only launch, prepare and inspect the sealed native manifest;
   preserve `ACQUISITION_CAPTURED_NOT_QUALIFIED` until the raw reducer runs.
4. Before descendants, implement acquisition-receipt materialization, all-four
   branch orchestration, all-state cold readouts, and the final paired reducer.

No change to the scientific design or dose is required by these findings.

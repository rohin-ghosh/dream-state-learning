# Mechanism status audit — 2026-09-11

This note is a read-only audit of existing artifacts plus one scheduling
decision. It introduces no new mechanism or benchmark claim.

## Bottom line

The sleep writer is producing a repeatable behavioral delta, but the completed
R3 curves are not paper-grade evidence because their commit gate selected on
the same eight-program panel later reported. The first run that fixes this,
R5, now gates on a separate 12-program panel and reports only on the original
eight-program panel.

The completion-frame memory-dose implementation was committed and launched by
another active research process while this audit was in flight. Its revised
equal-exposure cells now hold 16 renderings per occurrence fixed while varying
the number of templates. The launch is exploratory only: the benchmark and
acceptance changes do not have a matching ratified architecture change, and an
independent post-launch review found remaining interpretation and resume-safety
problems described below.

## Existing lifetime evidence

R3 is rank 8, no parent, 1,024 episodes, sleep every 32, paired seeded ON/OFF
probes every 64, and a score/brevity/canary commit gate. Five completed clean
seeds have run-level mean ON-minus-OFF deltas:

| Seed | Mean paired delta | Positive checkpoints |
|---|---:|---:|
| 500 | +0.0434 | 15/16 |
| 501 | +0.0175 | 16/16 |
| 502 | +0.0551 | 16/16 |
| 503 | +0.0209 | 16/16 |
| 505 | +0.0321 | 16/16 |

Across independent seed means: +0.0338 (sample-SD 0.0157; descriptive 95%
t-interval +0.0144 to +0.0532). This is strong exploratory evidence that the
mounted adapter changes performance in the intended direction. It is not an
unbiased estimate of prospective improvement because the gate used the report
panel.

R4 adds a parent to the same basic loop and is still completing. At this
snapshot, seven seeds have 9–16 paired checkpoints each; 84/93 checkpoint
deltas are positive and the mean of the seven per-life means is +0.0202.
This is neither a clean parenting effect nor a final result: the runs use new
seeds, two parent model sizes, adaptive parent text introduced during the
lives, and the same report-panel gate as R3. R4 shows continued writer activity
under parenting, not that parenting helps.

Older RP parented lives are scout-only. Although each has 128 completed wake
files, their ledgers contain 1,040–1,048 reconstructed episode instances rather
than 1,024. Repeated process resumes appended 16–24 extra partial/replayed
instances. Do not use RP seeds 400–402 for a paper claim or as clean lineage
parents.

## Clean next lifetime

R5 changes one validity-critical condition: candidate adapters are selected on
a disjoint 12-program gate panel while the eight-program report panel is never
used for selection. It has no parent. R5 seed 700 stopped after executing the
120–128 batch but before writing its wake marker; resuming would replay those
eight experiences. Its artifacts were preserved and the resumed process was
stopped. Seed 700 is pilot-only.

Fresh R5 seed 701 was launched from an empty directory on A40 GPU 6 with the
same runtime hashes and these defining flags:

```text
arm B; seed 701; 1,024 episodes; sleep 32; report probe 64; 16 ticks;
wake batch 8; rank 8; probe gate; disjoint_panel/panel_v1.json; no parent
```

This is the highest-value running mechanism test because its reported curve is
not post-selected by its own writer gate.

## Memory-dose audit

The completed synthetic car sweep did not demonstrate clean owner-bound
parametric memory. Its automatic finalist was explicitly a fallback:
`B/across/occurrences/short`, labeled `rewrite-habit`, with
`I_d = 0.3640` and `d_p = 0.0530`. The correct reading is that the write changed
text behavior without passing the planned clean storage gates.

The completion-frame rescore is a sensible diagnostic: an existing adapter
might contain a fact that a declarative completion cue can extract even when
question answering cannot. No retraining is needed for this rescore. The first
bank's existing-adapter results are:

| Existing adapter | Frame dP at dose 16 | Owner-vs-similar log-odds | 95% bootstrap interval | Frame spill |
|---|---:|---:|---:|---:|
| A, across sleeps | +0.008 | +0.048 | [−0.199, +0.308] | 0.070 |
| A, within session | +0.024 | +0.138 | [−0.086, +0.386] | 0.065 |
| B, across sleeps | +0.152 | +0.672 | [+0.164, +1.189] | 0.114 |

Cell B therefore has an owner-specific completion signal on this first bank,
but it also moves the controls by 0.114, almost four times the planned 0.03
spill ceiling. This is evidence of a binding mixed with a broad completion
habit, not clean memory and not “nothing.” Banks 1–2 are required before any
pooled reading.

The revised fixed-exposure trio is `F_r16k1`, `F_r16k4`, and `F_r16k16`: all
emit 16 renderings per ledger occurrence while varying template diversity. An
`F_r64k16` cell applied to the existing owner dose ladder yields total owner
exposures 64, 256, and 1,024. This fixes the earlier arithmetic objection.
The 26/26 memory-dose CPU mock suite passes on the committed bytes. The full
CPU runner reports 149/157: five golden-file failures are a last-bit float
serialization difference (`...1507` versus `...1505`), and the other three
tests are local HTTP-server fixtures blocked by this session's socket sandbox.
No functional failure in Cell F appeared in that run.

Remaining problems:

- Frame candidate mass is reported but is not part of `G9_frame_binding`;
  the separate `G9_mass` uses non-frame paraphrase cues. Automated frame
  labels must not be trusted without inspecting raw frame mass.
- A failed binding gate with a moderate or large frame delta can be labeled
  `frame-nothing`; confidence failure, non-specific habit, and no effect are
  not separated correctly.
- Existing-corpus and throughput-probe resume paths are not fully bound to
  corpus/adaptor identity, so a later code or corpus repair could silently
  reuse a stale artifact.
- Several thresholds and controls are newly proposed benchmark decisions, not
  ratified protocol bytes.

Treat Cell F as a disposable exploratory diagnostic. Do not promote its
automatic pass/fail labels or use it for a paper claim until those issues are
resolved and independently reviewed. The lifetime and parenting experiments
are unaffected.

Operationally, the original queue placed bank 0 of the 16-rendering template
comparison on a different node from banks 1–2. Because a node-dependent
generation delta has already been observed elsewhere, a same-A40 bank-0 queue
was added behind the active bank-1/2 queue. This permits a three-bank
within-node analysis; the cross-node bank-0 result remains a sensitivity
replicate rather than part of that pool.

## Live addendum — 2026-09-11 08:53 UTC

### Cell F first directional read: repetition amplifies the frame, not binding

The first completed high-repetition cell is bank 0, `F_r16k1`, with one
surface form repeated 16 times per occurrence. It is a screening result, not
a finding. Relative to adapter-off, the frame-completion probability changes
by +0.050 at dose 0, +0.299 at dose 1, +0.416 at dose 4, and +0.660 at dose
16; frame candidate mass rises from about 0.009 off to approximately 1.000
on. The dose-rise check passes (+0.360), but the binding check fails: the
frame interaction interval is [-0.106, 1.939], and mean spill into non-owner
frames is 0.439 against the frozen 0.03 ceiling.

The narrow interpretation is useful: repetition is a powerful write
amplifier, but repetition in one phrasing mainly teaches the broad habit
"complete this colour sentence" rather than a clean owner-specific memory.
The equal-exposure `F_r16k4` and `F_r16k16` cells are running now. They test
whether surface diversity preserves the owner effect while reducing spill.
No Cell F claim is warranted until three same-node banks and an untouched
confirmation agree.

### R5 seed 701 reached its first sleep without a resume

The live R5-loose pilot completed four contiguous eight-episode wake batches,
compiled 124 new items plus three principles at sleep 32, trained rank 8 at
learning rate 1e-4 with return code 0, and passed the action-interface canary
at 1.00 parseable ACT rate. The disjoint score gate was still evaluating at
this cut, so the adapter remained a candidate and no commit/reject verdict
was available. The life process remained alive. This is operational evidence
only: its default score tolerance is 0.02 and its format canary still uses
the older report-panel programs, so it remains an exploratory R5-loose pilot
rather than a paper-grade retention result.

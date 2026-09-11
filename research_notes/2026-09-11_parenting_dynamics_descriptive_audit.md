# Parenting dynamics: first delayed descriptive audit (2026-09-11)

## Scope

This is a read-only audit of already-generated R4 parented and R3 control
receipts. It is not a randomized parenting experiment and cannot establish a
causal parenting effect. It asks a narrower question: after a valid parent
brief was demonstrably shown, did the child's *executed* behavior change
immediately, after one advice-conditioned sleep, or after four sleeps?

Only authoritative `act` ledger rows count as actions. Generated `ACT:`-like
prose never counts. Parent-absent ON/OFF probes are excluded if any parent text
appears in their stored prompts.

Reproducibility:

- Receipt archive: `node1_v6_out_receipts_2026-09-11.tar.gz.part.aa`, SHA-256
  `815c61f499941c0a51110f9ee279a7033af2eb4fba855427720bcb14b9dc9b3f`.
- Analyzer: `organism_v6/parenting_dynamics.py`, SHA-256
  `510f6658888e6f482b68d339116acd4a8cc9ed9f52b2ff18cbd31fcdbc439a29`.
- Full local JSON report: `report-v5.json`, SHA-256
  `91556e2737e392f7a4a4a4d3336b8666e6e1346a810fc4310b8eff7d0f46b33c`.
- Focused CPU suite: 28 tests passed.

## Inclusion

The archive contained three R4 parented lives and three R3 controls. Only
`R4_B_seed604` was internally complete enough for delayed interpretation.
`R4_B_seed605` and `R4_B_seed606` were excluded because their reconstructed
episode counts exceeded their wake-receipt exposure counts (504 vs 496 and 696
vs 688), consistent with a live resume/replay boundary. All three R3 controls
qualified.

The preregistered descriptive sufficiency floor was four complete R4 and four
complete R3 lives. This audit has one and three, so `s4_sufficient=false` and
no aggregate efficacy claim is allowed.

## One qualifying parented life

The first valid v3 parent brief in `R4_B_seed604` was delivered at episode 160.
Its exact text was present in 32/32 prompts in every measured window. No later
distinct parent brief entered any of those windows.

| Measure | Pre-brief 32 | Direct 32 | After one sleep 32 | After four sleeps 32 |
|---|---:|---:|---:|---:|
| First-note lexical rehearsal | 90.6% | 100.0% | 96.9% | 96.9% |
| Thought says it may change route | 34.4% | 53.1% | 43.8% | 15.6% |
| Intended change becomes a different predicted, executed action | 12.5% | 15.6% | 25.0% | 0.0% |
| Realization given stated intent | 36.4% | 29.4% | 57.1% | 0.0% |
| Mean best program-size reduction | 55.90% | 55.89% | 56.11% | 54.96% |
| Mean executed attempts | 35.1 | 21.2 | 18.1 | 21.7 |

The clean descriptive pattern is **persistent echo, transient action change**.
The child restated the lesson nearly every episode. Actual route-changing
behavior rose most after the first advice-conditioned write, then vanished by
four writes despite the exact reminder remaining in context. Task score did
not show a corresponding durable gain.

The parent-free adapter probe at episode 192—the first probe after training on
the direct post-brief child stream—was 0.060 below its adapter-off pair on the
report score. Later probe deltas returned to approximately zero (+0.0025 to
+0.0031). This is not evidence that parenting caused harm: the panel has only
eight programs and the historical writer selected adapters using a related
report panel. It is evidence that lexical uptake must not be used as a proxy
for a beneficial write.

The three R3 controls also moved without parenting. Their executed-change
deltas versus their pre-event windows were:

| Control | Direct | After one sleep | After four sleeps |
|---|---:|---:|---:|
| R3 seed500 | 0.0% | -6.25% | -6.25% |
| R3 seed501 | +3.125% | 0.0% | 0.0% |
| R3 seed502 | +3.125% | +3.125% | 0.0% |

With one qualifying parented life, these controls rule out a strong reading of
the anecdote. They do not estimate the parent effect.

## Bounded conclusion and next use

The current evidence supports exactly this statement:

> In one qualifying life, repeated parent advice became a persistent verbal
> ritual and coincided with a short-lived change in executed behavior, but the
> action change and task benefit were not durable. The existing histories are
> insufficient to measure parenting efficacy.

The next ordinary parenting canary should therefore use matched randomized
parent-versus-sham assignment, context reset before the exam, and later
executed action plus world outcome as its primary measures. The same immediate,
one-sleep, and four-sleep windows should be retained. Lexical restatement stays
as an echo diagnostic only; a parent-free ON/OFF read remains the mediation
check.

The full C11 guard specification is intentionally untouched and deferred to
the final paper-grade run.

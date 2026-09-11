# Final adapter × text brief: matched historical 2×2 audit

Date: 2026-09-11

Status: **post-hoc carrier diagnostic only.** This audit identifies which
already-generated cells are mechanically comparable. It does not establish
that textual memory generally beats parametric memory or qualify either
carrier for the paper.

## The matched comparison

Twelve historical lives have all four cells on disjoint panel v1:

- `F`: frozen base, no brief;
- `A`: the exact final committed adapter, no brief;
- `T`: frozen base plus the exact final waking brief;
- `AT`: the same adapter plus the same brief.

All four cells use the 12-program panel with SHA-256
`24ecfe874fafb216d7b8073322b61dda53497da5080751131112b0845884003a`,
16 thought ticks, and common generation seeds 4242 and 5242. The shared
node-specific `F` files contain three repetitions, but only their first two
are paired with the other cells. There are 48 logical cells backed by 38
unique JSON files because the frozen cell is shared within node.

The mechanically complete lives are:

- node 1: `R2_B_seed0`, `R2_B_seed1`, `R2_B_seed5`, `R2_B_seed6`;
- node 2: `R2_B_seed2`, `R2_B_seed3`, `R2_B_seed4`, `R2_B_seed7`,
  `R2_B_seed8`, `R3_B_seed503`, `RP_B_seed400`, `RP_B_seed401`.

The R3 and RP lives are scientifically different arms and are not pooled with
R2. The coherent R2 subset therefore contains nine historical lives.

| Life | F | A | T | AT | Factorial interaction |
|---|---:|---:|---:|---:|---:|
| R2-0 | .2524 | .2145 | .2731 | .1619 | -.0733 |
| R2-1 | .2524 | .2731 | .2667 | .2731 | -.0144 |
| R2-5 | .2524 | .2198 | .2525 | .2447 | +.0248 |
| R2-6 | .2524 | .2214 | .2524 | .2294 | +.0079 |
| R2-2 | .2532 | .2496 | .2731 | .2519 | -.0177 |
| R2-3 | .2532 | .2362 | .2322 | .2530 | +.0379 |
| R2-4 | .2532 | .2495 | .2498 | .2495 | +.0034 |
| R2-7 | .2532 | .2283 | .2481 | .2687 | +.0456 |
| R2-8 | .2532 | .2514 | .2649 | .2495 | -.0136 |

Across these nine lives:

| Quantity | Mean |
|---|---:|
| Frozen `F` | .2528 |
| Adapter `A` | .2382 |
| Text `T` | .2570 |
| Adapter + text `AT` | .2424 |
| Adapter main contrast `A-F` | -.0146 |
| Text main contrast `T-F` | +.0041 |
| Combined contrast `AT-F` | -.0104 |
| Factorial interaction `(AT-A)-(T-F)` | +.00008 |

Only one of nine adapter-only cells and two of nine combined cells exceeded
their node-matched frozen base. The near-zero mean interaction says the small
brief benefit and larger adapter harm were approximately additive *on this
post-hoc average*. It does not erase the strong life-level heterogeneity.

## What is not matched

The analogous report-panel tally is incomplete. Its `T` and `AT` cells use
seeds 4242/5242, whereas the historical life `F` and `A` probes use seed 777.
Therefore the earlier “brief >= adapter in 12/20 lives” count is a descriptive
cross-run tally, not a matched factorial comparison.

Other incomplete sets are:

- R3 seeds 500--502 and R4 seeds 601--603: `T` but no `AT`;
- R3 seed505: report `T/AT`, but no disjoint `AT`;
- RP seed402: `T` but no `AT`;
- routine-only files: one shared deterministic diagnostic rather than
  independent life-level text-memory replicates.

The launcher comment in `gpu/brief_baseline_2x2.sh` overstates completeness on
the report panel for the same seed reason. The disjoint 2×2 becomes complete
only by joining its outputs with `gpu/disjoint_reprobe.sh`.

## Claim boundary

The defensible summary is:

> In a post-hoc, same-node, common-random disjoint-panel comparison across
> nine historical R2 lives, final text briefs produced a small average score
> increase while final adapters produced a larger average decrease. Their
> average factorial interaction was nearly zero, with heterogeneous signs by
> life.

This is not evidence that textual memory generally outperforms parametric
memory. The waking brief is static and handoff-sized, not a certified
candidate-blind evolving retrieval baseline; the disjoint panel is already
researcher-used; several source histories have resume defects; and this
comparison was not prospectively registered.

The next read-only analysis should use the existing matched ledgers to count
authoritative ACTs, first/modal routine, chunks-to-best, invalid or empty
actions, `DONE`-first behavior, and per-program interaction contributions.
That can diagnose whether `AT` changes execution through action volume or
interface effects. It requires no new model calls. No more routine-only cells
are informative.

Point-in-time code receipts, identical locally and on both nodes:

- `gpu/brief_baseline.sh`:
  `1ae70ed975a3b74ce4110580df72469807fd87177106140c43b11fcc96609854`;
- `gpu/brief_baseline_2x2.sh`:
  `1b846707a81cc47a781bb48009da30f423b5bf28c78a517b356c1f93b41a4ea9`;
- `gpu/disjoint_reprobe.sh`:
  `ea0b8aefb58057a7c4a228453f5e2e3224742851a33a5650135ee3e917cb8543`;
- `organism_v6/probe_adapter.py`:
  `ddb7f90ec5a05a9d21ae6ec1797d5a6485cdcac090a49232c8ac1a3335041b4f`.

The full per-life JSON, adapter, and brief hashes are preserved in the fresh
audit transcript; any later paper use must promote them into a durable
machine-readable receipt rather than relying on mutable paths.

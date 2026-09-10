# Fable v6.1 long-run partial follow-up v2

Date: 2026-09-06

Status: read-only descriptive follow-up to
`20260906_fable_v61_longrun_independent_audit_v1.md`. No process, code,
adapter, corpus, probe, or run artifact was modified. B0 and B1 were still
running. This is not a prospective learning result and grants no architecture,
benchmark, parenting, writer, model, or GPU authority.

## Live state inspected

- A0, A1, and A2: `LIFE_DONE`, 1,024 episodes.
- B2: `LIFE_DONE`, 1,024 episodes.
- B0: latest completed wake `wake_0744_0752.json`; latest paired probe 704.
- B1: latest completed wake `wake_0720_0728.json`; latest paired probe 704.
- Three GPU processes were present; B0 and B1 were confirmed by live
  `run_life_v2` process handles rather than inferred from files.

The exact paired JSON checkpoint sets have these fixed-list aggregate hashes.
Each aggregate is SHA-256 over the ordered `sha256sum` output for adapter-on and
adapter-off files at episodes 64, 128, ..., 704; the final B2 suffix covers
768, 832, 896, 960, and 1,024.

| evidence set | aggregate SHA-256 |
|---|---|
| B0 through 704 | `5466b3a51dd9c559298e7221b01d0822ece4fac666993fb096c4a278d9b683b8` |
| B1 through 704 | `9e793a16109a9168bae49647d21d16879c8bdd5bde6053eb20f991571e021995` |
| B2 through 704 | `5534f5faf9b7ea1c98000a9a2e03cbb500f56fe76d84a8521f29da898c539395` |
| B2 episodes 768--1,024 | `6bcc181c59f88bb70adab26cf830160911f21adf0981f425a8db720af55f08db` |

## Paired adapter-on minus adapter-off curves

| episode | B0 | B1 | B2 |
|---:|---:|---:|---:|
| 64  | `+0.054466` | `+0.014646` | `+0.024149` |
| 128 | `+0.042606` | `+0.023965` | `+0.000130` |
| 192 | `+0.043378` | `+0.002984` | `-0.013538` |
| 256 | `+0.046130` | `+0.020337` | `-0.006506` |
| 320 | `+0.023747` | `+0.040069` | `-0.430951` |
| 384 | `+0.054616` | `+0.058894` | `-0.279899` |
| 448 | `-0.012189` | `+0.061554` | `-0.271681` |
| 512 | `+0.032353` | `+0.043142` | `-0.201080` |
| 576 | `+0.033547` | `+0.061554` | `-0.476035` |
| 640 | `+0.037238` | `+0.058894` | `-0.402252` |
| 704 | `+0.001848` | `+0.058894` | `-0.407074` |
| 768 | pending | pending | `-0.488541` |
| 832 | pending | pending | `-0.401392` |
| 896 | pending | pending | `-0.358367` |
| 960 | pending | pending | `-0.418648` |
| 1,024 | pending | pending | `-0.434834` |

At episode 704 the raw means were:

- B0: adapter on `0.487793`, off `0.485945`;
- B1: adapter on `0.529087`, off `0.470193`;
- B2: adapter on `0.065282`, off `0.472356`.

## Interpretation

The writer effect is not a stable monotonic continual-learning curve:

1. B0's positive early difference decays to approximate parity at episode
   704.
2. B1's adapter-on mean is exactly `0.529087` at every checkpoint from 384
   through 704. This plateau is consistent with stable reinforcement/fixation
   of one supplied broadly useful action prior; it is not evidence of ongoing
   improvement.
3. B2 remains catastrophically below adapter-off after the previously
   localized motor-channel/dialect failure.

The between-life realization is therefore qualitatively unstable: one fading
effect, one stable plateau, and one channel collapse. Averaging these paths
would hide the mechanism, while selecting B1 would be survivorship bias. The
current run is useful evidence that writer realization and action-channel
preservation are binding constraints. It cannot establish that periodic LoRA
consolidation improves an agent across lifetime.

The paper-grade successor must use exact native response targets, common-random
paired generation, prospective loaded-source and prompt receipts, independent
life-level replication, and separate free-routing and typed-forced proposal
endpoints. It must compare periodic writes with active textual memory and a
matched final-batch experience-distillation control.

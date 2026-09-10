# Fable v6.1 terminal three-root report v2

Date: 2026-09-07

Status: repaired exploratory, post-hoc, read-only analysis of completed legacy
CompilerGym artifacts. No model, tokenizer, compiler, adapter, benchmark,
process, or GPU operation was launched, stopped, or changed by this analysis.
This report supports no confirmatory parenting, continual-learning, discovery,
or superiority claim.

This v2 supersedes v1 only as the current terminal analysis. The attacked v1
and its independent `REVISE` advisory remain immutable provenance.

## Bottom line

All three sleep-v2 roots have a `LIFE_DONE` marker and a complete episode-1024
build. For each root, all sixteen post-first-write checkpoints from episode 64
through 1,024 contain one adapter-on and one adapter-off ledger and summary.
The repaired analyzer verifies exactly the eight registered probe programs in
every ledger and summary and requires ledger-reconstructed per-program scores
to equal the saved summary values.

The three observed paths are heterogeneous:

- roots 0 and 1 usually have higher adapter-on than adapter-off saved panels,
  while their terminal adapter-on actions are highly concentrated on one
  supplied six-pass routine; and
- root 2 has a severe registered action-routing failure after its corpus
  develops many decorated `ACT:`-like lines.

These associations show that the legacy writer is behaviorally consequential
and unstable across these three runs. They do not identify a population
effect, continual improvement, causal transport, novel discovery, or the
one-parent mechanism.

## Exact terminal saved panels

| root | adapter on | adapter off | on - off | on actions | on dominant share | off actions | first-action-cap difference |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | `0.523262003` | `0.486183774` | `+0.037078229` | 163 | 161/163 (`98.8%`) | 62 | `+0.063425031` |
| 1 | `0.529087121` | `0.470193135` | `+0.058893986` | 156 | 145/156 (`92.9%`) | 71 | `+0.067998584` |
| 2 | `0.051111111` | `0.485944727` | `-0.434833616` | 1 | 1/1 | 75 | `-0.408725862` |

The three terminal differences have mean `-0.112953800`, median
`+0.037078229`, two positive roots, and one negative root. Those are
descriptions of three paths, not an inferential estimate.

The dominant terminal adapter-on routines in roots 0 and 1 were:

```text
-mem2reg,-sroa,-gvn,-simplifycfg,-licm,-instcombine
-mem2reg,-sroa,-gvn,-simplifycfg,-instcombine,-constprop
```

Both extend the four-pass opening explicitly supplied in the birth prompt.
The observations are compatible with selection, reinforcement, or reuse of a
taught action prior; they cannot establish novel strategy discovery.

## Post-first-write probe-window AUC

The normalized trapezoid covers episodes 64--1,024. It excludes episode zero
and the first 64 waking episodes because episode zero used the earlier harness.
It is therefore not whole-lifetime AUC.

| root | on AUC | off AUC | on - off | positive / negative checkpoints |
|---:|---:|---:|---:|---:|
| 0 | `0.510644770` | `0.477639476` | `+0.033005294` | 15 / 1 |
| 1 | `0.519026638` | `0.472472752` | `+0.046553886` | 16 / 0 |
| 2 | `0.183621212` | `0.474366299` | `-0.290745087` | 2 / 14 |

Checkpoints within a root are dependent repeated observations. They are never
treated as independent experimental units.

## Fixed-action-cap diagnostic by root

The table gives the mean adapter-on minus adapter-off score across each root's
sixteen dependent checkpoints after retaining only the first `K` executed
actions per program.

| root | K=1 mean (positive checkpoints) | K=2 | K=4 | K=8 | K=16 mean (positive checkpoints) |
|---:|---:|---:|---:|---:|---:|
| 0 | `+0.038335` (14/16) | `+0.042952` | `+0.039952` | `+0.033684` | `+0.031663` (15/16) |
| 1 | `+0.051365` (15/16) | `+0.056536` | `+0.051396` | `+0.047166` | `+0.045908` (16/16) |
| 2 | `-0.271803` (4/16) | `-0.271803` | `-0.277965` | `-0.283146` | `-0.283488` (2/16) |

For roots 0 and 1, executed actions beyond the first action cannot explain the
positive mean panel differences. This does not control generated-token volume,
action parsing probability, unseeded sampling, checkpoint dependence, or
other arm differences. The diagnostic is post-hoc.

## Corpus dialect proxy, not parser compliance

The repaired corpus reader uses only `payload["corpus"]`, exactly the list
passed to the legacy trainer. It does not re-add `principles` or inspect
metadata. The metric below is narrowly the share of exact column-zero
`^ACT:` lines among lines matching a broader case-insensitive embedded-colon
`ACT\s*:` heuristic. It is not the registered parser's acceptance rate; the
legacy parser also accepts other spellings.

| root | column-zero `ACT:` / ACT-like colon lines | fraction | decorated lines | hash-prefixed lines |
|---:|---:|---:|---:|---:|
| 0 | 1261 / 1343 | `0.938943` | 82 | 34 |
| 1 | 1005 / 1149 | `0.874674` | 144 | 0 |
| 2 | 352 / 1449 | `0.242926` | 1097 | 354 |

All three first-sleep values are `1.0`. Root 2's low terminal share co-occurs
with its registered one-action panel. Together with the earlier post-hoc
permissive extraction assay, this is consistent with a self-reinforcing
serialization shift contributing to the registered routing failure. Unseeded
writer realization and incomplete runtime ancestry prevent a causal
attribution, and permissive extraction never replaces the registered score.

## Validation and immutable analysis artifacts

The repaired analyzer fails closed unless:

1. all sixteen expected checkpoint numbers exist for every root;
2. ON/OFF ledger and summary files both exist;
3. every JSONL row parses;
4. each ledger exposes exactly the eight registered program IDs;
5. each summary exposes exactly those same eight programs;
6. each stored summary mean equals its eight stored program values;
7. each ledger's zero-floored best score equals the stored program score; and
8. episode 1,024 exists as the terminal pair.

Analyzer SHA-256:
`174bf386acd42abe934a8bef0cb2363c5aceecf155129d72e6e390d38667e231`.

Exact machine-readable result:
`20260907_fable_v61_terminal_analysis_v2.json`, SHA-256
`93ec4301a722f7b8b237cb6516fd30ac506405da0d0a9dc14a39bb0f6ff90e46`.

Complete artifact manifest:
`20260907_fable_v61_terminal_artifact_manifest_v2.json`, SHA-256
`ec7949ae176595d7cc4229545920f41539be7ff2de09aee7cb4d181110f18a80`.
It contains 306 `(relative path, byte count, SHA-256)` entries totaling
`549,182,047` bytes:

- 96 probe ledgers;
- 96 matching probe summaries;
- 96 consumed sleep corpora;
- 3 `LIFE_DONE` markers; and
- 15 terminal compile/adapter completion, configuration, weight, and training
  metadata artifacts.

The canonical compact-JSON encoding of its ordered `entries` array has
SHA-256
`ee864d1eb9a77556ce0bdf496f01194c60825b5b1178ab4f22b983d38d45b10c`.
This matches the summary embedded in the machine-readable result.

Reproducer:

```text
python3 research_loop/advisory/analyze_fable_v61_probe_actions.py \
  --root /localhome/local-rohing/v6_out --compact-final --results-only

python3 research_loop/advisory/analyze_fable_v61_probe_actions.py \
  --root /localhome/local-rohing/v6_out --compact-final --manifest-only
```

## Remaining causal and provenance limits

1. Generation and training realizations were not fully seeded or
   common-random across paired probes.
2. Each nominal 1,024-episode life repeated only 67 unique programs 15--16
   times.
3. Arm B received waking briefs during life; adapter-off at a B-history probe
   does not create a never-learning twin.
4. The exact imported runtime bytes remain unproved because sources changed
   beneath long-lived processes and saved thought rows omit exact prompts.
   On-disk source hashes from the earlier audit are not runtime ancestry.
5. The writer trained all tokens of bare compiled prose rather than exact
   native response continuations and had no typed-interface commit canary.
6. The useful opening was present in the birth prompt.
7. AUC, fixed-action caps, and corpus-dialect analyses were defined post hoc.

The maximum safe use of this legacy run is design diagnosis. It supports the
prospective need for native-response writer validation, separate proposal and
routing endpoints, exact writer/runtime receipts, and a commit canary that
rejects an adapter associated with degraded typed action execution. It does
not support describing the current system as a successful self-learning or
parented agent.

## Provenance chain

- attacked terminal report v1:
  `20260907_fable_v61_terminal_three_root_report_v1.md`, SHA-256
  `4baf7b52d5a741fcb5c34db2adf5e74b99138ea786011f95f9a373922660d603`;
- independent v1 reaudit:
  `20260907_fable_v61_terminal_three_root_report_independent_reaudit_v1.md`,
  SHA-256
  `a9405255130a336fb812e09906d46d35919741e778623f749dbfebd3e32ec016`;
  and
- earlier source/runtime, collapse-recovery, and exploratory-control audit:
  `20260906_fable_v61_longrun_independent_audit_v1.md`.

This v2 needs its own fresh independent re-audit before being called closed.

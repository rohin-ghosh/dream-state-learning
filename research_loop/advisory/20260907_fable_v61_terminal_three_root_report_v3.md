# Fable v6.1 terminal three-root report v3

Date: 2026-09-07

Status: repaired exploratory, post-hoc, read-only analysis of completed legacy
CompilerGym artifacts. No model, tokenizer, compiler, adapter, benchmark,
process, or GPU operation was launched, stopped, or changed by this analysis.
This report supports no confirmatory parenting, continual-learning, discovery,
or superiority claim.

This v3 supersedes v2 as the current terminal analysis. The attacked v1 and v2
reports and their independent `REVISE` advisories remain immutable provenance.

## Evidence-status warning

Every numerical value below is **author-observed from remote artifacts**. The
local analyzer, saved output, receipts, and checked-in source proxy are mutually
consistent, but a fresh reviewer did not receive the 549 MB of remote artifact
bytes and therefore has not independently artifact-verified the values. The
remote receipt binds the paths, byte counts, and hashes that the author read; it
is not a substitute for external access to those bytes.

The saved ledgers make malformed JSONL, missing programs, unexpected programs,
and ledger/summary score disagreement detectable. They do **not** make a
valid-JSON truncation at a record boundary mechanically detectable: no terminal
record or saved per-program tick count exists. Accordingly, this report calls
the 96 ledger/summary pairs *available and internally validated*, not complete
execution traces.

## Bottom line

All three sleep-v2 roots have a `LIFE_DONE` marker, all 32 scheduled sleep
directories have `COMPILED` and adapter `DONE` markers, and terminal adapter
weights/configuration/training metadata are present. For each root, all sixteen
post-first-write checkpoints from episode 64 through 1,024 have an adapter-on
and adapter-off ledger and summary. The analyzer verifies exactly the eight
registered probe program IDs in every ledger and summary and requires
ledger-reconstructed per-program scores to equal the saved summary values.

The three observed paths are heterogeneous:

- roots 0 and 1 usually have higher adapter-on than adapter-off saved panels,
  while their terminal adapter-on actions are highly concentrated on one
  supplied six-pass routine; and
- root 2 has a severe registered action-routing failure after its corpus
  develops many action-label lines that the checked-in parser source proxy
  would reject.

These are direct associations between adapter state, saved registered behavior,
and corpus syntax in three legacy paths. They do not identify a population
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
positive mean saved-panel differences. This does not control generated-token
volume, action parsing probability, unseeded sampling, checkpoint dependence,
or other arm differences. The diagnostic is post-hoc.

## Corpus syntax against the on-disk source proxy

The corpus reader uses only `payload["corpus"]`, the list passed to the legacy
trainer. It does not re-add `principles` or inspect metadata. The checked-in and
post-run remote `batch_loop.py` files match byte-for-byte and contain this
case-sensitive, column-zero parser regex:

```text
^(PREDICT|ACT|NOTE|RECALL|DONE)\s*:?\s*(.*)$
```

The source-proxy metric below counts action-label candidates and asks how many
would be interpreted as `ACT` by that regex. It remains a **source proxy**, not
runtime parser compliance, because the long-lived processes did not save import
receipts.

| root | source-proxy `ACT` syntax / action-label candidates | fraction | categorized near misses |
|---:|---:|---:|---:|
| 0 | 1263 / 1297 | `0.973786` | 34 hash-prefixed |
| 1 | 1005 / 1005 | `1.000000` | 0 |
| 2 | 353 / 797 | `0.442911` | 357 hash-prefixed; 87 decorated/`Action` alias |

All three first-sleep source-proxy fractions are `1.0`. Root 2's low terminal
fraction co-occurs with its registered one-action panel. This is consistent
with a serialization shift contributing to the registered routing failure.
Unseeded writer realization, incomplete runtime ancestry, and the post-hoc
metric prevent causal attribution; permissive re-extraction never replaces the
registered score.

The older embedded-colon heuristic is retained in the machine output under the
explicit name `column_zero_act_colon_fraction` for backward comparison. It is
not parser compliance and is not the primary syntax statistic in this report.

## Validation and evidence receipts

The repaired analyzer fails closed unless:

1. all sixteen expected checkpoint numbers exist for every root;
2. ON/OFF ledger and summary files both exist;
3. every saved JSONL row parses;
4. each ledger exposes exactly the eight registered program IDs;
5. each summary exposes exactly those same eight programs;
6. each stored summary mean equals its eight stored program values;
7. each ledger's zero-floored best score equals the stored program score;
8. episode 1,024 exists as the terminal pair;
9. all 32 expected sleep corpora exist for every root; and
10. every scheduled sleep has `COMPILED` and adapter `DONE` markers.

These checks do not detect valid-record-boundary truncation, as stated above.

Analyzer SHA-256:
`231f975f00938a01a4313818c178df984e943716043018eb153bb1a0fac86607`.

Exact machine-readable result:
`20260907_fable_v61_terminal_analysis_v3.json`, SHA-256
`a041e7e6a526a6062fca669aeb4fb57f309d755035de7f655f5460ece7975efc`.

Remote analysis-input/lifecycle receipt:
`20260907_fable_v61_terminal_remote_analysis_receipt_v3.json`, SHA-256
`c5fe66a89aed57d228be5728f76f38e1d31de7fdb7db4523622bef40996c739c`.
It contains 492 `(relative path, byte count, SHA-256)` entries totaling
`549,182,605` bytes:

- 96 probe ledgers;
- 96 matching probe summaries;
- 96 consumed sleep corpora;
- 3 `LIFE_DONE` markers;
- 192 per-sleep `COMPILED`/adapter-`DONE` markers; and
- 9 terminal adapter configuration, weight, and training-metadata artifacts.

The canonical compact-JSON encoding of its ordered `entries` array has
SHA-256
`483fa14abdc6c6fa3298168c90b293e7d56b3c8da433764d64f4a9f8e4f0da74`.
This matches the summary embedded in the machine-readable result.

Post-run on-disk source-proxy receipt:
`20260907_fable_v61_on_disk_source_proxy_receipt_v3.json`, SHA-256
`032174761669e1c6e9f7124ff02617b82f358915b1e836af7b905abf1b8acc8c`.
Its eight remote hashes match the current local source files byte-for-byte;
this still does not prove imported runtime ancestry.

Local evidence manifest:
`20260907_fable_v61_local_evidence_manifest_v3.json`, SHA-256
`4025ea76e825e63188fd4bba58063615615ac5a731871a08c93685e749203a97`.
It binds the analyzer, tests, machine result, remote receipt, and source-proxy
receipt. The report and its independent audit remain outside this acyclic
manifest.

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
   Post-run on-disk source equality is not runtime ancestry.
5. A valid-JSON truncation at a record boundary cannot be ruled out from the
   saved ledger schema.
6. The writer trained all tokens of bare compiled prose rather than exact
   native response continuations and had no typed-interface commit canary.
7. The useful opening was present in the birth prompt.
8. AUC, fixed-action caps, and corpus-syntax analyses were defined post hoc.

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
- attacked terminal report v2:
  `20260907_fable_v61_terminal_three_root_report_v2.md`;
- independent v2 reaudit:
  `20260907_fable_v61_terminal_three_root_report_independent_reaudit_v2.md`,
  SHA-256
  `b71d2e740937972d05cc6ee73d96a185251290b72ac98d03b8194f3f70ca2ab9`;
  and
- earlier source/runtime, collapse-recovery, and exploratory-control audit:
  `20260906_fable_v61_longrun_independent_audit_v1.md`.

This v3 needs a fresh independent re-audit before being called closed.

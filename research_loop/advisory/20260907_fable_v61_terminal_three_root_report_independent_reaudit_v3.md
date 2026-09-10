# Fable v6.1 terminal three-root report independent reaudit v3

Date: 2026-09-07 UTC

Advisory path:
`research_loop/advisory/20260907_fable_v61_terminal_three_root_report_independent_reaudit_v3.md`.

Scope: fresh, read-only adversarial audit of the v3 terminal report, analyzer,
analyzer tests, compact analysis JSON, remote analysis-input/lifecycle receipt,
on-disk source-proxy receipt, local evidence manifest, and the v2 independent
reaudit. I ran only local CPU/read-only checks. I did not access a remote host
or GPU, invoke a model, compiler, adapter, or benchmark, or edit any audited
artifact. This advisory is the only file created by the audit.

## Verdict

**PASS — for local package integrity and closure of the six v2 audit issues.**

This is not a pass for independent verification of the underlying run. All
ledger-, summary-, corpus-, lifecycle-, and terminal-adapter-derived facts
remain **author-observed from remote artifacts, not independently
artifact-verified**. The 549,182,605 remote bytes were unavailable in this
environment. I could verify the receipt's internal structure and its binding
into the local package, but not the truth of any individual remote byte count
or digest, rerun the analyzer on the remote inputs, or reconstruct the reported
measurements from the underlying ledgers and corpora.

Within that explicit evidence boundary, I found no remaining defect requiring
revision. V3 honestly narrows the scientific use to post-hoc design diagnosis;
it is not evidence for confirmatory parenting, continual learning, discovery,
population effects, causal transport, or superiority.

## Bytes audited

| artifact | locally recomputed SHA-256 |
|---|---|
| `20260907_fable_v61_terminal_three_root_report_v3.md` | `3595b428295a5678ae8ab8a4edeb21e19f7f100010badc379b7b5c16d1f1c44e` |
| `analyze_fable_v61_probe_actions.py` | `231f975f00938a01a4313818c178df984e943716043018eb153bb1a0fac86607` |
| `test_analyze_fable_v61_probe_actions.py` | `34d02a5e9bb9ed89d4d05fc453caeab8a3ed05c77b7d669d987bf84cb2407057` |
| `20260907_fable_v61_terminal_analysis_v3.json` | `a041e7e6a526a6062fca669aeb4fb57f309d755035de7f655f5460ece7975efc` |
| `20260907_fable_v61_terminal_remote_analysis_receipt_v3.json` | `c5fe66a89aed57d228be5728f76f38e1d31de7fdb7db4523622bef40996c739c` |
| `20260907_fable_v61_on_disk_source_proxy_receipt_v3.json` | `032174761669e1c6e9f7124ff02617b82f358915b1e836af7b905abf1b8acc8c` |
| `20260907_fable_v61_local_evidence_manifest_v3.json` | `4025ea76e825e63188fd4bba58063615615ac5a731871a08c93685e749203a97` |
| v2 independent reaudit | `b71d2e740937972d05cc6ee73d96a185251290b72ac98d03b8194f3f70ca2ab9` |

The report has the expected SHA-256. Every hash it prints for the analyzer,
machine result, remote receipt, source-proxy receipt, v1 report, v1 reaudit,
and v2 reaudit matches the current local bytes.

## Independently verified local facts

### Receipt structure and category coverage

The remote receipt is valid JSON. Its `entries` array has 492 unique paths in
lexical order. Every entry has exactly `path`, nonnegative integer `bytes`, and
a lower-case 64-hex `sha256`. The declared count and byte sum independently
recompute to 492 and 549,182,605. Compact key-sorted JSON encoding of the
ordered array recomputes to
`483fa14abdc6c6fa3298168c90b293e7d56b3c8da433764d64f4a9f8e4f0da74`,
matching both the receipt and analysis JSON.

I generated the expected path set independently from three roots, probe
checkpoints 64 through 1,024 by 64, and sleep checkpoints 32 through 1,024 by
32. It equals the receipt path set exactly, with no missing or extra path. The
category counts are:

- 96 probe ledgers;
- 96 probe summaries;
- 96 sleep corpora;
- 3 `LIFE_DONE` markers;
- 96 per-sleep `COMPILED` markers;
- 96 per-sleep adapter `DONE` markers; and
- 3 each of terminal adapter config, weights, and training metadata.

Thus the report's grouped `192` per-sleep-marker count and `9` terminal-adapter
count are exact. The compact analysis's `artifact_manifest_summary` equals the
remote receipt object after removing only `entries`.

The local evidence manifest is also valid JSON. Its five entries exactly bind
the analyzer, tests, analysis JSON, remote receipt, and source-proxy receipt.
Every locally recomputed size and digest matches; its declared count and byte
sum recompute to 5 and 131,576. The eight files in the source-proxy receipt all
exist locally and their current byte counts and SHA-256 values match that
receipt. This verifies current local source equality only; the receipt's claim
that the same hashes were observed remotely is author-reported, and neither
fact establishes imported runtime ancestry.

### Analyzer and tests

Static inspection confirms that the compact-final path requires the exact 16
probe checkpoints for every requested root, all four ON/OFF ledger/summary
files per admitted pair, the exact registered eight-program sets, saved summary
means, zero-floored ledger/summary score agreement, terminal checkpoint 1,024,
the exact 32 sleep-corpus checkpoints, all scheduled completion markers, and
terminal adapter artifacts. Manifest construction covers every consumed probe
and corpus input plus those lifecycle artifacts.

The analyzer uses only the `corpus` field. Its new source-proxy statistic uses
the same case-sensitive, column-zero marker expression found in the currently
receipted local `organism_v6/batch_loop.py`; applying the expression separately
to split lines is equivalent to that file's multiline use for this statistic.
The code labels the result as a source proxy and keeps the old embedded-colon
heuristic separately named.

All eight local unit tests pass. They cover the live zero floor, exact ledger
program coverage, malformed JSONL, exact summary programs and saved mean,
ledger/summary disagreement, corpus-field isolation, source-proxy case/column
sensitivity with categorized near misses, and four-file checkpoint discovery.
Source inspection also finds the repaired
`post_first_write_probe_window_auc_by_seed` key in compact-final,
`--summary-only`, and default output, with no retained `lifetime_auc` key.

### Machine-result arithmetic and report transcription

The analysis JSON is valid and its top-level schema and keys agree with the
analyzer's compact-results output. The following independently recomputed
relations all pass:

- every terminal `on_minus_off` equals `on - off`;
- the three terminal differences recompute to mean `-0.11295380021101331`,
  median `0.03707822888896134`, two positive roots, and one negative root;
- every displayed dominant-action share equals dominant count divided by
  action count;
- every AUC difference equals its saved ON AUC minus saved OFF AUC, and each
  AUC checkpoint tuple is exactly 64 through 1,024 by 64;
- all root/cap sign counts sum to 16, and all AUC sign counts sum to 16;
- every source-proxy numerator plus near-miss count equals its candidate
  denominator, every near-miss category sum equals its near-miss total, and
  every fraction recomputes from its numerator and denominator; and
- every terminal, AUC, fixed-cap, action-count, dominant-share, syntax, and
  category value printed in the report agrees with the JSON at the displayed
  precision.

These checks verify arithmetic and transcription from the locally saved
machine result. They do not independently establish the machine result's
remote-derived inputs.

## Disposition of the six v2 issues

1. **Receipt scope: closed.** The remote receipt now has all 192 nonterminal
   and terminal per-sleep markers in addition to the probe, corpus, root, and
   terminal-adapter categories. The local manifest separately and acyclically
   binds the analyzer, tests, machine output, remote receipt, and explicit
   source-proxy receipt. The report accurately calls these a remote
   analysis-input/lifecycle receipt and a local evidence manifest rather than
   a remotely verified full-run archive.
2. **Remote evidence status: closed.** The report opens with a prominent
   warning that every number is author-observed from remote artifacts and was
   not independently artifact-verified. It explains what receipt consistency
   does and does not prove. This audit retains that label.
3. **Parser/source-proxy statistic: closed.** V3 reports a separately named
   source-proxy acceptance numerator, candidate denominator, fraction, and
   categorized near misses for each root, binds the inspected on-disk parser
   proxy, and explicitly disclaims runtime parser compliance.
4. **Truncation claim: closed by narrowing.** The report now claims detection
   only of malformed JSONL, program-set defects, and ledger/summary score
   disagreement. It prominently states that valid-record-boundary truncation
   is not mechanically detectable without a completion invariant and calls the
   pairs available and internally validated rather than complete traces.
5. **AUC naming: closed.** All three analyzer output modes and the analysis
   JSON use the post-first-write probe-window name; the report identifies the
   64--1,024 domain and disclaims whole-lifetime AUC.
6. **Causal language: closed.** The attacked causal-sounding sentence is gone.
   V3 describes direct saved-path associations, uses “co-occurs” and
   “consistent with” for the syntax/routing observation, expressly prevents
   causal attribution, and retains the unseeded, dependence, repeated-program,
   no-never-learning-twin, runtime-ancestry, truncation, writer-objective,
   taught-opening, and post-hoc limitations.

## Residual evidence boundary, not a repair defect

`/localhome/local-rohing/v6_out` is absent here, and no copied terminal ledger
or corpus was found in the local repository. Therefore the remote receipt
cannot serve as independent proof of the 492 remote objects: its individual
hashes, sizes, existence claims, and all measurements computed from them await
access to the receipted bytes. The report already states this accurately, so it
is a preserved evidence-status limitation rather than an unclosed v2 issue.

No new run, model call, compiler call, benchmark, GPU work, or audited-artifact
edit is required for this PASS.

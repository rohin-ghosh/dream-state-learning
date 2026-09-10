# Fable v6.1 terminal three-root report independent reaudit v2

Date: 2026-09-07 UTC

Advisory path:
`research_loop/advisory/20260907_fable_v61_terminal_three_root_report_independent_reaudit_v2.md`.

Scope: fresh, read-only final audit of the repaired terminal report, compact
analysis JSON, artifact-manifest JSON, analyzer, the v1 independent reaudit,
and the earlier v6.1 audit where needed. I ran only local CPU/read-only checks.
I did not access the remote host or a GPU, invoke a model, compiler, adapter,
or benchmark, or modify any audited artifact. This advisory is the only file
created by the audit.

## Bytes audited

| artifact | locally recomputed SHA-256 |
|---|---|
| `20260907_fable_v61_terminal_three_root_report_v2.md` | `2f01a33187571cda2c3035bec19e000108fb2ae8f1456251afaf110506ba34a0` |
| `20260907_fable_v61_terminal_analysis_v2.json` | `93ec4301a722f7b8b237cb6516fd30ac506405da0d0a9dc14a39bb0f6ff90e46` |
| `20260907_fable_v61_terminal_artifact_manifest_v2.json` | `ec7949ae176595d7cc4229545920f41539be7ff2de09aee7cb4d181110f18a80` |
| `analyze_fable_v61_probe_actions.py` | `174bf386acd42abe934a8bef0cb2363c5aceecf155129d72e6e390d38667e231` |
| v1 independent reaudit | `a9405255130a336fb812e09906d46d35919741e778623f749dbfebd3e32ec016` |

The analyzer, compact-result, and manifest hashes exactly match the hashes
printed in the repaired report.

## Verdict

**REVISE.**

The repair closes the numerical, zero-floor, corpus-field, root-aggregation,
principal AUC-label, rounding, fixed-action-cap, and most claim-language
defects. The report and machine-readable files are internally consistent.
It does not close every exact v1 requirement, however. Most importantly, its
manifest is not the full receipt set required by the v1 reaudit, the remote
artifact bytes remain unavailable for independent verification without the
required explicit status label, and the requested parser/source-proxy corpus
acceptance statistic is still absent. These are repairable receipt and scope
defects, not a reason to reject the narrow negative design diagnosis.

## Checks that pass

### Exact paired checkpoint and panel coverage

In the `--compact-final` path used to create the audited JSON, the analyzer
requires the observed checkpoint tuple for each named root to equal exactly
`(64, 128, ..., 1024)`. A checkpoint is admitted only when both ON/OFF ledgers
and both ON/OFF summaries exist. `read_actions()` rejects unexpected episode
IDs and requires all eight registered IDs to occur; `read_probe_summary()`
requires exactly the same eight result keys. The compact JSON independently
records the exact 16-number tuple for each of roots 0, 1, and 2. Thus the
8-program by 16-checkpoint by 2-arm coverage claim passes, subject to the
structural-truncation qualification below.

### Ledger/summary agreement and live zero floor

For every admitted root/checkpoint/arm, the analyzer reconstructs each
program's full-ledger score as `max([0.0] + action_scores)`, compares every one
of the eight values with its saved summary value at absolute tolerance
`1e-12`, verifies the stored summary mean against its eight values, and then
checks the panel mean again. Fixed caps use the same zero floor. The local unit
tests for negative-score flooring, exact program sets, malformed JSONL,
summary mean mismatch, ledger/summary mismatch, corpus-field selection, and
four-file pair discovery all pass (`7/7`).

### Corpus field and dialect naming

`corpus_texts()` now schema-checks and reads only `payload["corpus"]`; it no
longer adds `principles` or arbitrary metadata values. The report accurately
renames the published statistic as the share of exact column-zero uppercase
`ACT:` lines within the broader case-insensitive embedded-colon `ACT\s*:`
heuristic. It explicitly says this is a dialect proxy, not parser compliance.
The displayed `1261/1343`, `1005/1149`, and `352/1449` fractions, complements,
and rounding match the compact JSON.

### Machine-readable values, hashes, and arithmetic

The compact result and manifest are valid JSON. The manifest has 306 unique,
lexically sorted paths; every row has a nonnegative byte count and a
lower-case 64-hex SHA-256. Its row count and byte sum independently recompute
to `306` and `549182047`. Compact, key-sorted JSON encoding of the `entries`
array recomputes to
`ee864d1eb9a77556ce0bdf496f01194c60825b5b1178ab4f22b983d38d45b10c`,
matching both JSON files and the report.

The terminal rows, three-root mean/median and signs, AUC values and signs,
corpus endpoints, action counts, dominant counts, and fixed-cap root summaries
in the report agree with the compact JSON at the displayed precision. Nine
decimal places resolve the former root-0 AUC subtraction discrepancy.

### Root aggregation and narrow action-cap interpretation

The compact JSON provides, for every cap and every root, `n=16`, mean, median,
and positive/negative checkpoint counts. Its separately named pooled section
calls the 48 rows dependent checkpoints rather than replications. The report
presents the root means, identifies the within-root dependence, and makes only
the narrower first-action statement for roots 0 and 1. It explicitly leaves
generated-token volume, parsing probability, unseeded sampling, checkpoint
dependence, and other arm differences unresolved. This closes the v1
aggregation and action-cap requirements.

### Primary AUC and scientific-claim language

The audited report and compact result use “post-first-write probe-window AUC”
and specify episodes 64--1,024; the report explicitly says it is not
whole-lifetime AUC. The stability--plasticity, destructive transport,
discovery, parenting, continual-improvement, and superiority overclaims from
v1 are removed. The report calls the paths heterogeneous, limits the result to
post-hoc design diagnosis, qualifies the panel observations as associations,
and preserves the unseeded/runtime-ancestry/confounding caveats.

## Exact remaining issues

### 1. The 306-entry manifest is internally valid but not complete under the v1 receipt requirement

The 306 rows break down exactly as the repaired report says:

- 96 probe ledgers;
- 96 probe summaries;
- 96 sleep corpora, 32 per root;
- 3 root-level `LIFE_DONE` markers;
- 3 terminal `sleep_1024/COMPILED` markers;
- 3 terminal `sleep_1024/adapter/DONE` markers; and
- 3 each of terminal adapter config, weights, and training metadata.

That closes the ledger, summary, corpus, terminal-adapter, and terminal-marker
categories. It does not close v1 correction 4's full receipt scope:

- the analyzer itself is not an entry;
- the compact analyzer output is not an entry;
- no bound runtime source is an entry; and
- the manifest includes only the three terminal `COMPILED` and three terminal
  adapter `DONE` markers, not the 93 nonterminal markers of each type implied
  by the 31 other receipted sleep directories per root.

The analyzer and compact output do have separately printed hashes, which is
useful, but that is not the requested single sorted full-evidence manifest.
The eight on-disk source files listed by the earlier audit are source proxies,
not proven imported runtime bytes; the repaired report correctly preserves
that ancestry limitation, but no source receipt of either kind is in this
manifest. Therefore the heading “Complete artifact manifest” must either be
narrowed to “remote analysis-input and terminal-state manifest,” with its
omissions stated, or the missing categories must be added to a new manifest.

### 2. Remote-derived values are still not independently artifact-verified

`/localhome/local-rohing/v6_out` is absent in this audit environment, and no
terminal probe ledger was found under `/Users/rohing`. I therefore could not
recompute any manifest entry's byte count or SHA-256, rerun the analyzer over
the remote inputs, or reconstruct AUC and cap values from the 96 ledgers. The
local checks establish source/output/manifest consistency only.

V1 correction 4 explicitly required all remote-derived values to be labeled
“reported, not independently artifact-verified” until an auditor could access
the bytes. V2 instead calls the panels “Exact” and the manifest “Complete” and
never gives that required evidence-status label. Add the label to the terminal
scores, AUCs, cap summaries, action/corpus counts, and remote manifest
receipts, or provide the receipted remote bytes for independent hashing and
reconstruction.

### 3. The requested parser/source-proxy corpus statistic is missing

The corpus-field and dialect-name repair is correct, but v1 correction 2 also
required a separate acceptance count using the exact run-bound parser, or,
because runtime bytes cannot be bound here, an explicitly named source-proxy
parser count plus near-miss categories. The analyzer computes only:

- the broader embedded-colon heuristic;
- exact column-zero uppercase `ACT:`;
- hash-prefixed lines; and
- a catch-all decorated complement.

It never applies the inspected parser expression to the corpus lines and does
not report a parser/source-proxy acceptance numerator. The report's statement
that the legacy parser accepts other spellings is accurate disclosure, but it
does not supply the requested comparison statistic. Add a separately named
source-proxy acceptance count using the receipted on-disk parser bytes and
retain the runtime-ancestry caveat; do not call it run-bound compliance.

### 4. “Rejects truncated files” is proved only for syntactically truncated JSONL

`read_actions()` rejects an invalid partial JSON line and missing/unexpected
program IDs. It does not require a per-program terminal record or other
completion invariant. A valid JSONL prefix that has already mentioned all
eight IDs can pass if the retained actions' zero-floored maxima still match
the summary, even if later non-improving rows were lost. The unit test covers
only an invalid partial JSON object.

Either narrow the claim to “rejects malformed JSONL and missing/unexpected
program IDs” or add a receipted row-count/completion invariant sufficient to
detect valid-record-boundary truncation. The present manifest hash would
detect mutation only when compared with accessible original bytes; it cannot
establish this independently in the current environment.

### 5. Two analyzer output modes retain the old AUC name

The audited compact artifact correctly uses
`post_first_write_probe_window_auc_by_seed`, but the analyzer's
`--summary-only` and default output paths still emit `lifetime_auc_by_seed`.
Rename those two keys as well. This is a naming defect in the reproducer, not
an arithmetic defect in the audited compact result.

### 6. One causal-sounding sentence should be narrowed

The sentence “These associations show that the legacy writer is behaviorally
consequential” still combines an associational premise with a causal-sounding
conclusion despite the unseeded, non-common-random arms. Replace it with a
direct observation such as “adapter status is associated with materially
different behavior in these three paths.” The surrounding caveats and the
rest of the report's claim language are appropriately noncausal.

## Disposition

The repaired result is suitable as an internally consistent, author-reported
post-hoc design diagnosis. It is not yet a fully receipted or independently
artifact-verified terminal result, and it should not be marked closed until
the six scoped items above are repaired or the corresponding claims are
narrowed. No new run, model call, compiler call, benchmark, or GPU work is
needed for those repairs.

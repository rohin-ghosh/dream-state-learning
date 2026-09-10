# Fable v6.1 terminal three-root report independent reaudit v1

Date: 2026-09-07 UTC

Scope: fresh, read-only audit of
`20260907_fable_v61_terminal_three_root_report_v1.md`, its analyzer, and the
five earlier v6.1 audits/follow-ups. No model, compiler, adapter, benchmark,
run process, or GPU operation was invoked or changed. The audited report and
analyzer were not modified; this advisory is the only new file.

Audited report SHA-256:
`4baf7b52d5a741fcb5c34db2adf5e74b99138ea786011f95f9a373922660d603`.

Audited analyzer SHA-256:
`6eea666a0de0e34bcf1655acfe7d3be84a76bcb48fc39ba589982f63e55a633b`.
This exactly matches the analyzer hash printed in the report.

## Verdict

**REVISE; source/report-consistency pass with material qualifications, but
not an independent artifact-verification pass.**

The displayed terminal arithmetic is correct, the high-level warning against
a pooled positive continual-learning claim is warranted, and the report is
appropriately explicit that the run establishes neither parenting nor novel
strategy discovery. Its qualitative picture -- two adapter-on concentrated
plateaus and one severe executable-channel failure -- is consistent with the
earlier contemporaneous reports.

The report is not ready to be treated as a fully receipted terminal result,
however. Three defects touch its central evidence: the analyzer does not prove
that a ledger pair is complete, its corpus “strict” statistic is not the
registered parser's acceptance statistic and may include corpus metadata, and
the terminal receipt table does not bind the intermediate ledgers used for AUC
and 48-checkpoint cap aggregates. Several causal/mechanistic phrases also
exceed what the unseeded, post-hoc design establishes.

The negative scientific bottom line survives these corrections. The exact
counts, AUCs, and cap summaries remain author-reported until the consumed
artifacts are independently available and the analyzer defects below are
repaired or shown not to change the results.

## Evidence boundary: local consistency versus artifact verification

The remote root named by the report,
`/localhome/local-rohing/v6_out`, does not exist in this audit environment.
No `v6_out` directory or terminal `probe_ep1024.ledger.jsonl` was available
under `/Users/rohing`. Therefore I could not open the listed remote files,
recompute their hashes, rerun the analyzer on them, verify ledger cardinality,
or compare reconstructed scores with probe-summary JSON.

What was independently verified locally:

- the report and analyzer bytes and their hashes;
- arithmetic that can be recomputed from values printed in the report;
- consistency with values and trajectories printed in the five prior v6.1
  audits/follow-ups;
- analyzer behavior by source inspection; and
- the locally inspected `organism_v6/batch_loop.py` hash,
  `42ddb1b9a2a9b821bf025d847b327b18fade58b850053e1507702a919df4cc59`,
  which matches the on-disk source hash recorded by the earlier audit.

The last point is source consistency, not runtime binding. The earlier audit
explicitly found that long-lived processes could have imported older bytes
before source files changed, so the exact live parser/runtime ancestry remains
unproven. The terminal receipt strings are syntactically plausible SHA-256
values, but without the files they are claims about artifacts, not
independently verified receipts.

## Arithmetic audit

### Values that pass

Using the six-decimal terminal values printed in the report:

| root | recomputed on - off |
|---:|---:|
| 0 | `0.523262 - 0.486184 = +0.037078` |
| 1 | `0.529087 - 0.470193 = +0.058894` |
| 2 | `0.051111 - 0.485945 = -0.434834` |

Their mean is exactly `-0.112954` and their median is `+0.037078` at the
displayed precision. The signs and two-positive/one-negative root count are
correct.

The reported marker divisions also round correctly:

- `1261 / 1343 = 0.9389426657`, printed `0.938943`, with `1343-1261=82`;
- `1005 / 1149 = 0.8746736292`, printed `0.874674`, with `1149-1005=144`;
- `352 / 1449 = 0.2429261560`, printed `0.242926`, with `1449-352=1097`.

The terminal dominant shares also round correctly:
`161/163 = 98.773%` and `145/156 = 92.949%`.

### Display-level discrepancy

The root-0 AUC row prints on `0.510645`, off `0.477639`, and difference
`+0.033005`. The displayed operands subtract to `+0.033006`. This can easily
result from independently rounding higher-precision analyzer outputs, but a
table presented as exact must either show enough digits, mark columns as
independently rounded, or print a difference consistent with the displayed
operands. The other two AUC rows are consistent at six decimals.

### Values not independently recomputable here

The fixed-first-action deltas, all AUC values, per-root checkpoint sign counts,
48-checkpoint cap means/medians, and `33`--`35` positive-pair range require the
remote ledgers. Their formulas are visible in the analyzer and the printed
numbers are mutually plausible, but the underlying values and ordering could
not be verified from local files.

## Material findings

### 1. “Complete paired checkpoint” is only a filename-existence test

`complete_checkpoints()` admits a checkpoint whenever an adapter-on ledger
filename and its adapter-off counterpart exist. It does not require either
summary JSON, exactly the eight registered probe IDs, a terminal record,
non-truncated JSONL, or agreement with the saved summary. `capped_panel()` then
pads any missing episode IDs with zero and rejects only *more than* eight IDs.
An interrupted seven-program ledger can therefore be silently scored as an
eight-program “complete” panel.

Consequences:

- report lines 13--15 (“complete paired ... artifacts at all sixteen
  checkpoints”) are not established by the analyzer described as the
  reproducer;
- line 35 (“saved best-of-panel scores”) is imprecise because the analyzer
  reconstructs scores from act rows and never reads or cross-checks the saved
  probe-summary JSON; and
- selecting `rows[-1]` as “terminal” means latest discovered pair, not a
  required episode-1024 pair.

There is a second score-semantics edge case. The live state initializes
`best_score = 0.0`, but `capped_panel()` uses the maximum recorded score without
flooring a nonempty all-negative prefix at zero. Thus its reconstruction can
disagree with the registered best score for a program whose first `K` actions
are all negative. The terminal data may not exercise this edge, but that must
be demonstrated rather than assumed.

### 2. The reported “strict-marker fraction” is not parser compliance

The analyzer defines its numerator as case-sensitive exact-column-zero
`^ACT:\s*` and its denominator as any line containing case-insensitive
`ACT\s*:` anywhere. That is a useful, explicitly post-hoc dialect proxy, but it
is not the inspected harness parser's accepted language.

The locally inspected `batch_loop.py` uses:

```text
^(PREDICT|ACT|NOTE|RECALL|DONE)\s*:?\s*(.*)$
```

with multiline matching. For the `ACT` branch this accepts, among other forms,
`ACT: x`, `ACT : x`, and colonless `ACT x`; because the delimiter is optional,
it even matches `ACTION: x` as `ACT` with argument `ION: x`. It rejects leading
indentation, lowercase `act:`, and the observed Markdown wrappers. The
analyzer's numerator and denominator therefore neither reproduce nor fully
bracket parser acceptance.

There is also a corpus-schema problem. `corpus_texts()` iterates *all* values of
a JSON object. The legacy writer stores `corpus`, numeric `n_new`, and a
separate `principles` list; principles have already been inserted into
`corpus` with a prefix. The analyzer can consequently inspect corpus metadata
and duplicate current principles rather than measuring only the actual texts
passed to `train_adapter.py` (`payload["corpus"]`). Whether this changes the
reported terminal marker counts cannot be determined without the remote
corpora.

Therefore report lines 80--93 must not call these values strict parser
fractions or use them alone to localize registered failure. They are exact
`^ACT:` shares among lines matching a broader embedded-colon heuristic, subject
to recomputation over the actual training corpus field.

### 3. Receipts do not bind the evidence used for the longitudinal claims

The terminal table supplies seven episode-1024 hashes per root. That is useful
for terminal endpoints, action counts, terminal corpus statistics, and the
terminal adapter bytes if an auditor can access the files. It does not list or
aggregate-hash the 90 nonterminal ON/OFF ledgers consumed by the sixteen-point
AUC and 48-pair fixed-cap analyses. Nor does it receipt an analyzer output file
or manifest that maps every consumed path to size and hash.

Earlier follow-ups partially cover prior data, but not the exact evidence set:
the v2 aggregates are described as hashes over paired probe JSON rather than
the ledgers the analyzer reads; later notes receipt selected episode-832,
episode-896, and episode-960 ledgers. They do not collectively bind all 96
ON/OFF ledger inputs used by the terminal analyzer.

The report also has no hashes for `LIFE_DONE`, intermediate `COMPILED`/adapter
`DONE` state, `train_meta.json`, or a full terminal directory manifest. A hash
does not by itself establish completeness or ancestry. The prior source/runtime
warning remains in force.

### 4. Checkpoint pooling is descriptive, not a 48-unit replication

The cap means, medians, and positive counts pool sixteen dependent checkpoints
from each of three roots. Equal checkpoint counts happen to give each root
equal numeric weight in the mean, but `33`--`35 of 48` must not be read as 48
independent replications. The report acknowledges dependence elsewhere, yet
the cap paragraph does not state it at the point of use and does not expose
root-level cap summaries. A single collapsing trajectory can dominate all
pooled means while the two concentrated trajectories dominate the medians;
that contrast is a description of these three paths, not an estimated
population distribution.

The fixed-action diagnostic does show a narrower fact if recomputed values are
valid: taking more *parsed/executed actions beyond the cap* cannot explain
every positive ON-minus-OFF checkpoint. It does not rule out generated-token
volume, parsing probability, stochastic generation, or other between-root and
between-probe differences. “Rules out a universal action-volume explanation”
is too broad without that qualification.

### 5. AUC is post-first-write probe-window AUC, not whole-lifetime AUC

The normalized trapezoid starts at episode 64 and ends at 1,024. Episode zero
and the first 64 waking episodes are excluded because the report says the
episode-zero harness was not comparable. This is a defensible diagnostic, but
“lifetime AUC” overstates its temporal coverage. It is a normalized
post-first-write probe-window AUC over `[64, 1024]`. The report should say so in
the table, prose, and output interpretation.

### 6. Several mechanism verbs outrun the design

The design has unseeded ON/OFF generations, incomplete runtime ancestry, a
repeated 67-program curriculum, post-hoc endpoints, and no intervention on
the proposed self-reinforcement mechanism. Those limitations are accurately
listed, but the following phrases are still too strong:

- “stability--plasticity failure distribution” names an unmeasured theoretical
  tradeoff; the data establish heterogeneous behavioral outcomes;
- “repeated LoRA writes can ... transport ... and ... destroy” is causal and
  should be an adapter-associated observation or a “consistent with” claim;
- “localizes ... to self-reinforcing serialization drift” conflates a proximal
  serialization mismatch with a longitudinal causal feedback mechanism;
- “rules out a universal action-volume explanation” exceeds the scope of the
  executed-action cap; and
- “does justify three prospective gates” should be “motivates” or “reinforces
  the rationale for,” not validation that those gates are sufficient.

The saved terminal examples plus the permissive post-hoc evaluation can
support this narrower statement: decorated serialization is a demonstrated
proximal reason that particular useful saved action strings were not executed,
and the temporal corpus association is consistent with, but does not identify,
a self-reinforcing writer mechanism.

### 7. Learning/discovery boundary is mostly good but should be uniform

The report correctly says it supports no confirmatory learning, parenting,
discovery, or superiority claim; explicitly notes that the four-pass opening
was in the birth prompt; and refuses to relabel prompt-seeded extension as
invention. Those are important strengths.

For consistency, the bottom line should not assert that the system was
“sometimes transporting a useful taught procedure.” The evidence shows
adapter-associated repetition/generalization of routines extending a
prompt-supplied scaffold and is *compatible with* reinforcement/transport.
Because adapter-off generation is not common-random and the terminal routines
are six-pass extensions rather than the exact supplied four-pass string,
“transport” should remain an interpretation, not a discovered learning fact.
Likewise “plateau rather than continue improving” is a held-out panel plateau,
not proof that no other competence changed.

## Exact required corrections before a clean pass

1. **Validate complete panels.** Require checkpoint set exactly
   `{64,128,...,1024}` for each named root; require both JSON and JSONL files;
   require exactly the eight registered probe IDs in every ledger; reject
   malformed/truncated files and unexpected IDs; recompute each program's
   `max(0.0, first-K scores)`; and assert full-ledger per-program best scores and
   means agree with the saved summary JSON within a declared tolerance.

2. **Recompute and relabel corpus statistics.** Read only the schema-validated
   `payload["corpus"]` training texts. Report the existing numerator as
   “exact-column-zero uppercase `ACT:` lines,” not “strict parser” rows. Add a
   separate acceptance count using the exact parser implementation bound to
   the run, plus explicit near-miss categories. If runtime parser bytes cannot
   be bound, call the comparison source-proxy analysis and retain the ancestry
   caveat.

3. **Re-run every reported scalar after corrections 1--2.** Publish a compact
   machine-readable output and its SHA-256. If values are unchanged, state that
   explicitly; otherwise replace terminal scores, caps, AUCs, signs, action
   counts, marker counts, and derived prose.

4. **Receipt the full consumed evidence set.** Publish a sorted manifest with
   path relative to each `L_B_seed*` root, byte size, and SHA-256 for all 96
   ON/OFF ledgers and summaries, all corpus endpoints used, terminal adapters,
   completion markers, bound runtime sources, analyzer, and analyzer output.
   Hash the manifest itself. Until an independent auditor can access those
   bytes, explicitly label all remote-derived values “reported, not
   independently artifact-verified.”

5. **Make roots the descriptive aggregation unit.** Add per-root summaries for
   every action cap (mean/median or post-write cap AUC and positive/negative
   checkpoint count). Label checkpoint-pooled `n=48` results as dependent
   descriptive observations, not replication or uncertainty. Do not attach a
   population or distributional inference to three uncontrolled roots.

6. **Rename AUC.** Replace “lifetime AUC” with “normalized post-first-write
   probe-window AUC, episodes 64--1,024,” including in prose interpreting the
   result. Resolve the root-0 six-decimal subtraction mismatch by printing
   sufficient precision or noting independently rounded columns.

7. **Narrow the cap claim.** Replace “rules out a universal action-volume
   explanation” with: “under this post-hoc ledger reconstruction, later
   executed actions beyond the fixed cap cannot explain every positive paired
   checkpoint; token volume, parsing, stochastic generation, and root
   confounding remain unresolved.”

8. **Narrow causal and learning language.** Replace the theoretical
   “stability--plasticity failure distribution” with “heterogeneous behavioral
   outcomes”; replace causal “transporting/destroying” with “consistent with
   reinforcement/transport” and “coinciding with severe executable-channel
   loss”; replace “localizes ... to self-reinforcing” with “demonstrates a
   proximal serialization mismatch and is consistent with a self-reinforcing
   mechanism”; qualify the plateau as panel-specific; and replace “justifies”
   prospective gates with “motivates” or “reinforces their rationale.” Retain
   the existing explicit rejection of discovery, continual-learning,
   parenting, and superiority claims.

With these changes and an accessible full manifest, the report's core
conclusion could receive a clean descriptive terminal-audit pass. Without
them, it should remain an exploratory source-consistent synthesis rather than
an artifact-verified result.

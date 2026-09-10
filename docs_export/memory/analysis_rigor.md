---
name: analysis-rigor-cell-counts
description: "Report experiment mechanisms as cell counts, never narrativized patterns; my over-claims get independently audited"
metadata: 
  node_type: memory
  pinned: false
  originSessionId: d66e193e-e075-475c-96de-a582e32ee6c5
  modified: 2026-09-05T09:34:50.601Z
---

# Analysis rigor: cell-count claims, never narrative claims

During Dream-State v6 (2026-09-05), I reported a mechanism ("the adapter
takes 3x fewer but better actions — exploration collapse") from a diagnostic
table where that pattern held cleanly in only ONE of three lives. My own
printed output contradicted the summary (one life had MORE actions
adapter-on: 267 vs 120; another had a WORSE invalid rate), and I presented
range summaries ("~36-104 vs ~110-245") that glossed over the reversals.
Codex's independent verification (relayed by Rohin) found: fewer actions in
only 6/8 checkpoints, invalid-rate improvement in only 4/8 — plus a real
held-out-contamination bug I had missed (CompilerGym benchmark URIs carry a
"benchmark://" prefix, so my probe-exclusion string match failed and 3-6 of
8 "held-out" probes leaked into training).

Standing lessons:
1. When reporting an experimental mechanism, give PER-CELL COUNTS (e.g.,
   "6/8 checkpoints") and name the reversals explicitly. A mechanism that
   holds in one life is "a plausible hypothesis for one life," not a
   finding. Distinguish verified effects (paired score differences) from
   interpretive stories.
2. Before claiming any held-out/train split is clean, verify identifier
   NORMALIZATION on both sides of the exclusion (prefixes, URI forms,
   canonical names) — string mismatch silently voids the split.
3. This project runs adversarial cross-agent verification (Codex audits my
   claims, my reviewers audit Codex's). Write every claim expecting that
   audit: it will happen.

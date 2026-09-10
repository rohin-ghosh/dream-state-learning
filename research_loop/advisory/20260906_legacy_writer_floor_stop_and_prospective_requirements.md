# Legacy writer floor: stop decision and prospective collection requirements

Date: 2026-09-06

Status: author-side strategic advisory. This grants no architecture,
implementation, model, target, GPU, or scientific-claim authority.

## Decision

Do not implement or run the legacy continuation-writer floor from the current
v6.1 traces. This is not a scientific negative. Three fresh deliberations
converged on the same conclusion: a narrowly defensible assay could be built,
but only by adding disproportionate provenance, visibility, sealing, and
failure-state machinery around traces that were never collected for causal
replay. That is the wrong use of spare GPUs and engineering time.

The terminal v3 consensus is
`research_loop/changes/chg_20260906_legacy_continuation_writer_floor_v3/consensus.json`
(SHA-256 `648f99a32ce62fd996e7f0473e8d34672bb995ce67cca78d0e1e3e8e00c69a8c`).
It recommends rework and explicitly forbids implementation.

## What the old traces can and cannot say

They do establish a useful feasibility fact: exact persisted continuation
bytes exist in sufficient raw volume for a small adapter corpus. At the
audited wake-256 boundary the three lives contain 168, 179, and 127 unique
eligible continuations under the feasibility parser.

They do not preserve the prompts that produced those continuations. The known
birth example also dominates B0/B1: the exact four-pass example appears in
124/168 and 134/179 rows (and 34/127 in B2). Excluding it leaves only 44, 45,
and 93 rows. Consequently the legacy data cannot cleanly identify task
conditioning, prompt/action binding, novelty, recurrence, online learning, or
a full think/dream/sleep mechanism. Any adapter result would be compatible
with an offline cross-program action prior shaped by the birth prompt.

## Requirements transferred to the prospective nursery

The failed floor bought concrete collection laws. The next source life must
record these at generation time rather than reconstructing them later:

1. exact rendered user bytes, message JSON bytes, chat-template bytes,
   tokenizer revision, intended input IDs, and engine-reported consumed IDs;
2. immutable source-code/dependency/container hashes loaded by each process;
3. role-scoped stores: trainer can read only admitted training examples;
   target identities, outputs, and scores are unavailable to it;
4. typed tool calls separated from free thought, with the exact parsed action
   bytes, action-space indices, target reset-state module hash, I0/I1, and
   recomputed score joined in one atomic record;
5. parent correction, child restatement, dream successor state, and sleep
   target as distinct typed fields, with explicit masked-input versus
   supervised-target token spans;
6. generated-token budgets and outcome classes that separate accepted
   positive, accepted nonpositive, invalid, malformed, and silent behavior;
7. full-corpus feasibility receipts before training: nonzero labels, no target
   truncation, EOS retention, dose, duplication, payload diversity, and scope;
8. adapter tensor identity plus duplicate nonzero-adapter serving canaries;
9. an append-only authority/receipt DAG and whole-run atomic failure semantics;
10. a reporting-only output namespace that cannot automatically enter a live
    life, dream, parent pack, or future training corpus.

These are infrastructure requirements, not cognitive modules. THINK remains
one free-flowing model operation; DREAM remains context reconciliation; SLEEP
remains the write. The requirements only ensure that later claims refer to the
path that actually ran.

## Next experimental unit

Use a prospectively instrumented nursery cycle:

`child state -> prediction/thought -> typed action -> public outcome ->
parent process correction -> child restatement/near transfer -> dream state ->
response-only low-rank write -> parent-absent held-out behavior`.

First establish a writer/absorption floor and a single held-out disposition
change. Only then scale to repository-wide parenting, long CompilerGym lives,
or Rohin's teaching time. The old v6.1 lives remain valuable descriptive data
and an engineering stress test; they are not repurposed as causal nursery
training evidence.

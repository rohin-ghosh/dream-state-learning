# PCFL strong external-memory fairness audit

**Date:** 2026-09-13 PT  
**Role:** independent watcher-side, pre-execution audit  
**Evidence cut:** repository through `b834c375`  
**Scope:** PCFL v2.2 zero-fit and the proposed `PCFL-STREAM-16` successor;
no runtime, model, tokenizer, fit, benchmark, or GPU action

## Short verdict

The current PCFL v2.2 `ACTIVE_LINKED_TEXT` condition is **not** a strong
external agent-memory baseline. It is a supplied-memory service ceiling: the
fixture constructs an exact address-to-row map, the actor may request an exact
`EVENT`, `EVENTS_AT`, or `LINKS_FROM` address, and the service returns the
registered row. That is appropriate for proving that the task is readable,
but it cannot support a superiority claim.

The post-DEV `ACTIVE_LINKED_TEXT` design is close to a genuinely strong
baseline: it has an unlimited branch-local raw-plus-typed store, BM25 plus
typed-graph PPR, adaptive actor-written queries, citations, causal cuts, and
both on-policy and fixed-history comparisons. It is not yet claim-ready,
because it is unimplemented and because four remaining choices could
manufacture weakness:

1. selecting the access budget and certifying it on the same four roots;
2. allowing one of four certificate roots to fail completely;
3. calling a capped access curve or five-cut lifetime “saturation”; and
4. making the reusable stratum inaccessible to lexical/graph retrieval even
   though the LoRA sees the full training corpus.

None of this should delay zero-fit DEV. The smallest repair is a **zero-fit,
no-training certificate on four fresh baseline-only roots at the predeclared
maximum `(q=16, B=8192)`**, followed by the already planned on-policy and
same-DLT-history comparisons. This supports superiority over one precisely
named strong configuration. It does not, by itself, support “external memory
saturated.”

## 1. What each text condition actually tests

| condition | actual question | permitted label |
|---|---|---|
| v2.2 `FULL_CHILD_TEXT` | Can the actor use all ideal EVENT/LINK text placed in context? | supplied-text ceiling |
| v2.2 `ACTIVE_LINKED_TEXT` | Can the actor obtain ideal rows through an exact public-address service under 12 reads, 4096 returned tokens, and 2048 generated tokens? | supplied-memory service ceiling |
| C11 `M-TEXT` | Can a fixed policy use a finite supplied-memory relay? | fixed-policy supplied-memory precursor |
| successor `ACTIVE_LINKED_TEXT` | Can a frozen actor maintain and query its own evolving public raw-plus-typed memory? | strong external agent-memory baseline, **only after certificate** |
| `RAW_RAG` | Does ordinary lexical retrieval expose useful evidence? | retrieval ablation |
| `NATIVE_CONTEXT` | Does the evidence work while it still fits directly in context? | context ceiling/early-life reference |
| `EXACT_WITNESSED_GRAPH` | How much task headroom remains with an exact evidence graph? | oracle-like task ceiling, not a deployable baseline |

The v2.2 source makes the first distinction literal. `materialize_queries`
builds the exact request table from ideal rows. The runtime then permits at
most 12 sequential reads and returns the table entry or `MISS`. There is no
evolving updater, corpus-scale ranking, or native-life retrieval problem.

Historical static briefs, `Ledger.recall`, and the `EXTRA_MEMORY` LoRA arm are
not substitutes. `EXTRA_MEMORY` is another parametric writer treatment, not
external memory. The static brief and token-overlap recall path lack an
evolving lossless store, causal visibility, graph traversal, fixed token
accounting, and a certificate.

## 2. Fairness ledger

### Information

- **On-policy comparison:** DLT and linked text may collect different later
  histories. That is legitimate only as a whole-system comparison.
- **Fixed-history comparison:** at every cut, linked text must receive every
  unique eligible public event and authentic child EVENT/LINK row available
  in the DLT history, including rejected-row status, at the same frontier. It
  must not receive a DLT-only invented inference.
- Compiler paraphrases, wrappers, and repeated optimizer presentations are
  exposures, not extra experiences. Do not duplicate text records to imitate
  LoRA epochs.
- For a strict carrier attribution, add `ALT_SHARED`: exactly one canonical
  text record for each unique semantic source used by the DLT fit. Keep
  `ALT_FULL`—all eligible raw events plus admitted typed rows—as the stronger
  native opponent. Beating `ALT_FULL` is conservative; beating only
  `ALT_SHARED` licenses only a matched-information carrier claim.

### Availability and history

- Raw public action/outcome events should become searchable on the next
  continuation. Do not delay them to SLEEP merely to weaken text.
- A child-authored typed row should become searchable at the first common
  authenticated admission frontier. If formation is batched, siblings become
  visible only after the round barrier, never in Python consume order.
- On-policy stores, caches, query state, and histories remain branch-local.
  Same-history probes are disposable read-only forks and must not write back.

### Actor work, reads, and compute

- Freeze the maximum at `q=16` adaptive reads and `B=8192` cumulative returned
  memory tokens for the primary strong-text endpoint.
- Every query is generated by the ordinary actor. Query tokens and query
  turns count inside the same cumulative 2048 generated-token allowance;
  misses, repeats, invalid reads, and unused reads receive no replacement.
- Use the same task bytes, action allowance, output parser, addressed outcome
  tape, and decode seeds in paired conditions.
- Do **not** call compute matched. Linked text may consume up to 16 retrieval
  operations and additional model turns; DLT consumes optimizer/SLEEP compute
  and adapter storage. Report actor calls, query tokens, returned tokens,
  retrieval/index CPU time, prompt tokens, final-output tokens, persistent
  bytes, adapter bytes, optimizer target tokens/updates, accelerator time, and
  wall time separately.

### Context

- A tokenizer preflight must prove that task/state, all query/return turns,
  the full `B=8192` memory allowance, and the reserved actor output fit without
  truncation. Memory may not evict task/state or borrow output space.
- DLT's lack of returned text is a real systems advantage, but it can also be
  a context-position artifact. Run native-empty DLT plus a wrapper-,
  position-, and length-matched target-independent sham sensitivity. A change
  greater than `.05` blocks a pure carrier claim; the whole-system comparison
  remains reportable.

### Policy and topology

BM25 (`k1=1.2`, `b=.75`) plus 20-step float64 PPR, `.5/.5` score fusion, and
MMR `.8` is a credible PCFL-specific strong baseline. It is not a reproduction
of every external-memory method and should be named as the **certified PCFL
ACTIVE_LINKED_TEXT configuration**, not “external memory in general.” No dense
encoder is required if the frozen certificate passes.

The reusable-structure stratum is the most important leakage-by-design risk.
Fresh opaque IDs and local bindings can leave the query with no lexical or
graph bridge to earlier analogous modules, while LoRA training exposes every
module globally. That would design the text plateau. Before confirmation,
either:

1. prove in the certificate that ideal linked text can retrieve and solve the
   reusable cases without an identical answer row; or
2. run opaque-only and bound the claim to independent exact bindings.

Do not add cross-module retrieval cues or a reusable family after observing
which carrier wins.

## 3. Smallest exact strong-baseline certificate

This is post-DEV, zero-fit, inference-only, and uses **four fresh roots that
are never used to tune the retriever and never enter confirmation**.

To avoid an additional tune/certificate split, freeze `(q=16, B=8192)` before
these roots exist. The lower `q/B` response surface may be reported
descriptively but cannot select the primary configuration. If selecting a
smaller configuration matters later, use separate tuning roots.

Each root has 16 balanced, candidate-free tasks:

```text
2 information strata
  x 4 endpoint types
      (route, same-evidence/different-goal, delayed OLD+NEW, expansion)
  x 2 surface/order twins
= 16 tasks/root; 64 total.
```

For the reusable stratum, no identical answer row may exist. The registered
public evidence must still make the relation identifiable.

### Noncompensatory pass arithmetic

All of the following must pass:

1. Model-free visibility, future-answer blindness, row hashes, citation
   identity, restart/cache rebuild, insertion-order invariance, and wrong-root
   isolation are exact: `100%`.
2. `FULL_CHILD_TEXT`, `ALT_MAX(q16,B8192)`, and
   `EXACT_WITNESSED_GRAPH` each score at least `60/64`, with no root below
   `14/16`. This replaces “15/16 on three of four,” which permits the fourth
   root to be `0/16`.
3. Legal final actions are at least `61/64` (`>=.95`). Every returned row has
   an exact source citation: `100%`.
4. A truthful binding twin redirects at least `12/16` tasks on **each** root
   (`>=48/64` pooled).
5. Each registered necessary-row/LINK/OLD/NEW cut loses at least `6/16` tasks
   on **each** root (`>=24/64` pooled for each cut family).
6. Adding irrelevant or wrong-root memory changes pooled utility and legality
   by at most `3/64` (`.046875 <= .05`) and produces zero valid false rows.
7. `EXACT_WITNESSED_GRAPH - NONE` leaves at least `.10` utility headroom.
8. The reusable half passes its own `>=30/32` floor. Otherwise the baseline
   has not shown access to the information on which broad superiority would
   be judged.

Certificate failure means the assay has not fielded a strong opponent. It is
never evidence that parametric memory is better.

## 4. Smallest paper endpoint after the certificate

No extra baseline fit is needed.

At every presealed lifetime cut:

1. run on-policy `DLT_PERIODIC`, `SLEEP_FROZEN`, and `ALT_FULL` from identical
   empty deployment states under the common opportunity tape;
2. on a disposable copy of the exact DLT history, evaluate `DLT`, `ALT_FULL`,
   and `ALT_SHARED` with common tasks/seeds and the frozen q16/B8192 reader;
3. retain `RAW_RAG`, `NATIVE_CONTEXT`, `EXACT_WITNESSED_GRAPH`, and
   `NONE/WRONG_ROOT` as diagnostics; and
4. report root-paired normalized AUC plus terminal utility.

A defensible **whole-system** statement requires the certificate,
`DLT_PERIODIC - ALT_FULL >= .05`, a one-sided 95% root-level lower bound above
zero, and a positive terminal difference. A **parametric carrier** statement
additionally requires the fixed-DLT-history DLT-minus-`ALT_FULL` AUC lower
bound above zero. If DLT beats only `ALT_SHARED`, say “matched unique semantic
records,” not “strong external memory.”

If the reusable stratum exists, require positive DLT-minus-text AUC there and
an opaque-stratum harm upper bound below `.05`; never hide either stratum in
the average.

## 5. Saturation is a separate result

Three different claims must not be merged:

- Flat utility from lower to higher `q/B` is **access-budget response**.
- Flat utility across five life cuts is a **finite observed curve**.
- “Practical local plateau” requires the prospectively frozen seven-cut
  extension: new unique evidence every interval, simultaneous 90%
  equivalence intervals for late slope and the last two gains inside
  `[-.05,+.05]`, retained old competence, exact-graph headroom `>=.10`, and a
  doubled-access condition also flat within `.05`.

If q16/B8192 still helps, label it `MAX_TESTED_ACCESS`. DLT may still be
reported as superior to that exact certified configuration if the endpoint
above passes; neither “saturated baseline” nor “improves beyond saturation”
is then permitted. If the benchmark cannot physically double access without
context truncation, saturation is simply unmeasured.

## 6. Release decision

Proceed with PCFL v2.2 zero-fit unchanged. Its exact service ceiling is an
upstream assay check, not the final opponent.

After DEV passes, the cheapest fair strong-baseline path is:

```text
freeze ALT_MAX q16/B8192
  -> four fresh zero-fit certificate roots
  -> freeze updater/retriever bytes
  -> run ALT_FULL on-policy and on identical DLT histories at every cut
  -> add ALT_SHARED only as the cheap matched-information attribution
  -> claim exact-configuration superiority if and only if its gates pass
  -> reserve saturation language for the seven-cut extension
```

The current hard blockers are therefore implementation, a fresh-root
certificate, exact availability/context accounting, and the reusable-stratum
access proof. They are post-DEV work and do not justify delaying zero-fit DEV.

## Evidence inspected

- `organism_v6/pcfl_vertical_dev.py`
- `gpu/astra_pcfl_vertical_dev.py`
- `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_synthesis.md`
- `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_2_writer_repair.md`
- `research_notes/analysis/2026-09-13_pcfl_dev_to_paper_grade_successor.md`
- `research_notes/analysis/2026-09-13_pcfl_stream16_successor_objective_redteam.md`
- `research_notes/analysis/2026-09-13_downstream_compression_and_strong_memory_gate.md`
- `research_notes/analysis/2026-09-12_text_memory_baseline_readiness_audit.md`
- `research_notes/2026-09-11_strong_evolving_active_text_baseline_candidate.md`
- `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/change.json`
- `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/consensus.json`

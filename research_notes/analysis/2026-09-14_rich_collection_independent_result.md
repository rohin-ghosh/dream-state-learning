# SEQ261 rich-v1 collection — independent terminal review, 2026-09-14

**Released.** Frozen full-stage replay and direct episode reductions agree with
`2026-09-14_rich_collection_first_result.md`: 880 recorded native calls,
80 valid source EVENTs, all 64 planned TEACH episodes attempted but none
complete, and zero admitted rows in each of the three supervision views.
All 16 native phases completed; no fit occurred. The dominant failure is a
literal prediction-label gate, not evidence of a unique semantic deficiency.

## Evidence and replay

Root `C` is
`gpu_artifacts_local/astra_rich_collection_terminal_20260914_attempt1/extracted/astra_rich_collection_20260914_attempt1`.
The sibling `terminal.tar.gz` verifies to
`2d7a387dba0006b7b066f0d41459a017ce2b0059c48c269f8c90297e76c905eb`.
Frozen source is `803f59c809d836f60f7a22b57a75b4d045626994`; its bound rich
protocol SHA is `339c25c05cdb1bd6ba07bfd22520c68df6f23117fed0627cb245e23c6ba2bd2f`.
Checked 1,164 phase/prepare/launch JSON files against archive payload bytes,
and all 41 imported frozen Python files against local Git objects. The frozen
protocol file also matches its bound hash. This is bounded evidence checking,
not a complete ancestor or archive-inventory certification.

Replayed `source/gpu/astra_rich_trajectory_collection.py:execute_phase` for all
four phases on all four shards. The generator callback consumed only saved
`CALL_*.json` responses, checking exact prompts and role/task metadata, then
required complete consumption and equality with each saved `DATA.json`.
The emission callback compared 128 would-be output documents without writing
them. Rich/goal helpers retained their private FunctionType-bound namespaces;
old unbound hop defaults were not substituted. Per-phase output-file hashes,
source/teaching/critique result dependencies, and registry hashes also join.

| Shard | EXPOSE calls | TEACH calls | CRITIQUE calls | BASELINE calls |
|---|---:|---:|---:|---:|
| 0 | 40 | 21 | 16 | 140 |
| 1 | 40 | 25 | 16 | 141 |
| 2 | 40 | 28 | 16 | 137 |
| 3 | 40 | 20 | 16 | 144 |
| Total | 160 | 94 | 64 | 562 |

Each shard's five worlds contain four accepted records: 80 actual ROUTEs and
80 actual EVENT responses, not 80 synthetic replacements. Direct checks join
each emitted ROUTE to its offered port and each transition's source, port,
destination and receipt to the edge; actual EVENT text matches the receipt's
expected identifiers. Full replay independently regenerates the public prompts.

## TEACH failures and interpretation

All 64 attempt-manifest entries are attempted, failed and retained. The 94
rich calls comprise 30 passing intermediate calls plus 64 terminal checker
rejects; zero complete episodes means zero TERSE, RICH and RICH_ACTION_ONLY
candidate rows. The prospective partial-candidate policy did not discard
otherwise complete episodes. No hidden native exception explains these zeros:
all saved native call errors are null and no `FAILED.json` is present.
Episode `actor_callback_error` here records the replayed validation exception.

| First stopping check | Count |
|---|---:|
| `explicit_prediction_line_required` | 56 |
| `not exact short ROUTE` | 5 |
| `exact_rationale_action_envelope_required` | 2 |
| `rationale_unseen_public_identifier` | 1 |

All **56** prediction-gated responses contain a parsed action matching the
source-informed coach's prescribed command. The checker runs before returning
that action to the environment, so it was not executed on that turn. Of these
stops, 37 occur at turn index 0, 18 at index 1, and one at index 2. Earlier
actions remain recorded; there is no observed continuation after rejection.
Thus zero candidates does not establish inability to execute the remaining
actions, nor does this action agreement authenticate the rationale's truth.

Important precision for the other labels (zero-based shard/world/task):

- The five `not exact short ROUTE` errors are **not five demonstrated wrong
  ROUTE choices**. Four action suffixes contain extra prediction prose
  (0/1/3, 1/2/2, 2/1/1, 2/3/3); two of those begin with READ. The fifth
  (2/3/2) emits unsupported `WAIT`. These fail the strict command parser.
- The two envelope rejects (0/2/2 and 2/3/1) emit bare READ commands. The
  public system allows command-only output, while the coach requests an
  envelope and the actual rich parser requires it. Report these as failures
  of the declared rich capture contract, not necessarily invalid READ syntax.
- The unseen-ID rejection is 1/2/3. Identifier-membership checking is not
  comprehensive factual-content verification. Across all calls, 87 actions
  parse and 86 match the coach; this is not an autonomous action-success rate.

CRITIQUE preserves one actual call for every attempted episode. **62/64** pass
the capture/nonempty check; none has grounded-content approval. The other two
are shard2/call2 (world0/task2) and shard3/call4 (world1/task0): both have
nonempty text but hit 512 generated token IDs, terminal=false/truncated=true,
and replay `nonterminal_or_truncated`. They are not missing or empty critiques.
All other 878 calls are terminal and nontruncated. Every captured context is
within 2,048 tokens and output within its phase cap (160 or 512).

## Baseline and visibility

Direct final-goal/two-route reductions and frozen pair scoring reproduce:

| Unchanged37ec readout | Goals | Strict opposite-goal pairs |
|---|---:|---:|
| TRAIN OWN_TEXT | 33/64 | 3/32 |
| PROBE OWN_TEXT | 6/16 | 1/8 |
| PROBE UNAVAILABLE | 1/16 | 0/8 |

Strict pairs are tasks (0,2) and (1,3), requiring both goals and distinct
source-correct first ports. TRAIN successes are shard1/worldD pair(0,2),
shard2/worldA pair(1,3), and shard3/worldD pair(1,3). PROBE successful tasks
by shard are `[0]`, `[1,3]`, `[3]`, `[2,3]`; only shard1 has a pair.
UNAVAILABLE succeeds only shard0/task0. No cases are omitted: the 14-call
deficit from the 576-call baseline ceiling is six five-call invalid routes,
one five-call duplicate-address stop, and invalid-command stops at three
and two calls. All remaining episodes use six calls.

TEACH is intentionally source-informed: the native child sees the coach's
next command and, for routing, already-public source text. It is not blind or
autonomous planning. Replayed student prefixes exclude parent guidance; no
current rich PROBE identifiers occur in any TEACH guided/student prompt or
critique input. Critiques reconstruct only actual public action histories;
they do not receive the private plan, discarded rationale sidecars or scores.
Baseline actors receive command-only public tasks and actual OWN_TEXT or
UNAVAILABLE replies, without parent hints or evaluator witnesses. Teacher
scaffolding is not silently reclassified as child-discovered reasoning.

## State, cost and limits

Every phase records loaded/before/after state
`37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0`,
unchanged frozen base, zero fits/updates and training disabled. These are
recorded state/hash joins, **not actual tensor or base authentication**.
No learning, rich-vs-terse efficacy, retention change or H1/H2 result follows.

Summed native-phase elapsed seconds are EXPOSE 559.022308, TEACH 883.602348,
CRITIQUE 1,189.288936 and BASELINE 636.604836: **3,268.518428 seconds**, about
0.908 allocated A100-hours, including phase setup but excluding prepare and
outer guard overhead. This is not parallel campaign wall time or kernel
utilization. Guard records start all shards at 18:51:18 UTC, completing at
19:04:03/19:04:26/19:05:35/19:06:00 UTC. Generated token-ID totals are
4,869/11,831/18,183/6,303 by phase, including terminal IDs where present;
they are not supervised-label counts.

Checks used local `sha256sum`, `git show`, bounded file inspection and inline
standard-library Python (`json`, `hashlib`, `tarfile`, counters/assertions).
An import blocker excluded torch, transformers, tokenizers, peft, numpy and
HTTP clients; frozen replay imported none of them. Exploratory assertions
were corrected to the actual transition schema and to preserve the two
truncated critiques; the final all-phase replay passes. Final memo check:
`git diff --no-index --check /dev/null <this memo>`.

No model/tokenizer loading, GPU, network, new native calls, replay outputs or
changes outside this memo. No exhaustive prose-truth review, future v2 outcome,
unique semantic-failure explanation or broader framework approval is claimed.
Primary counts and its cautious interpretation agree; the parser-label and
critique details above are wording caveats, not changed results. Ownership
released for Main to bind.

# SEQ096 — independent bounded relation-surface review

Date: September 12, 2026, approximately 17:23 UTC.

## Verdict

**PASS for bounded numerical, provenance-binding, and interpretation consistency. No finding requiring correction.** Independently reproduced the relation counts **1/3 original, 3/3 fullclarified, 2/3 tokenclarified**, the **1/3 versus 3/3 full-record faithfulness** counts, and the reported call/token/time totals from archived raw receipts. The token-only condition has **no full-record endpoint**, not zero faithful records.

This is not a new scientific efficacy certification, general capability result, old-root material approval, GPU launch gate, or model-origin authentication. No repo edits, Git operations, network access, GPU/process queries, parent jobs, tests, or model executions were performed. Archives were read in memory without extraction. Only this requested `/tmp` report was written. Main's active panel and the earlier manuscript fixes were not re-reviewed or altered.

## Reviewed identities and evidence notation

- Memo: `research_notes/astra_memos/ASTRA_RELATION_SURFACE_TERMINAL_2026-09-12.md`, SHA256 `d308af5899027328a8e6d146c1f4ad91cc4d4a5a043122db3f133826e454ab1b`.
- New capsule: `research_notes/astra_memos/receipts_20260912/astra_relation_surface_terminal_20260912.tgz`, independently hashed to the requested **`acf05efb84c336b9afd3d495a81f37e43627d551dc4dd3999d5f8533353de2e0`**.
- Its `reduction.json` independently hashes to **`a8c5d25657cfa946dd8cc77bc7918621150ddccf612168963ffd61e159833dca`**, matching memo lines 49–50 and `main_release.json`.
- Prior v2 capsule independently hashes to `d3433cc22e398343bee59f755f2d2ac9dc5308347eba4ef421abdd76ae969ef8`.
- Below, **S** denotes member root `astra_relation_surface_20260912_attempt1/` in the new capsule; **V** denotes `astra_rulegame_interaction_v2_20260912_attempt1/` in the prior v2 capsule. JSON receipt members are single-line files: references to members mean line 1 plus the named JSON path. JSONL references use actual line numbers.

## 1. Exact original-case binding — PASS

| v2 record call | v2 action call | Execution suffix | Actual TRY | Prediction | Observation | Expected relation | New calls: original / fullclarified / tokenclarified |
|---|---|---|---|---|---|---|---|
| 0008 | 0007 | #t1 | [2,3,4] | false | true | mismatched | 0000 / 0001 / 0002 |
| 0010 | 0009 | #t2 | [1,2,3] | true | true | matched | 0003 / 0004 / 0005 |
| 0012 | 0011 | #t3 | [0,1,2] | null / absent | true | unavailable | 0006 / 0007 / 0008 |

All executions belong to exactly `P:rule0/astra-minimum-20260912/lesson0/apply`. I cross-checked record-to-action IDs, execution IDs, triples, prediction fields, returned outcomes, and source response text against **V/formation/data/events.jsonl**, record lines 8, 10, 12, and **V/formation/data/calls/**. These are not substituted cases, newly simulated outcomes, or a selected A-only subset.

Additional custody checks:

- **S/plan.json** `formation_manifest` equals the actual SHA256 of **V/formation/data/manifest.json**: `4fef2770a6be151bc00fc4782575134643f8754b2cd149380b48a4aaf6dfed41`.
- Its `formation_plan` equals the actual SHA256 of **V/plan.json**: `5cc110bceb6e92186bc707fdd4369eaf53690a4fba694ac1fa5b8b8dbfcc88f7`.
- **S/plan.json** itself matches **S/plan.sha256.json**: `6c522873311b46398772bde30b640df2adbcba4ee9d6dcbb836d037aaa7d55ae`.
- All **21 file hashes** in **S/run/data/manifest.json** match archived bytes, including all 18 request/response files.
- The locally inspected `organism_v6/relation_surface_diagnostic.py` matches its archived source pin `497a1121e89f7214436b6a5b58a566f05f62f3af3e4225edad1e02fee44db8df`. Its lines 17–21 fix the old manifest/plan and three cases; lines 37–67 enforce exact records, raw action text, actual world fields, and original prompt identity. Lines 73–84 construct only the nine specified requests. This is a local source-file hash comparison, not independent reconstruction of a Git commit or remote source tree.

Memo anchors: lines 3–8 and 18–20. Source bindings and the recorded source path agree with the memo's new source identifier `1d12a4c40de58944ea34c986ff87afafc415bbc3`.

## 2. Actual input intervention — generic definition, not case-label injection

Every fullclarified prompt equals its exact original v2 record prompt plus one newline and this **identical case-independent string**:

> Explicit mapping: no prediction (null) => unavailable; prediction equal to observation => matched; prediction different from observation => mismatched.

This supplies the task's comparison rule, including all three possible labels; it does not append the expected answer for the particular case. The existing `Observed fields` explicitly expose the recorded values/prediction/observation in **all** conditions. Clarification therefore changes instruction content, not access to a newly computed per-case relation label. It is not an unaided deduction of the label semantics either: the definition is intentionally supplied.

- The new **original** condition's prompt bytes equal the corresponding archived v2 record-request prompt bytes.
- Within each new original/fullclarified pair, request dictionaries differ only in `call_id`, `surface`, and the appended `prompt` text. JSON output format, cap 100, temperature 0.0, seed 20260912, event, role, and stop settings are held fixed.
- Each tokenclarified prompt retains the exact original event prefix, then the same generic mapping, then “Output only the relation token: matched, mismatched, or unavailable. No JSON or other text.” It replaces the JSON instructions and changes the output cap to **8**, versus **100** in both full-record conditions. Thus token-only is not a single-factor format/cost comparison.
- Every recorded rendered prompt is exactly the request inside the same Qwen system/user/assistant wrapper. No extra case-specific system instruction or hidden answer block appears in the rendered prompts. All nine requests are role `record`, with no `expected` field.

Evidence: **S/plan.json** `requests`; all **S/run/data/calls/*.request.json** `request.prompt`; all response receipts `response.rendered_prompt`; source lines 23–29 and 73–84. Memo lines 22–29 correctly distinguish this within-run contrast from the historical v2 generations, whose temperatures were 0.7 and whose seeds were 1746689691, 1897205537, and 101859255. These new “original” calls are **fresh reruns**, not the old responses reused as a matched stochastic baseline.

## 3. Raw outputs and endpoint reduction — PASS

| Actual case | Original: relation / full-record faithful | Fullclarified: relation / full-record faithful | Tokenclarified: relation / relation correct |
|---|---|---|---|
| false / true | matched / no | mismatched / yes | mismatched / yes |
| true / true | matched / yes | matched / yes | matched / yes |
| absent / true | matched / no | unavailable / yes | matched / no |
| Correct relation | **1/3** | **3/3** | **2/3** |
| Faithful full record | **1/3** | **3/3** | **Not an endpoint** |

I decoded the six JSON outputs independently, checked their keys and fields against the source execution values, and recomputed each expected relation from the original prediction/observation pair. All six records are syntactically valid; the two failing original records have wrong relation values, not malformed syntax or wrong copied triples/Booleans. The three token responses are accepted relation strings. All nine archived `correct`, `unparseable`, `raw_text`, and applicable `record_audit.eligible` values agree with the independent reduction.

All nine generations report normal `finish_reason: stop`; none reaches its output cap. The token-only absent-prediction failure is preserved as `matched`, not corrected to `unavailable` or excused as truncation.

Evidence: **S/run/data/calls/0000.response.json** through **0008.response.json**, `response.text`; **S/reduction.json** `rows`. Memo table at lines 10–15 and endpoint distinction at lines 17–20 are accurate.

## 4. Calls, tokens, caps, and cost denominators — PASS

Counts below were independently summed from the native token-ID array lengths and paired request-start/response-end timestamps, not copied solely from reduction counters.

| Surface | Calls | Native input tokens | Native output tokens | Sum of maximum output caps | Generation-call seconds |
|---|---:|---:|---:|---:|---:|
| original | 3 | 762 | 108 | 300 | 3.159887536 |
| fullclarified | 3 | 840 | 111 | 300 | 3.231139185 |
| tokenclarified | 3 | 558 | 8 | 24 | 0.335586398 |
| **Total** | **9** | **2160** | **227** | **624** | **6.726613119** |

The clarified full-record prompts add 26 native input tokens per case; this is not a token-matched comparison. Equal original/fullclarified output caps do not imply equal realized token cost. The 624 figure is the sum of ceilings, not actual generated tokens.

**S/run/worker/supervision.json** records **81.985712571 seconds**, including owned cleanup, with `returncode: 0`, `ok: true`, empty owned group/device, and reservation release verified. This is not the outer launch-to-Main-release interval, active GPU compute, billed GPU time, or campaign throughput. Memo lines 38–45 retain the appropriate exclusions. No dollar cost is established; the reduction explicitly leaves `monetary_cost` null.

The archived stdout preserves cleanup escalation at line 54 (“killed 1 engine procs, freed=True”) and the resource-tracker semaphore warning at lines 56–57. **S/main_release.json** records Main's independent device/process/queue release check at 17:19:03.887863 UTC. This review reads those receipts; it does not re-certify live vacancy or independently prove the absence of every possible foreign-process side effect. The recorded backend cleanup scope is its owned handle/descendant engines only; no contradictory foreign-process targeting appears in the reviewed evidence.

## 5. Claim boundaries and smallest optional clarifications

**No required scientific wording fix found.** The following boundaries in the memo are supported and must survive manuscript integration:

- The three cases are deliberately selected, correlated events from one P-arm apply task, with positive observations only; they are neither a representative Boolean benchmark nor independent learner replicates (lines 18–20).
- Adding the generic definition changes the two erroneous fresh full-record outputs while leaving the already-correct case correct. This supports a local interface-definition explanation. It does not prove that ambiguous wording caused every historical failure, establish general Boolean competence, or test the strongest teacher (lines 22–29).
- The token condition's 2/3 is relation-only, not 2/3 faithful full JSON; the absent-prediction error remains (lines 17–18 and 26).
- These are nine new readouts from a fresh root, not replacement source records, retrospective rescue of SEQ094/095, or authorization to fit the old roots. Archived backend identity has `adapter_input: null` and `adapter_files: {}`; the release reports zero fits, parent calls, and world actions. No writer/parent/world phase is present in the nine-call capture (lines 7–8 and 29).
- No parenting, learned internalization, model ceiling, G3/P1/G5/H1/H2, mechanism freeze, or clean-lineage claim follows (lines 19–20 and 53). Official origin remains `UNRESOLVED_LOCAL_HASHES_ONLY`.

**Optional LOW-priority clarity, not a correction requirement:** label the first table column “Original prompt, fresh rerun at temperature 0” and say “two newly generated full-JSON responses” instead of “two repaired full-JSON responses.” The present lines 22–29 already supply the distinction, but these labels reduce the chance that a copied table is mistaken for retrospective old-root rescue. Also retain the **100/100/8** output-cap distinction if the token contrast is expanded in the manuscript.

The future training/design recommendations at memo lines 31–36 are not numerical consequences established by these nine calls. This review neither independently validates the earlier V3 negative-results history nor approves that proposed direction. They should remain recommendations/context, not be promoted as SEQ096 learning results.

## Disposition for Main

The memo's “independent numerical review is pending” status at lines 51–52 may now be updated to **“Independent bounded raw-call/count/source-binding review passes; no efficacy, generalization, or old-root writing approval is implied.”** Preserve the failed original/token outputs and all cleanup receipts. No rerun, new fit, seed/format search, or active-panel intervention is requested by this review.

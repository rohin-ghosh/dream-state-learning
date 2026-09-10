# Public Pathway Consolidation v4 — complete-bound execution amendment

Status: proposal only. The complete normative architecture is the following
ordered byte stack, all rebound in the v4 change artifact and fresh review:

```text
PPC1 change + protocol
< PPC2 change + protocol
< PPC3 change + protocol
< PPC4 change + this protocol
```

Later bytes override an explicit conflict; otherwise earlier clauses remain.
No unlisted note, consensus prose, code, Fable artifact, or previous run is
normative. This amendment disposes PPC3 consensus SHA-256
`41a5af896db6cef24a1b0a75d1e1ec9a8efd0f4e61dcf84536b70dd00aa71f81`.

## C1. Typed item roles close the learning/evaluation boundary

Every item is immutably assigned before dispatch:

```text
ACQUISITION       public action outcomes are visible within the life and may
                  become SLEEP candidates after item close.
MEDIATION_ACQUIRE like ACQUISITION, with a preassigned immutable mediation_id.
PROBE             same-item public transitions may support recurrent action,
                  but the complete item and score are writer-ineligible forever.
STATIC_SEAL       no model; instrument construction only.
```

Only closed ACQUISITION or MEDIATION_ACQUIRE roots enter later source THINK,
source DREAM, or SLEEP. A PROBE result never enters later cognition, retrieval,
DREAM, writer selection, training, or redesign. Confirmatory effects are
computed on PROBE items. Acquisition performance is descriptive except where a
separately registered acquisition estimand explicitly uses it.

Role transitions are impossible. The lifecycle records role before input hash.
The writer predicate requires role in `{ACQUISITION, MEDIATION_ACQUIRE}` and
rejects every PROBE-derived ancestor, mixed root set, or target-derived repair.

## C2. Privileged provenance and complete operation admission

`canonical_root_partition` is a privileged, precommitted equivalence partition
used only for deduplication, support independence, split sealing, and audit. It
contains opaque class hashes but no truth, answer, score, condition, or target
membership. Model and DREAM never see it. SLEEP may use class equality/union but
not generator semantics. Replacing hidden generator labels while preserving
public events and the partition must leave row inclusion and bytes unchanged.

A public cognitive transition is writer-eligible only when all predicates hold:

```text
item role eligible; exact causal prefix; active open branch; legal operation;
all referenced IDs allocated and visible; no PROBE/hidden/future ancestor;
target schema contains only operation enum plus typed public-domain values;
no free-form hypothesis, rationale, agenda, summary, answer, or dream prose in
the loss-bearing target; canonical root union nonempty; status COMMITTED.
```

Loss-bearing DECIDE targets may contain only the operation enum, harness IDs,
registered public relation/pass/action IDs, fixed reason enums, and numeric
prediction bins. Free-form QUERY/HYPOTHESIZE/REVISE/DREAM text remains public
input/context and audit evidence but is masked from loss in PPC4. This is a
conservative first assay of operation policy, not private-chain training.

## C3. Executable public schemas

Every THINK request ends with canonical JSON state and the exact ordered fields
`contract, role, goal, logical_clock, budgets, active_branch, open_subgoals,
hypotheses, opened_records, pending_prediction, surprises, last_transition,
repeat_table`. The response is one JSON object:

```json
{"contract":"ppc4.op.v1","op":"ENUM","args":{}}
```

`op` is one of the eleven PPC3 operations. `args` has an exact per-op schema:
OPEN_SUBGOAL `{parent_id}`; QUERY_LEDGER `{query_type,subject_id,relation_id}`;
FOLLOW `{record_id}`; HYPOTHESIZE `{record_ids}`; PREDICT
`{direction,value_bin,action_id}`; ACT `{action_id}`; REVISE
`{hypothesis_id,record_ids}`; BACKTRACK `{}`; REQUEST_DREAM
`{reason,record_ids}`; DEFER `{reason}`; STOP `{reason}`. Additional or missing
fields fail parse. IDs obey PPC3 B1. Free text is not an operation argument.

The complete repeat table and two most recent normalized error codes are
rendered on every later call. Input schema version, output schema version,
parser version, tokenizer, prompt bytes, and canonical serializer hashes must
match; mismatch is INVALID_CELL before dispatch. Unit oracles must explicitly
accept valid diamonds and reject directed cycles.

## C4. Prospective decisive pathways and bypass gates

Every PCFL mechanism target is generated with one presealed minimal decisive
local-atom path and no oracle-valid alternative of equal or smaller budget.
The path ID, bridge edge, binding twin, null return, and expected action swap are
fixed before model work and hidden from cognition. Scientific path-use requires
all of:

1. the authentic run opens/cites every local edge in order before ACT;
2. the registered bridge cut, binding twin, and null memory each change the
   predeclared action/value direction within the same target family;
3. PATH beats SHUFFLE, ONE_SHOT_QUERY, OPEN_LOOP, ENDPOINT, DIRECT_QA_LORA,
   SAME_LIFETIME_BATCH_POSTTRAIN, REFLECTION_LESSON_TEXT, STANDARD_AGENT,
   TARGET_STATE_ONLY, FULL_CONTEXT, and RAW_RAG under their exact gates;
4. the actual cited path equals the presealed path; post-hoc chosen paths do not
   receive credit.

EXPLICIT_GRAPH and LINKED_TEXT are substrate competitors. If either matches or
wins, connected-pathway evidence may remain but no LoRA-specific superiority is
claimed and the winning substrate advances.

## C5. Matched-policy substrate assay and exact READ bytes

Memory substrate comparisons use one frozen policy adapter trained from the
identical DECIDE+ACT row manifest and mounted identically for every substrate.
Only the READ provider varies among TEXT_READ, GRAPH_READ, and READER_LORA.
A separate base-policy transport assay mounts no policy adapter and measures
typed read fidelity only.

Every provider receives exactly:

```json
{"contract":"ppc4.read.v1","query_type":"RELATION","subject_id":"ev-00000000","relation_id":"public_relation_id","candidate_domain_hash":"64hex","max_returns":1}
```

and returns exactly:

```json
{"contract":"ppc4.read.v1","status":"FOUND|NOT_FOUND","record_id":"rec-00000000|null","subject_id":"ev-00000000|null","relation_id":"public_relation_id|null","object_id":"ev-00000000|null","root_union_hash":"64hex|null"}
```

No rank, score, raw index key, condition, path, latency, or provider name is
returned. Candidate-domain bytes/order and request/response tokenization are
identical. READER_LORA is mounted only inside the isolated provider process;
the policy thinker receives the same response bytes under identical weights.

## C6. Component dose estimand

The READ/DECIDE/ACT diagnostic trains three separately addressable component
adapters from fixed family manifests, each with the same positive loss-bearing
target-token count `D`, optimizer/update schedule, rank slice, and source-root
allocation. The 2x2x2 cells mount additive combinations of these frozen
components; disabled slices are present as zero tensors so active bytes and
module shapes match. The `000` cell is the no-gradient reference. This
identifies inference-time presence and interactions among matched-dose learned
components, not decomposition of the jointly trained PATH adapter.

The production-like PATH adapter is separately trained jointly at total dose
`3D`; matched bundled controls also receive `3D` positive tokens. No synthetic,
unsupported, or loss-masked row counts as positive exposure. Claims must say
either component-adapter effect or joint PATH package; they cannot cross.

## C7. Explicit DREAM schema formation

PCFL-Schema requires a typed provisional DREAM commitment before the first
confirmation item:

```json
{"contract":"ppc4.schema.v1","schema_id":"hy-00000000","variables":["x","y"],"relation_template":"registered_public_template_id","support_record_ids":["rec-00000000"],"predicted_observation":"registered_public_outcome_id"}
```

The schema is provisional, public, time-stamped, and writer-ineligible at
commit. It must predict at least two later, independently rooted acquisition
outcomes and encounter zero registered contradictions before SLEEP eligibility.
Confirmations were not present in the DREAM prefix; target combinations and
hidden schema truth remain sealed. Root-family union prevents restatements from
counting as confirmations. SLEEP trains the confirmed typed schema record only
after this boundary.

Required controls: no-DREAM schema arm; temporally shuffled commitment after
confirmation; root-shuffled schema; local-atoms-only memory; matched explicit
graph/text schema; adapter off; and decisive schema/binding cuts. A base model
that infers the schema at probe time without using the committed record is a
valid bypass and prevents a learned-schema claim.

## C8. Linked mediation lineage

Before an epistemic choice, randomization assigns one immutable
`mediation_id` and memory intervention. That ID is carried through the exact
public action, new observation root, writer admission record, training row,
published adapter manifest, later READ/path trace, and later PROBE action. No
stagewise average may be joined after the fact.

The four interventions remain separately randomized/matched: prior memory
correct vs wrong/null; observation included vs equal-row/equal-token sham;
later path intact vs presealed cut; adapter mounted vs unmounted. Full-flywheel
credit requires the complete same-lineage chain in at least three successive
cycles and the preregistered joint estimator across independent lives.

## C9. Static sealing, side channels, and status semantics

The two no-model sealers check only exact static quantities: counts, hashes,
byte identities, role assignments, partitions, split disjointness, twin/cut/
shuffle relations, candidate domains, shortcut classifiers, and deterministic
scripted-oracle closures. They make no standard-agent or behavioral ceiling
claim. Behavioral ceilings require the later model-run manifest.

Logical budgets, fixed-shape normalized errors, and cold-process policy remove
model-visible operational differences. Paired fault fixtures perturb cache,
latency, batching, provider/error timing, and filesystem/process paths while
holding model-visible bytes and selection fixed. Every run reports missingness
by condition. Differential missingness above the later registered threshold
invalidates comparative estimation; it is never imputed into a favorable score.

Reporting states are disjoint:

```text
CONSTRUCTION_FAIL  instrument/contract never became scientifically runnable
RUN_INVALID        executed bytes violated integrity or authority
MISSING            authorized cell absent under registered missingness rules
VALID_NULL         valid execution, effect threshold not met
VALID_ADVERSE      valid execution, treatment worse than comparator
VALID_POSITIVE     valid execution, every conjunctive gate passed
```

Audit failure cannot be called scientific falsification. A valid null/adverse
result is immutable evidence and cannot be erased by redesign.

## C10. Prospective numeric rules

Confirmatory inference uses independent lives, paired within sealed life/root
blocks where applicable. Familywise alpha is 0.05 with Holm correction across
co-primary contrasts; all effects report simultaneous 95% intervals and raw
life-level values. A positive mechanism contrast requires both adjusted lower
confidence bound above zero and paired standardized effect at least 0.35. Power
simulation must be at least 0.80 for that threshold under the frozen pilot
variance source; otherwise the run is explicitly a pilot.

Pathway success requires every C4 conjunct, not an aggregate. Full-flywheel
success requires every C8 link and at least three successive cycles. Baseline
saturation requires the upper simultaneous interval for normalized improvement
slope to be <=0.002 per checkpoint for two successive intervals, while the
treatment lower interval exceeds 0.002. Schema compression additionally
requires held-out schema/action utility to pass the 0.35 rule, adapter bytes to
remain fixed, sufficient-statistic information to increase, episodic-detail
reconstruction not to increase beyond its predeclared equivalence margin, and
matched text/graph/shuffle gates to pass. Exact life count and maximum extension
are set from untouched pilot variance before confirmatory targets are sealed.

## C11. Distinct execution gates

The proposal registry must separately name future behavioral tests for READ
fidelity, component effects, policy-matched substrate comparison, recurrence,
adaptive retrieval, authentic path use/cuts, bypass ceilings, stream capacity,
schema formation/compression, full mediation, saturation, operational
missingness, and postrun status/claim mapping. Preflight can test only contract
construction and scripted sensitivity. No omnibus postrun audit creates an
estimand retroactively.

## C12. Current authority

Unchanged: present ratification may authorize isolated contracts, deterministic
CPU/no-model fixtures, and exactly two no-model sealers only. It does not
authorize parenting, model calls, canaries, LoRA, behavioral execution, GPU
work, or claims. A later exact model/run manifest, fresh review, and explicit
human ratification are mandatory.


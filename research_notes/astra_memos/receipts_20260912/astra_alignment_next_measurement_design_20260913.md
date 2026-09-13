# After SEQ160: minimal fresh-development measurement proposal

September 13, 2026. **Design only; Main selects the protocol.** No code, source,
scorer, native state or SEQ160 evidence is changed. No fit or automatic training
use of raw child content is proposed. This is not a permissive rescue of SEQ160.

## Decision and evidential basis

Recommend **explicit task/output instructions plus a narrow, predeclared
field-level evaluator**, not an unrestricted semantic judge. Separate task
binding, serialization and actual-experience recording. Remove lexical
restatement success from any feasibility conjunction; preserve the restatement
verbatim as an intervention intermediate, not a certified explanation.

The frozen audit found all nine cells at 0/16 on PROCESS_USE,
RECORD_FAITHFUL and FULL_MATERIAL. All144 public notes failed normalization;
that does not establish144 wrong public bindings. A seed2 ALIGNED C note
visibly included the correct latest receipt ID/action/outcome plus rejected
metadata. Conversely, P examples omitted relation, records omitted source or
address, and some own-event relations were wrong or Boolean. A schema-only
explanation of every failure is therefore also unsupported. Source processing
and serialization need separately observable outcomes on **new instances**.

## The two choices

| Choice | What becomes identifiable | Principal risk | Recommendation |
|---|---|---|---|
| A. Explicit, arm-uniform serialization and task contract | Required public bindings and own-event fidelity at known output paths; distinguish missing fields, wrong values and wrong format | Naming prior/outcome/relation and requesting the latest event cues or directly teaches the operations; ALIGNED may become redundant | Adopt for a small DEV measurement diagnostic; qualify treatment effects accordingly |
| B. Broad semantic scoring of freely structured notes | Potentially useful information expressed outside a narrow schema | Extracting from nested receipts, prose, aliases or multiple candidates needs policy choices; a judge can perform the missing selection/comparison on the child's behalf | Do not adopt as the next primary assay. It needs its own prospectively frozen rules and adversarial examples, not post-outcome judgment |

For B, even a prospective scorer must distinguish **explicitly selected latest
receipt** from copying both receipts, and **explicit comparison** from merely
listing two values. Searching all nested text for a correct answer can credit
a non-answer. Human/semantic assessment, if later chosen, must be separately
versioned, blinded to arm, permit ambiguous/unassessable labels, and never
replace the frozen SEQ160 score. No such rescore is proposed here.

## Smallest recommended cohort: eight tasks × three arms × three roots

- Reuse the same three original pre-memory perception adapters and frozen base,
  CPU world and explicit adapter routes. They are exposed DEV roots, not clean
  confirmation subjects. Zero new adapters, fits, updates or parent-model calls.
- **8 new tasks per arm:4P +4C.** P covers each Boolean prior/outcome combination
  once. C covers latest receipt first/last in display × latest outcome true/false
  once; use different actions and opposite outcomes across its two receipts so
  wrong receipt selection is observable. All observations come from the frozen
  CPU world, with candidate selection completed before any model response.
- Same exact8 task bytes/order across all arms and learner seeds. Four blocks
  of2 tasks, family order P-C-C-P in every root; each family has fresh instances
  in both halves. Do not infer learning from half comparisons or infer order
  effects. This deliberately removes the previous order-by-learner assignment;
  family/block position is still not independently randomized.
- **ALIGNED, SWAPPED, ACTIVE_NEUTRAL**, each with one fixed contact and one child
  restatement call before each block. Reuse the frozen P/C lesson strings:
  ALIGNED gets P-C-C-P; SWAPPED C-P-P-C, hence identical lesson multisets.
  Neutral contact, exact text: “Continue with the next scheduled tasks using
  their instructions. Briefly acknowledge this message before proceeding.”
  Use the same restatement request, context insertion and call ceilings in all
  arms; insert only the current raw restatement into each task-local context.
- Each arm has16 possible task calls +4 restatement calls =20; **60/seed,
  180 total maximum**. Invalid action means no dispatch/record call; retain its
  task slot. No replacement tasks, retries, successful-root selection or dose
  escalation. Separate fresh inference state per arm, no cross-task history
  except the block's current restatement; match start adapters and generation
  settings, not generated trajectories or realized token totals.
- ACTIVE_NEUTRAL is the contact/restatement-opportunity control, **not** an
  exactly token-matched control. Report contact, restatement, task and record
  tokens separately. ALIGNED−SWAPPED measures lesson relevance versus the
  other process lesson; ALIGNED−NEUTRAL distinguishes benefit from SWAPPED
  interference. If A≈N>S, do not call it positive coaching benefit.
- Omit bare NO_PARENT to keep the diagnostic minimal. Neutral supplies ordinary
  instructions with matched interaction opportunities, not a no-contact
  baseline. SEQ160's historical NO_PARENT must not substitute for a fresh arm.
  If Main specifically needs the no-contact contrast, add8 tasks/root without
  restatements:48 extra calls,228 maximum; that is a different selected design.

Eight tasks gives only4 observations/family/root, the minimum for these
structural balances, not a powered efficacy or transfer test. Do not carry
forward SEQ160's16-task thresholds or halve them mechanically.

## Explicit observable contract and necessary operations

Freeze literal instructions and typed templates before execution. The following
is a proposed contract, not final native prompt bytes. Display the same
family-specific contract to every arm; use type placeholders, not worked task
answers, evaluator labels, hidden rules or a sample solved receipt.

**Wake outer object:** `{"note": OBJECT, "prediction": BOOLEAN,
"action": {"kind": "TRY", "values": [INTEGER, INTEGER, INTEGER]}}`.
Fresh prediction must be Boolean even when earlier public C receipts have null
predictions. Retain the existing action bounds and one-dispatch rule.

- **P note:** `{"predicted": BOOLEAN, "observed": BOOLEAN,
  "relation": "matched" | "mismatched"}`. Instruction: “For the public receipt,
  report its prediction as stated before that action, its returned observation,
  and whether those values match. These are not your new action's prediction
  or outcome.” Required operations: preserve earlier prediction, locate actual
  public observation, compare without replacing either. The ordinary task
  explicitly requests these operations; this is not discovery from coaching.
- **C note:** `{"receipt_id": STRING, "try": [INTEGER, INTEGER, INTEGER],
  "observed": BOOLEAN}`. Instruction: “Select the executed public receipt with
  greatest time, not the last receipt displayed. Report that receipt's ID,
  action and observation together.” Required operations: select by chronology,
  bind all three fields to the same receipt; dumping both receipts is not a
  selected answer. This instruction itself teaches the selection criterion.

**Post-outcome record outer object:** `{"address": STRING, "source": OBJECT,
"event": {"receipt_id": STRING, "try": [INTEGER, INTEGER, INTEGER],
"predicted": BOOLEAN, "observed": BOOLEAN,
"relation": "matched" | "mismatched"}}`.
`source` has the task's P/C note schema and denotes the earlier public evidence;
`event` denotes only the child's actual new dispatch and returned receipt.
`address` is the supplied task address. Explicitly say that source is not an
origin prose string, and event is not the source receipt. Public and new receipt
IDs remain distinct even when the chosen action or outcome coincides. Compare
source against original public evidence, not against an erroneous wake note;
compare event against the actual new execution, not a teacher-written record.

New-record relation and source comparison remain child outputs. Do not insert
the correct relation into a template or have the evaluator's answer emitted
by a wrapper. Capture exact raw continuations before all evaluation.

## Prospective scoring: exact paths, independent columns, no lexical gate

1. Decode one unfenced JSON object; reject duplicate keys, nonfinite values,
   ambiguous multiple objects and type coercion. Whitespace/key order do not
   alter content; raw canonical serialization is a separate observation.
2. Evaluate each required field **only at its declared path** (`note.*`,
   `source.*`, `event.*`, `address`). No recursive search, flattening, aliases,
   prose interpretation, best-candidate choice or conversion of Boolean
   relation to a string. This is direct typed equality, not broad semantics.
3. Separate JSON-decode status, schema completeness/extra keys, field presence,
   type validity, and exact required-field correctness. A missing field is not
   silently filled. A decode failure is unassessable at field level and fails
   success on the full denominator, rather than being described as a wrong
   factual value. Score other accessible fields independently when one is
   missing or mistyped. If extra metadata accompanies all correct required
   values, report content success **and** a separate schema violation; freeze
   this distinction prospectively, not after results. No extras may create
   alternate action paths or relax the original strict dispatch checks.
4. Public-processing endpoint: all required P/C wake-note bindings correct with
   normal completion. Report P preservation/comparison and C selection/same-
   receipt binding separately, always /4 family or /8 all tasks. Do not AND this
   endpoint with lexical RESTATE, new-action success or record serialization.
5. Separately report strict dispatch /8, record-source correctness /8, each
   own-event field /8, and complete source+address+own-event content /8. Also
   show called-record denominators, never substitute them for /8. Schema-
   compliant full records are a further joint endpoint, not a substitute for
   the separately measured content. Uncalled records remain failed slots.
6. Preserve delivered lessons, raw restatements, insertion identities and
   token costs. Restatement delivery/completion is observable; a lexical
   checklist may be descriptive but cannot veto application performance.
   No semantic restatement proof, mediation estimate or selection of “good”
   restatements is inferred. All task/field masks and both paired contrasts
   remain labeled by learner; the three roots are the replication units.

Pre-run CPU fixtures should include correct fields with extra time metadata,
missing relation, wrong relation with correct prior/outcome, nested copied
receipts without a selected C answer, source/new-receipt swaps, null fresh
prediction, malformed/duplicate JSON, noncanonical valid JSON, and invalid
action with an uncalled record. Pin expected content/schema labels separately.
These are proposed acceptance checks, not tests executed by this design sidecar.

## Freshness, stopping and interpretation

Freeze a new named DEV namespace and complete8-task roster/source-world receipt
manifest before generation; reject overlapping task IDs, public receipt IDs
and complete task fingerprints against the supplied prior inventory. Change
source instances, not just IDs. Reserve a separately generated CONF namespace
and seeds without inspecting its cases during curriculum/scorer development;
no CONF call in this assay. Namespace disjointness does not establish absence
of all training exposure. No old held IDs, answer bytes or raw successful child
outputs enter new training or task construction.

One bounded cohort only: proposed ceiling1800 controller seconds +180 collection
seconds/root, same as the prior lifecycle pattern but a new declared cap, not
a runtime guarantee. Stop at its task or wall-time ceiling; report incomplete
cells as incomplete, never denominator-shrink or retry them. This proposal
authorizes no native work. Main owns lifecycle details and any execution.

**What remains unidentified:** even a consistent A>N and A>S would establish
only incremental relevance of a fixed lesson/current-restatement package under
explicit task instructions in these exposed DEV roots. It would not identify
adaptive parenting, transfer from parental advice alone, restatement mediation,
persistence, spontaneous process discovery, action-grammar internalization or
H1/H2. Ordinary instructions deliberately teach/activate the same operations;
ceiling performance in all arms cannot refute parenting, and zero contrasts
cannot distinguish redundancy from lack of receptivity. A further factorial
instruction-information manipulation would be needed to isolate that source
of instruction, and is **not** included in this minimal assay.

This is consequently a **measurement-development branch**, not the decisive
parenting experiment. If Main's immediate requirement is attribution to parent
advice rather than reliable observability under explicit instructions, this
minimal next assay is insufficient and should not be represented otherwise.
No automatic pass/promotion, sleep material adoption, guardian framework or
formal C11 expansion follows from the design.

## Frozen evidence used (read only)

- `/tmp/astra_parenting_alignment_analysis_result_20260913_attempt1/analysis.json`
  SHA256 `ee2e60a502a2884c2ed20701612ed05f6e04a718eff8c6775d543ac1df4b2b10`.
- `/tmp/astra_parenting_alignment_analysis_result_20260913_attempt1/raw_schema_audit.json`
  SHA256 `8d1c27f688b0512c69a0418a888d78f27030fc252ef64e80e7979fc5bc0a66a2`.
- `/tmp/astra_parenting_alignment_analysis_execution_20260913_attempt1.md`
  SHA256 `7ee46cd5525e41907e96e09d391be77adc7acf38ec13246861c5a0563ae9c03a`.
- Frozen alignment protocol SHA256
  `5c53d6aa850b3a3a409c255ab9b28ce3b090f7325f35688437e42a86b1cccce5`;
  pre-reveal schema caveat SHA256
  `878af7a5af789d2b66ee385945ce26d5b437cd9f531f4bde06cffd1d157e6d46`.
- Main reports completed SEQ160 archive commit937ecd69; no Git inspection or
  amendment was performed here. This document is the sole new file.

EDITSTOP

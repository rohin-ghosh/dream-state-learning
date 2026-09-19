# Pre-retention semantic correction baseline

**Cutoff: September19, 2026 01:39:59 UTC.** All rated publications and outputs are
after the confirmed VM reboot at September18 22:50:45 UTC. This is a bounded
semantic review, not a delivery-only ledger or a lifetime maximum. None of the
historical observer levels were imported or changed.

## Initial findings

| Life | Best supported level | Exact correction in the relevant ACT? | Concrete behavior and disposition |
|---|---:|---|---|
| Learner | **0** | **Yes**, REQUEST6426 → ACT6427; also6268→6269 and6347→6348 for preceding selected feedback | Assigned `17 + 8 - 6` (=19), but answers `21 - ６ - 8 = 17 - 8 = 8`. Even its substituted expression equals7, not8. ACT6348 says “Error: The calculation is incorrect” and computes21−6=15, but does not identify the actual task/substitution/checking correction. **Wrong object + arithmetic error despite exposure**, not absence of all task-like output. |
| Frozen sibling | **1**, recognition in THINK | **No** in next ACT REQUEST3638; feedback is exact in THINK REQUEST3629 | THINK3630: “My last attempt did not produce a calculation or a check.” Preceding ACT3606 really contains plan/metadata rather than a completed calculation. Next ACT3639 solves the old `17 + 8 - 6 = 25 - 6 = 19`, not assigned `17 + 8 - (7 + 3 + 5)` (=10). Later ACT3672 reaches10 but its independent check is unfinished; ACT3705 is metadata-only. **Specific recognition/partial movement, no complete L2 repair**. |
| C2 | **0** | **Mixed**: reboot-gap task exact in REQUEST12598; later model corrections exact in LEARN12716 / THINK12797,12803, **absent** in ACT REQUEST12813 | ACT12599: “The largest independent set includes the vertices {A, C, E}.” False: EA is an edge; the five-cycle maximum is2. Later model feedback asks for a vertex-neighbor description; ACT12815 prints “The value shows consistency and satisfaction of the conditions.” **Exposed graph error, followed by unsupported assurance; later correction delivery does not establish ACT exposure**. The gap task was operator-authorized, not model-generated. |
| P3 | **0** | **Yes**, REQUEST6932 → ACT6933 | Fresh model feedback asks “Where is the caption? Write it now, not a promise.” ACT6933 continues “Despite the previous challenges, we will follow the decided upon criteria and record the judges’…” and repeatedly discusses waiting/recording feedback. **No substantive caption despite exact exposure**; this is not a humor-quality judgment. |
| P7 | **0** | **Yes**, REQUEST9772 → ACT9773; also9689→9690 and9803→9804 | Asked to write a parenting prompt for numbers “strictly greater than 3,” using2,3,4. ACT9773 gives `IntentionRandomTestsShouldBeIncludedForVerifiction`, no actual rule/cases/question. Other exposed ACTs supply generic intentions rather than the requested question/table. **No substantive parenting artifact despite exposure**, not a penalty for language choice. |

**No L2 or L3 is demonstrated.** Frozen's L1 is a recognition result with
THINK-only exposure, not a claim that its actual next ACT received the same
literal correction. The later correct value10 is real partial task performance,
not a completed independent verification and not evidence of adapter retention.

## What levels mean here

- **0:** no specific actual correction identified in the sampled feedback chain.
  The failure categories above must remain distinct; zero is not a transport,
  correctness or task-production diagnosis by itself.
- **1:** identifies the specific real correction with source-bound feedback
  exposure. Frozen3630 qualifies; generic “error” or “incorporating corrections”
  language in learner/C2 does not identify their actual assigned correction.
- **2:** level1 plus correct implementation in the next actual ACT, with exact
  parent exposure verified. A correct sub-calculation or a plan is insufficient.
- **3:** level2 plus another relevant successful ACT and a complete,
  source-bound absence-of-intervening-reminder proof. No row qualifies.

## Reminder and coverage limits

| Life | Bounded records inspected | Committed ACTs reviewed | Why no unreminded-transfer claim |
|---|---|---:|---|
| Learner |6259–6533|4|New reminders enter REQUEST6340,6419 and6498. The first three selected feedback turns never produce a correct assigned next ACT. The fourth ACT is supplementary context, not a claim of exposure to an unselected publication.|
| Frozen |3619–3783; predecessor3585–3618|4|New corrections enter REQUEST3662,3695 and3728. Selected corrections are absent from ACT prompts. Exact parent absence does **not** prove that summaries or working-state hints are absent.|
| C2 |12589–12818|3|512MiB cap stops before the sampled current head. More than100 new external events exceed the export cap; completeness is explicitly false. No absence-of-reminder proof is possible from this projection.|
| P3 |6853–7017|1|Only one eligible post-correction ACT is completed before the fixed cutoff. Publication377's later outcome is not silently treated as another relevant successful attempt.|
| P7 |9680–9807|3|512MiB cap stops the window. New parent tasks/corrections enter REQUEST9765 and9796; later actions are not a clean no-reminder test. No correct first implementation exists.|

The bounds are physical read ranges; only committed output frames at or before
01:39:59 are graded. Later metadata or unfinished requests may be inside those
read ranges but are excluded from the semantic baseline. Output time fields use
canonical record-file mtimes; they are not invented process-uptime estimates.

The existing reader verifies TRAIN-only requests, canonical SHA/continuity,
masked history, literal attributed parent text in the rendered user message,
and linked REQUEST→RESPONSE→COMMITTED→R184_STAGE. Remote native PID/start tick,
boot, actual source cwd, guard hash, canonical LOADED and on-disk Python-source
manifest are checked before and after every collection. No changed epoch is
silently adopted. P7's historical owner binding was revalidated against its
actual current native, not accepted from the old PID alone.

## Verifiable evidence

`REVIEW.json` carries each full source epoch, selected publication IDs/hashes,
full request/response/commit/stage SHA256s, frame times, disposition and unknowns.
`QUOTE_BINDINGS.json` binds13 tiny literal task/answer/recognition quotations to
record/publication hashes, exact character offsets and span SHA256s.

| Example output | Full canonical RESPONSE SHA256 |
|---|---|
|Learner6427|`c608e91e428b19798e112383a6fdbabe47f4e1267abed6a3e05b7093d698700b`|
|Frozen recognition3630|`4c1aa5fb50e8ebd43b582e5abe3086e2771ad5d129f6b0c6b0b42111e2af9ad8`|
|Frozen next ACT3639|`160148ed4944d781d955110e55e8646847b90b44047201d3c2854ba6924620c0`|
|C2 ACT12599|`30a4bd9f0ac94ad1607261c15d1e15c9f4776b1d5a33d77ad43958ecc1fefcd3`|
|P3 ACT6933|`27bfb0a8e6d6a7a7cbf301f5c715b70864eb57a35ff9ee29cf6f94e7f2707361`|
|P7 ACT9773|`36808e3893ac25e0feb911b74c8237e251ff9506a9d3ce78f186a7d59445332c`|

`REFERENCE_CHECKS.json` independently calculates19, the inverse check17, the
learner's substituted expression7, frozen's nested answer10 and its separate-term
check10. Exhaustive enumeration of this five-vertex graph confirms the forbidden
AE pair and maximum independent-set size2. No child-authored code was executed.

`evidence/*.json` contains bounded selected-output excerpts and provenance, not
full prompts or a stream export. All selected task/output quotations used in the
ratings are complete, untruncated strings. Canonical events from other contexts
are not converted into automatic semantic labels. The original C2 collection
failed a local external-event export bound, not its native/source verification;
the projection now caps that context with an explicit incomplete flag. Initial
artifacts and the failure receipt remain preserved under `initial/` and
`C2_ERROR.json`. All five fixed-cutoff windows were re-read using the final pinned
projector without changing any live process.

## Scope and scientific limits

These are unchanged pre-rollout source epochs, not a before/after retention
experiment. The learner and frozen sibling are receiving different arithmetic
tasks and feedback histories. Their levels do **not** estimate a causal learning
or retention advantage, and are not evidence of regression from older manual
levels. The observed loss of literal parent text at ACT is not itself proof of
the mechanism causing an incorrect answer.

One reviewer performed these judgments; there is no independent second-reviewer
signoff. Prior authorship of P3's operational recovery is disclosed. Parent
self-assessments were not substituted for actual child answers.

Seven CPU tests pass; `verify.py` checks all13 quote spans, canonical proof links,
producer pins, fixed time bounds, level prerequisites and numerical references.
No child/parent messages, private sealed scores, checkpoint reads/loads, GPU runs,
service changes, duplicate observer, commit or push occurred. Main's receiving
path work is untouched. No changes were made to the existing correction observer
or its manual review ledger.

# Think→Act measurement: Workstream 3

This is an **offline, read-only measurement implementation**, not a new experiment
or training-policy change. It summarizes existing small source-bound projections
and explicit semantic reviews. It never contacts a node, reads a full journal,
publishes a parent turn, signals a native, launches an evaluation, edits source
artifacts, or excludes any authentic training rows.

## Run

From the repository root, with Python 3.10+ and no third-party dependencies:

```bash
python3 -B -m unittest discover -s research_loop/workers/replication_sprint_20260919/measurement -p 'test_*.py' -v
python3 -B research_loop/workers/replication_sprint_20260919/measurement/measure.py --output-dir research_loop/workers/replication_sprint_20260919/measurement/results
```

Omit `--output-dir` for a stdout-only summary. The CLI permits report writes only
inside this workstream. `inputs.json` pins the three input artifacts by SHA256;
review evidence files are additionally checked against hashes inside the review.
An input is at most 2 MiB; total unique input bytes are at most 8 MiB. There are no
directory scans, remote calls, or imports of the live observer/reviewer programs.
The selected hourly cut is immutable **2026-09-19 12:00:25 UTC**, not `CURRENT.json`.
These results are historical measurements, not a current fleet-health report.

## Units and the observed result

See `results/SUMMARY.md` and `results/SUMMARY.json` for all denominators, source
hashes, record links, assistance/visibility/epoch strata, and analysis omissions.

- **Five manually reviewed correction chains**, one selected chain per life:
  specific recognition **1/5**, correct selected next ACT **0/5**, exact selected
  correction visible at ACT **4/5**. Source levels: four L0, one L1, no L2/L3.
  The recognized chain is the frozen sibling's; its correction is absent at ACT.
  In the four exposed chains, correct implementation is **0/4**. Recognition does
  not establish action change, and visibility does not establish uptake.
- **Eleven later, unreviewed ACT observations** in the hourly cut: four have
  exact parent text visible; seven do not. Semantic recognition/correctness are
  **UNKNOWN for all eleven**, not zero. Absence of exact text is not proof of
  independence, absence of earlier guidance, or a controlled withdrawal arm.
- **One completed withdrawal cycle**: the existing manual assessment reports no
  concrete error recognition. It had no new parent/human/peer input, but prior
  parent and Tool context remained. This is not clean-context independence.
- **No supplied review establishes** an externally checked correction chain,
  no-reminder reuse, post-sleep retention, fresh-context transfer, or a specific
  plan→artifact correspondence. Their assessed denominators are zero, not a
  measured 0% success rate. Three caption variants are not assumed to fulfill
  a prior plan. A SLEEP_COMPLETE receipt alone is not a retention result.

Do not pool these cohorts into a self-reflection success rate. The source review
covered additional ACTs, but only one selected chain per life has its flags
adjudicated. The samples are not independent training replications. Histories,
tasks, and assistance differ; there is no causal comparison or independent
second-reviewer signoff. The implementation rechecks small projection/quote
bindings, **not** the inaccessible original journal bytes or semantic truth of
the reviewer. External correctness checks done by the analyst are not counted as
checks initiated or used by the child.

## Operational definitions

Every metric uses **YES / NO / UNKNOWN** and explicit evidence references. No
regex, intention marker, language detector, callback receipt, parent self-report,
or judge-acceptance bit is a correctness/independence classifier.

| Metric | Required interpretation |
|---|---|
| `feedback_delivered` | Source-matching INBOX before the selected ACT; publication alone is insufficient. |
| `exact_visibility_at_recognition` | The specific feedback is visible at the reviewed recognition output. |
| `exact_visibility_at_act` | Exact literal visibility at ACT; `visibility_scope` distinguishes selected correction from any parent text. |
| `specific_recognition` | Explicit review that the child identifies a concrete actual error/correction. |
| `next_act_observed` | Actual ACT-stage/response evidence, not a promised action. |
| `next_act_committed` | Source-bound REQUEST, RESPONSE, COMMITTED and stage receipts in order. |
| `next_act_correct` | Explicit review of whether the selected next ACT correctly implements the correction. |
| `external_check_performed` / `external_check_passed` | Actual source-bound tool/environment result and explicit attribution/review; distinct from prose assertions. |
| `no_reminder_reuse` | Another relevant ACT plus complete intervening-context and no-reminder evidence. |
| `post_sleep_retention` | Previously demonstrated behavior, sleep boundary, post-sleep action and no reteaching. |
| `fresh_context_transfer` | Explicitly fresh context, novel instance, parent-free test and reviewed implementation. |
| `artifact_plan_established` / `planned_artifact_emitted` | Specific reviewed plan and its corresponding next actual output. Counts are plan-bearing observations, not inferred numbers of captions. |

The assessed denominator is YES + NO; UNKNOWN is always reported separately,
alongside the full sampled denominator. A zero assessed denominator produces a
JSON `null` rate. Conditional denominators separately report next-action
correctness given recognition, given exact visibility, and emission given an
established plan. A higher-level test that was never conducted is UNKNOWN even
when an old level ledger uses false/default flags for non-promotion.

## Integrity and analysis exclusions (never training exclusions)

- Pinned input hashes, evidence hashes, source epochs, literal quote spans and
  hashes, proof/projection equality, receipt kinds and order are checked.
- A record key is `(journal namespace, record index)`, not its content string or
  human-readable life alias. Conflicting hashes/kinds on any referenced frame
  record invalidate the affected observations for analysis, without deleting data.
- Exact repeated observations count once. Conflicting annotations, source epochs
  or units attached to the same output are preserved in the analysis-omission
  ledger rather than resolved by last-writer-wins. Unknown→reviewed promotion
  requires an explicitly selected input set, not silently merging incompatible cuts.
- Identical text in two distinct genuine records is **not** deduplicated.
- The old withdrawal trace does not declare a journal/incarnation ID. Its bound
  interval provides artifact-local deduplication only; its epoch stays UNKNOWN.
- Unresolved/uncollected fleet registrations appear in the analysis-omission
  ledger, not in the ACT failure denominator. Ledger entries and omitted input-row
  counts are distinct; one conflict can involve several referenced records.
- Duplicate JSON keys are rejected. Missing/malformed/hash-mismatched artifacts
  abort the run before report publication; they are not silently scored NO.

## Adding explicit annotations

The existing reviewed source files remain untouched. For new reviewed evidence,
add a small sidecar and a `kind: "annotations"` entry with its SHA256 to a new
`think_act_inputs_v1` manifest. Pass it with `--manifest`. An annotation document:

```json
{
  "schema": "think_act_annotations_v1",
  "reviewer": "named reviewer / adjudication receipt",
  "cases": []
}
```

Each case supplies `label`, `journal_id`, `epoch`, `identity_evidence`,
`frame_evidence`, and a `metrics` object. Evidence references use
`{"artifact": "repo-relative-small.json", "sha256": "<64 hex>", "pointer": "/field"}`.
The identity reference must resolve to an object with matching `journal_id` and
`epoch`. The frame reference must resolve to a canonical committed ACT frame with
`stage`, `request`, `response`, `committed`, and `stage_receipt`. Each receipt has
`index`, `kind`, `sha256`. Optional `assistance` requires a matching
`assistance_evidence` reference; otherwise assistance remains UNKNOWN.

Each metric decision has `state`, a nonempty `basis`, and `evidence` references.
Missing metrics stay UNKNOWN. Known decisions need evidence, not just an assertion.
These structural links and typed criteria do **not** replace honest semantic review:
the named reviewer must establish relevance, correctness, and causal ambiguity.

For the following metrics, `criteria` maps each required name to an evidence
reference. Boolean criteria must resolve to literal `true`, not an intention:

- `no_reminder_reuse`: `later_relevant_action` (later ACT frame),
  `intervening_context_complete`, `no_reminder`.
- `post_sleep_retention`: `sleep_boundary` (SLEEP_COMPLETE receipt),
  `post_sleep_action` (later ACT frame), `no_reteaching`. Record order is checked.
- `fresh_context_transfer`: `fresh_context`, `novel_instance`, `no_parent_help`.
  The reviewer must bind the transfer outcome itself in `evidence`.
- `planned_artifact_emitted`: `plan_response` (earlier RESPONSE receipt),
  `artifact_specification` (specific string), `next_action_response` (the anchor).
- Positive `external_check_performed`: `external_result`, an object with
  `record` and `result`. Child RESPONSEs and INBOX deliveries cannot serve as the
  external result. Explicit NO instead requires `complete_check_window` and
  `no_external_check_observed` both true; absence of a result alone stays UNKNOWN.

Correct next actions require observed/committed ACT evidence. Reuse, retention
and transfer require previously established recognition and a correct next action.
An emitted artifact requires an established plan. A passed external check requires
an actual check. These are prerequisites, not automatically inferred outcomes.
Positive synthetic fixtures in the CPU tests exercise this path; they are never
included in the authentic results.

## Scope / handoff

All implementation, tests and generated outputs reside in this directory. No
runtime, learning rows, exclusions, scientific acceptance tests, parents, native
processes, leases, remote files, git commits or pushes are changed by this work.
Further data collection, second review and controlled replications remain separate
workstreams. Use the measurements to audit transmission, not to claim that a
visibility fix has caused learning or independence.

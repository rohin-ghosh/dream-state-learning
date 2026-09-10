# Clean-child lineage guard v1 — source-only advisory

Date: 2026-09-10

Status: **source-only systems/provenance advisory**. This document does not
authorize implementation, model/tokenizer execution, data or benchmark
generation, training, adapter/checkpoint work, GPU/resource use, result
evaluation, scientific claims, publication, release, or transfer.

Fresh-review note: the requested fresh covert-flow reviewer could not be
spawned because every collaboration slot was occupied. The attack catalogue
below is therefore a local adversarial pass, not an independent review. A
fresh independent implementation review remains required by `AGENTS.md`
before any scientific run.

## Verdict

The smallest adequate guard is not a new cognitive mechanism. It is three
content-addressed control objects around the existing child:

1. an immutable record for every artifact that can influence a child or
   parent;
2. one atomically promoted clean-lineage head; and
3. a one-way disposable-evaluation receipt whose outputs are monotonically
   tainted and have no transition back to a clean head.

The guard must derive contamination transitively from input records. A caller
may never assert `gym_exposure="none"`. Missing, unknown, inconsistent, or
unreadable provenance means **not clean**.

This directly enforces Rohin's existing rule:

```text
clean child/parent -> disposable final-gym descendant -> quarantined results
                  \___________________________________X no return edge
```

“No return” includes weights, optimizer state, rows, summaries, DREAM/SLEEP
products, outcomes, parent state, rankings, stopping decisions, curriculum or
prompt selection, and hyperparameter choices conditioned on sealed results.

## Scope: enforcement versus new science

### Non-material enforcement of already ratified visibility rules

These items implement the rules already present in Adaptive Parent v5, the
CompilerGym quarantine note, and Rohin's clean-child ruling. They do not add an
arm, cognitive organ, estimand, or claim:

- fail closed on absent or unverifiable provenance;
- compute taint as the monotone union of all ancestors and inputs;
- put final/deployment visits in disposable descendants;
- forbid all descendant-to-clean child and descendant-to-clean parent flows;
- use fresh root-local parent state in parent-present evaluation cells;
- make SLEEP candidate corpus and candidate adapter one transaction;
- quarantine both after rejection, leaving every committed head unchanged;
- bind immutable birth, mechanism, child, parent, corpus, ledger, DREAM state,
  domain/partition, and source hashes;
- validate every read or promotion at the relevant entry point; and
- add mutation/regression tests that prove these denials.

### Scientific choices this guard must expose but must not decide

The following remain material design choices and need the normal deliberation
and exact-ratification path. The guard represents their answers as bound data;
it does not choose them:

- which task families and partitions count as target-blind development,
  development-only task exposure, writer-gate panels, developmental exams,
  and sealed final evaluation;
- whether any **development-only** CompilerGym aggregate may inform a later
  mechanism or hyperparameter choice (sealed-final results are always denied);
- the exact bootstrap source allowlist and proof of family disjointness;
- which preregistered aggregate developmental-exam codes may update the
  parent's notebook under v5;
- release timing for blinded final results and whether every root must finish
  before any human sees them; and
- any change to THINK/DREAM/SLEEP, writer, eligibility, rank, masks, dose, or
  promotion semantics.

If no ratified answer exists for one of these fields, its value is `DENY`, not
an inferred permission.

## The three control objects

All hashes below are lowercase SHA-256 of exact bytes. JSON used as an identity
is canonical JSON (UTF-8, sorted keys, no insignificant whitespace). Paths are
locations only; identity comes from hashes and registry records.

### 1. `artifact_record.json`

Required for every adapter, optimizer state, corpus, ledger segment, working
checkpoint, DREAM product, parent notebook/playbook, teaching file, prompt,
mechanism source bundle, evaluation descriptor, summary, result, ranking, and
selection receipt.

Required fields, with no optional provenance shortcuts:

```json
{
  "schema": "clean-lineage-artifact/v1",
  "artifact_id": "sha256:<canonical-record-body-sha>",
  "kind": "ADAPTER|OPTIMIZER|CORPUS|LEDGER_SEGMENT|WORKING_STATE|DREAM_STATE|PARENT_STATE|TEACHING_INPUT|MECHANISM|EVAL_DESCRIPTOR|EVAL_RESULT|SUMMARY|RANKING|SELECTION_RECEIPT",
  "payload_sha256": "<sha256 of one file or canonical tree manifest>",
  "payload_bytes": 0,
  "producer": {
    "entry_point": "<module:function or command identity>",
    "source_bundle_sha256": "<hash>",
    "invocation_sha256": "<hash of exact normalized argv/config>",
    "run_id": "<immutable id>"
  },
  "input_artifact_ids": ["sha256:..."],
  "evidence_ids": ["<immutable public action/outcome id>"],
  "lineage_id": "<id or NONE>",
  "root_id": "<id or NONE>",
  "domain_exposures": [
    {"domain_id": "<id>", "partition_id": "<id>", "role": "TARGET_BLIND_DEVELOPMENT|DEV_TASK_EXPOSED|WRITER_GATE|DEVELOPMENT_EXAM|SEALED_FINAL"}
  ],
  "information_class": "CLEAN_ELIGIBLE|TASK_EXPOSED_DEV|SEALED_FINAL|QUARANTINED|INVALID",
  "taints": ["<monotone reason code>"],
  "selection_eligible_for": ["<ratified decision scope id>"],
  "parent_text_targeted": false,
  "created_at_utc": "<audit only; never identity>"
}
```

Validation rules:

- `taints` equals, rather than merely contains, the canonical union of every
  input's taints plus locally derived taints.
- `SEALED_FINAL` on any input forces `SEALED_FINAL_RESULT` taint and an empty
  `selection_eligible_for` list.
- `TASK_EXPOSED_DEV` cannot become `CLEAN_ELIGIBLE` through summarization,
  paraphrase, relabeling, copying, aggregation, or author-model rendering.
- `parent_text_targeted=true` is never an ordinary child SLEEP target.
- Every evidence ID resolves to an immutable typed public event record; an ID
  string without a resolved record is invalid.
- Directory payloads use an explicit recursive tree manifest. Symlinks,
  hardlinks outside the owned artifact root, device files, sockets, and
  unlisted files are forbidden.

### 2. `clean_lineage_head.json`

This is the only mutable pointer. The referenced artifacts are immutable.

```json
{
  "schema": "clean-lineage-head/v1",
  "lineage_id": "<immutable lineage id>",
  "generation": 0,
  "state": "CLEAN_DRAFT|CLEAN_SEALED|CLEAN_ACTIVE|CLOSED",
  "birth": {
    "base_model_artifact_id": "sha256:...",
    "tokenizer_artifact_id": "sha256:...",
    "bootstrap_artifact_id": "sha256:...|NONE",
    "birth_manifest_sha256": "<hash>"
  },
  "mechanism_artifact_id": "sha256:...",
  "policy_scope_id": "<ratified visibility/domain policy id>",
  "heads": {
    "adapter": "sha256:...|BASE",
    "optimizer": "sha256:...|NONE",
    "corpus": "sha256:...|EMPTY",
    "ledger": "sha256:...|EMPTY",
    "working_state": "sha256:...|EMPTY",
    "dream_state": "sha256:...|EMPTY",
    "parent_state": "sha256:...|EMPTY"
  },
  "ancestor_head_sha256": "<previous exact head or NONE>",
  "allowed_input_classes": ["CLEAN_ELIGIBLE"],
  "allowed_domain_partition_ids": ["<prebound ids>"],
  "forbidden_domain_partition_ids": ["<prebound ids>"],
  "last_transaction_id": "<id or NONE>",
  "head_sha256": "<hash of all preceding fields>"
}
```

Promotion is compare-and-swap on `(lineage_id, generation, head_sha256)`.
Every new head increments `generation` by exactly one and binds the exact prior
head. The promotion directory is staged, fsynced, validated, then one atomic
rename replaces the pointer. A crash before the rename leaves the old child;
a crash after it leaves the fully bound new child.

### 3. `evaluation_fork_receipt.json`

```json
{
  "schema": "clean-lineage-eval-fork/v1",
  "fork_id": "<immutable id>",
  "source_lineage_id": "<id>",
  "source_head_sha256": "<sealed clean head>",
  "state": "CREATED|RUNNING|TERMINAL_QUARANTINED|RELEASED_READ_ONLY|INVALID",
  "evaluation_role": "DEV_TASK_EXPOSED|DEVELOPMENT_EXAM|SEALED_FINAL",
  "domain_id": "<id>",
  "partition_id": "<id>",
  "eval_descriptor_artifact_id": "sha256:...",
  "descendant_root": "<dedicated non-clean root>",
  "fresh_parent_state_artifact_id": "sha256:...|NONE",
  "allowed_output_root": "<dedicated quarantine root>",
  "return_policy": "DENY_ALL",
  "result_release_group": "<prebound group id>",
  "output_artifact_ids": ["sha256:..."],
  "receipt_sha256": "<hash of all preceding fields>"
}
```

The source head is mounted/read as immutable input. Evaluation writes only
under `allowed_output_root`. The clean lineage root and persistent parent root
must not be writable by the evaluation process. Evaluation-local SLEEP and
parenting may exist only if the ratified cell requires them; all such artifacts
inherit the evaluation taint and die with the root.

## State transitions

### Clean child

```text
CLEAN_DRAFT --all sources verified--> CLEAN_SEALED
CLEAN_SEALED --start governed life--> CLEAN_ACTIVE
CLEAN_ACTIVE --accepted SLEEP CAS--> CLEAN_ACTIVE(generation + 1)
CLEAN_ACTIVE --mechanism change--> new CLEAN_DRAFT sibling from last clean head
CLEAN_ACTIVE --fork evaluation--> CLEAN_ACTIVE + disposable CREATED fork
CLEAN_ACTIVE --end development--> CLOSED
```

There is no transition from an evaluation, quarantined, invalid, or rejected
object into any clean state.

### SLEEP transaction

```text
previous committed head
  -> STAGED(candidate corpus + candidate adapter + exact receipts)
  -> VALIDATED
       -> COMMITTED: atomically promote corpus and adapter together
       -> REJECTED_QUARANTINED: promote neither; old head remains exact
```

Rejected corpus is not “prior corpus.” Rejected DREAM products, canary traces,
gate scores, and candidate optimizer state are quarantined with it.

### Evaluation descendant

```text
CREATED -> RUNNING -> TERMINAL_QUARANTINED -> RELEASED_READ_ONLY
                     \-> INVALID
```

Release permits offline reporting only. It never changes source eligibility.
No retry may reuse learned descendant state. An infrastructure retry starts
from the same immutable source head and descriptor in a fresh descendant root.

## Required entry-point checks

The same library validator must be called by every entry point; wrappers alone
are insufficient because today modules can be invoked directly.

### `create_clean_birth`

- Resolve every base/bootstrap/teaching/mechanism input through the registry.
- Recompute payload and record hashes and transitive taint.
- Require `CLEAN_ELIGIBLE`, an explicitly allowed domain/partition role, and
  no ancestor marked `TASK_EXPOSED_DEV`, `SEALED_FINAL`, `QUARANTINED`, or
  `INVALID`.
- Require an exact bootstrap source allowlist and disjointness certificate.
- Refuse unknown sources, path-only sources, and free-text exposure claims.

### classroom / parent / wake start

- Require the exact current clean head and policy scope.
- Require task domain/partition on the clean allowlist.
- Require parent model, prompt, skills/files, permissions, and incoming parent
  state to match the head.
- Parent notebook updates accept only predeclared target-blind development
  events or the preregistered aggregate developmental-exam codes allowed by
  v5. They reject all final/deployment descendant artifacts transitively.
- A classroom clone writes only isolated evidence; it cannot change the child
  or canonical parent locally. The reducer validates the exact dispatch set.

### DREAM / SLEEP compile

- Require an explicit input-artifact allowlist, not a directory scan.
- Resolve every row to immutable evidence and the current clean lineage.
- Refuse parent text as a target, unsupported drafts, unmanifested summaries,
  descendants, other lineages, and any quarantined candidate.
- Candidate corpus ancestry must be exactly the previous **committed** corpus
  plus eligible new evidence; rejected round corpora never enter.
- Emit candidate corpus and adapter records under one transaction ID.

### promotion / resume / “latest adapter”

- Recompute the entire candidate input closure and verify candidate gates were
  run against the exact previous head.
- Compare-and-swap both corpus and adapter; partial promotion is impossible.
- Resume only the exact recorded head. Never infer state by scanning for the
  lexically latest directory or marker.
- A mechanism identity mismatch forks a sibling and can never silently resume.

### `fork_evaluation`

- Require a `CLEAN_SEALED` or exact saved-age `CLEAN_ACTIVE` head.
- Copy or read-only mount its artifacts into a new descendant namespace.
- Create a fresh root-local parent state when a parent is present.
- Bind domain/partition/role and `DENY_ALL` before the first task byte is
  visible.
- Refuse an output path inside any clean child, canonical parent, bootstrap,
  teaching, compiler-input, or decision-evidence root.

### final/deployment evaluation runner

- Verify the evaluation receipt before model loading or task release.
- Run entirely inside the descendant root; no canonical writer or parent-state
  update endpoint is writable.
- Tag all outputs, including aggregate metrics and plain-language summaries,
  with the evaluation taint.
- For a sealed final, place outputs behind the prebound release barrier. Root
  failures follow the predeclared retry rule; scores never choose retries.

### rank, hyperparameter, curriculum, prompt, and mechanism selection

- Every choice emits a `SELECTION_RECEIPT` naming all inspected evidence and
  the ratified decision scope.
- The checker rejects any input whose `selection_eligible_for` omits that
  scope, including any `SEALED_FINAL` derivative.
- Absence of a receipt blocks sealing the next clean mechanism/parent policy.
- Human inspection is an information flow: manually reading a sealed result
  and then choosing a value cannot be laundered as an unconditioned decision.

## Current source holes this guard closes

### `organism_v6/classroom_round.py`

- `gym_exposure="none (rule-game only)"` is a caller-authored string.
- A round is resolved by directory markers rather than bound artifact hashes.
- `old_rows` loads every earlier `corpus.json`, including rejected rounds.
- SLEEP and exam live in the same round directory with no one-way namespace.
- The parent ledger/playbook is lineage-global and has no artifact-level input
  eligibility check.
- There is no transitive source closure for pooled classroom rows.

### `organism_v6/bootstrap_corpus.py`

- Arbitrary `--ledgers` paths are accepted with no manifest/domain validation.
- `corpus.json`, the trainer input, drops row provenance and retains only
  `q`/`a`; richer provenance lives in a sidecar that is not binding.
- `sources` are path strings, not immutable input artifact IDs.
- Re-authoring a task-exposed episode can therefore make it look generic while
  preserving the forbidden information flow.

### `organism_v6/run_life_v2.py`

- It creates or resumes a life from a directory without a clean-birth record.
- `brief()` and prior-corpus construction scan directories rather than the
  committed head; a rejected sleep's corpus/brief can return later.
- It promotes an adapter marker independently of the corpus used to create it.
- `latest_adapter()` is inferred from disk state rather than a CAS head.
- CompilerGym probes/gates influence adapter promotion in the same life. This
  is valid only for a predeclared development/gate role; it is forbidden for a
  disposable sealed-final descendant and cannot be called “clean parenting.”
- No entry point prevents final-gym observations or parent updates from being
  written back into the source lineage.

## Mutation and regression test matrix

All denials must occur before model loading, tokenizer loading, training, or
task release. Each test must also assert that the prior clean head hash is
byte-identical afterward.

| ID | Mutation / attempted flow | Required result |
|---|---|---|
| CLG01 | Omit the source manifest or one required field. | Fail closed; no output artifact. |
| CLG02 | Write `gym_exposure="none"` beside a task-exposed adapter. | Derived taint wins; promotion denied. |
| CLG03 | Delete/rename a quarantine marker or move payload into a clean path. | Registry ancestry still tainted; denied. |
| CLG04 | Alter one payload byte after sealing. | Hash mismatch; artifact becomes `INVALID`. |
| CLG05 | Feed a clean-looking summary/paraphrase authored from a final result. | Transitive final taint preserved; denied. |
| CLG06 | Add one final outcome, ranking, or score to a parent notebook patch. | Parent CAS denied; previous parent head unchanged. |
| CLG07 | Use a final result in a rank/LR/prompt/curriculum selection receipt. | Decision ineligible; next clean seal denied. |
| CLG08 | Point bootstrap generation at `R2_B_seed3`, `bootstrap_v1`, or `bootstrap_v2`. | Source denied before author-model call. |
| CLG09 | Put one rejected round's row in the next cumulative corpus. | Corpus closure mismatch; SLEEP denied. |
| CLG10 | Promote adapter but not corpus, or corpus but not adapter. | Transaction/CAS denied; neither head changes. |
| CLG11 | Crash before and after staged promotion. | Before: old head; after: complete new head; never mixed heads. |
| CLG12 | Resume by a newer directory than the recorded head. | Exact-head mismatch; refuse resume. |
| CLG13 | Replace mechanism/rank/mask while keeping the lineage ID. | Refuse; require new sibling lineage. |
| CLG14 | Run a final task with output root under the clean lineage or parent root. | Refuse before task release. |
| CLG15 | Let an evaluation-local SLEEP adapter initialize the source child. | Evaluation taint; denied. |
| CLG16 | Reuse the treated child's private parent record for a control/final root. | Parent-state identity mismatch; denied. |
| CLG17 | Smuggle a source through symlink, hardlink, unlisted file, or nested directory. | Tree-manifest/path check denies it. |
| CLG18 | Claim an unknown domain/partition is target-blind. | Missing policy binding; deny. |
| CLG19 | Reuse a consumed final partition as development or writer-gate input. | Role/partition conflict; deny. |
| CLG20 | Read a sealed result before its release barrier and alter a later root schedule. | Access and/or schedule receipt fails; no later root runs. |
| CLG21 | Aggregate many tainted results and omit their input IDs. | Producer/input-closure mismatch; artifact invalid. |
| CLG22 | Retry only low-scoring roots or keep a descendant's optimizer cache. | Descriptor/retry mismatch; retry denied. |
| CLG23 | Include parent words directly as response-loss targets. | Corpus eligibility check denies rows. |
| CLG24 | Use an unmanifested local file or environment variable in parent/child prompts. | Invocation closure mismatch; run denied. |
| CLG25 | Attempt cross-lineage corpus or adapter merge. | Lineage/source-policy mismatch; denied unless a separately ratified data-parallel treatment explicitly permits exact evidence union. |

Positive tests are equally necessary:

- a clean target-blind classroom event can update the clean ledger;
- a v5-approved aggregate developmental-exam code can update only the allowed
  parent field;
- an accepted SLEEP transaction promotes matching adapter+corpus heads;
- a rejected transaction leaves the previous child usable;
- two disposable final cells can read the same sealed snapshot while writing
  to different quarantine roots; and
- release changes report visibility, never artifact eligibility.

## Artifacts that remain quarantined now

The following are development/diagnostic artifacts, never clean-child inputs
for a later CompilerGym parenting or final comparison:

- `R2_B_seed3` and every derivative;
- `~/v6_out/bootstrap_v1` and `~/v6_out/bootstrap_v2`, explicitly marked
  `QUARANTINE_TASK_EXPOSED` by Fable;
- all R2, R3, R4, RP, R_B, and L_B CompilerGym life adapters, corpora,
  ledgers, DREAM/SLEEP products, parent briefs/playbooks, probes, summaries,
  rankings, and downstream renderings;
- CompilerGym-derived rank-calibration, write-swarm, procedure-extraction,
  ritual-selection, gate-tuning, and bootstrap-selection artifacts when the
  intended downstream claim uses CompilerGym; and
- any unmanifested or incompletely manifested candidate source, including
  apparently target-blind `lineage3_*` rule-game and nursery artifacts, until
  their full ancestry, domain, parent visibility, and source hashes are
  audited and re-expressed as `CLEAN_ELIGIBLE` under a ratified policy.

This does **not** erase or discredit those artifacts. They remain valuable
development characterization and can motivate a prospectively frozen method.
They simply cannot become the clean child's personal history, the clean
parent's state, or selection evidence outside an explicitly permitted
development scope.

Local-machine note: the declared `/Users/rohing/v6_out` quarantine marker
files were not present in the local workspace during this audit; their status
is established by the append-only Fable/Codex coordination record, not locally
reverified bytes. The implementation audit must verify the authoritative node
copies before any transfer.

## Smallest implementation seam

If separately authorized, add one module such as
`organism_v6/lineage_guard.py` and call it directly from:

- clean-birth/bootstrap construction;
- `classroom_round` live, sleep, exam, and reducer phases;
- `run_life_v2` start, compile, candidate train, promotion, resume, probe, and
  parent-update paths;
- every adapter trainer and corpus compiler; and
- every evaluation and selection entry point.

It needs only five operations:

```text
resolve_and_verify(artifact_id)
derive_artifact(kind, payload, exact_inputs, local_exposures)
validate_clean_inputs(lineage_head, artifact_ids, decision_scope)
cas_promote_sleep(previous_head, candidate_corpus, candidate_adapter, gates)
fork_disposable_evaluation(clean_head, descriptor, quarantine_root)
```

No automatic directory discovery, path-only identity, free-text cleanliness,
or caller-supplied taint clearing is allowed. That is the minimum boundary
that turns Rohin's contamination rule from documentation into a fail-closed
property.


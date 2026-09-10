# V5 blocker resolution: directional capabilities, isolated exams, and release

Date: 2026-09-09

Status: successor-proposal input only. No implementation, model/tokenizer
execution, data or benchmark generation, adapter/checkpoint work, GPU/resource
use, external scientific execution, claim, publication, or push is authorized.

The cognitive architecture remains exactly THINK, DREAM, and SLEEP, with an
optional pre-parenting birth bootstrap. This repair concerns only the
experimental harness's information and authority boundaries.

## 1. Replace the composite head with minimal capabilities

No semantic stage can read a composite lineage head. The successor separates:

- `active_weight_artifact`: the immutable birth plus current committed personal
  adapter needed to run a child or compare a candidate;
- `eligible_life_evidence`: grounded child-authored public traces admitted by
  the support rules;
- `candidate_closure`: staged views, corpus, adapter, and their provenance;
- `candidate_root_capability`: a non-dereferenceable handle to the staged
  candidate used only by preservation and promotion;
- `cas_token`: an opaque equality-only token over the full committed transaction
  head; and
- parent-audit and repetition-control roots, which remain inaccessible to
  semantic DREAM/SLEEP/evaluation stages.

The SLEEP compiler receives the active weight artifact, eligible-life
capability, immutable birth, and equality-only CAS token. It cannot inspect or
derive parent/repetition roots through the token. The candidate evaluator gets
the prior active weight, candidate root, and preservation panel. The promotion
gate gets only the candidate root, typed verdict, and equality-only CAS token.

## 2. No generic `derived_only` channels

The successor removes generic `derived_only` visibility. Every allowed
projection becomes a named minimal capability with an exact operation:

- `READ`: semantic bytes may be inspected;
- `WRITE`: a new typed artifact may be emitted but prior artifacts of that type
  are not thereby readable;
- `BIND_EQUALITY`: compare an opaque content token for exact equality only;
- `DEREFERENCE`: load the one artifact class explicitly named by the capability;
  and
- `APPEND`: add an audit event without reading or rewriting prior content.

No capability may expose counts, content-derived hashes, order, timing, error
behavior, filenames, cache keys, or handles beyond its declared operation.
There is no catch-all visible or derived composite object.

## 3. Direction and lifecycle are part of the matrix

The exact matrix is stage x directional capability, not merely stage x broad
information class. Each capability exists only within one named epoch:

1. bootstrap construction;
2. developmental wake;
3. DREAM rebuild;
4. candidate SLEEP/write;
5. candidate preservation/promotion;
6. disposable scientific exam;
7. audit; or
8. externally authorized release.

A stage cannot read its own prior outputs unless a separate READ capability is
listed. Every stage invocation has a fresh transaction ID; outputs close when
the epoch ends. Taint tests cover direct and transitive paths, including counts,
IDs, timing, caches, errors, and stale handles.

## 4. Split exam execution, truth scoring, and reporting

Disposable scientific evaluation uses three isolated stages:

- **Exam model executor:** receives only the public exam input and an
  active-weight-only capability; emits a model transcript. It cannot see hidden
  truth, prior transcripts, prior scores, reports, parent/repetition state,
  candidate evidence, or release state.
- **Truth scorer:** receives the frozen hidden answer and completed transcript;
  emits a score. It cannot call the model, alter the transcript, or see the
  continuing lineage.
- **Scientific reporter:** receives frozen score records; emits reporting
  artifacts only. It has no edge back into child, parent, DREAM, SLEEP,
  candidate, promotion, audit authority, or release.

The model-facing executor is recreated for every disposable exam and destroyed
after emitting its immutable transcript.

## 5. Split audit from authority

There is no omniscient auditor that authors a release decision.

- A **blindness auditor** reads dependency manifests and taint receipts, not
  hidden answers, scientific scores, child content, or candidate content.
- A **lineage-safety auditor** reads transaction/root receipts and preservation
  receipts, not downstream hidden answers or scientific reports.
- An **authority verifier** reads only an externally authored, exact human
  authorization artifact plus the hashes/statuses of required audit receipts.
- The **release controller** reads only the authority-verifier decision and the
  exact artifact/scope roots it names.

Human judgment may of course be informed by a separately presented scientific
report. Inside the executable graph, that judgment enters as a new external
authority artifact; no auditor derives it from evidence.

## 6. Fixed parenting gets an immutable cursor, not mixed state

The fixed parent controller receives only:

- an immutable table of outbound lesson bytes keyed by ages 1, 9, 17, and 25;
- a monotone schedule cursor advanced by the external lesson clock; and
- a write-only audit append capability.

It cannot read child behavior, scores, candidate decisions, live-parent
history, adaptive acquisition/relapse state, or its own audit history. Mock
children with opposing behavior histories must receive identical bytes at
identical lesson ages.

Adaptive parenting remains a separately labeled package with narrow access to
public committed child behavior and its own prior messages. It cannot see
private evaluation, candidate, promotion, or release state.

## 7. Safety gates cover every affected action class

`required_before: model_execution` is not sufficient as a generic string. The
successor declares an exact first-affected-action registry containing:

- CPU or GPU model execution;
- tokenizer execution on treatment data;
- bootstrap or benchmark data generation;
- writer, adapter, merge, or checkpoint work;
- candidate compilation, evaluation, or promotion;
- disposable scientific evaluation; and
- any external scientific dispatch or release.

The directional-capability, exam-isolation, rejected-write, and gate-order
fixtures must pass before the first corresponding action in this registry. The
fixture attempts every action with prerequisite receipts missing, failed,
stale, and valid and proves fail-closed behavior.

## 8. Tests that must change in the successor

- Evidence/support and writer taint tests include transitive capability, epoch,
  stale-handle, timing, count, hash, cache, and error channels.
- Lineage fault tests use active-weight, eligible-life, candidate-root, and
  equality-only CAS capabilities rather than a composite head.
- Incremental-blindness review cannot author or influence release.
- Standardized advice, adaptive package, storage/use, replay, and cadence exams
  use active-weight-only executors followed by isolated truth scoring.
- Fixed-policy and repetition tests prove immutable-cursor behavior and no
  controller self-history.
- Evaluation noninterference becomes a full directional
  capability-by-stage-by-epoch product plus transitive taint test.
- Rejected-SLEEP tests include whole-head staleness and concurrent
  parent/repetition commits while promotion remains active-weight-only.
- Gate-order tests bind the explicit first-affected-action registry rather than
  relying on a broad phase label.

All v4 downstream implementation, data, statistics, writer, replay, safety,
review, and claim contracts remain mandatory after this proposal-level repair.


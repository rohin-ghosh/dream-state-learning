# Clean-child lineage guard v2 — smallest enforceable boundary

Date: 2026-09-10

Status: **source-only repaired architecture advisory for deliberation and exact
human ratification**. It authorizes no implementation, model/tokenizer/author
execution, corpus or benchmark generation, training, evaluation, GPU/resource
use, scientific claim, release, publication, or transfer.

## Source boundary

This fresh-context repair used only:

- `AGENTS.md`;
- `research_loop/advisory/20260910_clean_child_lineage_guard_v1.md`;
- `research_loop/advisory/20260910_clean_child_lineage_guard_v1_adversarial_review.md`;
- `research_loop/coordination/20260910_compilergym_bootstrap_quarantine.md`;
- `research_loop/plans/adaptive_parent_development_v5_consensus.md`.

No implementation source, runtime artifact, model, tokenizer, external source,
or local/remote quarantine state was inspected. The v5 document is itself an
exact proposal for human ratification, not evidence that ratification happened.
Any v5-dependent option below therefore remains disabled until its exact bytes
and this enforcement packet are ratified through `AGENTS.md`.

## Verdict

Replace v1's universal, producer-declared taint graph with one experiment-scoped
security boundary:

1. a small lineage authority, under a different OS principal, is the only
   writer of accepted clean state;
2. it launches each state-affecting operation with a one-use grant whose
   **maximum readable set** and sole scratch write root are fixed before any
   protected input is exposed;
3. it accepts an output only from that launch and conservatively makes every
   granted readable object a dependency, whether or not the worker says it read
   the object; and
4. at final launch it irreversibly closes the source lineage and hands a frozen
   snapshot to a separately privileged, blinded, disposable-final service that
   has no clean write capability.

This is implementable because it does not attempt to observe every causal read
or erase human memory. It uses ordinary process/VM access control to make the
allowed read set complete, and a serialized authority to make promotion real.
It is deliberately not a universal information-flow-control system.

The enforced claim is narrow:

> No process admitted by this authority can mutate this experiment's accepted
> child or canonical parent from undeclared local bytes, from a CompilerGym
> descendant, or from sealed-final results; final-root writes cannot reach the
> closed source lineage.

It does **not** prove that an approved teaching file is semantically unrelated
to CompilerGym, that a remote provider internally forgot all state, that a host
administrator did not bypass isolation, or that a human did not remember a
released score while designing a later experiment. Those are authenticated
intake assertions, trusted-service assumptions, administrative controls, and
claim limitations respectively.

The immediate quarantine remains unchanged: `R2_B_seed3`/seed 303 and its
derivatives cannot initialize or update the clean CompilerGym child or parent,
enter its SLEEP/bootstrap corpus, select its bootstrap, or support a clean
from-scratch CompilerGym claim. Renaming, copying, summarizing, or re-authoring
one of those artifacts does not create an eligible authority input.

## The boundary, not a global lattice

There is no global `CLEAN_ELIGIBLE` bit and no general-purpose declassification
language. The exact ratified `experiment_manifest` contains four fixed
operation policies:

| Operation regime | Read authority | Allowed accepted-state effect | Result visibility |
|---|---|---|---|
| Target-blind classroom | Exact birth/head slots, exact approved classroom task/generator blobs, exact parent policy, and brokered fresh requests | Reducer may advance the declared child/parent state slots transactionally | Normal development audit visibility |
| Developmental-exam clone | Exact saved head plus exact preregistered exam panel | Default none; if separately ratified, one named finite-alphabet declassifier may update only enumerated parent-notebook fields | Raw clone records remain quarantined |
| Exploratory task-exposed gym descendant | Exact saved head and an explicitly development-only partition | None into that head or its parent; it may inform a separately ratified future method freeze, never the child's personal history | Development-only; claim records the exposure |
| Sealed final gym | Exact closed frozen head, opaque final descriptor, and fresh root-local state | None; child and parent changes are root-local and discarded | Encrypted/blinded until the prebound release condition |

Eligibility is thus a small table over a named operation and destination, not a
property attached forever to every file. Sealed-final non-return is absolute
for the experiment. The only possible exam return is the one explicit positive
exception proposed by v5; it is absent unless ratified.

## 1. Scoped lineage authority

### Security principal and store

One `lineage-authority` service runs under an OS account whose private store and
signing key are unreadable and unwritable by classroom, trainer, parent, author,
evaluator, developer, and final-runner accounts. The service exposes a narrow
local API; it does not execute models or arbitrary caller code.

Its scope is one ratified experiment and its named sibling lineages. It stores:

- exact byte blobs addressed as `sha256:<digest>`;
- the ratified experiment/birth/freeze manifests;
- immutable grants, run receipts, state-transition events, declassifier events,
  final-handoff events, and partition-consumption events; and
- one serialized accepted-state pointer for each lineage.

This is the previously missing registry/control plane, made explicit and small.
It is not a repository-wide registry. Files outside it are simply unavailable
to an authorized state transition until a separately authorized intake copies
their exact bytes into a manifest slot. Clean intake is allowlist-only; there is
no path-name rule and no way for a worker to assert or clear contamination.

### Exact identity and authentication

Identity never includes a self-referential hash field:

- `blob_id = SHA256(exact file bytes)`;
- `record_id = SHA256(type_tag || 0x00 || exact_core_bytes)`; and
- an envelope carries `record_id`, `type_tag`, the exact immutable core bytes,
  authority key ID, and an Ed25519 signature over all three.

The authority, not a worker, emits the core bytes with one canonical encoder.
The accepted JSON subset has ASCII field names, UTF-8 strings, integers only,
ordered arrays, bytewise-sorted object keys, minimal escapes, no insignificant
whitespace, and no trailing newline. Floats, duplicate keys, NaN/infinity,
unknown fields, and alternate encodings are rejected. A timestamp, if wanted,
is an ordinary signed core field; no identity field may be edited later.

Multi-file objects are bundles of fixed logical slots mapped to blob IDs. Slot
names match `[a-z0-9_.-]+`; they are not filesystem paths. Arbitrary directory
trees, symlinks, hardlinks, sockets, devices, and unlisted files are never
accepted as payload identities. The authority materializes a bundle itself.

A valid hash proves byte identity. The authority signature additionally proves
that the scoped authority admitted the record. Neither proves a semantic claim
such as task-family disjointness; such a claim is a signed ratifier assertion
bound into the experiment manifest.

### Minimal experiment manifest

The exact manifest binds:

- experiment, lineage, claim, and ratification IDs;
- base model, tokenizer, bootstrap, mechanism/runtime, writer/compiler/trainer,
  parent model/revision/prompt/permissions/tools/files/skills, and teaching
  bundle blob IDs;
- the exact target-blind classroom source allowlist and bootstrap sources;
- exact development, exam, and sealed-final partition descriptor digests and
  their disjointness assertion;
- the four fixed operation policies in the table above;
- the optional developmental-exam declassifier code digest, input panel,
  finite output alphabet, permitted parent fields, budget, and use count;
- sandbox/runtime image and broker-policy digests;
- the state slots, gates, saved ages, final cells/roots/seeds/order/budgets,
  retry predicates, stopping rule, metrics, and release predicate; and
- the authority and release-service public keys.

An omitted field is denial. A domain or partition label by itself has no
authority. The descriptor digest and signed disjointness assertion must match
the manifest. The authority can authenticate who made that assertion and its
exact bytes; it cannot prove semantic disjointness by cryptography.

### Minimal accepted state

Each immutable `state_event` contains:

- lineage ID, generation, phase, previous state-event ID, and causing grant and
  run-receipt IDs;
- fixed slots for child adapter, optimizer, cumulative corpus, evidence index,
  working/DREAM state, parent notebook, and any brief or cache allowed to affect
  future execution; and
- unchanged manifest-bound birth, mechanism, parent-policy, tokenizer, and
  runtime IDs by reference.

If bytes can affect a later child or parent run, they must occupy a state slot.
Entry points may read future state only through those slots. A lexically newer
directory, marker, probe, brief, cache, rejected corpus, or unreferenced object
is unreachable by construction.

The authority owns a transactional database and is the sole promoter. Before a
promotion transaction, every output blob is content-verified, stored under the
authority account, and durably synced. In one serialized database transaction
the authority:

1. verifies that the current pointer equals the grant's exact expected state;
2. inserts the next immutable event with a unique `(lineage, generation)`;
3. conditionally changes the pointer from the expected event ID to the new ID;
4. requires exactly one changed pointer row; and
5. durably commits before reporting success.

Two writers from one generation cannot both succeed. A crash exposes the old
event or the complete new event; staged unreferenced blobs may remain but are
not state. Evaluation receipt “changes” are also new linked immutable events,
never edits to a content-hashed record. Crash/recovery behavior is part of the
required test packet for the chosen database and filesystem.

## 2. One-use execution grants and OS confinement

### Grant contents

Before protected input, task, model, tokenizer, or author bytes are exposed,
the authority signs a one-use `run_grant` containing:

- operation type and exact policy clause;
- expected state-event ID and complete logical read bundle;
- executable/source and runtime-image digests;
- sanitized environment values and resource limits;
- network mode (`NONE` or one exact broker endpoint/policy);
- a new empty scratch/output object and log sink;
- exact dispatch/candidate/panel set, randomness input, and gate descriptor;
- permitted result schema and permitted state-slot mutations; and
- nonce, expiry, and single-consumption ID.

The dependency set of every admitted output is the **entire grant**, including
all readable blobs, state/policy/descriptor IDs, executable/runtime identity,
broker requests and responses, candidate set, failures/exclusions, and prior
state. The worker supplies no authoritative input list. Over-approximating the
read set is intentional: an omitted-input lie cannot make an output cleaner.

### Required confinement property

The launcher runs the worker under a distinct unprivileged OS identity in a
private mount/filesystem and process namespace, or in a VM providing the same
property. It must:

- expose only authority-opened immutable input objects from the grant;
- expose one new writable scratch root and no clean/canonical/final-result
  store;
- provide no host home, shared cache, ambient temp directory, clipboard,
  terminal, or interactive input;
- replace stdin, capture stdout/stderr, sanitize the environment, close all
  inherited file descriptors, and forbid process attachment to other runs;
- disable networking, or permit only the exact broker socket in the grant; and
- execute the exact granted image/binary and revoke the grant after one launch.

The authority hashes and opens each regular input without following links,
checks the opened object's metadata and bytes, and gives that same opened or
sealed object to the sandbox. It does not validate a path and later reopen it.
Substrate-specific mechanics may differ, but acceptance tests must demonstrate
the property. A same-user library wrapper alone does not qualify.

A helper invoked directly outside the launcher can compute on arbitrary
developer files, but it cannot read authority-owned protected blobs, obtain a
valid receipt, write the authority store, or promote a head. Sensitive lower
layers independently require the one-use grant handle before the authority
materializes protected inputs. Thus wrapper bypass cannot create accepted
state.

### Run receipt

A small trusted launcher, not the worker, returns an immutable receipt binding:

- the grant and expected-state IDs;
- every materialized input blob and broker exchange;
- executable/runtime identities;
- output blob IDs and schema-validation result;
- normalized termination class; and
- log blob ID in the operation's permitted visibility store.

Tracing actual opens is optional audit evidence, not the security premise. The
maximal readable set in the grant is the dependency closure. If the platform
cannot establish confinement, the receipt says `UNCONFINED` and no output is
eligible for authority intake.

### Remote parent or author boundary

The sandbox has no general network. An allowed remote call goes through a
broker named in the manifest. The broker constructs the request from granted
blobs, uses a fresh request/root credential, forbids caller-supplied conversation
or cache IDs, records exact request/response bytes and provider/model/revision,
and returns only the recorded response. For final roots it issues a distinct
session identity per root.

This authenticates the observed call and prevents the local worker from using
another network source. It does not let the local OS prove the provider's
internal statelessness. Strict cross-root freshness therefore additionally
requires a ratified provider/session-isolation guarantee. Without it, report
“fresh broker session with no observed client-side carryover,” not proven
remote-memory independence; if that weaker boundary is scientifically
insufficient, remote output is ineligible.

## 3. Target-blind classroom and transactional SLEEP

### Meaning of target-blind here

During `ACTIVE_DEVELOPMENT`, the authority can grant continuing-state writes
only to the exact classroom source/generator/task bundles listed in the
experiment manifest. CompilerGym binaries, programs, passes, outcomes, task
identifiers, transformed derivatives, final descriptors, and known quarantined
sources are absent from the sandbox read set and broker policy.

This enforces byte-level non-availability under the declared machine boundary.
The assertion that an approved generated microdomain is semantically unrelated
to CompilerGym remains a human-ratified intake claim. An operator with host
administrative power or a ratifier who manually copies remembered final
content is outside the enforced boundary and invalidates the stronger claim.

Parallel classrooms receive the same exact state snapshot and isolated scratch
roots. Their local writes cannot update the child or canonical parent. A reducer
grant names the exact dispatch universe, including failures and exclusions, and
may consume only the corresponding signed receipts.

### Corpus and mask contract

The trainer-consumed corpus, not a sidecar, is a structured bundle. Every row
contains:

- all source evidence IDs, including every contrast/replay source;
- ordered immutable text segments with derived roles such as child action,
  parent text, harness/outcome, child restatement, or compiler rendering;
- the exact recipe/compiler and tokenizer IDs; and
- tokenizer-bound token spans and the compiler-derived response-loss mask.

There is no caller-authored `parent_text_targeted` Boolean. The compiler policy
determines which source roles may receive loss; parent, exam, final, and harness
spans are masked. A child restatement may be an allowed response target under
the ratified learning rule, but it retains its parent/evidence ancestry. The
trainer independently verifies row IDs, source completeness, tokenization, and
masks, and refuses `q`/`a`-only input or provenance in a nonbinding sidecar.

### One accepted-state transaction

One SLEEP candidate grant binds the previous exact state, complete cumulative
committed corpus, new evidence set, candidate adapter/optimizer, gate set, and
every derived brief/state effect. On acceptance, a single `state_event` updates
all changed future-readable slots. On rejection, none advance. Candidate
corpus, adapter, optimizer, gates, DREAM products, briefs, and caches stay in
the candidate quarantine and can never be selected by “latest” scanning.

Parent notebook promotion uses the same conditional state update. Valid
target-blind lesson outcomes may update ratified fields; infrastructure-invalid
events cannot. Any field or auxiliary file later shown to the child/parent must
be a state slot, eliminating an untracked lineage-global playbook.

### Developmental-exam exception

An exam clone starts under a grant with no accepted-state write capability.
Its raw task text, actions, outcomes, model changes, logs, and summaries remain
in the exam quarantine.

If, and only if, the v5 exception and its exact implementation are ratified, a
separate `exam-declassifier` principal may read the one prebound panel and emit
one value from a finite manifest-bound alphabet. The authority verifies its
code, panel, output alphabet, one-use budget, and destination field list, then
records a linked declassifier event and may conditionally update only those
parent-notebook fields. It cannot emit free text, update child/corpus/mechanism,
or handle sealed-final input. With the option disabled or any mismatch, exam
return is `DENY_ALL`.

This resolves v1's contradiction: developmental exams have a narrow proposed
parent-only return; sealed finals never do.

### Task-exposed method development is not classroom continuity

A development-only CompilerGym descendant cannot update the child or parent
from which it forked. If a ratified scientific plan permits its results to
inform mechanism or hyperparameter development, that occurs outside the clean
lineage and must end in a new exact method-freeze manifest and a new clean birth
whose personal history uses only allowed target-blind sources. The claim must
state that the method was CompilerGym-development-informed and name the
development partition. The sealed final partition must be distinct and
unconsumed.

If the same partition or keys were exposed, they are consumed and cannot be
called sealed final. Under the present quarantine, `R2_B_seed3` derivatives are
not eligible to select a CompilerGym bootstrap or condition the clean child's
hyperparameters; any broader development-use permission is a new material
choice, disabled by default.

This is a per-experiment split/freeze rule, not a global use-relative taint
calculus.

## 4. What sealed final blinding requires

### Freeze and irreversible handoff

Before final task bytes are available, the authority verifies the exact final
plan and changes the source lineage from `ACTIVE_DEVELOPMENT` to
`SEALED_FINAL_CLOSED` in a serialized state event. That phase has no transition
back to a writable clean phase. All final cells read the same named frozen
snapshot. Parent-present cells receive the same mature pedagogy core and exact
parent policy plus a fresh root-bound empty private child record and broker
session, as proposed by v5; treated developmental private state cannot enter a
control/final root.

Final-root child, parent, optimizer, corpus, cache, and SLEEP changes exist only
inside that root's disposable write store. Completion destroys or archives the
root read-only; no root initializes another.

### Separate principals and channels

Meaningful blinding requires more than a result directory:

- a final scheduler/runner OS or VM principal inaccessible to developers and
  the lineage-authority worker accounts;
- an opaque, manifest-bound final partition supplied only to that runner;
- a result/log/telemetry store encrypted to a separate release principal;
- no developer-readable stdout/stderr, filenames, missing-file signals,
  resource telemetry, per-root completion timing, scores, or summaries;
- fixed wall-clock reporting points and a constant-shape status interface;
- a prebound root/cell/seed/order schedule, resource envelope, stopping rule,
  candidate universe, metric set, retry predicates, and release condition; and
- a blinded operations principal that alone maps failures to the finite
  preregistered infrastructure codes and applies allowed retries.

The developer-visible scheduler state is fixed-shape `BATCH_PENDING` until the
release condition. If a problem needs discretionary investigator intervention,
the whole confirmatory batch is aborted without partial score access; any later
attempt is a newly declared experiment. Scores, runtime, exit status, output
size, or missing artifacts never choose roots or retries.

The release principal appends a signed release event only after every prebound
root is terminal under the plan or the plan follows its exact abort rule.
Release changes report visibility, never source eligibility. The closed source
head stays byte-identical.

This cannot be honestly implemented on a workstation where an unblinded
investigator has administrator access to the final process, telemetry, result
bytes, or release key. On such a machine the system can provide tamper-evident
bookkeeping and process separation, but not sealed human blinding. Strict
sealed-final claims require an actually separate administrative/release trust
domain.

After release, human learning is not erased. The consumed final partition is
recorded append-only and cannot be reused by this authority for another
confirmatory claim. A later method may explicitly be post-unblinding and use a
new final partition; it cannot retroactively alter or reopen the closed lineage.

## Enforcement versus evidence versus trust

| Property | Status |
|---|---|
| Worker cannot read undeclared local files, ambient input, clean state, or final results | OS/VM-enforced, conditional on the launcher and administrator boundary |
| Worker cannot write the accepted head, canonical parent, authority log, or signing key | OS-enforced plus authority API authorization |
| Output dependencies include every possible worker-readable granted object | Enforced structurally because the authority constructs the dependency set from the grant |
| Only one promoter wins and crash exposes old or complete new state | Transactionally enforced by the single-writer authority; verified by crash/race tests |
| Final root cannot write the source lineage | OS/VM-enforced and strengthened by irreversible lineage closure |
| Developer cannot see final scores or score-correlated operational signals before release | Enforced only with a separate scheduler/result/release administrative domain |
| A record came from this authority and exact bytes did not change | Authenticated/tamper-evident bookkeeping, not semantic proof |
| Approved source is truly target-blind; partition descriptors are semantically disjoint | Signed ratifier/data-curator assertion plus audits/tests, not OS-provable |
| Remote provider retained no hidden state | Trusted provider/session-policy assumption; broker proves only the observed local protocol |
| Human did not remember or privately communicate a result | Not generally enforceable; prevent access before release, close the experiment, and limit the claim |

## Entry-point binding

Implementation authorization, if later granted, must first inventory every
route to the protected stores. At minimum the scoped authority must mediate:

- clean birth/bootstrap intake before any author/model access;
- classroom common start, live branches, exact reducer, parent patch, DREAM,
  SLEEP compile/train/gates, promotion, rejection, resume, and saved-age exam;
- every corpus compiler and trainer that could produce an accepted slot;
- all reads of prior adapter/corpus/brief/cache/parent state;
- development-only gym fork and the optional exam declassifier;
- final freeze, root creation, scheduler/retry, result collection, release, and
  partition consumption; and
- direct lower-level model, parent, compiler, trainer, updater, promoter, and
  evaluator commands.

The decisive coverage rule is not “all commands called a validator.” It is:
only the authority can expose protected input or update accepted state, and it
does so only for a consumed grant and signed launcher receipt. A missed helper
therefore has no protected capability. Repository-wide implementation review
must still confirm that no second writable clean store or authority credential
exists.

## Acceptance tests required before implementation approval

All negative tests fail before protected model/tokenizer/author/task bytes are
exposed or accepted state mutates. Each asserts the previous state-event ID and
all canonical parent/child slots remain exact. These tests directly dispose of
the adversarial review's AR01–AR20:

| ID | Required test and result |
|---|---|
| AR01 | Omit a readable input from the worker's claimed metadata. Authority-derived maximal grant closure still includes it; worker metadata cannot reduce ancestry. |
| AR02 | Attempt reads through host path, env, stdin, network, remote session ID, cache, inherited FD, clipboard, terminal, or process attachment. Sandbox denies the channel; unconfined receipts are ineligible. |
| AR03 | Supply task/final-exposed evidence under a clean-looking artifact label. Evidence bytes must be a granted bundle slot and the operation policy rejects the source/descriptor; there is no separate untainted evidence edge. |
| AR04 | Render a contrast from primary and randomly selected secondary episodes while recording one. The grant/receipt and trainer row must bind both or serialization fails. |
| AR05 | Give the trainer `q`/`a` rows with provenance only in a sidecar. Trainer rejects before loading/training. |
| AR06 | Falsely mark parent, paraphrase, harness, exam, or final spans as trainable. Compiler-derived tokenizer mask/source-role verification rejects; caller has no Boolean override. |
| AR07 | Try to choose a mechanism after an unrecorded final inspection, failed candidate, early stop, or human intervention. Before release results are inaccessible and the lineage is closed; after release the partition is consumed and any later method is explicitly post-unblinding, not a continuation or independent confirmation. |
| AR08 | Change root/seed/order/retry/stopping from score, runtime, status, size, or missing files. Sealed scheduler exposes only fixed-shape batch status and follows the signed plan; discretionary intervention aborts the batch. |
| AR09 | Emit one permitted developmental aggregate into one allowed parent field. It succeeds only through the exact ratified one-use declassifier. |
| AR10 | Send that aggregate or any sealed-final derivative to child, corpus, mechanism, prompt, LR, schedule, or another parent field. Authority operation/destination policy rejects. |
| AR11 | Race two promotions from one state generation. Exactly one conditional pointer update commits. |
| AR12 | Crash after every blob, database journal, event, pointer, and directory durability boundary. Recovery exposes old or complete new state, never mixed state; unreferenced blobs remain unreachable. |
| AR13 | Mutate an evaluation receipt's state or outputs. Rejected; each transition must be a new signed linked event. |
| AR14 | Swap a verified payload via symlink/rename or modify it between check and use. Authority supplies the same opened/sealed immutable object or aborts. |
| AR15 | Present a stale probe/gate/cache from another candidate/head. It is not in the exact grant/state slots and cannot be consumed. |
| AR16 | Make a rejected artifact lexically newest. Resume/reducer/parent/wake read only state slots; rejected bytes stay unreachable. |
| AR17 | Relabel or overlap a final partition under another name. Exact descriptor digest and signed manifest/disjointness assertion must match; any exposed digest is consumed. Semantic assertion limits are reported. |
| AR18 | Invoke a direct trainer/compiler/parent updater/evaluator/promoter without a grant. It cannot obtain protected inputs, authority receipt, or accepted-state write access. |
| AR19 | Reuse remote parent/author state across roots. Broker forbids conversation/cache reuse and binds fresh root sessions; missing provider isolation proof downgrades the claim or makes remote output ineligible. |
| AR20 | Release final visibility. Only a release event/access policy changes; closed source and every state slot remain identical. |

Additional positive tests are required for: exact target-blind birth; normal
classroom evidence/reducer/parent update; complete accepted SLEEP transaction;
rejection with corpus/adapter/optimizer/parent/brief rollback; authorized resume;
optional parent-only developmental code; two final roots reading one snapshot
while writing distinct disposable stores; full-batch blinded release; and
post-release refusal to reopen the lineage or reuse the consumed partition.

## Disposition of all v1 blockers

1. **Lying manifests:** removed as a security premise. OS confinement fixes the
   readable set; authority-derived maximal-grant dependencies replace declared
   “actual inputs.”
2. **Semantic/statistical feedback:** final plans, schedules, retries, logs, and
   release are prebound behind a separate blinded principal; the lineage closes
   before exposure. Human memory is explicitly outside the claim.
3. **Broken transitive closure:** no heterogeneous universal graph is needed.
   Every admitted output binds the entire fixed grant, including evidence,
   code/runtime/policy, broker exchanges, candidates/failures, prior state, and
   descriptor. State can read only fixed slots.
4. **Global-versus-use-relative cleanliness:** replaced by the four-operation
   destination matrix and, if ratified, one exact exam-to-parent declassifier.
   Sealed final remains absolute non-return.
5. **Undefined identity, mutable receipts, unauthenticated writers, fake CAS,
   and crash gaps:** exact immutable signed record bytes, linked transition
   events, an authority-only key/store, same-open-object execution, and a
   serialized conditional database update resolve them.
6. **Unauditable parent-target Boolean:** removed. Structured source spans and a
   tokenizer-bound compiler-derived mask are mandatory in trainer input.
7. **Uncounted registry/sandbox/release systems:** made explicit as three scoped
   trusted services with separate principals and stated trust limits. The
   design no longer claims three JSON files enforce information flow.

## Material choices requiring exact ratification

This packet is a repaired proposal, not a non-material bug-fix authorization.
Before implementation, the durable `AGENTS.md` path must ratify at least:

- the exact experiment manifest and target/development/exam/final split bytes;
- the source allowlist, disjointness assertion, and current quarantine intake;
- authority record schemas, canonical encoding, signer, database, durability,
  recovery, and OS/VM launcher substrate;
- parent/author broker and the accepted remote-isolation claim;
- the exact state slots and SLEEP transaction boundary;
- the corpus roles, compiler policy, tokenizer masks, and gate semantics;
- whether the v5 developmental-exam declassifier exists and its exact finite
  interface;
- whether any development-only CompilerGym result may inform a new method
  freeze, and the resulting claim language;
- final schedule/retry/status/release/abort behavior and administrative trust
  domains; and
- every acceptance test above.

Only after exact human ratification may scoped implementation and CPU-only
tests begin. A fresh independent implementation reviewer and author-side
scientific advocate remain required before any GPU/scientific-claim gate.


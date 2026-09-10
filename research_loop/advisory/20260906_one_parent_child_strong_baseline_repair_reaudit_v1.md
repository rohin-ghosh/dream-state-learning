# One-parent/one-child strong-baseline repair re-audit v1

Date: 2026-09-06

Status: fresh independent read-only re-audit of the current source-bound
proposal. This advisory changes no candidate bytes and authorizes no
implementation, model/tokenizer call, benchmark, adapter operation, GPU use,
or scientific claim.

## Verdict

**REVISE.** The repair correctly makes `LEAFE_STYLE_FINAL` descriptive-only,
moves it after immutable headline artifacts, removes it from the adaptive
root rule, and adds arithmetically correct diagnosis/recovery input and
retrieval ceilings. It also adds a genuinely disjoint, once-only semantic
certificate. The candidate is nevertheless not yet an exact or semantically
closed strong-memory contract: its actual updater prompt omits the schema,
its retrieval/render surface disagrees about raw ledger blocks, its admission
table permits unsupported record fields, its 960-record-embedding ceiling is
false under legal transitions, and the retrospective LEAFE branch does not
freeze memory/state at the historical branch point.

## Disposition of the three prior blockers

1. **Exact `ACTIVE_TEXT_FIXED` bytes/schema/query/accounting — NOT CLOSED.**
   The typed output shapes and four-line query are substantial progress, and
   `4,160 + 240 = 4,400` query embeddings/root is correct under the stated
   cadence. The complete callable byte surface and record-update accounting
   are still not closed by the current bytes.
2. **Semantic faithfulness plus a disjoint once-only certificate — PARTIAL.**
   Development/certificate seed and ID namespaces are disjoint; code and
   thresholds freeze before one scoring pass; failure requires a new version
   and new sealed cases; scores do not return to the updater. Those controls
   pass. The runtime semantic predicate and certificate scoring unit remain
   permissive/ambiguous, so the certificate does not yet certify the claimed
   closed semantics.
3. **Coherent descriptive-only LEAFE timing/input budget — CORE REPAIR
   PASSES, CAUSAL SNAPSHOT DOES NOT.** The former power/timing contradiction is
   gone. `589,824` diagnosis/recovery input tokens, 160 added queries,
   `151,552` returned active-text tokens, 160 calls, 45,056 output tokens, and
   one fit/root all recalculate. A future-information edge remains unless the
   historical branch snapshot is bound explicitly.

## Exact blockers

### 1. The exact prompts do not provide the schema they demand

The system message tells the frozen base to match schema version 1, but the
two declared exact user messages contain neither operation-specific schemas,
enums, transition rules, nor a schema placeholder. This contradicts the
headline plan's 1,024-token `fixed instruction/schema` partition and leaves
the actual updater to guess a repository-local protocol it cannot see. Bind
the exact schema/instruction bytes presented on each call and recompute the
partition/output feasibility.

The remaining prompt inputs are also names rather than byte contracts:
`OBJECTIVE_METRIC_CLOCK_BYTES`, causal-spine events, raw-assistant events, and
the cited-event/record bundle have no closed object schemas or renderers here.
The plan furthermore indexes and may return raw ledger event blocks through
BM25, while the supporting contract defines actor insertion only for complete
`RECORD` JSONL and says no other memory text is inserted. Define event-block
boundaries, IDs, canonical bytes, ranking/packing eligibility, and whether
they are actor-visible or updater-only. Also bind terminal-newline behavior
and JSON escaping, not merely future example hashes.

### 2. The semantic merger admits records not entailed by their evidence

Support and counterevidence arrays need not be disjoint, and most proposition
kinds define no mechanical counterevidence predicate. Declared scope is not
tied to cited events, so an arbitrary `PROGRAM` or `PUBLIC_FEATURE` key can be
attached to otherwise valid evidence. `SCORE_EFFECT` and
`PREDICTION_BIAS` constrain a median/sign but do not derive
`outcome_class`; `PROCESS_ASSOCIATION` likewise leaves the claimed outcome
underconstrained. `memory_type` is not mapped to proposition kind, and
guidance lacks exact mode/cardinality/condition laws, allowing empty or
irrelevant guidance arrays and incoherent `NONE` objects. `ADD`, `REVISE`,
and `SUPERSEDE` also do not close the legal provenance of
`supersedes_memory_id`.

Define a total per-kind recomputation law for scope, support,
counterevidence, outcome, record type, guidance, and supersession provenance.
Then define the certificate's exact scoring unit and denominator—including
malformed outputs, `REFLECT` items dropped by `NOOP`, and missing guidance—so
“precision over every non-`NOOP` emitted proposition” is executable rather
than interpretive.

### 3. The record-embedding and stored-record bounds are wrong

A legal `SUPERSEDE` changes the old record's canonical document to
`SUPERSEDED` **and** creates a new record. Four such deltas can therefore
change eight dense documents in one program, not four. `LINK` also changes
the source document and requires index maintenance. The 960/root ceiling is
valid only if an explicitly defined tombstone/removal policy avoids embedding
the old record; no such policy or retrieval filter exists. Otherwise the
simple worst-case ceiling is 240 programs times eight changed documents =
1,920 embeddings/root, before any retry/reindex policy.

In addition, `linked_memory_ids` has no cardinality bound and cumulative
revisions may grow retained evidence arrays. The 256-token emitted-record cap
does not explicitly cap the post-merge stored record, yet actor retrieval must
return complete records within 1,024 tokens. Bound the canonical stored
record and all arrays, define oversize transition failure, and include every
changed document in dense/BM25 accounting.

### 4. Retrospective LEAFE retrieval can see the future

The comparator diagnoses the earliest historical failure/surprise only after
the full headline artifacts are immutable, but it merely says that it reuses
the frozen `P0` store. A terminal `P0` store contains records written after an
early branch point. Bind diagnosis and recovery to a content-addressed
snapshot of model checkpoint, context/ledger prefix, environment state,
active-text store/index, query fields, and clock as of that point. Otherwise
the descriptive comparator leaks future public outcomes into its recovered
branches. The descriptive label does not cure that information advantage.

## Nonblocking findings

- Per-service/root isolation, parent deletion, public-only evidence, and the
  `D -> C_active -> C_public` interpretation remain coherent.
- Main call/output/input arithmetic outside record re-embedding still
  recalculates to the stated ceilings.
- The paper and readiness note correctly qualify `R0` as a
  frozen-parameter active-memory reference and forbid a powered LEAFE win.
- The workflow and source-binding manifest name the repaired contract and
  match all currently listed source hashes audited below.
- Query sanitization should run NFKC before delimiter replacement; the current
  reverse order lets compatibility characters normalize into `|` after the
  delimiter pass.

## Required disposition

Repair the four blockers, regenerate source hashes, and obtain a new bound
independent approval. Until then, `ACTIVE_TEXT_FIXED` may be described only as
proposal-stage; it has not earned the word **strong**, and neither scientific
root spending nor the optional LEAFE diagnostic is authorized by this audit.

## Audited hashes

- `AGENTS.md`: `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e`
- headline plan: `c7de12fe75f6971e8ad27888e3a95deabe8f01c2fca03eb0770e187e7c7e65ca`
- active-text contract: `2dd39a5ad56558f9164763fc33dd936b012385f0b63fcd75de67d30db3206606`
- scope proposal: `466319fa741a583f2cb9cf1dd6e01fd255877feae5818ea7697e3fab1e17dc75`
- deliberation workflow: `969b3f96b73dd506db5e40edabdad094493feed4891f540bb24b51aab93c7dac`
- source-binding manifest: `48e8a7379f613a47c2462dbe0bf39fd09454756e01b20cbae7f873bc509ca4ed`
- paper: `3ad83dc406cdf2331a7ce833e1566002942fd21ed6b447313fe7315f6f83dc59`
- readiness note: `6665141669151135365781352a5c4d237caee1c5233ffc0dd8a150dd67bf75ed`
- prior integrated audit: `2e787b059992d0861f0d71d3f4924a3c8e0a355373f6d7573365683f8c9fc0d8`

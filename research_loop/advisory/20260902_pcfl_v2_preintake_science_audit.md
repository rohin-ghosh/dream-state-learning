# PCFL-Compose v2 pre-intake science and benchmark audit

**Status:** read-only pre-intake advisory. No proposal, intake state, code, CPU
construct, model, network, or GPU work was changed or run.

## Binding check and verdict

I audited the exact v2 change SHA-256
`2fc2521d821efc2ff4852ef9decbb4c2bdf834a8f1b0ff438aec7e78d2a0f047`.
All declared `context_files` hashes, including the complete authored v2 bundle,
matched their bound values. The all-pass assignment arithmetic is also correct:
**484 Dream + 2,926 recurrent Think + 4 structured one-shot Think = 3,414
scientific model calls**, with exactly two non-replacing replay opportunities
for a **3,416 process-call** maximum.

**Recommendation: do not enter intake yet.** The science boundary is now
substantially disciplined and the stated 3,414-call all-pass branch is a good
paper-directed DEV spend. However, two exact interface omissions make the
central fresh-Dream-2 revision path non-executable as bytes, and the Stage-1
gate does not yet require a memory-selection response to raw A. These are
small, no-new-call repairs, but they are blocking before a fresh intake.

After those repairs, the proposal is worth a 3,416-opportunity DEV spend as a
go/no-go instrument for later powered and post-context work. It remains
inappropriate as a paper-efficacy experiment or as evidence about lifetime,
LoRA, general external memory, raw perception, or recurrence efficiency.

## What the current roster can identify

| Allowed clause | Status after stated gates | Reason |
|---|---|---|
| Prospective commitments from public events plus supplied local permutations | **Identified, conditional on construct/chronology gates** | Dream-1 runs before A, target packets arrive only after corpus freeze, and the A candidate/branch B endpoints are terminally checked. This is a prediction result with supplied local operators, not a raw-perception result. |
| Raw-A-conditioned Dream-2 revision | **Not yet identified as written** | h has a common Dream-1 clone, same coupled Dream-2 seeds, and raw-A/mechanical descendants as the declared differences. But the all-pass gate requires branch-correct B commitments, not a charged raw-A read plus an explicit changed/selected terminal memory object. Correct B could be produced while retaining the same pre-A corpus. |
| Frozen opaque corpus changes later action | **Identified only on selected `h=0` rows, if valid paired rows pass** | EMPTY/crossed/sham are paired over sampled z and antipode by goal twin. The reducer separates valid first-action redirection from failure-mediated differences and requires action success contrasts. This does not establish h-swapped revision-to-action mediation. |
| Factor-specificity stress test | **Correctly an alarm, not positive identification** | q-specific SELF/EMPTY/OBSERVED pairs have identical q/z/target/twin keys and are not pooled. The calibrated q rule can detect an alarming independent gain; its absence is not evidence of a population factor effect. |
| Untouched Stage 2 evidence | **Correctly conditional only** | Stage 2 rows exist at T0 but open only after the fixed Stage-1 conjunction, remain separate, and terminate `HUMAN_REQUIRED`. They are an output-blind conditional canary, not replication or an unconditional second factor sample. |
| Recurrent Dream / Think mechanism | **Only the qualified Dream comparison; opaque Think necessity is untested** | The one-shot Dream wording correctly says eligible-information/output-capacity matched but interaction/compute unmatched. The four one-shot Think rows are AST-only, so no opaque Think recurrence conclusion is licensed. |

The selected-h and conditional-stage restrictions are unusually well handled in
the authored text: `experiment_spec.md`, `assignment_ledger.md`, and
`analysis_contract.md` all prohibit pooling, h mediation, or a replication
claim. No additional h-cut row is needed for the exact selected-h corpus-action
clause; adding it would deliberately change the 3,414 design.

## Blocking exact-byte repairs

### B1. Typed receipts do not support the declared Dream-2 or Think reads

`event_catalog.schema.json` permits `CANDIDATE` and `TARGET_MENU` handles, but
its only `charged_read_receipt.payload` requires the public-event fields
`before`, `action`, `after`, and `slot_permutation`. It has no candidate
payload/receipt, NOTE/AST reader receipt, or target-menu receipt. This conflicts
with the declared fresh Dream-2 candidate-handle read, the target-time lexical
or AST reader, and the visibility matrix's statement that staged opaque bytes
reach Dream-2 through a candidate-handle READ.

As a result, v2 currently has no typed, target-blind, model-visible way for a
fresh Dream-2 process to inspect a Dream-1 candidate and then RETAIN it. It
also cannot validate the reader behavior that T05, T06, T07, and T11 promise.
This is a protocol-executability blocker, not an implementation detail.

**Required replacement:** define a discriminated receipt union, with exact
canonical forms for at least:

1. `PUBLIC_EVENT_RECEIPT`: the current raw `before/action/after` plus the
   event-local `slot_permutation`;
2. `CANDIDATE_RECEIPT`: a charged Dream-1 candidate envelope plus a new,
   fixed-shape **Dream-2-session capability** minted only after the read;
3. `OPAQUE_NOTE_RECEIPT` and `AST_RECORD_RECEIPT`: the exact target-time reader
   return or `NOT_FOUND`; and
4. `TARGET_MENU_PACKET`: post-freeze task input, not a pre-Dream catalog item.

The capability maps a read candidate to immutable bytes only in the current
Dream-2 session. It must be fixed-shape and hide content address, digest,
path, variant, cache, and deduplication. A Dream-2 RETAIN selects that
session-local capability; REPLACE stages a new object. This preserves the
firewall and adds no model calls. Update `event_catalog.schema.json`,
`semantic_dsl.schema.json`, `semantic_contract.md`, `resolver_reducer.md`,
`visibility_contract.md`, prompts, and T05/T06/T07/T10/T11 fixtures together.

### B2. The phase/state grammar cannot express several required terminals

The compact `semantic_dsl.schema.json` permits every operation enum in every
phase, does not define phase-specific READ/PREDICT/USE payloads or NOTE/AST
node objects, and requires `candidate_capability` even for `COMMIT` with
`decision=ABSTAIN`. The prose says ABSTAIN has no active corpus, while the
schema requires a capability that elsewhere denotes an exact staged candidate.
Nor is there a model-visible non-digest node identity for PREDICT to select
from its own staged workspace.

This leaves the harness with discretion precisely where v2 intends a
model-owned, content-addressed decision. It also prevents a Stage-0 maximum
fixture from proving the real accepted language rather than an informal
implementation choice.

**Required replacement:** make `RESOLVER_STEP` a phase-discriminated,
cross-field schema/validator contract. It must define READ query/handle,
model-authored node payload and stable session-local node reference, PREDICT
manifest/prediction/parent fields, USE/LOCK payloads, and phase operation
allowlists. Define COMMIT as a `oneOf`: RETAIN/REPLACE require exactly one
current-session capability; ABSTAIN requires no capability and materializes no
corpus. Bind candidate payload maximum to a number that can coexist with the
complete-candidate maximum. The current `4,096` payload ceiling alongside a
`3,072` complete-candidate ceiling should be replaced by one feasible
cross-field maximum verified by the pinned-tokenizer fixture. Update T06, T07,
T09, T11, and T16; no row or call count changes.

### B3. “Revision” needs a model-selection receipt, not only correct B

The h fork itself is sound: Dream-1 is cloned, Dream-2 seeds are coupled, and
the causal-difference allowlist correctly admits raw A plus its event-local
extraction/receipt descendants. Yet the Stage-1 conjunction requires only both
h branch-correct Dream-2 B commitments. It does not require either branch to
READ raw A, select a non-ABSTAIN candidate, REPLACE/otherwise alter the
pre-A selected object, or produce distinguishable branch-selected corpora.

The current evidence can therefore support “raw A was followed by
branch-appropriate B commitments,” but not the stronger descriptor “fresh
Dream-2 made registered branch-appropriate revisions.” It cannot be repaired
by the selected-h action cuts, which intentionally do not test h mediation.

**Required replacement:** add a mechanical `revision_receipt` to the existing
Stage-1 conjunction. For each h branch it must show a charged raw-A receipt,
a non-ABSTAIN terminal Dream-2 selection, and a terminal manifest whose
provenance includes that raw-A receipt. If “revision” remains in the permitted
descriptor, additionally require predeclared branch-responsive selection—for
example a `REPLACE` from the Dream-1 selected object and byte-distinct
content-addressed terminal corpora across h, audited offline only. This proves
a raw-A-associated selected-byte change, **not** h-mediated action. The
alternative is to delete “revision” and report only B commitment response.
Amend `experiment_spec.md` §§1 and 4, `analysis_contract.md`,
`assignment_ledger.md`, and T02/T10/T15/T18. This changes no calls or controls.

## Extractor, q alarm, and stage conditionality

### Supplied extractor: acceptable, but only under the stated narrow claim

The extractor is acceptable scaffolding for this DEV. Its normative contract is
pure, stateless, event-local, globally label-equivariant, and limited to the
literal observed six-slot permutation of a charged public event. It has no
family, root, h/q, target, history, closure, factor, gauge, inverse, or
cross-event input/output. The same payload is supplied to factor, independent,
opaque, AST, one-shot Dream, exact, and observed interfaces, and T04/T05/T07
require the rendered q-null and unread-read gate after serialization.

That is a fair common *perception* interface, not an external verifier of the
unseen target. It does materially scaffold the problem: v2 tests the connection
and use of already extracted local operators. It does not test operator
perception from trays, factor discovery, schema discovery, or autonomous
algebra extraction. The result descriptor names the extractor, so no extra
ablation is required. Retain the event-local source/hash and the q-null-after-
extraction test; removing either would weaken the scientific firewall.

### q and selected-h framing: scientifically correct for DEV

The q alarm is correctly non-inferential. Its four rows per q are coupled,
not four samples; the exhaustive Stage-0 vector table makes it a calibrated
warning rather than a binomial test. A quiet q root merely means the particular
matched-negative canary did not trip. It does not show factor identification,
estimate a false-positive rate, or validate a population difference.

Selected-h cuts are equally honest. h=0 corpus interventions are presealed and
the absent h=1 cuts are costed at 372 recurrent Think calls. The proposal
separates raw-A-to-Dream-2 response from selected-h corpus-to-action and
forbids h-mediated-action language. Stage 2 is conditional on a fixed open-root
gate, output-blind as to its sealed root artifacts, and always terminal. These
restrictions prevent selection bias in the *conditional DEV description*; they
do not turn Stage 2 into an unconditional replicate.

## What can be removed without weakening the allowed core result

The core causal/specificity DEV needs Stage 1, the two Stage-2 primary forks,
same-h/q EMPTY/OBSERVED controls, and selected-h crossed/sham rows. It does
not need a representation or recurrence-interface diagnostic to license the
narrow descriptor above.

| Non-core Stage-2 panel | Calls | Removal effect |
|---|---:|---|
| AST diagnostic, two selected lives | 220 | Removes only the separate structure-assisted representation diagnosis; it cannot rescue opaque SELF. |
| Structured one-shot Think | 4 | Removes only the AST interface diagnostic; no opaque Think conclusion is currently allowed. |
| One-shot Dream plus iterative D4 evaluation | 128 | Removes the qualified recurrent-Dream interface comparison; the descriptor already prohibits recurrence/efficiency claims. |
| **All three** | **352** | Leaves a **3,062-call** scientific ceiling and the same permitted opaque causal, selected-h, and q-alarm claims. |

This is not a demand to remove them. At 352/3,414 calls they are modest and may
be valuable for debugging an expensive future study. But they are ancillary to
the allowed primary result, so a strictly minimal paper-direction go/no-go can
drop them rather than treating them as proof of recurrence or representation.
By contrast, do **not** remove the full Stage-0 renderer/extractor/null
certification, the open-root oracle ceiling, q-specific controls, or the
selected-h crossed/sham rows: each protects one of the remaining causal clauses.

## Pre-intake disposition

Once B1--B3 are frozen, hash-bound, and re-reviewed, the authored v2 is a
well-targeted low-cost DEV: it can falsify a strong claim cheaply, preserves
the correct independent unit, and does not waste another several thousand
nested calls on unattributable baselines. Its appropriate decision value is
whether to invest in a separately ratified new-root confirmation and a genuine
post-context/lifetime study. It is not itself paper evidence, and a green
receipt must not automatically authorize the next experiment.

Until then, the recommendation remains **pre-intake hold**. The missing typed
receipt/state machinery and revision receipt mean that a green Stage-1 gate
would not yet have the exact causal semantics the v2 descriptor asserts.

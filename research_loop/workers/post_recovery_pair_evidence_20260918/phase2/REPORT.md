# Phase2: current-parent retention across THINK → ACT

**Non-material mechanism repair; CPU-only proposal, NOT deployed.** No learner,
parent, policy, journal, process, GPU allocation or live source was changed.
No private score/panel/readout data was read. This does not claim better learning.

## Observed mechanism, not inferred from child self-report

Both running natives have identical guard-pinned bytes for the driver, stream,
history and plain-context modules. `PROVENANCE.json` binds those bytes to the
observed `/proc` identities, guard hashes, immutable records and proposed fork.
This is source/guard/process evidence, not an introspection of resident Python
objects. The reproduced token counts corroborate the actual recorded path.

The call path is `ThinkActLearn._generate_stage → ContinualStream.step →
compact_for_prompt → TrainHistory.compact/render`. `step` protects only the
suffix appended **in that call**. On the next ACT call, the correction received
during THINK is now historical and may be crossed by the compaction frontier.
`correction_parents` tracks the correction ledger; it is not a retention pin.
Existing Rohin pins are separate and unchanged.

Concrete frozen trace: INBOX2746 → REQUEST2756 message6 (masked) → THINK2757;
then CONTEXT_INPUT2762 → COMPACTION2764 → REQUEST2765 → ACT2766.
The current parent event is `parent:inbox:910c908bf27745289ac7155581abedf0`,
source SHA `6738e46b1d1c372022c359e85283e9a1265500e2fb60686c4a7573683c7511f0`.
It is raw event1165. The ACT call protects from1169, but compacts through1167,
carrying the **previous child summary83**, not that parent correction. Thus the
parent is absent from the actual ACT request, although its raw history survives.
THINK2757 identified the missed second method/changed starting number; ACT2766
did not complete the correction. No correction-success upgrade is justified.

This loss occurs in all three reviewed frozen ACTs (2700,2733,2766). All four
reviewed learner ACT requests (4056,4135,4214,4293) retain their current parent;
the learner's errors cannot be attributed to this loss in the reviewed window.
These are bounded-window findings, not lifetime or first-ever claims.

## Exact tokenizer counterfactual

`ACTUAL_BUDGET_REPLAY.json` uses canonical CONTEXT_INPUT2762 and the native
Qwen tokenizer/chat-template bytes, on CPU without generation or live writes:

| Variant | Before | After | Frontier | Current correction rendered |
| --- | ---: | ---: | ---: | --- |
| Existing behavior | 5182 | 4072 | 1167 | no |
| Proposed retention | 5182 | 4378 | 1167 | once, exact source text |

Both remain below the **unchanged 4608 threshold**, with context6144 and
generation cap512; every historical token is still masked. Baseline counts and
frontier exactly reproduce COMPACTION2764. This is a counterfactual prompt
repair, not a new child ACT or a behavioral result.

## Minimal proposed change

Three copied modules only; the exact delta is `REPAIR.patch`:

- The driver remembers the newest source-bound parent actually rendered in
  the current THINK request. A freshly delivered parent supersedes it. This
  is a delivery-order rule, not a semantic correction classifier.
- THINK continuations and ACT receive one explicit retained-parent event ID.
  Unrelated archived prompts are not all pinned or resurrected. A visible
  preexisting correction can qualify when actually rendered in current THINK.
- History rendering includes that exact existing parent event once if normal
  compaction omits it, with the same parent/source attribution and masked labels.
  It does not rewrite history, invent a child summary, or add a training row.
- Retention is a current-wake handle, cleared at LEARN/new wake, not a growing
  permanent pin list. Existing human pins and original raw history remain intact.
- The exact same threshold/token counter rejects over-budget prompts. An
  oversized correction still raises the existing budget error before generation;
  the repair does not truncate it, grow context, or promise universal liveness.

The standing old tests cover incoming-input protection, prior child-summary
carry, oversized input, and explicit human pins. They did **not** cover a parent
crossing from an already-rendered THINK into the following ACT. The new tests
cover that omission, two THINKs, newest-vs-archived inputs, provenance, masking,
console coexistence, no permanent pins, and hard budget enforcement.

## Validation / prospective adoption

Run `python3 research_loop/workers/post_recovery_pair_evidence_20260918/phase2/test_retention.py`.
Use `phase2/run_checks.py` to reproduce both the new and five existing contracts.
`TESTS.log`: 17 targeted synthetic tests pass. `LEGACY_TESTS.log`: five focused
existing retention/masking tests pass against the fork. No model was sampled.

No safe resident hot-adoption hook has been established and none is attempted.
The owner can stage this exact three-file delta into a **new immutable source
closure**, preserving recovery/continuation patches, R227 admission, frozen
optimizer semantics, original parent cadence and the 6144/4608/512 limits.
Verify baseline hashes before applying; never overwrite the active source.
Use only a subsequently authorized supported COMPLETE-boundary adoption,
with same journal/adapter/optimizer/RNG/working state and new source pins.
Do not claim zero downtime or treat this proposal as restart authorization.
An arbitrary mid-THINK restart is not supported: the transient handle is
reconstructed from an actual future THINK request, not invented from old input.

After adoption, inspect actual LOAD/source pins and the next source-bound
parent → THINK REQUEST → ACT REQUEST chain. Require the exact correction once,
externally masked, at the existing budget. Score the following **actual ACT**
for application and a later relevant attempt without a reminder separately.
Neither retention in context nor repeating the answer demonstrates adapter
retention, level2, or level3 correction survival.

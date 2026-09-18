# R223/R224 current ownership and implementation

This worker owns `gpu/ny_caption_life.py`, `gpu/ny_caption_life_service.py`,
`tests/test_ny_caption_r223_freeform.py`, `tests/test_ny_caption_continuous_r223.py`,
and this worker directory. Turing's explicit handoff confirms no shared-library
edits. Old R221 ownership/API-request text is superseded, not current authority.

The latest handoff assigns this worker `gpu/ny_caption_generation_service.py` too.
Main owns disjoint `rohin224_caption_adoption` and P3 service deployment.
Turing/Main coordinate P3; Jason/Main control node2GPU6.
Main assigns/checks the base inference GPU on ovx4. This worker performs no life
stop, service switch, pinned-source hot-swap or GPU launch in this implementation.
Judge candidates on ovx5 continue untouched. No historical caption resubmission.

## Implemented and CPU-tested, not live-loaded

- Freeform named/numbered scenes and multiple scenes; no mandatory JSON,
  Scene/Direction/Count/Caption fields or fixed guess count. Optional Count is
  advisory. Real two-caption Scene1 routing does not count closing commentary.
- Exact-source latest own committed THINK salvage when ACT needs clarification;
  ACT/THINK labels, literal spans and hashes retained; no invented caption text.
- New native client renders actual feedback before LEARN, then requests a new ACT
  in the same opportunity if clarification is needed. At most three ACTs total,
  common declared repair allowance, tokens charged once. Exhaustion ends the
  opportunity, not the life; unknown dispatch is never blindly retried.
- One persistent controller/backend/scorer per condition for24+ opportunities;
  history/state/pending requests survive restart. Source/plan/backend changes do
  not masquerade as continuous state. Hourly attempts/optional planned counts/
  parsed/fault/scored/accepted/novel and ACT/THINK tokens are separately collected.
- Standalone-generation validator/callback: `generation_origin.py` and
  `adapters.SocketScorer`. Native API: `SERVICE_API.md`. Standalone wire contract
  and Main integration: `GENERATION_API.md`.
- `adapters.BaseBackend` reuses the verified FrozenBase loader/generate methods,
  never the old one-shot fixed-format prompts. Plain base is no-LoRA/no-learning.
  Frozen C2 inference is NOT an unparented learning cohort. Native node2GPU6 must
  supply actual RESPONSE/COMMITTED/ACT journal evidence.

Top50/65 + relevance + novelty remain unchanged. Safety/token bounds remain.
Freeform captions are chunked internally through the legacy growth allowance;
every validated caption is dispatched without rejection/drop for its count.
Actual chunk ranges/feedback and any safety-interrupted remainder are recorded.
Direct legacy CaptionActionPolicy callers remain unchanged. Controller budgets:
THINK384/ACT768, prompt2048, common three-ACT repair allowance. Native token caps
remain its actual pinned runtime config; receiving operators must verify/report
those config values before claiming matched token budgets.

## Adoption and privacy

CPU code/tests do not prove live deployment. Turing/Main preserve full game,
novelty and replay state at an owner-chosen completed scorer boundary, coordinate
one endpoint switch, and report new actual client/source and scored feedback.
An old pinned native client can use new freeform server parsing but will not gain
same-opportunity retry until its own safe source adoption.

Archive public source/docs/aggregate receipts only. Exclude runtime `private/`,
service `attempts/`, `SESSION_STATE.private.json`, private panels, transcripts,
generations and optimizer files. Bundle here is code only, not a live snapshot.

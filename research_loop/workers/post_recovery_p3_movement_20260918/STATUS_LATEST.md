# P3 post-recovery movement — September 18, 2026

## Finding, not a liveness claim

**The interface delivers feedback and adaptive parent turns, but the inspected
ACTs do not produce substantive captions or apply the delivered correction.**
Only **three** committed post-LOAD ACTs existed at the caught-up journal cut
**21:32:38 UTC / record5534**. The requested5–10 were not yet available. No older
failed-tail ACT is counted. Attribution and parent-ledger checks finished at
21:36 UTC; this is a fixed observation cut, not an assertion about later output.

The unchanged P3 retry is LOAD5317, PID699464/start33078516, original journal
`0727d448bca644bfa64f1a1f65c1f21f`. No new learner, parent, publisher, scoring call,
row filter, native source/admission change, lease change or signal was made.

## Actual ACTs

| Cycle | ACT / finished UTC | ACT REQUEST → COMMITTED | Generated / prompt tokens | Substantive captions, manual | Actual result |
|---|---|---|---|---|---|
|154|5329 /21:00:57.480|5328→5330|512 /8264|0|4 planning fragments parsed/scored; ranks65,65,65,64 of65; all rejected|
|155|5410 /21:14:04.684|5409→5411|512 /7271|0|No judgment: scene not unambiguously identified|
|156|5491 /21:27:50.147|5490→5492|512 /6876|0|No judgment: scene not unambiguously identified|

All three report `truncated=true`: **1536 generated ACT tokens**, each at512.
Raw lengths are2892/2884/2867 characters and435/435/431 whitespace words.
These are token-array lengths, not estimates from character counts.

Manual reading of the complete raw ACTs finds repeated work-splitting,
waiting/review plans, and promises to write later—not literal cartoon captions.
This is a source-bound manual judgment, not an automated semantic filter or
general quality detector. No training rows were removed or normalized.

Parser counters are separate: candidate lines14/15/15; recovered fragments4/0/0;
unparsed lines10/15/15. All three report a format fault. The parser's
`no_caption_act=false` is **not** evidence of a substantive caption.
Accept rate is **0/4 actually judged recovered fragments**, not0/3 ACTs and not
0/4 genuine jokes. Two of three ACTs received no judgment, not low humor scores.
The four scored fragments are `repeat=false`, `replayed=false`; each source is
counted once. No historical rescoring notice, cached replay or reference-panel
caption is counted as a new attempt.

## Source-bound feedback delivery

| Source ACT | Tool inbox | INBOX → first rendered REQUEST | Subsequent ACT with that feedback |
|---|---|---|---|
|5329|`51fd8d75fcdf415ba8c2a88fe549df67`|5336→5338|5410, via REQUEST5409|
|5410|`219028825039491eaff05c07bb81cbf9`|5417→5419|5491, via REQUEST5490|
|5491|`03f5548ed3f741a5b5e8bea1cdf2aaa9`|5498→5500|Not yet in this cut; first render is LEARN|

Each Tool publication is checked against its immutable projection and RESULT,
the canonical RESPONSE hash, and exact unchanged `document.response.raw`.
Actual REQUEST message text is matched, not merely an INBOX or ACT-service
receipt. External text remains masked. Full hashes are in `ATTRIBUTION.json`
and `DELIVERY.json`; raw private targets are not published.

The RESULT→session→loaded-listener chain identifies scorer PID443523 and its
bound prior configuration. Its referenced current judge runtime hashes to
`0bcd17e266defc772855501a1da02286ce83c80b975e081eb0acfa9e67239c3f`.
**Limitation:** RESULT does not embed an immutable per-attempt adopted-judge
epoch. Current configuration bytes alone do not prove historical in-memory
judge bytes. Thus own-attempt attribution is verified; exact adopted-epoch
attestation remains incomplete. No panel contents or sealed scores were read.

## Does the strong parent respond?

Yes, but delivery is not successful child uptake. Original-ledger SOURCE,
API_REQUEST and RESULT hashes were checked; these turns request `xhigh`.

| Parent turn | Authenticated source actually used | Delivery / next ACT | Response to failure |
|---|---|---|---|
|315|Preserved5310, before this sample|INBOX5319→REQUEST5321; ACT5329|Names planning instead of caption; asks for a literal scene line|
|318|ACT5329 +LEARN5339, including Tool at5338|INBOX5398→REQUEST5400; ACT5410|Names all four failing ranks; changes dialogue to a warning-label approach|
|319|**THINK5401**, not later ACT5410|INBOX5424→REQUEST5481; ACT5491|Names missing warning label; changes to a bank-product-name approach|
|324|ACT5491 +LEARN5501, including Tool at5500|Published `9c49f6912e96409991bb2fdbde0387e6`; **render pending at cut**|Names scene-identification failure, distinguishes it from humor judgment; changes to a reversed financial obligation|

Parent319 was based on an earlier THINK, so it must not be described as reacting
to ACT5410's later Tool verdict. Parent324 is an existing parent's real
publication, not this sidecar's intervention and not a proved REQUEST/render.
Parent315's old source is ledger-bound but outside the incremental post-LOAD
journal window; no fresh old-tail audit is claimed here.

## Correction evidence and limits

In the **two next-ACT opportunities after own feedback**, neither5410 nor5491
identifies its specific delivered failure and applies it to a literal caption.
Both instead assert that feedback has not arrived despite the matching Tool
message being present in their actual ACT REQUEST. The bounded ACT trace
supports **level0 only** (feedback exposure), not level1 specific correction
identification, level2 application, or level3 later reuse without reminder.
This is not a claim about every THINK/LEARN response, permanent inability,
learning causality, or corruption cause. The final Tool receipt has no later ACT
in this cut, so there is no invented third correction opportunity.

The proximal failure is observable planning repetition and missing literal
caption/scene selection. Transport loss is not demonstrated. A further
elicitation inconsistency is visible in REQUEST5490: the retained operator
template demands Scene/Direction/Count/Caption fields, whereas actual results
use `R223_FREEFORM_CAPTION_QA_V1` with `planned_count_required=false`.
This is a possible prompt confound, **not** evidence that a valid caption was
rejected for formatting or that fixing that template would solve repetition.
Native source was not changed.

## Next discriminating intervention — proposed, not sent

Use the **existing sole parent** after its already-published324 turn is accounted
for; do not add a second publisher. One short observation can contrast the last
actual no-judgment receipt with the child's claim of missing feedback. Ask the
child, in its own words, to distinguish scene-identification failure from an
unfavorable humor rank, then write one literal caption for one explicitly chosen
scene. Do not supply the joke or introduce a required answer schema.

Predeclare separate observations: (1) does the next own response recognize the
actual Tool result; (2) does the next ACT contain a literal caption; (3) can the
unchanged parser route it; (4) what judgment actually returns. Recognition
without a caption narrows the issue toward execution/elicitation; a caption
without scene routing isolates interface use; a routed rejected caption exposes
creative performance. Continued planning falsifies success for this probe.
No outcome or causal conclusion is assumed in advance.

No live repair or extra corrective turn was warranted on this evidence. The
only repair is to this new audit's cache-input digest bookkeeping, with focused
CPU regressions. Learner, parent and feedback services were left untouched.

## Validation and publication

`python3 -m unittest discover -s research_loop/workers/post_recovery_p3_movement_20260918 -p 'test_*.py' -v`

**12 tests PASS**, including wrong journal/LOAD, gaps/hash breaks, exact origin,
raw preservation and rejection versus no-judgment. This is audit validation,
not a claim that scientific outcomes improved. `MANIFEST.json` lists every
published path/hash; private evidence and operational paths remain excluded.

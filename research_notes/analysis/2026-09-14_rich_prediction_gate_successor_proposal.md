# Rich prediction gate: prospective successor proposal

2026-09-14. **Proposal only; no implementation, launch, fit, or v1 rescoring.**

## Evidence and diagnosis

Inspected frozen source `803f59c809d836f60f7a22b57a75b4d045626994`,
`organism_v6/experienced_event_rich_trajectory.py` (SHA256
`ed0e59ed9719908f616bfd57d5b27c68ae58ec9cf45a8765687569bed1b3fb0d`),
and collection protocol `research_notes/analysis/2026-09-14_rich_trajectory_collection_protocol.md`
(SHA256 `339c25c05cdb1bd6ba07bfd22520c68df6f23117fed0627cb245e23c6ba2bd2f`).
Read Rohin69 and Builder's stage-specific interpretation in
`research_loop/COORDINATION.md` (18:50/18:53 UTC).

Main reports terminal TEACH stages with zero candidates, dominated by missing
literal `PREDICTION:`. This memo checks one raw example, not the full reduction.
Stage completion is not task success. In `_collect`,
`_grounding` runs **before returning the action projection**. Its required nonempty
line beginning exactly `PREDICTION: ` can throw and end the episode without executing
an otherwise parseable command. Conversely, the label plus generic prose passes
that check: it does not establish useful prediction or grounded explanation.
Identifier membership likewise does not verify relations or factual truth.

### One exact terminal-capsule sample

Verified local `gpu_artifacts_local/astra_rich_collection_terminal_20260914_attempt1/terminal.tar.gz`
SHA256 `2d7a387dba0006b7b066f0d41459a017ce2b0059c48c269f8c90297e76c905eb`.
Within its extracted `astra_rich_collection_20260914_attempt1`, sampled
`shard0/teach/CALL_000.json` (SHA256
`d973282a9f8b10c877a19864fef20afb054bc29c40be203fd12950201a9573a4`).
Exact `response.raw`, with no terminal LF:

```text
RATIONALE
The current node is N_POVU3M5Z6U, and the goal is N_OAJBB2KLL4. The relevant ports are P_7Y5MMK2CKE and P_QFYO2CGIQR. The event E_7UNHFUTYI6 has not been read yet. Reading this event might provide information on the state of the node or the path to the goal.

ACTION
READ EVENT E_7UNHFUTYI6
```

Native response: terminal=true, truncated=false, error=null; 317 prompt tokens,
105 generated tokens including EOT. Verified messages/response/error exactly
match capture0 in `shard0/teach/LESSONS.json` (SHA256
`443f8929d3e88c45d675c5c073984984dc32e2d49afd7f32b45d65065e33ae35`),
and the saved action span equals that raw READ command. The address is publicly
listed and uninspected. Capture0 records `explicit_prediction_line_required`;
episode0 ends `actor_callback_error`, with zero memory reads and zero routes.
The action was **not executed**. The prose identifies uncertainty but its forecast
is broad: this is neither a retrospective content pass nor evidence the remaining
trajectory would succeed. The successor should execute such valid actions while
keeping content admission separate; the original failure remains unchanged.

## Smallest successor delta

1. **Separate execution from content.** Keep native prompt/provenance checks,
   terminal/token/context bounds, exact single-envelope/action extraction, and
   unchanged environment legality/turn limits. Malformed, ambiguous, nonterminal,
   or integrity-invalid responses still cannot execute. After successful extraction,
   record rationale findings separately; missing prediction labels, unsupported
   prose, or generated guidance echoes must not throw from the actor callback.
   Return only the exact action slice. Actual prompt leakage remains an integrity
   failure, distinct from a child's generated echo.
2. **Separate accounting.** Record `execution_error`, content findings, actual
   transitions, and `action_complete` independently. The latter retains the existing
   six-command/source-plan match, four reads, two commits, and final-goal checks,
   without conflating content rejection. Keep failed and successful attempts alike.
   No repaired response, synthetic continuation, retry, or new observation.
3. **Natural-language expectation, not a password.** Prospectively amend the
   articulation instruction to request a checkable next-feedback expectation,
   explicitly distinguished from an observation; a literal heading is optional.
   Log heading presence diagnostically. Do not replace it with a synonym whitelist
   or claim automatic semantic understanding. Retain existing source/visibility
   restrictions and non-recurrent, parent-free public histories.
4. **Admission remains outcome AND content.** Use the fixed rubric below to review
   every action-complete TRAIN episode; record pass/fail/unresolved and supporting
   raw spans per turn. Unresolved is not admitted. Admit all six rows only when all
   six pass. TERSE/RICH/RICH_ACTION_ONLY share exactly those episode/call IDs;
   execution-only successes are not an automatic TERSE fit pool. Report execution,
   review, candidate counts, and `complete_corpus` separately; `fit_ready=False`
   until a separate content-review/fit contract authorizes a write.

## Content floor: stage-specific, not length

| Stage | Required useful content, grounded only in the pre-action public prefix |
|---|---|
| READ, including the first | Identify the listed uninspected address or an unambiguous reference, what remains unknown, and why inspection helps choose a goal-directed path. Expect retrieval/feedback, not knowledge of an unread edge or receipt. Later reads distinguish already observed information from remaining uncertainty. No requirement to justify an opaque address using unavailable facts. |
| First ROUTE | Connect observed edges from CURRENT through the chosen port/intermediate node toward the requested goal. Explain the relevant choice rather than merely list IDs. Predict this hop's intermediate outcome, not premature final success. |
| Final ROUTE | Use the actual preceding transition and observed remaining edge to connect CURRENT/port to the requested goal; forecast the next goal-reaching feedback without inventing a receipt. |
| CRITIQUE | Cite an actual public success, discrepancy, or unsupported inference and propose one relevant next check. Failed episodes remain eligible for this separately reviewed candidate pool; critiques never certify actor targets. |

Reviewers receive TRAIN prior-public-prefix/actual-target pairs, without coach text
or PROBE scores. Outcome checks use separately identified actual transition
records; later feedback cannot justify a pre-action factual claim. Padding,
first-person wording, a heading, or generic “I expect a reply” is not sufficient.

## Required prospective tests and boundary

- Valid action without the literal label executes; equivalent explicit forecast
  can pass review. A labeled but vacuous explanation executes but fails content.
- Unread/false factual assertions reject content without fabricating feedback;
  truncated, ambiguous, malformed, or prompt-drifted responses never execute.
- First READ cannot require hidden facts; first ROUTE cannot claim final success;
  final ROUTE must use actual CURRENT. Test valid/invalid examples at each stage.
- One content-rejected turn excludes its whole six-row episode from all three
  forms, not from execution denominators; other qualifying episodes remain.
- Replay rejects altered action spans, content decisions/evidence, prefixes, or
  row membership. Preserve exact raw targets, masks/EOT, and all critique attempts.
- Frozen v1 fixtures/hashes and rejection results remain unchanged. Bind a distinct
  successor schema/run/protocol before calls; retain four phases and existing caps.
  No v1 salvage, favorable-shard selection, automatic fit, or equal-compute claim.

This would implement Rohin69's richness **and** outcome floor for admission while
measuring execution independently. It does not establish that richer prose is
true reasoning or improves transfer; those remain prospective questions.

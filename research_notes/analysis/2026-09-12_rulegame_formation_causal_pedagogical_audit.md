# RuleGame minimum formation: fresh causal and pedagogical audit

**Date:** 2026-09-12 16:44 UTC
**Scope:** completed formation only, at remote root
`/localhome/local-rohing/astra_diagnostics/astra_rulegame_minimum_20260912_attempt1`.
This is an independent read-only audit and recommendation. It changes no
builder source, experiment, adapter, job, GPU allocation, active v8 state,
architecture, or claim. It does not pause Astra under `AGENTS.md`.

## Verdict

**Nothing from this root is valid to write.** The parented arm produced no
apply execution and therefore no child event record. The active-control arm
produced two structurally and factually faithful event records, but both of
its parent/control interactions violated the prospectively selected neutral
control contract; the process arm also has a paired material shortage. The
root is already terminal as `MAIN_DECLINED_MATERIAL`, with no `write/` or
`evaluation/` directory. The two faithful control records are valid raw
diagnostic observations, not admissible training rows for this comparison.

The formation is a useful, trustworthy failure localization. It is not a
parenting result, a learning result, or a THINK--DREAM--SLEEP relay. Its main
failure is the child/action interface, followed by invalid treatment/control
realization and weakly grounded parenting. The immutable/replay/cleanup layer
worked as intended by refusing to salvage those failures.

## Evidence and custody checked

I read the operating contract, the RuleGame minimum protocol and direct source
and tests, the thesis/parenting/TDS contracts, and builder entries
`research_loop/COORDINATION.md:4362-4393`. I then inspected the named remote
root through `gpu/ovx2_ssh.sh`, read all 32 raw request/response pairs and the
event stream, and performed read-only file/existence/hash checks. I did not run
the diagnostic, model, tokenizer, trainer, or any GPU command.

Remote byte anchors:

| artifact | SHA-256 / fact |
|---|---|
| `plan.json` | `9611a98567c8d0465a4c4072e6bab80cc6a91b0342099da99e67d2d75de73231` |
| formation manifest | `d4a157f3a4e39a46dad20282e14192663b6d0320990ec80818d6a7ad1160ef68` |
| `events.jsonl` | `a973528330a6a8c2540efd04ca9194b96c71848e4ac0885d443955cc23cef4af` (32 rows) |
| formation `result.json` | `7c2a1f3abf23800dc6e89e36a13c6dcac6016640841278d917053f085b0fabd2` |
| `material/main_audit.json` | `6c2bbc989b70592ebb9fd2d88b0f712048f43ce8b7b0ae2f20b3ff0a8fd83eb2` |
| `material/result.json` | `614288d1e0f01e4778649753f701aff28de56c84f9f1df7c3ee33c080afe96ab` |
| later stages | `write/` absent; `evaluation/` absent |

The formation capture contains 70 manifest-bound files. Its replayed
provenance report is `ok=true`; native backend identity says no adapter; the
owned backend closed; the supervisor exited zero after 169.634 seconds and
reports the owned group and GPU empty. Model identity remains exactly what the
plan says: local byte pins, not official base-origin authentication. These
facts support custody and execution, not semantic validity.

## What actually happened

All eight tasks have `valid_quiz=false`, `terminal=protocol_invalid`, and a
recorded quiz accuracy of zero. The zero is therefore a missing/invalid quiz
endpoint, not evidence that the child answered all quizzes incorrectly.

| arm / lesson | pre | parent/control realization | apply and records |
|---|---|---|---|
| P / rule 0 | Three actual TRYs; the fifth response emitted several ACTs and fabricated `[OUTCOME]` lines, so no scored quiz. | Generic advice to scope observations; no hidden answer, but no concrete evidence-linked diagnosis. | First response was `PREDICT: T` plus `TRY: 1,2,3` without `ACT:`. No world execution and no record. |
| P / rule 1 | First response had `PREDICT: T` plus noncanonical `TRY: 1,2,3`; no execution. | Falsely diagnosed failure to predict, then suggested trying `4,5,6`. | Child followed the suggested triple but again omitted `ACT:`. No execution and no record. |
| A / rule 0 | Three actual TRYs; the fifth response emitted multiple ACTs, so no scored quiz. | Praised the child and asked it to restate a nonexistent quiz outcome and what it learned, not merely the neutral acknowledgment. | One actual TRY produced faithful record call `0020`; the next wake response emitted multiple ACTs. |
| A / rule 1 | First response used noncanonical `TRY:`; no execution. | Asserted that an unexecuted triple had been tried and asked for more experience content, rather than neutral acknowledgment. | Three actual TRYs produced four record calls total across A. Calls `0020` and `0028` were faithful; `0026` and `0030` incorrectly wrote `matched` for a mismatched prediction. The fourth wake response emitted multiple ACTs. |

Totals are P: 0 apply TRYs and 0 records; A: 4 apply TRYs, 4 record
generations, 2 exact event-faithful records. The complete run used 20 wake,
four parent, four restatement, and four record responses. Actual exposure was
not closely matched: P versus A parent inputs were 2,275 versus 521 native
tokens, parent outputs 167 versus 63, and wake calls 8 versus 12. The protocol
properly called this opportunity matching rather than exact realized-compute
matching, but the observed imbalance is too large to ignore in any causal
reading.

There is also pre-treatment response instability. P and A rule-0 pre calls at
tick 3 had the same prompt SHA-256
`885efc3cada8c1db560927bcfbabd3e25a6cf9f7f72b88ebbb1023e6b8af9b72`
and the same sampler seed `311336830`, yet emitted different triples. Because
arm identity is only receipt metadata and is not in the backend prompt, that
divergence cannot be attributed to parenting. Its exact backend cause is not
identified here; the demonstrated fact is that prompt-plus-seed did not make
these sequential samples an exact pair.

## Exact failure causes

1. **The native motor contract failed before the pedagogical question could
   be measured.** The strict parser requires one canonical line beginning
   `ACT: `. Four tasks instead began with `TRY:` and four ended when the model
   generated multiple ACTs or an entire imagined interaction in one response.
   Strict rejection was correct; interpreting intended actions would be
   post-hoc evaluator repair.

2. **Raw child text and authoritative world text were not separated in the
   parent's view.** Child responses themselves emitted `[OUTCOME]` strings,
   including unexecuted and sometimes false outcomes. `play_task` passes the
   joined transcript to `parent_turn`; the parent does not receive a typed
   view distinguishing executed environment rows from child-authored outcome
   claims. The durable event log distinguishes them, but the adaptive teacher
   prompt does not. This makes grounded diagnosis unreliable.

3. **The process parent missed the realized deficit.** In lesson 1 the child
   did state `PREDICT: T`; the actual failure was the missing `ACT:` marker.
   The parent instead said that no prediction was made. In lesson 0 it gave a
   generic scope lesson without tying the correction to a verified line or
   outcome. Thus the treatment was conditional on text in the weakest sense,
   but not a correct, evidence-bound adaptive intervention.

4. **The active control was not the declared control.** Both A turns asked for
   task/experience reflection and made unsupported statements about a quiz or
   executed attempt. That is process-like content rather than a neutral
   acknowledgment whose acknowledgment alone is restated. The control defect
   precedes selection of its two faithful records.

5. **Paired material was impossible even under a permissive content audit.**
   The selector requires two eligible apply records per arm. P had zero. A had
   two. No quiz gate is part of this minimum selector, so the absence of valid
   quizzes would not rescue or further reduce P; the paired-shortage condition
   alone is terminal.

6. **The run contains source atoms, not a DREAM contribution.** The explicit
   record prompt mechanically asks the child to serialize one verified event.
   It does not ask the child, before any answer-bearing blueprint, to select or
   propose a reusable link, schema, scope, or storage decision whose later
   value is checkable. Under the project TDS contract, a joined ledger is an
   authentic SLEEP source but is not evidence that DREAM contributed
   intelligence (`2026-09-12_think_dream_sleep_minimum_decisive_program_audit.md:39-52`).

7. **No SLEEP or parent-removed test happened.** The material gate declined
   the root, no corpus was emitted, and no fit, reload, OFF comparison, or
   readout occurred. Consequently neither persistent write nor transfer is
   observed.

## Does this parent match Rohin's strongest adaptive-parent intent?

**No.** It is a small baseline parent call, not the strongest adaptive design
already present in the repository.

The launch contract asks for the strongest relevant existing parenting design
and a matched control (`ASTRA_LAUNCH_PROMPT_2026-09-12.md:227-240`). The
repository's first-ranked adaptive variant is contingent scaffolding: vary
directiveness with verified success/failure history, ask when the child is
close, name a category after one failure, and state a correction after repeated
failure (`organism_v6/PARENTING_MENU.md:17-29`). Process feedback is supposed
to cite the child's goal/prediction, one concrete gap, and one next move
(`PARENTING_MENU.md:70-80`). The wider thesis targets failure-to-causal-
diagnosis-to-reusable-child-lesson, discretionary storage, and child-authored
organization—not mere teacher-conditioned JSON serialization.

Here the parent sees one noisy raw transcript, no typed actual-event view, no
verified performance/history, no contingent ladder, and no factuality gate
before delivery. The realized parent made one false diagnosis and one generic
diagnosis. The comparison is against a semantically failed praise/reflection
control, not a dose/content-matched noncontingent or shuffled-feedback arm.
Finally, the write target would have been two event JSON objects, not a learned
decision about what deserves consolidation. This is useful interface scouting,
but it is below Rohin's strongest adaptive-pedagogy intent.

## Exact maximum defensible claim

> In one frozen-base Qwen2.5-7B RuleGame formation, the sealed harness
> faithfully captured and replayed 32 generated responses and their actual
> world executions, then stopped before training. Every task terminated on a
> strict action-protocol violation and no valid quiz was produced. The process
> arm produced no apply event or record; an invalid active-control treatment
> produced two exact child-formatted records of actual apply events under an
> explicit record schema. This demonstrates only limited prompted event
> serialization plus a correctly functioning fail-closed custody/selection
> path—not effective or adaptive parenting, a matched causal parenting effect,
> child-authored DREAM, SLEEP learning, persistence, transfer, H1, or H2.

Do not shorten this to “parenting failed”: the run never acquired a valid
process-arm apply event with which to test parenting. Do not shorten it to
“the child cannot record experience”: it recorded two control-arm events when
given an explicit schema. Do not call the recorded zero quiz fields task
failure rates.

## Smallest aligned next formation

Do not salvage or reinterpret this root. A new versioned, development-only
formation should test one competency: **verified failure/outcome ->
evidence-bound diagnosis -> discretionary reusable child lesson**. Keep the
same frozen base and LoRA-only SLEEP path, but change the interaction before
spending another fit:

1. **Make THINK executable without replacing it.** Use separate child THINK
   and typed single-action slots. The child first predicts/reasons in its own
   words; a bounded structured action slot then carries exactly one TRY or
   quiz action for execution. Only the harness may emit authoritative outcome
   rows. Child-written strings resembling `[OUTCOME]` remain raw thought and
   can never enter the parent's verified-event view. Prove this interface on
   fresh development-only IDs before formation; do not tune it on the sealed
   readout panel.

2. **Use the actual adaptive parent and a causal control.** The treatment
   parent sees a typed table of only executed actions, predictions, public
   outcomes, parse failures, probe diversity/calibration, and recent
   development history. It uses the repository's contingent ladder and gives
   one evidence-citing process intervention, never the hidden rule or readout
   information. The control receives a presealed yoked/deranged process
   intervention from the same target-blind feedback bank at the same schedule
   and token envelope, not generic praise and not a request for task
   reflection. This isolates contingency/information from contact and style.
   A factual or control-contract violation terminates the pair; no parent
   regeneration or favorable selection.

3. **Require a real child DREAM decision.** After the apply events and before
   any held-out blueprint, remove the raw parent message and ask the child,
   once per lesson, whether to store zero or one lesson. A candidate must cite
   its own execution IDs, distinguish observation from inference, state scope,
   and name the proposed reusable relation or process move. This is a
   discretionary organization decision. A mechanically filled event JSON is
   supporting provenance, not the DREAM endpoint.

4. **Keep the formation minimal and paired.** Two fresh lessons per arm are
   sufficient for a kill scout if each permits enough verified pre/apply
   actions to expose a process error and one later DREAM opportunity. Freeze
   fresh development IDs, all caps, the two-per-arm threshold, the factual
   predicate, and all rejection reasons prospectively. Require two qualified,
   distinct child DREAM candidates in **both** arms. A shortage, invalid
   parent/control turn, invalid action interface, or copied teacher span ends
   at formation with no replacement tasks and no write.

5. **Let SLEEP compile; do not let it invent.** If and only if formation
   passes, deterministically compile the qualified child candidates, with
   immutable action/outcome/parent-call provenance. Train only the verbatim
   child-authored candidate span; exclude parent/control text, restatements,
   prompts, hidden truths, evaluation panels, and wrappers from supervised
   tokens. Parent-influenced paraphrase is allowed only as explicitly sourced
   child compression; direct copied lesson text is not. Keep an actual
   SLEEP-off/shadow condition and sterile reload.

6. **Read out the competency, not just quiz score.** On fresh rule families
   and task IDs, delete the parent, nursery text, restatements, ledgers, caches,
   and recall state. With only the neutral action/post-outcome interface, test
   whether the child independently predicts, selects what merits storage, and
   writes a grounded reusable lesson; then test the downstream utility of that
   material against the yoked child and no-write baseline. Quiz accuracy is a
   secondary task endpoint. A minimal TDS mechanism claim additionally needs
   a matched `DREAM_NULL`/derangement and `SLEEP_OFF`; parenting versus yoked
   control alone does not identify DREAM necessity.

This is the smallest justified repair because it directly attacks the three
observed blockers—motor serialization, ungrounded/noncontingent teaching, and
the missing DREAM decision—while preserving the public action/outcome source,
child-owned learning bytes, deterministic provenance-gated SLEEP, parent
removal, and held-out isolation. More RuleGame lessons, seeds, fits, or prompt
sweeps on the present interface would repeat a broken integrated run rather
than answer the causal question.

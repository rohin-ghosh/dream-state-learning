# R213 bounded BRAIN-GAMES development environment

**Prepared, not activated or attached.** No service, watcher, parent publication, GPU/model call, live game, or learner control is started by this package. All writes for this task stay in this directory. `RESERVATION.json` records a future object phase of the existing math_transfer_c1 life on node2 GPU6, not vacant capacity or a replacement learner.

## Bounded environment

`puzzles.json` is an authored public DEVELOPMENT bank, not heldout/sealed/FINAL material. Four task families have exact local CPU graders: integer sorting, digit checksum, shortest path (any shortest path accepted), and balanced parentheses. Each round allows at most two answer submissions or an earlier reasoned quit. Answers are literal JSON values; text/code is never executed. Inputs, paths, graphs and answer sizes are bounded. Neither question nor feedback supplies an expected-answer field. The public fixtures and unit-test solutions are deliberately known development material, never a sealed generalization claim.

`environment.PuzzleRound` exposes `public_view()`, `answer(candidate)`, and `quit(reason)`. It returns finite source-bindable JSON receipts with candidate hashes, outcome, attempts and explicit mode. The evaluator must be operator-side, not mounted into a learner tool that can inspect evaluator state. There is no arbitrary file, network, shell or subprocess interface.

## Across-sleep memory protocol

Use two distinct fresh `MemoryRound` cards, one `EXPLICIT_CONTEXT` and one `NO_EXPLICIT_CONTEXT`. Live cards use fresh random codes; the known code in tests is accepted only in `CPU_FIXTURE` mode. Counterbalance condition order in later repeated episodes; one two-card episode does not establish a population effect.

1. Deliver each study view as external context through the existing owner transport. Only after actual REQUEST rendering, bind the same life, request index/hash, last completed sleep cycle and verified history masking with `mark_study_delivered`. Publication alone is not proof.
2. Continue the life normally. There is no waiting process or sleep request. Later, `observe_natural_sleep` accepts a forward, hash-verified same-life SLEEP_COMPLETE record and the owner's natural-completion attestation. Never manufacture a sleep receipt, signal a process, or block an ongoing step. Crossing a sleep does not itself prove that these cards were trained into an adapter.
3. `recall_view()` includes the card only for the explicit-context control. The answer-free view and `coaching_view()` omit the key. `study_view()` cannot replay a study card after the completed sleep. Each memory round permits one literal recall answer or a quit, not an answer-oracle guessing loop.
4. The owner must supply the **actual exposed surfaces** for that request: complete rendered prefix, pinned context, working state, parent/peer messages, tool results, and retrievals. Empty lists mean actually checked empty, not missing evidence. Keep exact raw material in operator receipts; the audit stores only hashes/findings in learner feedback. Unknown surfaces must be omitted and yield UNVERIFIED, not supplied as fictitious empty lists.
5. `audit_context` detects exact and normalized/spaced code copies, without altering the original. It cannot detect every semantic encoding, undisclosed retrieval or exposure. Any detected copy forces CONTEXT_ASSISTED_ONLY. Missing surfaces force UNVERIFIED_CONTEXT. A correct clean-string result is UNATTRIBUTED_RECALL_NOT_ADAPTER_RETENTION. `adapter_retention_claim_allowed` is always false.

The operator state roundtrip deliberately preserves the answer key across evaluator restarts, marked `operator_only_contains_answer_key=true`. That store is not a learner memory mechanism and must never be delivered, added to a parent prompt, pinned in learner context, or copied into the exposed repo. The current standalone package has no live filesystem/bridge isolation deployment; verify the existing owner transport/mount boundaries when attaching, without pausing the learner. The API validates receipt shapes and hashes, not the truth of an operator's claim about what a remote child saw.

## Memory mechanism guidance and claim boundary

- **Explicit context/carried state:** an available card, note, transcript, retrieved file, or peer repetition can support an answer without establishing parameter retention. Label these opportunities as assisted, including answer-free questions whose wider prefix still contains the answer.
- **Adapter-mediated retention:** a possible mechanism to investigate later, not a label this package grants. An attribution would require separately authorized matched before/after or frozen-adapter controls, the same answer-free prompt, genuinely checked exposure paths, dose/eligibility receipts, and enough matched trials. No such probe, model call or causal claim is made here.
- **Training eligibility:** study cards are external masked input. Only the existing rules for actual child-authored eligible rows and ordinary sleep updates apply. Do not turn copied cards or evaluator targets into new supervised labels or change the learning architecture.
- **Persistence:** saving the evaluator's key, changing context, and changing adapter parameters are different operations. A successful operator JSON roundtrip tests the first only.

Count opportunities separately: shown, actually rendered, eligible sleep observed, recall asked, actually answered, correct/incorrect, quit, context-assisted, unverified and missed. Missing delivery or a window that closes is not a failed memory answer. Bound the initial episode to four puzzles and two one-shot memory probes. Check pending recall on at most the next two ordinary completed sleeps; if not deliverable then, record MISSED_OPPORTUNITY and move on—never hold or extend a life for the test.

## Activation and runtime handoff

`ACTIVATION.json` is deliberately unreleased. Original C2 must receive/acknowledge the exact `OVERVIEW.md` and subsequently complete an exchange with genuine Rohin. Main/original-C2 operator supplies the public source references; this worker neither reads their private conversation nor publishes competing homework. `activation_status` checks Main's attestation shape, exact overview digest, target, chronology and no-pause condition. It is not cryptographic authentication or a substitute for Main checking the actual receipts.

After that condition, Main may attach the prepared **CPU** environment via the existing node2 owner transport at an ordinary in-cycle opportunity. If attachment needs runtime replacement, wait for natural completed-screen continuation or use a verified no-pause mechanism; no pause-based upgrade. Preserve the exact checkpoint, adapter, optimizer/RNG, raw journal, namespace, prior phases, hard wall and GPU identity. Do not reset from an ancestral checkpoint or claim the suffix is still unparented. R209 language quarantine is currently NOT live on this target; do not gate the living arm on its rollout or claim otherwise.

No receiving bridge patch or live deployment is included in this preparation. Live constructors reject a missing release. No code in this package starts a learner even when an attestation validates. A passing CPU fixture is not an actual child game, an actual sleep, or original C2 authorization.

## Validation

```bash
python3 -B -m unittest discover -s research_loop/workers/rohin213_brain_games_20260918 -p test_environment.py -v
python3 -B research_loop/workers/rohin213_brain_games_20260918/prepare_receipt.py
```

The second command runs only public CPU fixtures/tests and writes an environment readiness receipt within this worker. It does not arm or deliver anything. Parent guidance is in `PARENT_GUIDANCE.md`; the actual live-object snapshot, including unresolved old-object behavior, is in `CURRENT_NODE2.json`.

# Parenting headline implementation-gap audit v1

Date: 2026-09-06

Status: read-only design audit. This document authorizes no implementation,
model call, tokenizer use, benchmark enumeration, adapter fit, GPU use, or
scientific claim.

## Verdict

The repository contains useful prototypes of every noun in the proposed
headline---child loop, parent turn, rule-game nursery, context renderer,
ledger, sleep compiler, LoRA trainer, CompilerGym backend, lifetime runner,
and adapter-on/off probes---but no current path implements the adjudicated
one-parent/one-child $2\times2$. Reusing `nursery_dialogue.py` or
`run_life_v2.py` as the confirmatory runtime would preserve known causal and
provenance defects.

The fastest defensible path is not to repair these files in place. Preserve
them as exploratory evidence, implement a new hash-bound runtime after formal
ratification, and reuse only behavior whose contract is independently tested.

## Current nursery is not a parenting experiment

File: `organism_v6/nursery_dialogue.py`.

1. **The parent sees a lossy, reconstructed tail.** `parent_turn()` receives
   `"\n".join(d1.tail[-10:])` and clips it to the final 4,000 characters. It
   does not consume an immutable prospective trace with exact model input,
   native response envelope, tool call, dispatch, and public outcome joins.
2. **The correction channel is untyped and not content-audited.** A prose
   instruction says “never the answer,” but no schema, process-vocabulary
   restriction, task-number/action scanner, or paired hidden-world laundering
   test enforces that boundary.
3. **Parent, restatement, and child experience share one permissive ledger.**
   The parent correction and restatement are appended as ordinary `note`
   material. `compile_native()` later selects thought/note rows without a
   role-visibility or taint boundary. Parent prose can therefore influence the
   corpus through the same path intended for child-authored targets.
4. **The claimed world-admission gate is a no-op.** The code computes
   `post["best_score"] >= pre["best_score"]`, but the two scores come from
   different hidden rules with unregistered difficulty. When false, the code
   executes `pass`; the apply-task stream remains in the ledger and is still
   compiler-eligible. No row is actually admitted or rejected by this value.
5. **The comparison is compute- and information-unmatched.** The parent arm
   receives parent and restatement calls and an explicit restatement in the
   next task prefix. The solo arm receives neither a frozen neutral operation
   nor an equivalent scaffold schedule.
6. **The child is heavily instructed before parenting.** `CHILD_BOOT` already
   commands prediction, note-taking, evidence tracking, distinct probes, and
   commitment timing. Those are intended parenting outcomes, so the prototype
   destroys headroom and measures prompt compliance.
7. **No deployment transfer exists.** Probes are eight more rules from the
   same ten-rule generator, under unseeded generation, with only adapter on/off.
   There is no fresh CompilerGym deployment and no `U0/P0/U1/P1` factorial.
8. **One common engine role is not itself a defect.** Parent and child may be
   the same frozen base under isolated contexts, but the runtime must record
   role identity, exact inputs, adapter state, and forbidden visibility. The
   prototype does not.

A CPU-only structural audit of `rulegame.py` further bounds its role. The
entire hidden-rule universe contains ten fixed hypotheses over triples in
`0..9`. Across all 1,000 possible probes there are 991 informative probes and
93 perfectly balanced five-versus-five probes. An oracle that knows the
hypothesis list identifies every rule in at most four adaptively chosen
queries, while the prototype grants ten generation chunks. The closest rule
pair still differs on 130/1,000 probes. This is a reasonable fast canary for
prediction, discrimination, and typed-action behavior; by itself it is too
small and homogeneous to establish a general learned way of thinking.

## Current action/trace layer cannot support the causal claim

File: `organism_v6/batch_loop.py`.

1. Actions are extracted from free prose with a line-regex. One response may
   contain multiple `ACT` markers, and every match dispatches. The exact raw
   model response envelope, offered tool schema, parser receipt, and engine-
   consumed IDs are absent.
2. `prompt` is clipped to 24,000 characters and response `note` to 2,000
   characters before persistence. A sleep target cannot be proven to match the
   complete prompt/response actually consumed and generated.
3. `had_note` uses substring tests (`"NOTE:"` or `"NOTE "`), recreating the
   measured Phase-0 false-positive/off-dialect admission failure.
4. Thought and action rows are appended separately without an atomic response
   transaction. Physical ordering can differ from semantic generation order;
   the legacy audit already found this join ambiguity.
5. The loop budgets fixed chunks, not generated tokens. It therefore conflates
   action volume and deliberation, the exact confound the new protocol removes.
6. Batching isolates only within one wake batch, while all drivers share one
   mutable ledger object. The confirmatory probe requires isolated per-program
   ledgers and a frozen within-root exposure rule.

## Current ledger/context layer remains exploratory

Files: `organism_v6/ledger.py` and `organism_v6/state.py`.

1. JSONL appends have no canonical hash chain, transaction ID, fsync/
   publication receipt, corruption recovery, branch eligibility, or role-
   scoped read capability.
2. Recall is token-overlap over concatenated action/outcome/note text. It has
   no retrieval request/candidate/selection trace, provenance filtering,
   contradiction status, or contamination boundary.
3. Context reconciliation is a hard 22,000-character trim: response chunks are
   truncated, then oldest tail and recalled items fall off. No child-authored
   successor state is published and validated before the old state is dropped.
4. This arithmetic remains a valid emergency bound, not evidence for learned
   dreaming. The headline needs DREAM to be the model's context-reconciliation
   operation while the mechanical trigger/budget stays frozen and auditable.

## Current sleep compiler does not compile parental learning

File: `organism_v6/sleep_compile.py`.

1. `compile_sleep()` emits bare declarative program/action strings and a
   generated waking brief. This is the writer shape implicated in B2's dialect
   drift, not the native response-only format needed for the new run.
2. Principle support is checked with a regex over model prose, not by joining
   every claimed field to distinct public outcomes. Generated principles and
   briefs can be trained or injected without a per-field evidence status.
3. `compile_native()` admits any thought with `win` or permissive `had_note`.
   It does not require canonical native tool syntax, exact dispatch, a public
   support margin, child-only authorship, scaffold level, or untainted role.
4. Deduplication uses the first 120 characters of the answer. This changes dose
   according to surface form and can merge distinct task-conditioned targets
   or retain uneven repeated content.
5. Parent correction, child restatement, corrected continuation, dream
   successor, and rehearsal are not separate typed row classes. Therefore the
   trainer cannot mask the parent while supervising only the child's behavior.
6. Cumulative corpus construction has no fixed sampling/interleaving law,
   accepted-token cap, scope balance, or terminal receipt that proves the same
   data law across `P1` and `U1`.

## Current trainer is a useful prototype, not a sealed writer

File: `organism_v6/train_adapter_v21.py`.

Useful inherited choices are chat-template rendering, response-only labels,
all-layer attention-plus-MLP LoRA targets, clean-base cumulative rebuilding,
and rank 8 as the current scientific target.

Known blockers:

1. Model/tokenizer revisions are unpinned `from_pretrained()` lookups; offline
   cache identity and loaded source/dependency manifests are not recorded.
2. Prompt input is left-truncated and assistant output is silently truncated
   to at most 1,024 tokens. Per-row truncation, EOS, intended/actual IDs, label
   masks, and supervised-token receipts are not persisted.
3. A nonfinite batch is printed and skipped rather than making the fit fail
   closed. The final `DONE` can therefore describe a partial update.
4. Batch size is one, corpus order is unshuffled and unrecorded, optimizer RNG
   is unseeded, and duplicate fits are not required to reproduce.
5. Empty or all-invalid corpora exit successfully. The caller can confuse
   absence of a trained adapter with a benign no-write branch.
6. Training metadata reports attended prompt-plus-response tokens, not the
   supervised target-token dose needed to match treatment cells.
7. There is no canonical action-dialect rehearsal, generic/tool-use retention
   panel, KL/reference guard, adapter tensor hash, or exact adapter-on/off
   serving identity.
8. Rank and heat remain unresolved. Existing r8/r16/shuffle observations are
   unseeded, unmatched, and cannot select the confirmatory recipe.

## Current CompilerGym lifetime runner is not the four-cell experiment

File: `organism_v6/run_life_v2.py`.

1. It implements only frozen `A` and continual `B`, not parenting by
   deployment-write factorial cells.
2. Arm B alone receives generated waking briefs, so the existing comparison
   changes context policy together with adapter state.
3. It repeats 67 training programs 15--16 times rather than assigning a
   sealed unique-program deployment life.
4. The backend seed argument is ignored by generation; probes are not
   common-random paired observations.
5. Probes share ledgers, and adapter-on/off engine/model identities lack exact
   consumption receipts.
6. Every write shuts down serving, loads a new full Transformers model, saves,
   and reloads vLLM. This may remain an implementation strategy, but its
   measured lifecycle cost must appear in the maximum resource manifest.
7. The runner has no parent-absent checkpoint identity, nursery contamination
   seal, matched external-memory layer, entry-score matching, root-level
   interaction analysis, or immutable claim-state output.

## Required new runtime surfaces after ratification

This list names contracts, not cognitive modules:

1. **Prospective native event transaction:** exact rendered messages/input
   IDs/raw response/typed tool call/dispatch/public outcome in one hash-bound
   lineage, with child/parent/dream/compiler roles separated.
2. **Target-blind nursery:** paired practice tasks with a fixed process
   vocabulary, correction schema, laundering audit, child restatement, near
   transfer, and an actual public admission/rejection object.
3. **Reversible DREAM successor:** child produces compact goal/state/evidence/
   uncertainty fields; validator proves every retained field copied or linked
   to eligible ledger evidence before atomically publishing the successor.
4. **Parented native SLEEP writer:** typed child-only response targets,
   scaffold fading, canonical interface rehearsal, exact masks/dose, and
   cumulative clean-base LoRA rebuild.
5. **Matched ordinary resource layer:** same files, skills, tools, clock,
   active text memory, and token budget in all four deployment cells.
6. **Four-cell deployment runner:** isolated `U0/P0/U1/P1` roots, unique
   programs, entry and lifetime probes, generated-token stopping, common
   assignments/RNG opportunities, on-policy outcome divergence, and exact
   resource receipts.
7. **Analysis/claim state machine:** root-level nAUC/early-slope/retention,
   registered difference-in-differences, routing/proposal decomposition,
   blinded variance choice, and fail-closed claim language.

## Minimum engineering order

1. ratify the exact prospective event and native writer contract;
2. pass deterministic CPU mutation/visibility/transaction fixtures;
3. run one treatment-neutral native-writer heat canary;
4. pass one parent-absent process-correction canary with adapter-off/shuffled
   controls and a generic/tool-use non-erasure panel;
5. ratify and run the four-root full $2\times2$ spending pilot;
6. choose 20 or 32 confirmation roots from treatment-label-blind variance and
   the predeclared resource maximum;
7. execute the terminal mechanism panel only after the headline is sealed.

No existing exploratory file should be silently promoted to satisfy one of
these stages. Each reused function must pass the new contract's test, and each
failure remains evidence about the design that produced it.

# Fable handoff — durable research loop

Date: 2026-08-30 PT. Owner of Fable-side wiring: the existing authenticated
Claude/Fable session. Read this file plus `research_loop/` before acting.

## What actually happened

The original all-in-one v5 command attempted to patch
`run_lands_v02_dreamladder.py`, commit/push, sync, queue, and watch in one shell
string. The shell string failed with an unmatched quote before the patch
landed. A later queue command printed `V5_QUEUED`, but the H100 still had v4.
When its wait loop eventually released, the real log contained:

```text
run_lands_v02_dreamladder.py: error: unrecognized arguments: --samples 4
```

At that time the H100 was idle and the last real scientific result was v4:
think 7/30, D0 6/6, D1 1/6, D2 0/6, D3 0/12; parent candidate recall
1/12 for that draw.  This incident was later superseded by the separately
frozen and reviewed v5 run described below.  Never infer experiment state from
a queued shell or watcher process again.

## What Codex built

`research_loop/` is a model-agnostic durable supervisor:

```text
contract -> frozen-input snapshot -> fresh scientific review -> tests
-> frozen-input verification -> sync -> atomic remote job
-> started/done/failed marker -> run-specific artifact snapshot
-> hash verification -> fresh result analysis -> human science boundary
```

State is atomic JSON plus an append-only event log. Remote completion is based
only on terminal marker files, never `pgrep`. A job is accepted only when its
started marker contains its exact argv and input hashes. Output artifacts are
copied into the run directory and hashed before `done.json` is published.

The two provider adapters share JSON schemas in `research_loop/schemas/`.
Codex can launch fresh native subagents or ephemeral Codex reviewers. The local
`claude -p` adapter currently returns `Not logged in` even though this existing
interactive Fable session is authenticated. That is a transport/auth issue,
not token capacity and not a science failure.

## Fable-side task

Wire this existing authenticated session to the same file contract; do not
build a second scientific supervisor.

1. Accept a request object containing:
   - `request_id`, `run_id`, and node id;
   - exact prompt and response-schema paths;
   - context-file paths and SHA-256 values;
   - the shared autonomy boundary.
2. Run a fresh-context, read-only review. Do not reuse the implementer's
   reasoning trace as evidence.
3. Write one response JSON atomically (`tmp` + rename), validated against the
   requested schema. Never write prose as the routing signal.
4. Never launch GPU work, edit the evaluated experiment, push, contact people,
   or acquire leases from the reviewer transport.
5. If the active session cannot truly start fresh, disclose that and write an
   `escalate` verdict rather than pretending independence.

Suggested mailbox paths (implement on the Fable side or ask Codex to expose the
corresponding handoff node):

```text
.research_loop/handoffs/inbox/<request_id>.request.json
.research_loop/handoffs/outbox/<request_id>.response.json
```

Use `research_loop/schemas/review.schema.json` and
`research_loop/schemas/result.schema.json`. Do not change these schemas without
human review.

## V5 transition history

The first fresh reviewer correctly rejected the recovered patch because its
four identical prompts were greedy (`temperature=0`), so they were not samples.
Codex repaired that with temperature 0.7, distinct recorded seeds, cumulative
role prefixes, canonical parent-set counting, frozen manifests, and run-specific
artifact snapshots. Seventeen CPU integrity tests passed.

The second fresh reviewer still rejected launch. Required remaining repairs:

1. Persist an exact reporting schema per prefix: raw candidate lines, parsed
   candidates, unique supported claims, provisional fallbacks, and actual
   retained claims. Offline truth fields must be added only after corpus commit.
2. Resolve retention semantics. Current `supported else provisional` snapshots
   can silently remove an earlier provisional memory. For the claimed
   cumulative dream process, use an explicitly append-only epistemic ledger
   (provisional may be upgraded but not silently deleted), or call the outputs
   non-nested prefix-specific snapshots.
3. Add semantic unit tests for deduplication, prefix isolation, malformed
   proposals, and provisional-to-supported transitions; substring checks are
   insufficient.
4. Stop loading an ambient `organism_corpus_*.json`; generate the dreamtext and
   dreamlora corpus entirely from this frozen lifetime/run.
5. Extend the frozen set through transitive world/think code, pin the Qwen 32B
   model/tokenizer revision (`5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd` on
   the H100), and capture package/CUDA/GPU environment metadata.
6. Label this condition permanently as a task-family-scaffolded,
   public-evidence exact-gate **ceiling/reference diagnostic**. It is not the
   headline no-exact-verifier autonomous-dreaming arm.
7. Report actual parsed proposal and token/query budgets. Four samples at k=6
   are up to 24 candidates/target and are not matched-compute improvement over
   v4.

Codex completed the bounded implementation repairs on 2026-08-31: stochastic
sampling and prefix isolation; canonical/malformed accounting; append-only
retention with contradicted fallbacks labeled honestly; a fresh run-owned
corpus; pinned model revisions and environment capture; semantic tests; and a
content-addressed review -> lock -> remote-spec -> executed-input chain checked
before and after every remote stage.  The task-family/public-exact-gate arm is
permanently labeled a ceiling/reference diagnostic.  Fable's mailbox transport
is now integrated as the first fresh review, with `gpt-5.6-sol`/`ultra` as the
required independent review and capacity-resilient fallback.  Neither reviewer
may independently change the v5 scientific design or relaunch it.  A new frozen
hash set must pass both reachable reviews before `sync_h100` becomes reachable.

Reviewer-only context remains local. The remote worker verifies the exact
approval-receipt hash, reviewed lock/spec hashes, and all declared execution
inputs against that lock; it does not require internal notes such as the mini
ledger to be exported to the GPU host.

## User-facing truth

- The phrase `Selected model is at capacity` referred to the selected
  `claude-fable-5` serving pool being temporarily full. It did not indicate
  exhausted user tokens.
- `claude -p: Not logged in` is a separate headless CLI-auth problem.
- Codex's nested app-server sandbox denial is another separate local execution
  problem; native subagents and managed unsandboxed read-only review work.
- The early queued shell did **not** run v5; the supervisor correctly prevented
  that invalid transition.  A later content-locked snapshot
  (`dream-ladder-v5-dev-20260831T161813-13cf3c10`) passed the independent
  review gate, ran on the H100, was pulled and hash-verified, and received a
  fresh result analysis.  Its terminal scientific decision is **stop**: direct
  parent proposal recall plateaued at 3/12, the public gate retained 0/5 true
  supported parent claims, the final 12-parent corpus was entirely false, and
  29/30 downstream thinker outputs were malformed.  It is archived as a
  negative ceiling/reference diagnostic and must not be replicated or
  transported into LoRA.
- The old supervisor state may show a later approval-binding failure because
  shared source files changed after the completed run while work moved to the
  recurrent design.  That fail-closed state is not evidence that the already
  pulled run was invalid: the authoritative run-specific `done.json`, frozen
  input snapshot, deterministic analysis, and fresh result review remain
  content-addressed under the completed run id.

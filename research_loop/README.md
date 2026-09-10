# Durable research supervisor

This directory turns the project-development cycle into a resumable graph.  It
does not put an LLM in charge of scientific goalposts.  Deterministic nodes run
tests, freeze bytes, launch jobs, and verify artifacts; fresh-context agents
review or interpret; human nodes guard genuinely scientific choices.

This is a small purpose-built state machine, not LangGraph.  The state lives in
JSON rather than any model session, and `watchdog.py` is the persistent outer
process.  Workers are disposable; the watchdog is not a worker.

## V5 path

```text
local contract
  -> content lock
  -> fresh Fable mailbox review (optional transport; rejection is binding)
  -> fresh gpt-5.6-sol/ultra review (required)
  -> CPU acceptance tests
  -> reverify lock + approval receipt
  -> sync
  -> hash-bound remote job
  -> started/done/failed marker polling
  -> run-specific input/output snapshot verification
  -> fresh result analysis
  -> human scientific boundary
```

The remote runner receives the SHA-256 of the exact approval receipt on its
command line.  The receipt binds the reviewer decision to the lock and remote
spec; the lock binds every declared executable input.  The runner verifies the
chain before and after every stage.  A modified source, lock, spec, receipt, or
workflow cannot silently continue an initialized run.

Fable requests use:

```text
.research_loop/handoffs/inbox/<request-id>.request.json
.research_loop/handoffs/outbox/<request-id>.response.json
```

Provider capacity errors are retried with fresh ephemeral contexts.  State and
events live under `.research_loop/`, so no chat session or watcher is the source
of truth.  Remote status comes only from run-specific JSON markers.
The context catalog routes repo-grounded context by job: broad project history
for planning/repair, and the smaller exact goalposts/ledger/code set for a
scientific review.  This avoids both context amnesia and indiscriminate dumps.

## Commands

```bash
.venv/bin/python -m research_loop.validate_v5_contract
.venv/bin/python -m research_loop.plain_tests \
  research_loop.test_research_loop research_loop.test_v5_semantics \
  alchemy.test_integrity lands.test_v02

.venv/bin/python -m research_loop.supervisor \
  research_loop/workflows/dream_ladder_v5.json init --force
.venv/bin/python -m research_loop.supervisor \
  research_loop/workflows/dream_ladder_v5.json run
.venv/bin/python -m research_loop.supervisor \
  research_loop/workflows/dream_ladder_v5.json status

# Detached persistent runner (safe to invoke again; singleton lock prevents two)
./research_loop/start_watchdog.sh
cat .research_loop/dream-ladder-v5-dev.watchdog.json
```

The current Semantic World v0.2 D3 endpoint has a known target-only shortcut.
Audit it explicitly with:

```bash
.venv/bin/python -m lands.audit_v02_shortcuts --seed-start 1 --seed-stop 101
```

Exit status 1 is expected for v0.2: both a sorted pair of visible target
outcomes and either single visible role outcome deterministically decode the
held-out answer. A future game is GPU-ineligible until the same audit passes
its ambiguity gate, together with the stronger Counterfactual Confluence
invariants in `plans/counterfactual_confluence_v03.md`.

Do not use `init --force` on a live run.  A workflow edit after initialization
requires a new run ID.  The supervisor stops at a human node instead of
silently changing prompts, splits, budgets, claims, or follow-up experiments.

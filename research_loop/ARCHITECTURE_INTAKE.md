# Durable architecture-change intake

Every material design idea enters the project as a byte-bound deliberation
chain before it becomes implementation work:

```text
human idea + durable context
  -> advocate: explicit graph / loop / claim / visibility / test delta
  -> systems interpreter: independent organism-level reconstruction
  -> benchmark interpreter: independent shortcut/identifiability reconstruction
  -> adversarial reviewer: cross-critique after both interpretations exist
  -> adjudicator: agreements, disagreements, resolutions, test dispositions
  -> HUMAN REQUIRED
  -> exact human ratification (when actually authorized)
  -> scoped implementation authorization
```

The state machine lives in `architecture_intake.py`. It validates JSON schemas,
exact source hashes, context-file hashes, complete visibility matrices,
cross-document identifiers, independent interpretation perspectives, full
concern/test dispositions, and legal phase ordering. It makes no
scientific-quality judgment. Only an explicit human-ratification artifact can
authorize implementation; it binds the exact consensus, exact paused state,
human authorization evidence, and authorized scope.

Example commands:

```bash
.venv/bin/python -m research_loop.architecture_intake --root . init \
  --change path/to/change.json --state .research_loop/intake/change-id.state.json
.venv/bin/python -m research_loop.architecture_intake --root . interpret \
  --state .research_loop/intake/change-id.state.json --artifact path/to/interpretation.json
.venv/bin/python -m research_loop.architecture_intake --root . interpret \
  --state .research_loop/intake/change-id.state.json --artifact path/to/benchmark-interpretation.json
.venv/bin/python -m research_loop.architecture_intake --root . critique \
  --state .research_loop/intake/change-id.state.json --artifact path/to/critique.json
.venv/bin/python -m research_loop.architecture_intake --root . consensus \
  --state .research_loop/intake/change-id.state.json --artifact path/to/consensus.json
.venv/bin/python -m research_loop.architecture_intake --root . ratify \
  --state .research_loop/intake/change-id.state.json --artifact path/to/human-ratification.json
```

Every transition re-hashes every earlier artifact. Editing a proposal after it
has been interpreted, or an interpretation after it has been critiqued, makes
the chain invalid. Consensus pauses at `human_required`. A separate,
evidence-bound human ratification releases only its declared
`authorized_scope`; it is not permission for unrelated GPU runs or claims.

## Persistent deliberation runner

`architecture_deliberation.py` turns the diagram above into a resumable
CPU-only process instead of relying on a one-off chat ritual. Copy
`workflows/architecture_deliberation_v1.template.json`, replace the change ID
and directive path, and select the durable project context for this decision.
The directive file is included verbatim and every source is hash-bound before
the first model call. The template starts from the project thesis, goalposts,
experiment design, idea log, review pack, handoff, and mini-ledger rather than
only the latest implementation file; trim or extend that list explicitly for
the decision instead of trusting chat history.

```bash
.venv/bin/python -m research_loop.architecture_deliberation path/to/workflow.json init
.venv/bin/python -m research_loop.architecture_deliberation path/to/workflow.json run
.venv/bin/python -m research_loop.architecture_deliberation path/to/workflow.json status
```

The advocate first emits explicit graph, loop, claim, visibility, and test
deltas. The systems and benchmark interpretations then run concurrently in
fresh contexts over identical proposal/source bytes and cannot see one
another. Only after both validate does a fresh critic see both; only after the
critique validates does the adjudicator run. Each role can use an ordered list
of Codex, Claude, or Fable-mailbox executors; embedding callers can inject a
different executor through the Python API.

The runner rejects missing, malformed, noncanonical, stale, or source-inexact
outputs and never overwrites a conflicting artifact. Its only successful
terminal state is `human_required`, with `implementation_authorized: false`.
There is intentionally no `approve` or `ratify` runner command. If Rohin later
approves the exact paused chain, create a human-ratification artifact and use
the existing `architecture_intake ratify` command. The implementation
supervisor independently revalidates that approval and its literal scope.
An adjudicator recommendation of `rework`, `reject`, or `defer`, any unresolved
disagreement/concern, or a removed/underspecified acceptance test is not
releasable: human routing cannot convert it into a technical pass. Repair the
proposal/evidence and produce a new hash-bound deliberation chain. This keeps
the critic's required changes durable and prevents an author advocate from
overriding them.

Freshness is process-level for Codex (`exec --ephemeral`) and Claude (`-p`).
The Fable transport contract requires its interactive server to spawn a fresh
read-only reviewer; this boundary is auditable but not cryptographically
provable by the mailbox itself. Model independence is therefore reported as a
protocol property, not a statistical guarantee of uncorrelated errors.
An injected Python executor is trusted to honor the same read-only/freshness
contract; the runner validates its outputs and all bound inputs but cannot
sandbox arbitrary caller code. A timed-out Fable request may also receive a
late response after another provider has succeeded; request IDs are never
reused, and that late response is preserved but never routed into the chain.

## Supervisor enforcement

A durable supervisor workflow that implements a material architecture change
must declare the exact intake state and the exact scope it will exercise:

```json
{
  "architecture_intake": {
    "mode": "material_change",
    "state": ".research_loop/intake/change-id.state.json",
    "requested_scope": ["architecture delta implementation", "CPU acceptance tests"]
  }
}
```

The supervisor fails closed unless the intake is `human_approved`, carries
`implementation_authorized: true`, and the requested scope is a literal subset
of the ratification's authorized scope without intersecting forbidden scope.
It records hashes for the workflow, intake state, ratification, consensus, and
every intake artifact. Those bytes and the scope are revalidated before every
node, including dry runs. A stale or replaced artifact pauses the run before a
command, agent, remote sync, or GPU node can execute.

Repository workflows that predate this gate and do not claim to implement a
new material architecture use the explicit declaration:

```json
{"architecture_intake": {"mode": "legacy_no_material_change"}}
```

Omitting the declaration remains accepted only for backwards-compatible test
and external workflows; it is durably labeled `legacy_undeclared` and confers
no material-change authorization.

# R140 operator-only CPU tool service — 2026-09-16

Additive wrapper for the EXISTING R127 pilot, not a child/parent/model change.
Main keeps manual lead and alone decides local deployment/launch on the node.
No deployment, remote publication, live source edits, sandbox run, or commit was
performed for this change. Use original pilot **source2** dependencies plus the
new service; do not substitute concurrently edited local dependencies.

## Gate and launch interface (Main only, later)

Choose `START = current saved-prefix index + 1`, strictly greater than 1698.
1695 is already handled by Main: `r140_validation_1695/VALIDATION.json` and
Tool4395... remain historical evidence, NEVER replay candidates. The service
also pins the full bytes of record `START - 1`; it does not discover a prefix.
From the intended frozen source2 environment, using canonical absolute paths:

```sh
python3 -m gpu.orch_r140_pilot_tool_service pins --root "$PILOT" --gate-root "$GATE" --start-index "$START"
python3 -m gpu.orch_r140_pilot_tool_service check --config "$CONFIG"
python3 -m gpu.orch_r140_pilot_tool_service run --config "$CONFIG"
```

`pins` and `check` only read; neither creates a gate nor dispatches/publishes.
They require the existing five passing CPU receipts, current boot/profile/capture
binding, journal identity, prefix hash, and service/dependency source closure.
Generate pins in the intended deployment environment, not this changing checkout.
`CONFIG` is one JSON object with these exact fields (replace placeholders):

```json
{
  "root": "/canonical/existing-pilot", "gate_root": "/canonical/existing-cpu-gate",
  "state": "/canonical/NEW-r140-state", "spool": "/canonical/NEW-r140-spool",
  "start_index": 1699,
  "journal_id": "FROM_PINS", "journal_manifest_sha256": "FROM_PINS",
  "start_after_sha256": "FROM_PINS", "gate_sha256": "FROM_PINS",
  "source_closure_sha256": "FROM_PINS",
  "wall_seconds": 900, "poll_seconds": 2, "max_polls": 300,
  "max_inspections": 1000, "max_calls": 4,
  "max_request_bytes": 400000, "max_output_bytes": 262144
}
```

1699 is only the minimum illustration: replace with `START` after Main's actual
saved prefix. All four directories must be disjoint, without symlinks; state and
spool must be NEW (existing parents). They become owner-private. Never reuse a
spool under another state. A restart requires identical config/pins and preserves
cursor, counters, and both wall-clock and same-boot monotonic deadlines.

## Behavior and limits

- Read only numbered pinned stream records. A RESPONSE lacking adjacent
  COMMITTED stays pending at its cursor, with no dispatch/publication intent;
  polling/inspection limits remain durable. Commit arrival triggers full
  adjacent TRAIN/hash/chain/terminal/nontruncated validation via `verify_origin`.
- Execute only one exact top-level `python experiment` fence, retaining source
  bytes unchanged. Ordinary Python, prose, and quoted examples are not requests.
  Malformed attempts are narrowly the exact requested tag or ` ```python` with
  the immediate first body line `python experiment`. Only verified provenance
  can produce a separate validation-only REJECTED receipt through `_inbox`.
  Invalid committed provenance is retained locally, never executed/published.
- Durable dispatch intent precedes the unchanged `run_request`. Reserve 75 wall
  seconds per launch and 65,536 combined output bytes per call. The existing
  sandbox retains its 15-second runtime, 128 MiB memory, CPU quota, device deny,
  clean environment, no network/secrets/other-root inputs, and bounded capture.
  No new privileged operations or sandbox-policy overrides are implemented.
- A separate operator worker bounds blocking dispatch; hard wall interruption
  prevents later publication. A killed/uncertain worker does NOT prove sandbox
  teardown: any already-started unit remains subject to the existing runtime
  limit. Never retry it; Main must inspect its preserved evidence.
- Persist the original records, proof, exact request/source, exact dispatcher
  result bytes and publication receipt. `publish_tool` uses a hash-bound exact
  result snapshot, not rewritten output. Durable publication intent precedes
  either inbox writer. Any interrupted intent stops the namespace; no automatic
  retries, inferred success, or replay using a fresh namespace. Exhausted caps
  also stop permanently. READY restarts alone may continue, including pending tails.

Validation uses real temporary journal/inbox files and real console/dispatcher
interfaces with execution mocked. Run the new test module with pytest; adjacent
CPU experiment, request parser, confinement-policy, and pilot-console suites
provide mock-only compatibility coverage. No real sandbox/runtime is needed.

Local validation: **278 tests + 34 subtests passed** across those five modules,
including real console tuple unpacking, pending COMMITTED arrival/restart,
invalid committed provenance, narrow 1695-form rejection, and no-replay intents.

# Exploratory PCFL A1 READ-interface result audit

**Date:** 2026-09-13 UTC  
**Run label:** `EXPLORATORY_PCFL_READ_INTERFACE_COMPONENT_NOT_V2_QUALIFICATION`  
**Node/root:** node2,
`/localhome/local-rohing/astra_diagnostics/pcfl_interface_a1_20260913_attempt1`  
**Controller observed:** PID 182656  
**Verdict:** **negative component result; no READ handshake; no v2 or paper
qualification**

## Result in one sentence

Disclosing the three READ command forms did not make the clean Qwen2.5-7B
actor use memory: all 64 first responses committed directly to `ROUTE`, no
READ was attempted or served, no registered port was emitted, and no route
succeeded.

This is evidence about **interface-policy elicitation only**. Because no READ
was issued, it does not test whether a service return would be accepted,
carried into a second turn, or used correctly.

## Exact observations

- The same controller was observed live as PID 182656 with the expected
  `astra_pcfl_interface_outer` command and bound manifest, then observed absent
  after its own completion. It was not restarted, signaled, or altered.
- The run completed 64/64 native calls in 203.291 seconds overall
  (192.880 actor-operation seconds), with 22,080 verified prompt tokens and
  5,416 verified output tokens. It performed **0 fits and 0 updates**.
- The frozen matrix was four exposed roots x two goals x all eight
  `(old, relevant, distractor)` bit combinations: 64 tasks, all labeled
  `ACTIVE_LINKED_TEXT`.
- **64/64 outputs began with `ROUTE`; 0/64 began with `READ`; 0 reads and 0
  service responses occurred.** Every task used only physical actor slot 0;
  its twelve later READ-capable slots remained uncalled.
- **64/64 copied the correct opaque START and GOAL identifiers.** The failure
  was after the colon: **0/64 used even one port identifier registered to its
  root, and 0/64 matched the required five-port route.**
- The 48 bounded outputs were route-shaped one-line strings containing
  placeholder ports such as `X,Y,Z`, `X1234567890`, or bare letters. All were
  scored `legal=false`, `strict=false`, `graph_success=false` and ended as
  `INVALID_TURN`.
- The other 16 outputs hit the 256-token cap while enumerating long bare-letter
  sequences and ended as `LENGTH`. These were goal 0 on excluded roots 0 and
  3, repeated across all eight memory-bit cells.
- There were only **eight distinct raw outputs**: one for each root/goal pair.
  Within every root/goal pair, output bytes were identical across all eight
  old/relevant/distractor settings. Thus the model's response was insensitive
  to every memory-state condition before any service access.
- Reducer result: `read_handshake_tasks=0`, `served_read_tasks=0`,
  `route_successes=0`, `stage_gate_passed=false`, and
  `full_assay_qualified=false`. `invalid_read_tasks=0` is vacuous because no
  READ was attempted.

The public prompt listed the exact legal commands and explained their return
types, but exposed no registered query address beyond task START/GOAL and did
not explicitly instruct the actor to begin with `READ EVENTS_AT <START>`.
The actor could in principle construct that legal query from the disclosed
START, but instead immediately filled the terminal ROUTE template with
generic placeholders.

## Capture, replay, close, and release audit

- `completed.json` binds 396 stage files. A fresh read-only SHA-256 pass found
  **zero missing or mismatched files**. The outer controller's
  `stage_completed.json` is byte-identical to the stage `completed.json`
  (file SHA-256
  `a4ad9e496d3306cc8bc99d83489acbe1106a5343cd45271f917d3be5bec42131`).
- Report payload SHA-256:
  `37526a11397b17ac422aa60dc2322c4e9ced44d98628505a47a0647322100c3d`.
  Completion payload SHA-256:
  `e32be63d6d4003f361890ce23228c27dae1bd2f87d136a48f26b7b5ebc43a9d8`.
- All 64 calls preserve request, render, raw-token/native response, and joined
  attempt captures. The post-actor custody receipt verifies the clean C0
  native actor identity, 64 calls, token totals, load receipt, and close
  receipt (`native_actor_custody_verified=true`).
- Local replay is valid and points to the report hash. The report/replay's
  embedded `native_custody_verified=false` predates the separate post-actor
  custody receipt and remains a reason not to promote the run; it was not
  silently rewritten.
- Actor close reports 64 calls, no error, no budget overrun, and delegates
  process/GPU release to the outer controller. The native engine shutdown
  returned successfully.
- Outer lifecycle receipts show worker PID 182667 returned code 0; its owned
  process group had no remaining members and
  `owned_group_released=true`. Post-release GPU inspection found the bound GPU
  UUID with an empty compute-process list. Queue state matched before and
  after, and the post-CVD check was clear under the predeclared non-worker
  service exceptions. The inner `gpu_released=false` field is the pre-outer
  snapshot paired with `outer_release_required=true`; the outer receipts are
  the authoritative release evidence.

## Causal interpretation and next decision

The run rules out one optimistic assumption: merely documenting a local READ
API is not enough for this base actor to choose retrieval over an immediate
answer on opaque route tasks. It does **not** show that the READ service is
broken, because its dispatch/return/continuation path was never reached. It
also says nothing about LoRA storage, connected knowledge, traversal after a
successful read, learning, or the supplied-memory ceiling.

Do not advance A2/A3/A4 or select an interface from this result. The bounded
successor is specified separately in
`2026-09-13_pcfl_a1_zero_read_minimal_successor.md`: add only the public,
answer-free requirement that at least one READ precede ROUTE, then run an
eight-task exposed-root smoke before any 64-task repeat. This still leaves the
query form and address child-selected. If that smoke again produces almost no
legal READs, stop prompt-prose iteration and test a symmetric typed-action
interface instead.

Any such successor is new development optimization. The corrected v2 closure,
full prebinding, unseen confirmation roots, and independent implementation
gate remain required before a supplied-memory or paper-grade claim.

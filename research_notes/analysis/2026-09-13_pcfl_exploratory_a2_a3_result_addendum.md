# Exploratory PCFL A2/A3 exact-graph and typed-THINK result addendum

**Date:** 2026-09-13 UTC
**Run labels:**
`EXPLORATORY_PCFL_DIRECT_GRAPH_COMPONENT_NOT_V2_QUALIFICATION` and
`EXPLORATORY_PCFL_THINK_INTERFACE_COMPONENT_NOT_V2_QUALIFICATION`
**Node/roots:** node2,
`/localhome/local-rohing/astra_diagnostics/pcfl_interface_a2_20260913_attempt1`
and
`/localhome/local-rohing/astra_diagnostics/pcfl_interface_a3_20260913_attempt1`
**Controllers observed:** A2 PID 185622; A3 PID 185678
**Verdict:** **both exploratory components are negative; neither qualifies
v2 or C0**

## Result in plain language

Giving the clean Qwen2.5-7B actor the complete route graph was not enough for
it to compose the required five-step opaque route. Asking it to THINK first
also did not produce a usable multi-turn test: it wrote a whole multiline
monologue in its first response, violating the one-line typed interface, so
the controller correctly stopped each task before a continuation. Both
conditions scored 0/64 graph-successful routes.

The A3 result is therefore an **interface-handshake failure**, not evidence
that additional deliberation cannot help. No task completed even one accepted
THINK turn.

## Matched comparison

The two rosters contain the same 64 case/goal keys. For every corresponding
task, the user-visible exact graph/task bytes, source rows, and actor seed are
identical. Only the system-level action policy differs: A2 forbids THINK and
requires a one-shot ROUTE; A3 requires one to six one-line THINK responses
before ROUTE. Both have READ disabled and perform zero fits and zero updates.

| observation | A2 direct graph | A3 typed THINK requested |
|---|---:|---:|
| tasks | 64 | 64 |
| actual / possible calls | 64 / 64 | 64 / 448 |
| verified prompt tokens | 31,936 | 34,688 |
| verified output tokens | 2,530 | 13,642 |
| task reasons | 54 `ROUTE`, 10 `INVALID_TURN` | 40 `INVALID_TURN`, 24 `LENGTH` |
| accepted THINK turns | 0 | 0 |
| strict graph successes | 0 | 0 |

### A2: exact graph, direct answer

- All 64 raw outputs begin with one ROUTE line and preserve the exact START
  and GOAL.
- The required route has five ports. Every proposed route instead has only
  two or three items: 26 have length two and 38 have length three.
- Fifty-eight outputs contain at least one port registered to that root; in
  total, 144 of the 166 emitted items are registered ports. This is a real
  improvement over A1's zero registered ports, but it is not composition.
- Independent replay over each supplied EDGE graph confirms **0/64 exact
  expected port sequences and 0/64 paths reaching the goal**. The outputs
  splice local ports while skipping required middle transitions.
- Reducer result: `route_successes=0`, `stage_gate_passed=false`, and
  `full_assay_qualified=false`.

### A3: exact graph, typed THINK requested

- The frozen prompt explicitly says that each response must be exactly one
  physical line, that THINK and action must never be combined, and that at
  least one THINK must precede ROUTE.
- All 64 first responses begin with `THINK`, but every response contains two
  to nine physical lines. Each contains one to nine THINK lines; 54 also
  contain a ROUTE line in the same response. Thus **0/64 THINK turns were
  accepted**, no CONTINUE message was sent, and all six later actor slots for
  every task remained uncalled.
- Twenty-four first responses exhausted the 256-token cap. Forty ended before
  the cap but were still invalid multiline turns. The run consumed 5.39 times
  A2's output tokens without entering the recurrent protocol.
- Of the 54 embedded ROUTE lines, 52 are complete enough to parse
  independently; all 52 preserve START/GOAL, but none equals the required
  five-port sequence and none traverses the supplied graph to the goal. The
  other two ROUTE lines are visibly truncated by the token cap.
- The prose does refer to graph nodes and tries to reason over branches, but
  it frequently invents transitions or substitutes node fragments for port
  identifiers. More generated reasoning text did not become a legal physical
  action under this interface.
- Reducer result: `thought_tasks=0`, `thought_interface_tasks=0`,
  `route_successes=0`, `stage_gate_passed=false`, and
  `full_assay_qualified=false`.

## Capture, replay, close, and release

- A2 controller PID 185622 was already absent at the first read-only poll and
  had complete terminal receipts. A3 PID 185678 was observed live under its
  exact bound command and later absent after self-termination. Neither was
  restarted, signaled, or altered.
- Each stage's `completed.json` binds 396 files. Fresh read-only SHA-256 passes
  found zero missing or mismatched files. Each outer `stage_completed.json`
  is byte-identical to its stage `completed.json`: A2 file SHA-256
  `7a5d6b2e2e9fe53e9ceb7cff9be8e89bdeeef15af13fa271d09e00e9f7e9c4be`;
  A3 file SHA-256
  `f0b96fbe2a7b68341b0cea62520db3748be8e1fb2e975185167d429b551323a0`.
- A2 report payload SHA-256 is
  `151077c51044f1a087100bec030b26f5554e05b3a9f7ceac5664e157368dfac0`;
  A3 is
  `61c8d6a822bc43e23cdf8759966c3ff23d3c341a87d0d1a11c43ecb7ec83b89d`.
  Local replay is valid for both.
- Post-actor custody verifies native clean-model identity, exact call and
  token totals, load receipts, and close receipts for both stages. As in A1,
  the report/replay's embedded `native_custody_verified=false` is the
  preserved pre-custody state; the separate post-actor custody receipt is
  true.
- Native engine shutdown returned. Outer workers 185744 (A2) and 185812 (A3)
  exited code 0; both owned process groups were empty and marked released.
  The respective bound GPU UUIDs had no compute process after release, queue
  state matched, and post-CVD checks were clear under the predeclared
  non-worker service exceptions.

## Bounded interpretation

Three component facts are now established on exposed roots:

1. A1: merely disclosing READ does not elicit a READ.
2. A2: supplying the exact graph elicits registered local ports but not the
   five-edge composition.
3. A3: asking for typed recurrent thought elicits abundant reasoning prose,
   but not one accepted typed THINK turn under the current one-line protocol.

Do **not** interpret A2 versus A3 as a causal estimate of useful thinking.
A3 never entered the planned recurrent treatment, and it also differs in
available calls, prompt policy, and generated-token use. The result instead
localizes the next interface question: can the actor emit exactly one bounded
THINK command, receive CONTINUE, and only later emit ROUTE? That must be shown
before testing whether recurrent deliberation improves graph traversal.

These runs do not test LoRA storage, online learning, retention, connected
knowledge formation, or the supplied-memory ceiling. They also retain all
pre-v2 implementation limitations already recorded in
`2026-09-13_pcfl_c0_interface_v2_implementation_audit.md`. Nothing here may be
called paper-grade C0 or v2 qualification.

# Same-task cue counterfactual readout: minimal prospective spec

2026-09-14. **Design only; no execution authorized by this memo.** Scope: conditional external-record use, not a robustness suite. Prior analysis scopes are released. Main owns any implementation/resource guard/launch. No fitting, model loads, remote changes or helper implementation occurred here.

## Fixed design: 16 episodes, one bank

Use unchanged `organism_v6.experienced_event_read_route.run_episode(task, actor, read_memory, transition)` with two saved seed0 actors:

- Cue-on: `/tmp/astra_cue_sleep2_20260914_attempt1/train/adapter`; final state receipt `9d3c97ae280dd33c0acb5b7a67cb162ccb2d53d63d0668d2206aa091ac944e63`.
- Cue-loss-off: `/tmp/astra_cue_sensitivity_20260914_attempt1/CUE_LOSS_OFF_seed0/train/adapter`; final state receipt `a160b83ab9a716b5c1cba25252c9b3341db205e7269f245d6d71d33415d4ea34`.

These are previously audited receipt bindings, not freshly hashed weights; verify loaded-state bindings at future execution. See `2026-09-14_cue_loss_control_results.md` (SEQ226) for common S1/data and denominator-normalized loss control.

Prospectively fix `experienced_event_microloop.build_bank("ASTRA-CUE-COUNTERFACTUAL-READOUT-20260914-A1")`: **four facts, two worlds, two ports/events/outcomes per world**. Freeze four `public_task(fact)` objects from the factual bank **once**, in bank order. Reuse their exact bytes for both conditions and states. No layout/order variation, bank selection or alternate seeds. Before execution, require IDs disjoint from prior training/cue and held-bank IDs; collision or unverifiable disjointness blocks this specification rather than silently resampling.

## Treatment: coherent outcome reassignment only

For each world's factual records `(E0, N, P0, G0, R0)` and `(E1, N, P1, G1, R1)`:

| Condition | External EVENT outcomes | Actual transition |
|---|---|---|
| Factual F | E0 GOT G0; E1 GOT G1 | P0→G0; P1→G1 |
| Swapped S | E0 GOT G1; E1 GOT G0 | P0→G1; P1→G0 |

Keep EVENT/AT/DID/EVIDENCE identifiers, record grammar, trailing newline, task NODE/GOAL, listed PORTS/EVENTS and their order unchanged. Only GOT bytes and the matching transition outcome mapping change. **Do not regenerate public tasks from swapped facts:** that would change GOAL. Do not swap port labels or feed swapped records against factual transitions.

`read_memory` returns the selected condition's exact `_event(fact)` text as terminal/nontruncated external text, with no model-based reader. Actor receives only the existing public controller messages; condition labels, expected actions and scorer metadata remain private. Use fresh conversations, unchanged frozen weights, identical deterministic decoding and reset paired generation seed for each F/S task pair. Execute state order cue-on/loss-off, task order 0–3, condition order F/S; no cross-episode history or state updates. Existing bounds: three actor calls/two reads/one commitment per episode; **at most 48 actor calls and 32 external-text callbacks**.

## Fixed denominators and raw decision evidence

- Per state: factual GOAL arrivals **/4**, swapped arrivals **/4**, and primary **paired-correct port reversal /4**: both episodes reach the unchanged GOAL and commit their respective, necessarily different, correct ports. Missing/malformed/exhausted episodes remain failures, never dropped.
- READ uptake and second-READ episodes: each condition **/4**, combined **/8**. Also report exact READ call counts and committed ports per pair.
- Conditional next-action diagnostic **/4 pairs**: identical first READ in F/S; after its matching GOT, ROUTE that record's DID; after its mismatching GOT, READ the other event then ROUTE its DID. Report all raw actions/text, matching-versus-mismatching branches, and failures/no-READ pairs. This stricter read-then-route pattern is secondary: correct direct inference after a mismatch may pass primary reversal without passing this diagnostic.
- Identical public prefixes should produce identical first actions before any record is delivered. Any paired discrepancy is a decoding/pairing validity failure; retain it in the ledger, flag the readout invalid, and do not claim a clean treatment contrast or selectively rerun.

Persist task/bank/controller/adapter bindings, exact condition record bytes, transition tables, decode settings and complete episode traces with SHA256 before interpreting counts. No extra panels, training reuse or promotion of these evaluation records into cue collection. Pure identifier/order-fixed routing cannot pass both mappings on a task; read-backed reversal supports conditional record use on these four tasks, **not** broad reasoning or robustness. States share S1/training banks; this is one bank and one optimizer-seed pair, not independent replication. Existing old-task accuracy shows no robust cue-loss advantage; this readout neither retests nor changes that conclusion.

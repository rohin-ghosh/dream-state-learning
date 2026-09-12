# SEQ105 — memory acquisition improves; retention is seed-dependent

All three predeclared original-parent continuations completed and were fully
released on September 12, 2026, 19:43:16–19:43:33 UTC. Main verified all501
capsule hashes, terminal/release references, and192 raw-response/reduction
matches. Separate raw-call review is pending.

| Original parent seed | Original dev memory /16 | New dev memory /16 | Exact training-prefix memory /16 | Retained habit /32 | Correct ACT /32 |
|---|---:|---:|---:|---:|---:|
|0|4|14|14|0|0|
|1|7|16|16|0|0|
|2|3|16|16|32|32|

Both memory panels query the SAME16 authored facts, not32 independent facts.
The exact panel uses the original training prefixes; the development panel
uses the fixed alternate question wording. All48 memory responses across
each panel are valid colors. Seed0's two incorrect bindings persist across
the two interfaces. This establishes acquisition in this finite authored
setting, not general memory, novel-fact transfer, child sleep or parenting.

Seeds0/1 do not emit valid ACT at all on the32 arithmetic questions. Seed0
emits colors; seed1 emits color repetitions, with23 arithmetic calls ending
at the64-token cap. These are output-interface failures, not demonstrated
erasure of latent arithmetic knowledge. Seed2 retains all32 PREDICT-before-ACT
responses and correct actions while answering all16 memory facts correctly.
Thus two-task coexistence in one adapter is possible here, but this recipe
does not reliably preserve it across seeds. Do not choose seed2 as a clean
or preferred child, infer that separate adapters are necessary, or promote
general G3/readiness. Every seed and failure remains in the analysis.

## Recipe and limits

Each run forks its ORIGINAL SEQ098/099 teach adapter. Exactly the original16
memory rows, their unchanged rendered spans, labels and source-event metadata
are trained for20 epochs at batch4, LR3e-4:80 new updates,160 cumulative.
Fresh AdamW and original-parent-matching optimizer seed; one rank8 adapter,
frozen base, no arithmetic/habit rehearsal. Per seed:14,080 input-token and640
target-token presentations. Native masks include42 ignored context tokens,
one color target and EOS; zero truncation/drops were required and checked.
This changes subset, exposure and cumulative training relative to the original
mixed fit, so it does not isolate dose versus interference as a causal factor.
Inherited controls/OFF are references, not a new matched80-update control.

Three new fits,240 updates and192 calls (48dev+16exact per seed), with both
panels required regardless of outcome. No new OFF/HF/confirmation calls.
All64 confirmation cases remain unrequested. Model origin stays
`UNRESOLVED_LOCAL_HASHES_ONLY`; formal C11 remains deferred.

## Artifacts and cost

Node3 root: `~/astra_diagnostics/astra_fundamental_memory_only_20260912_attempt1`.
Source: `3a12807f88747bafd0aada1d4a09ba88b915f903`.
Plan SHA256: `0f8d1a3042b92c3c940309f0b909f7ee535c295e3c3fb6197a8d45c4c137ac90`.
Capsule SHA256: `8400de86e541573a73803b8ee821e753d3ba644e8346a13f85f6a26a691b1a0a`.
Capsule, validation, collector, analysis script/JSON and runner are archived in
`receipts_20260912/`; weights remain immutable on node3.

Full reservation1666.592415s (27.776540A40min), controllers1101.776900s
(18.362948min), workers785.153102s (13.085885min). Scopes are nested, never
additive. Full reservation includes collection delay, not claimed GPU busy
time. All controllers and owned GPU processes were absent at full release;
no foreign process was killed. Native collection exceeded the SSH120s window
but continued as PID205218; Main inspected its successful original artifact
and did not rerun `finish`.

Next decision: use the already-running compatible-habit root0 result to assess
explicit rehearsal; select a bounded replay comparison if retention remains
the limiting link. Conditional-operation corpus preparation continues on CPU.
No larger parenting launch is justified merely by these memory counts.

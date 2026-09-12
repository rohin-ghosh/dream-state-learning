# SEQ-116: interleaved memory replications — September 12, 2026

**Both new FOUR_VIEW branches meet the prespecified thresholds. Effects
relative to SINGLE_VIEW vary by seed; no general superiority is established.**
All448 new raw calls and96 inherited original-parent calls were independently
recounted, with zero contradictions against stored reductions. Original seed0
results below are inherited SEQ113, not rerun.

| Seed / arm | Dev memory /16 | Exact /16 | Lexical families, each /16 | Habit /32 | ACT correct /32 |
|---|---:|---:|---|---:|---:|
|0 SINGLE|16|16|16 /16 /16|32|32|
|0 FOUR|16|16|16 /16 /16|32|32|
|1 SINGLE|16|15|16 /15 /16|32|32|
|1 FOUR|15|15|15 /15 /15|32|32|
|2 SINGLE|4|5|4 /4 /4|0|0|
|2 FOUR|16|16|16 /16 /16|32|32|

These are the same16 authored facts across five query surfaces, not80
independent facts. Three learner seeds do not turn repeated probes into
independent learner observations. Seed1 FOUR consistently misbinds device-011
as blue rather than green; SINGLE's exact error is a different key. Seed2
SINGLE retains valid PREDICT-before-ACT formatting on all32 arithmetic
responses but all ACT values are wrong. The legacy habit metric includes
correctness: its zero is not pure format loss or proof of latent erasure.
Every new response is parser-valid, stops normally, and is under its token cap.

## Recipe and interpretation

Each new branch independently forks its corresponding original80-update teach
adapter, then performs320 updates to400 cumulative with a fresh same-seed
optimizer, rank8, LR3e-4 and one LoRA. The original16 memory and16 selected
arithmetic sources are presented40 times each. Every four-row batch contains
two distinct sources of each kind. SINGLE repeats one question; FOUR uses four
training phrasings. Target presentations match at10000 per child; input
presentations do not (66160 versus67120); padded slots match at76960.

Inherited parent dev memory was7/16 and3/16 for seeds1/2, with32/32 habit/ACT.
No new OFF baseline was executed. The threshold required FOUR dev/exact and
each lexical family at least15/16, habit at least30/32, and ACT at least31/32,
plus technical completion. All three FOUR seeds now meet it. SINGLE results
were not part of that criterion. Seed0 ties and seed1 slightly favors SINGLE;
seed2 is a large opposite difference, not proof that wording variety generally
prevents interference. The non-parented authored-material experiment does not
qualify operational sleep, general G3, P1, G5, H1/H2 or a mechanism freeze.

## Custody, costs and next comparison

Source `22b7e528f6f62358981ed2264d30ee7242926160`.
Native roots under `~/astra_diagnostics/astra_interleaved_memory_replay_20260912_attempt1/`:
`fits_root1_attempt1` and `fits_root2_attempt1`. Controllers249359/249709 and
watchers249360/249710 ended naturally; no watchdog signals. Full release was
verified at23:03:37.296976UTC and23:04:22.219692UTC, before custody deadlines.

Through-collection reservations total2431.477s, or40.525 aggregate A40-min
across two GPUs, not concurrent elapsed wall time. Worker/controller/collection
windows overlap and must not be added. Raw readout cost is19596 input and2408
output tokens. No earlier parent/root0 cost is included in that subtotal.

Capsule hashes:
- Seed1: `e3014e7b362c983e6bba053fa91605a3307959861f2838ec35cf3637f4e6b60d`.
- Seed2: `0a46c83632af87b3988bfd685d2ebde9f4682dfa56d9ff68861c65774d924447`.
- Raw review: `9f3e8471cca264814c6d96dc707baea17e6a96a0fc1d44aba649581a0fa11fe7`.

Herschel reconstructed raw counts, schedules and lineage without native/model
execution. He authored older related replay code and the root0 audit; this is
an independent reduction, not a blind or fresh-author review. Native weight
and tokenizer checks are receipt-level evidence here. Model origin remains
`UNRESOLVED_LOCAL_HASHES_ONLY`. Detailed raw cases and costs are archived in
`receipts_20260912/astra_interleaved_replications_independent_review_20260912.json`.

Main next selects a versioned sequential-new-content allocation comparison,
starting from seed0 FOUR consistently rather than per-seed winners: two new
disjoint16-fact banks, replay versus extra-new-data at the same update budget,
old/new/habit readouts after each fresh reload. This deliberately has unequal
new-fact exposure and cannot isolate replay at fixed new-data dose. First
budget is90 A40-min including collection; implementation/native validation are
still required. No new launch is authorized by this result memo alone.

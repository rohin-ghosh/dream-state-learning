# Durable screen custody integration

Builder, September 13, 2026 Pacific. Storage plumbing, not scientific release.

## Implemented interface

`ScreenCustodySink(directory, torch=None, limits=...)` implements the accepted
screen runtime's existing event callback. Use a fresh directory in a trusted
existing parent and a context manager; pass the sink to
`run_reduced_state(..., custody_sink=sink)` with the same actor's actual calls
list. No model/tokenizer loading, input admission, checkpoint selection,
scoring, continuation decision or route/core semantics is added here.

The sink reuses exclusive/no-follow writes, bounded files and fsync from the
checkpoint filesystem helper, but not its adapter/optimizer envelope. Typed
builtin encoding preserves raw bytes/text, high64 integers, EOS-bearing ID
lists, tuple/list distinction and float bits. Only known screen/driver records
are projected. Supplied plain strided tensors become detached CPU tensor-only
sidecars; no arbitrary-object pickle. The terminal ledger references previously
captured call snapshots instead of re-reading mutable backend objects later.

The event protocol checks all 280 reserved slots, state/seed/request binding,
call order, physical/native indices and terminal capture references. Native
record identity remains the runtime's responsibility. Corrupted/missing/order-
invalid files fail verification. Unsupported fields/cycles and I/O failures
produce incomplete custody and stop later dispatcher calls, without retries
or overwriting evidence. Supported siblings and partial files are retained.

`verify_receipt(directory, limits=...)` is bounded and read-only; it never
imports torch or unpickles sidecars. Prior events and sidecars are re-read and
verified before COMPLETE is published. Complete export can describe an
aborted screen; scientific_success is always false. Exception class, typed
arguments and supported attached fields are DIAGNOSTICS, not preservation of
the original exception/traceback/interpreter state. Tensor device, strides,
storage aliases and autograd identity are not preserved. This verifier checks
byte integrity, not authenticated provenance or decoded tensor content.

A marker write/fsync failure may leave readable but durability-uncertain bytes.
Readback cannot prove that a past fsync succeeded and must never override a
failed sink's incomplete status. Retain the returned in-memory ScreenRun and
partial files; do not retry that sink or interpret a marker as experimental
success. Trusted exclusive access and native provenance remain caller duties.

Default bounds are 8 MiB per event, 8 MiB per tensor, 256 MiB total, 562 events
and 4,096 files. Caller limits require prospective representative validation;
these defaults are not a measured native full-screen envelope. This is not a
replacement for the separate final paper-grade C11 guard.

## Executed validation and independent review

Worker: 24 focused tests, **23 PASS / 1 optional torch SKIP**, 3.497s.

Main node2 CPU tensor test: **1 PASS in 0.087s**, torch 2.13.0+cu130,
CUDA hidden, OMP/MKL and torch intra/inter-op threads fixed at one. It stores
and round-trips an actual int64 tensor including 2**63-1 and EOS ID 1, verifies
shape/dtype/content and unchanged source/RNG. No model/tokenizer is instantiated.
Observed September 13, 17:24:12–17:24:14 Pacific; the receipt retains the
equivalent September 14 UTC timestamps and full command. Shared node2 checkout
was not changed; isolated source hashes were checked again after execution.

Main integrated discovery command:
`python3 -m unittest discover -s tests -p 'test_composition_birth_stage2a*.py'`.
Observed September 13, **17:24:36–17:29:41 Pacific**: **604 tests, 584 PASS,
20 native-only skips, 303.545s**. All **57 source/test hashes** were unchanged.
The skipped cases have separate receipts (9 trainer, 6 checkpoint, 2 actor,
2 readout-continuity, 1 tensor export); no combined native-20 run is claimed.

Turing independently reviewed the exact frozen source/test and returned
scoped PASS, no blocking findings. He ran no tests, model or remote commands.
The acceptance is source/storage-only; no native/science/C11 approval follows.
No test, worker or GPU experiment remains active from this slice.

| Artifact | SHA-256 |
|---|---|
| organism_v6/composition_birth_stage2a_screen_custody.py | 94f0421933dbd69885bc256d4c663b5ba31daad33e72e1c01ccf985eee00c18c |
| tests/test_composition_birth_stage2a_screen_custody.py | 3d530ca65ebe46ec554027d503acdbde104c133961ce75ae06dd76ceec9b0fb2 |
| research_notes/astra_memos/receipts_20260912/astra_stage2a_screen_custody_cpu_20260913_attempt1.log | 2e23681f51b3492c8ebcbfa229514b0b59596be79512cdde69cbde8489d2279b |
| research_notes/astra_memos/receipts_20260912/astra_stage2a_custody_integration_20260913_attempt1.log | 99d3a84facd7bef4e3f5eb698a2e64c4ed8aa0921ddcb7d46162f68d85cabc69 |
| gpu_artifacts_local/stage2a_screen_custody_cpu_20260913_attempt1/source_bundle.tar | 6933dd8f51ad17048a6ba4aa86aedb71e26fed2c5f1d7c02013aae4352d83d34 |

The archive also remains at /tmp/astra_stage2a_screen_custody_cpu_20260913_attempt1.tar;
the isolated node2 source tree is /tmp/astra_stage2a_screen_custody_cpu_20260913_attempt1.
It includes the frozen Stage2A source/tests and an empty tests/__init__.py.
Keep these receipts and archive unchanged; new attempts get new directories.

## Remaining critical path

The historical E0-r memo relay is reconciled separately; no E0 queue is
reactivated and no E0-r outcome inferred. Registered-route/core definitions
remain unanswered at the 17:30 Pacific pull. They affect leak acceptance and
core hashes, so this exporter is not permission to invent them or substitute
empty inventories. Next: bound those definitions, finish full source inventories
and source audit, then separate material/tokenizer/runtime preparation and the
reduced BASE/D1 560-slot screen before authentic two-SLEEP integration.
The full campaign and paper claims remain incomplete; formal C11 stays deferred.

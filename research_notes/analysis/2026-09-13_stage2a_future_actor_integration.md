# Stage2A future-ID and actor integration

Builder, September 13, 2026. Engineering evidence only; mission incomplete.

## Implemented and bounded

`composition_birth_stage2a_future_inputs.py` rebuilds the complete selected
birth source and exact retained arm before deriving candidate/disclosed/future
identifiers. Its universe and disclosure follow the prospective source
disposition, SHA256
`6f442bd1af56ca5a0b925ae56925b53207cfa9e1ef72f0c25315956da9987154`.
QUERY/EVENT/PORT roles include off-path and unregistered entries; destination
NODEs include all EVENT.GOT and effective world destinations. Only retained
parsed service fields, WORLD outcomes and actor operands disclose candidates.
Task-field exceptions remain occurrence-specific scanner decisions, not global
subtraction. Provenance and reconstructed snapshots are immutable. Pass
`tuple(sorted(result.future_identifiers))` to the scanner. The separate future
limit is 16,384; field/route limits remain 4,096, with hard errors, no truncation.

Mendel's independent read-only review returned scoped PASS on the four exact
future/scanner hashes below; no concrete flaw or visibility counterexample.
The review ran no duplicate tests. This is NOT complete semantic/route
inventory validation, input-authority authentication or full Stage2A GO.

`composition_birth_stage2a_actor.py` accepts an already-loaded HF model and
explicit tokenizer/backend/device. It implements exact low64 seeds, template
count agreement, greedy generation/caps, raw output/failure custody and model
mode/config/RNG restoration. PEFT forwarding-only generation-config ownership
has a regression test and native CPU exercise. It contains no loader. Custody
is currently in memory: authenticated identities, public source selection,
durable export, exclusive device ownership, deadlines and native qualification
remain outer responsibilities. No numerical tolerance is retroactively added.

Mendel also returned independent scoped PASS on the exact actor source/test
and native receipt hashes below: low64/RNG restoration, PEFT ownership,
caps/template checks and failure custody. No duplicate tests or model loads;
this does not certify durable export or native/scientific readiness.

## Completed Main receipts

1. Node2 native CPU actor tests: observed **23:27:47–23:27:52 UTC**;
   **2 PASS in 2.657s**, tiny random GPT2 baseline and rank-8 PEFT, synthetic
   tokenizer, CPU float32, fixture seed 20260913. CUDA hidden; OMP/MKL and
   torch intra/inter-op thread counts prospectively fixed at one. Receipt
   records torch 2.13.0+cu130, transformers 5.5.3, peft 0.20.0 and tokenizers
   0.22.2. Greedy-generation warnings are retained. This is NOT Qwen, real
   tokenizer, CUDA, controller learning or a scientific result.
2. Integrated VM command:
   `python3 -m unittest discover -s tests -p 'test_composition_birth_stage2a*.py'`.
   Observed **23:28:58–23:33:54 UTC**; **553 tests, 536 PASS, 17 native-only
   skips, 294.802s**. All **52 source/test hashes** remained unchanged.
   The skipped 9 trainer, 6 checkpoint and 2 actor tests have separate native
   receipts; no single combined native-17 run is claimed. The checkpoint
   receipt includes fresh-process disk restore and D2 continuity; that is
   distinct from this actor receipt.

The timestamp in an attempt filename is a label, not its observed start.
Neither test remains active. No GPU science was launched/killed, no real
Qwen/tokenizer was instantiated, no curl/wget retry or approval requested.

| Artifact | SHA-256 |
|---|---|
| organism_v6/composition_birth_stage2a_future_inputs.py | e0b2b4572b1d4fe9f25cc861d2d08c4e3c9046d220c237560a6732ceb1335930 |
| tests/test_composition_birth_stage2a_future_inputs.py | c12b8c990006a503835c073afc766ae475bcd8c6443719ff357056328cda23a5 |
| organism_v6/composition_birth_stage2a_scanner.py | bc07eee278d02fbb925bae05d41ea8f98dbde0d35efe20f41574fe59c41532e2 |
| tests/test_composition_birth_stage2a_scanner.py | 830954bb7c19cb4e7e712597e8fb6a3da92dd82b3974c50cf01943b2da6371a5 |
| organism_v6/composition_birth_stage2a_actor.py | 9b376d43a7564b00ef9e75513853a735103bad3b055e527af97e8ede5359957a |
| tests/test_composition_birth_stage2a_actor.py | 6926d4940cbdff6c23b64a4898805edcc2373e95b65c15f35ee83d28cbfe543b |
| research_notes/astra_memos/receipts_20260912/astra_stage2a_actor_native_cpu_20260913T2328Z_attempt1.log | de0187a7aef644aa4a4d4f05db37a3ad59687ca17a0d703afacf10d9f21bbebe |
| research_notes/astra_memos/receipts_20260912/astra_stage2a_future_actor_integration_20260913T2330Z_attempt1.log | 5c4f8c62621ce4fed96a83c24cfcb5852bef562dc68d940ae7291b8992158e1e |
| gpu_artifacts_local/stage2a_actor_cpu_20260913T2328Z_attempt1/source_bundle.tar | 461a4d184f837debe7ae3283bc6d97fae404005727d424a39e4c7503918af707 |

Native bundle has 33 entries, including empty tests/__init__.py for isolated
test import. Same archive and extracted source survive under
`/tmp/astra_stage2a_actor_cpu_20260913T2328Z_attempt1` (tar suffix for archive),
with the durable local archive above authoritative. Shared node2 checkout was
not edited. No node1 writes occurred; earlier bounded preservation audit is
unchanged and does not certify other owners' data or subsequent writes.

### Native CPU reproduction recipe

This recipe is derived from the pinned test/bundle and observed environment;
it is not a new execution receipt or a claim to recover the original shell
command verbatim. Reuse the preserved extracted bundle read-only, or extract
the hash-verified archive into a fresh attempt directory. Never overwrite
the original evidence. In that isolated directory on node2, run:

```bash
env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  /localhome/local-rohing/v2/venv/bin/python -c 'import torch, unittest; torch.set_num_threads(1); torch.set_num_interop_threads(1); suite = unittest.defaultTestLoader.loadTestsFromName("tests.test_composition_birth_stage2a_actor.NativeCPUCompatibilityTests"); result = unittest.TextTestRunner(verbosity=2).run(suite); raise SystemExit(0 if result.wasSuccessful() and result.testsRun == 2 and not result.skipped else 1)'
```

Capture stdout/stderr in a new receipt and verify both tests actually ran
without skips, along with the printed environment/thread binding. Do not
install dependencies or substitute a real model/tokenizer to reproduce this
tiny engineering assay. Reproduction is optional; no need to rerun a passed
test merely because conversational context changed.

## Still required

No reply to the remaining source-contract questions was present in the
23:40 UTC checkout read. Registered-route membership, boundaries, recovery,
termination/rendering and birth-core depth/history conventions remain open.
The future component does not resolve them. Full scientific semantic-object
and route inventories must not be replaced by toy-empty values. Continue
independent runtime source work, then complete the source bridge and separate
material/tokenizer/runtime preparation when definitions are bound.

Reduced BASE + D1 ATOM_LOCAL remains 280 reserved slots per state, 560 total;
qualified same-adapter authentic two-SLEEP is next, not storage-only repeats.
SEQ195 and Q0 are complete and are not relaunched. Formal C11 stays deferred.
No G3/H1/H2, parenting, mechanism freeze or complete-campaign claim follows.

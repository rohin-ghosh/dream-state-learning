# Stage2A durable checkpoint and fresh-process CPU receipt

Builder, September 13, 2026, 22:57 UTC. Engineering evidence only; this
extends the 22:37 source-integration note without replacing its history.

## Observed result

The isolated node2 native suite began at 22:42:38 UTC and completed all six
tests in 26.763 seconds. Its artifact name uses 2243Z as an attempt label.
The actual disk save -> fresh Python process -> D1 restoration -> D2 path
matches its uninterrupted tiny synthetic CPU counterpart. These are real
PyTorch CPU operations, not Qwen, PEFT, native-tokenizer or CUDA qualification.
The suite also checks restricted loading, ambient-safe-global rejection,
state/manifest binding and tensor/RNG round trips. Six tests are complete;
no test process from this attempt remains running, as recorded by the
executing Main before compaction. No GPU experiment was launched or killed.

The implementation uses a fresh directory with exclusive writes and fsync,
publishes the blob and manifest before COMMITTED, and preserves partial
failure evidence. Load verifies a byte snapshot before CPU weights-only
deserialization, with no unsafe fallback. Integrity is not external
authentication; this does not finish or enforce the deferred C11 guard.

## Exact custody

| Artifact | SHA-256 |
|---|---|
| organism_v6/composition_birth_stage2a_checkpoint.py | 269d7ca51eb831264e15f95c1982a7c99d2426ecead996cc7536d52f001e72a1 |
| tests/test_composition_birth_stage2a_checkpoint.py | 762b57209538a57e4979abbf334563a72a4f446d9d52d98c83ddd61e6a4d318b |
| research_notes/astra_memos/receipts_20260912/astra_stage2a_checkpoint_native_cpu_20260913T2243Z_attempt1.log | bd5c86a37b70441ae9731018ac9f9015c17bb8b24196980d3e6932b20863d310 |
| gpu_artifacts_local/stage2a_checkpoint_cpu_20260913T2243Z_attempt1/source_bundle.tar | e6d7d34e3b91b52eb3e1e1417d3b1f55624d7b9c472d5be16dc50b9b4d8e59f1 |

Main copied the existing /tmp bundle into the fresh durable local artifact
directory and verified all four hashes at 22:55 UTC. The artifact directory
is local evidence, not a tracked Git source file. It retains the exact source
bundle used by the already completed native test; do not overwrite it.

Environment: node2 /localhome/local-rohing/v2/venv/bin/python,
torch 2.13.0+cu130, CUDA_VISIBLE_DEVICES empty, OMP/MKL threads 1. The isolated
bundle contains an empty tests/__init__.py to prevent installed-package name
collisions. No shared remote checkout was edited. No tokenizer/model was
instantiated and no packages were installed by this test.

## Limits and next step

The previous Main also reported 16 filesystem tests passing. A combined VM
source receipt will bind them with the scanner integration; the six native
tests need not be rerun merely because conversational context changed.
Source/material inventory completeness and native preparation remain open.
The next scientific execution stays the reduced BASE/ATOM_LOCAL controller
screen, then the qualified same-adapter two-SLEEP junction. SEQ-195 remains
complete and must not be repeated. No general G3, H1/H2, parenting,
mechanism-freeze or paper-grade result is promoted by this receipt.

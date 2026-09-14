# Readout versus training-state continuity

Builder, September 13, 2026 Pacific. Tiny CPU integration evidence only.

The accepted actor and trainer had separate tests. This additional check
composes them on one caller-owned training model to verify that a readout
does not silently change the state used for the next update stage. No source
module changed; only a new test reuses the existing synthetic fixtures.

## Executed check

Node2 ran two tests, **2 PASS in 14.235s**, with real torch 2.13.0+cu130,
CUDA hidden, OMP/MKL and torch intra/inter-op threads prospectively fixed at
one. The training model is the existing tiny real-autograd fixture. Generation
is an explicitly synthetic callback, not HF generation or a model forward;
the tokenizer is also synthetic. No Qwen/model download, real tokenizer,
GPU science or package installation occurred. The local VM invocation skips
both tests because torch is absent; those skips are not the native PASS.

Success checks immediate live adapter/optimizer/Torch-RNG hashes, populated
gradients, requires_grad flags, mixed module modes and config identity after
readout seeds 0, 2**63 and 2**64-1. It then verifies D2 equals the no-read
control. The immediate comparisons matter: D2 equality alone could conceal
ambient RNG drift because the trainer restores its saved boundary RNG.

Failure checks that the original exception and its partial-output tensor stay
in memory, state/config are unchanged, and the actor refuses another generation.
No D2 is run after that failed readout; this test does not authorize continued
experimentation after a failed screen. The failure case does not independently
stress populated gradients/mixed modes. Full-model/cache immutability, actual
HF/Qwen generation and CUDA continuity remain untested here.

Turing independently reviewed the exact test/receipt/source pins read-only:
scoped PASS, no concrete flaw requiring repair. He executed no duplicate test.
This is not persistent behavioral learning, controller birth, parenting,
mechanism freeze, runtime qualification or a completed sprint.

## Custody and reproduction

The receipt contains the complete command and observed timestamps:
September 13, 17:15:37–17:15:53 Pacific (September 14, 00:15:37–00:15:53 UTC).
Its immutable UTC fields are retained as emitted by the execution clock.
Source was transferred to a fresh isolated node2 /tmp directory; the shared
remote checkout was not edited. Main rechecked actor/trainer/test hashes on
node2 after execution. No test process remains running.

| Artifact | SHA-256 |
|---|---|
| tests/test_composition_birth_stage2a_readout_continuity.py | a259a03dd53b457743d30ed2a1482729372738130e94b114d01a9aa711899f95 |
| organism_v6/composition_birth_stage2a_actor.py | 9b376d43a7564b00ef9e75513853a735103bad3b055e527af97e8ede5359957a |
| organism_v6/composition_birth_stage2a_training.py | 7b5669dfccb1ab68e27dd14a9f608ec2d746052484ee3e6c3ca96b4e4efd436e |
| research_notes/astra_memos/receipts_20260912/astra_stage2a_readout_continuity_cpu_20260913_attempt1.log | 0a360fce49b78d4a721136983cb3b2b4bc46c3096d0158218a405aabb697f203 |
| gpu_artifacts_local/stage2a_readout_continuity_20260913_attempt1/source_bundle.tar | d4d4d8ea249cf3438c2a686357ee2b036d7f9c5cea69fe3c130624232e84f347 |

The same tar remains at /tmp/astra_stage2a_readout_continuity_20260913_attempt1.tar;
the extracted tree on node2 is /tmp/astra_stage2a_readout_continuity_20260913_attempt1.
Archive includes the committed Stage2A source/tests, this new test and an empty
tests/__init__.py to isolate test imports. Reproduce only in a new receipt or
directory; do not overwrite the passed attempt or rerun solely after compaction.

Durable screen custody is a separate worker-owned implementation in progress.
Registered-route/core definitions and the complete source/material/native
opening remain pending; this fixture neither resolves nor bypasses them.

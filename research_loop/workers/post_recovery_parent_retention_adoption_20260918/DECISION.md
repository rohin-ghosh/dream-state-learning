# Decision: stage only; NO-GO for live adoption

2026-09-18. Non-material CPU-only preparation of the existing phase2 repair.
No launch/restart/hot patch is authorized or implemented by this worker.

## Exact applicability

Read-only `ovx4_ssh.sh` observations at **22:06:39 UTC** and **22:08:29 UTC**
match phase2's exact process incarnations, cwd, argv, guard bytes, and **all
207 guarded Python files per life**. There are no extra unguarded Python files
in either observed source closure. Both members have identical source pins.

| Life | PID | /proc start ticks | Guard SHA-256 |
| --- | ---: | --- | --- |
| R231 learner | 493500 | 10070880 | `282ad372328b6244f0cc82b4cfbd39de0fcdd2b7a748c681449f937cbfadd632` |
| R232 frozen | 471737 | 9987073 | `197463ab56dab2b04a88797c28dffd854a56bd1a8756cdfa611f0995690d7a0b` |

The phase2 patch SHA-256 is
`7053d826efcfbc6ee6a8f44f36a8dbe8c179dd4d9ffb485a7ac548a075e876f1`.
Strict patch application reproduces the tested fork byte-for-byte:

| File | Observed preimage | Staged postimage |
| --- | --- | --- |
| `gpu/orch_r184_think_act_learn.py` | `65a20ebfaaa47f8b38be6e2666ad9cc82aaf57a783510a6b5aff50f8724d0e46` | `88bade651bb372c7ee0f00848deb767dbeec70ec5a208b01603f92539df6d505` |
| `organism_v6/orch_r125_continual_stream.py` | `baf6cc915dd430db580a28f9e6a21678c5a90ba59a9fd4b5651943cc3db6484e` | `e81275bf891dec9ad68572f6432c5709b8a1099fbc6f08833bb39db65758b2ce` |
| `organism_v6/orch_r124_train_history.py` | `1211c8f312f8572dd51938ffde4806f7171e6368f1c5ea12a296ff02567e4625` | `ec7ecd7ebf395885606e7b500a47baedd11172a4c46e23b8d05d569dc8fac1d3` |

Use `stage/STAGING_RECEIPT.json` as the machine-readable authority for hashes.
It preserves the other **204 source pins** for each life, including R232
recovery, frozen optimizer implementation, R205 runtime, R227 row policy,
native checkpoint restore and journal implementation. Context/threshold/output
budgets remain 6144/4608/512. No plans, guards, leases, parent files, checkpoints,
RNG payloads, working state or journals are staged or modified.

**Do not replace a source tree with the main checkout.** The observed pair's
journal hash is `08dab0bb84596b522fc08db8cdb2c4a26db9e416acfcf9cc35bacdd233d924a4`;
the local checkout journal at review was
`0b0d309cbb0399be3b9488fab0eb049063e321b927bf5b4b2c43369448bdf06f`.
The pair's `checkpoint_tail` plan field is absent/null and there is no
`gpu/checkpoint_tail_runtime.py` source pin. Main's separate C2/checkpoint-tail enrollment is not this pair's
baseline. This three-file overlay neither imports that enrollment nor rolls it
back: all other files must remain untouched. If one of the three target files
changes during C2 integration, these bytes cease to be an applicable preimage;
do not blindly overwrite or merge them. Rebind and retest separately.

## Existing mechanisms reviewed — not an adoption hook

1. **The live driver has no source-adoption handoff.** Hash-bound
   `gpu/orch_r184_think_act_learn.py:900` creates one driver and loops through
   wake, sleep completion, `R184_LEARN_COMPLETE`, console drain/readout and the
   next wake. There is no source-switch/reservation callback. The actual
   R205 `birth_loop` metadata (line 284) calls `compact_birth` and `original_loop`,
   not an adoption hook. `SOURCE_STRUCTURE_OBSERVATION.json` binds AST call
   metadata to the actual guarded source, without copying remote source text.
2. **`continue_pair.py` exists, but is not reusable for this repair.** In
   `../rohin231_curriculum_birth_20260918/recovery_20260918T1646Z/`, it requires
   `pins == guard['source_pins']` at line 79. Changing any of these three files
   fails `identical_runtime_source`. Its identities at line 18 are the OLD
   399101/412570 incarnations, not 493500/471737. Its `extension_spec.py:42`
   requires a strictly forward deadline change; current deadlines already
   equal the fixed authority. It uses pidfd SIGTERM at line 158 and dispatches
   after exact old-process exit and an unchanged journal head. This is an
   old, specifically authorized same-source continuation, not a resident hook.
3. **`prepare_resume.py` and receiving-sidecar retry are also insufficient.**
   `prepare_resume.py:38` requires the old native absent, and line 60 requires
   `exact_old_runtime_source_provenance`. The sidecar retry binds the existing
   recovery constructor's exact checkpoint; it explicitly retains source pins.
   Neither reserves/stops the current pair at a boundary for a source change.
4. **Native resume supplies primitives, not the missing handoff.** Exact
   live-hash `gpu/orch_r125_continual_native.py:728` restores stream/working
   state from the same journal, requires a resolved saved-RNG boundary and one
   matching model checkpoint. Lines 334–363 restore adapter, AdamW, Python,
   CPU and CUDA RNG. The actual journal constructor metadata has `fcntl.flock`;
   guard supervisor metadata has a `DISPATCH_ONCE` directory. These prevent
   conflicting writers / repeat dispatch for an attempt; they do not authorize
   a new attempt, prove the old native exited, or atomically reserve its COMPLETE.
5. **C2 is not an interchangeable controller.**
   `../rohin233_recovery_node4_20260918/c2_checkpoint_tail_recovery.py:19`
   is pinned to a different root, UID, native PID/start, guard, journal,
   COMPLETE11502, nonzero optimizer state and specific source-delta allowlist.
   It does not cover this learner/frozen pair. The P7/C2 deadline controller
   and old R165 frozen serialization repair likewise are not generic R231/R232
   source-adoption hooks. None was executed.

**Conclusion:** an exact-COMPLETE continuation implementation exists, but no
existing supported end-to-end mechanism was found that adopts this source
delta for the running pair while preserving all required state and excluding
a duplicate native. Do not improvise a restart, signal, monkeypatch, or source
swap. The staged artifact deliberately contains no launcher, receiving guard,
checkpoint selection, PID mutation or permission to run. A future implementation
would be separate work, not execution of this worker's receipt.

## CPU evidence and limits

`CPU_TESTS_FINAL.log`: **45 passed** — 19 helper/refusal regressions, 17 original
phase2 retention tests, five original retention/masking contracts, four original
pair COMPLETE predicate tests. The earlier 43-test log is preserved too.
The 19 helper tests cover whole-closure drift, repinning, PID reuse, dead process,
guard/plan/lease/life/deadline mismatch, expired capture, exact patch pre/postimages,
non-fork receipt bytes, missing member, extra file and worker-only no-overwrite
staging. These are not GPU, checkpoint-payload, deployment or scientific tests.

No checkpoint tensor/RNG payload or private eval score/panel was copied.
Observation proves disk/guard/process correspondence at its timestamps, not
resident Python heap identity, a currently reserved boundary, no sampling gap,
or future applicability. The transient parent handle must begin on a genuine
future THINK; no mid-THINK reconstruction or adapter-learning claim is made.
No live writes, messages, signals, GPU jobs, parent changes, lease extensions,
publication or commits occurred. Main integrates only allowlisted worker files.

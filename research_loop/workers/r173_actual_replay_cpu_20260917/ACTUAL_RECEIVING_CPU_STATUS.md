# R173 actual receiving CPU attempt — failed, no retry

## Outcome

One sanctioned `gpu/ovx2_ssh.sh` invocation consumed the sole candidate attempt.
Receiving execution ran **2026-09-17 15:11:04.702380–15:11:07.251714 UTC**
(**08:11:04.702380–08:11:07.251714 PDT**). There was no second remote call.

**This is not passing CPU evidence. ASSEMBLY must continue to refuse a rebind.**
The transport returned 0, but the receipt is `FAILED_NO_RETRY`, `success=false`,
`test_suite_success=false`, and `evidence_rebind_eligible=false`; the local
launcher returned 1. Unittest reports **85 test cases, 87 error events, zero
assertion failures, zero skips**, with only **five recorded passes**. Error
events include subtests/cleanup, not 87 separate test cases. The receipt's
flat `outcomes` array is not exhaustive for subtests; its raw `test_output`
and unittest totals are authoritative. No tests were removed or weakened.

## Source custody actually established

- Independent, create-only scratch:
  `/localhome/local-rohing/orch_r173_actual_replay_cpu_20260917_attempt1`.
- Original source:
  `/localhome/local-rohing/orch_r144_node3_targets_20260916t1515z_2/physical1/source`.
- Original guard:
  `/localhome/local-rohing/orch_r144_node3_target_physical1_20260916t1545z_5/GUARD.json`,
  SHA256 `8bbb6c007083884574b427b318ef3e466f26e514452b5ee5e7972801aca8ce9d`.
- Guard-bound original plan:
  `/localhome/local-rohing/orch_r144_node3_targets_20260916t1515z_2/physical1/PROPOSED_PLAN.json`,
  SHA256 `cde51871c4ebb8e0b95b484c79f6a6bab0cb7ac424fd3c893a477ff8d68b1413`.
- **1,854 original guard-whitelisted Python files + exactly three frozen R168
  helpers = 1,857 source files.** Every original byte hash matched; the exact
  candidate inventory remained unchanged after tests. No suffix boundary/loss
  helper, newer plain-context, STARTUP, non-Python artifact, or other unvetted
  file was added to the candidate source. The harness and single TRAIN fixture
  were separate, outside `source/`. This CPU scratch is not a ready staging tree.
- The bound-input reader counted **23,293,408 bytes** for the original guard,
  plan, and whitelisted Python source. This counter excludes candidate
  inventory rehashes, fixture I/O, and interpreter/library reads; it is not a
  global I/O measurement. No journals, saved-life checkpoints, evaluator
  artifacts, condition maps, answers, or score data were read.
- Candidate-manifest SHA256:
  `0148d734ad436e189829cc946028e4d04fdccd081ca6375211a6905291f6ac9d`.
  Its serialization is `receiving_cpu.encoded(candidate_source_sha256)`:
  sorted, two-space-indented JSON with one trailing newline, not replay's
  compact JSON digest.

| Actual dependency | Receiving SHA256 |
| --- | --- |
| `gpu/orch_r125_continual_native.py` | `cdb54252763472fd21ea12fd7694b208d968422c375dbf0647088cde736e6d48` |
| `gpu/orch_r108_guided_native.py` | `df88511d8ff24170cdbb3739040a75c8788d7cce9157f270fe7ae89d0839187c` |
| `gpu/orch_r144_sleep_targets.py` | `8070e8047dd7d795df727204d2e79a2b2f7d906d88c095ac07777a8e566ed9a9` |
| `organism_v6/orch_r125_plain_context.py` | `b3859e4a45d53fc67c51add5dad8431985ca0adda901389e0206819a56245d92` |

The receipt records 33 executed project-file paths and their actual hashes,
including all three runtime dependencies. Native module code came from
candidate `source/gpu/orch_r125_continual_native.py`, not the workspace or
archived fixture native. Module execution counts are **imports**, not counts
of successful `NativeChild.sleep` calls. No focused native test passed.

## Precise failure and missingness

**Primary cause is this sidecar's over-restrictive audit fence, not a discovered
baseline incompatibility.** `freeze_selection -> saved_boundary -> read_bound
-> directory_fd` opens `/` with `O_RDONLY | O_DIRECTORY | O_CLOEXEC` to safely
walk directory descriptors. The fence incorrectly rejected that directory
traversal as `read_outside_candidate_or_installed_runtime:/`. Fixture setup
failed before the native replay assertions. This was not covered by the
11 preflight local unit tests; their success did not establish integration
compatibility. The post-attempt diagnostic test reproduces this exact fence
mistake locally without a remote rerun. The attempted runner stays unchanged.

Other denied operations recorded by the fence:

| Denial | Count | Interpretation |
| --- | ---: | --- |
| Reading directory `/` | 86 | Legitimate descriptor traversal incorrectly denied. |
| Writing `/dev/null` | 2 | Torch's transitive `dill` import probes file types; fence incorrectly forbade the sink. |
| Reading `/proc/174526/maps` | 1 | Denied runtime metadata read; contents were not read. |
| `subprocess.Popen` | 2 | Blocked before child creation. Commands were not captured; do not infer them. |

The real Torch CPU test errored during library import at `dill`'s `/dev/null`
probe. It did **not** establish Torch unavailability, perform the tiny optimizer
comparison, or produce a CUDA-initialization observation. `torch.imported=false`
and `cuda_initialized=null` are not a successful CPU-training receipt.

Two retained native tests also require prohibited R145 suffix helpers. They
failed earlier in setup here, so their anticipated missing-import problem was
**not reached**. No suffix code was copied, no test was silently skipped, and
no passing substitute receipt was fabricated.

The five passes cover a foreign-boundary pre-read refusal and four guard-patch
checks. They do not establish baseline-plus-four-update execution, completed
sleep, numerical equality, or receiving replay readiness. No retry, remote
repair, second candidate, or edited post-hoc passing receipt is authorized.

## Preserved provenance and handoff

All local paths below are in this R173 directory:

- `ACTUAL_RECEIVING_CPU.json`: exact receiving stdout bytes, SHA256
  `26e9efb519fbc0a8129fd47daa115d71b715a3907ff19e506ca3ee69359de285`.
  Remote copy: scratch `RECEIVING_CPU.json`; local `WRAPPER_STDOUT.txt` is
  byte-identical. Contains all test output, path adaptations, source/read
  manifests, module hashes, failures, and denials.
- `receiving_cpu.py`: attempted runner, SHA256
  `79f68ba20697d63aa8a80cb52956855bd5886660489dffe190c088b45e4c8637`.
  It is intentionally **not repaired after this attempt**.
- `run_once.py`, `ATTEMPT_STARTED.json`, `PAYLOAD_MANIFEST.json`,
  `WRAPPER_RESULT.json`, `WRAPPER_STDERR.txt`: transfer and one-attempt custody.
  Existing local and remote latches prevent the same attempt being repeated.
- `LOCAL_CPU_TESTS.json`: 11 preflight local tests passed; source hashes bind
  the actual runner and original test file. This is runner-unit-test evidence,
  not receiving integration approval.
- `test_attempt_evidence.py`: post-attempt, local-only integrity and diagnosis
  tests; no candidate execution or remote access. All seven passed, recorded
  separately in `POST_ATTEMPT_LOCAL_TESTS.json`; this does not upgrade the
  failed receiving result.
- `ASSEMBLY_V2_EVIDENCE_REBIND_DESIGN.md`: design only; explicitly rejects this
  failed receipt as admission/CPU authority.

R170's bootstrap and staged physical1 source were not touched. No native
process was signaled, no model/7B load or GPU job was launched, and no provider
call, operational GO, saved handoff, wall/lease change, evaluator admission,
human ratification, or saved-state-ownership claim was made. Main retains all
operator, source lifecycle, recovery, and scientific gates. The actual b385
source-copy mismatch is explained; **usable actual receiving CPU proof remains
missing**.

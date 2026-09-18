# Independent R174 receiving review — September 17, 2026

Latest disposition: R174 remains rejected. The separate, hash-bound R175
receiving/source-only approval is appended below; it does not relabel R174.

## Verdict: reject R174 as positive receiving/rebind authority

The consumed attempt ran 2026-09-17 15:33:23.797396–15:33:30.737638 UTC.
**All 85 original tests passed, zero failures/errors/skips, including the real
tiny Torch CPU exact-update test. Nevertheless the whole attempt is
FAILED_NO_RETRY, success=false, evidence_rebind_eligible=false.**

The final fence gate rejected three subprocess requests before child creation:

1. `/sbin/ldconfig -p`
2. `/usr/bin/gcc -Wl,-t -o <R174 scratch>/tmp/tmp1zwirrtm -ldl`
3. `ld -t -o /dev/null -ldl`

The receipt contains their three metadata records and three matching denial
strings. No allowed subprocess probe was recorded. Main attributes these
requests to optional ctypes library discovery during Torch import; the command
shapes are consistent with that explanation, but the receipt does not contain
per-request caller stacks. These were denied requests, not executed compiler
or linker jobs. An isolated independent local audit-hook test confirms the
three requests raise before process-creation primitives can run.

The failure is preserved, not converted to a skip or a positive receipt. SSH
wrapper returncode 0 means the receiving program returned its JSON; it does
not mean success. Independent tests confirm `run_once` returns 1 for these
exact failed JSON bytes even with wrapper returncode 0, and its consumed latch
prevents another invocation. No retry of R173 or R174 is approved.

## Harness delta against consumed R173

- The new scratch is distinct and create-only. Runner, helper, original-test,
  TRAIN-fixture and test-support payload hashes bind the transferred bytes.
  The same guarded source reader retains the 64 MiB total/2 MiB per-file bound.
- Read-only ancestor directory opens repair descriptor traversal; subsequent
  foreign file reads remain rejected, including relative traversal via a
  directory descriptor. The exemption requires O_DIRECTORY and no write flags.
- The actual `/dev/null` character sink can be opened; removal, chmod and
  unrelated device/file access remain outside the allowance. Own maps/status/
  stat resolve to the current process only; foreign process metadata and
  environment files remain denied in the reviewed cases.
- Only the listed `uname -p` executable/argv combinations with standard PATH
  gain a subprocess exception. No such call actually occurred in R174. This
  is an allowance for the pinned trusted test/import workload, not a general
  subprocess sandbox or an arbitrary-child-environment security guarantee.
  Compilers/linkers, other subprocesses, shell operations, signals and network
  operations remain denied by the reviewed hooks; native extension behavior
  is not a general adversarial Python containment proof.
- Both suffix-related negative tests remain intact. Their two exact R145
  helpers are separately pinned and executed from scratch/test_support, never
  copied into or counted as runtime candidate files. The support import hook
  is a test harness capability, not a learner runtime addition.

No further harness mutation is needed to explain this failed result: the
fence deliberately rejects the unallowed library-discovery requests. Main's
separate R175 proposal needs its own exact-byte scope and fresh attempt; do not
silently add compiler/linker permission or remove R174's recorded denials.

## Full artifact checks, not just result labels

The independent tests parse the entire receipt and programmatically check:

- Exact equality of ACTUAL_RECEIVING_CPU.json and WRAPPER_STDOUT.txt, wrapper
  stdout/stderr hashes, empty stderr, runner hash, payload manifest and the
  recomputed full payload hash, scratch identity and exact wrapper command.
  Substituting the old R173 stdout for R174 is refused despite shared schema.
- All **1,857 candidate source pins** equal the consumed R173 candidate map:
  1,854 bound original Python files plus exactly three R168 helpers. Native is
  `cdb542...`, plain-context is the actual `b3859e...`, and neither R145 support
  file is present in that runtime map. Manifest digest is
  `0148d734ad436e189829cc946028e4d04fdccd081ca6375211a6905291f6ac9d`.
- All **1,856 bound input-read references** are exactly original guard, original
  plan, and the 1,854 source files, with unique paths and matching hashes.
  Their byte counts sum to **23,293,408**, under the bound, and every individual
  file is under 2 MiB. No STARTUP, checkpoint, model-weight, saved-life or
  evaluator input appears in that bounded read list. Candidate/library reads
  are separate from this original-source counter.
- All **38 executed runtime-file records** and every loaded project module
  resolve to the appropriate source/support tree with matching pins. Actual
  native and all three runtime dependencies were executed from candidate
  source, not the archived workspace fixture. Execution counts denote code
  execution/imports, not proof of model training or handoff.
- Every original test file hash matches the pinned repository bytes. Adapted
  hashes are independently reconstructed; full AST comparison permits only
  the exact native/guard/fixture path expressions. All 85 named methods have
  one PASS outcome, with no method removal, assertion/tolerance change, or
  loss of either suffix-negative case.
- Actual Torch imported on the receiving host and the tiny CPU optimizer test
  passed; CUDA initialization was false. CPU visibility/offline flags and all
  no-GO/no-handoff/no-ownership/no-admission flags remain explicit. The final
  failure and false rebind eligibility override the successful test subset.

These are checks of the exact receiving artifacts returned through Main's
wrapper. This reviewer did not re-read or execute anything remotely, inspect
live learner state, or claim a fresh remote filesystem census. The guarded
runner's per-file read/hash checks are the provenance underlying the artifact.

## Independent local evidence and pins

`test_receiving_review.py` plus Main's `test_receiving_repair.py`:
**30 passed**, no skips or expected failures. Review probes use local fixture
directories, mocked wrapper invocation, and one isolated CPU audit-hook probe;
they do not execute the receiving harness or call the sanctioned SSH wrapper.

```bash
TMPDIR=/tmp CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/tmp/r136-pytest-support python3 -B -m pytest -p no:cacheprovider \
  research_loop/workers/r174_receiving_cpu_repair_20260917/test_receiving_review.py \
  research_loop/workers/r174_receiving_cpu_repair_20260917/test_receiving_repair.py \
  -q --tb=short -rs -rx
```

| Artifact | SHA256 |
| --- | --- |
| receiving_cpu.py | `6ebeeed6786b2194f874cd1a66a3164b0c302a1054d0fed8f36b48e9cd09b2f2` |
| run_once.py | `9fcb4d27ba7c9a7aa1b1b7df1fa3d70e5f93bb117d5ccbd59f53c338c2c837f8` |
| test_receiving_repair.py | `362ec5d7feaf162d30756b477f1ccc8433b52eba9896d16eadf021f6d98d955e` |
| SCOPE.md | `be2f1a30f0baa7861aeb9b84109c0eb492741ae8108ecccc5a9dbb5da5a84da2` |
| ACTUAL_RECEIVING_CPU.json / WRAPPER_STDOUT.txt | `d14cda179688a3d145ea1ae5e8039c4e5c4dd3f530ded4d28ac523051a2e28dd` |

Only this report and the separately named review tests are reviewer-owned.
All consumed source/receipt bytes remain unchanged. This rejection concerns
receiving evidence only; it neither reopens the R170 V2 recovery review nor
grants GPU, staging, saved-state handoff, replay, lease, or scientific GO.

## Final R175 disposition — approved receiving evidence only

Independent verification completed September 17, 2026, 15:53 UTC. This section
approves the consumed R175 receiving proof for the exact physical1 original
source plus three pinned R168 helpers. It is not an approval of a generic
receiving utility or any learner lifecycle action. R173/R174 source, attempts
and receipts remain untouched; R174 is still FAILED_NO_RETRY and ineligible.

The R175 attempt ran **15:45:53.545129–15:46:00.041766 UTC**. Its actual schema
is R175_ACTUAL_RECEIVING_CPU_V1 and status CPU_TESTS_PASS_NOT_ADMISSION:
**85 PASS, zero failures/errors/skips/denials**, including the real tiny Torch
CPU baseline-plus-four-update test. CUDA remained uninitialized. Success and
receiving-rebind eligibility are true; admission, saved-state ownership,
saved handoff, operational GO, STARTUP copying and full-source-approval flags
remain false. There is one consumed attempt, no retry permission and no
failure, failure_type or traceback. No receipt has been promoted in place.

### Full evidence and exception verification

- Recomputed transferred payload and runner digests; exact wrapper command,
  scratch, latch and payload manifest agree. Actual JSON is byte-identical
  to wrapper stdout; transport returncode is zero and stderr is empty with
  matching recorded hashes. This verifies the complete receipt, not its label.
- All 1,857 runtime pins equal the consumed R173 and R174 candidate maps:
  1,854 originals plus three helpers. The complete manifest digest remains
  `0148d734ad436e189829cc946028e4d04fdccd081ca6375211a6905291f6ac9d`.
  Actual native is cdb542 and actual plain-context is b3859e, not the historical
  dcfd variant. All 1,856 original source/guard/plan reads agree; their byte
  counts total 23,293,408, below 64 MiB, each at most 2 MiB. Source is unchanged.
- All 38 executed runtime files and every loaded project origin match their
  source pins. Both R145 negative-test helpers are separately pinned under
  test_support and excluded from the runtime inventory. Every original test
  hash, exact path-expression-only AST adaptation and all 85 distinct method
  outcome IDs were checked. No assertion, tolerance or method was weakened.
- The sole actual allowed process request is exactly `/sbin/ldconfig -p`,
  with cwd null and the replacement environment exactly PATH=/usr/bin:/bin,
  LANG=C, LC_ALL=C. No provider/credential variables are forwarded or logged
  by this exception. The Popen shim requires the exact stream/option contract;
  the audit allowance requires its scoped context and revalidates both files.
- Both wrapper and `.real` are canonical, root-owned, mode 0755 and hash-bound
  in the preflight and actual probe record. Recomputed the 387-byte wrapper's
  script digest from its captured text. Its dpkg-trigger branch requires zero
  arguments, so the exact one-argument `-p` request cannot enter it. The final
  exec forwards `-p` to the separately pinned 1,051,280-byte ELF. Preflight
  inspection itself reports no binary execution or remote writes.
- Compilers, linkers, altered ldconfig argv and shell forms remain denied.
  Independent tests exercise denials without starting those children; author
  tests additionally exercise dirty env cleanup, option rejection, both-file
  hash/canonical/ownership drift, and scoped Popen handling with a fake spawn.
  The inherited uname exception did not execute in R175. These are checks on
  pinned trusted tests/imports, not a hostile-native-code containment proof.

### Frozen R175 evidence

All paths in this table are under sibling `r175_receiving_ldconfig_20260917`.

| Artifact | SHA256 |
| --- | --- |
| ACTUAL_RECEIVING_CPU.json / WRAPPER_STDOUT.txt | `8f60e4ae3d9e21766b46f816822852285b2f757a0cb952089184d38f1df9b1b3` |
| receiving_cpu.py | `a4314df92c8aa5c75156d3085bc7c5d698152d6f15a9c93ba5d53193fd8da38c` |
| run_once.py | `f325353770964800a0d714ffad5cd9619c03b61e74452f01dc6a2011e257dabf` |
| SCOPE.md | `6d793fbaab2cd3aa7ab0a8a2e4197f1d7f5e1e8363508efb347c327beb269caa` |
| test_ldconfig_permission.py | `a382e2dc6c74298f5ab6e5af7caf9263126e5dbc78411b44a2e4a8062ba9315e` |
| /usr/sbin/ldconfig (receiving host) | `bfd5df90c7f070feab584435f106f254ffffaa268a04de5b5c3bd61d59c092f3` |
| /usr/sbin/ldconfig.real (receiving host) | `aa6de6d24c9223de013f6294c1db270c0c5247741a35127a0e058bf386725666` |

### Independent CPU result and limit

Final combined local run: **118 passed, 48 subtests passed; zero xfails,
skips or failures**, covering both receiving review revisions, R174 author
repair tests, R175 exception tests, final assembly review/author tests and
scaffold wiring tests. See the exact command and final source pins in
`../r170_replay_boundary_20260917/REVIEW_ASSEMBLY_V2.md`.
Logs are `/tmp/r170-r175-independent-final-CPU.log` and `.xml`.

No remote wrapper, receiving rerun, GPU, model, learner signal, scaffold copy,
selection or GO was executed by this review. The real tiny CPU test is not
an actual learner checkpoint restore or observed replay dose. **No remaining
receiving-proof blocker was found for these exact consumed R175 bytes.**
Source scaffold permission is bounded separately in REVIEW_ASSEMBLY_V2.md;
handoff/admission/replay authorization is explicitly absent.

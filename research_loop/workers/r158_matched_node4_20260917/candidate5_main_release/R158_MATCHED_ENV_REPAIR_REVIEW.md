# R158 TRAIN environment E1/E2 independent repair re-review

## Verdict — September 17, 2026, 04:29 UTC

**APPROVE — E1 and E2 repairs only, at the exact source/test hashes below.**
No additional concrete blocker was found in these two repaired paths. Approval
was withheld until candidate2's installed actual-adapter evidence arrived and
its receipt/log/source joins were checked. This is not approval of staging,
source freezing as a whole, admission, a GPU launch, parent-helper changes,
capacity, live child delivery, or scientific improvement.

The original `research_loop/workers/R158_MATCHED_CAPACITY_ENV_REVIEW.md` is
preserved unchanged at SHA-256
`4fc265dc7f5032b6b34677fccfb726259a80281801aa0a10fda0e3dcc0ec6749`.
Its rejection still describes the old helper/test bytes. This new artifact
disposes only its E1/E2 findings for the replacement bytes; it does not
retroactively approve the rejected version or erase the original concerns.

Only this new report was authored. No source/test/parent-helper edits,
coordination writes, reverts, staging, remote execution, package installation,
GPU/model calls, or live-answer inspection were performed by this reviewer.
Local CPU tests and inline probes used temporary synthetic fixtures, empty
CUDA visibility and disabled bytecode/pytest caches. Main and the staging
worker retain ownership of parallel work.

## Exact approved bytes

| Reviewed file | SHA-256 |
| --- | --- |
| `gpu/orch_r158_train_gym.py` | `dd88f24f5ff12949e94cc8a78c398c699219c9823b93027dd878342a824bbc8b` |
| `tests/test_orch_r158_train_gym.py` | `c30b41de00bdefacdac56d030e224236986e2ad220c23b5f35887fbc5e792de5` |

These hashes were checked before and after the local tests, and match the
installed-adapter receipt's source inventory and receiving status. Changes to
these bytes require another appropriately bounded review, not inherited PASS.

## E1 — resolved: actual repository adapter import and installed path

`gpu/orch_r158_train_gym.py:46` now imports the actual `ReasoningGymGym` class;
construction and the `inspect.getfile` ledger binding use the same class.
`tests/test_orch_r158_train_gym.py:56` calls the real `dataset(0)` with only the
package-version lookup replaced by a wrong-version result. It now reaches
`pinned_reasoning_gym_version` rather than raising the original ImportError.
An independent inline spy confirmed that the real import reaches exactly the
`reasoning-gym` version lookup, which is called once before refusal.

The new parameterized installed test at
`tests/test_orch_r158_train_gym.py:145` does not replace `dataset` and covers
task indices 0/1/2: countdown, knights_knaves and mini_sudoku. It calls the real
adapter, asserts package version 0.1.25, checks the actual verifier, offers the
task, records a synthetic child answer through the real journal/stream,
checks that committed answer, verifies prefix/target mask flags, then consumes
feedback and verifies its appearance in a subsequent rendered prefix.

The test intentionally supplies the reference as a **synthetic fixture child
answer**. Its success is integration evidence, not model problem-solving,
learning, or live child-task delivery. The reviewed log prints no answers.
Its three-family scope is not represented as a new 24-task adapter test.

Candidate2's required `bootstrap_reasoning_gym.txt`, repository adapter and
split ledger are present in the recorded inventory with hashes matching the
local dependencies below. This closes the original wrapper-execution gap,
unlike the earlier direct package-only smoke.

## E2 — resolved: latest explicit declaration, no stale fallback

`gpu/orch_r158_train_gym.py:65` now enumerates XML starts and line-form answer
declarations together in text order, selects the last declaration, then
requires its own terminator/completeness. A later incomplete XML or line
submission no longer falls back to an older closed answer in either format.

Independent checks reproduced all four previously dangerous committed cases:

| Capped synthetic child output | Repaired result |
| --- | --- |
| `<answer>4</answer>\n<answer>5` | `NO_COMPLETE_ANSWER` |
| `<answer>4</answer>\nAnswer: 5` | `NO_COMPLETE_ANSWER` |
| `Answer: 4\nAnswer:` | `NO_COMPLETE_ANSWER` |
| `Answer: 4\n<answer>` | `NO_COMPLETE_ANSWER` |

For each case, the independent probe used the real offer/journal/stream/check
path, replaced the grader and feedback publisher with fail-if-called spies,
and verified **zero grader calls, zero publisher calls, `checked=false`, and
no answer-attempt directory**. This directly establishes refusal before
grading, not merely an absence of a feedback assertion in a test.

Complete mixed-format revisions now select the later answer: an earlier XML
`4` followed by terminal line `Answer: 5` selects `5`; the newline-complete
capped equivalent also selects `5`; a later closed XML answer supersedes an
earlier line answer. Complete XML/line answers followed only by unrelated
capped prose remain usable. Five independent parser cases exercised these
positive boundaries in addition to the checked-in parser and committed-row
regressions at test lines 14, 114 and 130.

This disposition concerns the supported explicit-declaration contract, not
general natural-language intent inference. The original review's C1
cross-task/operator-attribution limitation is unchanged and not silently
resolved: this repair does not establish global response deduplication or
distinct task attempts. Parent-helper review was explicitly excluded.

## CPU evidence

### Independently executed locally

**40 passed, 3 skipped in 1.48 seconds**:

```bash
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/r136-pytest-support:$PWD python3 -B -m pytest -q -rs -p no:cacheprovider tests/test_orch_r158_train_gym.py
```

All three skips were the installed tests at line 147 because `reasoning_gym`
is absent from this interpreter. They were not counted as passes or used to
approve E1. The independent import/no-grader/no-publisher and positive-parser
probes described above are additional synthetic checks, not extra pytest
passes. The capacity suite was not rerun.

Main's `research_loop/workers/r158_train_gym_20260917/CPU_TESTS_REPAIR1.log`
reports **180 passed, 3 skipped, 34 subtests passed in 11.80s**, SHA-256
`0e1f5d340f189e0ee4a930ac6c45780bfbb8b958be208fce4e7933519a7a1a6e`.
This is supplemental author-side evidence, not another independent run.

### Installed actual-adapter evidence — inspected after arrival

Directory: `research_loop/workers/r158_matched_node4_20260917/`.

| Artifact | SHA-256 |
| --- | --- |
| `CANDIDATE2_RECEIVING_INSTALLED_ADAPTER.json` | `4e4734ecd0c231b327e54686a4718aa61730e9dadb2e4bab9e2d64f812381780` |
| `CANDIDATE2_RECEIVING_INSTALLED_ADAPTER_TESTS.log` | `b0a2cb5ff076a5c53b7b0fd213a4afa2e9cfdae80eaefecc0a24b65b78f6c195` |
| `CANDIDATE2_RECEIVING_CPU.json` | `b198f0fc39605076781cf50a26414e917397481cb2a442810124935c8a35ce09` |
| `CANDIDATE2_RECEIVING_CPU_TESTS.log` | `e0e1b20ae4e7ca95e15357fc7a7782490b534d8e71a18cbe2204027a57563e89` |
| `CANDIDATE2_RECEIVING_STATUS.json` | `594226b5e6186f3bf0ddcf087df1efa299963449e79915ec18bd5284cb09bdea` |

The dedicated installed receipt reports host `[REDACTED_HOST]`, exit code 0,
`passed=3`, `actual_dataset_not_mocked=true`, `GPU_calls=0`,
`unchanged_source=true`, `source_frozen=false`, and no real-child delivery.
Its command selects exactly
`tests/test_orch_r158_train_gym.py::test_installed_actual_adapter_offer_check_cpu`
using `/localhome/local-rohing/v2/venv/bin/python -B -m pytest -q -rs -p
no:cacheprovider`. The matching log says **3 passed in 1.76s**, without skips.

I independently recomputed the four status-referenced receipt/log digests,
checked the dedicated receipt-to-log hash join and PASS/exit/count fields,
and compared all five relevant source/dependency inventory entries to local
file hashes. The broader receiving log reports **748 passed, 5 skipped in
14.61s**; its skips concern the unpatched-source staging fixture, not these
three installed tests. That broader suite is supporting context only, not
an expansion of this review or an additional independent execution.

These are staging-worker-produced installed-run receipts whose bytes and
joins I independently verified, not a claim that I personally executed on
the receiving host. The dedicated actual-adapter run, the reviewed test body,
the exact source binding and the local adversarial regressions together
satisfy the requested E1/E2 re-review prerequisite.

### Bound adapter dependencies

| Dependency | SHA-256 matching installed inventory |
| --- | --- |
| `organism_v6/reasoning_gym_gym.py` | `da9879537d33923c9702b1a5b3d63d6a2fcb396a64e110a886bd445c33e1c084` |
| `organism_v6/reasoning_gym_families.json` | `220071c8783ed4d608b04015c188e8b22fc5745c10f250c7fbd724dd854649ea` |
| `organism_v6/bootstrap_reasoning_gym.txt` | `9b2cf7521bc75fe995ffa05a117f61d12ded24395e8b315e384f58add846e1f1` |

## Scope retained

The unchanged local capacity implementation hashes remain:

- `gpu/orch_r150_matched_native.py`:
  `9e901662f3e76dd282b610b87210e824e2ac99c7b91768823f087d9b4e842b71`.
- `gpu/orch_r151_memory_probe.py`:
  `6c47e9f49b696f036e2ab8d990bcdb5872c9ad3dcdf02c09913aefce0762b619`.

Their earlier bounded R1–R3 disposition is neither expanded nor retested here.
No live initializer/header observation, measured optimizer reserve, optimizer
step, node4 transformation/admission audit, parent-helper approval, or
scientific improvement claim follows. Main retains staging and promotion
decisions under the applicable contract. This report's own whole-file digest
is emitted separately; the original rejection is preserved.

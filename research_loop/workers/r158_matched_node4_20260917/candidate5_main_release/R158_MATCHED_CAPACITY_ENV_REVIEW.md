# R158 matched capacity / TRAIN environment independent bounded review

## Verdict — September 17, 2026, 04:22 UTC

**REJECT the combined reviewed bytes: two concrete TRAIN-adapter blockers below.**
**APPROVE the bounded R1–R3 capacity repairs at the exact hashes below.**
The capacity disposition is not approval of the TRAIN adapter, node4 source
transformation/staging, a launch, actual GPU capacity, or scientific improvement.
Both blockers were reported to Main during the review, before this artifact.

This is a fresh independent source/CPU review, not the repair author's report.
Read `AGENTS.md`, `R151_MEMORY_INDEPENDENT_REVIEW.md`, and
`R158_MATCHED_CAPACITY_REPAIR.md`; no nested AGENTS files were found in the
reviewed gpu/tests/research_loop directories. The only authored repository
file is this report. No source/test/coordination edits, staging, reverts,
remote access, GPU/model runs, package installation, process control, lease
operations, or sealed task/answer inspection occurred. CPU tests and inline
synthetic probes used temporary fixtures, disabled bytecode/pytest caches and
empty CUDA visibility. Concurrent work is preserved. Approval does not transfer
to later or transformed source bytes without a bound recheck.

## Blockers

### E1 — [P1] Production dataset adapter imports a nonexistent class

`gpu/orch_r158_train_gym.py:46` imports `ReasoningGym`, but the repository
module exports `ReasoningGymGym` at
`organism_v6/reasoning_gym_gym.py:76`, with no `ReasoningGym` alias.
Direct CPU invocation of **the actual** `dataset(0)` raises:

```text
ImportError: cannot import name 'ReasoningGym' from 'organism_v6.reasoning_gym_gym'
```

This happens before package-version validation or task generation. `offer`
therefore cannot deliver any task at these bytes. It fails closed, not by
leaking an answer. All integration fixtures in the new test file replace
`channel.dataset` at `tests/test_orch_r158_train_gym.py:53`, hiding the error.

**Required repair/recheck:** use the actual class consistently at import,
construction and `inspect.getfile`; add a regression that exercises the real
adapter import rather than replacing `dataset`. With the pinned installed
package, exercise `dataset` itself and a synthetic-journal offer/check path,
without publishing reference answers. A direct package-generator smoke alone
does not test this wrapper.

### E2 — [P2] An unfinished revision can be graded as an older answer

`gpu/orch_r158_train_gym.py:65` selects the last *closed XML answer* before
considering any line-form answer. Unclosed later declarations are ignored.
The line fallback similarly ignores an empty later `Answer:` declaration.
Consequently the parser can submit a superseded answer when a revision was
capped, and can ignore a later complete answer in another supported format.

Independent parser observations (`terminal=false, truncated=true`):

| Actual generated text | Selected answer |
| --- | --- |
| `<answer>4</answer>\n<answer>5` | `4` |
| `<answer>4</answer>\nAnswer: 5` | `4` |
| `Answer: 4\nAnswer:` | `4` |
| `Answer: 4\nAnswer: 5` | `None` |

The last row shows that the intended cap refusal already exists in one
representation, but not consistently across declarations/formats.

This was also reproduced through **real StreamJournal / ContinualStream /
offer / check**, not only the parser: a synthetic child committed
`<answer>4</answer>\n<answer>5`, 128 actual synthetic token IDs,
`terminal=false, truncated=true`. The fixture verifier accepts `4`.
`check` returned `CHECKED`, `accepted=true`, saved `answer=4` with the capped
boundary, and published one accepted-feedback inbox message. No reference
answer was exposed; the defect is which child answer the feedback represents.

**Required repair/recheck:** resolve answer declarations in text order across
the supported forms, and refuse an incomplete newer explicit submission
instead of silently falling back to an older one. Preserve support for a
complete delimited answer followed by unrelated capped prose. Add both parser
and committed-journal negatives for mixed formats, unfinished newer XML,
empty newer line declarations, and complete later revisions. A rejected
incomplete submission must produce no verifier feedback publication.

## R1–R3 disposition

| Item | Independent disposition and limits |
| --- | --- |
| R1: semantic capacity-proof acceptance | **APPROVE repair.** `gpu/orch_r150_matched_native.py:88` now requires exact runtime/prior-proof identity and tolerances, verified restoration without contradictory error fields, literal exact RNG, five finite losses in each paired pass and the maximum pass, finite nonnegative gradient-error evidence, typed integer memory dimensions/counts and plausible peaks/totals, exact bounded/full shapes and headroom, and complete consistent timing. Immutable receipt path/hash and initializer plan/configuration joins remain. Rehashed omission/contradiction/non-finite negatives pass. All three arms, fresh and resume, reject invalid proofs before constructors or arm-root creation. Scalar gradient error is not misrepresented as a substitute for the producer's per-element assertions. |
| R2: deadline acceptance | **APPROVE repair.** `gpu/orch_r151_memory_probe.py:52` starts the clock at callback entry, uses the earlier experiment/300-second deadline, checks after synchronized work and comparison, and checks final restoration/acceptance before PASS. Recorded cleanup allowance is zero extra PASS time. Synthetic preparation/snapshot/comparison/final-forward/synchronization/final-verification lateness and exact 1299/1300/1301 boundary tests pass. This is an acceptance bound, not a kernel-interruption guarantee; terminal receipt disk I/O follows the acceptance timestamp. No nested wall timer is introduced. |
| R3: cleanup failure evidence | **APPROVE repair.** `gpu/orch_r151_memory_probe.py:176` independently contains restoration steps, retains original measurement and cleanup errors, reports FAILED/UNVERIFIED rather than fabricated restoration, attempts terminal FAIL publication, and propagates failure. Injected zero-grad/adapter/optimizer/RNG/cache/base/restoration failures and measurement-plus-cleanup failures pass. Disk publication failure preserves STARTED/COMMIT, leaves RESULT/INITIALIZED absent, and chains the original error. Missing terminal evidence remains unresolved, never automatic retry permission. |

Initializer callback remains after checkpoint save and before loaded-initial
verification/publication; failure blocks INITIALIZED without recreating the
common checkpoint. Four TRAIN anchor families, full input/causal suffix-loss
routing, objective weights, zero optimizer updates/generation, adapter/base
checks, and optimizer/RNG/mode restoration remain in the reviewed paths.
The synthetic harness validates orchestration, not real-tensor numerical
equivalence or measured capacity.

## TRAIN separation, provenance, masking and anti-replay

- **TRAIN-only selection:** independently projected the split ledger's
  family/seed metadata without generating tasks or reading answers. All 24
  fixed IDs are TRAIN-family items inside the explicit TRAIN seed interval.
  The helper admits only indices 0–23 and the three named new matched-life
  roots. `split_of` alone labels non-canary seeds of TRAIN families as TRAIN;
  the stronger interval fact here was checked separately for these fixed IDs.
- **No observed answer-key publication:** source sends only the question and
  format instructions; grading uses the private entry and emits bounded
  score/accepted feedback plus the child's own answer in the receipt. The
  synthetic secret-reference regression passes. No sealed evaluation reader
  is used by this helper. Real-package delivery through the wrapper remains
  unverified because E1 prevents it.
- **Committed child provenance:** actual record reads reject symlinks,
  unstable identities and bad hashes. `verify_triple` joins adjacent
  REQUEST/RESPONSE/COMMITTED records, TRAIN request digest, committed state
  digest, actual response raw text/token IDs, source receipt digest, and the
  own-child row/prefix. A task not present in the request and a tampered
  response are rejected in tests. This is local journal provenance, not an
  independent attestation that a particular model generated the tokens.
- **Masking:** the own-child row requires `prefix_loss=false` and
  `target_loss=true`; environment publications use environment/TRAIN
  attribution. The independent journal probe also consumed feedback in a
  subsequent child turn: feedback appeared only in the prefix, not any child
  target, and both rows retained the mask flags. Expanded history/stream tests
  passed. This does not claim an actual GPU training update was inspected.
- **Per-task/response anti-replay:** exclusive task and attempt directories,
  write-once receipts and publication intents prevent repeat task offers and
  repeat checks for the same `(task_index, response_index)`. Independent
  injected verifier and feedback-publication failures both propagated,
  published zero new feedback messages, and blocked a second check with
  `FileExistsError`. Publication failure retained its RESULT as unresolved
  delivery evidence. No retries or overwrites were performed on live data.
- **C1 — bounded attribution limitation, not an additional blocker for an
  explicitly operator-selected check:** `verify_triple` only requires the
  task text somewhere in the request, and attempt uniqueness is per task.
  Offering synthetic tasks 0 and 1 before one child response allowed that
  same response to receive two CHECKED results, one per task. Historical
  presence does not establish which task the child intended to answer.
  Do not describe this as global response deduplication or proof of distinct
  task attempts. Any unattended multi-task dispatcher needs an explicit task
  selection/attribution rule and a cross-task regression; none was certified
  here. Existing same-task retry blocking is not disproved by this finding.

## CPU evidence and Main's supplemental evidence

Independent focused run: **505 passed in 10.71s**, no skips:

```bash
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/r136-pytest-support:$PWD python3 -B -m pytest -q -rs -p no:cacheprovider tests/test_orch_r151_memory_probe.py tests/test_orch_r150_matched_native.py tests/test_orch_r158_train_gym.py
```

Independent expanded run: **718 passed, 1 skipped, 137 subtests passed in
24.27s**; includes focused tests, so counts are not additive:

```bash
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/r136-pytest-support:$PWD python3 -B -m pytest -q -rs -p no:cacheprovider tests/test_orch_r151_memory_probe.py tests/test_orch_r150_matched_native.py tests/test_orch_r158_train_gym.py tests/test_orch_r150_matched_stream.py tests/test_orch_r150_matched_journal.py tests/test_orch_r125_continual_stream.py tests/test_orch_r124_train_history.py tests/test_orch_r125_stream_console.py tests/test_orch_r127_pilot_console.py tests/test_orch_r145_suffix_boundary.py tests/test_orch_r145_suffix_loss.py tests/test_orch_r145_suffix_loss_qwen_cpu.py
```

Explicit skip: `tests/test_orch_r145_suffix_loss_qwen_cpu.py:13`, installed
Qwen2/PEFT CPU runtime unavailable. `reasoning-gym` is also not installed in
this review interpreter; nothing was installed to bypass that limitation.
E1 was nevertheless independently reproduced before that dependency check.
Inline boundary/failure probes are additional synthetic observations, not
extra pytest passes. An initial probe's broad JSON glob hit journal metadata;
it was corrected to the journal's 20-digit record filenames before the
reported successful reproductions.

Main supplied `research_loop/workers/r158_train_gym_20260917/CPU_EVIDENCE.json`.
Its bytes independently match the supplied SHA-256
`749fab55b6902a4b4ff60895c85e9ee5901307993d7cc9599dd7b4c1ad8ea4b1`.
The referenced log and package-smoke hashes also match:

- `CPU_TESTS_20260917T0419Z.log`:
  `f9f57f42a577160291382edbe7e279614e67b34abc7e7afee09c61c07ac9aa61`;
  reports **164 passed, 34 subtests passed in 12.04s**.
- `INSTALLED_PACKAGE_SMOKE_20260917T0421Z.json`:
  `d3f64e2e8fbc6b46d5f41709452b16bd36cdcc688207094d59c9f705f9dc18aa`;
  reports package **0.1.25**, all 24 reference/invalid checks passing,
  no GPU, no child evaluation and no answers published. Package-source digest
  is `1b6a5bd08de098b215d66c06210d2c8b8733555cabb65a076ae236e62e23b861`.

These are accepted as **Main-provided CPU/package evidence with verified
receipt hashes**, not independently rerun installed-package evidence. The
aggregate explicitly says `child_task_delivery=false`. Neither receipt
establishes successful invocation of the broken repository `dataset` wrapper
or disposes the capped-revision reproduction. The receipt's helper/test hashes
match the rejected bytes, so this is not merely a stale-source mismatch.

## Reserve and operational exclusions

Main's clarification is retained: the prior derivation of **20,185,088 FP32
adapter elements** gives **154 MiB for two AdamW moment arrays**, not a complete
allocator/optimizer-step bound. No **1,894 MiB residual** is claimed measured.
The existing 2 GiB threshold is a total pre-step reserve, not an asserted
post-moment floor. Main's requested safe header/empty-optimizer confirmation
after initialization, without a step, remains Main-owned evidence, not
independently observed here. No new optimizer step or changed capacity floor
is required by this review. The absence of that live observation is not
recast as an R1–R3 repair failure.

Node4 admission/source transformation, leases, live initialization/header
inspection, actual 16k GPU capacity, readout cleanup, parent exposure,
equal realized task/token exposure, and downstream learning are outside this
verdict. No scientific improvement or GPU readiness claim is permitted by
these CPU results. Main retains coordination and staging ownership.

## Exact reviewed bytes — SHA-256

The six primary files were hash-checked before tests and again after the
independent tests and receipt inspection, without changes between those reads.

| Primary source/test | SHA-256 |
| --- | --- |
| `gpu/orch_r150_matched_native.py` | `9e901662f3e76dd282b610b87210e824e2ac99c7b91768823f087d9b4e842b71` |
| `gpu/orch_r151_memory_probe.py` | `6c47e9f49b696f036e2ab8d990bcdb5872c9ad3dcdf02c09913aefce0762b619` |
| `gpu/orch_r158_train_gym.py` | `6905ade5bcfa019c1278b4590058a670875175c01ccab362d344ec89d9158a97` |
| `tests/test_orch_r150_matched_native.py` | `ae43b9a2ed9ff5c1cb9b6640dbc80bf1a4d7bad80fc7b881b935899caab10a38` |
| `tests/test_orch_r151_memory_probe.py` | `68a15210f8d0bfeacf2af0202603d46b61637acf238a98e6170d4713dc2bf734` |
| `tests/test_orch_r158_train_gym.py` | `58eee3853663cefa921e92061760d63e35bccd32a767aa50484d5d77b803f946` |

| Supporting local input/dependency | SHA-256 |
| --- | --- |
| `AGENTS.md` | `7c9ee4b3050b72c31e933421e06a06a9fe167270dd804de97995d41bcf0a71f9` |
| `research_loop/workers/R151_MEMORY_INDEPENDENT_REVIEW.md` | `4858a389abb0709acef4880b87ffd054110572af9628d5196dcd593980f336f8` |
| `research_loop/workers/R158_MATCHED_CAPACITY_REPAIR.md` | `724f63bcc63106820e347476c4b99038a2be0d37d492feb4ff8c739b71ca2de2` |
| `organism_v6/reasoning_gym_gym.py` | `da9879537d33923c9702b1a5b3d63d6a2fcb396a64e110a886bd445c33e1c084` |
| `organism_v6/reasoning_gym_families.json` | `220071c8783ed4d608b04015c188e8b22fc5745c10f250c7fbd724dd854649ea` |
| `research_notes/R158_MATCHED_TRAIN_PARENTING_2026-09-17.md` | `0f4f05de1ae93833c549f10f4a002e6cf0c1139c026d4c923497a691eb954a4f` |
| `gpu/orch_r125_continual_native.py` | `cdb54252763472fd21ea12fd7694b208d968422c375dbf0647088cde736e6d48` |
| `gpu/orch_r125_stream_journal.py` | `3925a6dff44c71994d446445833207ba3b4a9c8a983b56a8f3e3de84239eb0ca` |
| `gpu/orch_r125_stream_console.py` | `35697239e89a6b9dd49505b3556eb2c149b214fdb5ad3116677712d9b4231b75` |
| `gpu/orch_r127_pilot_console.py` | `be7cfab563dcfe31590329e930b73238e26d39c7b03eb16c1859cc3e91f0b683` |
| `organism_v6/orch_r125_continual_stream.py` | `617e3ecd0bb45b35f0193ecd391bee21d0d86b2b32024ac5fe178fee13884c09` |
| `organism_v6/orch_r124_train_history.py` | `0c336e3c9d3f5fbcfa3446287b24f554052cd57ec5330fb1d4a84f5e0894dd91` |
| `organism_v6/orch_r125_plain_context.py` | `dcfd1f7f5584867e39356f336f53bb7222aeb535da87d5ecb8f1f0bb59f72feb` |
| `gpu/orch_r145_node3_capacity_recovery.py` | `3fce935672ffd4d19119fde7e503f5956262caa584c860fe45afe14efea0daf3` |
| `gpu/orch_r145_suffix_boundary.py` | `632c519fd4c5a840d13b1e9503e61f512340ee9361ef95dcd43cbaf704ee0ce5` |

Supporting hashes identify the local context, not a whole-dependency audit or
remote frozen-source attestation. The approved capacity producer/consumer pin
runtime receipt `c66a91b631937236d614095c07785f90242e4d476c45b7fa8fe5d65a8f277d2d`
and prior GPU proof `3d4e5ed2e7acf7501ab21a1361c511f5db9fe4ad25f96dd1e691fbc47277b281`;
those identities are not new GPU evidence from this reviewer. This report's
own whole-file hash is emitted separately to avoid a self-referential digest.

# SEQ246 matched-reader replay: independent terminal output audit

September 14, 2026. Source `5312cefb18ebbcf37bade654f553d4fcf39a0710`.

## Result and scope

**PASS: the 28 native classifier outputs, exact cross-arm prompts, captured
replay, strict scores, source admission and recorded identity/integrity
bindings agree. No native failure is present in the terminal receipts or
call captures.** This is an evidence-audit result, not a broad scientific
readiness or launch gate.

| Count | Original AUDIT_SFT | Original AUDIT_LOSS_OFF |
| --- | ---: | ---: |
| Fault invocations correct | **8/8** | **2/8** |
| True invocations correct | **4/6** | **4/6** |
| All invocations correct | **12/14** | **6/14** |
| Distinct fault prompts correct | **4/4** | **1/4** |
| Distinct true prompts correct | **3/4** | **3/4** |
| All distinct prompts correct | **7/8** | **4/8** |
| Addresses with both true and fault responses correct | **3/4** | **0/4** |

Distinct-prompt counts are computed from exact captured model-message hashes,
not inferred by dividing invocation counts. All repeats within each arm have
identical raw outputs and correctness. There are four source addresses,
eight distinct prompts, and fourteen invocations per arm—not fourteen
independent examples. Native strict denominators remain unchanged.

The SFT advantage is entirely on faulty replies: six invocation gains,
corresponding to three distinct prompts. Neither arm improves on the other
on accurate replies. Both falsely flag the same correct source-1 entry
twice. No arm-specific prompt difference explains the comparison.

## Terminal timing and preservation

| Arm | Native start UTC | Native finish UTC | Status | Calls | Fits |
| --- | --- | --- | --- | ---: | ---: |
| AUDIT_SFT | 13:58:33.306720 | 13:59:33.703745 | COMPLETE | 14 | 0 |
| AUDIT_LOSS_OFF | 13:58:33.342305 | 13:59:31.505032 | COMPLETE | 14 | 0 |

Both launch directories contain completion timestamps, and both native
CPU preparations report `PREPARED_NO_MODEL`. Neither arm has a `FAILED.json`
or launch abort marker. All 28 native calls have no error, terminal output,
no truncation, and recorded token counts within the 2048-input/160-output
bounds. Each arm contains exactly `CALL_000.json` through `CALL_013.json`.
These are observations of captured evidence; this sidecar runs no native
model, tokenizer, GPU operation, fit, job, or kill command.

Main's local capsule is the reduction authority:
`gpu_artifacts_local/astra_reader_audit_matched_replay_terminal_20260914_attempt1/extracted/`.
Main reports the complete archive SHA-256 as
`e613a66b1623212fa7d8ed9f68098a2984e69b9dc38fb2e48efcd619925ae708`.
That full archive hash is not independently recomputed here; the bounded
files actually used are independently checked.

Owned evidence directory:
`gpu_artifacts_local/astra_matched_reader_audit_independent_20260914T140118Z/`.
A single read-only terminal check was followed by a bounded capture through
`bash gpu/ovx_ssh.sh`, completed at **14:01:19.007676 UTC**. This preceded
Main's local-capsule message. All later work uses local files; there is no
further remote copy or polling.

| Preserved payload | Files | Exact bytes |
| --- | ---: | ---: |
| AUDIT_SFT complete structured run outputs | 20 | 390855 |
| AUDIT_LOSS_OFF complete structured run outputs | 20 | 369915 |
| Both native CPU preparations | 8 | 524892 |
| Launch source/PID/start/completion text receipts | 8 | 180 |
| Scoped deployed runner/helper/test/import source | 27 | 526020 |
| **Total payload** | **83** | **1811862** |

The initial remote snapshot has 71 files / 1,517,660 bytes. Twelve additional
import-dependency files / 294,202 bytes are copied only from Main's local
source capsule. All 83 copies match the corresponding local capsule bytes;
all 27 selected source files also match the declared Git commit. The
initial remote reads check size/mtime/ctime stability around each read and
provide complete per-file SHA-256 hashes for that bounded snapshot.

The two stdout logs and two resource-scanner reports are intentionally
outside this bounded sidecar capture; Main's full capsule preserves them.
No model or adapter weight file is copied. This is not an expanded custody
audit of the ancestor campaign or a duplicate training-schedule reduction.

## Exact prompt and replay checks

`replay_independent.py` uses the captured source helper with model/framework
imports blocked and bytecode writes disabled. It rebuilds each complete A3
case bundle from its captured collection and routes, then calls the pure
`collect_audit` with the recorded native responses as the callback. All four
resulting audit documents equal their corresponding captured documents in
full. A separate literal raw-output scorer also agrees on every response.

The script verifies:

- Each arm's runtime `CASES.json` equals its prepared case document, and the
  complete case documents equal one another across arms.
- Every native CALL's global index, packet-local index, packet name,
  message list, response, and prompt hash match the corresponding case and
  nested audit capture. There are no omitted or extra calls.
- All fourteen ordered model-visible message lists match cross-arm. The
  first eight come from A3 BEFORE, the last six from SELECTED AFTER.
- The fixed packets equal the original local A3 `ACTUAL_CASES.json` files.
  All **33 distinct A3 source-file bindings** listed in each arm's receipt
  match that original capsule; this is the same file set checked per arm,
  not 66 distinct observations.
- Both evaluator receipts carry `on_policy=false`, `parent_present=false`,
  `training_allowed=false`, and `fits=0`; case files are evaluator-only.

Pure replay retains the BEFORE reads from the two invalid-route episodes.
It does not invent missing transition outcomes, substitute reader replies,
or turn routing failures into successes. Source producer lineage still
includes the attempt1 collection reused in A3 attempt2.

Exact shared bindings:

- Ordered fourteen-prompt-hash list:
  `e1cf5d477a0194b09e11d521afe30e590de5d6b16f1bb72495cf4129237ca265`.
- Combined two-case-bundle dataset:
  `4e431d97af200558bffc1eb33097080a04f86406c653d2aef5f629aa4e779184`.

The first local replay attempt stopped at an omitted import dependency,
before any evidence replay or native action. The exact missing dependency
set was then copied from Main's capsule and verified against the declared
source commit; the complete replay passed. This local packaging failure is
preserved in `replay_attempt1_failure.json`, separately from the **absence
of native failures**. No captured scientific evidence was edited.

## All distinct prompts and their raw outputs

Within each row, the listed raw output is the same on every corresponding
invocation. `\n` below denotes a literal terminal LF; it is not added during
scoring. Source indexes and packet positions are zero-based.

| Source / EVENT | Stratum | Packet-local positions | Expected | SFT raw | OFF raw |
| --- | --- | --- | --- | --- | --- |
| 0 / `E_OBOXFV6WG4` | fault, BEFORE | 1, 3 | `E_OBOXFV6WG4` | `E_OBOXFV6WG4` | `E_id` |
| 1 / `E_BF3K34VYXU` | fault, BEFORE | 0, 2 | `E_BF3K34VYXU` | `E_BF3K34VYXU\n` | `E_BF3K34VYXU` |
| 2 / `E_PRS7JYHK37` | fault, BEFORE | 5, 7 | `E_PRS7JYHK37` | `E_PRS7JYHK37\n` | `E_id` |
| 3 / `E_LT27MCC2IZ` | fault, BEFORE | 4, 6 | `E_LT27MCC2IZ` | `E_LT27MCC2IZ` | `E_id` |
| 0 / `E_OBOXFV6WG4` | true, AFTER | 1 | `NONE` | `NONE` | `NONE` |
| 1 / `E_BF3K34VYXU` | true, AFTER | 0, 2 | `NONE` | `E_BF3K34VYXU\n` | `E_BF3K34VYXU` |
| 2 / `E_PRS7JYHK37` | true, AFTER | 4 | `NONE` | `NONE` | `NONE` |
| 3 / `E_LT27MCC2IZ` | true, AFTER | 3, 5 | `NONE` | `NONE` | `NONE` |

BEFORE faults preserve EVENT identity but alter all four node/port/outcome/
receipt fields; AFTER replies match the source tuple fully. These are real
captured reader replies, not synthetic faults authored for this audit.

**OFF's six missed fault calls are invalid `E_id` placeholders**, not valid
wrong addresses and not `NONE` abstentions. They supply no usable source
pointer. Do not infer their intended address or credit an unexpressed
semantic decision. SFT supplies the correct executable addresses on those
same six calls.

**Both arms' two true-case errors are valid-address false positives** on
`E_BF3K34VYXU`. They are source-admitted despite being wrong classifications.
The optional LF difference between arms changes neither score nor admission.
Thus the taught checkpoint is not a perfect true/fault checker here, and
the observed gain cannot be summarized as a reduction in false positives.

Paired distinct-prompt outcomes are three SFT-only successes, zero OFF-only
successes, and five ties. The stronger per-address requirement—correct on
both that address's accurate and faulty reply—holds for sources 0/2/3 in
SFT and no source in OFF. This is a descriptive four-address diagnostic,
not an independent statistical test or revised primary score.

## Source admission is separate from correctness

The native scorer accepts only the exact expected output or that output
plus one LF for correctness. Independently, a bare original source address,
optionally one LF, is admitted even if it is the wrong classification.
Neither generic placeholders nor embedded/substituted addresses are rescued.

| Packet | SFT native source-index sequence | OFF native source-index sequence |
| --- | --- | --- |
| BEFORE | `[1,0,1,0,3,2,3,2]` | `[1,null,1,null,null,null,null,null]` |
| SELECTED AFTER | `[1,null,1,null,null,null]` | `[1,null,1,null,null,null]` |

Filtering only nulls for a separate material roster gives BEFORE SFT
`[1,0,1,0,3,2,3,2]` and OFF **`[1,1]`**. Duplicates are retained. The two
AFTER source-1 admissions per arm are false positives, not evidence of a
needed repair. No material fit occurs in this matched replay.

## Evaluator identity versus stimulus producer

The independently checked original train receipts are preserved under
`gpu_artifacts_local/astra_reader_audit_lesson_independent_20260914/terminal_saved_adapters_20260914/files/{ARM}/train/`.
The native evaluator adapter paths remain:

- `/tmp/astra_reader_audit_lesson_20260914_attempt1/AUDIT_SFT/train/adapter`
- `/tmp/astra_reader_audit_lesson_20260914_attempt1/AUDIT_LOSS_OFF/train/adapter`

Both are original **200-update SEQ239** train receipts, with the corresponding
original lesson/source joins. Neither is a SEQ241 descendant that received
the later common 62 audit lessons. The SFT original-train hash is also the
one named in the A3 source ancestry join.

| Evaluator | Native before = after tensor-state SHA-256 | Original = native after weight-file SHA-256 |
| --- | --- | --- |
| AUDIT_SFT | `db3f213b0040ac92dbc45ab8373bf4a0c55185d4eb23a3fca781f0bf89b431c5` | `5b7c422dc3b61cbfc4b51363f2aef2ab3b4edb6b6bee680d10dda0c172ea5fcb` |
| AUDIT_LOSS_OFF | `42c8a7e212945dd71035d13655bbfc04214a51f17bf8baf969909961b0556684` | `f9275b58be20c3a2900a3d3e61fbbb806498f8b788ada6481b7ec606e76fe43b` |

Both native receipts report adapter-state equality, equality of the full
recorded adapter-file hash mappings, and successful frozen-base verification.
Those values match the original preserved train receipts. The common
expected base-state digest is
`a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`.
This independently checks **receipt consistency**, not a fresh sidecar
tensor measurement; no model/tensor loader or weight rehash runs here.

The A3 stimulus producers are different checkpoints:

- BEFORE/collection:
  `48dc1d6d77852bddba75e04ee7442f4ef2a8e72bce5719d39ade4ed974a2b042`.
- SELECTED AFTER:
  `207ad43ef65f1f6ba7c50d37f5d5dfa8c2253d1cb301e585d7b6b7a78bb93990`.

These packet producer states match original A3 stage receipts and differ
from both evaluated auditors. The result is therefore **new native outputs
from original auditors on identical third-party captured actual-reader
stimuli**, explicitly counterfactual/off-policy. The source table does not
make those A3 experiences the older evaluator's own experiences.

## Interpretation and prospective material-only consequence

The matched inputs remove the different-stimulus confound for this packet.
The original taught checkpoint emits more correct, executable fault
addresses than its original loss-off counterpart, while true-case performance
is equal and imperfect. This supports that narrow observed transfer result.
It does not establish general semantic checking, small-error detection,
on-policy selection utility, clean held-out confirmation, or an H1/H2 result.
The packet is postselected DEV evidence from a taught descendant, contains
only four addresses, and uses explicit receipt-grounded source scaffolding.

For Main's separate
`research_notes/analysis/2026-09-14_reader_audit_transfer_write_design.md`,
the directly supported material difference is the BEFORE executable roster
covering four sources versus OFF's `[1,1]`. The six OFF failures are generic
`E_id` outputs: a downstream disadvantage could arise from operational
pointer formatting/admission, not uniquely inferior internal semantic
judgment. The proposed writer is the same later A3 pre-write child that
experienced the source records; the selectors are earlier checkpoints
judging third-party stimuli. A consequence result would test this separated
selector/material/shared-writer composition, **not authentic parenting of
an entire on-policy life**. Reference reuse still requires Main's declared
roster and data/kernel contract equivalence; this 28-output review verifies
the source-valid rosters, not that successor training contract, and does not
claim its efficacy or request reruns.

## Reproducibility and release

The owned directory contains immutable raw evidence plus:

- `capture_manifest.json` and `local_check.txt`: initial 71-file preservation.
- `dependency_manifest.json`: twelve source dependencies added from Main's
  local capsule, without another remote read.
- `replay_independent.py`: exact pure-helper replay and separate raw scorer.
- `independent_replay.json`: every invocation, prompt, score, admission,
  duplicate mapping, original identity and check outcome.
- `completion_receipt.json`: final input stability and artifact hashes.

Key output/input hashes:

| Artifact | SHA-256 |
| --- | --- |
| SFT native `RESULT.json` | `f83c5d0c3ebe9586cd358fa58241ba46b66498b6147af69177eefe5930701994` |
| OFF native `RESULT.json` | `e89432c1de50e701638f85f6c08e96e0e49b26b6ebc9b964280fab5dcbc00d02` |
| `independent_replay.json` | `7272795ed6fcbd22ae10eb6d1c9b66f70cd180620c9a03df81975b9f97b6f0fb` |
| `replay_independent.py` | `372078d7bf7efc259e7c52759797fe2edfe1986e027f0cd074fd91ffa8017e97` |

Only this new independent memo and its owned audit directory are written.
Main's primary memo/log, prior released files, source code, adapters and
other workers' changes remain untouched. No commits or launch actions occur.
The review does not gate Main's continuing work.

# R179 independent R176 integration review — FIRST FIXED C2 sleep33 pair

**Verdict: REWORK. No GPU GO.**

Scope is exactly the first fixed C2 sleep33 ON/OFF tranche: two independent
fresh-process conditions, three unchanged probes each, six calls total. This is
an independent integration review, not adoption of the earlier R172 transfer
component verdict. It does not cover C5, later checkpoints, new baseline calls,
or R179 living-context implementation. Neither C5 custody nor completion of
R179 is a prerequisite for this tranche.

Public bindings were recorded **September 17, 2026, 17:33:06 UTC / 10:33:06 PDT**.
The actual receiving-byte observation was at **17:27:06 UTC**, and the actual
receiving-validator diagnostic was at **17:29:23 UTC**. Those observations are
point-in-time evidence, not a claim about later edits or current GPU vacancy.

## R179-I1 — blocking production read-budget mismatch

`stage_narrow_runner1.py:149` reserves **24 MiB = 25,165,824 bytes** of metadata
for each condition's preflight and native phase. The exact receiving configs
retain those amounts, and their ten execution-read authorities match the
original local nonrefundable ledger documents and hashes.

However, `r176_runner.py:164` hashes the entire 1,285-file receiving source
closure; `r176_runner.py:167` reads the receiving CPU receipt; and
`r176_runner.py:196` hashes the actual interpreter. These reads are charged by
`r176_runner.py:98` / `r176_runner.py:124` against that same phase allowance.
The following **mandatory lower bound alone** already exceeds the allowance:

| Mandatory read | Exact receiving bytes |
| --- | ---: |
| Source request | 144,574 |
| Source closure, one pass | 17,011,448 |
| Receiving CPU receipt | 137,944 |
| Bound interpreter | 8,025,024 |
| **Minimum total** | **25,318,990** |
| **Available per phase** | **25,165,824** |

This lower bound excludes imports, the runner CPU receipt, release/lease
receipts, runtime source rereads, other custody metadata, and subsequent config
checks. It applies to **both opaque configs**, without disclosing their
condition assignment. Passing only a reduced fixture cannot establish that
these production bindings fit the frozen allowance.

The receiving diagnostic used the **actual frozen `validate` and `Reader`
implementations**, actual config/source/CPU/lease/release files and actual
interpreter size. It refused at the interpreter open with
`ValueError('delegated_read_cap')`: **17,568,725** metadata bytes had been
successfully charged, the next charge was **8,025,024**, and the attempted total
was **25,593,749**, above **25,165,824**. No adapter read was attempted by this
diagnostic. It never reached strict admission, reservation, model loading or
generation. `start` calls this validator at `r176_runner.py:238`; the native
process calls it again at `r176_runner.py:269`.

For safety, this diagnostic substituted only in-memory GO/review fixtures and
in-memory ledger writes. Authorization fixtures satisfied the existing
validator's prerequisite checks; **they were never written, issued as real
approvals, or used to launch anything**. The actual caps and validation logic
were not increased, disabled or replaced with success. A separate audit guard
forbade receiving writes, process creation, network connections and signals;
model-library imports were also prohibited. This is a reproduced pre-admission
refusal, not a production authorization or successful native-run proof.

**Engineering disposition:** make the complete production validation/runtime
read plan fit explicitly bound finite authorities within the already-approved
R176 envelope. Account for the real source/interpreter/receipt footprint and
all repeated reads; preserve complete provenance and the unchanged loading
path. Do not disable charging, borrow R172 allowances, refund/reset consumed
preparation passes, or overwrite these configs/receipts. Bind any repaired
candidate and its receiving CPU evidence append-only and exercise its actual
phase-accounting integration before requesting the existing bound review/GO.
This is repair of an existing fixed-scope budget/provenance requirement, not a
new scientific gate. Do not test the broken candidate by invoking `start`:
`r176_runner.py:225` creates the once-only attempt before validation, so this
predictable refusal would consume its attempt directory unnecessarily.

## Other integration findings within the bound review

- **Transport/custody:** the wrapper-only observation independently hashed all
  1,285 receiving source files and every member of the captured payload,
  including **80,798,775 adapter bytes**. All matched their bound inventories.
  Source completion, receiving completion, original COMMIT, captured original
  BIRTH and source evidence join without checkpoint substitution. The two
  configs bind the same capture and source. Private contents were reduced to
  equality/permission checks; none are reproduced here.
- **Important transfer version distinction:** the receiving source contains
  `r176_transfer.py` SHA256
  `3be8a68e3bf79743a8eeda7af94140dc304080f4005b689b565d6d4a1cbbc6f7`.
  Current local `r176_transfer.py` is
  `9cd66a30f1199095188ffdaf619fc7cf5c05ae9be7e601f375da7a04e6d50273`.
  The preserved author copy shows the sole difference is the export receipt
  filename repair. The already-successful receiving copy was observed, not
  replayed. The earlier export receipt collision remains preserved; this
  review does not silently substitute the newer transport source into the
  historical receiving proof or require a redundant transfer.
- **Instrument/loading/privacy:** the generator and receiving source pins are
  unchanged; the runner calls the existing three-prompt generator with the
  original system/BIRTH-only context, not living history or a retelling
  invitation. The frozen loading path uses the expected base, read-only
  adapters, per-condition process isolation, unchanged decoding and 512-token
  caps. The generator retains before/after identity and read-only checks. The
  captured witness and pre-output rubric remain privately bound. This is
  code/custody assessment, not a claim that model loading or inference ran.
- **Calls/wall/missingness:** fixed-key and same-capture/source checks, once-only
  three-call charging, separate R176 ledger, 72-call/24-process outer envelope,
  non-sliding 90-minute wall, 900-second jobs, 19:30 UTC absolute end and existing
  lease margin remain present. The narrower runner cannot replace sleep33,
  insert an initial baseline or add C5. Missing/failed fixed cells are not
  negative scientific results or authority for replacement/retry. Tests cover
  fixed-slot independence, paired charges and wall refusal. No execution
  attempts or reservations existed at the receiving observation.
- **Adapter read accounting:** the explicit per-phase verification allowances
  and separate model-load reservation remain present. The load accountant
  precharges declared files and charges repeated observed Python-level opens.
  Its tests do not prove every native-library/mmap transfer is observed; this
  review neither changes that boundary nor waives the frozen read caps.
- **Admission:** the source-bound physical-slot lock, privileged scanner,
  exact host/UUID/interpreter/service/lease checks and refusal of a nonclear
  report remain in the execution path. The old-release receipt and current
  interpreter/service hashes matched. The scanner's source closure includes
  strict memory/utilization/process-visibility checks. **No scanner was
  invoked and no GPU was declared clear.** Existing fresh admission and Main's
  separate exact no-reset GO remain execution responsibilities, not extra
  reviewer-imposed conditions.

These observations do not dispose R179-I1 or certify unexecuted downstream
native/admission behavior. The integrated first-tranche verdict remains REWORK
because both exact candidates cannot pass their mandatory metadata gate.

## Exact public byte bindings

`REVIEW_R179_PUBLIC_BINDINGS.json` is the complete public path/hash binding for
the reviewed local code, preserved receiving-source copy, test evidence and
receiving references. SHA256:
`ee2c32d604350c98a71e8d89425b35c71132c01b6e9421027932022dda170ded`.
Its reconstructed local receiving request hashes to the actual receiving
request, binding the full local source-freeze inventory rather than trusting
only a remote self-reported pin set.

| Object | SHA256 |
| --- | --- |
| Local, preserved-author and actual receiving runner | `4ff1c97b374930b2b6e4c96d2f8d24fbedcdccfaae8c07471edd52720d7a6952` |
| Shared R176 preparation helper | `1fcb8f90a1f98ad38389af87b1527c11c018da65369588ec720005fa24229681` |
| Local/receiving narrow request | `09288bd9241d2278f965310811cb821c38566a1e137478b19f7ef757222be81e` |
| Local/receiving safe narrow receipt | `3fdd2c829925a9f49c113cafaa0f1d04c38b15863f66d52a974945f511eece8c` |
| Receiving source request | `b34fd19b891f5639456abaa0ad112727b643869350b5e5aafd10c3dd0203ed9d` |
| Receiving CPU gate, 39 tests | `9bc9428347d3743fb92b975fc8e88e022c7a1bf55697f2fb0a22d91f0e5cee39` |
| Narrow receiving CPU gate, 7 tests | `7b54d713a661d282029bd104fb7401ad4b635a72ebc4b128dd527b8a9f919a54` |
| Source completion copied to receiver | `c7ec6afb15ebf082f78867fd2f459441b2a22a300b2e9c982ef455e26d2896de` |
| Fixed C2 sleep33 COMMIT | `38067e8619851f556e49b3e3c26f307fd1b4abfd700fcb64d4cdde18a91dc70f` |
| Unchanged generator | `383415b6b37f8ff237c95b053439f6919f7ee47c452b3ffd015e606ff1962011` |
| Opaque execution config pin, no condition assignment disclosed | `5bb854538959cbab8e2453f55bd0c70f5f5355fdb9936c2738c87e737eabce63` |
| Opaque execution config pin, no condition assignment disclosed | `835b9b66d0f56c8419c958d96f32e828c45c2139aa4ce15611351561fa87c4f1` |

The original scope/proposal/twelve-slot pins and exact opaque paths are in the
binding file. The receiving root is
`/localhome/local-rohing/orch_r176_retelling_retention_20260917_generation1`.
No semantic condition map accompanies these public pins.

## Evidence and verification

- `REVIEW_R179_RECEIVING_READONLY_20260917T1730Z.json`: actual hash/custody/config
  observation. The JSON's `observed_utc`, not the filename suffix, is the
  observation time. It records **108,021,531 bytes across 1,318 file reads**,
  bounded by the review script's 192 MiB safety limit. These were reviewer
  observation reads; no operational allowance was altered or refunded.
- `REVIEW_R179_VALIDATE_READONLY_20260917T1732Z.json`: actual validator refusal
  with unmodified phase caps and no receiving-state writes. Its internal
  `observed_utc` is likewise authoritative.
- `review_r179_receiving_readonly.py` and
  `review_r179_validate_readonly.py`: complete reproducible wrapper-fed
  observation/diagnostic source. They were fed over `gpu/ovx_ssh.sh`; neither
  was installed on the receiver. No source-node command was needed.
- `test_review_integration_r179.py`: five new independent CPU regressions for
  actual public/local/receiving equality, the mandatory read lower bound and
  real cap refusal, the receiving diagnostic, original authority-ledger joins,
  and exact no-reset execution/review binding refusals.
- `REVIEW_R179_CPU_03_20260917.txt`: **41 tests passed**: all 36 author tests plus
  the five independent regressions. SHA256
  `c8394b1835daba22830617ecec5b206ac393612de63e00b0c45da2a2172129d6`.
  These passing regressions establish the budget defect; they do not turn the
  integration verdict into PASS. Earlier reviewer logs remain preserved,
  including an initial reviewer-only module-path error corrected before the
  final suite; no author/runtime file was repaired by this reviewer.

Only reviewer-owned files and temporary synthetic local fixtures were written.
No actual learner/evaluator state was written; no model/GPU/provider calls,
signals, privileged scans, live R179 context reads or execution GO occurred.
No responses, labels, scores, witness/rubric contents, condition assignments or
qualitative retention results are disclosed. No new gate beyond fixed R176
scope is introduced.

# Event-v2 acquisition archive: independent bounded verification

**EDITSTOP — review complete; no execution or claim promotion.**

Reviewed September 13, 2026; final audit executions at 19:35 UTC. Scope is the
already-captured VM archive, not Main's running follow-up sequences. Only this
new note and the companion new audit script were written. No experiment code
changed; no commits, remote commands, GPU operations, launches, native reducer
execution, archive extraction, or further delegation occurred.

## Verdict

**PASS for the available acquisition bytes and joins; incomplete provenance
closure, not native attestation.** All nine collection/stage joins and all 96
raw readout calls reproduce the expected result against literal material
targets, including the final LF, with `finish_reason == "stop"` and no
truncation. No acquisition hash/size/member-set mismatch remains in the final
audit. Missing referenced files and the original failed formation are explicit
limits, not silently passing checks.

For **each** optimizer seed 0, 1, 2, separately in **both W0 and W8**:

| Optimizer seed | C0 A | C0 B | A200 A | A200 B |
|---|---:|---:|---:|---:|
| 0 | 0/4 | 0/4 | 4/4 | 0/4 |
| 1 | 0/4 | 0/4 | 4/4 | 0/4 |
| 2 | 0/4 | 0/4 | 4/4 | 0/4 |

This confirms the bounded acquisition pattern only. Three optimizer seeds
share **one** eight-EVENT bank; they are not independent source-bank replications.
W8 is exposed DEV, not confirmation. Nothing here establishes retention,
follow-up success, autonomous discovery, parenting, H1/H2, G3, C11, generalization,
mechanism, significance, full-assay completion, or permission to promote a claim.

## Input identity and method

Archive: `gpu_artifacts_local/pcfl_v2_acquisition_20260913_attempt1/evidence.tar`.
Size: **539432960 bytes**. SHA256:

```text
fdc22c730206c5c9e6486099fc908b5daaaad78916c106eeb4f738fa86446879
```

The VM transfer directory's `attempt1` contains the native acquisition campaign
`pcfl_sequence_v2_acquisition_20260913_attempt5`; these are different naming
layers, not evidence of an extra seed. The campaign's archived start is
2026-09-13T18:59:24.279819+00:00 and finish is
2026-09-13T19:15:20.576734+00:00. The captured campaign status remains
`ACQUISITION_CAPTURED_NOT_QUALIFIED`.

Audit implementation:
`research_notes/astra_memos/receipts_20260912/event_v2_archive_independent_audit_20260913_bounded.py`.
It uses only the Python standard library, `tarfile` read-only regular-member
maps, and in-memory nested archives. It rejects duplicate member names,
absolute/traversal member paths, symlinks and other non-file/non-directory
types. It does not import or execute repository/archived experiment modules.
No extracted pathname is followed. The archived reducer is hashed, never run.

Independent scoring is UTF-8 byte equality of `raw.text` and the material
record's `target`, **without strip, normalization, parsing repair, or semantic
credit**, conjoined with stop termination and `truncated is False`. Receipt
scores are compared only after these independent results are calculated.

## Counts, joins and denominators

- Nine unique campaign results biject to nine collections: three A200 fits,
  three C0 readouts and three A200 readouts. All nine report zero exit status,
  no collection errors, and released workers; all completion snapshot bytes
  match their underlying stage completion file.
- All nine bind the proper input copies, learner seed, material file, spec,
  import, source declarations, invocation arguments and worker identities.
  Three A200 readouts bind the **same-seed** fit receipt and checkpoint. Their
  three mounted adapter files each match checkpoint bytes and the route digest.
  C0 routes have no fit receipt, no LoRA request and no adapter digest.
- Manifest learner labels are exactly `[0,1,2]`. Training config and train-meta
  seeds are respectively 0, 1, 2; all three adapter-model hashes differ. Nine
  `(boot_id,pid,start_ticks)` worker identities differ. The 96
  `(learner_seed,state,roster_id)` tuples and 96 raw-file hashes are distinct.
  Roster IDs intentionally repeat across states/learners; reader sampling
  `seed=0` is fixed in all three rosters and is **not** the optimizer seed.
- Exactly 16 raw calls per readout, indices 0000–0015, cover the ordered W0 A4/B4
  then W8 A4/B4 grid. For every call, request/row/ID, exact public messages,
  answer-free rendered prompt, unconstrained sampling, raw/response byte copies,
  raw hex, text hash, route, token counts, termination and captured cold-load
  chronology join. Every scored row is retained in the denominator.
- **96 stop, 0 length, 0 truncated, 0 missing expected raw calls.** Maximum
  observed output length is 70 tokens, below the 2048 cap. Independent totals:
  **9036 prompt tokens, 2642 output tokens**. Raw outcomes: **48 `MISS`** C0
  failures, **24 exact-target** A200-A passes, **24 wrong `EVENT`** A200-B
  failures. In particular, a syntactically EVENT-like B answer gets no credit.
- Exactly **three archived native fits, 600 updates, 2400 presentations**.
  Each A200 corpus is byte-content-equivalent to the ordered material item list:
  800 items, 200 four-item batches, chronological A records 0–3 only, cycling
  W0–W7; each `(A record, view)` occurs 25 times. All 2400 supervised target spans
  match the source EVENT target exactly; no B target is fitted. Training
  manifests report 800 encoded items, 200 steps, zero skipped targets and zero
  truncated items/target-token drops per fit. This verifies archived accounting,
  not fresh tokenization or execution.
- Rank 8, alpha 16, dropout .05, LR 3e-5, batch 4, AdamW, 200 maximum steps and
  fresh C0 initialization join through config/manifests. No predecessor,
  warm-start or parent-phase checkpoint is declared. Base identity declarations
  agree on Qwen2.5-7B-Instruct revision
  `a09a35458c702b33eeacc393d103063234e8bc28` and the archived model-file binding.
- No B200 run member, fit completion or launched fit phase appears in the
  acquisition run tree. B200/other follow-up **definitions** in material/source
  are not executions. There are three fitted adapter artifacts plus three
  byte-identical readout mount copies, not six fits. Absence outside this archive
  cannot be proved; Main's subsequent runs are not inspected here.

Per-readout token accounting:

| Seed | C0 prompt/output | A200 prompt/output | Truncated |
|---|---:|---:|---:|
| 0 | 1506 / 32 | 1506 / 875 | 0 |
| 1 | 1506 / 32 | 1506 / 842 | 0 |
| 2 | 1506 / 32 | 1506 / 829 | 0 |

## Source and inventory coverage

All outer files and files in both embedded source snapshots and the original
evidence archive were hashed. No duplicate/unsafe members were present in these
four inspected maps.

| Map | Total members | Regular files | Directories |
|---|---:|---:|---:|
| Acquisition evidence | 834 | 792 | 42 |
| Acquisition source tar | 484 | 470 | 14 |
| Original evidence tar | 148 | 142 | 6 |
| Original source tar inside original evidence | 440 | 426 | 14 |

All **29 declared inventory sets** match available members exactly: 27 from
nine acquisition stages (outer files, stage inventory, completion inventory),
plus the original formation's outer and stage inventories. All 2039 evaluated
inventory hashes and 1463 sizes match. Repeated checks of the same file through
different receipts are counted separately, not as new files.

Per seed, fit has 11 stage members and 29 outer-inventory members; C0 readout
has 90 and 108; A200 readout has 94 and 112. The outer inventory excludes its
own collection. All 995 resolvable path/hash references match. Sixteen distinct
acquisition source files join to their embedded snapshot, and 13 historical
source files join to the original snapshot (128 historical reference checks).

Eight records join chronologically to original raw EVENT calls
`0001,0003,0005,0007,0009,0011,0013,0015`. For each seed's copy, the generation
capture digest is recomputed over the **capture envelope**, not confused with
the raw-file hash. All six envelope file copies join to original members;
raw text, response text, raw hex, target hash, row bytes and stop termination
agree. The shared canonical record-list SHA256 is:

```text
932edc58c15f330420807c648b07b2adcd53938fd430f6b4907da248502e3678
```

This does not rerun the original world/admission logic, tokenizer verification,
or native importer/reducer. Import/spec seals and their available joins are
verified; arbitrary semantic claims inside a sealed receipt are not elevated
to independent attestation.

### Concrete failures and limits preserved

1. **The historical source formation failed.** Original outer return code is
   1, status `FAILED`; formation status is `FORMATION_FAILED`. Its 20 planned
   slots comprise 16 accepted EXPLORE/EVENT slots, one failed LINK at slot 16,
   and three explicitly `UNCALLED` slots. The failure is
   `child LINK differs from pre-output choice`. All **17 attempted raw calls**
   remain in the original nested archive, all stop-terminated; the failed LINK
   is not a hidden truncated or omitted attempt. The historical outer errors
   also preserve `worker did not exit zero` and missing `stage_completed.json`;
   `stage_completed_file_sha256` is null. The available failed-stage inventory
   itself is complete. Only the eight prior EVENTs supply this acquisition bank.
2. **Four outer path/hash references have no matching archived member**:
   `/tmp/astra_pcfl_v2_campaign_operator_20260913_attempt5.py`,
   `/tmp/astra_pcfl_event_sequence_S_A_inputs_20260913_attempt4.json`,
   `/tmp/astra_pcfl_event_sequence_S_A_allocation_20260913_attempt4.json`, and
   `/localhome/local-rohing/v2/venv/lib/python3.12/site-packages/vllm/v1/engine/core_client.py`.
   The absent operator is the actual launcher named by `launch.json`; hashing
   the included stage modules does **not** close this launch-provenance gap.
   The prior input/allocation templates cannot be byte-checked, although all
   actual per-seed inputs/allocations are present and joined. The shutdown
   library source cannot be rehashed; its declaration/close receipts are not
   independent validation of that implementation. No filesystem fallback or
   external lookup was used to fill these gaps.
3. **Archived reservation visibility is qualified.** All nine pre/post GPU
   snapshots show vacant target devices; queue observations match; CVD checks
   report clear with no unexpected/unresolved owners. However,
   `complete_cvd_visibility=false` and
   `PASS_WITH_EXPLICIT_NON_WORKER_SERVICE_EXCEPTIONS` apply to unreadable
   same-UID service PIDs 36935 and 36938 (systemd / sd-pam), under
   `EXPLICIT_MAIN_APPROVED_NON_WORKER_INIT_PAIR`. I do not turn that archived
   exception into full visibility, fresh approval, or a current machine survey.
4. **Model weights/tokenizer/runtime bytes are not in this evidence bundle.**
   Their recorded inventories agree across base binding, fit and readout
   declarations, but cannot be independently rehashed here. Raw token-ID counts
   and prompt-render joins are checked; actual tokenizer decoding/encoding is
   not recomputed. The model binding explicitly does not certify clean lineage
   or historical execution. Checksums establish internal byte consistency, not
   an external proof that a process executed those bytes.
5. Scope is this immutable acquisition capture, not archive completeness against
   an external authoritative machine inventory. Hidden or omitted executions
   outside the available members cannot be ruled out, nor can running follow-up
   results be inferred. No such evidence was requested or fetched.

## File hashes

All values below are **file SHA256**, not a JSON object's embedded `sha256`
seal, unless explicitly labeled canonical. Full per-member hashes and sizes are
reproducibly emitted by `--detail files`; all 96 per-call raw-file, raw-text and
target hashes are emitted by `--detail calls`.

### Campaign and embedded archives

```text
manifest.json                          4e41adf04873a5f119f2f372dcb6ab27c561134c8ff7f407e72ec6b242d89731
completed.json                         104037f11d0cec21c95863d8bc8acb81117b9b4dc697e252429490b6d20e8929
acquisition source tar                 21936c7acdd2fe846fb4ce78de2b5b2f86f13df8cdbf4c0be3211b887c28fc1b
original evidence tar                  bd6829dfa4e6c0a63f48cf184e28091e12cf9de9a231e0f6cda6672d5133c869
original source tar                    698ad6278f69131fdc7721d173753732631b7485b2d420ac293a2ef0e4e50280
archived reducer script (not executed) ac7d30845e8669f96f6f5cd5d66ed508f6e9df4e03085d21e88d5ee3b68a25ff
```

Campaign paths in this section are relative to
`localhome/local-rohing/astra_diagnostics/pcfl_sequence_v2_acquisition_20260913_attempt5/`.
Source and original-evidence tar filenames are the constants `SOURCE` and
`ORIGINAL` in the audit script; the historical source tar is nested inside
the original evidence.

### Nine collection/completion joins

`F` = `fit_outer` / `fit/completed.json`; `C` = `no_write_outer` /
`readout/completed.json`; `A` = `a200_outer` / `readout/completed.json`.
Each collection is `runs/seedN/<outer>/collection.json`.

```text
0 F collection 9849ce1c050bf64e914e4cfce72206faeef50e080920d8b201383e1206dae2ad
0 F completed  337e503482430f38be681b45a5676eca7ea1287925f911b70679dd923264d5e5
0 C collection b7345cc328007515b74fcbcdb5020f1336f88a03f8770fc2bb15372ddf524dad
0 C completed  162e082e73b42b3a68537c3c4248d2c564ee710a1c79db22550ea8ba6bea5be7
0 A collection 59e7d0d069b240bbd884f8c5388a9f13ea74a2b525f6ed69939a77b518039b22
0 A completed  d342cb7334f9d72099e2d7e37b760772df4320594670f045147639c0c00be525
1 F collection 07c1037ce47aa9da91b457a6c84481e57b07f664454a1a3ce7138d3cd4bea49a
1 F completed  c87a77d07449b244f28d7ae5316130ada58d1aacc7635978106d220106ddf2b9
1 C collection e793813fd97e387f8e05a1de7273c06216a1a6b04891e122251ea719278eef07
1 C completed  2db89f548e6cf895b2d52aeb50444c8bcd37eef2982a67e4ec29dc2d91522a20
1 A collection 07037207a812d17503434fc857b076f4ccfdacdb18cb8ba5bb0a4b1829137d03
1 A completed  fae38dc2a6df13868e90a51dfc8eec71bddd4efc0c37813e0868145b3e4d5c0a
2 F collection a51de48d7456a50ded6faf23b2f616c7a691eb5ba734e87a47e9304721f649af
2 F completed  f5aaf3b55624d1fc5e05f1ab0f65204447916c18872b436805b7c8f747244cd9
2 C collection 13f5c0c188360b2b48ad268f334b2273dd624f049bb37a3bcb960239d639aef1
2 C completed  79641559c1261d7fa6a5e4e867d760f40835cea806f3d24b3c12e6706c7497ca
2 A collection 618abe858ac38833c8b544f9262c885bcf30f055aa6e942f5b197840fc218233
2 A completed  cb452c29506a6a95f3ff04b4359334e56ec50c2b0cb3d89ac3885a7310af119a
```

### Materials, adapters and reduction receipts

```text
seed0 material 39555fece842bd2d3aa3573dcb6805116ad06e3010ca1913b6a0ea0a1f8bdf9f
seed1 material 805df872eb6e728f9b7a64ca3e328963c790fb4e29d97be3c225c4c98afcc705
seed2 material 51e56cc1b2baef481f70cc34b49c4a08859b631a11e2343854967f3d58656ba3
seed0 adapter  ac5405eddb5856f19b1db9025b692e781da7b88dd909938a37fcf784c99156a7
seed1 adapter  c3f9dd87888cbb3822c6b81df00ae9da52dae21386f845c804073e8c198f9ba4
seed2 adapter  01fb42dd9bf712c3cb856ac96f7faaf79a42d25be987a601dfca38d1404b202f
seed0 reduction receipt 045aaf1b99cf714752ccc4ce015f570bb0fc803539a61af7eabc5436ad42c0ea
seed1 reduction receipt 3b0efc7272d83d41e8bc238d35df1f32e151bf90ff055e9f7a84820321ef0cf5
seed2 reduction receipt a2e14c6d68e7e3fe2de8d8e5093aa5dd9d2f7e50263dc35a7c755f8ce03fb6bd
```

Materials are `inputs/seedN/material.json`; adapters are
`runs/seedN/fit_outer/fit/checkpoint/adapter_model.safetensors` and matching
readout copies. Reduction receipts are sibling diagnostic roots
`pcfl_sequence_v2_acquisition_reduction_seedN_20260913_attempt1/receipt.json`.
All three existing reduction receipts' request/input/fit/collection pins and
panels agree with this independent audit; their code was not rerun.

### Literal target-byte hashes

```text
A0 E_BRFFHBSD7R 1ed92f10eae3fb3555f84bb1b8dfb11d19d9546c8bce10f3654f109ea65c4dda
A1 E_QL4Q3BQTIY a6cb4153a1f4c2bfc50db8109d7e912ce55e8ede96d46c9f79ca331be107805a
A2 E_34RZZYUU6E b6587d26895a6987aa1b0ce547d90f8fe3a5538dcb51e28a0d821793f294294f
A3 E_B46SKGEBDB 38dc2344bbb64bf040b7350bfb8c413ebaceeea423d97fbb59f3d760707903fe
B4 E_YDPRENAG33 97d2f80c1d39d6b3f953bfee1f69b1cb6472b4890a4d2873274a31351bef8513
B5 E_J3Y2G224QM ecbf306d25b4172fbd59b8501a5fa52534b4184e290c85fd6cc69765113c4bda
B6 E_JMPFI47OZ5 245e27522dc6378ce5268f079a87287d13cfdab4d546d7c78b543383073445cc
B7 E_NVKV6RDQ27 0c5247fab49de8cd79ccda4ab066c4851c8044d7278d26fac84121edd378d076
```

### Canonical inventory and call-ledger digests

Computed as SHA256 of compact UTF-8 JSON with sorted keys, `ensure_ascii=False`.
Inventories map exact member name to `{sha256,size}`. The call ledger is the
ordered 96-element `calls` list emitted by `--detail calls`.

```text
outer inventory           5491eac851d0cf12624bbea3dd7b4dc071c2ffc7c3e2fa97cdf303270987f461
source inventory          c292260e2943c23d01bda3faee16a0e7a6a0b6a12dd0e86d4805730b251a9d4d
original inventory        5953907cfe7322d452b7e73ca98eed33c974f330e460cae1383a3c466609fc2a
original-source inventory ac29fe654d366b3e43fadf7dfcd7a34e050b957656abaa6af05a996fedfc3448
96-call ledger            53745a11c760d6df4b903c35fc106cb378d0db6175b777d7f956ef06c6819907
```

## Exact outputs and tests

Run from the repository root. No output file is required; all audit modes write
only to stdout. `-B` prevents bytecode writes. `set -o pipefail` retains audit
failures when filtering/hashing output.

```bash
AUDIT=research_notes/astra_memos/receipts_20260912/event_v2_archive_independent_audit_20260913_bounded.py
python3 -B "$AUDIT" --self-test
set -o pipefail
python3 -B "$AUDIT" | jq '{counts,raw_text_classes,checks,failures}'
python3 -B "$AUDIT" | sha256sum
python3 -B "$AUDIT" --detail calls | sha256sum
python3 -B "$AUDIT" --detail files | sha256sum
```

Final self-test output, exit 0:

```text
SELF_TEST PASS: 5 byte/termination cases; 4 duplicate/path/type cases
```

The five score cases cover exact LF-preserving pass, missing LF, length
termination, explicit truncation despite stop, and `MISS`. The four member-map
cases reject duplicate names, traversal, absolute names, and symlinks.

Exact selected final audit output, exit 0:

```json
{
  "counts": {
    "collections": 9,
    "fits": 3,
    "original_raw_calls": 17,
    "original_termination": {
      "stop": 17
    },
    "presentations": 2400,
    "raw_calls": 96,
    "strict_stop_passes": 24,
    "termination": {
      "stop": 96
    },
    "updates": 600
  },
  "raw_text_classes": {
    "MISS": 48,
    "exact_target": 24,
    "wrong_EVENT": 24
  },
  "checks": {
    "assertions": 320,
    "file_pins": 995,
    "historical_source_pins": 128,
    "inventory_hashes": 2039,
    "inventory_presence": 2039,
    "inventory_sets": 29,
    "inventory_sizes": 1463,
    "raw_call_checks": 1344,
    "seals": 34,
    "source_record_joins": 240,
    "training_items": 4800
  },
  "failures": []
}
```

Total: **13431 assertion evaluations**, including repeated cross-receipt joins;
these are not 13431 independent scientific tests. All three complete output
modes exited 0. Their **stdout-byte** SHA256s, including pretty-JSON formatting
and final newline, were:

```text
summary:      368f66571ec49d8c96ea09ecccb069dc65f7f1b8c268e1c9b3266617ad1eab74  -
detail calls: bb3068dfca594533453261d17b14c32937a3ce565560514119e87b9509904df6  -
detail files: 091caf12a317963e72353b99892ed990268d399108812e76e341f4fd070d8e69  -
audit script: 3126d845ee00e28424d8cf9aad6697bbc7d26ccb56972237eef0dfbf3ff8db3e
```

Development transparency: initial exploratory commands encountered missing
`python` (used `python3` thereafter), a nonexistent guessed request member, and
a list treated as a dict; no evidence was changed. Initial audit assumptions
were corrected against archived schemas: fit collections use `phase`, outer
inventories contain hash/size objects, capture hashes address envelopes, item
`order` is within-batch, and W8 uses its own public request template. Those
development failures are not reported as archive corruption. Final results
above are from the corrected script and fixed archive hash.

**EDITSTOP.** No more edits or executions are requested by this review. The
acquisition observation is reproduced, the original failure and provenance
limits remain explicit, and claim boundaries are unchanged.

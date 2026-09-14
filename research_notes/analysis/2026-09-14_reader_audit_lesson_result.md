# Independent reader audit — lesson collection and paired follow-up

**Updated interpretation: formal held-classifier gate PASS, but recent selected
record fidelity regresses in specific fields. Loss-off's selected-record
failures are receipt-only; SFT's selected record 2 fails only its node field.
This is not full factual erasure and not broad substrate readiness.**

## Scope and snapshot timing

Independent bounded reader, 2026-09-14. Owned writes are this new memo and
`gpu_artifacts_local/astra_reader_audit_lesson_independent_20260914/` only.
Read AGENTS/CLAUDE and the prospective
`research_notes/analysis/2026-09-14_reader_audit_lesson_design.md`.
No maincode/notebook changes, model/tokenizer loading, GPU commands, experiment
or background jobs, commits, or independently generated replacement answers.

Native source root: node2 alias,
`/tmp/astra_reader_audit_lesson_20260914_attempt1/`.
Read-only transport: `bash gpu/ovx_ssh.sh`.
Main's SEQ-238 at 12:17 UTC records completed collection and releases the paired
fits. The reader therefore captures terminal collection immediately and takes
later immutable snapshots of training/AFTER; no launch pause or reader approval
is requested. This audit does not gate Main's launches.

Initial snapshot: `snapshot_20260914T121824219458Z` under the owned artifact root.
It contains **135 files / 4,268,159 bytes**, each locally matched against the
remote SHA-256 manifest. Collection and prepare have terminal RESULT files;
both train phases are in progress, and both AFTER directories are absent in
this snapshot. Intermediate train evidence is not presented as completed fits.
All snapshots/attempt artifacts are retained rather than replaced.

## Collection result: independently reproduced

**PASS — exact native-call replay reproduces both complete collection documents.**
Collection RESULT says `LESSON_READY`, 80 calls, zero fits, frozen base unchanged.
Native collection ran **12:14:45.806537–12:16:13.091590 UTC**.
The reader passes only the captured response for the exact matching messages
back through the captured pure helper. No model/tokenizer library is imported;
an import guard rejects torch, transformers, tokenizers, peft, and safetensors.
No answer is synthesized, corrected, normalized, retried, or substituted.
All 80 captures have no call error; observed maximum input/emitted token counts
are 629/13 for DEV and 372/14 for baseline, within the declared 2048/160 bounds.

| Panel | Correct / all | True | Fault | Context |
| --- | ---: | ---: | ---: | --- |
| BEFORE held | 7/16 | 4/8 | 3/8 | Parent-free, four A2 events, two held skins |
| Coached DEV | 62/64 | 30/32 | 32/32 | Eight earlier own events, four DEV skins |

These panels differ in both records and guidance. **62/64 versus 7/16 is not a
learning delta or a matched intervention contrast.** Model state is unchanged
by collection. Only the later parent-free paired AFTER comparison addresses
the declared supervised-adapter intervention.

## Full 64-case DEV strata and coverage

In this table, each skin cell shows `true / fault` correctness for its two
actual calls. Skin and event indexes are zero-based. All 64 outcomes, including
exact raw output strings and native CALL filenames, are preserved in
`lesson_all_outcomes.json` and `lesson_all_outcomes.tsv` within the snapshot.

| Event index / address | Skin 0 | Skin 1 | Skin 2 | Skin 3 | True | Fault |
| --- | --- | --- | --- | --- | ---: | ---: |
| 0 `E_W76IFWI75T` | pass/pass | pass/pass | pass/pass | pass/pass | 4/4 | 4/4 |
| 1 `E_CHYIWYDY6Y` | pass/pass | pass/pass | pass/pass | pass/pass | 4/4 | 4/4 |
| 2 `E_X3YBAILZSM` | pass/pass | pass/pass | pass/pass | fail/pass | 3/4 | 4/4 |
| 3 `E_QAQ5WQZQRH` | pass/pass | pass/pass | pass/pass | pass/pass | 4/4 | 4/4 |
| 4 `E_24YAGJH7YH` | fail/pass | pass/pass | pass/pass | pass/pass | 3/4 | 4/4 |
| 5 `E_GFK5ULRT6G` | pass/pass | pass/pass | pass/pass | pass/pass | 4/4 | 4/4 |
| 6 `E_3FIXU7HBPN` | pass/pass | pass/pass | pass/pass | pass/pass | 4/4 | 4/4 |
| 7 `E_3K7UVCYOTM` | pass/pass | pass/pass | pass/pass | pass/pass | 4/4 | 4/4 |
| All | 15/16 | 16/16 | 16/16 | 15/16 | 30/32 | 32/32 |

Each four-record bank contributes **31/32**, true **15/16**, fault **16/16**.
Every event has at least one true success and one fault success; minimum
coverage is three true and four fault successes. Thus the declared per-event
collection readiness condition is met, independently of Main's launch decision.

### Every failed DEV output

Raw strings below use JSON string notation: `\n` is a preserved newline, not
an edit. Both are terminal, nontruncated responses with no call error.

| DEV case | Native capture | Skin/event | Expected | Actual raw | Failure |
| ---: | --- | --- | --- | --- | --- |
| 8 | `collect/CALL_024.json` | 0 / 4 | `"NONE"` | `"E_24YAGJH7YH"` | WRONG_OUTPUT |
| 52 | `collect/CALL_068.json` | 3 / 2 | `"NONE"` | `"E_X3YBAILZSM\n"` | WRONG_OUTPUT |

These two false fault declarations remain in the complete outcome records and
are excluded from the 62 selected training rows. No corrected targets replace
them. There are no failed fault cases in this coached DEV collection.

## Baseline: all 16 cases retained

| A2 event | True | Fault | Overall |
| --- | ---: | ---: | ---: |
| `E_43DKZR6D3S` | 2/2 | 1/2 | 3/4 |
| `E_VEEAOY3IIH` | 0/2 | 1/2 | 1/4 |
| `E_QQ43NOEYBQ` | 0/2 | 1/2 | 1/4 |
| `E_DEX6OHDHJP` | 2/2 | 0/2 | 2/4 |

All failures are terminal and nontruncated, with no call errors. Native index
equals held case index for these baseline calls. Full successes and failures
are in `baseline_all_outcomes.json` and `baseline_all_outcomes.tsv`.

| Call index | Kind | Expected | Actual raw | Failure |
| ---: | --- | --- | --- | --- |
| 1 | fault | `"E_43DKZR6D3S"` | `"E_id: E_43DKZR6D3S"` | WRONG_OUTPUT |
| 2 | true | `"NONE"` | `"E_VEEAOY3IIH"` | WRONG_OUTPUT |
| 3 | fault | `"E_VEEAOY3IIH"` | `"NONE"` | ABSTAINED_ON_FAULT |
| 4 | true | `"NONE"` | `"E_QQ43NOEYBQ"` | WRONG_OUTPUT |
| 5 | fault | `"E_QQ43NOEYBQ"` | `"E_id"` | WRONG_OUTPUT |
| 7 | fault | `"E_DEX6OHDHJP"` | `"E_id"` | WRONG_OUTPUT |
| 10 | true | `"NONE"` | `"E_VEEAOY3IIH"` | WRONG_OUTPUT |
| 12 | true | `"NONE"` | `"E_QQ43NOEYBQ"` | WRONG_OUTPUT |
| 15 | fault | `"E_DEX6OHDHJP"` | `"E_id"` | WRONG_OUTPUT |

Bare-address syntax is part of the predeclared score. The reader does not
rescore the decorated output at call 1 as a successful answer.
The two held prompt skins score 2/8 and 5/8 respectively.

## Source, target, and visibility checks

- Rebuilt both case bundles from their captured original EVENT records and
  reproduced all case/source seals, calls, coverage, rows, and collection seals.
  Exactly CALL_000–CALL_079 exist; the first 16 are held, the next 64 are DEV.
- All 62 admitted assistants are exactly successful actual native child raw
  outputs, plus the declared EOT policy. Every row passes the pure helper's
  complete source/capture/row validation.
- Each coached call adds the fixed procedural parent instruction; every
  student prefix equals its uncoached case prefix. No parent guidance appears
  in a student prefix or target. Held baseline calls are parent-free.
- The eight DEV and four A2 held event sets are disjoint. No held address is a
  selection target. The synthetic fault flag explicitly says it is not an
  authentic experience; a wrong reply keeps the queried address but takes the
  other tuple fields from another actual record in the same four-record bank.
- Both arms' captured TRAINING_ROWS are identical: 80 memory rows, 20 earlier
  cue rows, and 62 successful lesson rows. Memory contains exactly eight views
  of each of the eight earlier records plus two already-written A2 records;
  the other two A2 records are absent as memory targets. The A2 bank is excluded
  from **selection-lesson** targets, not all historical memory training.

The 14 initially captured deployed source files, including the pure helper's
import dependencies, all match their corresponding bytes at local commit
`f20a8cb651e5b6e2e7154d85c7a0d7dbc9f8b38a`. This is a file-level comparison,
not a claim that the entire hybrid deployed tree is that commit. The deployed
tree lacks the new design memo and three new tests at their source paths;
these are explicitly recorded as omitted/absent, not presumed deployed. The
prospective design is read locally. Resource scanner diagnostics are outside
reader evidence and omitted; adapter directories are deliberately omitted
from the bounded snapshots. Later separately authorized preservation is below.

| Binding | SHA-256 |
| --- | --- |
| Native entry | `ba99dffa2c4ae248177fb24b830d57a626f179cdc95d81a88d5b960aee84d0a2` |
| Pure lesson helper | `81e447afb444d4f929f0d8e0ae21c0fc21ad0f2ffda48f931b7d272606ecc745` |
| Trainer source | `1e22ba8609b32266e1302762ad3f1e0420ecdf3a4beae609a7ee613892f1864b` |
| Guard source | `441575fedac444589f5ff22445d9f416538c486d287c61f37386040c09377815` |
| LESSON.json file | `7d87253196b76abe49fba1b760846d08e89f27ead4867bf719747d2e2708dd4b` |
| Loaded initial adapter state | `b82490d3d1f848bcaaa58e2167bcbbb9d5d554d60154e7b61ab7944fbe2094b9` |

The last row is a recorded tensor-state digest, not the safetensors file hash.
The starting adapter file hash in ancestry is
`0808585011b357f710f8d65d69e56d9b3be38ca6b465271b1e913cb66e0f760a`.
No large adapter was copied in the initial reader snapshots. Following the
later explicit request, both terminal adapters are preserved separately below.

## Paired fits: terminal, source/mask/log checks pass

Later snapshot `snapshot_20260914T122526843972Z` contains both completed train
RESULTs. The SFT fit finishes at **12:24:30.456321 UTC**, loss-off at
**12:24:32.343837 UTC**. Earlier partial snapshots remain preserved, including
the 12/11, 127/127, 193/192, and first-terminal observations; no attempt or
partial log is replaced by the successful terminal capture.

| Check | AUDIT_SFT | AUDIT_LOSS_OFF |
| --- | ---: | ---: |
| Actual consecutive logged updates | 200 | 200 |
| Memory / cue / lesson presentations | 200 / 200 / 400 | 200 / 200 / 400 |
| Supervised lesson presentations | 400 | 0 |
| Actual supervised tokens | 15,115 | 12,538 |
| Treatment-reference supervised tokens | 15,115 | 15,115 |
| Optimizer / seed / LR | Fresh AdamW / 0 / 3e-5 | Fresh AdamW / 0 / 3e-5 |

Both native receipts record the exact same before-state
`b82490d3d1f848bcaaa58e2167bcbbb9d5d554d60154e7b61ab7944fbe2094b9`, matching
collection and the reused corrective AFTER baseline. Both have a nontrivial
after-state and frozen-base-unchanged flags. The reader verifies receipt and
code/hash bindings; it does not load tensors to recompute native state digests.

Both TRAINING_ROWS and all **162 encoded MASKS rows** are identical. Active
labels form one contiguous target-plus-EOT span; prefixes and surrounding
non-target positions are masked. Every last target ID is EOT 151645.
The reader replays the **captured pure training-index, collation, masking, and
normalization functions for all 200 updates**, using captured token-ID arrays,
without importing a tokenizer/model or executing training. For every matched
batch, input IDs, attention masks, indexes, and the memory/cue labels are
identical. Only the two lesson rows' labels are changed to all -100 in loss-off.

Every actual LOSSES row matches that schedule and its independently counted
causal labels. Common reference denominators match update-for-update; scaled
loss equals actual mean loss times actual/reference. The **2,577 fewer active
control tokens are intentional**, not an actual-token-equality claim. Both
recipes differ only in arm identity and supervised-lesson presentations.
MASKS/RECIPE/LOSSES hashes match train provenance; captured source files match
every code-provenance binding. Lesson receipt hashes match collection RESULT.

| Arm | Native recorded after-state | Recorded adapter_model.safetensors file SHA-256 |
| --- | --- | --- |
| AUDIT_SFT | `db3f213b0040ac92dbc45ab8373bf4a0c55185d4eb23a3fca781f0bf89b431c5` | `5b7c422dc3b61cbfc4b51363f2aef2ab3b4edb6b6bee680d10dda0c172ea5fcb` |
| AUDIT_LOSS_OFF | `42c8a7e212945dd71035d13655bbfc04214a51f17bf8baf969909961b0556684` | `f9275b58be20c3a2900a3d3e61fbbb806498f8b788ada6481b7ec606e76fe43b` |

These adapter-file hashes were initially **recorded native provenance**. The
later authorized preservation below independently verifies the same hashes
against remote and copied local weight bytes. Tensor-state digests remain
native recorded digests; no model or tensor loader is run by this sidecar.

## AFTER: terminal, all held and retention endpoints reproduced

Final snapshot **`snapshot_20260914T122722598852Z`** captures all phases terminal:
**501 files / 6,464,019 bytes**. SFT AFTER finishes at **12:26:59.367033 UTC**;
loss-off AFTER finishes at **12:27:02.293408 UTC**. Each AFTER reports exactly
**102 native calls**: 16 held audit calls, 70 new-task/reader/control/recall
calls, and 16 old-retention calls. No native FAILED file is present.

Both AFTER loaded-state hashes equal their own terminal train after-state,
and their training/lesson receipt file hashes match the captured RESULT files.
Both have fresh readout invocations, parent absent, and frozen base unchanged.
The reader reproduces both held collection documents from their exact native
CALL_000–015 messages/responses through the captured pure lesson helper. Held
case bundles match BEFORE exactly, and no held supervision row is emitted.

All routing episodes are independently replayed through the captured pure
READ/ROUTE controller using only recorded actor responses, reader responses,
and the recorded actual transition outcome. The full episode documents match,
as do their ordered native call traces and per-episode files. Every recall
score is recomputed from terminal/nontruncated raw output and the captured
exact expected string, including the strict `MISS\n` endpoint. This does not
synthesize a response or supply a replacement transition outcome.

The existing pre-lesson corrective AFTER baseline is copied read-only into
`files/baseline_corrective_after/` in later snapshots. Its state matches the
shared lesson start; its routing and recall are replayed/reduced in the same
way. No duplicate baseline model calls were made.

| Endpoint | Common BEFORE | AUDIT_SFT AFTER | AUDIT_LOSS_OFF AFTER | SFT minus control |
| --- | ---: | ---: | ---: | ---: |
| Parent-free held audit, overall | 7/16 | 16/16 | 7/16 | +9 correct |
| Parent-free held audit, true | 4/8 | 8/8 | 4/8 | +4 correct |
| Parent-free held audit, fault | 3/8 | 8/8 | 3/8 | +5 correct |
| New W0 parametric routing | 3/4 | 3/4 | 3/4 | 0 |
| New routing, reader adapter off | 2/4 | 2/4 | 2/4 | 0 |
| External held-text routing bank 0 | 4/4 | 4/4 | 4/4 | 0 |
| External held-text routing bank 1 | 4/4 | 4/4 | 4/4 | 0 |
| New-record recall W0 | 2/4 | 1/4 | 0/4 | +1 correct |
| New-record recall W8 | 2/4 | 1/4 | 0/4 | +1 correct |
| Old-record retention W0 | 8/8 | 8/8 | 8/8 | 0 |
| Old-record retention W8 | 8/8 | 8/8 | 8/8 | 0 |
| Unseen MISS | 0/4 | 0/4 | 0/4 | 0 |

SFT improves held accuracy by **9/16 = 56.25 percentage points** relative to
both BEFORE and loss-off: +4/8 true and +5/8 fault. Loss-off changes neither
held correct count nor any case's success/failure status. SFT corrects all nine
previous failures (indices 1, 2, 3, 4, 5, 7, 10, 12, 15) and loses none. Every
held event reaches true 2/2 and fault 2/2 in SFT; both held skins reach 8/8.

### Numeric misses and retained failures

- Loss-off still fails held cases 1, 2, 3, 4, 5, 7, 10, 12, and 15. Its exact
  failed strings match the baseline failure table except case 4 now emits
  `"E_id"` rather than `"E_QQ43NOEYBQ"`; both remain wrong for expected NONE.
  All nine raw failures are retained in terminal `pair_audit.json` and the
  original AFTER native files. SFT has no held classifier failures.
- Parametric routing still misses `E_DEX6OHDHJP` in both arms and BEFORE:
  **1/4 goals missed**, no gained or lost goal. Reader-off routing still misses
  `E_VEEAOY3IIH` and `E_QQ43NOEYBQ`: **2/4 missed** in all three conditions.
- New W0 and W8 recall each lose the previously correct `E_QQ43NOEYBQ` under
  SFT: **2/4 → 1/4**. Only `E_43DKZR6D3S` remains exactly recalled. Loss-off
  loses both formerly exact matches: **2/4 → 0/4**, specifically through
  receipt-only errors, not erased node/port/outcome fields. Thus both arms regress
  versus BEFORE on this memory endpoint despite the positive SFT-minus-control
  difference. No old W0 or W8 record is lost.
- MISS remains **0/4**, i.e. four misses per condition. Both external-text
  routing controls remain **4/4**; these supply researcher-provided memory
  text and are not evidence of successful parametric recall.

The narrowly predeclared checkpoint components are all met: SFT true/fault
are each 8/8 (two correct above each 6/8 threshold), its matched held contrast
is positive, and old W0 remains 8/8. **That limited checkpoint is not evidence
of improved routing, universally preserved memory, autonomous selection, or
the complete experience→selection→sleep→use loop.** Here the externally taught
reader-fault behavior transfers to the held A2 comparison prompts, but new
routing does not improve and exact new-record recall declines. Main owns any
subsequent task or experiment; this memo neither authorizes nor gates it.

## Urgent A2 per-field decomposition

This supplement uses the already captured original A2 EVENT records and actual
native replies, not synthetic replacement answers. All **69 observations** are
preserved in `a2_field_decomposition/decomposition.json` and `all_fields.tsv`
under the owned artifact root: 24 direct recall probes (three conditions × two
wrappers × four records), 21 actual parametric reader replies, and 24 actual
reader-adapter-off control replies. Literal field extraction and strict EVENT
grammar validation are recorded separately; invalid/missing fields are not
silently discarded. Every observation retains exact expected/actual raw text,
each field comparison, query identity, source file, and terminal flags.

### Original reference tuples

The original corrective selection is indices **0 and 2**. Indices **1 and 3**
were not selected for that memory write and remain absent from the 80 memory
training rows. All four are excluded from the selection-lesson targets.

| Index | Original EVENT | Selected | AT / node | DID / port | GOT / outcome | EVIDENCE / receipt |
| ---: | --- | --- | --- | --- | --- | --- |
| 0 | `E_43DKZR6D3S` | yes | `N_NQ7SZP2WK3` | `P_MLFJXQ3WZH` | `N_WBXQVETNWG` | `R_V75J4A4RYG` |
| 1 | `E_VEEAOY3IIH` | no | `N_NQ7SZP2WK3` | `P_X3KIPDIW4F` | `N_6AUMRWYCVK` | `R_YJNOWTRK53` |
| 2 | `E_QQ43NOEYBQ` | yes | `N_IRD6ZSHY2B` | `P_ONQCERJ5LE` | `N_ZXFXLP2ESD` | `R_6MJCDE77X2` |
| 3 | `E_DEX6OHDHJP` | no | `N_IRD6ZSHY2B` | `P_FWMNJO5UYN` | `N_DH2AYPUMUT` | `R_3KI5HYYQOV` |

### Selected records: every changed field

Both selected records are exactly correct in BEFORE W0 and W8. Every selected
AFTER reply preserves the correct EVENT address, port, and outcome. All are
terminal, nontruncated, and valid under the strict EVENT parser.

| Condition | Index | Wrapper / actual reader | Changed field | Expected → actual | Other fields |
| --- | ---: | --- | --- | --- | --- |
| SFT | 0 | W0, W8, actual W0 reader | none | exact original record | all five correct |
| SFT | 2 | W0 and actual W0 reader | node only | `N_IRD6ZSHY2B` → `N_IRD6ZSHY23` | EVENT, port, outcome, receipt correct |
| SFT | 2 | W8 | node only | `N_IRD6ZSHY2B` → `N_IRD6ZSHY63` | EVENT, port, outcome, receipt correct |
| Loss-off | 0 | W0, W8, actual W0 reader | receipt only | `R_V75J4A4RYG` → `R_3CHIKVFZ4I` | EVENT, node, port, outcome correct |
| Loss-off | 2 | W0, W8, actual W0 reader | receipt only | `R_6MJCDE77X2` → `R_3CHIKVFZ4O` | EVENT, node, port, outcome correct |

Thus per wrapper, among the two selected records:

| Field-level quantity | BEFORE | SFT | Loss-off |
| --- | ---: | ---: | ---: |
| Exact whole record | 2/2 | 1/2 | 0/2 |
| Exact EVENT address | 2/2 | 2/2 | 2/2 |
| Exact node | 2/2 | 1/2 | 2/2 |
| Exact port | 2/2 | 2/2 | 2/2 |
| Exact outcome | 2/2 | 2/2 | 2/2 |
| Exact receipt | 2/2 | 2/2 | 0/2 |
| Node+port+outcome jointly intact | 2/2 | 1/2 | 2/2 |
| Port+outcome jointly intact | 2/2 | 2/2 | 2/2 |

**The whole-record exact-match ordering reverses for the node+port+outcome
subtuple.** Loss-off scores worse on whole-record exact match while retaining
both selected operational tuples; SFT preserves receipts but corrupts one
node identifier. Opaque identifiers are exact and case-sensitive: this node
error is real, not a harmless spelling variant. Conversely, receipt corruption
is a provenance-fidelity failure, not evidence that the port/outcome mapping
was wholly forgotten. Neither measure by itself establishes general memory
quality or latent information availability.

### Unselected records 1 and 3: literal values, not newly lost successes

Both unselected records preserve their queried EVENT address but have wrong
node, port, outcome, and receipt in **both wrappers and all three conditions**.
They already failed these four fields BEFORE; their AFTER failures must not be
counted as newly forgotten previously correct facts. The exact returned field
strings are below; compare with the immutable originals above.

| Condition | Wrapper | Index | Returned node | Returned port | Returned outcome | Returned receipt |
| --- | --- | ---: | --- | --- | --- | --- |
| BEFORE | W0 | 1 | `N_NQ7J7B2WK` | `P_S7AIZXQ77X` | `N_WBXQVETNWG` | `R_V77FCXUDYO` |
| BEFORE | W0 | 3 | `N_KGA6B2GC43` | `P_6Q379NEQYX` | `N_R2R3W7QECX` | `R_O32FCXUDYO` |
| BEFORE | W8 | 1 | `N_IRYXQGCFDQ` | `P_GBVCPQPLZQ` | `N_ASWIKJMAEC` | `R_VEEAOY3IIH` |
| BEFORE | W8 | 3 | `N_FEKWBHXQIC` | `P_D67TYON4RO` | `N_PZO6WN5IY` | `R_3CHIKVFZQX` |
| SFT | W0 | 1 | `N_FEKWBHXIER` | `P_LRZJ7WQPLZ` | `N_XKJMA6ROET` | `R_OIAWCIMJMN` |
| SFT | W0 | 3 | `N_L5AIZBYJCX` | `P_2RVHKWHYEC` | `N_R2WQSVO7XZ` | `R_OIAWCIMJMN` |
| SFT | W8 | 1 | `N_FEKWBHXIER` | `P_LRZJ7WQPLZ` | `N_XKJMA6ROET` | `R_QKW7TYNMYX` |
| SFT | W8 | 3 | `N_FEKWBHXIER` | `P_LRZJ7WQPLZ` | `N_R2WQSVO7XZ` | `R_OIAWCIMJMN` |
| Loss-off | W0 | 1 | `N_FEKWBHXIER` | `P_LRZJ7WQPLZ` | `N_3CHIKVFZ4I` | `R_O34FCXUDYO` |
| Loss-off | W0 | 3 | `N_KGA6B2GC43` | `P_VCT6ADPQIC` | `N_FH6EXUSNGV` | `R_OIA6CFDQYX` |
| Loss-off | W8 | 1 | `N_IRZJLOLZCX` | `P_3CHIKVFZ4I` | `N_3CHIKVFZ4I` | `R_O34J5A4JYX` |
| Loss-off | W8 | 3 | `N_Q5AIZBYJCX` | `P_3CHIKVFZ4I` | `N_WBXQVETNWG` | `R_OIAWCIMJMN` |

Some baseline unselected replies fail strict identifier grammar as well as
factual comparison: W0 indices 1/3 and W8 index 3. Literal extraction preserves
their visible fields without validating or repairing those identifiers.
All SFT/loss-off direct A2 replies pass strict grammar; that does not make
their wrong field values true.

### Actual routing reader replies: same field changes, not a probe-only artifact

Each condition uses the same seven actual parametric reader calls. The query
sequence by zero-based task episode is `0:[0]`, `1:[0,1]`, `2:[3,2]`,
`3:[3,2]`. Thus selected indices 0 and 2 are read twice each; unselected index
1 once and index 3 twice. **All 21 actual parametric reader raw strings are
byte-identical to the corresponding condition's direct W0 probe** for the same
address. There is no inferential substitution from W8 or a synthetic stimulus.

| Actual parametric reader quantity | BEFORE | SFT | Loss-off |
| --- | ---: | ---: | ---: |
| Exact replies, all seven calls | 4/7 | 2/7 | 0/7 |
| Selected-record exact replies | 4/4 | 2/4 | 0/4 |
| Selected node-only failures | 0/4 | 2/4 | 0/4 |
| Selected receipt-only failures | 0/4 | 0/4 | 4/4 |
| Selected port+outcome intact | 4/4 | 4/4 | 4/4 |
| Unselected node/port/outcome/receipt all wrong | 3/3 | 3/3 | 3/3 |

Routing stays 3/4 with at least one read on all 4/4 tasks in every condition.
That coexists with the above reader errors; it does not prove that receipt or
node fidelity is dispensable in general. Reader-adapter-off controls have eight
actual replies per condition, all exactly `"MISS"` (no EVENT tuple), and route
2/4. Those 24 no-record replies are preserved separately, not counted as
invented factual tuples or evidence of lost learned adapter contents.

### Replay exposure and interpretation

The selected A2 training records were not omitted or replaced: each has eight
source-exact memory views and **16 actual logged memory presentations per arm**
(each of its eight rows is visited twice in the 200-update cyclic schedule).
Both arms still expose 80 total memory rows; their recent selected-record
fidelity changes therefore occur despite those retained presentations. This
checks data inclusion/exposure, not the mechanism of the resulting field drift.

The formal held-classifier checkpoint remains PASS. The recent-selected-memory
regression is **node fidelity under SFT versus receipt fidelity under loss-off**,
not blanket forgetting of every field and not broad substrate readiness.
Source admission of an actual native reply is separate from its correctness:
all recorded replies, including wrong tuples and MISS, remain in the audit.
Main's separately declared native actual-reader audit is a different no-fit
stage. This decomposition makes no claims about its yet-unreviewed results
and does not block its launch.

## Second-priority terminal adapter preservation

After the explicit follow-up authorization, **both complete terminal train
directories are preserved and byte-verified** under
`gpu_artifacts_local/astra_reader_audit_lesson_independent_20260914/terminal_saved_adapters_20260914/`.
Preservation runs **2026-09-14 12:32:58.651743–12:33:05.815436 UTC**.
All VM files and the retained archive are on the `/data` workspace, not `/tmp`.
Remote evidence remains read-only; no model/tokenizer/GPU operation is used.

| Arm | Complete train files | Exact file bytes | adapter_model.safetensors SHA-256 |
| --- | ---: | ---: | --- |
| AUDIT_SFT | 13 | 82,128,644 | `5b7c422dc3b61cbfc4b51363f2aef2ab3b4edb6b6bee680d10dda0c172ea5fcb` |
| AUDIT_LOSS_OFF | 13 | 82,131,354 | `f9275b58be20c3a2900a3d3e61fbbb806498f8b788ada6481b7ec606e76fe43b` |
| Total | 26 | 164,259,998 | each model file is 80,792,096 bytes |

Each copy at `files/{ARM}/train/` contains the complete `adapter/` directory
(weights, configuration, README), plus RESULT, REQUEST, ADAPTER_PROVENANCE,
DEV_CASES, HELD_CASES, INPUTS, TRAINING_ROWS, MASKS, RECIPE, and LOSSES.
Pre-copy and post-copy remote snapshots agree in full inventory, sizes,
hashes, and recorded file modification/change timestamps. All 26 local files
match both remote SHA-256 manifests; two strict local checks each pass 26/26.
Every adapter-file hash and every provenance-bound training-artifact hash
also matches the preserved native RESULT/ADAPTER_PROVENANCE values.

Retained archive `reader_audit_train_adapters.tar` is **164,290,560 bytes**,
SHA-256 `b13e7e40885dfef4edca163bed74dcfc4d7d2d6a4fb94519f10de2bfbe4be5ac`.
Its strict local checksum check passes. Archive plus extracted payload uses
**328,550,558 logical bytes**, excluding manifests/scripts/receipts.
Full per-file checksums are in `remote_before.sha256`, `remote_after.sha256`,
and identical `local_manifest.sha256`; JSON manifests include exact sizes.
`verification.json`, both `*_local_check.txt` files, and
`archive_local_check.txt` preserve the successful verification evidence.
No transport, copy, archive, source-stability, or hash failure occurred.

## Evidence and limitations

Under each snapshot, `manifest.json` inventories capture times, phase states,
files, byte sizes, per-file remote hashes, and omissions. `remote.sha256` and
`local_check.txt` establish matched local bytes. `collection_audit.json`
contains the exact-call replay checks, all outcomes, strata, coverage, source
comparisons, and target checks. `capture.py` and `audit_collection.py` in the
owned artifact root record the reader procedure; neither runs a model.
`audit_pair.py` records pure batch-mask replay, terminal fit provenance checks,
held exact-call replay, controller replay, and all endpoint score reductions.
Terminal `pair_audit.json` is **PASS_COMPLETE** and includes all per-event
endpoint outcomes and every retained failed raw recall output. Eight immutable
snapshots preserve **43,540,391 captured payload bytes** in total, excluding
the sidecar's own scripts/manifests/reports; no large adapter is included in
those eight bounded snapshots. The later adapter preservation is accounted
for separately above. The original `FINAL_RECEIPT.json` remains the immutable
12:29:35 close of the initial phase; `SUPPLEMENT_RECEIPT.json` binds the later
field decomposition, updated memo, and authorized adapter preservation.
The bounded attempt-root check found only the specified attempt1 at capture
time. There were no transport, integrity, replay, or native infrastructure
failures; observed child-output failures are explicitly retained above.

This is outcome-selected supervised teaching on researcher-rendered faults
over already-exposed, tiny DEV record families. It is not an autonomous
experience-selection result, an authenticated new experience, a clean
unopened-test estimate, a task-disjoint H1 result, an H2 slope, a population
effect, or a sampler comparison. Coverage is a finite collection property.
The reader's checksum/replay PASS is not a scientific success verdict.

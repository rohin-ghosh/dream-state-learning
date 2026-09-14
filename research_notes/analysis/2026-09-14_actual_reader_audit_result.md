# Independent terminal actual-reader audit — 2026-09-14

## Result and boundary

**Evidence/replay PASS.** Every native audit call is preserved and exactly
replayed. AUDIT_SFT classifies **5/7** actual reader invocations correctly and
admits source selections **[1, 3, 3]**; AUDIT_LOSS_OFF classifies **1/7** and
admits **[1]**. These are source-valid pointers, not new generated facts or
evidence that the subsequent repair will be useful. This stage makes **zero
fits**. The repeated source 3 is retained, not deduplicated away.

**Important limit:** SFT still misses both node-only errors in source 2. The
two actors audit different actual reader strings at all seven matched query
positions. Therefore 5/7 versus 1/7 is not an isolated same-stimulus comparison
of selection policies, and it does not establish broad substrate readiness.
Main's separately prepared four-cell repair is outside this sidecar's scope;
this report neither launches nor gates it.

Owned files: this new memo and the unique artifact root
`gpu_artifacts_local/astra_actual_reader_audit_independent_20260914T1248Z/`.
Read repository AGENTS/CLAUDE and the prospective actual-reader design. No
shared notebook, maincode, prior sidecar file, or other worker's edits are
modified; no commits, model/tokenizer/GPU execution, or launches occur.

## Native scope, timing, and preservation

Remote evidence: node2 alias,
`/tmp/astra_actual_reader_audit_20260914_attempt1/`.
Transport is read-only `bash gpu/ovx_ssh.sh`; remote stderr is suppressed to
avoid exposing internal hosts or credentials. No remote files are created.
No curl, wget, or WebFetch is used. All local evidence is in the data-backed
workspace; no large model or adapter is copied.

Declared source: **`adfbdd45911e1cf946ccd89bbc724af2210198df`**. Both launch
receipts identify it, both have completion timestamps, and all **24 captured
deployed source files** match their corresponding bytes at that commit. This
is a file-level verification of the captured runtime/helper files, not a claim
that every file in the deployed source tree was independently inspected.

| Arm | Native start UTC | Native finish UTC | Terminal status | Audit calls | Fits | Parent |
| --- | --- | --- | --- | ---: | ---: | --- |
| AUDIT_SFT | 12:33:47.512997 | 12:34:44.000552 | COMPLETE | 7 | 0 | absent |
| AUDIT_LOSS_OFF | 12:33:47.537633 | 12:34:44.337250 | COMPLETE | 7 | 0 | absent |

All dates here are **September 14, 2026**. Capture completed at
**12:48:11.935002 UTC**, after both arms were terminal.

| Preserved scope | Files | Exact bytes |
| --- | ---: | ---: |
| Complete native actual-audit JSON/text/log files, including prepare, launch, and both arms | 52 | 1,166,877 |
| Deployed source/helper/import-dependency files | 24 | 409,564 |
| Referenced A2 collection and lesson/train/AFTER lineage evidence, excluding adapters | 278 | 5,132,214 |
| Total captured payload | 354 | 6,708,655 |

There are **no omitted bounded native audit files**. Both sets of CALL_000
through CALL_006, ACTUAL_CASES, ACTUAL_READERS, INPUTS, REQUEST, RESULT, logs,
preparation files, and launch metadata are retained. All 354 captured local
files match their remote SHA-256 and byte sizes. The native-source read checks
file size/modification/change metadata before and after each read. Complete
per-file hashes and sizes are in `manifest.json` and `remote.sha256`; strict
local checksum results are in `local_check.txt`. The final receipt records a
second read-only remote hash verification and unchanged selected inventory.

## Complete counts and selections

| Quantity | AUDIT_SFT | AUDIT_LOSS_OFF |
| --- | ---: | ---: |
| Actual routing task denominator | 4 | 4 |
| Actual reader invocations audited | 7 | 7 |
| Overall classification correct | 5/7 | 1/7 |
| Correct on accurate replies | 2/2 | 0/0 — no accurate-reply cases |
| Correct on inaccurate replies | 3/5 | 1/7 |
| Source-valid pointer admissions | 3 | 1 |
| Admissions in invocation order | [1, 3, 3] | [1] |
| Unique original sources selected | [1, 3] | [1] |
| Previously written corrective sources | [0, 2] | [0, 2] |
| Unique newly selected relative to that write | [1, 3] | [1] |
| Mapped original query-row occurrences | 24 | 8 |
| Unique mapped original query rows | 16 | 8 |
| NONE outputs | 4 | 0 |
| Invalid pointer outputs | 0 | 6 |

The OFF accurate-reply stratum is absent, **not 0% accuracy**. Its source 0
and source 2 reader replies have receipt errors, so all seven inputs are
fault cases. SFT's two source 0 replies are fully accurate; its two source 2
replies are node-only faults. Both arms' unselected source 1/3 replies contain
multiple wrong fields.

Source index/address map is unchanged from the original A2 collection:

| Index | Address | Previously written in corrective sleep? |
| ---: | --- | --- |
| 0 | `E_43DKZR6D3S` | yes |
| 1 | `E_VEEAOY3IIH` | no |
| 2 | `E_QQ43NOEYBQ` | yes |
| 3 | `E_DEX6OHDHJP` | no |

The full seven-slot selection arrays, preserving non-admissions, are:

- SFT: `[null, null, 1, 3, null, 3, null]`.
- OFF: `[null, null, 1, null, null, null, null]`.

## All 14 actual responses

Indexes are zero-based. Raw outputs use JSON string notation; `\n` denotes
the actual retained final LF. No malformed address is repaired or rescued.
Both arms have the same episode/query ordering, but different reader strings.

| Case | Episode/read | Queried source | SFT reader kind | SFT actual audit output | SFT correct / admitted | OFF reader kind | OFF actual audit output | OFF correct / admitted |
| ---: | --- | ---: | --- | --- | --- | --- | --- | --- |
| 0 | 0/0 | 0 | true | `"NONE"` | yes / no | fault | `"E_id: E_43DKZR6D3S"` | no / no |
| 1 | 1/0 | 0 | true | `"NONE"` | yes / no | fault | `"E_id: E_43DKZR6D3S"` | no / no |
| 2 | 1/1 | 1 | fault | `"E_VEEAOY3IIH\n"` | yes / source 1 | fault | `"E_VEEAOY3IIH"` | yes / source 1 |
| 3 | 2/0 | 3 | fault | `"E_DEX6OHDHJP\n"` | yes / source 3 | fault | `"E_id"` | no / no |
| 4 | 2/1 | 2 | fault | `"NONE"` | no / no | fault | `"E_id"` | no / no |
| 5 | 3/0 | 3 | fault | `"E_DEX6OHDHJP\n"` | yes / source 3 | fault | `"E_id"` | no / no |
| 6 | 3/1 | 2 | fault | `"NONE"` | no / no | fault | `"E_id"` | no / no |

All 14 responses are terminal, nontruncated, and have no callback error.
SFT's maximum observed input/emitted counts are **368/10 tokens**; OFF's are
**367/14**, below the declared 2048/160 caps. There is exactly one recorded
audit call per actual memory invocation and no retry or extra response.

SFT's misses at cases 4 and 6 are important: the consumed source 2 reply changes
only node `N_IRD6ZSHY2B` to `N_IRD6ZSHY23`; EVENT, port, outcome, and receipt
remain correct, but the declared all-fields comparison still requires source
2, not NONE. OFF's source 0/2 replies preserve operational fields but change
receipts, and its outputs fail the strict pointer syntax. This is narrower
than claiming complete factual forgetting or universally reliable auditing.

## Why these are actual-source-linked calls

The reader replays the **captured deployed pure helper**, with a guard that
rejects torch, transformers, tokenizers, peft, and safetensors imports. The
callback returns only a native captured response after asserting exact equality
of its prompt and the helper's requested messages. The resulting full
ACTUAL_READERS documents equal the preserved originals, including every seal,
failure, summary, selection, row index, and material-origin record.

Additional checks establish the recorded native lineage:

1. Replayed the original A2 COLLECTION from its own eight captured native
   calls; verified four accepted original EVENTs and all 32 source query rows.
   Its captured file hash equals its native collection receipt.
2. ACTUAL_CASES embeds exactly that source collection, not replacement
   records. Each public receipt and source EVENT is validated by the existing
   pure collection/route preparation code.
3. All four source routing episodes equal their own AFTER panel, episode
   files, and the embedded route records. The pure controller replays their
   actual actor responses, reader replies, and committed transition outcomes;
   committed outcomes also match the original receipt-grounded collection.
4. The ordered actor/reader trace responses equal the independently captured
   numbered native OWN_PARAMETRIC calls. Every audit reader string equals its
   exact referenced memory trace, with case/episode/trace/response/raw hashes.
5. Native actual-audit RESULT, own AFTER RESULT, and own train RESULT join on
   the same arm-specific actor state and exact receipt file hashes. Both
   train starts join the common lesson actor; all source provenance documents
   agree. This is developmental ancestry, not a claim that the earlier A2
   collecting actor had the final post-lesson weights.
6. All six files in each native `actual_source.source_files` mapping match the
   copied original AFTER file hashes. The native entry and actual helper
   hashes match the deployed source bytes; both prepare-case bundles equal
   their terminal arm's cases.

**Authentication limit:** these checks establish unchanged captured native
file bytes, receipt-chain consistency, and exact replay. They do not provide
independent hardware attestation against coherently forged logs, nor do they
recompute tensor-state digests by loading a model. No such stronger claim is
made. Adapter file hashes below are native recorded lineage values; this
actual-audit sidecar does not copy or rehash the giant weight files.

## Admission, correctness, and duplicate accounting

Classification correctness compares the actual child string to the requested
address on a fault, or NONE on a true reply. Source admission separately checks
whether the actual child string names **any** original A2 source address.
A valid but wrong original address would remain source-admissible under this
policy; the reader does not impose a correctness gate. In this particular
dataset all four admitted pointers happen to be correct, so no observed
incorrect-but-valid admission demonstrates that branch empirically.

NONE and malformed/unknown strings create no substitute target. The SFT NONE
responses at its two node-only errors remain incorrect, non-admitted outputs.
OFF's decorated address and bare `E_id` outputs remain invalid; their apparent
intent is not used to salvage a selection.

Every admitted pointer maps only to the original source's eight existing
query rows. Source 1 maps to `[1,5,9,13,17,21,25,29]`; source 3 maps to
`[3,7,11,15,19,23,27,31]`. SFT contains source 1 once and source 3 twice:
**24 row occurrences, 16 unique rows**. OFF contains source 1 once:
**8 occurrences, 8 unique rows**. Each material-origin entry binds the actual
audit call and the original source raw hash. No reader-generated false tuple
or child audit output becomes a new memory fact. This branch does not fit any
of those rows.

All seven memory invocations are included, not just failed-route traces. In
each arm, five calls come from successful routes and two from the failed
route. Two of SFT's three admissions come from successful routes; OFF's only
admission also comes from a successful route. Both original AFTERs route 3/4.
Thus source selection is not filtered to route failures, and inclusion does
not prove that a selected record caused, explained, or will repair a goal miss.

## Exact hashes

These are SHA-256 values. File hashes and canonical helper document seals are
different objects and are explicitly distinguished.

| Object | SHA-256 |
| --- | --- |
| Deployed native entry `gpu/astra_reader_audit_lesson.py` | `2b1c52703f686095d70a601e295826dc34d183e880a54d1c47f7f6c564e07ab2` |
| Deployed pure actual helper | `c7d02970144015453201e47a00c946bd49e4be62581a81d5a845d338def4340e` |
| Deployed actual guard | `ed40b692b7f66affe4e2489261c1ab96b7b5c10c0223bfd9f0f2ccb5f0f94bdd` |
| Original A2 COLLECTION.json file | `d5d9162827c5f621644d96791c751283b50cde954c30c9ac87e2ed9a273f55c5` |
| Original A2 RESULT.json file | `c13d759e8fe6ad82839701d25d80c9291a4822fc06d8c56a920db5a2fc0b1245` |
| Shared lesson RESULT.json file | `93d20d7ca7051e8d7f2ee27ad9d4f7d91f0b35aaf351fbe0a24c0eaa0031d5a5` |
| SFT actual RESULT.json file | `0641ae595365177055bd5dadef054770359f5ef1d82271491cb0f717e33f1aa8` |
| OFF actual RESULT.json file | `25901598c1e0be804d17151ab34999ad88ca9be386ff361daf77bbb9235bc92e` |
| SFT ACTUAL_CASES.json file | `ea3e19f343560322cf87f6475146e5b870b97d6e244c8938335c5e7d24a82d00` |
| OFF ACTUAL_CASES.json file | `6e6474da172edb461a1585f2dede6456b48a1b8796743fb65be944c4c5129459` |
| SFT ACTUAL_READERS.json file | `0c7d3ecc2f1329c3fdf9c1b91690df944c32fc5198482c8dbc161827c518cd73` |
| OFF ACTUAL_READERS.json file | `f3ac87ffc52e61868590fc5077c07e417e0be8eee8cd1190a62961ef5d6753dc` |
| SFT canonical audit document seal | `da244e6b84ae263e8a9eaf781b925cfc26726939bf0440ff2f2c9e8e372d95e2` |
| OFF canonical audit document seal | `db71e7756dcc25a2d6af98b6da298140eb8410ff182b9adb9b6ff547c9fbd054` |
| SFT own train RESULT.json file | `434774fa817ad8b737c1fe9cd46a5bbe6d365c8f5e33f9cb74c45f7ad5367ed2` |
| OFF own train RESULT.json file | `1ad298353ed84c5c6bfa1cc005de79ec9e976cdec63d3838e3b393a82d291c29` |
| SFT own AFTER RESULT.json file | `4b22daac0f485c8227c62e3cce2cd68282ad5ac4fa06d6b3dbd31691c9c3cc33` |
| OFF own AFTER RESULT.json file | `b6ccbe717fde6d91fb18c778ed1e6ed5cc72202ab81c79d10c539f62a671942b` |

Native recorded state/file lineage:

| Actor | Tensor-state digest | Native recorded adapter_model.safetensors file hash |
| --- | --- | --- |
| SFT actual audit = SFT AFTER = SFT trained state | `db3f213b0040ac92dbc45ab8373bf4a0c55185d4eb23a3fca781f0bf89b431c5` | `5b7c422dc3b61cbfc4b51363f2aef2ab3b4edb6b6bee680d10dda0c172ea5fcb` |
| OFF actual audit = OFF AFTER = OFF trained state | `42c8a7e212945dd71035d13655bbfc04214a51f17bf8baf969909961b0556684` | `f9275b58be20c3a2900a3d3e61fbbb806498f8b788ada6481b7ec606e76fe43b` |

The earlier A2 collecting state is
`07ecf4c5d965db5ea2765482439db3de5e230d90e0d86a99876a9c4ce6109300`.
Both lesson fits begin from common corrective state
`b82490d3d1f848bcaaa58e2167bcbbb9d5d554d60154e7b61ab7944fbe2094b9`.
The distinct hashes are an explicit ancestry chain, not interchangeable IDs.

## Interpretation and handoff

The predeclared practical observation is supported narrowly: SFT correctly
recognizes the two accurate reader replies, selects two previously unwritten
original sources, and catches the three multi-field wrong invocations. The
control also selects one previously unwritten source. SFT misses both subtle
node-only errors; OFF admits no selections for its four receipt-only errors.
All failures and duplicate invocations are part of the denominator.

This is **actual captured-reader classification plus source-pointer
selection**, distinct from the earlier synthetic-fault held classifier and
from any later utility of a memory repair. It uses the original source table
and a fixed public comparison task; it is not autonomous experience discovery,
a new authenticated experience, amortized parenting, a task-disjoint H1
result, an H2 slope, a sampler claim, or broad substrate readiness. All seven
paired reader strings differ, so even the +4 correct count contrast must not
be presented as an isolated selection-policy effect. Repeated reads also do
not create independent population samples.

`independent_replay.json` contains all joins, exact counts, source comparisons,
and full per-call outcomes. The two `*_all_outcomes.json` / `.tsv` files expose
all 14 responses without filtering failures. `capture.py` and `replay.py`
record the sidecar method. `FINAL_RECEIPT.json` binds this memo, the replay
report, all preserved file checks, and the final remote recheck. No native or
reader infrastructure failure was observed; classification misses are the
explicit behavioral results above. Main owns the independent four-cell repair
and all future execution; this sidecar made no changes to that work.

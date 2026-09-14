# Selected-reader repair: independent field and decision analysis

September 14, 2026. Terminal local evidence read at **13:04:14 UTC**.
Declared repair source: `fbe0981c36c30590b4f640c4134cca48bf36272c`.

## Bounded conclusion

Both SFT repair cells and OFF_UNIFORM restore **every A2 field at W0 and
W8**, with all eight older records still exact. OFF_SELECTED restores the
previous receipt-only errors on A2 sources 0/2 and all four wrong body fields
on source 1, but leaves source 3's node/port/outcome/receipt wrong. It also
introduces an older-record regression: **receipt only at W0; port plus
receipt at W8**, not loss of the entire old fact.

**Both OFF cells falsely select source 1 after its actual reader reply has
become fully correct.** These are admissible original addresses but wrong
classifications, not useful repair evidence. OFF_SELECTED additionally emits
the invalid literal `E_ID\n` on both remaining actual fault invocations;
neither output is a selection of source 3. Both OFF cells retain a malformed
response on the same synthetic HELD fault, discussed below.

Both SFT cells retain the formal fixed-panel **16/16 classifier result**
(8 true, 8 fault). Their actual 6/6 panels contain **zero faults**. Thus the
earlier SFT node-only false negatives disappear because the memories are now
correct, not because these actual panels demonstrate successful detection of
node-only faults. This is a bounded DEV result, not broad substrate readiness
or a launch gate.

The preceding actual-audit memo is already complete:
`research_notes/analysis/2026-09-14_actual_reader_audit_result.md`.
This follow-up changes no strict score and performs no new generation.

## Evidence and method

All four repair-cell inputs are read directly from Main's local archive:
`gpu_artifacts_local/astra_selected_reader_repair_terminal_20260914_attempt1/extracted/{CELL}/after/`.
Only `RESULT.json`, `AFTER_HELD.json`, and `NEXT_ACTUAL_READERS.json` are used
as analysis inputs per cell. Each AFTER reports `COMPLETE`.

The two parent post-lesson AFTERs and prior actual audits come from the
already preserved bounded snapshot in this sidecar's owned directory:
`gpu_artifacts_local/astra_selected_reader_repair_fieldcaptures_20260914T1259Z/files/parents/{ARM}/`.
They correspond to the prior lesson AFTER and actual-audit roots, not a new
parent run. The earlier snapshot is left intact; no further remote copy is
made after Main supplies the terminal archive.

New diagnostic evidence is in the same owned directory:

- `local_field_inputs.json`: exact paths, byte sizes and SHA-256 hashes for
  **18 input JSON files / 1,478,848 bytes**, limited to the above field inputs.
- `field_analysis.json`: **144 recall rows**, **39 actual memory traces**,
  **96 HELD responses**, **39 actual-audit responses**, and their matched
  parent/cell field and decision deltas. These totals include both parents
  and all four repair cells; they are diagnostic coverage, not independent
  trials. W0/W8 and repeated reads are not deduplicated.

EVENT/AT/DID/GOT/EVIDENCE are compared literally as
address/node/port/outcome/receipt. Raw strings and recorded strict results are
preserved. A framing parser extracts tokens without repairing their spelling
or supplying missing identifiers. Across these 144 recall rows, **no strict
failure is merely a framing difference with all five fields intact**.
All inspected recall generations, actual reads and audit responses are
terminal and untruncated; audit captures contain no call errors.

Every one of the **39 actual reads** matches its corresponding W0 raw string
exactly. Every actual-audit reader string matches the memory trace at its
recorded episode/trace position. Therefore the actual-error decomposition
below describes text the routing actor consumed, not a substitute W8 probe
or a researcher-reconstructed response. No old-record actual routing reads
are present in these A2 traces; old-field findings are W0/W8 recall findings.

All 16 HELD case objects and captured input messages match exactly between
each repair cell and its own parent. This permits matched-input output
diagnostics, unlike the changing actual-reader stimuli. Audit success is
checked against only the exact expected output or that output plus one LF,
consistent with the captured scoring code. Embedded address substrings do
not receive credit or admission.

This is **not** a second full reducer, schedule, source-tree or adapter hash
audit. Goodall owns primary reduction; Main owns the full archive and adapter
verification. No weights are loaded or hashed here. Repository AGENTS/CLAUDE
were read. Only this new memo and the owned fieldcapture directory are
written; no shared notebook, code, model/tokenizer, GPU, job, commit, or other
worker's file is changed.

## A2: which fields changed?

Source indexes are zero-based and refer to original experienced records.
“Previously selected” here means the earlier corrective write `[0,2]`, not
the later actual-audit selections SFT `[1,3,3]` and OFF `[1]`.

| Index | EVENT | Earlier corrective status | Node | Port | Outcome | Receipt |
| ---: | --- | --- | --- | --- | --- | --- |
| 0 | `E_43DKZR6D3S` | selected/written | `N_NQ7SZP2WK3` | `P_MLFJXQ3WZH` | `N_WBXQVETNWG` | `R_V75J4A4RYG` |
| 1 | `E_VEEAOY3IIH` | unselected | `N_NQ7SZP2WK3` | `P_X3KIPDIW4F` | `N_6AUMRWYCVK` | `R_YJNOWTRK53` |
| 2 | `E_QQ43NOEYBQ` | selected/written | `N_IRD6ZSHY2B` | `P_ONQCERJ5LE` | `N_ZXFXLP2ESD` | `R_6MJCDE77X2` |
| 3 | `E_DEX6OHDHJP` | unselected | `N_IRD6ZSHY2B` | `P_FWMNJO5UYN` | `N_DH2AYPUMUT` | `R_3KI5HYYQOV` |

All six conditions preserve the EVENT address on every A2 recall. Body-field
accuracy and full-target accuracy are:

| Condition | Full target W0 / W8 | Correct node | Correct port | Correct outcome | Correct receipt |
| --- | --- | ---: | ---: | ---: | ---: |
| Parent SFT | 1/4 / 1/4 | 1/4 | 2/4 | 2/4 | 2/4 |
| Parent OFF | 0/4 / 0/4 | 2/4 | 2/4 | 2/4 | 0/4 |
| SFT_SELECTED | 4/4 / 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| SFT_UNIFORM | 4/4 / 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| OFF_SELECTED | 3/4 / 3/4 | 3/4 | 3/4 | 3/4 | 3/4 |
| OFF_UNIFORM | 4/4 / 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |

Each field count applies separately to W0 and W8; these are not pooled
eight-item denominators. Wrong identifier values can differ between wrappers.

### Previously written sources 0 and 2

- Parent SFT source 0 is already fully correct and stays so. Source 2 has
  **only a node error**: W0/actual `N_IRD6ZSHY23`, W8 `N_IRD6ZSHY63`, versus
  `N_IRD6ZSHY2B`. Port/outcome/receipt are intact. Both SFT cells restore the
  node. This is not recovery from a wholly missing record.
- Parent OFF source 0 has **only a receipt error**, `R_3CHIKVFZ4I`; source 2
  likewise has only `R_3CHIKVFZ4O` wrong. Both OFF cells restore the expected
  receipts shown above. Their previously correct nodes, ports and outcomes
  remain correct.
- These sources were not in either actor's next selected set. The design
  retains earlier written memory views in the common 80-row rehearsal pool;
  improvement here cannot be assigned to novel-source selection alone.

### Previously unwritten sources 1 and 3

Both parents have wrong node, port, outcome and receipt on both records,
while retaining the requested EVENT address. Both SFT cells and OFF_UNIFORM
repair all four body fields for both sources. OFF_SELECTED repairs source 1
but not source 3. Its residual source-3 values are:

| Field | Expected | OFF_SELECTED W0 and actual reads | OFF_SELECTED W8 |
| --- | --- | --- | --- |
| Node | `N_IRD6ZSHY2B` | `N_KGA6B2GC43` | `N_KGA6B2GC43` |
| Port | `P_FWMNJO5UYN` | `P_V64NBDX5WI` | `P_3WKN2W6B5Q` |
| Outcome | `N_DH2AYPUMUT` | `N_WBXQVETJ2Z` | `N_Y5WICSSO34` |
| Receipt | `R_3KI5HYYQOV` | `R_O34TYI56X2` | `R_V757K553V2` |

This is a persistent multi-field failure on an already incorrect record,
not a new loss of a previously successful source-3 recall. No repair cell
introduces a newly wrong A2 field relative to its own parent.

The actual OFF_SELECTED routing traces consume this wrong source-3 block
twice. The source-2 task then reads correct source 2 and routes correctly.
The source-3 task also reads source 2 but chooses `P_ONQCERJ5LE`, instead of
the target `P_FWMNJO5UYN`, and ends `wrong_outcome`. Thus the observed 3/4
routing is compatible with one persistent bad tuple; correct fallback
behavior on the other task does not validate the bad tuple.

## Older recall: partial regression, not whole-fact erasure

Both parents, both SFT cells and OFF_UNIFORM retain all eight old full targets
at W0 and W8. OFF_SELECTED's sole failing old record is zero-based index 4,
`E_24YAGJH7YH`; the other seven remain exact.

| Field | Expected | OFF_SELECTED W0 | OFF_SELECTED W8 |
| --- | --- | --- | --- |
| EVENT | `E_24YAGJH7YH` | correct | correct |
| Node | `N_L5AIZBYJCX` | correct | correct |
| Port | `P_TRD5MMZOCT` | correct | `P_TRD5MMZO53` |
| Outcome | `N_ODP6OY5I6Z` | correct | correct |
| Receipt | `R_FVUUONBAPF` | `R_V5SVO/1CZQ` | `R_V57YJ2S57H` |

W0 preserves the complete node/port/outcome tuple, but loses its exact
receipt. W8 additionally loses the exact port, while preserving node and
outcome. The slash-containing W0 receipt is corruption **inside an opaque
identifier**, not harmless prose or trailing whitespace. Both strict scores
remain 7/8. Retaining 80 rehearsal rows does not guarantee exact retention,
but this example does not support “the entire old fact was forgotten.”

## Actual-reader decisions: false positives versus invalid pointers

The following counts are context from the captured actual-audit summaries;
the new work is their error/field decomposition.

| Cell | Correct / calls | Accurate replies: correct / calls | Faulty replies: correct / calls | Admitted choices |
| --- | --- | --- | --- | --- |
| SFT_SELECTED | 6/6 | 6/6 | 0/0, absent | `[]` |
| SFT_UNIFORM | 6/6 | 6/6 | 0/0, absent | `[]` |
| OFF_SELECTED | 4/7 | 4/5 | 0/2 | `[1]` |
| OFF_UNIFORM | 5/6 | 5/6 | 0/0, absent | `[1]` |

Both SFT cells and OFF_UNIFORM query sources `[0,0,1,3,2,3]` in audit order.
OFF_SELECTED queries `[0,0,1,3,2,3,2]`. Repeated calls remain separate; the
two OFF_SELECTED fault calls concern one source, not two independent facts.

**Source 1 false positive, both OFF cells (case 2).** The actual reader
returns every expected field for `E_VEEAOY3IIH`. Expected auditor output is
`NONE`; actual output is `E_VEEAOY3IIH\n`. This is a syntactically valid,
source-admitted pointer and a semantically wrong positive. It must not be
filtered away, rescued as a useful choice, or described as an invalid pointer.
Parent OFF had correctly selected this same source when its old reader reply
was faulty. Continuing to flag it after repair is consistent with inadequate
content-sensitive discrimination, but does not by itself prove a mechanism
such as memorized address preference.

**Source 3 unresolved faults, OFF_SELECTED (cases 3 and 5).** Both reader
replies have the four wrong body fields listed above. Expected output is
`E_DEX6OHDHJP`; actual output is literal `E_ID\n`. It is not an original
address, so both calls are wrong and unadmitted. Parent OFF emitted `E_id`
at the corresponding source-3 positions. Capitalization and LF changes do
not create an address or demonstrate correct semantic fault localization.
There is no authorized rule to infer or substitute source 3.

The previously faulty source-0/source-2 replies in OFF are now correct, and
their new `NONE` decisions are appropriate. Since the inputs changed, these
successful calls do not establish newly acquired detection of receipt faults.
Similarly, SFT's former source-2 node-only misses are not retested as faults
once that reader output is repaired. Three cells have no actual fault
denominator; zero selections in SFT therefore means correct abstention on
this all-accurate panel, not demonstrated fault-detection coverage.

## Fixed HELD: what is syntax, what is decision change?

All HELD stimuli remain identical to the corresponding parent's cases and
messages. These are explicit synthetic composites, not additional actual
reader outputs. Both SFT cells preserve all 16 strict successes.

Parent OFF has nine errors: three valid-pointer false positives, one `NONE`
false negative, and five malformed outputs. OFF_SELECTED has four errors:
three valid-pointer false positives and one malformed fault response.
OFF_UNIFORM has three: two valid-pointer false positives and the same
malformed fault response. The remaining exact failures are:

| HELD case | Requested source / skin | Truth | OFF_SELECTED raw | OFF_UNIFORM raw | Diagnosis |
| ---: | --- | --- | --- | --- | --- |
| 2 | 1 / 0 | true | `E_VEEAOY3IIH\n` | `E_VEEAOY3IIH\n` | false positive on an intact record |
| 7 | 3 / 0 | fault | `E_ID_E_DEX6OHDHJP\n` | `E_ID_E_DEX6OHDHJP\n` | invalid pointer; strict fault failure |
| 10 | 1 / 1 | true | `E_VEEAOY3IIH\n` | `E_VEEAOY3IIH\n` | false positive on an intact record |
| 12 | 2 / 1 | true | `E_QQ43NOEYBQ\n` | `NONE` (correct) | additional SELECTED false positive |

The case-7 fault preserves requested EVENT 3 but substitutes source 0's
node/port/outcome/receipt. All four body fields differ. The output visibly
contains the expected address, but its extra `E_ID_` prefix makes it
inadmissible; **no substring salvage** is allowed. The other skin of this
same composite, case 15, produces the correct bare address in both OFF
cells. This is a remaining phrasing-sensitive failure, not proof that either
cell reliably handles the underlying fault independent of presentation.

Matched-input improvements from parent OFF:

- **Case 1:** `E_id: E_43DKZR6D3S` becomes `E_43DKZR6D3S\n` in both cells.
  The earlier output already contained the exact address but invalid framing.
  This observable gain can be explained by format repair; parent strict
  failure remains a failure, with no retroactive admission.
- **Case 3:** `NONE` becomes `E_VEEAOY3IIH\n` in both cells on the same faulty
  input. This is a genuine change from the wrong decision to the right one,
  not merely deletion of an output prefix.
- **Cases 4, 5 and 15:** generic `E_id` becomes, respectively, `NONE`,
  `E_QQ43NOEYBQ\n`, and `E_DEX6OHDHJP\n`, in both cells. These are strict
  invalid-to-correct gains. The old generic placeholder does not identify a
  latent correct decision, so they cannot all be labeled “format only.”
- **Case 12, UNIFORM only:** `E_QQ43NOEYBQ` becomes `NONE` on the identical
  true input, removing a genuine false positive. SELECTED retains the wrong
  decision, merely adding an allowed LF.

These five SELECTED and six UNIFORM gains explain the reported 7/16 to
12/16 and 13/16 changes; neither repair cell loses a parent HELD success.
The remaining source-1 false positives occur under both HELD skins and in
the actual audit, making the residual problem more than output grammar.
However, HELD case 2 and the actual source-1 case use the same accurate tuple
and neutral task wording, so this recurrence is not an independent
generalization test. No repeated-case evidence is treated as new sampling.

## Interpretation boundaries and handoff

The prospective repair design supplies the same 62 successful audit-lesson
rows to all four cells, including the formerly loss-off children. Improved
OFF classifier scores therefore occur **with new common audit supervision**;
they do not demonstrate that original parenting had no effect. SELECTED
versus UNIFORM is the within-state material comparison. Across-state
SELECTED comparisons mix different initial weights with different selection
sets, and this sidecar does not identify a causal selection-policy effect.

All full-target recall changes examined involve real identifier changes,
not merely nicer answer formatting. Classification changes are mixed:
some repair invalid framing, some reverse wrong valid decisions, and some
remain malformed or valid-but-wrong. These distinctions leave every strict
score and every native source-admission result unchanged.

Formal SFT classifier retention is intact here, alongside repaired recent
memory. OFF_SELECTED still combines a recent multi-field gap with an older
partial regression and unresolved actual fault decisions. OFF_UNIFORM
restores recall but retains false-positive audit behavior. None of these
results warrants a broad readiness, H2 interaction, replication, or
statistical-generalization claim. Main's subsequent work is not gated on
this memo.

Exact hashes of the new diagnostic outputs:

| File in owned fieldcapture directory | Bytes | SHA-256 |
| --- | ---: | --- |
| `field_analysis.json` | 311576 | `13ef7b4fd449c53898b5f69847a7f54c1a42c4e079bf2d72656c03fc62fa7fdc` |
| `local_field_inputs.json` | 6217 | `4d0c3abd3e7251268b7af966c21a2e49da5a5cb736d47a50e3e4c21bbb38d8ea` |

The input manifest provides full SHA-256 hashes for the bounded local inputs,
not a claim about Main's complete archive or adapter verification. A separate
`field_analysis_completion.json` receipt binds this memo and the diagnostic
outputs and records the final unchanged-input check.

# Microloop FINAL_LF_ONLY: first terminal result

Read-only terminal analysis, 2026-09-14; evidence inspected through 08:11 UTC.
Pipeline completion marker: **2026-09-14T08:04:16Z**. This note does not revise
the original strict scores, training selector, collection, or readout outputs.
Action-content counts below are explicitly **post-hoc diagnostics**, not passes.

## Preservation and evidence

Local preservation root:
`gpu_artifacts_local/astra_microloop_lf_first_result_20260914/`.

Under that root, `astra_microloop_20260914_attempt2/collection/` is the original
collection (alias **C**), and `astra_microloop_lf_20260914_attempt1/` is the
complete terminal pipeline root (alias **R**). Copied from the corresponding
`/tmp/` paths on node2 using the existing SSH wrapper. One archive stream copied
both scopes, including the saved adapter, raw per-call and aggregate records,
compiled rows, masks, losses, requests, results, CPU admission, and launch logs.
No base model or checkout/source tree was transferred. Run-local launch scripts
were retained as existing evidence; no code was executed from the copied run.

**83 source files, 81,081,102 bytes; all 83 SHA256 checks passed.**
`SOURCE_SHA256SUMS` records hashes computed on node2 before transfer;
`TRANSFER_VERIFY.txt` records verification of the local copies. The adapter
tensor file is 80,792,096 bytes. It is a PEFT adapter, not an optimizer-resume
checkpoint. `ANALYSIS_RECEIPT.json` records this analysis separately from originals.

Selected SHA256 identifiers (full inventory in `SOURCE_SHA256SUMS`):

| Artifact | SHA256 |
|---|---|
| C/RESULT.json | `9a17d0ae568972523366060933e6c82cb9fce422298bafe97fef46be42d5461d` |
| R/BASE/RESULT.json | `5d55b8b528eb0043d802781b1756e6cb94d6c054e59b63b330c072e04796480b` |
| R/sleep/RESULT.json | `c42010e12efed8a06c1e98901f09d576cf0c568175e837fa66255138e3c8a40f` |
| R/FITTED/RESULT.json | `e3be5f6dd3fa5ed86b52eb810316c3dee7315d1ffe42e16b966f793d3dc2aa3b` |
| R/sleep/adapter/adapter_model.safetensors | `8597605e7e07b882f613e359decee0193275d4bd16eacac8cd5c45db75f25788` |
| SOURCE_SHA256SUMS | `2e8ffeb880358e2a6ea0dfc14aad705d2c788d43ca95d9f730a62fdeb77f9c03` |

## Collection and write condition

`C/EPISODES.json` contains four actual EXPLORE generations and four actual EVENT
generations, with public messages, receipt observations, raw text, generated token
IDs, and termination flags. The offered actions match all four facts. EVENT
trailing-LF counts in bank order are **[2, 0, 2, 2]**; original `accepted` is false
for every episode and `C/RESULT.json` remains **0/4 accepted, no fit**.

A read-only comparison confirms each EVENT equals its observed fact after only
`raw.rstrip('\n') + '\n'`; no identifier, field, or other whitespace changes are
needed. Actual receipt text is present in each EVENT-generation conversation.
The successor's 32 compiled rows match these four source raws under
`FINAL_LF_ONLY`, eight W0–W7 wrappers per fact, with verified source and target
hashes. This is the prospectively labeled compiler condition, not retroactive
strict acceptance or a second collection. Readout EVENT expectations are likewise
canonical; generated readout text itself was not repaired.

`R/sleep/RESULT.json` records 200 updates, 800 presentations (200 per event),
39,800 supervised tokens, and unchanged frozen base. BASE and FITTED each made
24 calls in separate fresh processes; the fitted process loaded the saved
adapter. Both result records report frozen base unchanged. This analysis reads
those receipts; it does not independently load or verify model tensors.

## Results: strict versus post-hoc content

Source: `R/{BASE,FITTED}/RESULT.json`, `READOUT.json`, and matching `CALL_*.json`.
All 48 readout calls are terminal and nontruncated.

| Panel | Original strict BASE → FITTED | Post-hoc correct port BASE → FITTED |
|---|---:|---:|
| Recall W0 | 0/4 → 4/4 | Not an action panel |
| Recall W8 | 0/4 → 4/4 | Not an action panel |
| Native action, no supplied memory | 0/4 → 0/4 | 2/4 → 2/4 |
| Supplied addresses, actual own-read text | 0/4 → 0/4 | 2/4 → 4/4 |
| Exact-facts ceiling condition | 0/4 → 0/4 | 3/4 → 3/4 |
| Unseen-address MISS | 4/4 → 0/4 | Not an action panel |

Post-hoc action method: require raw text to match `ROUTE P_[A-Z2-7]{10}` with
no LF, then compare `raw + '\n'` to that call's recorded expected action.
Every one of the 24 action outputs lacks the required final LF. This explains
why even correct port choices fail strict scoring; it does **not** explain wrong
ports. Eight action outputs also choose the wrong port (5 BASE, 3 FITTED).
No saved `correct` value or original file was changed.

## Goal pairs, ordering, and labels

Bank order and correct actions (from `C/BANK.json`):

| Fact | World | GOAL | Correct port | Event |
|---|---|---|---|---|
| F0 | W_KJHE2LO2BC | N_PZO6QGCFYQ | P_GBV7TYNMYX | E_W76IFWI75T |
| F1 | W_KJHE2LO2BC | N_XKJMA6ROET | P_LRZJ7WQPLZ | E_CHYIWYDY6Y |
| F2 | W_CSUZOJNSRH | N_CMZXILYYFI | P_STMW7CXQGK | E_X3YBAILZSM |
| F3 | W_CSUZOJNSRH | N_FHOFB66WSI | P_IW6NBDXQPN | E_QAQ5WQZQRH |

Within each phase and each action condition, the paired public conversations are
byte-identical except for the **GOAL line**. Both ports and both addresses keep
the same display order within a pair. Correct port display positions across
F0–F3 are 0,1,1,0. Supplied memory is also fixed within each goal pair.

Actual native outputs do not switch ports with either goal swap: BASE chooses
F0's port for both first-world tasks and F2's port for both second-world tasks;
FITTED chooses F1's port for both first-world tasks and F2's port for both
second-world tasks. Equal 2/4 totals conceal a changed first-world preference,
not correct counterfactual selection. FITTED supplied-own-read outputs select
F0,F1,F2,F3's ports respectively, switching correctly on both goal pairs.

However, supplied-own-read versus ceiling is **not a matched ceiling contrast**:

- Own-read uses actual W8 outputs, concatenated in `public_events` order:
  **F1,F0** in world 0 and **F3,F2** in world 1. Label:
  `ACTUAL MODEL-READ TEXT`. FITTED has a blank line between EVENT rows because
  the preserved generation already ends with LF and the join adds another LF.
  BASE instead supplies `MISS\nMISS` in each world.
- Ceiling uses canonical source EVENTs in **bank order F0,F1 / F2,F3**. Label:
  `EXACT-FACTS CEILING`. It has adjacent EVENT lines with no blank separator.
- FITTED supplies the same exact fact set in both conditions, but order, label,
  and separator differ. The ceiling fails F3 in both phases: actual output
  `ROUTE P_STMW7CXQGK` instead of `ROUTE P_IW6NBDXQPN\n`
  (`R/{BASE,FITTED}/CALL_019.json`). FITTED own-read succeeds on F3's port
  content (`CALL_018.json`), still missing LF.

The 4/4 versus 3/4 content contrast cannot establish an own-memory advantage,
a causal ordering effect, or a directly comparable ceiling. These prompt
differences were observed, not experimentally isolated.

## Unseen-address failure is substantive

BASE emits exact `MISS` on all four unseen-address queries. FITTED instead emits
the following raw strings (JSON-style `\n` denotes the actual final LF), in
`R/FITTED/CALL_020.json` through `CALL_023.json`:

```text
EVENT E_4FVJF7U3EX AT N_KGA6B2GC43 DID P_IW6NBDXQPN GOT N_CMZXILYYFI EVIDENCE R_QKW7UDYZ1I\n
EVENT E_7YNFHGAESL AT N_KGA6B2GC43 DID P_STMW7QGCFB3 GOT N_E64C4RCI674 EVIDENCE R_4B6FCXUDO32\n
EVENT E_RKYD4WTET6 AT N_FEKWBHXIER DID P_LRZJ7WQPLZ GOT N_XKJMA6ROET EVIDENCE R_3CHIKVFZ4I\n
EVENT E_IITJSZYBOH AT N_KGA6B2GC43 DID P_LRZJ7WQPLZ GOT N_CMZXILYYFI EVIDENCE R_QKW3WN5GTY\n
```

All four claim unsourced EVENTs at untrained addresses. The first also mismatches
a trained port/outcome pair and invents a receipt containing `1`, outside the
base32 ID grammar. The second invents IDs with invalid lengths/characters. The
last two pass EVENT wire syntax but remain false memories: the third combines
F1's transition with F0's receipt; the fourth combines world 1's source/outcome
with world 0's port and an unobserved receipt. Thus MISS collapse is not another
final-LF-only scoring issue. It includes confabulated associations and identifiers.

## Bounded interpretation

This is a completed **own-event write and actual choice readout**, not a completed
ongoing-learning loop. One small bank, one master, one bounded write, and fresh
readouts show exact stored-fact recall plus successful goal-dependent port content
when actual recalled facts are externally supplied. W8 tests a new wrapper over
the same four facts, not new fact acquisition. Native helper-free choice remains
2/4 by content and fails both goal-swap pairs; all actions remain strict failures.
Unseen-address abstention regresses from 4/4 to 0/4.

World construction, singleton exploration opportunities, addresses, sleep timing,
replay distribution, and serializer are researcher-authored/exogenous DEV choices.
The model did produce the explored actions and receipt-grounded EVENT fields;
it did not choose an endogenous exploration curriculum or learn a general sleep
compiler. Supplied-address reading and injected read text are external assistance.
No autonomous parenting, causal proof, general retention, improved future learning,
H1/H2 success, or qualified lineage is established. No next release or gate is
selected here; Main owns that decision. Analysis performed no model/tokenizer
load, fit, GPU work, code/notebook changes, or commit.

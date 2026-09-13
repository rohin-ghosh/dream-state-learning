# EVENT-only importer/writer independent review — 2026-09-13

**Disposition: advisory, non-blocking. No concrete target-selection, lineage, schedule, or numerical-dispatch defect found in the reviewed frozen implementation.** This is source review, not execution qualification, native custody verification, or permission to make scientific claims. Formal C11/future confirmation infrastructure is outside scope.

## Evidence inspected

Scope: `research_notes/astra_memos/ASTRA_PCFL_EVENT_ONLY_SCOPE_2026-09-13.md`. Publication/API/test evidence: `/tmp/astra_pcfl_event_only_implementation_handoff_20260913.md`, now EDITSTOP. Current source/test SHA256 values match all four published hashes:

| File | SHA256 |
| --- | --- |
| `gpu/astra_pcfl_event_prefix_import.py` | `7f12702dffd10d78fae1d115b0bfb6fcf4f993ef8de70c312e47ff6abfa9f88f` |
| `organism_v6/pcfl_event_only_train.py` | `24faf066d22bd15361cd8fe95a40033a3011307cebb6ea94dad05c29aadf04e2` |
| `tests/test_astra_pcfl_event_prefix_import.py` | `f20488c8a38702348fa491ada443be6598240e0c6c7265be0b5f087f724c88bb` |
| `tests/test_pcfl_event_only_train.py` | `73fcce19ae7743cefe4109a22ffe6dcae5e906090360ec9deeb6b018088f5d55` |

Also inspected the existing numerical writer's lineage, schedule, encoder, fresh-base initialization, optimizer loop and completion path. No tests, tokenizer, model, native replay, GPU or remote commands were run. No native output/archive contents were opened for this review. No repository files were edited. The reported 26 tests PASS / 7.945s and structural smoke are Parfit's handoff evidence, not independently reproduced results.

## Bounded findings

### Low — caller scope binding is not verified against authority bytes

`pcfl_event_only_train.py:103` validates `authority_sha256` as a SHA256-shaped string only. Unlike the fixed original evidence and reconstructed schedule, it does not compare this field to the adopted scope file. A syntactically valid arbitrary authority hash can therefore survive `build_fit`; the handoff explicitly describes its structural smoke's synthetic authority hash.

Smallest correction: Main's preparation binds the actual adopted scope FILE hash and compares it to `fit.binding.authority_sha256`. Do not treat `validate_fit` as proof of authorization. This is a caller integration obligation, not a reason to add a general authority gate or block the excluded-root component diagnostic.

### Low — successful tokenizer verification receipt is not automatically persisted by train_fit

`pcfl_event_only_train.py:122–138` invokes `prefix.verify_tokenizer` before encoding/model dispatch, but discards its returned sealed receipt. The shared loop saves the earlier validation dictionary, whose `tokenizer_check_required_before_fit` remains true. This does NOT bypass tokenizer validation: failures propagate before the base factory. It does mean the ordinary saved fit artifacts do not include that positive standalone receipt.

Smallest correction: use the already documented integration API to persist `verify_tokenizer(imported, actual_local_tokenizer)` and bind its file hash/seal in Main's immutable preparation evidence. No worker edit is necessary. Do not interpret the unchanged pending import status as a failed check, or promote it to verified without that evidence.

No additional worker repair is requested. Main's original-v3 replay receipt likewise remains an external execution fact: the importer verifies its exact fields and canonical seal, not who executed it. The handoff already correctly requires the independent receipt FILE hash separately from its body seal. Preserve that distinction; no new signature/guard system is requested.

## Checked implementation boundaries

- Importer lines 83–163 pin the original archive, immutable files/source paths, all 17 capture sets and failed report/outer evidence. Lines 179–223 replay only the first 16 calls, reconstruct public history, actual world transitions/issued receipts and exact EVENT admission. The rejected LINK stays evidence, not a training row. Fixed hashes and reconstruction prevent accepting an alternate prefix merely by resealing it.
- The original FORMATION_FAILED, rc1, 17 calls, zero fits/updates, null writer payload and false custody/full-contract flags remain intact. Resource-release observations do not turn failure into full-bank completion. No original full-contract validation path is relaxed.
- Tokenizer verification checks pinned files/template, all 16 rendered prompts, explicit/template tokenization agreement and exact output-token decode including LF. First cold generation is checked against load.ready_at; operation start is not incorrectly required to follow cold load.
- Eight admitted EVENT rows materialize the fixed 14-query digest. Targets come from the actual admission/materialization path, not ideal rows. The writer reconstructs 14 originals plus six deterministic authentic replay slots, support-disjoint groups, W0–W7 only, five epochs and 200 updates. New source pins include the native helper. Base/seeds/environment/tokenizer are pinned to the original manifest binding.
- `encode_fit` uses the unchanged target-plus-EOS/context-mask encoder with zero truncation. `train_fit` uses the existing numerical loop, not a copy: fresh-base tensor hash, no warm adapter, frozen bf16 base, new rank8/alpha16/dropout .05 LoRA, LOW3e-5, fresh optimizer and all 200 updates before saved completion.
- Read roster is 14 sorted requests at W0 then the same 14 at W8: 28 per arm, 56 total. Constants match service14/14, AUTH W8 strict_stop>=13/14, C0<=1/14, difference>=12/14. These modules declare the endpoint; they do not execute/reduce readout or prove cold-arm completion. Main must use this roster rather than the older 17-address/153-call roster and preserve missing-arm failure rather than zero-fill.

## Test and claim limits

The tests explicitly use archived evidence and simulated replay/tokenizer fixtures; the numerical-dispatch test mocks `_train_encoded`. They establish structural/masking/dispatch regressions as reported, not a new real tokenizer qualification or EVENT-only 200-update/save/reload numerical run. The tests also require the fixed local archive path, so a source-only copy is not sufficient to reproduce that suite. Do not describe these fixtures as wholly synthetic or as native execution evidence; no additional numerical run is demanded by this review.

Only the fixed retrospectively selected, externally format-assisted own-EVENT prefix acquisition question is in scope: one life/root/fit, eight EVENTs, trained facts/addresses, W0 diagnostic and W8 held wrapper. No autonomous discovery, LINK composition, selectivity, preservation, generalization, clean-lineage, H1/H2/C11, or compute-matched no-write claim follows. Original full-bank failure and its unavailable 17-address endpoint remain unchanged.

**EDITSTOP — review artifact only. Main retains native replay, preparation, fit/readout, completion and release responsibilities.**

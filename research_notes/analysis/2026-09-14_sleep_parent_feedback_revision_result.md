# Parent-feedback sleep revision: exact records, whole candidate rejected

2026-09-14. Independent bounded read-only audit of node2 `/tmp/astra_adult_cycle2_20260914_attempt1/CUE_REPLAY/recollect_revision` (**R** below), its cited rehearsal source and necessary collection records. Only this memo is written. No model/tokenizer loads, GPU calls, fit, remote change, target repair or custody expansion.

## Disposition

**REJECTED WHOLE; retain NO_FIT.** All four generated EVENT lines exactly reproduce the corresponding actual public records, including event addresses and EVIDENCE receipts. However, **0/4 lines have the required W citations**, and the final `NONE` conflicts with the explicit supported-note-or-NONE-alone instruction. Correct receipt identifiers are factual provenance but do not satisfy the requested W-label citation format. This is an admission/instruction-following failure, **not fabricated transition content**.

Repetition was explicitly permitted: EVENT format alone is not a rejection reason. The revision removes the prior uncited prose opening and ambiguous travel bridges, but does not meet the remaining citation and exclusive-abstention requirements. Four accurate subrecords cannot be salvaged as an admitted whole note under this contract. No stripping NONE, attaching W labels, canonicalizing, or compiling a repaired target is authorized by this audit.

## Exact raw output and source grounding

The following is the entire output, with LF between lines and **no LF after final NONE**:

```text
EVENT E_43DKZR6D3S AT N_NQ7SZP2WK3 DID P_MLFJXQ3WZH GOT N_WBXQVETNWG EVIDENCE R_V75J4A4RYG
EVENT E_VEEAOY3IIH AT N_NQ7SZP2WK3 DID P_X3KIPDIW4F GOT N_6AUMRWYCVK EVIDENCE R_YJNOWTRK53
EVENT E_QQ43NOEYBQ AT N_IRD6ZSHY2B DID P_ONQCERJ5LE GOT N_ZXFXLP2ESD EVIDENCE R_6MJCDE77X2
EVENT E_DEX6OHDHJP AT N_IRD6ZSHY2B DID P_FWMNJO5UYN GOT N_DH2AYPUMUT EVIDENCE R_3KI5HYYQOV
NONE
```

For each W1–W4, I compared the output line to the captured child EVENT and independently inspected the public EXPLORE action, RECEIPT source/port/outcome/receipt ID, and offered EVENT address. All identifiers agree. No hidden bank outcome is needed to establish this match. The four lines occur in original transcript order, without new interepisode movement assertions.

Fixed counts: **1/1 terminal untruncated generations; 4/4 exact source EVENT lines; 4/4 covered episodes; 0/4 required W citations; 0/1 valid standalone abstentions; 0/1 admitted whole candidates; 0 fits.** The 41 whitespace-delimited words contain no demonstrated cross-episode synthesis beyond ordered record repetition. This is not evidence of useful extraction or learning.

## Exact prompt and actor binding

The captured NOTE `messages` equal `SLEEP_PROMPT.json`. Its four roles are `system,user,assistant,user`:

1. The unchanged rehearsal-allowed system, including “Cite the W episode labels supporting every factual statement.”
2. The unchanged four labelled public wake transcripts and rehearsal ending. Payload exactly reconstructs from collection public messages plus original child EVENTs; it is byte-identical to the prior recipes' payload.
3. The entire **unrepaired rejected rehearsal note**, exactly equal to the prior captured assistant output.
4. This exact parent feedback:

> Your whole note was rejected: the opening lacks W citations; “Next, I moved to” and “Then, I went to” imply unobserved interepisode travel; trailing NONE conflicts with a note. Regenerate the whole note. Cite every factual clause, distinguish transcript order from observed movement, and use either a supported note or NONE alone. Add no facts. Repetition is allowed.

Feedback bytes match the revision provenance and frozen source constant. All four prior rehearsal-file hashes and collection/collection-RESULT hashes in `SLEEP_REVISION_SOURCE.json` match actual remote bytes. REQUEST/RESULT arguments and runner hashes agree. This is parent-feedback-conditioned generation, **not parent-free recollection**; parent text is present in the prompt but is not trained.

The collecting A1 actor is `/tmp/astra_adult_cycle_20260914_attempt1/CUE_REPLAY/train/adapter`, not the later cycle2 fitted child. Loaded state matches both collection and rehearsal receipts:
`07ecf4c5d965db5ea2765482439db3de5e230d90e0d86a99876a9c4ce6109300`.
Initial/prior-adult training RESULT binding:
`3eaad009cc1546fa62209a1871b0b129140db485afc4676f057a93333faf8046`.
Expected initial adapter file hash in the request:
`7e6fe380553b20e23b63f5934199fb04a44388079ce3fcc68b0ccbb9e9602f26`.

Native receipt: `parental_revision_v1`, `RECOLLECTION_CAPTURED_NO_FIT`, `model_calls=1`, `fits=0`, `parent_present=true`, `terminal=true`, `truncated=false`, `training_admission=UNREVIEWED_NO_FIT`; no FAILED file. NOTE reports **1996 prompt tokens and 208 emitted token IDs**. Frozen source has one generation call with a 768-token ceiling, checks the full untruncated prefix, dispatches this phase separately from training, and checks adapter state unchanged after non-training phases. Native base-unchanged receipt is true. These are source/receipt checks, not a fresh tensor measurement or model rerun. Rejection here does not rewrite the native unreviewed-admission field.

## Source and file hashes

Frozen source: `e74ad52f5ff94aea043a03a79bc21e3e84420619`. `git show <commit>:gpu/astra_experienced_event_adult_cycle.py | sha256sum` matches the remote runner receipt. The pure recollection helper was inspected at that commit, not imported or executed.

| File / payload | SHA256 |
|---|---|
| R/SLEEP_REVISION_SOURCE.json | `9422b428b1d6a622581113538f1be0554c3c821c3e878ba452d2340229e09b07` |
| R/SLEEP_PROMPT.json | `c5d03c9425e4c7624b71666d9a95c429da035ed4dbef451460c8bcaac76ddc44` |
| R/SLEEP_NOTE.json | `2171a0f46f6f9e90d657beaa9647d1f386dcc314b1fd69f995502eac1c22e73b` |
| R/REQUEST.json | `870e86d597f281bed6e0b669e4be1e7bd7b23b554ccd364939f7839c0c998957` |
| R/RESULT.json | `2ee6c44dfbf5df771ca6d429e309d29cd8fcc290452504c8cf85018bb95e91d6` |
| Shared collection | `d5d9162827c5f621644d96791c751283b50cde954c30c9ac87e2ed9a273f55c5` |
| W1–W4 UTF-8 transcript payload | `de265370d4233da34da4f4247adc15ace832067c9fc35c56ded9abccd442a60e` |
| Parent feedback UTF-8 bytes | `8d67af9042cafc4a0a8c3000a1c93ba6db3c232fb2d1ffe70cb89e41a9ec4206` |
| Frozen native runner | `2634a0436055c91332a92eaeecf8d862ee42a76a5307dd0799c4bf2b4b46f39d` |
| Frozen recollection helper | `151b8a270baa8c3a5c1c2a0e470bbd9f2863a4e6bdcf05978b7cd28fcac92053` |

## Interpretation and release

The failed recipe is closed as training material. Exact copying demonstrates source-faithful reproduction here, not useful extraction. This single revision neither identifies why the broader note contract failed nor establishes incapacity to organize experience; learned format preference and visible transcript scaffolding are not isolated by this comparison. Original recipe1 remains valid abstention, and recipe2 remains a separately rejected candidate. No note has been admitted for fitting in these audits. This disposition does **not** gate Main's further useful no-fit diagnoses. Memo complete; scope released.

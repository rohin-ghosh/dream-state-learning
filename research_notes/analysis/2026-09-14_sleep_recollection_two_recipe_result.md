# Two sleep recipes: grounded subclauses, rejected rehearsal candidate

2026-09-14. Bounded read-only audit through `bash gpu/ovx_ssh.sh`; no model/tokenizer loads, GPU actions, fits, repairs or remote writes. Only this memo is created; no extra custody copy. Evidence root **R** is `/tmp/astra_adult_cycle2_20260914_attempt1/CUE_REPLAY`. Inspected `recollect` and `recollect_rehearsal` PROMPT/NOTE/RESULT/REQUEST plus the necessary `collect` records.

## Decision

**Recipe1 is valid abstention. Recipe2 contains four correctly cited transition triples, but its whole candidate is ineligible under the declared public-grounding/citation contract. Retain NO_FIT.** This is not a claim that the child cannot organize experience. Do not salvage four clauses, remove NONE, add citations or rewrite the narrative into training material in this audit.

| Captured result | Original recipe | Rehearsal-allowed recipe |
|---|---:|---:|
| Source runner binding | `a582c8d7` | `65506d54` |
| Calls / fits | 1 / 0 | 1 / 0 |
| Input / emitted token IDs | 1697 / 2 | 1735 / 171 |
| Terminal / truncated | true / false | true / false |
| Whitespace-delimited output words | 1 | 61 |
| Literal NONE abstention | 1/1 | 0/1 (note plus NONE) |
| Whole eligible note candidates | 0/1, abstained | 0/1, rejected |

Both native receipts say `RECOLLECTION_CAPTURED_NO_FIT`, `training_admission=UNREVIEWED_NO_FIT`, `parent_present=false` and `frozen_base_unchanged=true`. Rejection here is an analysis disposition, not a rewritten native receipt. Recipe1 lacks the later `sleep_recipe` field; its actual prompt establishes the original recipe.

## Public grounding: what passes and what does not

Recipe1 raw output is exactly `NONE`. Its system says “If nothing beyond repeating the records is supported, say NONE.” That allowed response provides no candidate organization to audit, and does not measure inability to rehearse.

Recipe2 raw output, unmodified:

> I explored the public route system and recorded my observations. I started at N_NQ7SZP2WK3 and used port P_MLFJXQ3WZH, which led to N_WBXQVETNWG (W1). Next, I moved to N_NQ7SZP2WK3 and used port P_X3KIPDIW4F, arriving at N_6AUMRWYCVK (W2). Then, I went to N_IRD6ZSHY2B and used port P_ONQCERJ5LE, reaching N_ZXFXLP2ESD (W3). Finally, I explored N_IRD6ZSHY2B with port P_FWMNJO5UYN, ending up at N_DH2AYPUMUT (W4). NONE

| Clause / span | Public evidence and disposition |
|---|---|
| Opening: explored and recorded observations | Supported in substance by public EXPLORE actions and EVENT commitments across W1–W4, **but uncited**. The recipe requires citations for every factual statement; this is a citation failure, not an invented experience. |
| W1: `N_NQ7SZP2WK3 → P_MLFJXQ3WZH → N_WBXQVETNWG` | Exact source/action/receipt match; cited correctly. “Started at” is supported within W1's offered source context, not a claim about an earlier journey. |
| W2: `N_NQ7SZP2WK3 → P_X3KIPDIW4F → N_6AUMRWYCVK` | Exact source/action/receipt match; cited correctly. |
| W3: `N_IRD6ZSHY2B → P_ONQCERJ5LE → N_ZXFXLP2ESD` | Exact source/action/receipt match; cited correctly. |
| W4: `N_IRD6ZSHY2B → P_FWMNJO5UYN → N_DH2AYPUMUT` | Exact source/action/receipt match; cited correctly. “Ending up” is supported as W4's outcome. |
| “Next, I moved to…” / “Then, I went to…” | Ordering W2 after W1 and W3 after W2 is supported by transcript order. **Movement between their contexts is not observed.** Four separately offered contexts do not establish travel from W1's destination back to W2's source, or from W2's destination to W3's source. These could be loose narrative transitions; nevertheless they are ambiguous/unsupported as interepisode movement and fail the strict whole-candidate rule. This does not demonstrate that such movement was impossible. |
| Final `NONE` | Inconsistent with a substantive supported note and the instructed abstention alternative. Not itself a fabricated transition; it is an output-contract inconsistency. |

Fixed subclause findings: **four grounded/correctly cited transition triples out of four; four cited episodes out of four; two ambiguous bridge spans; one uncited opening sentence; one trailing abstention marker.** These categories are not a contrived unified factual-clause denominator. Whole-candidate rejection follows even without resolving the bridge ambiguity because the opening lacks its required citation. No new cross-episode relation is established beyond chronological listing; faithful paraphrase is not demonstrated useful extraction.

## Same actor and actual-input checks

Both notes' captured `messages` exactly equal their saved PROMPT objects. Extracted W1–W4 transcript payloads are byte-identical between recipes and exactly reconstruct from each collection episode's four captured public messages plus raw child EVENT. The inspected public receipt lines, not hidden bank facts, support the four triples. No scoring flags or hidden outcomes are appended to that payload. Researcher-authored exploration/formation instructions remain visible: trace-supported posed rehearsal, not autonomous selection or a parent intervention.

Both loaded-adapter receipts equal the collecting child's state:
`07ecf4c5d965db5ea2765482439db3de5e230d90e0d86a99876a9c4ce6109300`.
Both bind initial/prior-adult training RESULT:
`3eaad009cc1546fa62209a1871b0b129140db485afc4676f057a93333faf8046`.
These are receipt comparisons, not fresh model reloads or weight measurements.

Changing the recipe produced a descriptive contrast from abstention to four grounded transition paraphrases with admission defects. The system and ending both changed, as did source version and input length; two single calls are **not an isolated causal test of the novelty clause**. Neither note was fitted or tested for downstream utility; no learning, retention, extraction benefit or controller improvement follows.

## Exact SHA256 receipts

Remote file bytes hashed with Python standard-library `hashlib.sha256`; no files were changed. Runner hashes also match `git show <revision>:gpu/astra_experienced_event_adult_cycle.py | sha256sum` for the two named source revisions.

| Path relative to R / payload | SHA256 |
|---|---|
| `collect/COLLECTION.json` | `d5d9162827c5f621644d96791c751283b50cde954c30c9ac87e2ed9a273f55c5` |
| Common W1–W4 UTF-8 payload, excluding outer prefix/ending | `de265370d4233da34da4f4247adc15ace832067c9fc35c56ded9abccd442a60e` |
| `recollect/SLEEP_PROMPT.json` | `093467bc8e066af9eb3df4ebd0541857fc4eed6f01b234a2c396aba0ef47c4ee` |
| `recollect/SLEEP_NOTE.json` | `6bbc9337a6300766d449bb9f67e7c4279e8eac4f1bdf38b9473f8f82e02fea7d` |
| `recollect/RESULT.json` | `c76534d0e3a00258c9027642a9666d1e0a5d19e4db3c31036e81f3fa9fe8e5de` |
| `recollect/REQUEST.json` | `4697b3d42c57e8d5036110b01ab1ff1fa4631f6eeb00ea9754ce379f4bdfb158` |
| `recollect_rehearsal/SLEEP_PROMPT.json` | `1552e07f97763f22847ddd47ab4cdec2a0851020e7e5fc50d08206a03a3ee7b5` |
| `recollect_rehearsal/SLEEP_NOTE.json` | `85fcc18faa9ec7bf883b65c5cd878a3f4a08ea3c951e45ba909638af329220d4` |
| `recollect_rehearsal/RESULT.json` | `edaa5d7845c4605555ebd525a21635ff8fcc8a3611e9ae6e3a00725f86be0b99` |
| `recollect_rehearsal/REQUEST.json` | `59498b11463883a2f963081b39bc930a23361f4107576a02a9ffdfa960b1ebd2` |
| Original runner | `029d771fdcba19ebd9e178fdcf41daef193a8fb7fe7ca6365c996c3855bfe50b` |
| Rehearsal runner | `fd6520ff37ae7756c1cefe4869fc3b1ff0863e8b01e274787a8cc89ac4154072` |

Scope finished and released. Main retains NO_FIT; no repaired target or follow-up generation is proposed here.

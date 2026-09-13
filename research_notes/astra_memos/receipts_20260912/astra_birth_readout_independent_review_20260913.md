# Initial birth raw review — PARTIAL terminal handoff / EDITSTOP

September 12, 2026, 18:23 PDT / September 13, 2026, 01:23 UTC.
Stopped at Main's request. **No approval or completed independent-review verdict.**
The existing script and JSON are unchanged; their formal frozen-result comparison
remains `PENDING_AFTER_COMPLETE_RAW_RECOUNT`. No further recount was run for this handoff.

## Completed work

- SHA256 verified both supplied capsules and the external readout validation;
  also verified the fit validation against the readout plan's bound hash.
- Independently checked all **814 readout + 39 fit archive member hashes**, the
  candidate hash, linked fit inputs, source/base/criteria joins, and recorded
  adapter identities. Archives were read in memory, not extracted.
- Recounted **all 384 raw outputs** using a new stdlib-only parser and public
  case inputs: belief/goal, expected/observed/prior action, sums and literals.
  No frozen scorer function was imported or executed. Reconstructed factor
  twin pairs from input differences and checked them against candidate pairs.
- Checked all raw call IDs, exact prompts/settings, loader identity receipts,
  request/response hashes, saved rendered prompts/input-token IDs, token bounds,
  sequential call timestamps, worker/spec joins and recorded successful cleanup.
- Derived registered thresholds and conjunction failures from the raw recount.
  Then inspected stored aggregate counts and selected raw failure rows manually;
  the **exhaustive automated frozen-result comparison was not completed**.

## Existing aggregate findings

Counts below use the assigned map (AUTH for OFF/AUTH, DERANGED for DERANGED).

| Cell | PROSPECT strict | REVISE strict | Belief / goal twins | Each revision twin family | Addition compliant | Copy compliant | 64-token limit |
|---|---:|---:|---:|---:|---:|---:|---:|
| OFF | 0/32 | 0/64 | 0/16 each | 0/32 | 8/16 | 8/16 | 96/128 |
| AUTH | 32/32 | 58/64 | 16/16 each | 26/32 | 15/16 | 16/16 | 0/128 |
| DERANGED | 32/32 | 56/64 | 16/16 each | 24/32 | 15/16 | 16/16 | 0/128 |

These headline counts agree with Main's summary and the inspected stored counts.
DERANGED scores **0/32 PROSPECT and 0/64 REVISE joint against AUTH truth**:
assigned-map success is not truthful-map success. Strict REVISE surface counts
are AUTH 64/64 and DERANGED 62/64; two DERANGED outputs name two NEXT actions.

**Registered conjunction: FAIL for both.** Each revision family requires 29/32;
addition requires 16/16 (95% rounded upward). AUTH meets the 58/64 REVISE floor
but fails all three revision twin floors and addition. DERANGED additionally
fails the REVISE floor. Copy, prospect, belief/goal twins, zero anchor tag spill
and the registered loss-from-OFF allowance pass. No thresholds were relaxed.

## Raw failure details already inspected

- AUTH REVISE failures: calls **0005, 0011, 0034, 0053, 0059, 0082**. All are
  template 2, truthful MATCH/KEEP cases with correct COMPARE and POLICY but
  wrong NEXT: the output chooses the first displayed action rather than the
  required prior action. Example 0005: prior wug, expected=observed=fep;
  raw `COMPARE: MATCH\nPOLICY: KEEP\nNEXT: dax`, required NEXT wug.
- DERANGED REVISE failures: **0007, 0009, 0030, 0032, 0055, 0057, 0078, 0080**.
  All are template 2, truthful mismatches assigned inverted MATCH/KEEP.
  Six give the wrong single NEXT; **0007 and 0055 emit
  `COMPARE: MATCH\nPOLICY: KEEP\nNEXT: dax, wug`**, not a unique next action.
  Repeated patterns across trial instances are not independent root replications.
- Both trained cells fail addition **0097**, `birth-r0-dev-addition-001`:
  public inputs **31+48=79**, raw **`ACT: 89`**. This is an arithmetic error,
  not just a formatting failure or token-limit event.
- OFF's 16 addition outputs all display the correct number on manual inspection;
  eight use ACT and eight use `<sum>` markup (two without a closing tag), hence
  only 8/16 protocol-compliant. This unregistered descriptive observation is
  **not** a replacement score. Trained 15/16 cannot be described as improved
  arithmetic over a numerically incapable baseline.
- OFF copy failures include `COPY: <literal>` and literal-containing wrappers;
  exact copy compliance remains 8/16. OFF's 96 length finishes are the entire
  conditional panel: explanatory prose consumed the 64-token budget. Do not
  infer absence of latent reasoning ability from that bounded output assay.

## Known parser/comparison gap — do not hide it

The unchanged independent parser **prefix-matches NEXT in the two dual-action
DERANGED rows**, recording NEXT=dax despite the trailing `, wug`. Their strict
and assigned-joint scores are still false, so the headline counts above are
unaffected. But its DERANGED AUTH-NEXT field count is **8**, versus frozen **6**;
that independent per-field count is not a valid unique-action count and should
not be used. No repair/recount was performed before this terminal handoff.

The independent parser also retains the visible correct assigned COMPARE/POLICY
tags on those malformed rows, reporting **64/64** each. The inspected frozen
scorer discards the whole fields object and reports **62/64** each. This is a
known parsing-granularity difference, not evidence that the malformed response
passes. An exhaustive row/field/stratum/twin/receipt comparison and final
discrepancy ledger remain unfinished. The JSON is a **partial review artifact**.

## Costs already checked

- Raw generation: **384 calls, 26,016 input tokens, 9,767 output tokens**,
  24,576 output-token ceiling; **322.931770 s** summed generation time.
- OFF/AUTH/DERANGED generation: **182.734200 / 70.348342 / 69.849228 s**;
  worker windows including cleanup: **321.661228 / 224.511399 / 221.379239 s**.
- Readout launch-to-release **949.620845 s**, including collection
  **37.153007 s**. Fit launch-to-release **488.560991 s**, including collection
  **38.730419 s**. Paired registered sum **1,438.181836 s**, below 5,100 s.
- First fit launch to final readout release is **1,569.818049 s**; the difference
  is the **131.636213 s** between fit release and readout launch. Do not label
  the phase sum as uninterrupted calendar elapsed time.
- Generation/load/training/worker/controller intervals are **nested, not added**
  to launch-to-release. Inspected training manifests report 128 steps, four
  epochs and zero nonfinite batches per arm, with 84.5/84.6 s train time;
  those are metadata observations, not an independent tensor/training audit.

## Trust and scientific limits

Reviewer authored the **downstream born-child readout helper**, not this original
birth runner or corpus. This is an independently implemented calculation, **not
a blinded review**: Main supplied expected counts and prior interface inspection
included scorer-related code. No native/model/tokenizer load, network, Git,
helper edits, launch or live-process action occurred in this review.

Hash/call matches establish local artifact consistency, not authenticated model
origin. Saved token/rendering matches are not independent tokenizer decoding;
full base/adapter tensors and remote final vacancy were not rechecked. The fit
metadata capsule does not supply adapter weights for a fresh tensor hash audit.
Successful remote closure is supported by the pinned receipts, not re-observed.

Finite controlled meaning: one authored root exhibits strong assigned conditional
mapping/format adherence in trained cells, including the inverted control, with
residual next-action and arithmetic failures and failed registered conjunctions.
It does **not** establish birth impact, durable general learning, an independent
holdout, clean ancestry, or L1/G3/P1/G5/H1/H2. Boundary:
**SOURCE_AUTHORED_BIRTH_NOT_CLEAN / UNRESOLVED_LOCAL_HASHES_ONLY**; exploratory only.

## Exact artifact hashes

```text
bd9c82ab7f113aa61e18a38271656b0fd8904fc30c749f9c3ba39b16b922ffca  /tmp/astra_birth_readout_independent_review_20260913.py
60a0adaad9158d1cfdd3ad8383c631f0cac28f7a4f1af6f616569b4a50847852  /tmp/astra_birth_readout_independent_review_20260913.json
07816cb0649255ddaec5377e0b2ab4442919ea806d2eb60243b0155f1dc96a2a  /tmp/astra_birth_readout_seed0_20260912_attempt1_capsule.tgz
4a47152320d9b78e16427c25858b9f8d37d2bb054d6db2fcda46128dd2a3a07b  /tmp/astra_birth_readout_seed0_20260912_attempt1_validation.json
d2460cb3be9b357ae1beecad84ae9bcfc7e76b61d296fb7b359ae9e68d8e2474  /tmp/astra_birth_fit_seed0_20260912_attempt1_capsule.tgz
d403b48b645dcc5ebd971a6527108f21287fd722981f128c8780c58a2f1cf770  /tmp/astra_birth_fit_seed0_20260912_attempt1_validation.json
```

**EDITSTOP — partial terminal handoff; no invented approval.**

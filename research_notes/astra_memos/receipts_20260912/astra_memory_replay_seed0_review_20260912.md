# Seed0 memory replay — raw review, EDIT-STOP

2026-09-12. **Raw recount/custody PASS; prospective progression FAIL. No seeds1/2 under this gate.** Main's reported counts and decision agree with this review.

**Authorship disclosure:** I authored the replay runner and collector. This is a separate raw reduction with independently written CPU checks, **not a fresh-author independent implementation audit**. I read128 new request/response pairs plus112 inherited calls (original dev48; SEQ105 root0 dev48/exact16), checking answers against original source records rather than taking summary scores as truth. Existing reducers/runner/collector were not invoked. Only this report was written; no GPU/model/network/Git/repository actions.

## Recount and progression

| Seed0 state | Dev memory | Exact-prefix memory | Correct ACT | PREDICT-before-ACT adherence |
|---|---:|---:|---:|---:|
| Original teach parent |4/16|Not recounted here|32/32|32/32|
| Inherited SEQ105 memory-only80 |14/16|14/16|0/32|0/32|
| **MIXED160,20 epochs** |**14/16**|**13/16**|**32/32**|**32/32**|
| **ALL_MEMORY160,40 epochs** |**16/16**|**16/16**|**0/32**|**0/32**|

Arithmetic expectations were independently recomputed from original source operands; memory labels came from the original device–color source records. All four new panels' row-level correctness/validity results agree with stored reductions. MIXED's32 arithmetic output strings are **byte-identical to the original parent's**. ALL_MEMORY emits no ACT or PREDICT declaration:19 arithmetic responses are `green`,10 `red`,3 `blue`. These are arithmetic-interface failures/color spill, not32 valid but numerically wrong sums.

The sealed root0 gate requires MIXED dev≥15/16, exact≥15/16, adherence≥30/32 and ACT≥31/32, plus both arms technically complete. Observed14,13,32,32 means **both memory conditions fail**; technical conditions pass. Both mandatory panels and the comparator ran despite this outcome. Do not substitute ALL_MEMORY's memory scores, pool panels, lower thresholds or launch roots1/2 selectively.

### Different mistakes on different prompt surfaces

| Device / source suffix | Source label | MIXED dev | MIXED exact |
|---|---|---|---|
|003|green|**yellow**|green|
|004|green|**yellow**|green|
|008|blue|blue|**yellow**|
|010|blue|blue|**yellow**|
|015|green|green|**blue**|

These are all five between-panel disagreements. MIXED's two dev errors and three exact errors are **disjoint**:11 facts are correct on both surfaces, five on only one, none wrong on both. ALL_MEMORY answers every fact correctly on both surfaces. Both panels concern the same16 learned facts; unlike wording does not introduce new facts or independent factual replication.

SEQ105's two errors were instead devices000/005, both yellow: dev answered green/blue; exact answered blue/green. MIXED fixes those two but introduces two different dev errors and three different exact errors; equal14/16 dev totals therefore conceal changed case outcomes. ALL_MEMORY fixes both without another memory error. Its arithmetic color distribution also changes from SEQ105's green16/blue16; the failed interface remains failed.

## Material, update and state accounting

| Arm | Original selected rows /epochs | New /cumulative updates | Native input /target per epoch | Input /target presentations |
|---|---:|---:|---:|---:|
| MIXED |32 /20|160 /240|1,654 /250|33,080 /5,000|
| ALL_MEMORY |16 /40|160 /240|704 /32|28,160 /1,280|

Verified full selected records, spans/meta/order and source IDs against the original80-row corpus. MIXED uses all16 memory rows plus the fixed first16 addition rows in original source order (`011,039,055,029,048,000,052,017,036,046,063,019,057,030,012,015`), preserving selected overall order. ALL_MEMORY is the unchanged original16-memory subset. Stored native row lengths/labels reproduce the original per-row receipts and nested-batch label hashes; memory masks remain42 ignored prefix tokens followed by color+EOS. No new tokenizer call was made.

Both fits have160 microbatches/updates, matching seed0, LR3e-4, rank8/alpha16/dropout.05, batch4/accum1, no packing/second chat wrapping, and EOS enabled. No skips, splits, truncation, empty fit or nonfinite batches. They fork **the same original80-step parent independently**, not each other or the damaged SEQ105 child. Fresh optimizer receipts show zero initial state, no restored/saved optimizer state, one adapter and frozen base.

Each arm's392 source tensor-inventory records equal its initialized records without dtype conversion; all392 final records differ, with unchanged shapes. Parent inventories before/after match the original pin; available physical adapter metadata hashes and both readout adapter bindings match fit inventories. **Weights are excluded from the capsule:** this independently checks stored native receipts/inventories, not a fresh tensor reload, base-freezing measurement or on-node immutability observation.

## Generation and reservation cost

All128 new requests retain temperature0, seed20260912 and cap64. **Zero length-capped calls; all finish `stop`.** Every memory response is one color token plus EOS. MIXED arithmetic uses14 output tokens on28 cases and12 on4; ALL_MEMORY arithmetic uses2 tokens each.

| Arm | Dev input/output tokens | Exact input/output tokens | Fit /dev /exact worker seconds |
|---|---:|---:|---:|
| MIXED |2,131 /472|672 /32|91.193 /155.246 /136.767|
| ALL_MEMORY |2,131 /96|672 /32|86.407 /138.512 /114.316|

New raw totals: **5,606 input tokens,632 output tokens**, versus8,192 output-token ceiling;31.504598529s summed request-to-response duration. Fit loops took50.2s and37.4s. These are different quantities from reserved device time.

All six supervision receipts report success/exit0/error-null and owned-group/GPU release. Their timestamps confirm sequential **MIXED fit→dev→exact, then ALL_MEMORY fit→dev→exact**. Worker sum722.441551507s; controller954.336828001s, within its1200s bound with140s cleanup reserve. Launch20:02:28.997513UTC → terminal20:18:23.380759UTC → observed full release **20:20:11.129284UTC**, September12,2026.

Full reservation is **1,062.131771s =17.702196183 A40-min**, below the90-minute envelope. Worker12.040692525min and controller15.905613800min are nested, **not additive**. Release interval was independently recomputed; XML shows an empty process list and the launch-bound GPU0 UUID. This is historical receipt/XML verification, not a live GPU check. No billed dollar cost or continuous GPU-busy measurement is established.

## Custody and claim limits

- Capsule SHA256: `2d4636e37a4668a6503e8ee7a021ed87b6479e54e8bf8126c82e7dcbbaa172e3`.
- Plan SHA256: `70405bfa50486feaa2b000ee8102a1cdf30265bccaf102958d7e3ea17035bbb9`.
- MIXED material SHA256: `ef1031d98f497c09f499e01d49a45afcb81c997bc9c1a68342145f87139ccc27`.
- ALL_MEMORY material SHA256: `758960c4bbfe1ae5328e30a25ebcf767f9d5ab9c3e968fe6c31e5470adca61fd`.

**331/331 hashes** agree across tar members, validation manifest and extracted files; no duplicate/link/traversal members. Checked all four raw-capture manifests, request/response value seals, prepared prefixes, reduction/terminal/fit bindings, release hashes and XML. Original parent provenance6 files and inherited dev readout inventory111 files match. Main's analysis was consulted after the separate raw recount, not used as its scoring input.

**Supported:** this root0 fixed-update allocation comparison shows complete measured memory recall with arithmetic-interface failure in ALL_MEMORY, versus preserved original arithmetic behavior but incomplete, surface-dependent memory recall in MIXED. It does **not** meet the predeclared joint progression criterion.

**Not isolated:** memory dose, token/compute cost or a unique interference mechanism. MIXED provides20 new exposures/fact; ALL_MEMORY40. SEQ105 memory-only80 supplies the equal20-exposure anchor but half the new updates and a different estimand. MIXED retains an original-parent behavior; it did not restore behavior from the SEQ105 child. Infer neither latent arithmetic-capacity erasure, necessary separate adapters, general G1/G3/P1/G5/H1/H2, other-seed/checkpoint outcomes nor new-fact generalization. No new OFF/HF/confirmation calls. **EDIT-STOP.**

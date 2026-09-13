# Parenting alignment — authorized local outcome handoff

Frozen reducer executed once successfully (exit 0), with no source changes, repair, retry, native work or recollection. Frozen gate remains failed; no promotion or writer authorization.

## All nine cells

P=PROCESS_USE, E=EXECUTED, F=RECORD_FAITHFUL, M=FULL_MATERIAL. All task denominators remain 16, including uncalled records. Masks run left-to-right task_index 0–15 in each seed’s manifest schedule; all three arms share that seed’s task order. Task IDs and complete paired rows remain in analysis.json.

|Seed|Arm|RESTATE /4|P/E/F/M /16|Execution mask|Restate mask|Calls|
|---|---|---|---|---|---|---|
|0|ALIGNED|0|0/16/0/0|`1111111111111111`|`0000`|36|
|0|SWAPPED|0|0/13/0/0|`1111111111110100`|`0000`|33|
|0|NO_PARENT|N/A|0/16/0/0|`1111111111111111`|`N/A`|32|
|1|ALIGNED|0|0/16/0/0|`1111111111111111`|`0000`|36|
|1|SWAPPED|0|0/15/0/0|`1111111101111111`|`0000`|35|
|1|NO_PARENT|N/A|0/16/0/0|`1111111111111111`|`N/A`|32|
|2|ALIGNED|2|0/16/0/0|`1111111111111111`|`0101`|36|
|2|SWAPPED|2|0/14/0/0|`1111110111111011`|`1010`|34|
|2|NO_PARENT|N/A|0/15/0/0|`1111111111111110`|`N/A`|31|

P, F and M masks are each `0000000000000000` in every cell. ALIGNED−SWAPPED and ALIGNED−NO_PARENT are 0 for P/F/M in every seed; execution differences are +3/+1/+2 versus SWAPPED and 0/0/+1 versus NO_PARENT. These are paired descriptive task counts, not independent learner replication.

## Exact feasibility screen

|Component|Seed0/1/2 mask|Cohort requirement passes|
|---|---|---|
|anchor_advantage|`000`|False|
|anchor_no_large_harm|`111`|True|
|faithful_material|`000`|False|
|repeated_activation|`111`|True|
|restatement|`000`|False|
|swapped_advantage|`000`|False|
|swapped_no_large_harm|`111`|True|

Conjunction **false**. Repeated activation passes only because 0 second-half successes >= 0 first-half successes in all roots; no evidence of improvement. No-large-harm passes on zero differences. ALIGNED restate 0/0/2 falls below 3/4 in all roots. Current frozen anchor lower bound is correctly >=−2; the pre-execution concern remains documented in the unchanged original handoff.

## Schema versus required bindings

All 144 wake notes fail normalization: 143 unknown/conflicting alias errors and one absent/unparsed note after malformed wake JSON. All 137 called record sources fail normalization. Consequently zero source-note cases have schema-valid required-field assessments: empty binding_errors is **not** evidence that bindings were correct, and field_correct=false under failed normalization is **not** evidence that raw required values were wrong. No broader normalizer or replacement endpoint was used.

|Seed|Arm|Called records|Source object-required / unknown-alias|Outer record schema failures|Record JSON parse failures|Own event all five fields correct|
|---|---|---|---|---|---|---|
|0|ALIGNED|16|15 / 1|16|1|10|
|0|SWAPPED|13|12 / 1|13|1|11|
|0|NO_PARENT|16|16 / 0|16|0|6|
|1|ALIGNED|16|12 / 4|8|4|9|
|1|SWAPPED|15|12 / 3|6|3|11|
|1|NO_PARENT|16|16 / 0|0|0|0|
|2|ALIGNED|16|12 / 4|16|0|6|
|2|SWAPPED|14|11 / 3|13|0|4|
|2|NO_PARENT|15|3 / 12|13|1|4|

Own-event field checks are the frozen scorer’s existing checks against the actual new child receipt, not public receipt targets and not a new success endpoint. The following counts separate absent/unparsed expected event fields from present but incorrect values/types. They must not be summed into a causal cohort estimate.

|Seed|Arm|Absent/unparsed event fields|Present incorrect event fields|
|---|---|---|---|
|0|ALIGNED|`{"observed": 1, "predicted": 1, "receipt_id": 1, "relation": 4, "try": 1}`|`{"relation": 2}`|
|0|SWAPPED|`{"observed": 1, "predicted": 1, "receipt_id": 1, "relation": 2, "try": 1}`|`{}`|
|0|NO_PARENT|`{"receipt_id": 4}`|`{"relation": 6}`|
|1|ALIGNED|`{"observed": 4, "predicted": 4, "receipt_id": 4, "relation": 4, "try": 4}`|`{"relation": 3}`|
|1|SWAPPED|`{"observed": 4, "predicted": 4, "receipt_id": 4, "relation": 4, "try": 4}`|`{}`|
|1|NO_PARENT|`{}`|`{"relation": 16}`|
|2|ALIGNED|`{"observed": 9, "predicted": 9, "receipt_id": 9, "relation": 9, "try": 9}`|`{"relation": 1}`|
|2|SWAPPED|`{"observed": 7, "predicted": 7, "receipt_id": 7, "relation": 8, "try": 7}`|`{"relation": 2}`|
|2|NO_PARENT|`{"observed": 2, "predicted": 2, "receipt_id": 2, "relation": 9, "try": 2}`|`{"relation": 2}`|

All305 calls terminate stop, not length. Of144 wakes,137 are format-valid but noncanonical and7 fail: six SWAPPED wakes have null fresh-action predictions (seed0 indices12,14,15; seed1 index8; seed2 indices6,13), and seed2 NO_PARENT index15 has malformed JSON. Their7 record calls remain uncalled, not retried or discarded. Only2 records are format-valid/noncanonical (seed2 NO_PARENT), still failing source requirements; no canonical wake or record passes.

### Qualitative examples — not a permissive rescore

- Seed2 ALIGNED task_index4, `pa-4c32836e93079f2891fa5be5402e` (C): wake note contains the latest public receipt ID `pa-a6042cdea704347c4d48da5b5077`, TRY `[7,4,6]`, observed true, plus time=2 and predicted=null. Those required public values visibly match that receipt, while extra time/predicted reject the frozen normalization. This is a concrete schema-restriction example, not a rescued primary score or cohort-wide content claim. Its later record uses note/prediction/action with MATCH, not the required address/source/event layout.
- Seed0 ALIGNED task_index0, `pa-eac3aa57ae37fef131360f8646b2` (P): note preserves public predicted=false and observed=false but includes time and omits required relation. The record is only an event object: all five own-event values match the new execution, but address/source are absent. This is not merely harmless whitespace or key order.
- Seed2 ALIGNED task_index0, `pa-43eae06f442a48e66506560c1c80` (P): record keeps distinct public and own receipt IDs, yet own predicted=false/observed=false is labeled mismatched rather than matched; address also absent. Thus schema restriction is not the only failure mode.
- Seed1 NO_PARENT task_index0, `pa-658b6262d5d0e5ba960c9ae8982e` (C): source is the receipt-origin prose string, not a public-note object; own relation is Boolean true, not the required matched string. All16 records in this cell have a present incorrect relation value/type.
- Delivered restatements are replay-joined verbatim and task-local. Seed0 ALIGNED’s P restatement says to maintain the initial prediction independently, preserve predicted/observed values and check consistent/different; the lexical screen still fails operation/scope patterns. This can expose a lexical metric limitation, but is not semantic proof or a changed RESTATE label. Exact contact/raw/score receipts are retained in raw_schema_audit.json.

Pre-reveal caveat: `research_notes/astra_memos/ASTRA_ALIGNMENT_NOTE_SCHEMA_CAVEAT_2026-09-13.md`, SHA256 `878af7a5af789d2b66ee385945ce26d5b437cd9f531f4bde06cffd1d157e6d46`, Main reports committed11cc2e9b before reveal. Closed-schema failure alone cannot establish absence of process skill; no exploratory permissive rescore is performed here.

## Costs and timing

|Seed|Arm|Wake/restate/record|Prompt tokens|Output tokens|Generation seconds|
|---|---|---|---|---|---|
|0|ALIGNED|16/4/16|14488|3301|130.628271|
|0|SWAPPED|16/4/13|12933|3555|141.998692|
|0|NO_PARENT|16/0/16|13105|3574|145.921899|
|1|ALIGNED|16/4/16|15548|5729|229.362888|
|1|SWAPPED|16/4/15|14907|5799|222.894122|
|1|NO_PARENT|16/0/16|13192|4503|172.123691|
|2|ALIGNED|16/4/16|13806|2767|114.083710|
|2|SWAPPED|16/4/14|12757|2578|106.204863|
|2|NO_PARENT|16/0/15|12145|5310|207.436124|

Total:144 wakes +24 child restatements +137 records =305/312 maximum calls;122881 prompt +37116 output tokens.0 parent-model calls,0fits,0updates,0new adapters. Generation spans sum1470.654261s across three roots, not elapsed cohort wall time. Fixed lesson literal lengths P42/C44tokens; each lesson arm receives the same172-token lesson multiset, but actual full prompts/output costs differ. NO_PARENT is not token-matched.

|Seed|Prepare seconds|Controller seconds|Collection seconds|Holder start→exit seconds|
|---|---|---|---|---|
|0|18.556624|576.365350|5.578783|583.320621|
|1|18.086935|777.749508|5.585855|784.751240|
|2|17.810297|582.941065|5.678029|589.934749|

Holder spans use pinned launched.started_unix→exit.completed_unix exactly; not GPU-active time. Generation/arm times nest within controllers; do not add them. Prepare is separate; collection is included within holder span.

## Execution, pins and tests

One successful local invocation; no failed scientific attempt or post-reveal code repair. CPU raw world/parser replay and custody checks passed. No native replay/model/tokenizer/tensor verification was claimed. Main separately verified archive extraction and original parent payloads.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 /tmp/astra_parenting_alignment_analysis_20260913.py \
  --manifest /tmp/astra_parenting_alignment_analysis_inputs_20260913_attempt1.json \
  --manifest-sha256 f326cab1164681f566f29fda96284aea53cd53d8f8caf7c8be0989f5c846034d \
  --source-root /tmp/astra_level1_real_record_source_20260913_attempt1 \
  --protocol-path /data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_PARENTING_ALIGNMENT_DEV_2026-09-13.md \
  --module-dir /tmp \
  --out /tmp/astra_parenting_alignment_analysis_result_20260913_attempt1
```

Command above is the preserved successful command, not a request to rerun into the existing write-once directory.

Frozen fixture suite:13PASS6.674s before outcomes; not rerun here. Test command:
```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp python3 -m unittest -v test_astra_parenting_alignment_analysis_20260913
```

Exact pins:
- `/tmp/astra_parenting_alignment_analysis_20260913.py` SHA256 `bfb91300b4d9e3c7abdd3c12a1b61541321db323ed96b7d49cc240a95cb6085d`.
- `/tmp/test_astra_parenting_alignment_analysis_20260913.py` SHA256 `845a3c041dc4efa40004e7bfdc97e057b79f580efa9626f79d447ce459649bfa`.
- `/tmp/astra_parenting_alignment_analysis_20260913_handoff.md` SHA256 `71fa7886f2420353a295ce29230575dfc9065a7a31c8a7963b937e43ab610d81`.
- `/tmp/astra_parenting_alignment_core_20260913.py` SHA256 `71311d3d9add1f485289c6ee6824ef758393193ee05bcc088674d12697b11010`.
- `/tmp/astra_parenting_alignment_run_20260913.py` SHA256 `712248f1fc86b026e68e9cfbc791d3b441c6ded53db82f7622f8f2cd2b8b8c2a`.
- `/tmp/astra_level1_real_record_run_20260913.py` SHA256 `3c03304ee5309517ce34f91b121594f0070b37bfb14f31f429f915d8310cc20e`.
- `/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_PARENTING_ALIGNMENT_DEV_2026-09-13.md` SHA256 `5c53d6aa850b3a3a409c255ab9b28ce3b090f7325f35688437e42a86b1cccce5`.
- `/tmp/astra_parenting_alignment_archive_receipt_20260913.json` SHA256 `855bd8f85fe87ce1a45bbca4ac494e018ccec48bd136eb692d102ef3522387c3`.
- `/tmp/astra_parenting_alignment_analysis_inputs_20260913_attempt1.json` SHA256 `f326cab1164681f566f29fda96284aea53cd53d8f8caf7c8be0989f5c846034d`.
- `/tmp/astra_parenting_alignment_analysis_result_20260913_attempt1/analysis.json` SHA256 `ee2e60a502a2884c2ed20701612ed05f6e04a718eff8c6775d543ac1df4b2b10`.
- `/tmp/astra_parenting_alignment_analysis_result_20260913_attempt1/analysis.md` SHA256 `f52436c52c0fc193a51467f1e593793cba4cde1728f63926a31e6be35162ccf1`.
- `/tmp/astra_parenting_alignment_analysis_result_20260913_attempt1/raw_schema_audit.json` SHA256 `8d1c27f688b0512c69a0418a888d78f27030fc252ef64e80e7979fc5bc0a66a2`.

Main archive: `gpu_artifacts_local/parenting_alignment_20260913_attempt1/evidence.tar` SHA256 `ee83389388135d786c0508e602db01f8678a29c0b2a8a53efae6d2ecf3ae220f`,856members,13578240bytes. Main’s original-parent archive SHA256 `addc2e61ce05f2b622482adde82f16c2c571db6dd072b0fb7750a4d6dc559a3a`; payload verification was separately supplied, not repeated here.

## Limits

Three learner roots, not144 independent tasks. Same 2:1 order confounds learner and lesson order. Identical task/lesson multisets do not match generated trajectories or token costs. Results concern immediate fixed-lesson/current-restatement packages; no mediation, adaptive-parent, persistent learning, parenting amortization, H1/H2 or paper promotion. Frozen failure and schema/lexical measurement caveats coexist; neither overrides the other.

EDITSTOP

# C2 no-exclusion adoption: NOT LIVE

Read-only observation: **2026-09-18 12:00:18 UTC**. Original C2 PID **3624513**, start ticks **25171256**, latest LOADED **7620 at 07:28:47.072 UTC**, head **9450**.

## Actual running sleep, not source intent

- Current sleep **93**: SLEEP_REQUEST **9413**, SLEEP_RECIPE **9414** (journal-file mtime **11:54:05.826 UTC**).
- Recipe actually names `R181_NEW_ONLY_V1`, `R194_FULLWIDTH_CODE_TARGET_EXCLUSION_V1` and `R195_CHILD_ROW_REVIEW_V1`. It declares **4 candidate NEW rows**, **16 presentations**, **0 selected old rows**, anchor lambda **0.25**.
- TARGET_ELIGIBILITY **9415** proves semantic filtering actually ran: **segment 318** is excluded under the R195 review, with **R209 prose/script quarantine** and **R213 uncertain-content** evidence. **3 NEW rows remain, 48 presentations planned**, not all four rows. Raw target bytes are unchanged. This sleep was not yet COMPLETE at the observation; no finished-update total is inferred from the recipe.
- Native and driver `learn_row_policy` are both **null**. Existing R213 content, R209 prose, R220 question and R220 fabricated-speaker selectors remain configured in the frozen driver.

## Published source is not adoption

- Published commit `bb1e9a9033979d50ed97072675515f7290de1237` implements prospective `R227_ALL_AUTHENTIC_CHILD_ROWS_V1`.
- A correctly adopted R227 recipe declares `learn_row_policy=R227_ALL_AUTHENTIC_CHILD_ROWS_V1`, `active_semantic_filters=[]`, and `semantic_row_exclusion=false`. **None of these fields appears in live recipe 9414.** Omitted newer metadata is not evidence that filters are off; actual exclusion 9415 independently establishes the opposite.
- The running image's native/driver/content-module hashes still match their old guard pins. `organism_v6/orch_r227_learning_policy.py` is **absent from that image** and its source pins.
- **No-exclusion adoption remains pending.** No supported gapless policy-reload hook is available in this loaded image. No restart, gap, hold, signal, live-source edit, new filter, dosage change or fake hot adoption was performed.

See `C2_NO_EXCLUSION_RECEIPT.json` for exact event/source hashes and bounded exclusion proof. Private raw state remains excluded from publication. The completed recall and four-retirement commits remain `58828cf568b0a7a4945cddf228d7c1d9d87e66f3` and `d88ba9c47b0845dbd259d6e5fd211baf715fcc94`.

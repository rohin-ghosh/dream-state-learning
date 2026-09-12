# SEQ-069 bounded staging-doc review

**Verdict: no actionable high-, medium-, or low-severity finding in scope. Previous comparator ambiguity is fixed.** Advisory only; this is not a gate on main's repairs or concurrent replay, and does not certify that replay's outcome.

Scope: only newly added P0 counts, costs, custody/transport claims, and comparator wording. Compared local copies of the supplied committed terminal memo and parts manifest; no Git/commit-status inspection, archive reconstruction, archive/part-content hashing, payload verification, reducer/replay, GPU work, or repository edit. Only text/arithmetic checks, small-document hashes, and part file-size metadata were read. This review is the sole output file.

Read window: **2026-09-12 09:59:50–10:00:37 UTC**. Exact snapshot hashes below were read at **10:00:37.604087–10:00:37.604463 UTC**; conclusions do not cover later concurrent changes.

## Checks and dispositions

1. **PASS — terminal counts and all-zero interpretation.** `paper_prototype/astra_sprint_draft_20260912.tex:368`, `paper_prototype/astra_sprint_abstract_20260912.md:14`, collaborator draft `:15`, and claim map `:107` agree with terminal memo `:72` and `:124`: 64 schedules each; lesson/sham 1,913/1,632 nonempty records, 1,903/1,627 measured ACTs, zero strict faithful and unique grounded records. Rejection sums reconcile exactly, including newly explicit action-mismatch **2/0**. TeX `:385` and claim map `:120` correctly limit the degenerate empirical bootstrap to observed differences, not population zero/equivalence. **Correction: none.**

2. **PASS — all 10 newly tabulated exposure values match.** `paper_prototype/astra_sprint_draft_20260912.tex:396` and claim map `:124` match terminal memo `:73`: requests 2,937/2,656; teacher-token exposures 596,211/419,648; all child-output tokens 523,532/516,698; NOTE_AFTER tokens 189,485/161,746; prompt exposures 9,351,173/8,815,390. Arithmetic independently checks **203×2,937=596,211**, **158×2,656=419,648**, and 1,024 wake requests plus slot requests equals total requests. Abstract `:17` and collaborator `:17` preserve retokenized-output and unequal-dose caveats. **Correction: none.**

3. **PASS — timing/cost and skipped execution remain distinct.** TeX `:409` and claim map `:131` do not infer exact formation GPU-hours or duration from partial logger times/09:32:51 observation, consistent with terminal memo `:249`. TeX `:415`, collaborator `:17`, and claim map `:133` preserve actual `PAIRED_SKIP_INSUFFICIENT_MATERIAL`, required 64/available 0/selected 0 and no P0 fits/adapters/probes; empty directories are source-supported at terminal memo `:239`. Frozen analysis completion is not mislabeled a new learning experiment or CPU-test scientific success. **Correction: none.**

4. **PASS, receipt-level only — transport/custody consistency.** TeX `:534`, abstract `:15`, collaborator `:19`, and claim map `:139` correctly identify ordered **part00 then part01**, not a tracked standalone `.tgz`. Whole and part digest strings exactly match manifest `:11`; the manifest's own hash matches the claim map. Metadata sizes **62,914,560 + 51,626,836 = 114,541,396 bytes**, matching terminal memo `:314`. The **6,024 = 6,016 + 8** content-file count matches memo `:280`/`:316` and is attributed to recovery, not this review. No transport or scientific replay was repeated. Reported push `98373338` is attributed to main, not independently verified here. **Correction: none; retain that attribution and do not infer success of main's concurrent replay.**

5. **RESOLVED — comparator denominator.** `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md:13` now explicitly says **“32/64 correct and 58/64 valid”**, replacing the ambiguous “32/58.” It further distinguishes the counts from 32-of-58 accuracy. This resolves the prior LOW wording finding without changing results. **Correction: none.**

Historical pending statements in claim-map `:208`/`:212` are explicitly superseded at `:214`. Current abstract `:3`/`:7` and TeX `:431` correctly complete bounded P0 accounting/custody while leaving the learning campaign and canonical integration incomplete. No further manuscript or literature review was undertaken.

## Exact reviewed versions

References above use **collaborator draft** and **claim map** for the two full paths below. **Terminal memo** is `research_notes/astra_memos/ASTRA_P0_MATERIAL_TERMINAL_2026-09-12.md`; **manifest** is the final path below.

| File | SHA256 |
|---|---|
| `paper_prototype/astra_sprint_draft_20260912.tex` | `492f9621956863919e4868fe3dcd8889ff65e2a0d694ee379d0847a27e2b3c92` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `812ccea97b16c637e0529c07228460d47f5b3ded2662f53b5ea4d1f915ecc9a6` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `ea1ef64e1bfb81aeedf8130b0f8ff91d0268f552f9d49d520d2db074d8bed825` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `bd9cde3b955eaa35cf6e2068e0011b6edb2f751bc1d59e758de7f30fe7ea7a05` |
| `research_notes/astra_memos/ASTRA_P0_MATERIAL_TERMINAL_2026-09-12.md` | `aa5391797d2aa93b56ccf2d2341cb9f2eb629ebff93d9d9aea1ed8b24fcea1c4` |
| `research_notes/astra_memos/receipts_20260912/astra_P0_material_terminal_20260912.parts.md` | `0f6530263839bad74375778284335b15075b01dcedd55f0e220e2b4c85336530` |

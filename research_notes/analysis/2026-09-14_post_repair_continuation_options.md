# Post-repair continuation: existing paths and exact gaps

September 14, 2026. Bounded source-only review, updated after Main reports all
four repair cells terminal. Local JSON summaries were checked below; this is
not an independent raw-trace reduction or native tensor inspection.
Inspected checkout HEAD: `d9d9e97fc7eccc88a3b3f39561d5ac5e497eea25`.
Only this memo is edited; no model/tokenizer imports, native runs, source edits,
draft/notebook changes, commits or launch instructions.

## Terminal condition supplied by Main and checked locally

Source `fbe0981c36c30590b4f640c4134cca48bf36272c`; local root
`gpu_artifacts_local/astra_selected_reader_repair_terminal_20260914_attempt1/extracted/`.
All four AFTER RESULT files say COMPLETE. Their panels, AFTER_HELD summaries and
NEXT_ACTUAL_READERS summaries agree with Main's preliminary endpoint report:

| Repair cell | Own routing /4 | A2 recall W0/W8, each /4 | Old W0/W8, each /8 | Classifier /16 | Next actual audit |
| --- | ---: | ---: | ---: | ---: | --- |
| AUDIT_SFT_SELECTED | 4 | 4 | 8 | 16 | 6/6 true, all NONE, zero choices |
| AUDIT_SFT_UNIFORM | 4 | 4 | 8 | 16 | 6/6 true, all NONE, zero choices |
| AUDIT_LOSS_OFF_SELECTED | 3 | 3 | 7 | 12 | 4/7 correct; source1 false positive |
| AUDIT_LOSS_OFF_UNIFORM | 4 | 4 | 8 | 13 | 5/6 correct; source1 false positive |

SFT's common pre-repair routing3/4 and exact A2 recall1/4 become4/4, with old8/8
and classifier16/16 retained. This supports **useful taught-selection → fact
write → action repair on this DEV lineage, matching uniform, not superiority**.
The OFF failures remain part of the comparison. Both OFF children receive the
same audit-lesson rehearsal during repair; cross-state contrasts also differ
in initial weights and selections. Neither all-true post-repair audit tests
fault sensitivity; the retained16-case classifier provides that separate check.
MISS remains0/4 in every cell. AFTER calls are106/106/109/106 in table order.

Main now chooses **AUDIT_SFT_SELECTED** as the continuation parent. Its checked
local train RESULT SHA256 is
`5ad2ed4492375626941cef0113bd7d6c1e60e8147acca7ec21cf5e8cfa02428b`;
AFTER RESULT SHA256 is
`3de825f271da07fb481329ea3a62c6b2505dab135c4b6841ca96d26d6446c84f`.
The AFTER receipt binds that train RESULT and records the same adapter state as
train's after-state:
`48dc1d6d77852bddba75e04ee7442f4ef2a8e72bce5719d39ade4ed974a2b042`.
Recorded adapter-file SHA256 is
`335e2866dba9889647d18cbe1cd9bce58231c7ce4fbafe2f982cce24716c9821`.
The next native parent must be that cell's `train/adapter`, authenticated through
these receipts/files and a live state check, not the post-lesson ancestor or
the uniform sibling. This writer hashed only the two RESULT files, not weights.

**Do not repeat same-bank repair:** the selected SFT child's next audit admits
zero choices. A fresh bank is the relevant next question; no pointer, fault,
or repeat fit should be manufactured to keep the old loop running. Independent
full reduction remains separate and behind Main's execution.

## Bottom line

**No unmodified native entry currently joins a repaired AUDIT_SFT child to a
genuinely fresh adult bank and a matched selected/uniform sleep.** The existing
100-update repair writer is the closest reusable writer, not the 400-update
adult driver. Missing pieces are explicit bank/collection provenance, terminal
repair-parent acceptance, removal of A2-only audit assumptions, and a decision
about replay coverage versus evaluation of all twelve prior records. These are
observed interfaces, not a proposal to implement or bypass their checks.

The current design is
`research_notes/analysis/2026-09-14_selected_reader_repair_design.md`.
Within each developmental state, SELECTED/UNIFORM begin from the same parent;
across those terminal repair cells the weights already differ. A **new material
comparison** must fork one declared terminal repaired child twice and share its
one collection/action/audit packet. Continuing two different repaired children
instead compares trajectories, not material alone. Main's disclosed choice is
now AUDIT_SFT_SELECTED; the new uniform-material fork would share this exact
parent, not use the already different AUDIT_SFT_UNIFORM terminal weights.

## Reusable interfaces and blocking boundaries

| Need | Existing interface | Exact limitation |
| --- | --- | --- |
| Authenticate a terminal repair parent | `gpu/astra_selected_reader_repair.py:18` `load_inputs`; `:61` `checked_training` | Reconstructs the original lesson/actual-audit ancestry, validates COMPLETE/100 updates, parent/material arms, source, before/after state and adapter/training-file hashes. Its CLI has only prepare/train/after (`:87`), not next collect; its loader still starts from the post-lesson parent. |
| Load the same saved child, not a new adapter | `gpu/astra_experienced_event_microloop.py:114` `Engine`; repair entry `:121` and `:135` | Existing callers set engine phase to readout, pass the saved adapter directory and compare live LoRA state to the terminal training digest. Engine phase train instead initializes a new rank8 adapter (`:138`): it is not a warm-start switch. Engine alone does not authenticate the caller's lineage. |
| Offer four new experiences | `organism_v6/experienced_event_microloop.py:65` `build_bank(master)`; `:106` exploration, `:123` observation, `:139` validation, `:159` compilation; `organism_v6/experienced_event_adult_cycle.py:127` `collect` | Arbitrary-master bank construction exists, but adult collection/replay only accepts cycles1/2 with fixed A1/A2 masters (`:48`, `:78`, `:146`). Both are already exposed. Reusing A2 is recollection, not a fresh bank. There is no exposed fresh-bank collection/replay argument. |
| Admit the repaired parent to adult collection | `gpu/astra_experienced_event_adult_cycle.py:21`, `:42`, `:68`, `:640` | Cycle1 demands the second-sleep receipt; cycle2 demands a cycle1 adult-training receipt. Neither accepts repair-schema/100-update ancestry. Changing a directory or relabelling the receipt does not solve this. CLI cycles are only1/2 (`:578`). |
| Child action and actual-reader audit | `organism_v6/experienced_event_read_route.py:58` `run_episode`; `gpu/astra_experienced_event_cue_sleep.py:158` `evaluate`; `organism_v6/experienced_event_actual_reader_audit.py:29` `build_cases`, `:91` `collect_cases` | Controller/reader tracing is reusable. Audit preparation calls `experienced_event_corrective_replay.prepare_cases` (`:80`), which replays a fixed adult collection, requires cycle2 and all four committed route records (`:87`). A fresh bank cannot just be labelled A2. Missing/failed transitions cannot be reconstructed from an answer bank. |
| Selected versus uniform sleep, no new trainer | `gpu/astra_selected_reader_repair_train.py:32`, `:65`, `:91` | Existing100-update, fresh-AdamW, rank8 writer accepts exactly80 memory +20 cue +62 lesson +32 wrapper-major new rows. It preserves duplicate selections, supports all four records uniformly, and records uniform-reference denominators and per-fact doses. Actor/source binding is explicitly caller-owned (`:88`); the native loader does not accept a next-bank packet. |
| More than eight old records | `gpu/astra_experienced_event_adult_cycle.py:145` `evaluate`; `:84` `encode_old_rows`; `organism_v6/experienced_event_adult_cycle.py:174` `adult_indexes` | Evaluation rejects old-bank lengths other than4/8; old encoding/schedule accepts only32/64 rows. These are genuine guards, not output-label issues. Repeated whole evaluations to work around the cap would duplicate action/control calls. |

### Twelve-record accounting is separate from replay-row accounting

The next fresh four-record bank makes original4 + A1 four + A2 four the **twelve
prior records**. Previously failing A2 records stay in the denominator; report
per-field and exact BEFORE/AFTER outcomes rather than treating every old failure
as newly forgotten. The current eight-old panel plus four A2 probes covers those
twelve only while A2 is still the current bank.

`gpu/astra_reader_audit_lesson.py:29` constructs80 memory rows: eight older facts
plus only the two originally selected A2 facts, eight views each (`:45`). Repair
new rows separately contain all four A2 facts. Moving the new-row slot to a new
bank while retaining that80-row curriculum leaves two A2 facts outside old-memory
replay. That can be disclosed, but is **not full twelve-record rehearsal**.
Full eight-view rehearsal would require96 memory rows; none of these selected,
corrective or adult writers accepts that layout. The older corrective writer
requires64/20/32 (`gpu/astra_corrective_sleep_train.py:86`), and the lesson writer
requires80 memory rows (`gpu/astra_reader_audit_lesson_train.py:88`). No schedule
expansion, silent omission, or replacement of source rows is justified here.

### Required continuity, using existing binding patterns

The evidence chain must remain terminal repair train/file hashes → live loaded
adapter-state equality → that child's new collection captures → that same
unchanged child's committed action and actual reader traces → source-valid
audit choices → two fits from that identical parent → each saved adapter's
fresh readout binding. Repair entry `:114`, `:135`, `:163` and `:170` demonstrate
loading, trace capture and read-only state/base checks, not a generic next-cycle
loader. Hash strings or copied weights alone cannot substitute for those joins.

Keep all source-valid audit choices, including duplicates or semantically
unhelpful choices; copy their original experienced rows, never faulty reader
text or supplied source-table prompts. `organism_v6/experienced_event_actual_reader_audit.py:70`
records correctness separately from source admission. NONE/rejected output
creates no substitute. The repair writer requires1–8 selections even for its
uniform reference; zero selections is a real unsupported paired-sleep case,
not permission to invent a pointer. Parent-free here excludes new guidance at
collection/action/audit; rehearsing the existing62 parent-stripped lesson rows
does not make the lineage historically unparented. Offered worlds/public audit
prompts still are external scaffolding.

## At most three bounded options

1. **Use the current repair terminal packet — complete, no new science.**
   Read the existing train/AFTER/NEXT_ACTUAL_READERS artifacts and their reduction;
   do not rerun probes merely for this review. Repair entry `:163` already runs
   classifier, routing/recall/retention and actual-reader auditing. Incremental
   model calls/updates are0; the summary check above supports Main's choice to
   consider fresh experience. Existing per-cell caps are100 updates and at most
   `76 + 16 + 24 = 116` AFTER generations: core panel, eight-old W0/W8, and16
   classifier plus at most8 actual audits. This establishes only current-bank
   repair/retained skill, not a reason for another same-bank fit. Any later
   integrity discrepancy must remain visible rather than be erased by this memo.

2. **One fresh parent-free collection/action/audit from SFT_SELECTED — next
   bounded question, but no unmodified entry yet.**
   Reusable collection/controller/audit primitives are listed above, but fresh
   master/replay acceptance and repair-parent binding are absent. If Main later
   supplies a source-reviewed path, four episodes cost at most8 collection calls,
   four own routing episodes at most20 calls (three actor +two reads each), and
   at most8 actual audits: **36 generations, zero updates** for that narrow
   packet. This excludes retention/classifier controls. With the existing full
   panel shape plus twelve-old retention and16 classifier cases, the conditional
   bound is `8 + 76 + 24 + 16 + 8 = 132`. It is a prompt/collection feasibility
   result, not write utility on the new bank. No such fresh packet or native
   budget is asserted to exist now; no duplicate BEFORE or extra selector is
   needed for option3. If the fresh audit also yields no choices, preserve that
   outcome; do not force the selected/uniform sleep interface to accept a fiction.

3. **One shared collection, two same-parent material forks — smallest decisive
   utility branch, conditional and not runnable unmodified.** Use option2's
   one common BEFORE/audit packet, with actual nonempty source-valid choices,
   and the existing repair writer twice, only
   after Main resolves the binding/A2/retention gaps and explicitly chooses
   whether the unchanged80-row replay coverage is acceptable. Keep the existing
   100-update recipe: **200 total updates**, per arm100 memory +38 cue +62 lesson
   +200 new presentations, with actual/reference tokens and duplicate-aware
   doses reported. Full common BEFORE plus two AFTERs, each using the panel
   accounting above, gives the conditional ceiling `8 + 3*(76+24+16+8) = 380`
   generations, inclusive of common selection and post-fit actual audits. These
   are helper-cap arithmetic, not measured time or a qualified new runner.
   Different per-fact doses remain; same-parent material utility is not isolated
   selector-policy learning, H1/H2, or an independent learner replication.

**Recommendation:** Main's terminal SFT_SELECTED result supports considering
**option2 on one fresh bank**, not another same-bank repair. If that new bank
yields source-valid choices, option3 is the smallest decisive next material
comparison: two forks from the same SFT_SELECTED parent, one shared collection
and paired BEFORE, with no additional selector or learner. This asks whether
the useful integrated behavior recurs beyond the repaired bank; the current
uniform tie does not predict selection superiority. No existing CLI satisfies
that branch today. If full twelve-fact
rehearsal is required rather than twelve-fact evaluation with disclosed partial
replay, the fixed existing writer is also insufficient; return that decision
to Main rather than silently changing the recipe. No new trainer/rank/base,
literal weights-hop, automatic refit or implementation is proposed here.

Existing guard references only: `gpu/astra_adult_collection_guard.sh:35` uses a
1920-second lease allowance and1860-second timeout; repair guard `:29` uses7440
seconds for train/readout, with5460/1860-second timeouts and60-second kill grace
(`gpu/astra_selected_reader_repair_guard.sh:39`). Native internal checks are
5400 seconds for training and1800 otherwise (`gpu/astra_selected_reader_repair.py:110`).
These hard caps are not runtime estimates and do not authorize a new continuation
or establish current device/lease availability. Main owns remaining source work,
runtime decisions and independent verification behind execution.

# Selected reader repair — first terminal result

September 14, 2026, 13:01 UTC. Main analysis from all four complete native cells;
independent reducer and field audit are in progress, not prerequisites to further
authorized work. Source `fbe0981c36c30590b4f640c4134cca48bf36272c`; prospective
protocol `2026-09-14_selected_reader_repair_design.md`. This is SEQ-241.

## Result

The taught auditor's actual selections `[1,3,3]` produce a useful repair sleep:
the updated child recalls all four A2 records under both read wrappers, routes
4/4, retains eight older records, and retains the 16/16 parent-free classifier.
This matches uniform replay; it is NOT a selection-superiority result. The
former loss-off child's selected `[1]` sleep leaves one A2 fact unresolved and
loses one older fact. Its uniform fork repairs all four and retains the old bank.

| Endpoint | SFT prior | SFT selected | SFT uniform | Loss-off prior | Loss-off selected | Loss-off uniform |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Own routing | 3/4 | 4/4 | 4/4 | 3/4 | 3/4 | 4/4 |
| A2 strict W0 recall | 1/4 | 4/4 | 4/4 | 0/4 | 3/4 | 4/4 |
| A2 strict W8 recall | 1/4 | 4/4 | 4/4 | 0/4 | 3/4 | 4/4 |
| Older W0 recall | 8/8 | 8/8 | 8/8 | 8/8 | 7/8 | 8/8 |
| Older W8 recall | 8/8 | 8/8 | 8/8 | 8/8 | 7/8 | 8/8 |
| Parent-free classifier | 16/16 | 16/16 | 16/16 | 7/16 | 12/16 | 13/16 |
| Reader-OFF routing | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| Held supplied-text routing | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 |
| Unseen MISS | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |

Each prior is that state's own post-lesson AFTER, not the common pre-lesson
checkpoint. All strict scores are unchanged; field-level analysis is separate.

## Continued use of the updated learner

After reload, the newly repaired child acts using its own memory and audits
every reader response it just consumed, under the same parent-free audit prompt.

| Cell | Actual audit | True stratum | Fault stratum | Admitted source pointers |
| --- | ---: | ---: | ---: | --- |
| SFT selected | 6/6 | 6/6 | absent (0/0) | none |
| SFT uniform | 6/6 | 6/6 | absent (0/0) | none |
| Loss-off selected | 4/7 | 4/5 | 0/2 | `[1]` |
| Loss-off uniform | 5/6 | 5/6 | absent (0/0) | `[1]` |

No fault stratum is not perfect fault detection. Both loss-off-derived children
select source1 despite its correct reader response: those are source-valid
false positives, not repaired or filtered selections. SFT's six NONE responses
are correct abstentions after successful repair. No automatic subsequent fit
is warranted on this now-correct SFT bank.

## Budgets and measured operating envelope

Every fit completes 100 updates with 100 prior-memory, 38 cue, 62 audit-lesson,
and 200 new-memory presentations; batch4, fresh AdamW LR3e-5, seed0, unchanged
rank8/frozen base. New-source presentation counts by index0..3:

- SFT selected: `[0,72,0,128]`; actual target tokens16093.
- SFT uniform: `[50,50,50,50]`; tokens16449.
- Loss-off selected: `[0,200,0,0]`; tokens16349.
- Loss-off uniform: `[50,50,50,50]`; tokens16449.

All use reference target-token denominator16449. No equal actual-token or
per-fact exposure claim. The shared behavior pool includes the62 audit rows
even for the former loss-off child: this is a common repair curriculum, not
continued withholding of audit supervision. Across developmental states the
initial weights and selected source sets differ; this is not a same-state
isolation of selection policy. Within each state, initial adapters match.

Native train phase durations, including load/checkpoint, are respectively
200.107,199.207,199.777,199.944 seconds. Fresh AFTER phases are
151.757,149.270,155.134,152.589 seconds. Total native phase wall time summed over
the four dedicated A40s is0.3911 hours, not measured kernel-active GPU time;
all four finished within about six minutes of the common12:52:55UTC start.
There are427 AFTER calls (106,106,109,106). Maximum encoded training sequence
is575 tokens; configured context cap2048 is not a tested length575→2048 guarantee.
All four logs contain allocator OOM/recovery warnings during training, yet all
100 loss records, saves and readouts completed. Do not describe memory headroom
as ample or omit these warnings from larger-run planning.

## Preservation and limitations

Complete terminal root, including source, four adapters, logs, launch/prepare
receipts and all captures, is preserved at
`gpu_artifacts_local/astra_selected_reader_repair_terminal_20260914_attempt1/`.
Archive `terminal_root.tar` is396359680 logical bytes; SHA256
`773f4c2d34ea6fdad74e2ba8f9057670d20c72c3ac9ec24d8ca1e42f17e6e280`.
All3196 files pass the separate remote hash manifest in `local_check_v2.txt`.
An earlier verification command used the wrong local working directory and
produced only an empty `local_check.txt`; it is retained, not evidence of a pass.
All four adapter inventories and AFTER-to-train state/receipt joins also pass.

This supplies an observed finite chain: taught audit behavior, parent-free
source choices on actual reader errors, persistent selected-material write,
improved own actions, retained taught behavior, then appropriate abstention on
the repaired reads. It is one adaptively exposed DEV lineage, one seed, one
small task family with receipt-grounded source tables and external scheduling.
Uniform is equally successful for SFT. No H1 generalization, H2 slope, overall
selection advantage, clean ancestry, general mechanism freeze, or mature
autonomous self-improvement is established. Unknown-MISS failure remains.

Next: a fresh experience bank from the successful SFT-selected child is more
informative than another sleep on the repaired bank. Locate/reuse the existing
collection and continuation interfaces; declare the next comparison before any
new collection or fit. Independent field/replay analysis and manuscript updates
continue in parallel.

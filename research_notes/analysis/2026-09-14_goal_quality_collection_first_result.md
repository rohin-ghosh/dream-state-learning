# Quality-filtered collection — SEQ262, 2026-09-14

All four new collection units complete; CPU assembly accepts1452actual child
trajectory rows. This is a successful dataset-collection result, not successful
training, transfer, improved learning or recovery of failed SEQ258 admission.

| Unit / original shard | Newly taught TRAIN worlds | Actual new calls | Accepted opposite-goal pairs | Rows |
|---|---:|---:|---:|---:|
| 0 | 7 | 168 | 14/14 | 168 |
| 1 | 8 | 192 | 16/16 | 192 |
| 4 | 7 | 168 | 14/14 | 168 |
| 6 | 7 | 168 | 14/14 | 168 |

New696calls contribute696rows from116successful coached episodes. Original
768TEACHcalls are reused, not regenerated:756rows retained under the new
uniform paired-episode rule. The failed old task and its successful opposite-
goal counterpart are excluded together; no teacher/canonical replacement.
Combined1452rows correspond to242episodes/121pairs. The source-valid teaching
population is61worlds/244episodes/122pairs, while the original64TRAINworlds/
256episodes/128pairs remains recorded; three TRAINsource defects prevented
12episodes. These are explicit outcome/source filters, not an unbiased sample.

All16PROBEworlds remain in any future fixed64goal/32pair readout; the one
invalid PROBEaddress must return literal MEMORY UNAVAILABLE, alongside its
three actual valid records. No correctedSEQ259candidate is used. There are
zero newEXPOSEcalls, zero baseline repeats, zero fits/updates, unchanged37ec.

Per-unit native phase seconds185.747419,199.119869,188.427423,183.441456;
sum756.736167 (~0.210allocated A40-hours, setup included). Actual-source CPU
prepare26.702149s; assembly35.032524s wall, no model. All guards started
19:09:57UTC on node3GPUs0–3; units0/1/4/6, guardians83105–83108.

Exact source `cefc1955f508a6f7d444f19271b1d89b3e217e08`, protocol
`cf742f62dc45810caeea3ec68272a9e1a8c97d3b7c6c06f148639252ba1738f1`.
Root `/tmp/astra_goal_quality_20260914_attempt1`; new dataset and source joins
in `assembled/CAPSULE.json`. Native read and CPU assembly replay preserve
every discarded attempt; previous all-eight1536-row admission remains failed.

Terminal capsule verified on VM `/data`:
`gpu_artifacts_local/astra_goal_quality_terminal_20260914_attempt1/terminal.tar.gz`
SHA `10d2bccf87dc65638710c64b546da2120e951370f23497f93f92c8e2514b4d1c`.
Main verified result/assembly counts. Independent review remains pending.
This variable corpus cannot be silently supplied to the original blocked
1758-row/12384-update scale fit. SEQ260's full TRAIN/weak PROBE result argues
against treating larger command-only fitting as the default next expenditure.
A separately declared controlled fit, with fixed source selection and readout,
must answer the next transfer question; no such quality fit has launched.

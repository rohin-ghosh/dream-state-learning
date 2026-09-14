# SEQ266 quality fit — independent terminal result

September 14, 2026. **Released to Main. Evidence PASS; frozen engineering
target FAIL.** Independent episode reduction upholds FULL **30/32 strict
PROBE pairs**, versus LOSS_OFF **1/32** and matched baseline **2/32**. FULL
exceeds both comparators and meets every retention threshold, but only
15/16 PROBE worlds have a successful pair. The required every-world condition
fails. No exclusions, promotion, new fit or changed criterion follow.

This is strong incremental evidence for text-supported opposite-goal behavior
on these held-identifier worlds within one exposed-DEV environment family,
not broad environment transfer, H1/H2 or new parametric EVENT acquisition.

## Independent counts

Derived from individual episode tasks, traces and committed transitions, then
compared with native summaries. Pairs are fixed tasks (0,2) and (1,3), sharing
display order but opposing goals. Both tasks must reach their goal through two
legal source-grounded commits and use distinct source-correct first ports.

| Endpoint | Matched37ec baseline | FULL_TARGET | LOSS_OFF |
|---|---:|---:|---:|
| PROBE OWN_TEXT goals | 33/64 | 62/64 | 26/64 |
| PROBE OWN_TEXT pairs | 2/32 | 30/32 | 1/32 |
| PROBE worlds with a pair | 2/16 | 15/16 | 1/16 |
| PROBE UNAVAILABLE goals | 3/64 | 23/64 | 0/64 |
| PROBE UNAVAILABLE pairs | 0/32 | 0/32 | 0/32 |
| Fixed TRAIN diagnostic goals | 7/16 | 16/16 | 8/16 |
| Fixed TRAIN diagnostic pairs | 2/8 | 8/8 | 1/8 |
| Old W0; W8 | 16/16; 16/16 | 16/16; 16/16 | 16/16; 16/16 |
| Held audit | 16/16 | 16/16 | 16/16 |
| Original taught; previous fresh goals | 3/4; 3/4 | 4/4; 4/4 | 2/4; 2/4 |
| Actual native readout calls | 944 | 960 | 932 |

All 64 goals/32 pairs per PROBE condition remain in each state. TRAIN is only
the four fixed shard0/1/4/6 world0 diagnostics, not all61 eligible TRAIN worlds.
FULL has2/2 pairs in every PROBE world except index2, which has0/2. Baseline's
two pairs occur at indexes3 and5; control's one occurs at index5. Thus all
baseline/control successful pairs remain successful under FULL.

FULL gains30 individual goals and loses one relative to baseline; it gains37
and loses the same one relative to control. Pair gains are28 and29 respectively.
This is not merely improvement over a deteriorating control: FULL also exceeds
the actual matched unchanged baseline. Nevertheless achieved retention is not
matched: control's original/fresh2/4 differs from FULL4/4.

## Residual failed world — preserved, not excused

World `ASTRA-GOALSCALE-20260914-V1-SHARD-1-BLOCK-0-PROBE-A` is PROBE index2.
Its original `shard1/expose/COLLECTION_08.json`, record3, already rejects
`E_W5YA3H6TNF`: actual EVENT text ends with `R_GFU5MU3J4`, whereas its actual
transition/public receipt is `R_GFU5MU33J4`. The source collection seal is
`631459b14c8356431977162f02bf849d23ca70a628078c9d1f4f159a5c5dfdfc`.
Original ROUTE and EVENT captures are collection-local6/7; no new source
failure was introduced by this fit. The original source is under
`gpu_artifacts_local/astra_goal_scale_terminal_20260914_attempt1/extracted/`.

All three states' OWN_TEXT stores return the identical three accepted actual
EVENT strings plus literal `MEMORY UNAVAILABLE` at that address. Independent
trace-to-store comparisons confirm no canonical substitute or corrected text.
All four FULL tasks read all four addresses; tasks0/1 succeed, tasks2/3 fail.

In `FULL_TARGET/after/PROBE_2_OWN_TEXT_2.json` and
`FULL_TARGET/after/PROBE_2_OWN_TEXT_3.json`, FULL chooses `P_VD4QGEZVKT` then
`P_7QV4OUBPN2`, arriving legally at `N_QXTYUSWLOZ` instead of requested
`N_7P5OYA74NA`. The expected first port is `P_3TILLNKUCR`. These are actual
wrong-goal dead ends, not parser errors, truncated calls or evaluator exceptions.
The failed episode calls are156–161 and162–167; wrong route calls160/161 and
166/167. Episode-file SHA256s, respectively:
`0aa6237059fd1024a5f0549f69b7841413e38ec1a7c0781c052d07de87892a9f` and
`da294aa5112f370ebeab81a83d159135ddbb61d14f82cf8e72d9a16bf21f156c`.

**Co-occurrence is supported; sole causation is not.** Both baseline and
control actually succeed on this same world's task2 with the same unavailable
address (baseline route calls160/161; control156/157). FULL loses that case.
No restored-text counterfactual exists here. Keep the failed world and both
failed pairs; neither30/30 nor an impossibility claim is warranted.

UNAVAILABLE does not reproduce FULL's paired performance:0/32 despite23/64
goals. All32 opposite-goal pairs have equal first-port selections within the
pair, and all returned memory text is unavailable. This separates individual
arrival/command execution from successful same-display goal discrimination.

## Source, dose and saved-to-fresh-state checks

Frozen root, denoted R below:
`gpu_artifacts_local/astra_goal_quality_train_terminal_20260914_attempt2/extracted/astra_goal_quality_train_20260914_attempt2`.
Exact source `7f9d4251ae1ff4c5ff9138adf267d081fffa6331`; protocol
`1683ca250ef6f95cb41c7972685279a07ec3693fb9ab34e049ffb975e8eb96e9`.
Five bounded frozen files match their Git objects: quality driver/guard,
two-hop helper, goal-pair helper and protocol. The frozen conjunction is still
at least24/32 pairs, a pair in every world, old W0/W8 and audit at least15/16
each, original/fresh at least3/4 each. FULL fails only world coverage; control
also fails aggregate pairs and original/fresh retention. No source/gate drift
was found in these checks.

Prepare, both TRAINs, baseline and both AFTERs share exactly the same recorded
input binding. Both1674-row materials and reference encodings are identical.
All2928 updates per arm have the declared schedule, finite recorded losses and
recomputed active/reference label counts. Only new rows222–1673 lose labels in
control; input IDs and target IDs remain identical. Active/reference labels
are238274/238274 versus173814/238274: **64460 fewer active labels**, not equal
active dose. Both have4477997 nonpadding input-token presentations. Memory and
cue/audit presentations are2928 each; old trajectories48 and new trajectories
5808; every trajectory row appears four times. All1452 new rows are TRAIN-only;
no fixed PROBE identifier occurs in serialized training model inputs/targets.
This does not redo the earlier full collection/teacher-strip audit or retokenize.

Initial state is
`37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0`.
FULL saved/reloaded/final state is
`e226cea230b4b970cd5a94cb2b853350aa8bfb95ab4ba69cba3e78ebdd0ad3bf`;
control is
`4f0dccf5b7cf37b872eafc3a50990e0cdfda027fb0140f0aad999f27606e4ee3`.
Both saved adapter-file hashes match. TRAIN state receipts join parent-to-saved;
AFTER arguments select their own saved adapters, and loaded/final receipts join
unchanged to that state. Separate stage launch receipts support fresh-process
AFTERs; TRAIN finishes before its corresponding AFTER starts. Both bind the
same baseline RESULT hash
`c2fe5b4735ea7252fff27e7ea777093e798df882f57262ab0391ad91b6b671a2`
and their own TRAIN RESULT hashes. TRAIN explicitly did not read baseline results.
These are recorded-state/file joins, **not independent live-tensor authentication**.

## Calls, visibility, costs and primary comparison

All2836 native CALL files join, multiplicity included, to actual goal-episode,
recall or audit captures. The432 fixed TRAIN/PROBE episodes (144 per state)
have common task identities and reconstructed public-only message histories:
task, actual child commands, supplied memory and actual committed transitions.
There are no extra teacher/score/path-witness messages in those histories.
The24 old-graph episodes and96 recall/48 audit responses were also reduced and
joined; old-graph outcomes were checked from recorded commits, not a reopened
ancestor-source audit. No calls are missing or discarded. All2836 native error
fields are null; all responses terminal/untruncated. Task failures remain:
OWN_TEXT PROBE baseline33goal/25dead-end/4invalid-route/2invalid-command;
FULL62goal/2dead-end; control26goal/23dead-end/14invalid-route/1invalid-command.
UNAVAILABLE is baseline3goal/1dead-end/60duplicate-address,
FULL23goal/24dead-end/17duplicate-address, control64duplicate-address.

Recorded generated tokens total35579; prompt-token occurrences1076178, not
independent retokenization. Phase walls: baseline639.992s; FULL TRAIN5585.312s
and AFTER647.024s; control TRAIN5600.709s and AFTER645.363s. Total13118.401s,
about3.644 assigned GPU-hours, not kernel time/equal compute. AFTERs finish
21:32:18.474 and21:32:32.274 UTC. FULL's960 calls meet, not exceed, the cap;
its fixed battery is complete, not a cap failure. No current GPU status is
independently certified by this local review.

After obtaining independent counts, compared the released primary
`gpu_artifacts_local/astra_goal_quality_train_20260914_attempt2/RESULT.md`,
publication `60aca837a649ea3049bb08cf9272d3881a84b450`, report SHA256
`421948c3bac69ae031e69bc7ddc3bcf59da7c31ab6d7896089df1071ed44a777`.
**No discrepancy in the requested core counts, failed-world identity, dose,
state joins or bounded interpretation.** Preserve its disclosed failed
prelaunch-notebook-publication deviation; this result check does not turn that
into a passed logging gate or introduce a new science gate.

## Commands and limits

Used read-only `ls`, bounded `rg`/`sed`, `git show`, `sha256sum`, and inline
standard-library Python (`json`, `pathlib`, `hashlib`, `collections`, `math`,
`datetime`, `subprocess`). Checks cover task construction, episode seals,
source-correct two-hop ports, actual transition/receipt joins, pair reductions,
public-history reconstruction, all-call multiset joins, retention responses,
all saved masks/batches/loss ledgers, selected source/file hashes and state
receipts. Relevant frozen code: R/source/gpu/astra_goal_quality_train.py
(`first_ports`, `summarize_world`, `evaluate`, training/state loaders),
R/source/organism_v6/experienced_event_two_hop.py and
R/source/gpu/astra_event_two_hop_memory.py. No repository module was imported;
no old unbound helper defaults were used. The first exploratory reduction
expected a flat old-graph episode; unwrapping its actual `episode` field fixed
that reviewer-only KeyError. The successful checks above changed no raw data.

Actual archive is `quality_attempt2_terminal.tar.gz` in R's capsule parent,
186969188bytes, independently hashed as
`0152cafb69aa7715b5f4fbb15caa4954f03c62c1f3c063883ed9c17c9aa00deb`.
No full9315-entry inventory rerun, ancient provenance reconstruction, model,
tokenizer, torch, GPU, remote/network operation, native repetition, code/BOARD/
notebook/draft edit or commit. Static memo whitespace check passed. Only this
memo is written; primary-result and integration ownership remain with Nash/Main.

## Short draft alignment check — September 14, 2026

Checked only the uncommitted SEQ266 subsection at `paper_prototype/main.tex:1016`
(`sec:quality-breadth-fit`), through its source references before SEQ247.
Reviewed block SHA256:
`e57a157a1856175ec90e0362ff541db3b9d7a2286c6706b618f3bdad04e26014`.
**Quantitative and scientific alignment PASS:** primary/baseline/control counts,
15/16-world gate failure, retained unavailable address, noncausal qualification,
retention asymmetry, masks/dose, saved states, calls/tokens and assigned-time
cost match this review. Same-family held-identifier transfer is not broadened
to rich learning, authentic L2, H1/H2 or full engineering success.

Two integration updates remain in the inspected bytes: `paper_prototype/main.tex:1020`
says both fits and AFTERs completed "during21:32"; Main's proposed "By21:32"
repair correctly separates fits finishing21:21 from AFTERs finishing21:32.
`paper_prototype/main.tex:1022` still says independent raw review is pending;
that was honest when authored, but Main can now bind this released review and
update the status during integration. Neither future edit is verified here.
Recorded physical release/logging statements are checked against the primary,
not a new live GPU check. No draft edits, other-five-file review, TeX build or
whole-paper recertification. Memo/addendum ownership released to Main.

# Future-only FIFO V1 — CPU implemented, NOT enabled in native training

## Direct scope and status

Main, September 15, 2026, 06:22 UTC:

> Main decision06:22: promote fresh-row-latency design to CPU implementation of NEW prospectively labelled scheduler version for future ingestion only, not live yet. Root28.5minappenddelay may starvenewrows as corpuskeepsgrowing. Proposed maintainglobalbatch4 +2legacyfacts, use other2slots as1oldtrajectory/1FIFO never-presented-new whenqueueexists, otherwise original2trajectory; preservecurrent375/history/cursor/RNG/optimizer/checkpoint, sameFULL/OFFglobalrowselection/newlabelmask. Explicitqueue/counters onresume, preventdup/loss/starvation, log actual presentations/dose nothardcodedepoch. No L2/replaychangetoR105. You may refine if invariant/throughput reasoningdemands; send exactdelta/tests/ETA before anynativechange. Freeze sourceversion/readoutinterpretation; comparelaterFULL/OFFwithinnewversion, don'tcallpriorvsnewchangeisolation. Keepallfiveoldworkersrunninguntilnextdurablecheckpointandreadytests; no gatedidle. Priority afternewsegmentreceiverbinding, whilepublisherreviewsrun (firstbatchveto4/12, noneaccepted yet).

Implemented only in `organism_v6/orch_combined_l1_fifo_v1.py`, version
`COMBINED_L1_FUTURE_FIFO_STABLE_REHEARSAL_V1`. No native driver imports it.
The separate segment1 receiver is already polling; all five old workers continue.
This is not an instruction to stop them or permission to deploy this scheduler.

## Exact proposed delta

- At a future matched durable boundary, retain the full existing exposure vector,
  logical update, corpus/version, and both native checkpoint hashes. Preserve
  adapter, AdamW, every rank RNG file and all other native state. The CPU scheduler
  does not load, modify, or recreate any of those objects.
- All corpus rows present at activation remain historical rehearsal. In particular,
  current375 are NOT relabeled as fresh or retrospectively queued, even if an
  earlier activation snapshot contains unpresented historical rows.
- Keep global batch four and the exact two legacy-fact calendars:
  `(update-1)%128` and `128+(update-1)%82`. Same encoded whole rows, FULL/OFF row
  order, global reference-token normalization formula, masks and optimizer recipe.
- Only subsequently accepted, native-checked, whole-corpus-deduplicated external
  generation appends receive FIFO first-exposure tickets. A batch ID binds its
  manifest, native receipt, corpus prefix and version; rebound IDs fail closed.
  Duplicate rows must already be removed upstream; fully deduplicated zero-add
  batches may be recorded once. No admission, semantic selection, text edits,
  teacher material, parenting experiences or L2 data enter through this scheduler.
- While tickets exist: one rehearsal trajectory and one FIFO never-presented row.
  Otherwise: two rehearsal trajectories. No hardcoded total presentations or epoch
  stopping count. Actual committed optimizer steps update counts.

**Refinement for starvation:** the rehearsal list has a persistent cursor and a
fixed membership for each current round. Newly first-presented rows join at a round
boundary, not by continually changing the modulo denominator. At activation the
cursor equals `2*logical_update % existing_trajectory_count`, so with no future
intake the old schedule is exactly reproduced. After intake, two-slot rehearsal
fallback uses the retained round/cursor, not recomputation from a growing corpus.
This is an explicit scheduling change, not a claim of identical old trajectories.

The initial 12 legacy trajectories remain in this fair rehearsal ring. Unlike the
earlier0615 swap/repayment illustration, their exact per-update positions and
finite-window counts are NOT protected; only the first210 legacy fact rows retain
their exact calendar. This follows the proposed one-rehearsal/one-fresh allocation.
During a persistent FIFO backlog old trajectories receive one slot/update rather
than two. No deferred-repayment or fixed finite-horizon dose equality is claimed.

## Persistence and latency contract

State includes schema/source version, activation checkpoint hashes, original
counts, current counts, corpus targets/version, FIFO, rehearsal ring/cursor,
pending additions to the next rehearsal round, exactly-once intake bindings and
first-future-presentation updates. Planning is pure and does not count as exposure.
`commit_after_optimizer` requires the matching state digest, exact next update and
unchanged plan; stale/duplicate commits fail. A checkpoint receipt binds scheduler
state to native update/counts and adapter/config, optimizer and every rank RNG hash.
Restore verifies this receipt and reproduces the next plan exactly.

For a newly appended batch, if Q tickets are already queued and B are appended,
first exposure of its last row occurs by `ingestion_update + Q + B`, conditional on
that many successful optimizer updates. Later arrivals cannot overtake it. This is
not an unconditional wall-clock promise: native training ends at its existing
deadline and paused/failed updates do not provide progress. A finite current
rehearsal round finishes despite continuous arrivals because its length cannot
grow mid-round. With a growing corpus no constant uniform repeat-rate guarantee
for every historical row is claimed.

## Tests and limitations

20 focused CPU tests pass: exact original schedule without intake, future-only
scope, immutable history, FIFO counts/order, continuous-arrival fairness, manifest
idempotence/rebinding, changed-prefix/duplicate rejection, teacher/L2 quarantine,
non-mutating plan/failed intake, commit exactly once, checkpoint/RNG hash binding,
missing rank rejection, loss/duplication corruption, deterministic paired plans
under1/2/3 rank partitions, and explicit old-dose difference. Existing native
collator tests verify identical inputs/attention/reference denominator across
FULL/OFF, whole target+EOS labels, and masks on every nonlegacy selected row.

Combined source/receiver/continual subset:140PASS4SKIP. Three existing torch tests
skip because local torch is absent; one native-only packet fixture skips in the
source-only checkout. Do not report these skips as native-equivalence passes.
The separate receiver's64-candidate tokenizer-only replay passed both Node2 and
A100; that is NOT native optimizer validation of this new scheduler.

Native scheduler/checkpoint integration, crash-boundary behavior with actual
optimizer objects and unequal-rank gradient equivalence remain pre-deployment
work. Conditional engineering estimate:10–15minutes after a native-integration
scope is requested, plus at most the current128-update checkpoint window for a
controlled transition. No stop is scheduled, no source transition started, and
no deadline/readout/call budget is extended by this estimate.

## Interpretation and existing readout

This changes temporal dose, old-rehearsal frequency, batch token weights under the
same normalization formula, and order-dependent AdamW history. Changing source
lengths may also change wall-clock throughput. FULL/OFF compare new-label
supervision within this version only; earlier-versus-later differences do not
isolate scheduling or richness. Anchor the intervention to exact paired checkpoint
hashes, publish per-source/row dose and label any mixed-phase terminal readout.

Remaining readout budget remains416 of1824: per arm64math/96route/48legacy.
The registered terminal paired parent-free DEV panel starts at the first matched
128-window boundary after07:03:10.779610Z. No new intermediate panel is added or
relocated. Current estimate is roughly07:04–07:05 start and07:20–07:25 completion
if prior throughput/lengths persist; native08:03:10.779610/global08:06:10.779610
bounds remain authoritative. Richness-first interpretation and frozen panels
remain unchanged; parents never receive held outputs or sealed scores.

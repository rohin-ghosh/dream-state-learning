# R228 cycle decision observations

## Immediate target: P3/GAME1

The immediate Fable measurement is the caption player P3/GAME1. C2/P7 below
are supplementary observations, not substitutes. `p3_collect.py` runs a
separate bounded read-only observer with committed journal tails and immutable
scorer receipts. `operator/P3_LATEST.json` contains per-cycle decisions beside
actual scored, accepted and new-pixel counts; `operator/P3_PROCESS.json`
contains its actual PID/start ticks, source hashes, successful reads and expiry.

`p3_audit.py` joins RESPONSE index and record hash **and exact raw ACT hash**
to a single scorer receipt. Duplicate migrated origins, absent feedback,
incorrect hashes and pending ACTs remain unknown; missing results are not zero.
`p3_read.py` reuses Leibniz's existing R221 `native_outcome_row` accounting:
noncached, ok, boolean-accepted results; acceptance is distinct from novelty.
The collector never reads reference panels or sends feedback. Main owns live
feedback delivery and Leibniz owns fleet/hourly aggregates.

Self-declared decisions remain separate from observed parsed scene/direction
label changes. Successive new-pixel increments may support a qualified game
progress observation, never semantic novelty or a causal learning claim.
Cycles are logical sleep cycles, not automatically controller opportunities.
Scorer and journal cuts are independently timed, not an atomic joint snapshot.
P3 raw inputs and source locations remain ignored private files.

Publication includes `accounting_snapshot.py`, an exact source-only copy of
the existing R221 accounting module, because that dependency was absent from
the publication base. The collector uses it only when the shared file is
unavailable. `p3_collect_0916_snapshot.py` preserves the exact collector bytes
bound to the original running-observer receipt; that process is not hot-reloaded.

Run `python3 -B p3_collect.py --start-cycle 69 --interval-seconds 60
--maximum-seconds 1800` only when its local observer lock is free. This reads
at most 256 new journal records per later poll and at most 512 receipts per
known scoring session. It creates no remote files, learner signals, model
calls, inbox changes, parent messages, service or cron entry.

## Supplementary C2/P7 observations

This directory alone owns the new sidecar. No learner, parent, generation,
inbox, filter or runtime changes; no P3/game feedback publication. The previous
R227 watcher continues unchanged. This sidecar reuses its already-captured
private tails locally; it makes **zero new remote calls**.

## Source binding

`source_adapter.py` reconstructs the exact R227 operator cut from the ordered
file hashes listed in its receipt. Journal/anchor/through/event identities must
agree. The unchanged R227 audit binds REQUEST→RESPONSE→COMMITTED→R184_STAGE and
sleep cycles, plus explicit THINK→ACT transitions. Its module hash is recorded.
Only bound own THINK/ACT is measured. Console ACTs remain separate; LEARN is
outside this decision metric, not excluded from training.

## Interpretations and uncertainty

- Self-declared decision is continue, branch, stop, ambiguous or unknown. Exact
  matched character offsets and span hashes bind claims to the original response.
  The last explicit declaration supplies the cycle summary, while all earlier
  declarations remain visible. Conflicting claims within a response are ambiguous.
- Questions, quoted/reported characters, fenced code, conditional/negated
  statements and runtime `Continue thinking:` scaffolding are not forced into a
  task decision. New wording or a new draft alone is not a new scene/direction.
- Scene/object/direction markers and structured selections are child-authored
  metadata, not confirmation that an environment accepted a change. Labels are
  hashed; multiple incompatible selections are ambiguous. Absent metadata is
  unknown. Alias/meaning equivalence is not inferred.
- `KEEPS_DISCOVERING` requires an explicit continuing decision and a discovery
  claim and is labeled **self-declared, unverified**. Different bytes never prove
  novelty, discovery, improvement, learning or scientific validity.
- `STOPS_CHANGES` requires an earlier stop/exhaustion declaration plus a later
  observed ACT label change. `STOPS_REPEATS` requires that earlier declaration
  plus exact repeated ACT bytes. These are qualified observations, not proof of
  task failure, actual stopping, or inappropriate repetition.
- `DECLARES_EXHAUSTION` is a claim only and does not automatically mean stop or
  prove the scene exhausted. Missing/pending ACT never means stop. Unknown is an
  explicit outcome, not a forced or negative choice. The English-oriented rules
  are incomplete and are not semantic eligibility criteria.

## Running and custody

`python3 -B decision_audit.py --label C2` (or P7) makes a fixed metadata report,
keeps full source evidence privately, and records the old watcher's actual
PID/start ticks/state/expiry without signaling or restarting it.

`python3 -B observe.py --interval-seconds 60 --maximum-seconds 3600` continuously
projects both existing local feeds. It cannot outlive the upstream observer's
declared expiry and does not extend that window. Outputs remain in this worker's
`operator/` directory; raw new decision rows are appended once under ignored
`private/`. The only process lock is local to this observer, not a learner gate.
`operator/PROCESS.json` records actual identity, successful projections, stale
upstream status, errors and expiry. No cron or system service is installed.

Reports contain counts, timestamps, hashes, offsets and record IDs, never raw
child/parent transcripts, object labels, live paths, hosts or credentials. Raw
unknown/ambiguous material remains intact privately. Count totals and per-cycle
status distinguish completed, sleeping and open cycles. No causal explanation
or register-based scientific claim is made.

Run focused synthetic tests with `python3 -B -m unittest discover -s
research_loop/workers/rohin228_decision_audit_20260918 -p 'test_*.py'`.

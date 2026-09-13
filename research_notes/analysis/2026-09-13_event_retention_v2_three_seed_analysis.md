# EVENT-retention-v2: completed three-seed component comparison

2026-09-13. Observed DEV component result, not a parenting or general G3 result.
Independent post-result raw recount passed on September 13, 2026. The committed
raw reducer and native input/failure-history validation have also passed.

Peirce independently recounted 288 calls and 72 A/B cells against captured
expected output bytes: 168 strict-match-plus-stop successes, all 288 stopped,
zero truncations. The cell vectors and all-in costs below agree. The review
verified the reduction and 3,336-member archive hashes, and charged seed0
attempt5's 196.98049139091745 seconds exactly once while retaining its exclusion.
This is artifact-level review, not native attestation, independent tokenizer
decoding, semantic rescoring, or qualification of a broader scientific claim.

## Result

All three optimizer seeds completed every predeclared branch. The following
counts hold separately for each seed 0, 1, and 2, in both W0 and W8:

| Checkpoint/condition | Old A records | New B records |
| --- | --- | --- |
| Original/no-write C0 | 0/4 | 0/4 |
| A200 acquisition | 4/4 | 0/4 |
| A200 then B200 new-only | 0/4 | 4/4 |
| A200 then B400 new-only | 0/4 | 4/4 |
| A200 then REPLAY400 | 4/4 | 4/4 |
| CLEAN_CUM600 from C0 | 4/4 | 4/4 |

All 288 accepted readout calls terminated without truncation. Correctness is
the predeclared strict output match together with stop termination, not a
manual semantic rescore. Full per-seed vectors, paired differences, and costs
are in `2026-09-13_event_retention_v2_three_seed_raw_report.md`.

Replay has an old-record difference of +4/4 against each new-only comparator,
with no new-record difference, in every seed/view. Replay and clean cumulative
training have the same measured outputs on these panels. This is an observed
zero difference, not an equivalence test or a claim of identical parameters.

## What this establishes and does not establish

Within this fixed eight-record exposed DEV bank, the recovered writer can
acquire the first bank, acquire a second bank while losing the first under
new-only training, and preserve both banks under the prescribed replay mix.
The result survives the recorded checkpoint/fresh-readout sequence. Three
optimizer seeds give consistent outcomes on the same bank; they are not three
independent banks, and W0/W8 are not independent task replications.

B200 matches the replay arm's new-record dose but not its additional old
record exposure or total work. B400 matches total followup updates but assigns
them all to new records. These two useful comparisons do not isolate a pure
replay effect at simultaneously equal old dose, new dose, and total work.
The clean-cumulative comparison also differs in phase-boundary loading and
optimizer/dropout reset. It is explicitly descriptive.

This does not establish held-out behavioral transfer, long-horizon stability,
saved optimizer resume equivalence, useful child-selected learning material,
parent removal, autonomous learning-policy improvement, or general G3/H1/H2.
It does not qualify a clean lineage or set MECHANISM_FROZEN_V0. The relevant
interfaces and broader tests remain necessary.

## Cost and excluded attempts

Accepted evidence contains 15 fits, 5,400 updates, 21,600 presentations and 288
readout calls. Five prior excluded fits add 1,000 updates and 4,000
presentations, with no extra readout calls. Thus actual all-in physical work
is 20 fits, 6,400 updates, 25,600 presentations and 288 readout calls, exactly
within the revised prospective cap. Excluded work is counted once, not
recovered as accepted primary evidence.

The three learners' recorded outer intervals sum to 6,212.651042 seconds,
including 958.121959 seconds of prior failures. This is not campaign wall time
or GPU-kernel compute time. Successful followups took 1,445.287808,
1,427.124744 and 1,425.905469 seconds for seeds 0, 1 and 2 respectively.

Seed0 attempt5's B200 fit was valid at the fit level but excluded after its
terminal readout-preworker interruption. Attempt6 ran all four fits/readouts
afresh from the original measured A200/C0; no terminal-root checkpoint was
carried forward. Earlier failed attempts and the unlaunched manual-continuation
proposal remain preserved. The helper argument repair before attempt6's
scientific start performed no fit/model call.

## Reproducibility pointers

- Seed0 final root: `pcfl_sequence_v2_followup_seed0_20260913_attempt6`.
- Seeds1/2 final roots: `pcfl_sequence_v2_followup_seed1_20260913_attempt5`
  and `pcfl_sequence_v2_followup_seed2_20260913_attempt5`.
- Node2 parent directory: `/localhome/local-rohing/astra_diagnostics/`.
- Final reduction completed at `2026-09-13T21:17:11.935123Z`.
- Final receipt FILE SHA256:
  `49dad92b29779ccbcd346deba243ab81e38e34d1288f67936050c0f752a5ee1f`.
- Final receipt sealed digest:
  `901b063f0d1cfd279f42f0e3b86e679599377c8496016c576f3e2385dd0a463d`.
- Local full final-root/source archive:
  `gpu_artifacts_local/pcfl_v2_final_three_seed_20260913_attempt1/evidence.tar`;
  3,336 members, node2 and VM SHA256 both
  `e0492b7ec5c5034490ee19c848a36b40884a780d4675ffd4749cca407b7f7438`.
- Acquisition and excluded-attempt archives remain separately required as
  linked in the handoff. This is not a standalone model/environment backup.
- Operator/reducer commit: `3f4c03bc80298d5fd1062db49fbe26174fdc1b34`.
- Immutable native science: warmfix4, unchanged during all final runs.
- Raw reducer full changed suite: 13/13 PASS, 588.534 seconds; native prior
  failure check and per-phase input preparation passed before launch.
- Reporting code: `gpu/astra_pcfl_event_sequence_v2_report.py`, committed
  at `fd9cc2b2`; 12/12 presentation/consistency tests passed.

Re-render the table without rerunning models:

```bash
python3 -B -m gpu.astra_pcfl_event_sequence_v2_report \
  --receipt gpu_artifacts_local/pcfl_v2_final_three_seed_20260913_attempt1/reduction.json \
  --receipt-sha256 49dad92b29779ccbcd346deba243ab81e38e34d1288f67936050c0f752a5ee1f \
  --output /tmp/event-retention-v2-report-fresh.md
```

The output path must be fresh. This presentation command checks the recorded
receipt, not the original remote files; use the pinned raw reducer for custody
validation with the preserved source paths and complete evidence dependencies.

## Next decision

Stop additional singleton-bank dose/rank/prompt scouting. Use this bounded
replay result as a component input to the controller/memory junction design,
not as evidence that the junction already works. The next critical work is
the existing Stage2A controller material/source contract, then same-adapter
controller preservation and child-authored OLD/NEW causal use under the
adopted two-SLEEP contract. The currently implemented parser, synthetic
allocator, and independently checked symbolic ledger are partial prerequisites,
not an integrated pilot or a completed developmental campaign.

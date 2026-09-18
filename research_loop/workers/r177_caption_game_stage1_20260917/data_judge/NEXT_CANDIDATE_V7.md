# V7/V8 bounded development contrast — September 17, 2026

Builder implementation under Main/Astra's delegated standing scope, not a new
human ratification. No conceptual review queue. V6 is frozen, not promoted:
tau=null, and its portable checkpoint is diagnostic-only.

## Evidence and predeclared decision

- V6 model-selection q-rank: selected step100 0.0436587; step2000 0.0806930.
  These model-selection observations motivate sampling/selection changes, not
  audit tuning. No retrospective checkpoint promotion or tau reduction.
- Owner-side threshold oracle: 448 registered threshold rows, top-ceil(5%)=23,
  maximum mean positive vote mass 0.3477571973 > fixed 0.30 objective.
  This is feasibility under perfect ordering, without the fit filter, not
  achieved precision. Receipt SHA
  `00d4e72acd7c8c9634baf7793d2d3c7749f29514f22fde5c72a6b9770ef42784`.
- Fresh pretrained initialization for each run, identical source/data/seed,
  per-contest shuffled no-replacement paired sampling. All eligible fitting rows
  in the 180 joined contests enter the candidate corpus, rather than 64 per
  mean-rating tertile. 82 train and 11 dev missing-description exclusions remain.
- V7 auxiliary coefficient 1.0, V8 paired coefficient 0.0. Preserve capped-vote
  smoothed three-class soft CE. Auxiliary is weighted squared error between
  same-contest predicted q differences and the same smoothed-target q differences;
  pair weight is the minimum capped vote weight. No new model forwards.
- Each run: 5,000 steps, batch16, at most80,000 distinct humor rows (not all1M
  rows and not a full epoch), evaluation every250 steps, max1,800 elapsed seconds.
  Original allocation/lease end is unchanged; each requires fresh strict
  physical2 UUID/minor confinement, seven denied foreign minors, current clear
  capacity, own bound CPU/provenance gate, and enough remaining allocation.
- Humor selection maximizes macro within-contest Spearman on model-selection,
  then minimizes soft CE as tie-breaker. Scene-fit independently selects using
  synthetic balanced accuracy/recall on that same registered selection pool.
  Record the selected age of each head separately from total optimizer steps.
- Temperature calibration and fixed0.30/5% tau objective stay on their registered
  disjoint development partitions. No modification from arm/audit outcomes.
  Report both pre/post-temperature q spread, training-only prior baseline on
  model-selection, absolute stress delta, coverage and vote-mass proxies.
- Reusing development is explicitly PROVISIONAL, not fresh independent-test
  evidence. Locked validation and FINAL stay unopened. Second blind comparator
  remains incomplete; no acceptance-success or top200-precision claim.

No warm start from v4/v6, no changed learner/vision/similarity source, no hosted
vision/provider call, no automatic retry or extension. A failed candidate is
preserved. Actual gates/starts/completions remain separate receipts.

## Portable v6 handoff

`PORTABLE_JUDGE_HANDOFF_V6.json` SHA
`60e7e060fb6a798fb65deb064ab275d222b1a2ad8fa2f32ca0b42ebfdc36094c`.
Local `portable/released_all_v6/judge_config.json` SHA
`d454a39d54ccd830089554c5f8828bb8b330f7fdb37b2654bc8ecb1ab56f55a1`;
safe `PUBLIC_SCORING_REPORT.json` SHA
`571b05c1e24eb18bcb1f9c9733c68a80e0f5b28904a79ce4789c2bb2fb09c7f9`.
Frozen runtime included; no captions/private error cases/contest identities.
`load_cpu_judge` intentionally refuses its null threshold. Image release is
owned/completed by Main; Ampere performed no image upload.

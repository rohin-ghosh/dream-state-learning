# Physical3 exact journal replay blocker — 2026-09-18 05:21 UTC

Root: `/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/SCALE_physical3/life`.
Ready receiving source: sibling `r210/source`; control: `r210/control`.

Main caption client SHA1978a3541323e7b607f5b5c66bfc70707b0af4e71d25b5b31f888f35ccd80a4a
is installed, with only `ny_caption_data.py` and a two-line scoped guard activation.
The actual public CHILD_ENVIRONMENT was fetched; no private scorer references read.
Operator environment opener02931fd2254f4651b3b820120755fd3d is preserved in inbox.

The first pre-native scan rejected only `process_identity_drift:15739`, physical3
0MiB. Existing retry helper archived that failed scan and repeated unchanged
admission. The second scan passed. Native then failed before LOADED during journal
replay, not model generation: `r195_actual_raw_review_required`.

Failing receipt: record366, COMPLETE57, SHA
`7e260f9e6f1fc70a810dfbd1e08b07111860f62db946a91938abb198c0dc652b`.
Its zero-step reason remains `no_eligible_child_rows`, subreason
`review_target_filters_excluded_all_rows`; latest record remains TERMINAL368.
Checkpoint57 and the full prior state are untouched, with no rollback.

CPU-only direct recomputation, using prior COMPLETE56(record335) frontier:
- Recomputed post-code retained NEW/REHEARSAL:0/0.
- Code-filter proof exactly matches the persisted receipt.
- Excluded rows exactly match the persisted receipt.
- Review proof common keys differ ONLY at `prose_target_filter`.
- Therefore stored eligibility authorization digest differs on replay.
- Receiving `organism_v6/orch_r194_code_target_filter.py` SHA
  `b42bb51df51f9102fe0d3f4e934ce839d92224261ef0c7b86db5cfc3cc09c168`.

Required next action: Main's source-compatible historical proof reconstruction,
not weaker validation or historical receipt rewriting. Native EXIT1 evidence is
preserved. No subsequent automatic retry occurs. Main GPU0 scorer remains live;
vision GPU1 and original kernel GPU4 remain untouched.

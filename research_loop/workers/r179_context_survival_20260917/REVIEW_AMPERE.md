# R179 scoped runtime review — Ampere

Observed: September 17, 2026, 17:10:40 UTC / 10:10:40 PDT.

**Finding: no concrete reachable runtime, masking, history-loss, or journal
transition defect found in the reviewed patch.** This is an independent scoped
code finding, not a new approval gate, receiving-source admission, or evidence
that a live successor has loaded or completed sleep. No core files changed.

## Exact reviewed bytes

- `gpu/orch_r179_context_survival.py`:
  `b36949c2d93662b876b6519eee9dddba0e5af94a294e1f570f37685cd9604a2b`
- `tests/test_orch_r179_context_survival.py`:
  `f5214c89df86ddead9e0a3a572552eda2b8d7f8f6ab507605dc4d7e9bce0ce65`
- Native baseline `gpu/orch_r125_continual_native.py`:
  `cdb54252763472fd21ea12fd7694b208d968422c375dbf0647088cde736e6d48`
- History `organism_v6/orch_r124_train_history.py`:
  `0c336e3c9d3f5fbcfa3446287b24f554052cd57ec5330fb1d4a84f5e0894dd91`
- Stream `organism_v6/orch_r125_continual_stream.py`:
  `617e3ecd0bb45b35f0193ecd391bee21d0d86b2b32024ac5fe178fee13884c09`
- Journal `gpu/orch_r125_stream_journal.py`:
  `3925a6dff44c71994d446445833207ba3b4a9c8a983b56a8f3e3de84239eb0ca`
- Local plain renderer `organism_v6/orch_r125_plain_context.py`:
  `dcfd1f7f5584867e39356f336f53bb7222aeb535da87d5ecb8f1f0bb59f72feb`

## Actual CPU checks

Ran locally with synthetic TRAIN fixtures only:

```text
TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s tests -p test_orch_r179_context_survival.py -v
9 tests passed; 2.411 seconds reported by unittest.
```

Also ran seven inline synthetic cases using that test module's real stream and
journal fixture. Four used exact token counts 12,287, 12,288, 12,289, and 15,872;
each checked the expected retain/compact decision, full journal latest-checkpoint
equality before sleep, journal equality after completed synthetic sleep, and
unchanged history across sleep. Two checked empty summary and no-distillation
at 15,000 visible tokens, including unchanged view, exact row-count change and
journal/sleep checkpoint equality. One reconstructed the entire old native source
by reversing only the two-line replacement. **Seven of seven passed.** These
counts are separate from Main's reported 108 tests plus 145 subtests; that larger
suite was not rerun or claimed here.

## Findings by concern

- **Token pressure:** `threshold_tokens` is `min(3*limit//4, limit-segment)`;
  it is 12,288 for the scoped 16,384/512 configuration. The helper measures the
  rendered presentation, not raw journal bytes, exactly once. Equality compacts.
  It uses nonmutating `history.render`, not the eviction-enabled stream renderer.
  Ordinary pre-generation hard-window eviction remains possible and unchanged;
  this is not a promise that all historical context stays visible indefinitely.
- **Empty summary:** the existing caller bypasses the new helper, preserves the
  actual empty target and emits `COMPACTION_SKIPPED`. No invented summary or
  new view operation is introduced, including the tested pressure case.
- **No distillation:** the existing early return stays byte-identical. There is
  no new generation, target or context-policy record. Absence of
  `CONTEXT_RETAINED` alone is not evidence of failure on this unchanged path.
- **Masks and history:** retain does not mutate the history checkpoint; compact
  advances only a visible-history operation while retaining raw events and the
  actual own response. Existing prefix masking and own-target loss stay intact.
  Both ordinary and corrected-retelling callers passed the supplied tests.
- **Journal/receipts:** the own generation is already durably `COMMITTED` before
  the helper. `CONTEXT_RETAINED` is metadata, intentionally not a new authoritative
  checkpoint. Its before/after history hash is consistent with that committed
  state. The compact branch emits the existing authoritative `COMPACTION` kind;
  real journal validation accepts its history-operation-only transition. Neither
  record proves optimizer work; use the actual `SLEEP_REQUEST`, completed sleep,
  and restored stream/checkpoint evidence for that claim.
- **Exact source delta:** the regex requires one exact old two-line block,
  rejects already-patched/zero-match source, verifies inverse byte reconstruction,
  and compiles the result. This is a narrow transformation, not a source-root
  hash allowlist. Actual receiving old-source pins and successor inventories
  remain the caller's responsibility; no broader source approval is inferred.

## Limits, not additional gates

No remote calls, learner journals, sealed contents, provider calls, GPU work,
signals, or learner changes were used. The reported 24-life source census and
14-native/2-invitation-only/8-inline distribution were supplied by Main, not
independently re-collected here. The local plain renderer pin above must not be
relabeled as the different `b385...` deployed closure. Node-local receiving tests
and Main's existing lifecycle checks cover those actual closures. The standalone
tests use synthetic token counters, not a receiving tokenizer throughput test.

## Appendix — preserved R177 DATA/JUDGE status

At this handoff the Stage1 data/judge suite has **105 passing CPU tests in
7.27 seconds**, synthetic fixtures only. Receipt:
`research_loop/workers/r177_caption_game_stage1_20260917/data_judge/evidence/CPU_TESTS_20260917_v2.txt`,
SHA `b9630266cbbc09663bbf0b882935f954beafc96372c133bdea6022f03aa9112c`.

Current WIP source pins, not GPU/model-validation receipts:

- `gpu/ny_caption_data.py`:
  `ec2b0ed8181649938784130c071046c31eacb42630e7f7c7d1e11597692c6bd3`
- `gpu/ny_caption_judge.py`:
  `f2c91f73cfdcb4e7bfa6f04478ebf6d8b432f6039275c4bfa4fb3d115a55b157`
- `tests/test_ny_caption_data.py`:
  `1a1ebe8b2ffe734c17a2617effbd7361ad8a6f47003e802187e5290fd4e164f7`
- `tests/test_ny_caption_judge.py`:
  `6e38f948a1f7f325342a5ec1054291036c27c11f119e4c1b7ee2ba6e5817cc18`

Prepared data: 378 eligible contests, 377 scene groups, 2,176,576 retained rating
rows. Pool counts are 262 train / 56 dev / 38 validation / 19 agent-development /
3 reserved FINAL. No historical caption text or FINAL identities are disclosed.

Bacon's image-only local-Qwen task packet is ready:
`research_loop/workers/r177_caption_game_stage1_20260917/data_judge/IMAGE_TASKS_agent_development.private.json`,
SHA `482ee743952441bf8d5acf1156cfcdc69f9ff0d8b3e5d6a2e3493252788bf302`.
It contains 19 tasks, not completed canonical descriptions or a scored game.

**Remaining:** actual local-Qwen description receipts (zero attached here), bound
receiving pretrained-model/package proof, Main capacity admission, actual judge
training/checkpoint, and second blinded local-model validation. No trained
checkpoint or GPU/model/provider execution is claimed. No human-panel blocker;
DEVELOPMENT remains matched learning PARENTED/UNPARENTED, FINAL deferred. R177 WIP
and prior failed data preparations are preserved; judge work resumes next.

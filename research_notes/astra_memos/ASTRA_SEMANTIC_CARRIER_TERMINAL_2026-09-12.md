# SEQ-080 — native semantic carrier passes its bounded surface test

September12,2026. Run `astra_semantic_carrier_20260912_attempt1`, source
241dd86e0e95b85a0359ca3807c134350d1c4955. Frozen four root-map cells each
score16/16 correct by greedy generation AND complete-candidate scoring.
All64semantic outputs are valid, with zero truncations/multiple actions;
complementary swaps32/32 for each operation; generation/scoring agree64/64.
All16copy calls pass, representing eight distinct prompts repeated per root.
This establishes only the specified exact-row native-action surface, not a
trained writer, memory, retention, parenting, H1/H2 or clean lineage.

The exact prepared144requests produced144records:80generations and64scoring
requests, with128candidate forwards and960finite response-token log-probabilities.
All four balanced confusion matrices are diagonal. Full-sequence target-minus-
alternative margin ranges6.060128182–22.906309813nats, mean13.392726735.
Candidates have8/7tokens including LF+EOS; every token is summed without
length normalization. All80greedy strings omit LF and end directly with
recorded EOS. That passes the declared ASCII-edge-whitespace parser, but does
not demonstrate greedy LF emission. Target LF itself has mean logprob−26.9495;
scoring margins include these suffix costs and are not raw model confidence
over every possible action string.

Main's original-source, CPU-only remote replay succeeds and matches the report.
Goodall independently checks157run files, exact156-member seal, request/record
bindings, material/prompt reconstruction, all counts and complete numeric
reduction. Independent review does not locally tokenize or rerun model logits.
Actual native preparation checked tokenizer/backend before execution. All
prepared prefixes fit138tokens or fewer, with32generation headroom within2048.

Controller93084 ran on node3GPU0, execution start12:35:53.327233UTC,
finish12:38:03.960816UTC,130.633576379seconds including validation/setup.
Owned timeout supervisor93136 cleanup succeeds; recorded worker93137.
Main observed controller/supervisor absent and full GPU/XML/CUDA/queue-free
check at12:40:05UTC; GPU0reservation released. No manualkill or other work
displaced. This is not a newly verified adversarial/cgroup guarantee.

Evidence under `receipts_20260912/`:
- `astra_semantic_carrier_terminal_20260912.tgz`, SHA256
  `053bea4b16428d401d5e7532fc2c68d8cd91063d90e31bb6fc1a9a9526c478ad`.
- `astra_semantic_carrier_replay_20260912.json`, SHA256
  `e99f4ca68fc720fcea0d602ae2d562bdfc7306354fccb055a97b1ac7036df3bd`.
- Independent review JSON SHA256
  `14e044e983c16b5649133c33598dfaa3a8239aab10e9c3c943598c28fa8c730f`.
- External cleanup observation SHA256
  `176b488eadc404f15d3cafdf2dc392a5dde3d4ea49e5696a8503a82d9c0b058f`.

Main selects a separate fresh semantic-Q0 conditional-writing comparison next.
Carrier roots/rows never become its training, primary or locality data. No
automatic fits or post-hoc threshold changes occurred. Local model hashes do
not authenticate official origin; the final C11 guard remains deferred.

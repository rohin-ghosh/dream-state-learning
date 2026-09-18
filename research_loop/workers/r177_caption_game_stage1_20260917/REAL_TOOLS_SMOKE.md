# Real scoring-component wiring smoke

Main, September 17, 2026. This is an invariant-preserving R177 DEVELOPMENT
integration check, not a new learner launch, judge-validation result or FINAL run.
The real command is `python3 -m gpu.ny_caption_stage1_tools --bundle PATH
--bundle-sha256 SHA256 --actions PATH --actions-sha256 SHA256 --output NEW_PATH`.
Both input paths are absolute, hash-bound files. An existing output directory is
rejected. There is no synthetic provider, score, embedding, threshold or vision
fallback. This command does not generate child text or run sleep updates.

## Required bundle

The bundle schema is `NY_STAGE1_REAL_TOOLS_SMOKE_V1`, mode `DEVELOPMENT`, with
`agent_id`, `lane` (`PARENTED` or `UNPARENTED`, metadata only), a loopback-only
`visual_endpoint`, `game`, `judge_budget`, and six path/SHA256 references:

- `game_manifest`: the existing game-only projection, exactly three
  agent-development contests, canonical neutral descriptions and image handles.
  No historical captions, answers, private labels or FINAL identities are needed.
- `judge_config`: the corrected trained classifier's frozen artifact. A null
  acceptance threshold, changed source or changed checkpoint fails closed.
- `similarity_runtime`: the calibrated frozen sentence encoder/pixel artifact,
  including its encoder manifest and required same-joke verifier.
- `vision_packet`: the local-Qwen image-only packet matching those image handles.
- `tokenizer_manifest`: schema `NY_CHILD_TOKENIZER_V1`, model ID
  `Qwen/Qwen2.5-7B-Instruct`, exact revision, canonical root, and SHA256 file map.
  The root contains only tokenizer.json, tokenizer_config.json, vocab.json,
  merges.txt, and optionally special_tokens_map.json/config.json. Counts use
  the actual child tokenizer, not words or classifier tokens.
- `verifier_scope`: a separate `agent_development`, verifier-only bounded scope,
  with the agent's exact namespace, zero label/pair-label calls, no retries and
  at most 32 verification calls. The TRAIN annotation budget is not reused or
  relabelled. Credentials are inherited privately, never written to this bundle.

`game` uses the classifier's frozen tau, zero transport retries, at most eight
visual calls and eight submissions per contest. `judge_budget` explicitly caps
CPU scoring at no more than 64 model examples, 32,768 padded model tokens and
600 seconds. Both classifier heads and the frozen sentence encoder run on CPU;
the already-admitted local Qwen service owns its separately bounded GPU budget.

The actions document contains only `mode: DEVELOPMENT` and a list of one to
eight explicit `inspect_image`/`submit_caption` actions in the existing grammar.
Every action must target the released development allowlist. The smoke stops on
the first tool error, preserving the request, environment result and game
snapshot. It does not replay possibly dispatched work. Each output is private.

## Status and limits

The CLI and eleven new CPU regression tests pass; the combined component suite
passes371 tests and66 subtests. Real execution is pending a usable
judge artifact (v6 trained but has no qualifying acceptance threshold), three
local-Qwen canonical descriptions/image handles,
live local service and development-verifier scope. This is an explicit component
wiring command, not a claim that either matched continuous learning loop is
already running. A successful smoke proves tool wiring only; judge reliability,
pixel merge/split errors and retained-learning evidence remain separate.

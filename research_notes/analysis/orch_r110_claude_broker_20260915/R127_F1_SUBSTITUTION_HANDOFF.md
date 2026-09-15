# R127 F1-only prospective model substitution: CPU ready, consumer blocked

Observed 2026-09-15T20:15:25Z. This is an explicitly authorized F1 route-only transport/attribution repair, not a change to the requested parent, head, visibility, scientific prompt, or historical verdicts. No Git operations, provider probes, credentials, GPU changes, process signals, or live broker replacement were performed for this candidate.

## Frozen source and tests

- Broker `gpu/orch_r110_claude_broker.py`: SHA256 `704df1d4184be7444daec4c5ccb29c65bc4969ab773d8e7cccb80f1a8011064b`.
- Tests `tests/test_orch_r110_claude_broker.py`: SHA256 `dc3bcf3a5d7d416b42f0a2803b555ba3726ee9a7560e87edc0c94269eed07d8b`.
- Local and node5 each **111 tests PASS**: `python3 -m unittest discover -s tests -p test_orch_r110_claude_broker.py -q`.
- Native log SHA256 `7ab2c5fa0acdb3f2e4a8cde0112db3ff54c5ee48c4d906ab801bac93f0067bec`.
- Native frozen candidate `/localhome/local-rohing/orch_r127_f1_substitution_20260915_v1/source`; no subsequent edits to those bytes.
- `CONFIG_CANDIDATE.json` in that runtime: file SHA256 `aa2abe0e496c5334f68ccc8c21d8108c378fd1a3814341de7dd1e66a6a0295d4`, canonical config digest `ab875529125f4c7279efe2a729aa1907cd57d24830af9b6bf4ec0a943d7521c1`. Candidate only, no launch receipt.

## Exact wire and scope

Both CLI `--allow-f1-route-substitute-model claude-opus-5` and config `allowed_substitute_models: ["claude-opus-5"]` are required and must agree. Only `branch=F1, family=route` permits the opt-in; all defaults/other branches remain strict. Head source/config is untouched. The requested CLI model remains `claude-fable-5-1`, LOW, unchanged tools-empty/max-turns1 and existing lane cutoff.

Successful substituted responses retain `requested_model`, truthful `actual_model`, the full actual `usage.model_usage`, and `model_attribution` with `status=SUBSTITUTED`, the usage digest and `fable_parent_claim_eligible=false`. The same attribution is exposed in parent metadata and publication metadata. The exact route plan shape remains `speak/message/rationale`; only parent-only rationale gets an explicit substitution label. Child-visible guidance is unchanged. SILENT remains SILENT, with substitution attribution. No silent trimming or historical reclassification.

`verify_response_model_binding(response, raw, 'route', task_id, branch='F1', allowed_models=['claude-opus-5'])` re-parses and compares plan/model/usage/attribution after the consumer has independently verified the node archive. It does not replace request identity, deadline, source/cohort, archive hash or lane validation.

The regression uses the actual C17 model-identity/usage metadata (Opus plus its Haiku companion) with a **synthetic** plan, not a historical failed-plan revalidation. Tests reject unknown/ambiguous model sets, canonical conflicts, wrong branch/family, config/CLI disagreement and raw/plan/identity/usage tampering. Five old MISSING response/stdout hashes are recorded unchanged in the compact receipt. No old claim is eligible for replay.

## Required route-owner boundary

The actual frozen consumer `/localhome/local-rohing/orch_r121_route_independent_20260915_v2/source/gpu/orch_r121_route_independent.py`, SHA256 `d1b0de12edc1ad45bbc1b3d20def7f0084198310ef0a7c9ee2db3f6bc6095673`, still rejects `response.actual_model != plan.provider` as `provider_identity_mismatch`. Therefore truthful Opus broker publication alone cannot establish native consumption. Do not change `actual_model` to Fable or mutate the running child's frozen source.

Main/Poincare must supply the compatible prospective route-consumer runtime/release/terminal binding. It must preserve truthful requested/actual identity and SUBSTITUTED attribution in observed/applied receipts, retain the raw join and all existing lane checks, and exclude substituted replies from Fable-parent-only claims. A matching source hash alone is not evidence of live consumer activation.

At observation, existing owned F1 broker **3825740**, PPID1, matched its recorded full identity; **84 claims**, no unpublished claims or pending requests, no terminal. It remains running unchanged. This is a point-in-time observation, not an ongoing quiescence guarantee. Queue root `/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_0_attempt1`; current terminal `R121_INDEPENDENT_TERMINAL.json`.

After compatible owner handoff, recheck identity/quiescence, fence the exact idle broker, take the branch provider lock, verify all claim hashes, retire only that predecessor and start one successor with explicit matching opt-in. Preserve queue, caps, terminal provenance, LOW, prompt files, credentials and all old charges; settle PPID1 before identity publication. Record first genuinely new published COMPLETE/SILENT separately from observed/applied consumption and latency. **Neither a new delivered nor a consumed substitution has yet been observed.**

## Publication allowlist

The adjacent `R127_F1_SUBSTITUTION_STAGE_READY.json` binds only the broker, its tests, this handoff and compact native CPU/custody metadata. No raw responses/prompts/tasks or unrelated source files are included. Main alone owns Git/publication. The TRAIN recipe addendum remains parked until this live-consumer dependency is resolved.

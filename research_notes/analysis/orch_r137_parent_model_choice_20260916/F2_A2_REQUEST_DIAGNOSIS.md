# R137 A2 pre-dispatch request construction diagnosis

September 16, 2026, 02:07:57 UTC bounded node observation. F2's consumer block remains unchanged. No live source, watcher settings, model configuration, credentials, processes, claims or historical outcomes were changed.

## Exact CPU-reproduced cause

The running A2 broker uses frozen `gpu/orch_r110_claude_broker.py` SHA256 `6d2dc623cf1e7000175de78160d6f791ac040ad3679bbd6ae852529b8db1cb99` under `/tmp/orch_math_feedback_uptake_r121_astra_source_20260915_v1`. Its `head_binding()` line 305 calls `render_parent_prompt()` line 269. The renderer requires exactly five head fields; the current F2 settings also contain the already-supported optional `NEXT_GUIDANCE` field. CPU-only parsing of the current prompt/settings deterministically raises `ValueError: head_fields_keys`, before any HTTP request or model invocation.

Current prompt SHA256: `0868d557211e352d64f8cd84ab72abd13fc075664022bc9734fb80429f73f38f`; fields SHA256: `80aef38460ce03fab175fea3c092997faae5f6ae3aef35255de3f84cc8723bb9`. No field values, prompts or transcripts are reproduced here. This is a current-input reproduction; historical generic exception receipts do not independently retain the exact exception text.

## Existing narrow fix and tests

Repository `gpu/orch_r110_claude_broker.py:312` already accepts exactly the original required fields plus optional `NEXT_GUIDANCE`, validating its type and UTF-8 length <=1024. Its `build_system()` at line 387 adds a hash-bound applicable note to the parent system, preserving the fixed template and excluding stale mismatched settings. The current repository parser returns `BOUND_REQUESTED_SETTINGS` on the same current F2 input. Repository source SHA256 observed: `f3fc5b3fd49473f40e78c97294317859bfb0c086b270e05d37e2be3eae54a054`.

Two existing CPU regressions PASS (mock provider only, zero real provider calls):

- `tests/test_orch_r110_claude_broker.py:145`, `ClaudeBrokerTests.test_async_next_guidance_bound_to_exact_prompt_without_template_changes`: bound note, unchanged fixed template, stale-note omission and oversized-note rejection.
- `tests/test_orch_r110_claude_broker.py:959`, `ClaudeBrokerTests.test_serialization_contract_follows_async_head_note`: note precedes the transport contract.

Intended future patch target is a NEW immutable A2 source copy of the frozen broker's `render_parent_prompt()` and `build_system()` only. Backport optional-field validation plus applicable note insertion/hash metadata; preserve the frozen transport contract, provider, low effort, budgets, timeouts, source validation and claims. Do NOT replace the entire frozen broker with repository HEAD: HEAD contains other unrelated changes. Do not drop the valid note, edit watcher-owned fields, retry a failed request, or use a fallback provider. A bound immutable source manifest and broker-only handoff would require Main's subsequent publication; no ready-to-launch candidate is claimed here.

## Actual recent delivery, bounded sample

Latest 20 native `parent_delivered` receipts by file modification time: **0 COMPLETE, 0 SILENT, 20 MISSING**. Native receipt timestamps span September 15 23:46:00 through September 16 02:06:41 UTC. Last identifier: `R121_C000037_E1_experience`.

Separately, latest 20 published response receipts: **0 COMPLETE, 0 SILENT, 20 MISSING**, all `construct_request / ValueError / captured_astra_failure_no_retry`, all `provider_dispatched=false`. Publication timestamps span September 15 23:32:46 through September 16 01:53:48 UTC. Publication and consumption are separate cohorts, not assumed one-to-one by ordering.

A2 counters advanced from native=856,parent=98 to native=882,parent=100; optimizer_steps=14169. The child is advancing despite failed parent construction. No broad history or raw reflection scan was performed. No new adapter was needed to identify the existing compatibility repair; none was staged or launched.

# R227 future Tool-feedback seam; Main owns live relay

Non-material presentation repair, CPU tested only. No native/scorer/P3 process
control, no P3 inbox publication, no live cached-source edits, no scoring change,
no training eligibility/filter change, and no historical ACT resubmission.

## Exact failure and repair

`gpu/ny_caption_life.py:activate` previously put `json.dumps(actual_result)`
directly in an environment/feedback TrainEvent. Real envelopes contain
`receipt_sha256` and nested `source_sha256`. The existing plain-context
`has_scaffolding` recognizes those strings and removes the whole event from
REQUEST and replay. The repository-specific Tool exception does not admit an
unprefixed caption envelope. This reproduces in a regression test, rather than
being inferred from absent visible ranks alone.

The future hook uses an attributed **Tool** projection with per-caption rank,
cutoff, acceptance, novelty status, cache flag, relevance/threshold, source
stage/span, response digest and scorer receipt digest. It omits raw transport
paths and repeated scaffolding, not actual result values. Full original
`R184_ACT.outcome.environment` and original scorer RESULT bytes/hashes stay
unchanged. The TrainEvent source digest still binds the full original result;
R184_ACT additionally binds the projected view. Environment text remains masked
context, never a child training target. Descriptive labels do not exclude child
LEARN rows. Clarification is attributed observed tool data, not an authority or
new runtime-control channel.

## Main's immediate relay API

`caption_feedback_payload(actual_result)` returns the child-safe dict; serialize
it once as JSON when your existing Tool-INBOX publisher adds its own `Tool: `
prefix. `attributed_tool_feedback(actual_result)` returns the already-prefixed
string for a native environment/feedback TrainEvent. Do not double-prefix.
Import from `gpu.ny_caption_life`; bind the actual scorer RESULT/source origin
through your normal source-bound relay. No invented schema or native origin.

The source delta and hashes are in `R227_FUTURE_TOOL_FEEDBACK_READY.json`.
35 focused tests pass: the old envelope is dropped; the new Tool view is present
in actual generator arguments, masked row prefix and replay; the raw result is
unchanged; ACT/THINK attribution, semantic repeats/cache and unknown results are
not reclassified. This does **not** prove adoption by any running life. Main
alone owns live P3 Tool-INBOX relay and its first rendered REQUEST proof.

## Actual reporting, not prepared-only

Read-only local scheduler PID218252 was dispatched08:57:41UTC and actually
published `R227_HOURLY_20260918T085746Z.{json,md}` at08:57:46.076790UTC.
`R227_HOURLY_LATEST.json` is authoritative for subsequent publication. Cadence is
each absolute UTC hour, plus09:36:33.658195UTC for the five new lives' first
elapsed hour; schedule upper bound14:09:07.497640UTC. No shared COORDINATION or
Main audit-file writes and no pushes. Public tables contain seven player rows
per applicable window, explicit attempt units/denominators, partial-hour flags,
raw-string/literal-review caveats, and no raw captions or physical host names.

Per-cycle continue/branch/stop observer implementation is not assumed here;
Main will coordinate its disjoint scope. No life-control action is implied by
this reporting or by a score/routing result.

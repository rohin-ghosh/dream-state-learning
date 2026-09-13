# Projected formation paired capsule analysis — EDITSTOP

Bounded interface-author reproduction, **not independent review**. CPU implementation
only; no native/result reads, models, tokenizers, GPU/process/queue queries, network,
Git, source edits or driver edits. Actual AUTH/OFF inputs remain unread. Main must
declare both closed before using this analyzer. No science verdict or launch.

## Owned files / stable API

- `/tmp/astra_projected_formation_analysis_20260913.py`
- `/tmp/test_astra_projected_formation_analysis_20260913.py`
- `/tmp/astra_projected_formation_analysis_handoff_20260913.md`

Public function (keyword-only, JSON-compatible return):

```python
analyze_pair(
    auth_archive=AUTH_CAPSULE,
    auth_validation=AUTH_VALIDATION,
    auth_validation_sha256=MAIN_PINNED_AUTH_VALIDATION_SHA256,
    off_archive=OFF_CAPSULE,
    off_validation=OFF_VALIDATION,
    off_validation_sha256=MAIN_PINNED_OFF_VALIDATION_SHA256,
    source=REPLAY_SOURCE,
    both_closed=True,
)
```

`both_closed` defaults False and is checked before input reads. It represents Main's
authorization, not a native state query. Both validation receipts must independently
say complete AND fully released. No one-mode analysis or incomplete promotion.

Input format: the explicit archive and external validation from
`projected_auth_off_rulegame_formation_run_v1_20260913` collection. Archives may be
relocated: recorded native root paths are evidence labels, never traversed. No need
for native model, adapter, fit root, original driver, or external dependency scripts.
`source` is a local checked copy matching the captured frozen role/source hashes
(Main source `830fe675ec16bdbe4c0a5dc36ec66908b28da6ce`). Importing a cached role from
another source fails instead of switching modules. Source replay is mandatory: if
unavailable or changed, no weaker verification status or fallback is emitted.

## Main command — only after BOTH closed

Set `REPLAY_SOURCE`, `AUTH_CAPSULE`, `AUTH_VALIDATION`, `AUTH_VALIDATION_SHA256`,
`OFF_CAPSULE`, `OFF_VALIDATION`, `OFF_VALIDATION_SHA256` to Main-reviewed paths/pins.
Use the trusted validation hashes, not hashes accepted from an unreviewed manifest.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/astra_projected_formation_analysis_20260913.py \
  --both-closed --source "$REPLAY_SOURCE" \
  --auth-archive "$AUTH_CAPSULE" --auth-validation "$AUTH_VALIDATION" \
  --auth-validation-sha256 "$AUTH_VALIDATION_SHA256" \
  --off-archive "$OFF_CAPSULE" --off-validation "$OFF_VALIDATION" \
  --off-validation-sha256 "$OFF_VALIDATION_SHA256" \
  --out /tmp/astra_projected_formation_paired_analysis_20260913_attempt1.json
```

Success prints output path/hash/status. Output is exclusive (`O_EXCL`, no symlink
leaf); existing output is never overwritten. Failure raises/nonzero, no aggregate
file, no automatic retry/substitution. Inputs are untouched; tar is never extracted.

## Checks and analysis

- External validation SHA, whole archive SHA before/after reading, every exact member
  SHA and complete inventory; bounded 32MiB/member, 256MiB uncompressed, 2048 members.
  Unknown names, duplicates, missing members, links and traversal rejected. Failure
  artifacts are not permitted in a completed capsule. Duplicate JSON keys rejected.
- Immutable plan/seal, binding, normalized completed genuine AUTH birth reference,
  source hashes, model pins, raw data manifest, exact journal pairs, timestamps and
  all-call capture barrier. AUTH and OFF require different roots but identical
  source, recipe/budgets, model, birth normalization and public binding evidence.
- Capture/terminal/receipt/supervision/launch/exit/collector-audit hash/content joins;
  worker/group/reservation release flags, process identity, cleanup, elapsed bounds
  and release chronology. Collection <=300s; controller <=900s; worker <=600s;
  cleanup140s; capture <=60 calls /18480 requested output tokens.
- Both capsules pass structural checks before either result is summarized. Frozen
  role replay then regenerates every request, action/world/event join and result;
  saved replay must equal this replay exactly. This preserves the strict parser,
  tentative invalid text, actual projected execution, route identities and grader.
- AUTH/OFF and P/A metrics retain exact frozen numerator/denominator definitions:
  original-valid attempts, projection recovery, final-quiz-valid tasks and record
  fidelity; zero denominators stay zero. Task rows and invalid/world/TRY counts
  retained. Report includes per-role token totals, per-call seeds/caps/routes and
  raw finish/stop reasons. Stop is not automatically called EOS.
- Exact parent and restatement raw call objects, source pre-task raw calls/events,
  and first apply request retain source/carryover evidence. The parent request is
  the exact input sent, including original transcript-tail truncation. Source
  events are analyst evidence, NOT additional parent-visible input. Raw capsule
  member paths are included for source inspection.
- Token and call totals can be summed across cells. Journal call seconds, worker
  reservation, controller, collection and launch-to-release seconds remain labeled
  nested quantities, never added into inflated cost or inferred A40-minute totals.

## Limitations / claim boundary

`parent_purity=UNREVIEWED_MAIN_JUDGMENT_REQUIRED`; `automatic_pass=False` always.
Main must inspect false recaps, restatement alterations, claim fidelity and actual
parent visibility semantically. Replay/hash equality does not automate that work.
Output status is `VERIFIED_AWAITING_MAIN_SEMANTIC_AUDIT`, not efficacy or acceptance.

Release is **pinned collector evidence**, not a fresh process/GPU/queue observation.
The final vacancy XML is outside the capsule: its external validation hash/summary
are reported, not independently revalidated. Native source/model/adapter bytes and
the upstream birth tree are not re-read; pinned reference identity is checked, not
ancestry re-authenticated. Source-authored NOT_CLEAN and historical local-origin
labels remain. No learning/retention/useful-write/parenting/H1/H2 claim. No native
compatibility claim until Main runs against actual paired closed capsules.

## CPU tests and hashes

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp:tests:. python3 -B -m unittest \
  test_astra_projected_formation_analysis_20260913 -q
```

16 tests PASS in10.701s. Synthetic archives only; real frozen CPU capture/replay,
including actual invalid-first then valid projection, exact tentative transcript,
raw/event and reducer tamper, source/schedule/model/birth/budget mismatches, two
individually valid but unmatched pairs, partial/release/hash/inventory/link errors,
closure-before-read check, and real subprocess CLI parsing/dispatch/no-overwrite.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp:tests:. python3 -B -m unittest \
  test_astra_projected_formation_analysis_20260913 \
  test_rulegame_action_projection test_born_rulegame_formation -q
```

59 tests PASS in13.161s. Repo source hashes rechecked unchanged.

- Analyzer SHA256: `30e69774098e60fb8ba57937147d2279023aaba98c6ac16964139f532bfffca9`
- Tests SHA256: `6ed589d600c19cc4117076f212c5c738fdfc1d11db5a5b75ef2bb7f7eb1685bb`
- Frozen role SHA256: `2cb24cf0447d3e5a7d8e61c9a0a65658e033f2c0bfc01b4b60ae15bce437a945`
- Frozen projection SHA256: `47564a630b166cadda546ac5ae65c79bd9ca223a8574b0cfc693d6bc0177ad19`
- Untouched diagnostic SHA256: `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`

EDITSTOP. Main owns actual closed-capsule authorization, native integration and any
subsequent semantic judgment, logging or archive.

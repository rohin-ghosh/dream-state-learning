# Projection ID hygiene — non-material forward repair — EDITSTOP

Scoped repair of an incidental prompt/control confound: harness-global call IDs
must not distinguish otherwise identical public states. No new learning behavior,
grader, parent visibility, parser, task budget or scientific claim. No launch or
v2 experiment selected; no old result reclassification. No result files read.

## Exact changes

Only two repository files changed:

- `organism_v6/rulegame_action_projection.py`
- `tests/test_rulegame_action_projection.py`

This handoff is the only new `/tmp` file. Role/diagnostic files, corpora, fits,
original drivers/analyzer, historical sources and native snapshots were not edited.
No Git/network/native/GPU operations.

Versioned opt-in:

```python
INTERFACE = "rulegame_action_projection_v2"
TASK_NAMESPACE = "astra-action-projection-v2-20260913"
```

Public markers now use only task-local response numbers:

```text
[UNEXECUTED_PROPOSAL response=1; no action dispatched]
<exact invalid raw text>
[END UNEXECUTED_PROPOSAL response=1; NO ACTION OR WORLD RESULT]
[PROJECTED_ACTION response=2 from_response=1]
<exact executed projection text>
```

`tentative_block(raw, tick)` no longer accepts a global ID. The pending proposal's
local tick is retained before clearing pending state. Full global `call_id`,
`projection_of`, execution and record source joins are unchanged in metadata.
Raw model text is never sanitized or rewritten, even if it happens to contain an ID.

Everything else remains: one strict same-child projection per invalid response,
second invalid terminal, same five wake slots, 400-token wake cap, strict original
parser and state checks, actual execution before record, untouched public world
outcomes, unchanged parent helpers and transcript-tail behavior. Parser aliases,
null forecasts and wrong predictions remain unchanged. No parent auto-certification.

## Role / replay integration

No role-file change is necessary. Existing dynamic calls work:

```python
role.make_binding(pin, expected_birth_pin_sha256=pin_sha,
                  interface=projection.INTERFACE, child_mode="AUTH")  # or OFF
role.source_hashes(projection.INTERFACE)
```

The unchanged role container schema is still
`born_rulegame_formation_action_projection_v1`; the explicit interface, fresh task
namespace and bound source hashes identify v2. Do not reinterpret that container
label as permission to replay v1 against current v2 source. New v1 task IDs fail
the current module's schedule check. Role capture/replay tests pass with v2.

Historical v1 must continue using `/tmp/astra_projection_replay_source_830fe675`
and the existing pinned analyzer/driver, not the current repository. Its projection
module hash was checked and remains the original hash. The new namespace changes
EID-derived seeds/quiz instances relative to v1, as intended by explicit versioning;
no claim of identical v1/v2 stochastic executions or panel instances is made.
Main owns any future driver/source version, matched experiment decision and launch.

## CPU regression evidence

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:. python3 -B -m unittest \
  test_rulegame_action_projection test_born_rulegame_formation -q
```

**45 tests PASS in 2.299s** (15 projection tests + 30 unchanged adjacent role tests).

New regressions:

1. Same public/raw/tick trajectory with global starting IDs 0017 versus 0044:
   all five wake prompts and final transcript/result are byte-identical. Covers
   multiple tentative and successfully projected markers with record calls between
   wakes. Metadata IDs remain distinct and every projection/record joins correctly.
2. Full deterministic formation fixture with invalid responses at ticks 1 and 3:
   P/A pre-task requests match for both lessons, excluding only non-prompt metadata
   `arm`/`call_id`; seeds, caps, temperatures, prompts and resulting native-like
   envelopes match. The tick-4 projection path is covered and full role replay passes.

Existing golden visibility updated only for the local marker/version. Existing
strict-parser, no-world-before-projection, budgets, termination, record truth,
AUTH/OFF routing, source checking, defaults and replay-tamper tests remain passing.
No native inference or independent scientific review is claimed.

## SHA256

- Projection v2: `9eeb962e9e2d7716bdbc9963dfdcccfc3219db52e852a00e8d8e655cdf68cbfe`
- Projection tests: `ab4c10491d373b72606a34608e8322215ac3fcf6cc94fbf2e3b450d57942c110`
- Unchanged role: `2cb24cf0447d3e5a7d8e61c9a0a65658e033f2c0bfc01b4b60ae15bce437a945`
- Unchanged diagnostic: `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`
- Frozen v1 replay projection: `47564a630b166cadda546ac5ae65c79bd9ca223a8574b0cfc693d6bc0177ad19`

EDITSTOP. Forward repair only; preserve all completed v1 artifacts and conclusions.

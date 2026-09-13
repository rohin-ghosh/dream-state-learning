# Endogenous action relay — bounded independent CPU review

**Core formation/admission/compiler: bounded PASS. One narrow supplied-replay
revalidation gap below; no full-runner or launch acceptance. EDITSTOP.**

Scope: inspect the new component/tests against the design memo and handoff, with
small synthetic CPU probes only. Main owns integration. No Q0 result was needed,
supplied or inspected. This review does not require a native writer, reset runner,
scientific scorer or deferred C11 framework inside this component.

## Reproducible finding F1 — shape equality does not revalidate the admitted replay

Location: `organism_v6/endogenous_action_relay.py:348`, particularly the structural
checks at354, raw-span checks at375, and returned digest at407.

`check_native_shapes` rejects several altered Replay fields, but a caller can
alter both AUTH/SWAP identically and still receive
`SUPPLIED_NATIVE_SHAPES_CHECKED_NOT_LAUNCH_AUTHORIZATION`:

1. In the first M0 row, substitute the same DREAM record's M1 action span/target
   into both arms. The unchanged cited execution is `-mem2reg` with SUCCESS,
   but the row now claims supported future action `-gvn`. Bytes remain genuinely
   child-authored, just for the **wrong mode**. Existing checks only establish
   that the target is some raw span and that both controls carry identical
   provenance, not that it is the admitted conditional for this key/mode.
2. Replace both32-quartet arrays with32 copies of their first quartet. The
   schedule remains32x4 and shape equality passes, but there are only four
   key/mode relations presented128 times each, rather than16 presented32 times.

Neither mutation is produced by `build_replay`; neither changes its original
source/material seals or formation. The helper hashes the supplied altered
Replay rather than comparing it against an independently retained expected
Replay digest. Frozen dataclasses prevent attribute assignment, not construction
of a replacement instance. Existing tests cover unequal-arm target changes and
changed schedule/length, but not these symmetric alterations.

**Impact is conditional, not a core authored-target bug:** the normal trusted
builder-to-shape-check path remains correct. A caller must not use this shape
result as standalone re-admission/provenance or work-coverage validation of a
deserialized/rebuilt Replay. The handoff already limits the helper to supplied
shapes and leaves runtime authenticity external; that limitation is material.

**Smallest disposition:** retain the digest of a freshly built Replay from the
externally anchored material/source seals, and require the checked/consumed
Replay to equal that digest. An explicit expected-replay hash at this boundary
would reject both examples without a new framework. Alternatively document and
enforce trusted immediate builder output only in the integration. Comparing a
freshly recomputed hash of an already modified input to itself is not the fix.
No source/test repair was made here.

### Reproduction (repository root; no files written)

```bash
python3 -B - <<'PY'
import sys
from dataclasses import replace
from hashlib import sha256
from collections import Counter
sys.path.insert(0, 'tests')
import test_endogenous_action_relay as fixtures
from organism_v6 import endogenous_action_relay as relay
material, blocks = fixtures.fixture()
replay = relay.build_replay(material, blocks,
    expected_material_sha256=relay.digest(material),
    expected_source_sha256=relay.digest(blocks))
def check(value):
    return relay.check_native_shapes(value, modes=material.modes,
        tokenizer_sha256=sha256(b'synthetic review encoder').hexdigest(),
        collation_sha256=sha256(b'synthetic review collator').hexdigest(),
        encode=fixtures.synthetic_encode, collate=fixtures.synthetic_collate).status
other = replay.formation.admitted[0].conditionals[1]
span = (other.action_span[0] + 1, other.action_span[1])
def wrong_binding(row):
    return replace(row, SUPPORTED_FUTURE_ACT=other.SUPPORTED_FUTURE_ACT,
        target=row.record.raw[slice(*span)], target_span=span)
altered = replace(replay,
    auth_quartets=((wrong_binding(replay.auth_quartets[0][0]),) +
        replay.auth_quartets[0][1:],) + replay.auth_quartets[1:],
    swap_quartets=((wrong_binding(replay.swap_quartets[0][0]),) +
        replay.swap_quartets[0][1:],) + replay.swap_quartets[1:])
print('cross-mode target:', check(altered))
duplicated = replace(replay, auth_quartets=(replay.auth_quartets[0],)*32,
    swap_quartets=(replay.swap_quartets[0],)*32)
counts = Counter((row.key, row.authored_mode) for index in duplicated.schedule
    for row in duplicated.auth_quartets[index])
print('duplicated:', len(counts), sorted(counts.values()), check(duplicated))
print('original:', check(replay))
PY
```

Observed: both altered inputs and the original return the supplied-shapes status;
duplicate coverage is `4 [128, 128, 128, 128]`. The actual probe also confirms
the wrong row is M0, executed `-mem2reg`, outcome SUCCESS, target `-gvn`, and
that the original source binding remains unchanged. These are synthetic token
fixtures, not a native tokenizer/model test.

## What passes in the intended builder path

- Closed ACT/DREAM grammar rejects extra bytes, NULL, unsupported actions and
  malformed citations without repair. EXECUTED_ACT is verified against its
  raw commitment. Future-action spans are copied from the exact child record;
  FAILURE checks the child's already-authored other action rather than creating
  it. The training suffix excludes only the shared hyphen already in `ACT: -`.
- External material/source digest mismatches and raw receipt-hash mismatches
  fail closed. Receipt IDs are globally unique; commit/outcome/DREAM sequencing
  and pre-child material sequencing are enforced for a complete admission.
  Citations join the same key/mode/object/block, not a later or other-block call.
- Eight supported records/16 conditionals are required. Any shortage yields no
  quartet rows, schedule, controls or fits; partial admissions remain diagnostic.
  Complementary modes, four bindings/action/mode and presealed opposite pairs
  are checked without selecting replacement pairs or consulting hidden truth.
- Full build produces128 rows,32 quartets replayed four times,512 presentations
  and32 presentations/relation. E_SWAP changes only the registered mode input,
  preserving each child target/span/record/execution; the builder's public
  surface comparison rejects other mode-pair byte differences. Only E_AUTH and
  E_SWAP are candidate-producing controls; E_SHADOW references unmounted E_AUTH.
- No hidden orientation/map argument or hidden scorer access appears in this
  module. Admission uses public committed action/outcome evidence and the
  two-action law. The balance checks inspect admitted public records, not an
  external truth table. No I/O, world query, model call, fitting or fallback root.

## Interface limitations, not additional defects

External capture must authenticate who generated bytes, actual prompts/process
identity, and public world outcomes, with independently retained seals. Hashes
and integer sequence claims cannot authenticate their own source; this is
explicit in the handoff. The independent world owner must bind/verify the hidden
map and outcome generator without handing the map to the compiler.

Presealed rendering provenance, prior-exposure exclusion and complete held/
locality/wrong-root/copy material are external. Object IDs are caller metadata;
lexical forbidden-word checks do not prove arbitrary prefix semantics or absence
of coded hints. Actual renderer identity and freshness cannot be inferred from
those checks alone. These are acknowledged adapter responsibilities, not a demand
to add hidden-truth access or a full runner here.

Supplied tokenizer/collator identities and equal reported shapes are not native
tensor authenticity, optimizer/initialization/dropout work equality, or valid
runtime loss masks. Those remain integration checks. OFF/SHADOW metadata does
not implement sterile evaluation or prove raw-output equality. Conditional
preparation is neither establishment of the Q0 prerequisite nor a launch/result.

## CPU evidence and exact reviewed bytes

Command: `python3 -B -m unittest discover -s tests -p test_endogenous_action_relay.py -v`

**22 tests PASS in0.361s.** Two additional in-memory adversarial substitutions
reproduce F1; baseline still passes. No new test file or log file was written.

| Reviewed artifact | SHA256 |
| --- | --- |
| `organism_v6/endogenous_action_relay.py` | `15821f621608858b73ff1aba80fb18c87832d548261e414c94035ff8615a73ad` |
| `tests/test_endogenous_action_relay.py` | `0ef92e03d96b14451b2f340f64a8c070cdd98a8a304f62c76a73c43eb4fd40dd` |
| `research_notes/analysis/2026-09-13_shortest_parent_free_one_sleep_endogenous_action_relay.md` | `6d16a4bb424fdda1f3052459b332e160bdbbc3d984753b7ad76542866c7aff7b` |
| `/tmp/astra_endogenous_action_relay_handoff_20260913.md` | `624209c3a9d4868e1c74b36eb61f68f15beb81254dbedc11a55b5d7f73faf314` |

Code/test hashes match the handoff. Prior involvement: downstream writer/learning
helpers, probe/projected-runtime tests, manuscript reviews and parent semantic
audit. I did not author this component. This is a separate, non-blinded project
review, not wholly project-independent replication or scientific proof.

Only this Markdown was written. No source/test/manuscript edits, Git, network,
GPU/model/tokenizer operation, Q0 live-output inspection or launch. **EDITSTOP.**

## F1 fix-verification addendum — final repair bytes only

**PASS: F1 closed under the externally retained trusted-builder seal contract.**
This addendum preserves the original review and limits verification to F1; it
does not expand formation, native-work, scientific or launch acceptance.

Verified final SHA256:
- `organism_v6/endogenous_action_relay.py`:
  `b7e489143841a83a58b46a8897108b885ea4e6f8caf062a10c25d2eeeceafe53`.
- `tests/test_endogenous_action_relay.py`:
  `1a728166c9a48c328901a2d591ed13eac1408fc6e1567019c30e2e7ebc5607a8`.

`check_native_shapes` now requires keyword-only `expected_replay_sha256`, checks
its format, and compares it with the supplied Replay digest before encoder or
collator callbacks. Both original F1 alterations—symmetric wrong-mode target
substitution and repeated-first-quartet coverage—raise `replay seal mismatch`
with neither callback invoked. Missing/malformed/mismatched expected hashes also
fail before callbacks; the unchanged trusted replay still passes synthetic shape
checking and returns its bound digest.

Reproduction command (repository root):

```bash
PYTHONPATH=tests python3 -B -m unittest -v \
  test_endogenous_action_relay.EndogenousActionRelayTests.test_expected_replay_hash_required_and_validated_before_callbacks \
  test_endogenous_action_relay.EndogenousActionRelayTests.test_symmetric_wrong_mode_target_substitution_rejected \
  test_endogenous_action_relay.EndogenousActionRelayTests.test_symmetric_repeated_first_quartet_rejected \
  test_endogenous_action_relay.EndogenousActionRelayTests.test_native_shape_interface_is_explicit_and_synthetic_only
```

**4 focused tests PASS in0.140s.** Main owns the separate25-test full rerun;
this addendum does not claim that rerun. As before, the expected hash must come
from the retained trusted builder output, not be recomputed from an altered
Replay. Native implementation/tensor authenticity and all other original
interface limitations remain unchanged.

Original report SHA256 before this append:
`a8ea49fb2700cc28ca919461fabc047066d9615202b7082f971456715d680622`.
Prior-project-involvement disclosure still applies. Only this report was
appended; no source/test edits, Q0-output reads, native/model/tokenizer work,
network, Git or expanded guard scope. **EDITSTOP.**

# Projected AUTH/OFF runtime CPU review — EDITSTOP

## Result and exact acceptance logs

**PASS:36 runtime tests in93.446s;11 launcher tests in0.026s.** Both exit0;
47 total across two separately executed suites, with no skips/expected failures.
No production driver, launcher, role, diagnostic or repository file was edited.
No concrete runtime defect remains demonstrated by this bounded suite. Main
retains source integration, native acceptance and launch decisions.

| Artifact | SHA256 |
| --- | --- |
| `/tmp/test_astra_projected_rulegame_formation_run_20260913.py` | `1ecba31c052823e59e06abb2103abb99dd2f92beaa8f84b5f97bda021175b4fc` |
| `/tmp/test_astra_launch_projected_formation_20260913.py` | `25885e26cecedf5d5c139a4ca27c90b55e291a4bd5f251460be42388cdea8d16` |
| `/tmp/astra_projected_runtime_cpu_20260913_final.log` | `a0103c8f24507f6ad9fa3bb9bab7dc95d808bb097fcf4717069e171b96e116c1` |
| `/tmp/astra_projected_launcher_cpu_20260913_final.log` | `b649ff1eaa858dd7ba6c4c038c2c57caf34a592a2e8a8d698ad4efa46be0da2b` |
| Main driver `/tmp/astra_projected_rulegame_formation_run_20260913.py` | `e0b673b7dc2ef6b556acfd47ab1df9db320c6122a459d957465cfe4315bb0a6e` |
| Main launcher `/tmp/astra_launch_projected_formation_20260913.py` | `3e79ca6fb0984a4814664bfd22aa05c20fc466bbb7a2f38506c581f0206170fa` |

The runtime log contains `Ran 36 tests` and ends `OK`; use36, not47, if referencing
that single log in the existing launcher's acceptance interface. The launcher log
contains `Ran 11 tests`. Neither VM log is represented as Main's native execution.

## Scope and coverage

- Reused original runtime/launcher unittest classes and synthetic birth pipeline
  fixtures, overriding only test-local module references and changed interfaces.
  Source-dependent tests ran only after Main supplied Arendt's final role hash.
  Projection is explicit in prepared/checked bindings; original default role
  behavior and the original diagnostic were not edited.
- **Public binding exercised, not mocked away:** real `public_binding` hashes and
  parses an actual temporary receipt. Positive fixture has14 local model entries;
  rejects changed receipt bytes, wrong pinned status/repository/revision/model,
  missing/extra entries, wrong count/hash, and normalized-map/path mismatches.
  Tests assert historical labels preserved and no clean-ancestry claim.
- Integration creates14 actual small model-fixture files *before* generating the
  synthetic completed/released birth. The public receipt therefore joins the
  genuine fixture-normalized model map, rather than overriding production binding
  checks or fabricating an OFF birth. PUBLIC_RECEIPT/PUBLIC_SHA alone are redirected
  in-memory to those fixture bytes; `public_binding` itself remains real.
- AUTH and OFF both retain the same original completed AUTH custody reference.
  AUTH's wake/record/restate routes use its adapter, parent stays OFF; OFF has
  adapter_input=None and adapter_files={} for every served role. Real projected
  capture/replay produces matching fixture requests and distinct binding hashes.
  Source inventories include the projection module. Wrong role pins and resealed
  mode/interface/public-binding mismatches fail closed; post-prepare public-receipt
  drift is rejected. No mutable production globals or live receipts are changed.
- Real journaling and replay retain all60 scripted calls, role events, loader
  envelopes and original native-input fixture fields. Barrier precedes replay;
  missing raw pairs and wrong parent routes reject before promotion. One mocked
  backend handle is constructed/closed once through the actual worker function.
- Completed AUTH and OFF fixture captures collect and revalidate through the
  consumer release API. Failed capture remains partial/unaccepted. Live owned
  sessions block outcome inspection; second vacancy failure leaves an archive
  without accepted validation. Unknown/credential metadata is rejected. Fresh
  preparation roots cannot be reused. Existing900/600/140/300 controller/worker/
  cleanup/collection caps and60-call/18480-token ceilings remain bound; attempts
  to extend the controller cap fail.
- CLI dispatch includes required child mode and no automatic write/readout.
  Launcher tests retain exact static/dynamic receipt fields, command and plan pin,
  actual mocked ownership, exit binding, offline environment and fresh sessions.
  OFF mode is bound through its immutable plan hash, not an invented extra launch
  field. Missing opt-in, wrong phase/driver hash, failed CPU log, occupied GPU,
  existing launch root and exhausted preflight window prevent launch. All GPU and
  process-launch effects in these tests are mocked.

## Source override and dependencies

Both new test entrypoints accept an absolute `ASTRA_SOURCE_ROOT` before imports;
relative paths reject. Runtime fixtures propagate it to the reused test modules
in memory, overriding their original VM-only test defaults without editing them.
Default remains `/data/home/rohing/dream-state`. Final local tests explicitly set
that environment variable. Main's alternate native snapshot path is supported by
the interface, but was not accessed or executed by this reviewer.

Commands run locally:

```bash
ASTRA_SOURCE_ROOT=/data/home/rohing/dream-state PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/test_astra_projected_rulegame_formation_run_20260913.py
ASTRA_SOURCE_ROOT=/data/home/rohing/dream-state PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/test_astra_launch_projected_formation_20260913.py
```

For Main's separate native CPU run, set
`ASTRA_SOURCE_ROOT=/localhome/local-rohing/astra_sources/830fe675ec16bdbe4c0a5dc36ec66908b28da6ce`
before either command. Keep the original `/tmp` fixture files and frozen birth
dependencies available; these tests deliberately reuse them, not a standalone
replacement framework.

Verified role/source pins:

- `organism_v6/born_rulegame_formation.py`:
  `2cb24cf0447d3e5a7d8e61c9a0a65658e033f2c0bfc01b4b60ae15bce437a945`.
- `organism_v6/rulegame_action_projection.py`:
  `47564a630b166cadda546ac5ae65c79bd9ca223a8574b0cfc693d6bc0177ad19`.
- Unchanged `organism_v6/rulegame_parenting_diagnostic.py`:
  `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`.
- Original runtime tests `/tmp/test_astra_born_rulegame_formation_run_20260912.py`:
  `1c84849bda1ef7661371f31ed231ea2faf6d3c4b757e4055840037c2f4ea8e61`.
- Original launcher tests `/tmp/test_astra_launch_born_formation_20260912.py`:
  `fe1372baeb0446f45646c89610398d1ec876e4d549c6ab8868c655ef55549acd`.
- Synthetic birth fixtures `/tmp/test_astra_birth_conditional_run_20260913.py`:
  `41718101dd3cfe1239f048e9e8686f4086a486bc80cd549cb21945b137c8f62b`.

## Findings and limitations

Two initial mistakes were in this reviewer's tests: using the file-reading `raw`
helper to serialize a dictionary, and trying to overwrite an exclusive plan seal
through the production sealing helper. Corrected to JSON fixture serialization
and explicit local tamper-fixture writes. No driver repair was indicated. An
initial10-second tool timeout interrupted the long synthetic suite; the complete
final run above is authoritative. Earlier logs are not acceptance logs. An
existing import-time ResourceWarning about an unclosed parent-prompt text file
is unrelated to these drivers and was not repaired.

This is CPU integration, not authentication of the real public14-file receipt,
native model loading, native token decoding, real GPU vacancy or live cleanup.
The temporary receipt's expected hash is a fixture pin, not a substitute production
receipt. Normalizer/help subprocesses are real CPU-only fixture invocations; no
model inference, GPU, Git, network, Q0 data or live experiment outputs were used.
No active Arendt tests/role files were edited. Public revision binding remains
prospective and does not retroactively clean ancestry or relabel historical
results. No writing/persistence/efficacy, P1/G3/G5/H1/H2 or freeze claim follows.
No formal C11 framework was added. **EDITSTOP.**

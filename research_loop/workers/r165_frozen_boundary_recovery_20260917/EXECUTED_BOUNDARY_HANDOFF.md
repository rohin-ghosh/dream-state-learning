# R165 candidate2 CPU boundary completion — executed once

September 17, 2026, **08:00:23.453502 UTC / 01:00:23.453502 PDT**.
Status: **VERIFIED_CPU_BOUNDARY_COMPLETION**, subprocess return code **0**.
The fixed operation latch is consumed. **Do not repeat the command or remove the
latch.** No native resume, readout dispatch, generation, training, or GPU launch
was authorized or performed.

## Authority and preflight

Main explicitly delegated authoring one operational GO and executing one CPU-only
`COMPLETE_MISSING_SLEEP1_ONLY_NO_GPU` against approved candidate2. This is recorded
as Main executor permission, not human ratification or a scientific claim.
Linnaeus's candidate2 approval and exact helper/test pins were verified locally.
The sanctioned `gpu/a40r_ssh.sh` wrapper was used with CUDA hidden.

Both read-only preflight and immediate pre-dispatch checks confirmed:

- Host `[REDACTED_HOST]`; exact helper
  `2d1a21bf23de229338fbf1cc8a5fd2a21abf00d68323d3b1cfca55cb735a49e8`.
- Exact 40-test actual CPU PASS receipt and tests hash; zero errors/failures/skips.
- Exact prepared SHA
  `f0fca62d24d8196bab0b889b98954834cb371becdd9c9af04b1a3e5e45c9ad25`.
- Original record13/pending boundary and all 29 prefix references still matched;
  original failed native PID681274 was absent.
- Production latch and new `boundary_attempt1` were absent; CUDA uninitialized.

GO was issued **08:00:16.858032 UTC**, expiry **08:15:16.858032 UTC**:
`not_before=1789632016.858032`, `expires=1789632916.858032`.
This is exactly 900 seconds and below unchanged wall `1789646400`.

## Exact receipts

Remote attempt directory:
`/localhome/local-rohing/orch_r165_frozen_boundary_recovery_20260917/candidate2/boundary_attempt1/`.

Exact local byte copies:
`candidate2_inputs/executed/candidate2/boundary_attempt1/` relative to this worker
directory. The fixed marker copy is under
`candidate2_inputs/executed/FROZEN_SLEEP1_BOUNDARY_CONSUMED/`.

| File relative to remote attempt | SHA256 |
| --- | --- |
| `MAIN_GO.json` | `ea9fc7b28d51ff09988e79ad336a3435768ccdfed22acf30bc950007e844fb87` |
| `COMMAND.json` | `1c31bc113a685a9a6ef226af3a65760de55e513930cc1dafe2f7c7fb67f63c1f` |
| `EXECUTOR_RESULT.json` | `632c6916abd4c9f049db38afa4952cc1de687afbd8f33235adfea4f538d782c9` |
| `completion/COMPLETED.json` | `8af235ff32f3f4100828f56985ad137ac90c35fe4a4b757cb5a2ca70d041fa5f` |
| `POSTCHECK.json` | `1d170edb952db74538646cd9043f1a5ba1f5e2211c709a1ba69fb8ae99f4fabf` |

`AUTHORITY.json`, `PREFLIGHT.json`, `EXECUTION.log`, `completion/ONCE.json`, and the
consumed marker are also retained in the downloaded archive. The record14 body
was not copied into this handoff; its metadata and exact hash suffice here.

## Actual command (historical; already consumed)

The CPU subprocess used the reviewed source directory as its working directory.
The GO lives in `boundary_attempt1`; the helper's create-only receipt destination
is its initially absent `completion` subdirectory.

```sh
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=/localhome/local-rohing/orch_r165_frozen_boundary_recovery_20260917/candidate2/source \
  /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r165_frozen_boundary_recovery complete \
  --prepared /localhome/local-rohing/orch_r165_frozen_boundary_recovery_20260917/candidate2/PREPARED_BOUNDARY.json \
  --prepared-sha256 f0fca62d24d8196bab0b889b98954834cb371becdd9c9af04b1a3e5e45c9ad25 \
  --main-go /localhome/local-rohing/orch_r165_frozen_boundary_recovery_20260917/candidate2/boundary_attempt1/MAIN_GO.json \
  --main-go-sha256 ea9fc7b28d51ff09988e79ad336a3435768ccdfed22acf30bc950007e844fb87 \
  --receipts /localhome/local-rohing/orch_r165_frozen_boundary_recovery_20260917/candidate2/boundary_attempt1/completion
```

## Verified current saved state

- Exactly one `SLEEP_COMPLETE` appended at record **14**, plus its intent; record
  directory contains 30 files. No second dispatch/retry occurred.
- Record14 file SHA:
  `06ae61dda0d1c83c9f170c3955a9140ce8c4ccf6dc7d41aeb12d507db8238b80`.
  Envelope SHA:
  `f62a474a3eb13179eba8689e6d35f6bb011b84d5bd593435dfda21d0aaeb5569`.
- `pending=null`, `rows=3`, `sleep_frontier=3`, `sleep_receipts=1`.
- All 29 original prefix references and six pinned original evidence files
  reverified unchanged after completion. Exact proposed transition matched the
  actual record; history/carry/counters were not regenerated or rewritten.
- Original sleep1 COMMIT remains
  `1aa0ab173c105e880c5b8da7ce697d57113c49d6c6536255b15cd4a3d443b977`;
  optimizer/RNG remains
  `ac936284676923e264bfa5d12fbb0eb39f7f584231ce0ff3a30ce4705809915c`.
  These bytes are selected for future restore; no resident model/RNG restoration
  is claimed by this CPU-only operation.
- Fixed marker `FROZEN_SLEEP1_BOUNDARY_CONSUMED/CONSUMED.json` SHA:
  `91e392a8c8f77573036e4e79dcae30063a3c5015788e22c2dadf22bf5e22ebe7`.
- Sleep1 readout is still **NOT_STARTED**, not complete. CUDA uninitialized;
  generation calls and optimizer updates both **0**. No native process launched.
- Original sources, old error records, parent3693784 and R162 service1389517 were
  not modified or restarted.

## New all-hands priority

Readmission-framework work is **parked**. No new readmission helper/tests/source
or native dispatch exists from this worker. Main/Mendel: this worker is available
for a bounded, disjoint R166 parent-takeover review or staging assignment. No R163
or benchmark maintenance is underway, and no shared R166 files have been edited.

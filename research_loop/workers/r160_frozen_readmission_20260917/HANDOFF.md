# R160 frozen-only readmission — CPU prepared, awaiting Main GO

Prepared September 17, 2026, 05:45 UTC; receiving copies collected 05:47 UTC.
No R160 GPU dispatch. The existing learning lives on physical5/7 were not
restarted or modified. Candidate5 source, cohort, plans, original refusal and
old PHASE_ONCE remain unchanged.

## Actual evidence

- Local command: `CUDA_VISIBLE_DEVICES= uv run --with pytest python -B -m pytest -q tests/test_orch_r160_frozen_readmission.py`
- Local result: 29 PASS in 0.41s (`CPU_TESTS_FINAL.log`).
- Receiving result: 29 PASS in 0.27s (`RECEIVING_CPU_TESTS.log`).
- Real CPU preparation called the original frozen R125 `guard.validate` on
  the new configuration; accepted. No scanner bypass or native call occurred.
- Operator SHA256: `84f2a24843c09fdef58408a28ffe02ba93f0431ecbcf86cf0414c957f7d2a4ba`.
- Tests SHA256: `f9725a97a30df85de5c7ca0629f9a3b52d374f3176db551c952216cde7731f8d`.
- Receiving CPU SHA256: `f58bda2f31c42ddc99ebccee7038478697dfca26e9564a43669b423bf827a6e5`.
- PREPARED_READMISSION SHA256: `4a916df78c8a4dd09749b6746fd73f0b5b3887111eaaef8832f117a577d897b8`.
- New GUARD SHA256: `bd217fa7bc3b3aaf3f30a938ebd97ab90f0b132dece5aa0e447c0614f8d54a36`.

Local JSON files are byte copies; their embedded paths retain the actual
remote bindings. Preparation already succeeded; do not rerun it.

## Required Main GO

Main creates a new `R158_MAIN_GO_V1` document with issuer `Main`, decision
`GO`, fresh bounded `not_before_unix`/`expires_unix`. Copy `binding` exactly
from local `PREPARED_READMISSION.json`'s `required_GO_binding`, and copy its
`initialization` unchanged. Add this mandatory top-level field:

```json
"readmission": {
  "path": "/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt5/control/run-parented_frozen-r160-readmission/PREPARED_READMISSION.json",
  "sha256": "4a916df78c8a4dd09749b6746fd73f0b5b3887111eaaef8832f117a577d897b8"
}
```

No GO was authored by this operator. The original run GO is insufficient.

## Authorized execution entrypoint (not executed)

After receiving a new exact Main GO and hash, dispatch once, detached after
the initiating SSH processes exit plus five seconds:

```bash
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  /localhome/local-rohing/v2/venv/bin/python -B \
  /localhome/local-rohing/orch_r160_frozen_readmission_20260917/source/gpu/orch_r160_frozen_readmission.py \
  supervise --main-go "$MAIN_GO_PATH" --main-go-sha256 "$MAIN_GO_SHA256"
```

The external operator requires original `validate_extra`, unchanged frozen
engine validation/supervision, the same physical6 exclusion lock, and a new
R160 once marker. Only allocation binding, attempt path and unit differ in
the copied GUARD. New attempt is `attempts/run-parented_frozen-attempt2`.
The old mixed-minor refusal is preserved, not declared clear or filtered.
Fresh full scanner admission remains mandatory; no automatic native retry.
Report actual PID/birth/LOADED or precise refusal promptly after dispatch.

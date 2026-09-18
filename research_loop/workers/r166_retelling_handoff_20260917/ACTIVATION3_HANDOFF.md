# Activation3 closure repair — no GO or signals

Non-material staging repair only. Preserve activation2 failures, GOs, sources,
dispatch intents and all live owners. No invitation/recipe/wall change.

Final helper SHA256: feaeae434d9e21c164f504621d3305ecd50ec2eae796350abeda757c989d4d51.
Final tests SHA256: 4a7c2dd98a0aa2fa538005675730721693379e3aa2df3f2d2fd0c44c8e9fe541.
Invitation/test remain 9277b09ca3f312bd7afa8bbcfc94f883940652c4199fe686c2ed47d73a992bcc
and b6f4ef8a65c09fa93b9b9fa705fd73f6f0ee589375eafa75024aa1f91f88132e.

Staging now copies the exact pinned invitation test. New inventory requires it;
predecessor delta permits only that added file plus updated handoff helper/tests.
Original files are still checked byte-for-byte. Regression executes actual
validate_cpu and inventory checks in a subprocess imported from the staged
successor, not the author's repository. Missing/tampered invitation tests fail;
legacy predecessor remains unchanged and the new candidate passes.

CPU: 92 tests + 59 subtests PASS in 5.94s:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/r136-pytest-support:$PWD python3 -B -m pytest -p no:cacheprovider -q tests/test_orch_r166_retelling_handoff.py tests/test_orch_r166_corrected_retelling.py tests/test_orch_r157_community_wall_extension.py
```

Log `CPU_ACTIVATION3.log` SHA256
32b2e657e3b284692f5cbfdbd303aa89e3d21fc8ca1dcc4b5d5d9aecfbdda315.

All four actual node5 preflights additionally executed the unmocked full
`preflight` CLI in separate processes with cwd and PYTHONPATH set to each exact
successor source; CUDA hidden/offline. Each validated the full request/source
closure and actual CPU saved-state loader. Return codes zero, READY output
matched saved READY bytes. Full subprocess command/cwd/stdout/stderr receipts
are under the remote operator `C<N>_SUBPROCESS.json`, individually hash-bound
by local `ACTIVATION3_PREFLIGHT.jsonl`.

Remote operator: `/localhome/local-rohing/orch_r166_retelling_operator_20260917_activation3`.
Life roots: `/localhome/local-rohing/orch_r166_retelling_C<N>_20260917_activation3`.

| Life | readiness/READY.json SHA256 |
| --- | --- |
| C1 | 22064f2c92befac12829eb489b79a3e78d07e92e72533bc9b7825b7255fd9578 |
| C2 | de01824feb37a84a14a1b915e502f52275d3f220da1f2dbbe1292c296df770db |
| C4 | b34e3e4ef838fed6ac00df909570016a3059bab5f94df036a03e005aa68ddaef |
| C5 | 7840d0f9d8764a9e36b8fd8637d1de9c2748e406d3d28822cbb1dd38bee1f1e6 |

Observed preflight times Unix 1789633573.6786242 through 1789633586.613071.
Each next GO must bind its NEW exact READY.required_GO_binding, issuer Main,
decision GO, schema R166_SAVED_BOUNDARY_MAIN_GO_V1, actual-now timestamps with
expiry <= now+1800 and original wall1789776000. Max wait/pause remain600 each.
No GO created, no execution dispatched, no native/parent signals or claims of
invitation adoption. C3 excluded. No source bytes changed after these pins.

After NEW Main GO only, execute once through ovx3 using exact successor source:

```bash
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT/source" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r166_retelling_handoff execute --output "$ROOT" --main-go "$GO_PATH" --main-go-sha256 "$GO_SHA256"
```

Do not reuse any activation2 operational launcher: its paths and authorized
hashes intentionally remain activation2. Actual boundary proof, strict device
admission and watchdog gates still apply; no automatic uncertain retry.

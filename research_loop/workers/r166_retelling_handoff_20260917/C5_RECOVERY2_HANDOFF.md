# C5 executable retired-owner recovery2

Fresh root `/localhome/local-rohing/orch_r166_retelling_C5_20260917_recovery2`.
Fresh operator `/localhome/local-rohing/orch_r166_retelling_operator_C5_20260917_recovery2`.
Old activation2/activation3 and preparation-only recovery1 remain untouched.

Helper655e72c553c934538b47e12987ffb9d493505f668721e0c432275b4617233681;
testsa6ae913da890680b387d5b3568bea97667988777b8254493909c80316b9b5660.
No source edits after these receiving pins. Main's dispatch-directory repair
and isolated real guard import are retained. Invitation unchanged9277b09c...
and invitation test unchangedb6f4ef8a...; source delta only handoff helper/tests.

102 CPU tests+63 subtests PASS14.48s in one combined process:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/r136-pytest-support:$PWD python3 -B -m pytest -p no:cacheprovider -q tests/test_orch_r166_retelling_handoff.py tests/test_orch_r166_corrected_retelling.py tests/test_orch_r157_community_wall_extension.py
```

Log CPU_C5_RECOVERY2_FREEZE.log SHAe95b77b4fdd1733a99f36aa99f61cdec6259eb5a7dc8086d061b2e19916c16d5.
Recovery end-to-end fixture exercises real recovery evidence/source/plan/GO
validation, real prepare/custody, real strict supervisor, real DISPATCH_ONCE
directory and unchanged native_entry with real OS parent/startticks and pipe
startup barrier. Scanner/systemd transport/model and synthetic checkpoint
loader are mocked; real Torch saved28 loader is separately exercised below.
Failure tests cover live predecessor, changed failure, changed source/plan,
checkpoint tamper, later journal suffix, old/wrong/expired GO, lock exclusion,
duplicate execution and uncertain scan. No recovery signal or OWNER_RETIRED
creation occurs; ordinary execute rejects recovery requests.

Actual node5 new-source preflight-recovery CLI PASS at Unix1789634731.7737947,
CUDA hidden/offline, stderr empty. CPU proof exactly equals prior saved28 proof
f961c96566a5f60f56dbd83ab143839d933607b7ef11f9adeda9d8d69b3fc9a4:
2478 optimizer steps, exact adapter/AdamW/RNG/context, boundary2899, original
wall1789776000. It verifies hashed pre-model failure and original retirement,
full predecessor sources and preserved checkpoint/journal, absence of original
owners and failed operator/timeout, and no subsequent work. No GPU or dispatch.

READY2fb6e99746f81451c1563c0c5a14d0b9ec4fb491070dbc6cb686525cbf151718.
REQUEST5e238d62daabbe1b28b8f70d63be6ff60f5ebf19f0390d0317ad5ae36e0e9b21.
PLANaf6ed5d6a0c1d7b5f586849a52c7a61072e76604d6ddac34e0ef9f665878fd01.
CUSTODYb0f9d6add88840d2484c950867a7f2089dc055233d82784eb3f47d92378f81dc.
Source manifest6233e75998a4d04278174b668321e94be704c695f2ff6709e33313bcea9923a3.
Subprocess receiptf84482df9abc5257eecfba82def7743bf90adfe59184eaff107ffff86bc83d11.
All exact references and binding are in local C5_RECOVERY2_PREFLIGHT.json.

## New Main recovery GO and executable entry

Only after fresh Main operational authority, create a new GO containing:
schema `R166_C5_RETIRED_RECOVERY_MAIN_GO_V1`, issuer `Main`, decision `GO`,
binding copied exactly from recovery2/readiness/READY.json.required_GO_binding,
not_before_unix actualnow, expires_unix actualnow+1800 <=1789776000.
The distinct schema refuses ordinary/previous GOs. No GO exists at handoff.

Run ONCE detached through ovx3 from exact source:

```bash
ROOT=/localhome/local-rohing/orch_r166_retelling_C5_20260917_recovery2
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT/source" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r166_retelling_handoff execute-recovery --output "$ROOT" --main-go "$GO_PATH" --main-go-sha256 "$GO_SHA256"
```

This takes the original exclusive C5 handoff lock, creates ACTIVATE_ONCE,
rechecks fresh GO/custody, CPU-prepares NEW control and preserved copies,
records RECOVERY_EXECUTION linked to the authentic original retirement,
then uses unchanged full privileged scanner/device envelope/containment and
native resume runner with repaired startup marker. It does not stop/retire
any process or create OWNER_RETIRED. Control/GUARD and attempt are created
only under this new root after GO; no prepared config is rewritten.
Failures retain RECOVERY_FAILED and actual attempt evidence, no retry.

C1/C2/C4 stay on healthy originals; no auto-relaunch. C3 excluded. No effective
invitation or LOADED claim before actual runtime records and request exposure.

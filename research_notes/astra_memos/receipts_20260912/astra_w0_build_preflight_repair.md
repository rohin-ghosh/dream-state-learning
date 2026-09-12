# W0 native-build preflight repair

Date: 2026-09-12 07:44 UTC. Classification: bounded non-material environment preflight repair, for a NEW immutable attempt only. No scientific/training recipe changes.

## Owned repository files
- `organism_v6/multikey_writer_gateway_simple.py`: CPU-only `native_build_preflight`, immutable preparation artifact, execution revalidation.
- `tests/test_multikey_writer_gateway_simple.py`: real C compiler/fake development-header interface, explicit controller preflight mocks, negative/order/CLI coverage.

No other repository files edited. No commit, pull, stash, rebase, notebook conflict resolution, network activity, GPU access, replacement fit, or automatic retry. No remote access or changes to deployed source b686fcf0. Existing node SHA256 identity is preserved.

## Precise behavior
1. `prepare_real` validates the existing config and lease, then performs native-build preflight BEFORE snapshot pinning, tokenizer loading, or run-directory creation. Missing prerequisites fail closed without creating a prepared run. CLI reports NONREPORTABLE_ABORT and returns 2; prerequisite failure does not fabricate a successful receipt.
2. Select the compiler from explicit `CC`, otherwise PATH `gcc`, then `clang`; an invalid explicit `CC` fails rather than silently falling back. No installation, downloads, CUDA/compiler-driver probes, model imports, or generated executable execution occur.
3. Use the running CPython's configured `sysconfig` include and platform-include paths. Require `Python.h` in the configured include path and `pyconfig.h` in an include directory. Inventory/hash all `.h` files in those trees.
4. Run compiler `--version`, then compile a minimal `#include <Python.h>` C translation unit into an object with `-std=c11 -fPIC -c`. Both subprocesses have 30-second timeouts. Require successful compilation AND an output object. Scratch source/object files live in a temporary directory and are cleaned up.
5. Record compiler resolved path, SHA256, full version output, configured compiler metadata, CPython version/executable path, installed Triton version, include paths/header SHA256 inventory, relevant environment values, exact compile argv, probe-source SHA256, return status/stdout/stderr, and explicit no-model/no-GPU flags in `native_build_preflight.json`. Triton version comes from `importlib.metadata.version("triton")`, never importing Triton or torch; absent distribution metadata fails closed. Existing write-once artifact and manifest/seal hashes bind its bytes. PACKAGES/config schema remains unchanged.
6. `execute_real` retains the explicit `--allow-gpu` and no-prior-attempt gates. It validates the prepared artifact binding, reruns compilation, and requires exact receipt equality BEFORE input pinning, GPU inventory/idleness checks, tokenizer load, worker launch, or EXECUTION_STARTED marker. Missing/broken prerequisites or changed evidence refuse execution. No retry loop or new attempt scheduling is added.
7. New executable preparations must contain the bound native receipt. Historical read-only replay using `check_source=False` remains possible without retroactively requiring this new artifact. No existing run is rewritten or repaired in place.

This narrowly tests CPython native-header compilation, not CUDA linking, Triton kernels, model loading, GPU health, or training success. It does not certify every possible native dependency. Main owns environment installation/repair coordination and whether/when to prepare a new immutable attempt.

## Validation
- `python3 -B -m unittest tests.test_multikey_writer_gateway_simple -q`: **60 tests passed**, no skips (baseline 51); final run 10.223 seconds.
- Positive prerequisite tests invoke an actual local C compiler against controlled fake `Python.h`/`pyconfig.h` files through the real preflight helper, not a nonexistent prereq API. Controller tests explicitly mock that helper separately from mocked CPU-suite subprocesses.
- New tests cover missing compiler; missing Python.h and pyconfig.h; actual compile rejection of broken transitive headers; stable compiler/header evidence; changed header bytes; metadata-only Triton version pinning/drift; prepare ordering; execute drift/failure ordering and no attempt marker; sealed receipt tampering; CLI missing compiler and missing GPU opt-in.
- Existing full mock four-fit replay, failed-worker/no-retry, scientific boundaries, node-hash identity and lease tests remain passing. Scientific/mock labels and training recipe/labels/caps are unchanged.
- `git diff --check` on the two owned files passed.
- Test output: `/tmp/astra_w0_build_preflight_tests.log`.

## Concurrent checkout preservation
The concurrent courier checkout operation removed an initial tranche of edits during the first test run. Only the two owned files were repaired again; no Git state or other contributor files were altered. Recovery copies of the final files are `/tmp/astra_w0_build_preflight_source.py` and `/tmp/astra_w0_build_preflight_tests.py`; scoped diff is `/tmp/astra_w0_build_preflight_repair.patch`. Pre-restoration snapshots also remain under `/tmp/astra_w0_*_before_repair.py`.

The metadata-only Triton follow-up is additionally preserved in `/tmp/astra_w0_build_preflight_triton.patch` (apply after the initial scoped diff); the recovery file copies contain the final combined state. No Git operations were performed after main's final no-Git instruction.

Main reports node3's existing environment repaired at 07:43 UTC with python3.12-dev/libpython3.12-dev 3.12.3-1ubuntu0.16 and Python.h SHA256 `729ef157f6026e6e1b3104593f87dddc597c3b83b60c7c2965878c62a56c6f7d`. This agent did not independently access node3; main will perform real CPU prerequisite validation. The failed W0 run remains sealed and no new attempt was initiated here.

Final source SHA256: `99abab2c78dc06756b0bbbeb86d5717c5baf430af2cbafdab206f4fc8af4cafc`.

Final tests SHA256: `874ca3984471694724c365d1efc98e04187afb3ddf997a173993eda7d2188f37`.

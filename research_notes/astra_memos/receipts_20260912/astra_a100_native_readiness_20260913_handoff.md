# A100 OFF native-readiness handoff

**EDITSTOP. CPU checks PASS; this model-readiness helper has NOT run natively.**
September 13, 2026. Main owns transfer, current lease/reservation/queue/vacancy
checks, explicit native launch, hard timeout and post-exit release checks.

## Prior smoke archive and release complete

The prior sampling smoke remains PASS, not a model-readiness result. Its closed
nine-file archive is `gpu_artifacts_local/a100_toolchain_smoke_20260913_attempt1/evidence.tar`,
SHA256 `d5430f9a7a7f914d237352e7ce8bbb5072a760bc4b668b2e7ff69d7d64645da0`.
Archive/member verification is already recorded beside it.

New `gpu_artifacts_local/a100_toolchain_smoke_20260913_attempt1/release.json`
records **08:26:05.909408 UTC**: expected GPU0 UUID matched, targeted all-process
NVIDIA XML empty, timeout PID36148 absent, same-user PGID36148 empty.
SHA256 `1ea11d460b74b60c1c3cca3748d37bddb2b783e3a4a68f77718fe590e8fa8242`.
This supplements the earlier inspection without modifying its historical
archive. It is a point-in-time release observation, not a new reservation.

## New helper scope and API

- `/tmp/astra_a100_native_readiness_20260913.py`
- `/tmp/test_astra_a100_native_readiness_20260913.py`
- `/tmp/astra_a100_native_readiness_20260913.cpu.log`

API: `--allow-gpu --output FRESH_ROOT`, with the exact full
`CUDA_VISIBLE_DEVICES=GPU-ff5f84e9-c70e-272d-a8e0-eb20aad05ac6`.
Refusal precedes native imports when opt-in/UUID is missing or incorrect.
Use existing `~/v2/venv/bin/python`; no package/global configuration edits.
The output root is exclusively created with mode0700; existing roots refuse.

**OFF only**: one vLLM model load and one fixed prompt, “Please reply with OK.”,
with **max_tokens=4**. EOS may yield fewer than four tokens; passing requires
1–4 valid token IDs, expected prompt-token identity and normal finish status,
not a particular answer. No benchmark, semantic scoring, training, optional
adapter discovery, or adapter loading occurs; `lora_request=None` explicitly.

The exact original 14-file public binding receipt is hash-checked. All 14
payload hashes/sizes are rechecked before model load and after a successful
readout. Model/revision are fixed to Qwen2.5-7B-Instruct at
`a09a35458c702b33eeacc393d103063234e8bc28`; no alternate model/network resolution
is requested. Hugging Face/Transformers offline flags apply in this process.

ENGINE/PARAMS are extracted as literal data from the pinned existing Level1
runtime, without executing it. Sole sampling change: max_tokens192→4. Engine
settings remain bf16, max_model_len16384, TP1, seed0, memory_fraction0.85,
eager mode, prefix caching off, trust_remote_code false, enable_lora true and
max_lora_rank32. LoRA capability is configured as in Level1 OFF, but **no LoRA
weights or route are tested**. Prompt rendering reuses the pinned public helper.

The accepted smoke helper supplies local PATH/CUDA_HOME, tool path/hash/version
checks, output-local JIT/temp paths, exclusive persistent mode0600 `native.log`,
and sanitized useful error messages/traces. Environment changes are process
local and restored; raw environment/credentials are never dumped. Preserve
native logs privately and never commit/report their raw contents or hostnames.

## Exact dependencies to preserve on A100

| Existing /tmp dependency | Required SHA256 |
|---|---|
| astra_a100_toolchain_smoke_20260913.py | `fd0628c850dd76c53b8660b83f9e1fac6a13460a569c1deb61b12d904e828c2e` |
| astra_level1_skill_run_20260913.py | `6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e` |
| astra_birth_skill_probe_run_20260913.py | `59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c` |
| astra_qwen_public_binding_receipt_20260913_attempt1.json | `e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019` |

Missing/mismatched dependencies fail closed; do not modify originals to satisfy
a pin. New helper/native root must not replace any original failure/smoke root.

## Main-only bounded launch — NOT executed here

After fresh prechecks and transfer/hash verification:

```bash
CUDA_VISIBLE_DEVICES=GPU-ff5f84e9-c70e-272d-a8e0-eb20aad05ac6 \
  /usr/bin/timeout --signal=TERM --kill-after=10s 580s \
  "$HOME/v2/venv/bin/python" -B /tmp/astra_a100_native_readiness_20260913.py \
  --allow-gpu --output /localhome/local-rohing/astra_diagnostics/a100_native_readiness_20260913_attempt1
```

The external process-group timeout is **required**, not supplied/enforced by
Python: 580s plus 10s grace is below600s. Keep compile/engine children in the
owned group; Main must reconcile/verify release after exit. A missing result,
timeout or nonzero exit is not a pass. Engine shutdown is invoked when exposed
by the existing API; result records availability, not GPU-release certification.

Fresh outputs include started/identity/tools/model-before/model-after/result
JSON, fixed request and raw response JSON, persistent native.log, and fresh
JIT/temp directories. Failure preserves existing receipts/logs; no retry or
collection is implicit. Successful result is `OFF_NATIVE_READINESS_PASS`, with
`scientific_pass=null`; only the sanity checks described above are asserted.

## CPU validation and pins

**21 CPU-only tests passed in 0.143s.** Native libraries were mocked, not loaded.
Coverage: exact opt-in/UUID and source pins; 14-file fixture integrity/missing
files; unsafe paths; fresh output; inherited settings; one OFF load/readout;
token/cardinality/prompt checks; preserved private failure log and shutdown;
offline flags; pre-load refusal and post-readout payload-drift failure.
Static checks: parsed AST, one explicit LLM construction/generate call, no
top-level native imports, no trailing whitespace.

| New /tmp file | SHA256 |
|---|---|
| astra_a100_native_readiness_20260913.py | `1d971c12e27ca00c4f1dcfb6158267b48b7944a142e62e64b9b3eab83b5a171d` |
| test_astra_a100_native_readiness_20260913.py | `7d549a6787e9f06ae255783353bd43855e8d104e4ddd5d5b9e26bc30373c86e8` |
| astra_a100_native_readiness_20260913.cpu.log | `a130ee7e465841db90156e7eb514559e198adf105e88d0ab661e89464dac8547` |

## Still untested for science

No native model-readiness outcome yet. Even an eventual PASS would not validate
adapter loading/routing, HF fitting/optimizer behavior, long prompts/generation,
the full Level1 panels, repetition/meta efficacy, other devices or A40 parity,
data provenance/contamination beyond the fixed model payload binding, parenting,
clean lineage, or the research mission. No training or benchmark run, source
runtime edit, original-root change, package installation, or Git action occurred.

EDITSTOP.

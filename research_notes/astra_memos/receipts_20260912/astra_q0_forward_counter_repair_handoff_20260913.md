# Q0 forward-counter instrumentation repair handoff

**EDITSTOP. Non-material instrumentation repair only.** Main owns artifacts, acceptance, integration, Git, and operations. Attempt1 remains immutable and NONREPORTABLE_RUNTIME_ABORT; this repair neither relabels nor resumes it. The original implementation handoff is preserved unchanged.

## Owned paths and final hashes

| Path | SHA256 |
|---|---|
| `gpu/astra_pairwise_q0.py` | `1459c037cccf2f043bc02f40fb9957f38c5620a4d0bcfc8cbb4ebf30fd31182a` |
| `tests/test_astra_pairwise_q0.py` | `bc08064301721157fa353247559105a31b11ee3e0c3b14d5dbbbfa255b9d42e3` |
| `/tmp/astra_q0_forward_counter_repair_handoff_20260913.md` | This new handoff; its hash is reported separately. |

Only those paths were edited. No archived source/helper/test, original handoff, capsule, root artifact, or archive-check sidecar was changed. Applicable instructions were checked. No pretrained weights, tokenizer, model download, network, GPU/native execution, Git operation, job launch/kill, package install, or later birth/relay/scientific-data read occurred. Tiny config-only Qwen tests are provided but could not execute in the available local environment.

## Cause and scoped repair

The previous worker registered its pre-forward hook on the causal-LM object returned by `model.get_base_model()` for PEFT. PEFT can call that object's `.forward` directly, bypassing its `nn.Module.__call__` hooks. Main reported zero model-call counters for the audit/PEFT fits while natural-prefix counters were positive; bare OFF counting worked. Those reported counters motivated this instrumentation repair, not a change to any scientific gate or interpretation of raw outcomes.

New `qwen_forward_decoder` at `gpu/astra_pairwise_q0.py:1678`:

- Accepts a real `Qwen2ForCausalLM` or `PeftModelForCausalLM` wrapping one.
- Resolves the registered causal-LM `.model` child to a real `Qwen2Model`.
- Checks Qwen2 model type, decoder/config identity, shared input embeddings, and layer-count consistency; rejects wrong architecture/path rather than falling back to an unverified hook owner.
- Requires the already-closed no-gradient-checkpointing recipe, preventing backward recomputation from becoming a different counter unit.

New `native_forward_counter` at `gpu/astra_pairwise_q0.py:1701` places the pre-forward hook on this shared real decoder. Both the PEFT direct-forward path and ordinary/generation causal-LM paths call the decoder module. The hook only increments the counter and returns no replacement arguments; it does not compute logits, alter gradients, consume RNG, or add forwards. Its context manager removes the hook and restores the prefix-counter context on success or exception, and rejects nested counters.

`native_worker` now uses that context at line1799. Counter names and DONE schema are unchanged. The reducer's exact native forward/token accounting check remains at line2063, unchanged and mandatory:

- audit:128 natural-prefix and128 model calls;
- fit:`128 + 4 * updates + 16` for both counters, hence148 at one update;
- evaluation:model calls equal prefix forwards plus generated-token count.

No expected counts were weakened, inferred from another counter, or fabricated. No reducer check was removed. Targets, maps, rank/LR/seed, canary mathematics, numerical policy, thresholds, update counts, lifecycle, caps, and hash-pinned historical helpers remain unchanged. There is no C11 expansion or scientific rescue.

## Regression tests

`ForwardCounterPlumbingTests` at `tests/test_astra_pairwise_q0.py:1155` adds three ordinary CPU Torch tests: no backward double-counting, cleanup after exception, and nested-context rejection with the outer context preserved. These patch the architecture resolver to a small Torch module and **are not Qwen/PEFT qualification**.

`TinyQwenForwardCounterTests` at line1195 adds five real config-only CPU regressions. They import installed Transformers/PEFT, construct `Qwen2ForCausalLM(Qwen2Config(...))` with a32-token vocabulary,16-wide one-layer decoder, and attach real PEFT LoRA. They do not call `from_pretrained`, load any tokenizer/weights, or download anything. The small model dimensions/generation length are fixtures, not alternate production recipe settings.

1. **Exact old-hook bypass reproduction and repaired training count:** simultaneously hooks the old causal wrapper and the corrected decoder; executes the actual PEFT natural-prefix forward, registered pairwise loss, backward, and AdamW update. Requires old wrapper count0, corrected model count1, natural count1, finite/nonzero LoRA gradients, and changed trainable parameters after the step.
2. **Instrumentation neutrality:** exact equality of hooked/unhooked logits and autograd gradients, unchanged RNG, and exactly one counted forward.
3. **OFF and adapter-ON generation:** actual cached greedy `generate` on a bare Qwen and a frozen real PEFT wrapper; each generates four fixture tokens. Requires model calls equal one explicit natural-prefix forward plus generated-token count, for both variants, with hook/context cleanup afterward.
4. **Architecture/no-checkpointing validation:** rejects an unrelated module, a replaced decoder path, and enabled checkpointing.
5. **Real-decoder exception cleanup:** an interruption removes the installed hook and restores context.

These five tests skip explicitly only when Torch/Transformers/PEFT are absent. Installed-but-broken imports are not silently replaced with mocks. Native acceptance must execute all five without skips.

## Exact local results

Available interpreter: `/tmp/astra_preservation_cpu_20260912/bin/python`, Python3.12.3, Torch2.8.0+cpu. Transformers and PEFT are absent; NumPy is also absent and produces the existing Torch warning. No dependency was installed.

Targeted command:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
/tmp/astra_preservation_cpu_20260912/bin/python -B -m unittest \
  tests.test_astra_pairwise_q0.ForwardCounterPlumbingTests \
  tests.test_astra_pairwise_q0.TinyQwenForwardCounterTests -v
```

Result:8 discovered,3 passed,5 explicitly skipped for absent Transformers/PEFT;0 failures/errors;0.065 seconds. This is **not** a successful execution of the real bypass regression.

Final full command, from the source root:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH="$PWD/tests:$PWD" \
/tmp/astra_preservation_cpu_20260912/bin/python -B -m unittest \
  tests.test_astra_pairwise_q0 \
  tests.test_semantic_objective_probe \
  tests.test_semantic_writer_diagnostic \
  tests.test_multikey_writer_gateway_simple \
  tests.test_writer_interface_calibration \
  tests.test_run_reasoning_neutral -q
```

Result: **217 discovered,212 passed,5 dependency skips,0 failures/errors;160.947 seconds.** All138 mandatory archived/helper tests passed; the five real tiny-Qwen tests remain unexecuted locally. The existing preparation acceptance rejects any skipped tests, so this local result cannot authorize a native launch.

## Main's required acceptance

Main reports an existing CPU-capable native environment with Torch2.13/Transformers5.5.3/PEFT0.20. Use that environment and the frozen source/support snapshot for the exact real regression first:

```bash
CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$SOURCE/tests:$SOURCE" \
  "$PY" -B -m unittest tests.test_astra_pairwise_q0.TinyQwenForwardCounterTests -v
```

Expected acceptance:5 real tests passed,0 skips. Then run the unchanged full CPU receipt workflow including its historical support manifest against the final source hashes. Expected full count is217 with0 failures/errors/skips. These are CPU config-only acceptance steps, not GPU/scientific proof. If the installed architecture/generation behavior disagrees, retain the failure and review this instrumentation; do not weaken expected counters or reinterpret attempt1.

Main must retain attempt1's archived original source for its authoritative replay. These changed source hashes are prospective only and cannot be substituted into that immutable run. No new root is prepared, authorized, or launched by this handoff.

## Historical helper identities rechecked

```text
98a90f33dcd5582b9e32fe21d08dd29283c82b955ff350c8c994d2903b2f0d41  gpu/astra_semantic_objective_probe.py
d6ea45ac6bfb5cabe6cbd1224f4cf101e96cbd0e07c029e934c2aa3e03e1ddb0  organism_v6/semantic_writer_diagnostic.py
b9fd33c7c11b2f57395f08d609bb1df004d9663eeefd143060bb1a24a34f10c8  organism_v6/multikey_writer_gateway_simple.py
9ab582ebc935ae36b88bd412fd06d799044661612f89a0770e46b92ab1b066c7  organism_v6/writer_interface_calibration.py
dd4f0a72cddc8226fa48ce50ab0faa6dd4e75f9db510aa89cfb5224898ee7496  organism_v6/run_reasoning_neutral.py
```

**EDITSTOP — bounded instrumentation code and tests frozen; Main owns real-dependency CPU acceptance and all subsequent operations.**

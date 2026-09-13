# Q0 forward-counter repair — bounded advisory review

**Reviewed:** 2026-09-13, final hash check 03:15:08 UTC.
**Disposition:** **Closed on bounded static review; no concrete residual defect identified in hook coverage unit, instrumentation neutrality, or cleanup.** No scientific gate, promotion, launch authorization, or reinterpretation of attempt1 is implied.

## Identities and comparison

Current files matched Main's supplied hashes at both checks:

```text
gpu/astra_pairwise_q0.py
1459c037cccf2f043bc02f40fb9957f38c5620a4d0bcfc8cbb4ebf30fd31182a

tests/test_astra_pairwise_q0.py
bc08064301721157fa353247559105a31b11ee3e0c3b14d5dbbbfa255b9d42e3

/tmp/astra_q0_forward_counter_repair_handoff_20260913.md
540eb33e5457b16b5ec122027c5574b0b45b6a0cf6567ec646651adb3025551a
```

Read-only `git show HEAD:<path>` confirmed that the committed original files were exactly the previously reviewed baselines:

```text
Original executor: 596071780b961031ef8ef5e352898391df47038db70e2acb68b5c3dbe15c201b
Original tests:    5e4eb5cb9926403319480b4bf8fc5d2225dd1768bb049909da604c1edb634afe
```

The two-path HEAD diff adds the decoder resolver and counter context, replaces the worker's old causal-wrapper hook with that context, and adds eight tests plus their discovery import. It does not change losses, numerical constants, targets, optimizer/update recipe, readout/reducer expectations, or terminal classification logic.

## Checks and conclusions

### Coverage unit — CLOSED

`gpu/astra_pairwise_q0.py:1678` resolves the actual registered `Qwen2Model` child of either the bare Qwen2 causal LM or its causal PEFT wrapper. Identity/config/embedding/layer checks prevent silently selecting a different descendant. The hook is on the whole decoder, not every transformer layer.

`gpu/astra_pairwise_q0.py:1710` therefore measures decoder invocations independently of whether PEFT enters the outer causal LM via `.forward` or `__call__`. The no-checkpointing check at line 1696 preserves the intended forward-only unit rather than counting backward recomputation. Prefix counting remains a separate measurement; model counts are not copied from it.

The unchanged reducer at `gpu/astra_pairwise_q0.py:2053` still requires audit 128/128; fit `128 + 4*updates + 16` for both counters (148 for one update); and evaluation prefix calls plus generated-token count. No failed count is made acceptable by this patch.

The real bypass regression at `tests/test_astra_pairwise_q0.py:1225` simultaneously requires old-wrapper count zero and corrected decoder/prefix counts one, with actual backward/update effects. Cached OFF and adapter-ON generation coverage is present at line 1267. These are appropriately targeted config-only tests, not claims about a loaded production model.

### Neutrality — CLOSED

`gpu/astra_pairwise_q0.py:1707` only increments a Python counter. It returns no replacement arguments, invokes no additional forward, changes no tensor/gradient, and calls no RNG operation. Resolver checks are observational; the counter does not change training/evaluation modes or the optimizer.

`tests/test_astra_pairwise_q0.py:1250` checks exact hooked/unhooked logits and autograd gradients plus unchanged RNG in deterministic evaluation. The training bypass test separately exercises the dropout-active PEFT path. The diff contains no numerical or scientific adjustment accompanying the instrumentation repair.

### Cleanup and worker integration — CLOSED

`gpu/astra_pairwise_q0.py:1701` rejects nesting before installing a second hook or replacing the context. Its `finally` removes the installed handle and resets the ContextVar token. `gpu/astra_pairwise_q0.py:1799` places audit, fit, evaluation, final budget/source checks, and DONE writing inside this context, so ordinary body exceptions also unwind it. Other preexisting hooks are not cleared wholesale.

Regression cases cover backward non-double-counting and removal at `tests/test_astra_pairwise_q0.py:1158`, exceptional cleanup at line 1170, nested rejection preserving the outer context at line 1179, and real-decoder cleanup at line 1298. No additional process-guard design is requested.

## Evidence boundary

Main reports all five real tiny-Qwen/PEFT CPU regressions passed on the native installed packages in **21.529 seconds, zero skips**. This is user-provided execution evidence, not a run independently performed or a receipt inspected by this reviewer. It addresses the handoff's earlier local dependency skips. The full 217-test run was described as in progress; no completion result is asserted here.

Only the repaired source/tests, their two committed baseline versions, and the new handoff were read for this review. Read-only Git show/diff was used solely for the requested baseline comparison; no Git state was changed. No tests, model, tokenizer, native worker, GPU, network, artifact replay, or later birth/relay input was used. Only this report was written.

Attempt1's immutable NONREPORTABLE_RUNTIME_ABORT status is taken from Main's statement and remains untouched. This patch is prospective instrumentation only; it is not a substitute source for attempt1's authoritative replay. No further repair is requested within this review's scope on these hashes.

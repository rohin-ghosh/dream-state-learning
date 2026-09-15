# Matched route behavior readout — September 15, 2026, 19:31 UTC

**Verified BEFORE/AFTER only; base-control comparison incomplete.** F1 cycles 13→14 and A1 cycles 12→13 were each evaluated on the same 32 public DEV prompts, with empty carried context, no parent, greedy decoding, and a fresh process for each condition. Eight tasks × two public contexts × two separately labelled prompt policies; no FINAL tasks, optimizer updates, or training-buffer writes.

| Branch | Prompt policy / public context | Changed outputs | Changed action strings | Median generated tokens, before→after | Responses with pre-action rationale, before→after |
|---|---|---:|---:|---:|---:|
| F1 | Minimal / initial | 4/8 | 2/8 | 34→11.5 | 5→3 |
| F1 | Minimal / supplied record | 0/8 | 0/8 | 12.5→12.5 | 0→0 |
| F1 | Explanation requested / initial | 8/8 | 4/8 | 138.5→139.5 | 8→8 |
| F1 | Explanation requested / supplied record | 8/8 | 3/8 | 133→118.5 | 8→8 |
| A1 | Minimal / initial | 0/8 | 0/8 | 12.5→12.5 | 0→0 |
| A1 | Minimal / supplied record | 0/8 | 0/8 | 12.5→12.5 | 0→0 |
| A1 | Explanation requested / initial | 3/8 | 1/8 | 13→13 | 3→3 |
| A1 | Explanation requested / supplied record | 3/8 | 1/8 | 43.5→43.5 | 4→4 |

All 128 verified BEFORE/AFTER responses terminated without truncation. Full generated text and token IDs remain in node-local call files. Historical route readouts also retain raw responses: a bare command is actual recorded behavior, not a logging omission. The explanation policy is an explicitly prompted diagnostic, not default behavior or a historical prompt replay.

**Interpretation:** A1's default-policy outputs are unchanged on all 16 prompts. F1 changes on four initial-context minimal prompts, with fewer rationale-bearing responses after the sleep. Explanation-requested responses change more frequently. These are text/action-string differences, not demonstrated improvement, coherent metacognition, generalization, or a causal effect of parenting. Action validity in the reduction is syntax only. No matched unparented-learning twin is present in this assay; LoRA-OFF would not supply one.

Both AFTER_LORA_OFF conditions generated their calls but failed the final read-only check: PEFT restored adapter `requires_grad` flags when leaving `disable_adapter()`. No COMPLETE receipt exists for either; neither is admitted to the comparison. Failed captures remain preserved, and no calls are retried or relabelled. The supervisor's `ASSAY_ATTEMPTS_FINISHED` means attempts ended, not that all conditions succeeded.

Prospective non-material repair: restore frozen parameter flags in sealed readouts without an optimizer, then perform the unchanged parameter-hash verification. Nineteen local probe/reducer tests pass, including wrong mounted-checkpoint rejection, no fabricated missing control, and forbidding this flag repair in training. Running v1 source was not modified. The prepared v2 export is not launched: repeating identical base-OFF inputs under a new name would not be new science. Physical ovx7 is handed back for cursor-preserving generation continuation after owner/provenance checks.

## Evidence

- Native reduction: `ovx:/localhome/local-rohing/orch_r124_route_behavior_20260915/RESULTS_1931.json`; copied here as a reduction only; SHA256 `73d675989c6f8cb8955869ed8a19b42db437014e0a9c90b665e4f60618bc7456`.
- Plan SHA256 `83933ffcd185a3721f0fb3b6b62d4845a64f47072a7b092ae436bd3eb0203654`.
- Identical prompt-file SHA256 in both branches: `e42cef46848b020718f246ebdd56f6198eb5a3fc0c69f67b467f112981a85f5d`.
- Raw root: `ovx:/localhome/local-rohing/orch_r124_route_behavior_20260915/run1`; all mounted-checkpoint, prompt, capture and COMPLETE bindings verified by the reducer for accepted conditions.
- Initial reduction command omitted PYTHONPATH and failed before reading model inputs; rerun with the frozen source on PYTHONPATH succeeded. Zero additional inference calls.

## Campaign coverage, not a success claim

Route and math are the sleeping pairs. Code and grid remain intentionally elicitation-only under R119, so they cannot answer a before/after-weight-sleep question. F3's C46 DEV receipt verifies all eight original clean system+user prompts with full raw text and token IDs (`R126_F3_DEV_CAPTURE.json` in the code analysis directory). Current grid per-cycle DEV coverage is missing; historical readouts must not be presented as current-epoch coverage. Math matched-readout controllers and current parent-delivery receipts are tracked separately; their success is not inferred from this route result.

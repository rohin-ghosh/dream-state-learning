# Note 23 — KV-eviction-as-learned-policy cluster + second external audit (2026-08-11)

Source: second external audit (adversarial prior-art hunt + code re-audit). All items
below verified by the auditor via direct fetch; re-verify at the Sep-20 re-sweep.

## The load-bearing find: KVP

**"Learning to Evict from Key-Value Cache" — arXiv:2602.10238 (Moschella, Manduchi,
Sener — Apple; ICML 2026).** Eviction reframed as RL: lightweight per-head RL agents
rank tokens by predicted usefulness for future decoding; frozen base LLM; enforced
budget; no architecture changes. Scope: KV cache only — no LTM, no consolidation.

**Impact on our claims:** the CONTEXT consumer of the tri-consumer claim is OCCUPIED.
Surviving differentiators (both required in print):
1. **Objective:** KVP's reward = future *decoding utility* (still in service of
   next-token, with lookahead). Ours = *distance-to-task-outcome* (AlphaGo-style
   value). "KVP learns what the model will want; Felt Attention learns what the task
   will need." Cost asymmetry honestly noted: their supervision is free (generation
   traces); ours needs environment rollouts — that's WHY the axis is still open.
2. **Tri-consumer unification:** one head + one value signal driving context + LTM
   writes + weight consolidation — nothing found crosses it.

**Cheapest novelty-isolating experiment (adopted into spec):** KVP-ablation — take a
KVP-style harness, swap reward from decoding-utility to task-outcome, hold all else
fixed, evaluate on an agentic task. One result = the objective claim, against a
published ICML baseline.

## Consumer-occupancy table (as of audit)

| Consumer | Occupied by | Gap left |
|---|---|---|
| Context/KV | KVP (RL, frozen, budget) | outcome-objective |
| LTM writes | AgeMem (REVISED Jul 2026 — now one GRPO policy over LTM+STM; re-read), D-MEM (heuristic), 2606.12945 (learned linear value fn) | attention-head form, outcome-trained into PARAMETRIC store |
| Weight consolidation | TMEM (online within-episode), COVE (rule+judge) | offline cross-episode learned head |
| **All three, one head/value** | **nobody** | **the claim** |

## Other IDs added by the audits (not previously in notes)

- **TRIM-KV (2512.03324):** learned per-token retention gate, frozen LLM, enforced
  budget, decay — distillation-trained, KV-scope. Weakens "importance-stratified
  retention unclaimed" → cite, claim outcome/cross-episode/consolidation deltas.
- **PM-Bench (2607.12385):** ports Virtual-Week paradigm to agent memory eval —
  paradigm-porting has precedent (with eMEM-Bench); our compound still unclaimed.
- Value-aware KV eviction cluster: 2606.03928 (stochastic value-aware eviction),
  **2605.08234 ("When Does Value-Aware KV Eviction Help?" — DIAGNOSTIC of regimes;
  read before designing the KVP-ablation, may pre-answer a regime question)**,
  2606.09916. Also: 2603.22329 (trained persistent memory for frozen LLMs),
  2607.17545 ("Retain or Consolidate?"), 2606.25115 (budget-curated on-device),
  2606.29178 (selective memory retention), 2512.12856 (Forgetful-but-Faithful:
  cognitive architecture + benchmark), 2606.14571 (StreamMemBench), 2607.10582
  (MemDecay).

## Code fixes from audit part 1 (all implemented, 27/27 tests)

1. **Gist/verbatim exposure confound (headline probe):** verbatim slot drew from all
   detail incl. one-shot facts → frequency faked a 0.21 dissociation from exposure
   alone. FIXED: verbatim draws from DR only (marginal-matched to SF by
   construction); permanent canary test: frequency dissociation must be ≈0
   (verified: −0.007 ± 0.171 over 25 seeds).
2. **C1 wording:** "beats untrained" was falsified by exp4's own table (value_z >
   trained_item everywhere). Corrected to "beats uniform; with a per-event signal,
   beats both" + explanatory note.
3. **Forgetting-curve age↔type confound:** full-class curve measured type, not decay
   (SF always young, SR always old). FIXED: SF-only curve + SR as labelled point +
   docstring caveat.
4. Stale test counts fixed everywhere.

## Scheduling

- **Final lit re-sweep: ~Sep 20** (not earlier) — NeurIPS notifications ~Sep 29 dump
  accepted-in-May work onto arXiv right at the ICLR deadline; position will move
  after we submit. Expect it; don't be surprised by it.
- Audit also confirmed: our lit notes contain NO fabricated IDs (6 spot-checked
  incl. suspicious-looking ones; all real, all accurately characterized).

## Spec decision forced by the audit (scorer vs modulator)

The prose implied head-as-MODULATOR ("your next token is interested in outcome");
the spec defines head-as-SCORER. DECIDED: **v1 = scorer** (head reads frozen hidden
states; its attention pattern drives external ops; zero interference — RLHF-value-
head pattern). **Modulator = v2** (Flamingo zero-init gating; "does the frozen model
degrade" becomes the central risk then). PAPER_SHEET §3 and IMPLEMENTATION_SPEC §2
updated to say scorer explicitly.

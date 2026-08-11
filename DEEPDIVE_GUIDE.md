# Deep-Dive Guide (for Rohin's morning read)

**Overnight summary in one line:** the red-team killed our headline CPU result
(it was an artifact stack), every artifact class is fixed with a canary now
guarding it, the missing LLM-facing half got built and gate-tested, and the
honest state is: *plumbing proven, ceiling measured, the head's real test moved
to the GPU tier where it always truly belonged.*

## How to read this repo in one sitting (order matters)

1. **This file**, then **`research_notes/redteam_4_felt_artifacts.md`** — the
   most instructive document in the repo: how a +0.12/t=5.9 "significant result"
   decomposed into a hardcoded constant, a label-leak-equivalent keyword gate,
   a cosine-floor confound, and salted-hash irreproducibility.
2. **`SIZING.md`** (post-audit corrected) — every GPU decision + recalibration rule.
3. **`IMPLEMENTATION_SPEC.md`** — incl. §5b amendments recorded tonight.
4. **The code** (~1,300 lines numpy, all CPU):
   - `game/dag.py` → `game/engine.py` (note: move-anywhere semantics — knowledge
     must be actionable; decor emitted on visit steps) → `game/generator.py`
   - `felt/head.py` (deterministic hashlib embeds) → `felt/fastweight.py` →
     `felt/baselines.py` (floor-corrected probes, online surprise, keyword_gate
     canary, oracle_weight ceiling) → `felt/harness.py` (checkpoint/resume)
   - `felt/llm_player.py` + `felt/gates.py` — the LLM-facing half built tonight:
     MockTextPlayer (a text-driven planner that only knows its prompt — passes
     win@manual=1.0 / win@none=0.0, proving game difficulty is purely knowledge),
     HFBackend (code-complete, GPU), manual/memory context injection, S0 gates.
5. **`experiments/REPORT_exp6.md`** — read the RETRACTION banner as a worked
   example of the failure mode this project's process exists to catch.
6. `research_notes/redteam_6_sizing_spec.md` — the honesty audit that forced the
   LLM-half build and the spec amendments.

## What the overnight audit found & what was fixed

| finding (redteam_4/6) | severity | fix (all tested) |
|---|---|---|
| "Felt effect" carried by a hardcoded 0.05 fallback (decor bypassed the head) | CRITICAL | decor facts now emitted on visit steps; fallback path banned by assert |
| Fact type ≡ action type → keyword gate ≡ label leak, BEAT the trained head | CRITICAL | detour rollouts (`scripted_noisy_play`) create within-type salience variance; `keyword_gate` = permanent canary policy |
| Cosine-floor confound: never-written fakes scored 0.595 | CRITICAL | floor-corrected probes (score − matched never-written fake); random detail sampling |
| Salted `hash()` → irreproducible runs (result varied 0.003–0.186 across draws) | HIGH | hashlib-based deterministic embeddings + determinism test |
| Pre-write "surprise" was init noise | MED | online per-chunk surprise vs current memory |
| Count-fact text collisions (24× reinforcement) | MED | episode ids in fact text |
| Ledger "GREEN" while the LLM half had zero code; 0/5 gates runnable | CRITICAL (honesty) | built `llm_player.py` + `gates.py`; gates now run on CPU via mock |
| SIZING errors (fact count, decode volume, 1.5B optimism) | MED | corrected; 3B budgeted as likely |
| Spec↔code deviations (goal-conditioning, d′ gate vacuity, LoRA claim) | MED | §5b amendments recorded |

## The honest post-fix state (this is the part to internalize)

- On the corrected metric, **all realistic policies ≈ 0 differentiation** with
  mock embeddings — felt, keyword gate, surprise, uniform alike.
- The **oracle-weight ceiling exists and expresses at hidden≥128**: +0.11
  (soft) / +0.22 (hard filter), AP 0.70–0.80. The instrument works; nothing
  learnable-from-mocks reaches the ceiling.
- Therefore the CPU tier's proven role is: **plumbing, canaries, gates, and the
  measured ceiling.** The head-works question is answered ONLY by real LLM
  hidden states — which is what the lease is for, with the §5b run-1 gate
  (head regret on real states ≤ ~3× mock's 0.03) as the hour-12 kill-switch.
- This is a BETTER pre-lease position than last night's fake positive: we now
  know exactly what signal must appear, exactly how we'll know, and exactly
  what it costs to find out.

## What was deliberately simplified
- One shared solver core (`_solve`) for optimal + noisy players.
- exp6 script deprecated rather than rewritten — the harness IS the experiment.
- v1 head stays goal-agnostic (spec §5b); LoRA claim removed (run-2 scope).

## Known limitations carried into the GPU tier (not hidden)
- Mock hash embeddings ≠ LLM states — the central open question, by design.
- MockTextPlayer is a planner, not an LLM — gates measure plumbing, not model skill.
- `dmem_style` lacks its prompted-utility half until the LLM tier.
- Closed-loop winnability (S4) code = the LLM-player loop exists, but the
  memory-condition wiring into S4 is first-lease work (S0-S3 are fully coded).
- Agent-2 code-validity report pending at write time; fold in if it lands.

## THE LEASE SPEC (when you've done the deep-dive and are satisfied)

- **Pool:** `general` (self-service). Node: **1× A100-80GB** (July's Pauli-80GB
  class is exactly right). The GB100 you saw works too but is overkill; don't
  spend pool-politics on it.
- **Duration: 48h** (the default), **one lease** to start. Second 48h only after
  S0-S2 results are in. (NOT 2 hours; and re-check the form's end-date bug.)
- **Justification text:** "LLM agent memory research: rollout generation and
  evaluation for a retention benchmark (single-node inference, Qwen2.5-1.5B/3B)."
- **Before booking, run locally once:** `PYTHONPATH=. python3 tests/test_felt.py
  && python3 tests/test_game.py && python3 tests/test_structmem.py` (47 tests).
- First-hour on the node: env setup script + S0 gates with the real model —
  the SIZING §5 table then tells you (and me) exactly what to do next.

## Design calls that are YOURS to overturn
- Fact taxonomy (what counts as gist vs detail) and the decor/count noise mix.
- Detour rate (0.25) and whether detours should also include failed-craft events.
- β form (multiplicative on surprise) and the swept range.
- Gate thresholds (0.85/0.35; the ≤3×-mock-regret run-1 gate).
- 1.5B-first vs 3B-first given the audit's ALFWorld evidence.

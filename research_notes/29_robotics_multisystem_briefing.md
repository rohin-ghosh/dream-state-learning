# Note 29 — Robotics multi-system briefing (agent-verified, 2026-08-15)

## Four transfers
1. FAST/SLOW WITH NEVER-BLOCK: all shipped stacks (Helix 7Hz→latent→200Hz;
   pi0.5 text-subtask interface; GR00T cross-attn; Atlas MPC) run the slow
   layer ASYNC — fast loop always acts on the LAST slow output. Adopt as a
   hard rule for the workspace loop (event-driven cadence, confirmed).
2. BG ARBITRATION + HYSTERESIS: Gurney/Prescott/Redgrave salience-bid
   selection worked on robots BUT deadlocked at equal salience (= our
   ping-pong loop, rediscovered) — fix: persistence bias for the current
   selection. (Also explains why temperature fixed our loops.)
3. CURRENCY VERDICT: TraderBots priced tasks as expected profit; Dias et al.
   2006 survey: bid-estimation quality is THE practical difficulty — prices
   were hand-engineered, never learned. Russell-Wefald VOC → resource-
   rational metalevel MDPs → 2024-26 LLM token-budget work. THE FELT HEAD IS
   A LEARNED BID ESTIMATOR; ITS CALIBRATION (not just ranking AUC) IS THE
   CORE RESEARCH RISK. Session-2 metric: calibration curves for the head.
4. SEMANTIC STORES > EPISODE LOGS: robotics' only proven LTM is structured
   queryable spatial-semantic maps (ConceptGraphs, CLIP-Fields); no deployed
   VLA has episodic memory (field-wide gap = ours). Validates fact-based
   memory over trajectory hoarding.

## Cautionary tale
LIDA never ran a physical robot; serial cognitive cycles died on real-time
requirements (Soar/ACT-R robot deployments stayed in toy environments).
Rule: the workspace deliberates; it NEVER owns the clock.

## Continual learning on robots (2025-26 state)
pi*0.6 RECAP (advantage-conditioned RL on autonomous rollouts) and DYNA-1
improve WEIGHTS from experience — competence-CL is starting; knowledge-CL
(queryable episodic stores) remains unbuilt everywhere.

# Note 25 — World-model & GWT landscape, Aug 2026 (agent-verified sweep)

Triggered by Rohin's amodal-central-model musing (2026-08-11, night of lease 1).
Sources verified by a web-research agent against primary pages; arXiv IDs listed.
**Caveat: re-verify all 2026 IDs at write-up (standing rule).**

## 1. LeCun / world-model program
- JEPA line: I-JEPA (2301.08243) → V-JEPA → V-JEPA 2 (2506.09985, action-conditioned,
  zero-shot Franka manipulation) → LeJEPA (2511.08544, provable anti-collapse via
  SIGReg) → identifiability theory (2605.26379, 2607.22430).
- LeCun left Meta Nov 19 2025 → **AMI Labs** (Paris, CEO Alexandre LeBrun);
  $1.03B seed at ~$4.5B post (Mar 2026; NVIDIA, Bezos Expeditions, Temasek…).
  Agenda names **persistent memory** as a pillar. NOTHING SHIPPED as of mid-2026
  (BBC July 2026: refining through year-end).
- Arena: Genie 3 → Project Genie (public Jan 2026); Waymo World Model (Feb 2026);
  World Labs Marble (commercial, $1B raise Feb 2026); Odyssey-2/Starchild/Agora;
  Decart; NVIDIA Cosmos 3 (June 2026, open omnimodel).

## 2. GWT in AI
- Architecture thread lives mainly in VanRullen's group: **Multimodal Dreaming**
  (2502.21142) = GW latent as fusion space for Dreamer-style world-model RL —
  the closest world-model×workspace combination. Also chained-operations routing
  (2025), ASAC attention-schema (2509.16058).
- **Headline: Anthropic, "Verbalizable Representations Form a Global Workspace in
  Language Models" (Transformer Circuits, July 2026)** — sparse mid-layer "J-space"
  (~10% activation variance, found via open-sourced Jacobian lens) behaves like a
  GWT workspace inside Claude-family LLMs. Formal commentaries by Dehaene & Naccache
  and Eleos AI. Directly relevant to us: workspace-like structure EXISTS in frozen
  LLM hidden states — the substrate our head reads.
- Consciousness-assessment thread: Butlin & Long rubric updated (TiCS Jan 2026,
  19 authors incl. Bengio/Chalmers/VanRullen); J-space is its main empirical case.

## 3. Verdict for us
- **No one in either camp does memory-write selection.** World-model camp treats
  persistent memory architecturally (AMI pitch, Genie memory horizon), never as a
  learned retention decision. GWT camp has the concept (workspace admission = a
  salience gate) but trains routing for within-episode computation, never against
  long-horizon outcomes over an external store.
- Positioning sentence banked: an outcome-trained salience head on a frozen LLM is
  an **operationalized GWT broadcast gate supplying the persistent-memory leg of
  the world-model agenda** — an open seam between the two programs. (Discussion
  section material; the paper stays anchored to memory/RL literature.)
- Anthropic J-space gives a concrete follow-up experiment: does our head's learned
  direction live in / near the J-space? (If their Jacobian lens is open-sourced,
  this is cheap and would be a striking interpretability tie-in. Post-paper-1.)

## 4. ACTION ITEMS (competitive)
- Agent-flagged possible NEW competitors not in notes 12-19:
  **2606.10616 "Learning What to Remember"** and **2606.05894 "EMBER" (budgeted
  retention)** — deep-read dispatched 2026-08-11 (night); verdict to be appended.
- Memory-R1 (2508.19828) confirmed ACL 2026 — already in our landscape (RL memory
  ops on external store; tool-call line, not a collision).

# Note 28 — GWT engineering briefing (agent-verified, 2026-08-15)

Full briefing delivered in-session; essentials preserved here.

## Five algorithmic commitments (Baars/Dehaene)
limited-capacity workspace → competition/coalitions → IGNITION (all-or-none
threshold) → global broadcast → broadcast-gated learning & memory writes.
Implementation skeleton: parallel specialists → salience bidding →
thresholded winner-take-all → broadcast → gated LTM write → next cycle.

## Implementations
- **LIDA** (Franklin ~2006-16; BICA 2016 tutorial): the complete blueprint.
  Cognitive cycle: percepts → preconscious workspace → CUE-BASED LTM read →
  attention codelets (salience daemons = felt attention pluralized) →
  coalition competition → broadcast → action; EVERY broadcast drives
  perceptual/episodic/procedural/attentional learning. WRITE = BROADCAST-
  GATED (admission = encoding, in the literature since 2006).
- Dehaene-Changeux GNW sims (ignition math; 2005 PLoS Biol).
- Goyal-Bengio Shared Workspace (2103.01197, ICLR'22): latent slots, top-k
  attention competition, bottleneck AS inductive bias; admission trained
  end-to-end on task loss (differentiable, not outcome-RL).
- VanRullen-Kanai GLW (2012.10390): frozen pretrained modules + learned
  latent translation = frozen-engine-plus-bridge. GW-Dreamer (2502.21142):
  RL dreaming inside the GW latent.
- 2025-26: GW Agents (2604.08206, LLM multi-agent hub, heuristic salience);
  Ignition Index (2608.05160: transformers ignite, Mamba ~doesn't);
  Anthropic J-space (Jul'26): emergent latent workspace inside Claude —
  ~25 concurrent concepts, all-or-none commitment.

## Answers
(a) Serious workspaces are LATENT; text loops = the slow symbolic tier.
    Two-workspace architecture: fast J-space inside the frozen model (free) +
    slow auditable symbolic workspace outside (ours).
(b) Exit = ignition threshold (workspace-enforced, not model-emitted).
(c) Memory paths: only LIDA has both — cue-based read, broadcast-gated write.
(d) TRAINED ADMISSION ON TASK OUTCOMES: nobody does it. Felt attention is
    novel exactly there.

## Verdict (the positioning gift)
Open problems per the field's own map: (1) learned admission from task
outcomes; (2) LTM coupling with learned components (LIDA modernized).
= felt attention + the wake-sleep memory system. Our pocket is the two
unbuilt rooms. Reading list: LIDA tutorial FIRST, then Goyal 2103.01197,
VanRullen 2012.10390, Ignition Index, J-space commentary.

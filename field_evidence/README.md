# Field evidence — dreaming learned from real use, not guessed
Artifacts from real deployed systems that do (manual or amortized)
versions of what the dream-state architecture automates. Purpose: ground
the dreamer's design in observed practice — what distillation actually
keeps, how feedback compounds, where summaries fail.

Contents:
- (pending) debug-agent self-report — Rohin's NVIDIA CURE tool-intelligence
  agent: ~2 months of human-feedback-driven distillation of a complex debug
  workflow into a ~5k-token subagent prompt; effectively a continuously
  amortized dreamer on a real workload. Source (NVIDIA-internal):
  gitlab-master.nvidia.com/nvl-ai/cure_fw/cure-fw
  feature/cure-tool-intelligence: demo/dream-state-learning-agent-self-report.md
  NOTE: internal artifact — check before quoting in any public paper.

What to mine from it (once here): which lessons survived distillation vs
got dropped; format of the distilled knowledge (rules? examples? both?);
how corrections were incorporated (overwrite vs append); the manual
equivalents of salience, renormalization, and forgetting.

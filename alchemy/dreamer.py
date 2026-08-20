"""Dreamer (SPEC_V2 §6): episode log -> LoRA training corpus, as TEXT.

dumb_dream  = raw transcription (substrate control arm).
llm_dream   = one prompted LLM call per episode chunk; sees episodes +
              outcomes + value logs (episode hindsight OK, eval set never);
              emits CROSS-EPISODE pattern memories in 2nd person.
Every emitted line passes the G2 leakage scan before entering the corpus.
"""

from __future__ import annotations

DREAM_SYS = (
    "You are the dream of an alchemist agent, consolidating its recent "
    "experience into long-term memories. Below are episode logs (goal, "
    "combine attempts, outcomes, success). Write memories as short "
    "second-person statements. PREFER cross-episode patterns ('Whenever "
    "you combine X with Y-like items, ...', 'X seems to react the same "
    "way as Z') over single-episode summaries. Include which combinations "
    "produce nothing or ruin the mixture — negative knowledge counts. "
    "Output one memory per line, no numbering, max {n} lines.")


def episodes_to_text(episodes: list) -> str:
    lines = []
    for i, ep in enumerate(episodes):
        lines.append(f"[episode {i}] goal: craft {ep['target']} | "
                     f"success: {ep['success']}")
        for st in ep["log"]:
            lines.append(f"  {st['action']} -> {st['obs']} "
                         f"(value {st['value_after']})")
    return "\n".join(lines)


def dumb_dream(episodes: list) -> list:
    """Raw log -> flat factual lines. No curation, no generalization."""
    out = []
    for ep in episodes:
        for st in ep["log"]:
            out.append(st["obs"])
    return sorted(set(out))


def llm_dream(episodes: list, model, tokenizer, world,
              chunk: int = 10, max_lines: int = 40) -> list:
    """Legacy HF path (smoke test)."""
    from alchemy.backend import HFBackend
    be = HFBackend.__new__(HFBackend)
    be.model, be.tok, be._adapters = model, tokenizer, {}
    return backend_dream(episodes, be, world, chunk, max_lines)


def backend_dream(episodes: list, backend, world,
                  chunk: int = 96, max_lines: int = 60) -> list:
    """Sleep-cadence dreaming: one prompted call per ~context of episodes
    (SPEC_V2 sleep cadence: ~96 eps @ 332 tok/ep ~= 32k). Batched."""
    prompts = []
    for i in range(0, len(episodes), chunk):
        block = episodes_to_text(episodes[i:i + chunk])
        prompts.append(DREAM_SYS.format(n=max_lines) + "\n\n" + block)
    out = []
    for txt in backend.generate(prompts, max_tokens=1200):
        for line in txt.splitlines():
            line = line.strip(" -*")
            if len(line) > 12 and not world.leakage_scan(line):
                out.append(line)
    return out

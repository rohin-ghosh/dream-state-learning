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
    import torch
    out = []
    for i in range(0, len(episodes), chunk):
        block = episodes_to_text(episodes[i:i + chunk])
        msgs = [{"role": "system",
                 "content": DREAM_SYS.format(n=max_lines)},
                {"role": "user", "content": block}]
        prompt = tokenizer.apply_chat_template(
            msgs, tokenize=False, add_generation_prompt=True)
        ids = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            gen = model.generate(**ids, max_new_tokens=600, do_sample=False,
                                 pad_token_id=tokenizer.eos_token_id)
        text = tokenizer.decode(gen[0][ids["input_ids"].shape[1]:],
                                skip_special_tokens=True)
        for line in text.splitlines():
            line = line.strip(" -*")
            if len(line) > 12 and not world.leakage_scan(line):
                out.append(line)
    return out

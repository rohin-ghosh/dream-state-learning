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
    "State every pair fact in BOTH orders (X with Y, and Y with X) and vary "
    "your phrasing across lines — do not repeat one template. Also include "
    "goal-form lines ('To craft Z, combine X and Y.'). "
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
    """Raw log -> flat factual lines. No curation, no generalization.
    NO dedup: natural frequency is signal (facts experienced often should
    be trained often — free exposure weighting)."""
    out = []
    for ep in episodes:
        for st in ep["log"]:
            out.append(st["obs"])
    return out


PARA_PRODUCT = (
    "You combine {a} and {b}. They fuse into {p}.",
    "Combining {a} with {b} yields {p}.",
    "{a} and {b} together make {p}.",
    "To craft {p}, combine {a} and {b}.",
    "Q: What happens when you combine {a} and {b}? A: PRODUCT {p}",
    "Mixing {b} with {a} produces {p}.",
)
PARA_NOTHING = (
    "You combine {a} and {b}. Nothing happens.",
    "{a} and {b} do not react.",
    "Q: What happens when you combine {a} and {b}? A: NOTHING",
)
PARA_RUIN = (
    "You combine {a} and {b}. The mixture curdles and is ruined.",
    "{a} and {b} ruin the mixture.",
    "Q: What happens when you combine {a} and {b}? A: RUIN",
)


def augment_corpus(episodes: list, world, abstain_frac: float = 0.15,
                   seed: int = 0) -> list:
    """Exposure manufacturing (spec REQUIREMENT, was unimplemented):
    every observed fact -> both orderings x varied templates (incl. a
    QA-format slice), plus an UNKNOWN slice for never-observed pairs so
    calibrated abstention exists in-weights. Frequency preserved: a fact
    seen k times is augmented k times."""
    import numpy as np
    rng = np.random.default_rng(seed)
    out = []
    seen = set()
    for ep in episodes:
        for st in ep["log"]:
            _, a, b = st["action"].split(" ")
            seen.add(tuple(sorted((a, b))))
            kind, prod = world.predict(a, b)
            tpl = (PARA_PRODUCT if kind == "product"
                   else PARA_RUIN if kind == "ruin" else PARA_NOTHING)
            for t in tpl:
                for x, y in ((a, b), (b, a)):
                    out.append(t.format(a=x, b=y, p=prod))
    # abstention slice: unseen base pairs -> UNKNOWN (never eval holdout
    # specifically — sampled from ALL unseen, holdout is a subset; the
    # model learns 'unseen => unknown', not holdout answers)
    names = sorted(world.ingredients)
    # CAP the abstention slice: it must teach 'unseen => unknown' as a
    # BEHAVIOR without materially covering the unseen space (an uncapped
    # slice would UNKNOWN-train much of the holdout and suppress the
    # extrapolation measurement)
    n_abs = min(int(len(out) * abstain_frac), 2500)
    tries = 0
    while n_abs > 0 and tries < n_abs * 20:
        tries += 1
        a, b = rng.choice(names, 2, replace=False)
        if tuple(sorted((a, b))) in seen:
            continue
        out.append(f"Q: What happens when you combine {a} and {b}? "
                   "A: UNKNOWN")
        n_abs -= 1
    rng.shuffle(out)
    return out


def llm_dream(episodes: list, model, tokenizer, world,
              chunk: int = 10, max_lines: int = 40) -> list:
    """Legacy HF path (smoke test)."""
    from alchemy.backend import HFBackend
    be = HFBackend.__new__(HFBackend)
    be.model, be.tok, be._adapters = model, tokenizer, {}
    return backend_dream(episodes, be, world, chunk, max_lines)


def backend_dream(episodes: list, backend, world,
                  chunk: int = 96, max_lines: int = 60,
                  token_budget: int = 22000) -> list:
    """Sleep-cadence dreaming, TOKEN-BUDGETED: accumulate episodes until
    ~token_budget input tokens, then dream that chunk (chain episodes vary
    in length, so fixed episode counts can overflow the window — canary
    bug 2026-08-21)."""
    count = (backend.n_tokens if hasattr(backend, "n_tokens")
             else lambda t: len(t) // 4)
    prompts, cur, cur_tok = [], [], 0
    for ep in episodes:
        t = count(episodes_to_text([ep]))
        if cur and cur_tok + t > token_budget:
            prompts.append(DREAM_SYS.format(n=max_lines) + "\n\n"
                           + episodes_to_text(cur))
            cur, cur_tok = [], 0
        cur.append(ep); cur_tok += t
    if cur:
        prompts.append(DREAM_SYS.format(n=max_lines) + "\n\n"
                       + episodes_to_text(cur))
    out = []
    for txt in backend.generate(prompts, max_tokens=1200):
        for line in txt.splitlines():
            line = line.strip(" -*")
            if len(line) > 12 and not world.leakage_scan(line):
                out.append(line)
    return out

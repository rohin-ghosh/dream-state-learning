"""LLM player loop for FeltCraft — the missing LLM-facing half (audit redteam_6).

Everything here is CPU-testable via MockTextPlayer (a TEXT-DRIVEN scripted player
that only knows what's in its prompt — so manual rendering, memory→context
injection, and action parsing are all genuinely exercised on CPU). HFBackend is
code-complete for the GPU tier (lazy torch import; never required locally).

Context modes (the calibration gates of SIZING §1):
  none    — obs only                               → win floor (gate: ≤0.35)
  manual  — obs + full world manual                → win ceiling (gate: ≥0.85)
  memory  — obs + facts the MEMORY retained (top-k by probe score over the
            agent's own experienced-fact log)      → the competitive condition
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional, Protocol

import numpy as np

from game import World, FeltCraft
from game.dag import requirements
from .head import hash_embed


# ------------------------------------------------------------------ rendering
def render_manual(world: World) -> str:
    lines = ["WORLD MANUAL:"]
    lines += [f"- crafting {it} requires {a} and {b}"
              for it, (a, b) in world.dag.recipes.items()]
    lines += [f"- {r} is found at {l}" for r, l in world.raw_locations.items()]
    return "\n".join(lines)


def render_memory_context(retained_facts: list, k: int = 12) -> str:
    if not retained_facts:
        return "MEMORY: (empty)"
    return "MEMORY (from past episodes):\n" + \
        "\n".join(f"- {t}" for t in retained_facts[:k])


_FEWSHOT = (
    "EXAMPLE (goal: craft plank; context says: crafting plank requires wood "
    "and wood; wood is found at site_9):\n"
    "NOW: [step 3] No wood here. [At: site_2. Inventory: empty.]\n"
    "ACTION: move site_9\n"
    "NOW: [step 4] You move to site_9. Resources here: wood. [At: site_9. Inventory: empty.]\n"
    "ACTION: gather wood\n"
    "NOW: [step 5] You gather 1 wood. [At: site_9. Inventory: woodx1.]\n"
    "ACTION: gather wood\n"
    "NOW: [step 6] You gather 1 wood. [At: site_9. Inventory: woodx2.]\n"
    "ACTION: craft plank\n")


def build_prompt(obs: str, context_block: str, history: list, n_hist: int = 6) -> str:
    hist = "\n".join(f"> {a}\n{o}" for a, o in history[-n_hist:])
    return (
        "You play a crafting game. Actions: explore | move <site> | "
        "gather <raw> | craft <item> | inspect. Reply with exactly ONE action, "
        "like 'move site_2' or 'gather raw_1' or 'craft c1_0' — no extra words.\n"
        "Strategy: if a resource is NOT at your current site, look up which site "
        "has it in your context and move there first. Craft sub-items in "
        "dependency order.\n\n"
        f"{_FEWSHOT}\n{context_block}\n\nRECENT:\n{hist}\n\nNOW: {obs}\nACTION:")


VERBS = ("explore", "move", "gather", "craft", "inspect")
_FILLER = {"to", "the", "a", "an", "from", "at", "in", "on", "some", "one"}


def parse_action(text: str) -> str:
    """Canonicalize to 'verb' or 'verb <arg>' (single arg token). S0 field bug 2:
    models answer in natural language — 'gather raw_2 from site_3' — and passing
    the raw tail to the engine made the item lookup fail every time. The harness
    is lenient; the ENGINE stays strict."""
    for line in text.strip().splitlines():
        l = line.strip().lower().lstrip("> ").removeprefix("action:").strip()
        toks = [t.strip(".,!?:;\"'`*()") for t in l.split()]
        toks = [t for t in toks if t]
        if not toks or toks[0] not in VERBS:
            continue
        verb = toks[0]
        if verb in ("explore", "inspect"):
            return verb
        arg = next((t for t in toks[1:] if t not in _FILLER), "")
        return f"{verb} {arg}".strip()
    return "inspect"


# ------------------------------------------------------------------ backends
class Backend(Protocol):
    def generate(self, prompt: str) -> str: ...


@dataclass
class MockTextPlayer:
    """Scripted player that reasons ONLY from its prompt text: it parses recipe/
    location facts out of the context block, tracks what it has seen this episode,
    and plans with the same requirements logic as the solver — but ONLY over
    knowledge visible in the prompt. Genuinely exercises the plumbing: if the
    manual renderer or memory injection breaks, this player gets dumb."""
    fail_rate: float = 0.0            # chance of a random action (noise knob)
    _rng: object = field(default_factory=lambda: np.random.default_rng(0))
    # per-episode scratch (reset by caller creating a new instance per episode)
    known_recipes: dict = field(default_factory=dict)
    known_locs: dict = field(default_factory=dict)
    inventory: dict = field(default_factory=dict)
    goal: str = ""
    at: str = ""

    def _ingest(self, prompt: str):
        for m in re.finditer(r"crafting (\S+) requires (\S+) and (\S+)", prompt):
            self.known_recipes[m.group(1)] = (m.group(2), m.group(3))
        for m in re.finditer(r"(\S+) is found at (\S+)", prompt):
            self.known_locs[m.group(1)] = m.group(2)
        for m in re.finditer(r"Resources(?: here)?: ([^.\n]+)", prompt):
            pass  # location contents visible in obs; locs learned via explore lines
        for m in re.finditer(r"find (site_\d+)", prompt):
            pass
        g = re.search(r"craft (\S+?)\.?(?:\s|$)", prompt.split("Your goal:")[-1]) \
            if "Your goal:" in prompt else None
        if g:
            self.goal = g.group(1).rstrip(".!")
        inv = re.findall(r"Inventory: ([^.\n]+)", prompt)
        if inv:
            self.inventory = {}
            for tok in inv[-1].split(","):
                tok = tok.strip()
                m = re.match(r"(\S+)x(\d+)", tok)
                if m:
                    self.inventory[m.group(1)] = int(m.group(2))
        at = re.findall(r"(?:move to|find|At:) (site_\d+)", prompt)
        if at:
            self.at = at[-1]

    def generate(self, prompt: str) -> str:
        self._ingest(prompt)
        if self._rng.random() < self.fail_rate:
            return f"ACTION: {['explore','inspect'][int(self._rng.random()*2)]}"
        goal = self.goal
        if not goal:
            return "ACTION: inspect"
        # plan over KNOWN recipes only
        if goal not in self.known_recipes:
            return "ACTION: explore"          # can't plan → look around (weak)
        # emulate requirements() over known recipes
        need_raw, crafts, missing_recipe = [], [], False
        def expand(it, have):
            nonlocal missing_recipe
            if have.get(it, 0) > 0:
                have[it] -= 1
                return
            if it in self.known_recipes:
                a, b = self.known_recipes[it]
                expand(a, have); expand(b, have)
                crafts.append(it)
            elif it.startswith("raw_"):
                need_raw.append(it)
            else:
                missing_recipe = True
        expand(goal, dict(self.inventory))
        if missing_recipe:
            return "ACTION: explore"
        if need_raw:
            r = need_raw[0]
            loc = self.known_locs.get(r)
            if loc is None:
                return "ACTION: explore"
            if self.at != loc:
                return f"ACTION: move {loc}"
            return f"ACTION: gather {r}"
        for c in crafts:
            a, b = self.known_recipes[c]
            if self.inventory.get(a, 0) >= 1 and self.inventory.get(b, 0) >= 1:
                return f"ACTION: craft {c}"
        return f"ACTION: craft {crafts[0]}" if crafts else "ACTION: inspect"


class HFBackend:
    """Frozen HF model backend (GPU tier). Lazy imports; code-complete.
    get_event_states caches per-event hidden states for head training."""

    def __init__(self, model_name: str, device: str = "cuda",
                 layers: tuple = (-1, -4, -8), max_new_tokens: int = 24):
        import torch  # noqa — GPU tier only
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype=torch.bfloat16, device_map=device,
            output_hidden_states=True)
        self.model.eval()
        for p in self.model.parameters():
            p.requires_grad = False
        self.layers = layers
        self.max_new_tokens = max_new_tokens

    def generate(self, prompt: str) -> str:
        t = self.torch
        try:   # Instruct models need their chat template (P1-6)
            prompt = self.tok.apply_chat_template(
                [{"role": "user", "content": prompt}], tokenize=False,
                add_generation_prompt=True)
        except Exception:
            pass
        ids = self.tok(prompt, return_tensors="pt").to(self.model.device)
        with t.inference_mode():
            out = self.model.generate(**ids, max_new_tokens=self.max_new_tokens,
                                      do_sample=False,
                                      pad_token_id=self.tok.eos_token_id)
        return self.tok.decode(out[0, ids["input_ids"].shape[1]:],
                               skip_special_tokens=True)

    def get_event_states(self, text: str) -> dict:
        """Multi-layer last-token hidden states for one event text (head input).
        Multi-layer per gate-3's fallback plan (redteam_6)."""
        t = self.torch
        ids = self.tok(text, return_tensors="pt", truncation=True,
                       max_length=512).to(self.model.device)
        with t.inference_mode():
            out = self.model(**ids)
        return {l: out.hidden_states[l][0, -1].float().cpu().numpy()
                for l in self.layers}


# ------------------------------------------------------------------ episode
def retained_fact_texts(memory, fact_log: list, k: int = 12) -> list:
    """Memory as a RETENTION FILTER over the agent's own experienced-fact log:
    rank logged fact texts by the memory's probe score; return top-k texts.
    (The memory never stores raw text — it gates what the agent may re-see.)"""
    if not fact_log:
        return []
    K = np.stack([hash_embed("KEY::" + t, 32) for t in fact_log])
    V = np.stack([hash_embed("VAL::" + t, 32) for t in fact_log])
    scores = memory.probe(K, V)
    order = np.argsort(-scores)[:k]
    return [fact_log[i] for i in order]


def play_episode(world: World, backend: Backend, goal: str, episode_seed: int,
                 context_mode: str = "none", memory=None, fact_log=None,
                 known_locations: Optional[set] = None, max_steps: int = 60,
                 trace=None) -> dict:
    env = FeltCraft(world, max_steps=max_steps)
    r0 = env.reset(goal, episode_seed, known_locations)
    if context_mode == "manual":
        ctx = render_manual(world)
    elif context_mode == "memory":
        ctx = render_memory_context(
            retained_fact_texts(memory, fact_log or []))
    else:
        ctx = "CONTEXT: (none)"
    # The goal must be in EVERY prompt: stateless backends forget it otherwise
    # (S0 field bug: it only rode the first obs, so from step 2 the model played
    # blind — win@manual == win@none == chance, manual worthless without a target).
    ctx = f"Your goal: craft {goal}.\n{ctx}"
    history: list = []
    obs = r0["obs"]
    while not env.done:
        now = f"{obs} {env.status_text()}"
        prompt = build_prompt(now, ctx, history)
        raw = backend.generate(prompt)
        action = parse_action(raw)
        rec = env.step(action)
        if trace is not None:
            trace(prompt, raw, action, rec["obs"])
        history.append((action, rec["obs"]))
        obs = rec["obs"]
    return {"success": env.success, "steps": env.steps, "goal": goal,
            "trajectory": env.trajectory,
            "facts": [{"text": f.text, "kind": f.kind, "structural": f.structural,
                       "step": f.step} for f in env.episode_facts],
            "known_locations": env.known_locations}

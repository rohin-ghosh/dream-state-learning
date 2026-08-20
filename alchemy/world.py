"""AlchemyWorld — latent compositional environment (SPEC_V2 §2).

Latents (essence, grade, rule table) are per-run randomized, stable for the
lifetime, and NEVER appear in any emitted text — leakage gate G2 is a grep
over emitted text for essence tokens (property in the physics).
"""

from __future__ import annotations

import dataclasses
import itertools
import numpy as np

REACTIVE = tuple(f"E{i}" for i in range(1, 33))  # internal only — never in text
INERT = "E0"
COLORS = ("amber", "violet", "ashen", "cerulean", "russet", "pale")
SMELLS = ("acrid", "sweet", "loamy", "metallic", "briny", "musky")

_SYL_A = ("vex", "mor", "tes", "gal", "rin", "dru", "kel", "sab",
          "fen", "lur", "os", "quin", "bel", "har", "nym", "cor")
_SYL_B = ("il", "run", "sic", "eth", "ock", "ane", "ura", "esk",
          "ov", "ith", "ard", "une", "yl", "ost", "ira", "em")


_SYL_M = ("", "", "ta", "ne", "go", "shi", "va", "pol")


def _nonce(rng: np.random.Generator, used: set) -> str:
    # 16*8*16 = 2048 possible names — supports large worlds + product families
    while True:
        n = rng.choice(_SYL_A) + rng.choice(_SYL_M) + rng.choice(_SYL_B)
        if n not in used:
            used.add(n)
            return n


@dataclasses.dataclass
class Ingredient:
    name: str
    essence: str      # hidden
    grade: int        # hidden
    color: str        # visible, independent of essence (false correlate)
    smell: str        # visible, independent of essence


class AlchemyWorld:
    """One life's physics. predict() is ground truth for held-out eval."""

    def __init__(self, n_ingredients: int = 24, n_inert: int = 4,
                 seed: int = 0, n_essences: int = 4):
        rng = np.random.default_rng(seed)
        self.seed = seed
        self.reactive = REACTIVE[:n_essences]
        used: set = set()
        self.ingredients: dict[str, Ingredient] = {}
        essences = ([INERT] * n_inert +
                    [self.reactive[i % len(self.reactive)]
                     for i in range(n_ingredients - n_inert)])
        rng.shuffle(essences)
        for e in essences:
            name = _nonce(rng, used)
            self.ingredients[name] = Ingredient(
                name, e, int(rng.integers(1, 3)),
                str(rng.choice(COLORS)), str(rng.choice(SMELLS)))
        # rule table over unordered reactive essence pairs
        self.rules: dict[frozenset, tuple] = {}       # pair -> (kind, ...)
        self.products: dict[tuple, str] = {}          # (pairkey, grade) -> name
        self.product_essence: dict[str, str] = {}     # chains: derived essence
        for pair in itertools.combinations_with_replacement(self.reactive, 2):
            key = frozenset(pair) if pair[0] != pair[1] else frozenset([pair[0]])
            r = rng.random()
            if r < 0.6:
                fam = _nonce(rng, used)
                self.rules[key] = ("product", fam)
                for g in (1, 2):
                    pname = f"{fam}-{'I' * g}"
                    self.products[(key, g)] = pname
                    self.product_essence[pname] = str(rng.choice(self.reactive))
            elif r < 0.85:
                self.rules[key] = ("nothing",)
            else:
                self.rules[key] = ("ruin",)

    # ---- ground truth ----------------------------------------------------
    def essence_of(self, item: str) -> str:
        if item in self.ingredients:
            return self.ingredients[item].essence
        return self.product_essence.get(item, INERT)

    def grade_of(self, item: str) -> int:
        if item in self.ingredients:
            return self.ingredients[item].grade
        return 2 if item.endswith("-II") else 1

    def predict(self, a: str, b: str) -> tuple:
        """(kind, product_name_or_None) — the held-out eval target."""
        ea, eb = self.essence_of(a), self.essence_of(b)
        if INERT in (ea, eb):
            return ("nothing", None)
        key = frozenset([ea, eb]) if ea != eb else frozenset([ea])
        rule = self.rules[key]
        if rule[0] != "product":
            return (rule[0], None)
        g = max(self.grade_of(a), self.grade_of(b))
        return ("product", self.products[(key, g)])

    def combine_text(self, a: str, b: str) -> tuple:
        """(kind, product, observation string) — what the agent sees."""
        kind, prod = self.predict(a, b)
        if kind == "product":
            obs = f"You combine {a} and {b}. They fuse into {prod}."
        elif kind == "ruin":
            obs = f"You combine {a} and {b}. The mixture curdles and is ruined."
        else:
            obs = f"You combine {a} and {b}. Nothing happens."
        return kind, prod, obs

    # ---- pools ------------------------------------------------------------
    def base_pairs(self) -> list:
        return list(itertools.combinations(sorted(self.ingredients), 2))

    def craftable_targets(self) -> list:
        """depth-1 product targets with at least one base recipe."""
        out = set()
        for a, b in self.base_pairs():
            kind, prod = self.predict(a, b)
            if kind == "product":
                out.add(prod)
        return sorted(out)

    def recipe_pairs_for(self, target: str) -> list:
        return [(a, b) for a, b in self.base_pairs()
                if self.predict(a, b) == ("product", target)]

    def sample_holdout(self, frac: float = 0.3, seed: int = 0) -> set:
        """Held-out-by-construction: these pairs are never co-present in any
        episode inventory (env enforces), so the split is physics, not luck."""
        rng = np.random.default_rng(seed + 101)
        pairs = self.base_pairs()
        idx = rng.permutation(len(pairs))[:int(frac * len(pairs))]
        return {tuple(sorted(pairs[i])) for i in idx}

    def leakage_scan(self, text: str) -> list:
        """G2: any internal essence token in emitted text = leak."""
        toks = set(REACTIVE) | {INERT}
        return [t for t in toks if t in text]

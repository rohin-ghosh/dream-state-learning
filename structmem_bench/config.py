"""Benchmark configuration.

A StructMem-Bench instance is fully specified by a BenchConfig + a seed. Everything
downstream (task stream, value signal, outcomes, ground-truth labels) is a
deterministic function of these, so results are reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BenchConfig:
    # --- fact universe (fixed size, so the presence matrix is well-defined) ---
    n_struct_frequent: int = 10      # SF: causal, appear often
    n_struct_rare: int = 10          # SR: causal, appear once/twice (rare-but-critical)
    n_detail_recurring: int = 10     # DR: useless distractors correlated w/ a struct fact
    n_random_detail: int = 16        # RD: useless distractors, uncorrelated
    oneshot_per_episode: int = 4     # DO: fresh single-appearance details per episode

    # --- stream ---
    n_episodes: int = 200
    p_present: float = 0.4           # marginal appearance prob (equal across types ->
    #                                  frequency is UNINFORMATIVE by construction)
    confound_a: float = 0.7          # P(DR_i present | its SF/SR partner present);
    #                                  b derived so marginal == p_present (collinearity)

    # --- value signal (what a mechanism may observe; NEVER the label) ---
    value_dprime: float = 1.5        # discriminability of per-appearance value:
    #                                  structural ~ N(dprime,1), detail ~ N(0,1)
    value_freq_decorrelated: bool = True  # if False, value leaks frequency (ablation)

    # --- outcome model ---
    outcome: str = "relational"      # "relational" (conjunctive recipe pairs) | "linear"
    n_recipes: int = 8               # relational: # of causal structural pairs
    outcome_temp: float = 1.7        # logistic steepness

    def __post_init__(self):
        assert self.outcome in ("relational", "linear"), self.outcome
        assert 0.0 < self.p_present < 1.0
        assert self.p_present <= self.confound_a <= 1.0, (
            "confound_a must be in [p_present, 1]; a=p means no confound"
        )
        # rare facts must be able to partner into recipes
        if self.outcome == "relational":
            assert self.n_recipes <= self.n_struct_frequent + self.n_struct_rare

    # --- derived ---
    @property
    def n_structural(self) -> int:
        return self.n_struct_frequent + self.n_struct_rare

    @property
    def oneshot_pool(self) -> int:
        return self.n_episodes * self.oneshot_per_episode

    @property
    def n_facts(self) -> int:
        return (self.n_struct_frequent + self.n_struct_rare
                + self.n_detail_recurring + self.n_random_detail + self.oneshot_pool)

    @property
    def confound_b(self) -> float:
        # marginal(DR) = p = a*p + b*(1-p)  ->  b = (p - a*p)/(1-p)
        return (self.p_present - self.p_present * self.confound_a) / (1 - self.p_present)

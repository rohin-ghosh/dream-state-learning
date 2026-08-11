"""Run harness — config-driven stages with checkpoint/resume sized to 48h leases.

Stages (each idempotent, each resumable from state.json):
  rollouts   — generate/extend the trajectory dataset (scripted now; LLM at GPU tier)
  head       — train FeltHead on the dataset (distillation on oracle salience)
  probe_eval — probe-tier comparison of write policies on held-out worlds
(closed-loop winnability is a GPU-tier stage; slot reserved.)

Design rule: a killed run loses at most one stage-chunk; `resume()` continues from
the last completed chunk. All state (config, rng seeds, completed units, metrics)
lives in <workdir>/state.json + artifacts.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path

import numpy as np

from game import World, generate_dataset
from .head import train_head_on_dataset, eval_head, FeltHead
from .baselines import PROBE_POLICIES, run_probe_condition


@dataclass
class RunConfig:
    workdir: str
    # game sizing (see SIZING.md for the arithmetic behind defaults)
    depth: int = 4
    branching: int = 3
    n_raw: int = 6
    n_locations: int = 8
    # rollouts
    train_worlds: int = 3
    train_episodes_per_world: int = 25
    # head
    d_h: int = 64
    head_epochs: int = 40
    # probe eval
    eval_worlds: int = 8
    eval_episodes_per_world: int = 30
    policies: tuple = ("uniform", "random_write", "surprise_only", "dmem_style",
                       "keyword_gate", "felt_b4", "felt_b12", "oracle_weight")
    seed: int = 0


class Harness:
    def __init__(self, cfg: RunConfig):
        self.cfg = cfg
        self.dir = Path(cfg.workdir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.dir / "state.json"
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if self.state_path.exists():
            st = json.loads(self.state_path.read_text())
            # config-drift guard (redteam_5): resuming a workdir with a DIFFERENT
            # config must fail loudly, not silently report stale results
            cur = json.loads(json.dumps(asdict(self.cfg)))  # normalize tuples->lists
            if st.get("config") != cur:
                raise ValueError(
                    f"workdir {self.dir} was created with a different config; "
                    "use a fresh workdir or delete state.json")
            return st
        return {"config": json.loads(json.dumps(asdict(self.cfg))),
                "completed": {}, "metrics": {}, "started": time.time()}

    def _save(self):
        # ATOMIC (redteam_5): a kill mid-write must never truncate state.json
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, indent=1))
        os.replace(tmp, self.state_path)

    def _done(self, stage: str) -> bool:
        return self.state["completed"].get(stage, False)

    def _mark(self, stage: str, **metrics):
        self.state["completed"][stage] = True
        if metrics:
            self.state["metrics"][stage] = metrics
        self._save()

    # ------------------------------------------------------------- stages
    def stage_rollouts(self):
        if self._done("rollouts"):
            return
        c = self.cfg
        r = generate_dataset(str(self.dir / "train.jsonl"),
                             n_worlds=c.train_worlds,
                             episodes_per_world=c.train_episodes_per_world,
                             seed=c.seed, depth=c.depth, branching=c.branching,
                             n_raw=c.n_raw, n_locations=c.n_locations)
        self._mark("rollouts", **r)

    def stage_head(self):
        if self._done("head"):
            return
        recs = [json.loads(l) for l in open(self.dir / "train.jsonl")]
        split = max(1, int(0.8 * len(recs)))
        head = train_head_on_dataset(recs[:split], d_h=self.cfg.d_h,
                                     epochs=self.cfg.head_epochs,
                                     seed=self.cfg.seed)
        q = eval_head(head, recs[split:], d_h=self.cfg.d_h)
        np.savez(self.dir / "head.npz", Wk=head.Wk, q=head.q, b=head.b)
        self._mark("head", **q)

    def _load_head(self) -> FeltHead:
        z = np.load(self.dir / "head.npz")
        h = FeltHead(d_h=self.cfg.d_h)
        h.Wk, h.q, h.b = z["Wk"], z["q"], float(z["b"])
        return h

    def stage_probe_eval(self):
        """Chunked per (world, policy); resumable mid-stage."""
        if self._done("probe_eval"):
            return
        c = self.cfg
        head = self._load_head()
        done: dict = self.state.setdefault("probe_units", {})
        results = self.state.setdefault("probe_results", {})
        for w_i in range(c.eval_worlds):
            world = World.generate(f"eval_{w_i}", seed=7000 + c.seed * 97 + w_i,
                                   depth=c.depth, branching=c.branching,
                                   n_raw=c.n_raw, n_locations=c.n_locations)
            for pol in c.policies:
                key = f"{w_i}:{pol}"
                if done.get(key):
                    continue
                m = run_probe_condition(world, head, pol,
                                        n_episodes=c.eval_episodes_per_world,
                                        d_h=c.d_h, seed=c.seed * 31 + w_i)
                results.setdefault(pol, []).append(m)
                done[key] = True
                self._save()          # checkpoint after EVERY unit
        summary = {pol: {k: float(np.mean([r[k] for r in rs]))
                         for k in rs[0]}
                   for pol, rs in results.items()}
        self._mark("probe_eval", **summary)

    def run(self) -> dict:
        self.stage_rollouts()
        self.stage_head()
        self.stage_probe_eval()
        return self.state["metrics"]

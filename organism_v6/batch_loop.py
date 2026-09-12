"""Batched episode driving: k episodes advance in lockstep rounds, one
vLLM generate() call per round (list of prompts). ~k x throughput per GPU
vs single-stream — the lever that makes 1000-episode lifetimes affordable.

Semantics note (DESIGN.md): episodes within one wake batch are isolated
from each other's fresh ledger writes (they all see everything from PRIOR
batches). Accepted trade-off; sleep boundaries are batch boundaries.
"""
from __future__ import annotations
import re
import time

from .state import State, render_context
from .ledger import Ledger

_MARK = re.compile(r"^(PREDICT|ACT|NOTE|RECALL|DONE)\s*:?\s*(.*)$",
                   re.MULTILINE)


class EpisodeDriver:
    def __init__(self, episode, bootstrap: str, gym, ledger: Ledger,
                 budget_ticks: int = 24):
        self.ep = episode
        self.bootstrap = bootstrap
        self.gym = gym
        self.ledger = ledger
        self.st = State(goal=episode.goal, metric=episode.metric,
                        episode_id=episode.eid, born_at=time.time(),
                        budget_ticks=budget_ticks)
        self.recalled: list[str] = []
        self.tail: list[str] = [episode.intro]
        self.n_acts = 0
        self.done = False
        # preschool (2026-09-12, THESIS_v2 section 7): the post-outcome slot.
        # None = today's loop, byte-identical; set by run_episodes_batch when
        # a PostOutcomeSlot is passed, then every measured ACT queues one
        # pending execution for the extra round (preschool.PostOutcomeSlot).
        self.note_after = None
        self.pending_after: list = []

    def prompt(self) -> str:
        self.st.tick += 1
        self._last_prompt = render_context(self.bootstrap, self.st,
                                           self.recalled, self.tail)
        return self._last_prompt

    def consume(self, chunk: str) -> None:
        st = self.st
        self.tail.append(chunk.strip())
        prev_best = st.best_score
        rec = dict(kind="thought", episode_id=self.ep.eid, tick=st.tick,
                   note=chunk.strip()[:2000],
                   prompt=getattr(self, "_last_prompt", "")[:24000])
        for m in _MARK.finditer(chunk):
            kind, arg = m.group(1), m.group(2).strip()
            if kind == "PREDICT":
                try:
                    st.pending_prediction = float(
                        re.findall(r"-?\d+\.?\d*", arg)[0])
                except (IndexError, ValueError):
                    st.pending_prediction = None
            elif kind == "ACT":
                score, outcome = self.gym.evaluate(self.ep, arg)
                self.n_acts += 1
                surprise = (score - st.pending_prediction
                            if st.pending_prediction is not None else None)
                act_row = dict(
                    kind="act", episode_id=self.ep.eid, tick=st.tick,
                    action=arg, prediction=st.pending_prediction,
                    outcome=outcome, score=score, surprise=surprise,
                    time_cost=round(time.time() - st.born_at, 1))
                if self.note_after is not None:
                    from .preschool import parse_outcome
                    exec_id = self.note_after.execution_id(self.ep.eid, st.tick,
                                                           self.n_acts)
                    act_row["execution_id"] = exec_id
                    self.pending_after.append(dict(
                        episode_id=self.ep.eid, tick=st.tick, execution_id=exec_id,
                        action=arg, outcome=outcome, facts=parse_outcome(outcome)))
                self.ledger.append(act_row)
                st.last_outcome = f"{outcome} (score {score:.4f})"
                self.tail.append(f"[OUTCOME] {st.last_outcome}")
                if surprise is not None and abs(surprise) > 0.02:
                    st.open_surprises.append(
                        f"predicted {st.pending_prediction:.3f}, got "
                        f"{score:.3f} for: {arg[:60]}")
                st.pending_prediction = None
                if score > st.best_score:
                    st.best_score, st.best_action = score, arg
                    st.last_progress_tick = st.tick
            elif kind == "NOTE":
                if arg:
                    st.add_note(arg)
                    self.ledger.append(dict(kind="note",
                                            episode_id=self.ep.eid,
                                            tick=st.tick, note=arg))
            elif kind == "RECALL":
                self.recalled = self.ledger.recall(arg or st.goal)
            elif kind == "DONE":
                self.done = True
        rec["win"] = st.best_score > prev_best
        rec["had_note"] = "NOTE:" in chunk or "NOTE " in chunk
        self.ledger.append(rec)
        if st.tick >= st.budget_ticks:
            self.done = True

    def summary(self) -> dict:
        return dict(episode_id=self.ep.eid, best_score=self.st.best_score,
                    best_action=self.st.best_action, n_acts=self.n_acts,
                    ticks=self.st.tick, notes=list(self.st.notes))


class NoEndTokenDriver(EpisodeDriver):
    """A gym that offers no end token (reasoning_gym, 2026-09-10): a DONE the
    child writes anyway is ignored — the situation runs to its tick budget.
    Everything else (marker parsing, ledger rows) is EpisodeDriver's."""

    def consume(self, chunk: str) -> None:
        super().consume(chunk)
        if self.st.tick < self.st.budget_ticks:
            self.done = False


def driver_class_for(gym):
    """EpisodeDriver unless the gym says it offers no end token."""
    offers = getattr(gym, "offers_end_token", None)
    if callable(offers) and not offers():
        return NoEndTokenDriver
    return EpisodeDriver


def _seed_for(eid: str, tick: int, base: int) -> int:
    import zlib
    return (zlib.crc32(f"{eid}/{tick}".encode()) ^ base) & 0x7fffffff


def run_episodes_batch(model, gym, episodes, bootstrap: str, ledger: Ledger,
                       budget_ticks: int = 24, log=print,
                       gen_seed: int | None = None,
                       driver_cls=EpisodeDriver, note_after=None) -> list[dict]:
    """Drive all episodes to completion in lockstep batched rounds.
    gen_seed: common-random seeding — chunk seeds derive from
    (episode_id, tick, gen_seed), so paired arms/probes with the same
    gen_seed face identical randomness.
    driver_cls (2026-09-10): EpisodeDriver by default (unchanged behaviour);
    NoEndTokenDriver for gyms without an end token.
    note_after (2026-09-12, preschool): a preschool.PostOutcomeSlot; after
    each round's chunks are consumed, every measured ACT of the round gets
    the post-outcome field in ONE extra batched call. None (default) = no
    extra round, byte-identical behaviour."""
    drivers = [driver_cls(e, bootstrap, gym, ledger, budget_ticks)
               for e in episodes]
    if note_after is not None:
        for d in drivers:
            d.note_after = note_after
    while True:
        active = [d for d in drivers if not d.done]
        if not active:
            break
        prompts = [d.prompt() for d in active]
        seeds = ([_seed_for(d.ep.eid, d.st.tick, gen_seed)
                  for d in active] if gen_seed is not None else None)
        chunks = model.batch(prompts, seeds=seeds)
        for d, c in zip(active, chunks):
            d.consume(c)
        if note_after is not None:
            note_after.run_round(model, active, ledger, gen_seed)
    out = []
    for d in drivers:
        s = d.summary()
        log(f"[episode {s['episode_id']}] best={s['best_score']:.4f} "
            f"acts={s['n_acts']} ticks={s['ticks']}")
        out.append(s)
    return out

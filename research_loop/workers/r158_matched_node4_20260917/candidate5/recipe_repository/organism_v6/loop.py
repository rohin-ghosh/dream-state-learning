"""v6 free-flow thinking loop (DESIGN.md section 2, revised).

No imposed turn structure. The model thinks in a continuing stream; the
harness scans each generated chunk for markers the model chose to emit:

  PREDICT: <float>        expected score for the NEXT action (required
                          before ACT for the surprise ledger)
  ACT: <action text>      submit to the gym; outcome injected into stream
  NOTE: <text>            persist to the state-block HEAD (model-owned state)
  RECALL: <query>         harness retrieves ledger entries into the MIDDLE
  DONE                    end the episode early

Everything else in the stream is just thinking and flows into the TAIL.
The bootstrap explains the markers once; planning patterns are emergent.
"""
from __future__ import annotations
import re
import time

from .state import State, render_context
from .ledger import Ledger

_MARK = re.compile(
    r"^(PREDICT|ACT|NOTE|RECALL|DONE)\s*:?\s*(.*)$", re.MULTILINE)


def run_episode(model, gym, episode, bootstrap: str, ledger: Ledger,
                budget_ticks: int = 64, chunk_tokens: int = 400,
                log=print) -> dict:
    """One episode: model free-thinks against one gym problem.
    `model(prompt) -> str` is a pure generation callable (base or base+LoRA).
    `gym.evaluate(episode, action) -> (score, outcome_str)` deterministic.
    Returns episode summary for measurement."""
    st = State(goal=episode.goal, metric=episode.metric,
               episode_id=episode.eid, born_at=time.time(),
               budget_ticks=budget_ticks)
    recalled: list[str] = []
    tail: list[str] = [episode.intro]
    n_acts = 0

    while st.tick < st.budget_ticks:
        st.tick += 1
        prompt = render_context(bootstrap, st, recalled, tail)
        chunk = model(prompt)
        tail.append(chunk.strip())
        ledger.append(dict(kind="thought", episode_id=episode.eid,
                           tick=st.tick, note=chunk.strip()[:2000]))

        done = False
        for m in _MARK.finditer(chunk):
            kind, arg = m.group(1), m.group(2).strip()
            if kind == "PREDICT":
                try:
                    st.pending_prediction = float(
                        re.findall(r"-?\d+\.?\d*", arg)[0])
                except (IndexError, ValueError):
                    st.pending_prediction = None
            elif kind == "ACT":
                score, outcome = gym.evaluate(episode, arg)
                n_acts += 1
                surprise = (score - st.pending_prediction
                            if st.pending_prediction is not None else None)
                ledger.append(dict(
                    kind="act", episode_id=episode.eid, tick=st.tick,
                    action=arg, prediction=st.pending_prediction,
                    outcome=outcome, score=score, surprise=surprise,
                    time_cost=round(time.time() - st.born_at, 1)))
                st.last_outcome = f"{outcome} (score {score:.4f})"
                tail.append(f"[OUTCOME] {st.last_outcome}")
                if surprise is not None and abs(surprise) > 0.02:
                    st.open_surprises.append(
                        f"predicted {st.pending_prediction:.3f}, "
                        f"got {score:.3f} for: {arg[:60]}")
                st.pending_prediction = None
                if score > st.best_score:
                    st.best_score, st.best_action = score, arg
                    st.last_progress_tick = st.tick
            elif kind == "NOTE":
                if arg:
                    st.add_note(arg)
                    ledger.append(dict(kind="note", episode_id=episode.eid,
                                       tick=st.tick, note=arg))
            elif kind == "RECALL":
                recalled = ledger.recall(arg or st.goal)
            elif kind == "DONE":
                done = True
        if done:
            break

    log(f"[episode {episode.eid}] best={st.best_score:.4f} "
        f"acts={n_acts} ticks={st.tick}")
    return dict(episode_id=episode.eid, best_score=st.best_score,
                best_action=st.best_action, n_acts=n_acts, ticks=st.tick,
                notes=list(st.notes))

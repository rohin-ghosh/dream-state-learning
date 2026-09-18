"""v6 conscious-space state block (free-flow revision, DESIGN.md section 2).

The context window is rebuilt every generation chunk from (state, ledger,
tail). State maintenance is split:
  - MECHANICAL fields (clock, tick, scores, outcomes, surprises): harness.
  - NARRATIVE state (focus, theories, self-reminders): model-owned via
    NOTE: markers, persisted in `notes` and re-rendered at the HEAD so the
    model's own plans survive context rebuilds.
No mode field, no imposed turn structure — planned thinking is emergent.
"""
from __future__ import annotations
import json
import os
import time
from dataclasses import dataclass, field, asdict


@dataclass
class State:
    goal: str = ""
    metric: str = ""
    episode_id: str = ""
    tick: int = 0
    born_at: float = 0.0
    budget_ticks: int = 64
    best_score: float = 0.0
    best_action: str = ""
    last_outcome: str = "(no actions taken yet)"
    pending_prediction: float | None = None
    open_surprises: list = field(default_factory=list)
    notes: list = field(default_factory=list)   # model-owned, via NOTE:
    last_progress_tick: int = 0

    def clock_line(self) -> str:
        alive = time.time() - self.born_at if self.born_at else 0.0
        stale = self.tick - self.last_progress_tick
        return (f"CLOCK: chunk {self.tick}/{self.budget_ticks} | alive "
                f"{alive:.0f}s | chunks since last progress: {stale}")

    def add_note(self, text: str, cap: int = 10) -> None:
        self.notes.append(text.strip())
        self.notes = self.notes[-cap:]

    def save(self, path: str) -> None:
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(asdict(self), f, indent=1)
        os.rename(tmp, path)

    @classmethod
    def load(cls, path: str) -> "State":
        with open(path) as f:
            return cls(**json.load(f))


CHAR_BUDGET = 22000  # ~6k tokens; leaves generation room in a 16k window


def render_context(bootstrap: str, st: State, recalled: list[str],
                   tail: list[str], char_budget: int = CHAR_BUDGET) -> str:
    """HEAD (bootstrap + state) + MIDDLE (recalled) + TAIL (thought stream).
    Ends mid-stream: the model continues thinking from here.
    Hard character budget: oldest tail falls off first, then recalled —
    ephemerality enforced by arithmetic (nothing is lost; it's in the ledger).
    """
    recalled = [r[:300] for r in (recalled or [])]
    tail = [t[:1200] for t in tail]
    head = [
        "=== YOU ===", bootstrap.strip(),
        "=== STATE ===",
        f"GOAL: {st.goal}",
        f"METRIC: {st.metric}",
        st.clock_line(),
        f"BEST SCORE THIS EPISODE: {st.best_score:.4f}"
        + (f"  (via: {st.best_action})" if st.best_action else ""),
        f"LAST OUTCOME: {st.last_outcome}",
    ]
    if st.open_surprises:
        head.append("OPEN SURPRISES (you expected vs got):")
        head += [f"  - {s}" for s in st.open_surprises[-4:]]
    if st.notes:
        head.append("YOUR NOTES (you wrote these to yourself):")
        head += [f"  - {n}" for n in st.notes]
    mid = ["=== RECALLED EXPERIENCE ==="] + (recalled or ["(nothing recalled)"])
    keep = list(tail[-14:])
    while keep or recalled:
        tl = ["=== YOUR THINKING (continues) ==="] + keep
        out = "\n".join(head + mid + tl) + "\n"
        if len(out) <= char_budget:
            return out
        if keep:
            keep.pop(0)          # oldest thought falls off first
        else:
            recalled.pop()       # then recalled, least relevant last
            mid = ["=== RECALLED EXPERIENCE ==="] + \
                  (recalled or ["(nothing recalled)"])
    return ("\n".join(head + ["=== YOUR THINKING (continues) ==="]) + "\n")

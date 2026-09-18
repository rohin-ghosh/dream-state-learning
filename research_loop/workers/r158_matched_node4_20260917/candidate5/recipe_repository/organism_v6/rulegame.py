"""Hidden-rule induction nursery gym (target-blind: zero compiler content).

The child probes a mystery box with triples of integers (TRY: a,b,c), the
box answers True/False per a hidden rule; then a QUIZ of held-out triples
measures whether the child actually induced the rule. Score = quiz accuracy.
Exercises exactly the taught skills: predict, test, scope, theorize.
"""
from __future__ import annotations
import random

RULES = [
    ("sum_div3", lambda a, b, c: (a + b + c) % 3 == 0,
     "sum divisible by three"),
    ("increasing", lambda a, b, c: a < b < c, "strictly increasing"),
    ("middle_avg", lambda a, b, c: 2 * b == a + c,
     "middle is the average of the ends"),
    ("has_repeat", lambda a, b, c: len({a, b, c}) < 3,
     "at least two equal"),
    ("all_even", lambda a, b, c: a % 2 == b % 2 == c % 2 == 0, "all even"),
    ("contains_zero", lambda a, b, c: 0 in (a, b, c), "contains a zero"),
    ("prod_even", lambda a, b, c: (a * b * c) % 2 == 0, "product is even"),
    ("range_le4", lambda a, b, c: max(a, b, c) - min(a, b, c) <= 4,
     "spread at most four"),
    ("first_largest", lambda a, b, c: a >= b and a >= c,
     "first is the largest"),
    ("sum_gt15", lambda a, b, c: a + b + c > 15, "sum greater than fifteen"),
]


class RuleGame:
    """One hidden rule per episode id. Deterministic from the eid."""

    def __init__(self):
        self._quiz_cache: dict[str, list] = {}

    def _rule(self, eid: str):
        # eid prefix "ruleN/..." forces rule index N (matched-difficulty
        # pre/apply pairs need the SAME rule class on different instances)
        if eid.startswith("rule") and "/" in eid:
            head = eid.split("/", 1)[0][4:]
            if head.isdigit():
                return RULES[int(head) % len(RULES)]
        rng = random.Random(eid)
        return RULES[rng.randrange(len(RULES))]

    def quiz_triples(self, eid: str, k: int = 6) -> list[tuple]:
        if eid not in self._quiz_cache:
            rng = random.Random(eid + "/quiz")
            name, fn, _ = self._rule(eid)
            pos, neg, guard = [], [], 0
            while (len(pos) < k // 2 or len(neg) < k // 2) and guard < 4000:
                t = (rng.randint(0, 9), rng.randint(0, 9), rng.randint(0, 9))
                (pos if fn(*t) else neg).append(t)
                guard += 1
            triples = (pos[:k // 2] + neg[:k - k // 2])
            rng.shuffle(triples)
            self._quiz_cache[eid] = triples
        return self._quiz_cache[eid]

    def evaluate(self, episode, action: str) -> tuple[float, str]:
        """ACT payloads: 'TRY a,b,c'  or  'QUIZ ans1,...,ans6' (T/F list)."""
        eid = episode.eid
        name, fn, _ = self._rule(eid)
        act = action.strip()
        low = act.lower()
        try:
            if low.startswith("try"):
                nums = [int(x) for x in
                        act.replace("TRY", "").replace("try", "")
                        .replace(":", " ").replace(",", " ").split()][:3]
                if len(nums) != 3:
                    return 0.0, "INVALID: TRY needs exactly three integers"
                r = fn(*nums)
                return 0.0, (f"the box says: {r} for "
                             f"({nums[0]},{nums[1]},{nums[2]})")
            if low.startswith("quiz"):
                raw = act[4:].replace(":", " ").replace(",", " ").split()
                ans = [x.strip().upper().startswith("T") for x in raw][:6]
                triples = self.quiz_triples(eid)
                if len(ans) != len(triples):
                    return 0.0, (f"INVALID: quiz needs {len(triples)} "
                                 f"answers (T/F) for {triples}")
                truth = [fn(*t) for t in triples]
                acc = sum(a == t for a, t in zip(ans, truth)) / len(truth)
                return acc, f"quiz score: {acc:.2f}"
            return 0.0, ("INVALID: use 'ACT: TRY a,b,c' to probe or "
                         "'ACT: QUIZ T,F,...' to answer the quiz")
        except (ValueError, IndexError):
            return 0.0, "INVALID: could not parse the numbers"

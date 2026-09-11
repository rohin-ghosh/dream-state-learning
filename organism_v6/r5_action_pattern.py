"""Read-only action-pattern audit for paired adapter ON/OFF probe ledgers.

The report shows how the realized panel gap changes when each trajectory is
scored through at most k authoritative action rows. It also checks whether
either condition repeats an action string exposed at birth.

Usage:
  python -m organism_v6.r5_action_pattern \
      --on probe_on.jsonl --off probe_off.jsonl --out audit.json
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import statistics


DEFAULT_ROUTINE = "-mem2reg,-sroa,-gvn,-simplifycfg"
DEFAULT_CAPS = (1, 2, 4, 8, 16, 32)


def normalize_action(action: str) -> str:
    return ",".join(part.strip() for part in action.split(",") if part.strip())


def load_acts(path: str) -> collections.OrderedDict[str, list[dict]]:
    episodes: collections.OrderedDict[str, list[dict]] = collections.OrderedDict()
    last_tick: dict[str, int] = {}
    with open(path) as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("kind") != "act":
                continue
            eid = str(row.get("episode_id", ""))
            if not eid:
                raise ValueError(f"{path}:{line_no}: ACT row has no episode_id")
            score = row.get("score")
            if (not isinstance(score, (int, float)) or isinstance(score, bool)
                    or not math.isfinite(float(score))):
                raise ValueError(f"{path}:{line_no}: ACT row has no numeric score")
            if not isinstance(row.get("action"), str):
                raise ValueError(f"{path}:{line_no}: ACT row has non-string action")
            try:
                tick = int(row["tick"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"{path}:{line_no}: ACT row has invalid tick") from exc
            if tick < last_tick.get(eid, tick):
                raise ValueError(f"{path}:{line_no}: tick order regressed for {eid}")
            last_tick[eid] = tick
            episodes.setdefault(eid, []).append(row)
    return episodes


def sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def condition_summary(episodes: dict[str, list[dict]], routine: str) -> dict:
    actions = [normalize_action(row.get("action", ""))
               for rows in episodes.values() for row in rows]
    nonempty_actions = [action for action in actions if action]
    first = [normalize_action(rows[0].get("action", ""))
             for rows in episodes.values() if rows]
    best = [max(float(row["score"]) for row in rows)
            for rows in episodes.values() if rows]
    action_ticks = [len({int(row["tick"]) for row in rows})
                    for rows in episodes.values()]
    n_action_ticks = sum(action_ticks)
    return {
        "n_episodes": len(episodes),
        "n_act_rows": len(actions),
        "n_nonempty_actions": len(nonempty_actions),
        "n_empty_or_noop_act_rows": len(actions) - len(nonempty_actions),
        "mean_act_rows_per_episode": statistics.mean(
            len(rows) for rows in episodes.values()
        ),
        "n_action_bearing_ticks": n_action_ticks,
        "mean_action_bearing_ticks_per_episode": statistics.mean(action_ticks),
        "mean_act_rows_per_action_bearing_tick": len(actions) / n_action_ticks,
        "n_episodes_reaching_tick16": sum(
            max(int(row["tick"]) for row in rows) >= 16
            for rows in episodes.values()
        ),
        "mean_best_score": statistics.mean(best),
        "unique_nonempty_actions": len(set(nonempty_actions)),
        "routine_first_count": sum(action == routine for action in first),
        "routine_all_count": sum(action == routine for action in actions),
    }


def paired_report(on_path: str, off_path: str, routine: str = DEFAULT_ROUTINE,
                  caps: tuple[int, ...] = DEFAULT_CAPS,
                  expected_eids: set[str] | None = None) -> dict:
    routine = normalize_action(routine)
    on, off = load_acts(on_path), load_acts(off_path)
    if set(on) != set(off):
        raise ValueError("ON and OFF ledgers must contain the same episode IDs")
    if expected_eids is not None and set(on) != set(expected_eids):
        raise ValueError("paired ledgers do not match the expected panel IDs")
    if not on or any(not rows for rows in list(on.values()) + list(off.values())):
        raise ValueError("each paired episode must contain an executed action")
    ids = list(on)
    cap_rows = []
    for cap in caps:
        on_scores = [max(float(row["score"]) for row in on[eid][:cap])
                     for eid in ids]
        off_scores = [max(float(row["score"]) for row in off[eid][:cap])
                      for eid in ids]
        cap_rows.append({
            "cap": cap,
            "on_n_reaching_cap": sum(len(on[eid]) >= cap for eid in ids),
            "off_n_reaching_cap": sum(len(off[eid]) >= cap for eid in ids),
            "on": statistics.mean(on_scores),
            "off": statistics.mean(off_scores),
            "on_minus_off": statistics.mean(
                a - b for a, b in zip(on_scores, off_scores)
            ),
        })
    per_episode = []
    for eid in ids:
        on_first, off_first = on[eid][0], off[eid][0]
        per_episode.append({
            "episode_id": eid,
            "on_first_action": normalize_action(on_first.get("action", "")),
            "off_first_action": normalize_action(off_first.get("action", "")),
            "on_first_score": float(on_first["score"]),
            "off_first_score": float(off_first["score"]),
            "first_score_delta": float(on_first["score"]) - float(off_first["score"]),
        })
    return {
        "on_path": on_path,
        "on_sha256": sha256(on_path),
        "off_path": off_path,
        "off_sha256": sha256(off_path),
        "routine": routine,
        "on": condition_summary(on, routine),
        "off": condition_summary(off, routine),
        "fixed_action_caps": cap_rows,
        "per_episode_first_action": per_episode,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--on", required=True)
    parser.add_argument("--off", required=True)
    parser.add_argument("--routine", default=DEFAULT_ROUTINE)
    parser.add_argument("--expected-panel",
                        help="optional JSON list of exact expected episode IDs")
    parser.add_argument("--out")
    args = parser.parse_args()
    expected = set(json.load(open(args.expected_panel))) \
        if args.expected_panel else None
    report = paired_report(args.on, args.off, args.routine,
                           expected_eids=expected)
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()

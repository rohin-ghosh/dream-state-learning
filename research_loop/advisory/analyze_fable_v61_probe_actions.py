#!/usr/bin/env python3
"""Read-only action diagnostic for Fable's v6.1 saved artifacts.

This script never calls a model or CompilerGym. It compares adapter ON/OFF
at every complete paired checkpoint using scores already recorded for
executed actions. It also summarizes the action-target distribution in each
sealed sleep corpus. It is deliberately post-hoc and therefore diagnostic
only.
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import math
import re
import statistics
from pathlib import Path


CAPS = (1, 2, 4, 8, 16)
REGISTERED_PROBES = (
    "cbench-v1/susan",
    "cbench-v1/sha",
    "cbench-v1/dijkstra",
    "cbench-v1/patricia",
    "cbench-v1/jpeg-c",
    "cbench-v1/tiff2bw",
    "cbench-v1/gsm",
    "cbench-v1/stringsearch",
)
EXPECTED_CHECKPOINTS = tuple(range(64, 1025, 64))
EXPECTED_SLEEP_CHECKPOINTS = tuple(range(32, 1025, 32))
SCORE_TOLERANCE = 1e-12
SOURCE_PROXY_MARK_RE = re.compile(
    r"^(PREDICT|ACT|NOTE|RECALL|DONE)\s*:?\s*(.*)$"
)
ACTION_LABEL_CANDIDATE_RE = re.compile(
    r"^\s*(?:[#>*+`-]+\s*)?(?:ACT|ACTION)\s*:?\s*.*$", re.IGNORECASE
)


def normalized_action(text: str) -> str:
    return ",".join(part.strip() for part in text.split(",") if part.strip())


def read_actions(path: Path) -> dict[str, list[dict]]:
    by_episode: dict[str, list[dict]] = {
        episode: [] for episode in REGISTERED_PROBES
    }
    seen_episodes = set()
    lines = path.read_text().splitlines()
    if not lines:
        raise ValueError(f"empty probe ledger: {path}")
    for line_number, line in enumerate(lines, start=1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"invalid JSONL at {path}:{line_number}: {exc}"
            ) from exc
        episode_id = row.get("episode_id")
        if episode_id is not None:
            episode_id = str(episode_id)
            if episode_id not in by_episode:
                raise ValueError(
                    f"unregistered probe episode {episode_id!r} in {path}"
                )
            seen_episodes.add(episode_id)
        if row.get("kind") == "act":
            if episode_id is None:
                raise ValueError(f"act without episode_id in {path}:{line_number}")
            row = dict(row)
            row["action"] = normalized_action(str(row.get("action", "")))
            by_episode[episode_id].append(row)
    expected = set(REGISTERED_PROBES)
    if seen_episodes != expected:
        raise ValueError(
            f"probe ledger {path} has episode IDs {sorted(seen_episodes)}, "
            f"expected {sorted(expected)}"
        )
    return by_episode


def read_probe_summary(path: Path) -> dict[str, float]:
    payload = json.loads(path.read_text())
    results = payload.get("results")
    if not isinstance(results, dict):
        raise ValueError(f"summary lacks results object: {path}")
    expected = set(REGISTERED_PROBES)
    if set(results) != expected:
        raise ValueError(
            f"summary {path} has programs {sorted(results)}, "
            f"expected {sorted(expected)}"
        )
    normalized = {key: float(value) for key, value in results.items()}
    expected_mean = statistics.fmean(normalized.values())
    if not math.isclose(
        float(payload.get("mean")), expected_mean,
        rel_tol=0.0, abs_tol=SCORE_TOLERANCE,
    ):
        raise ValueError(
            f"summary mean mismatch in {path}: stored={payload.get('mean')} "
            f"recomputed={expected_mean}"
        )
    return normalized


def capped_panel(by_episode: dict[str, list[dict]], cap: int) -> float:
    # Probe panels contain eight fixed programs. A program with no executable
    # action contributes zero under the live harness semantics.
    values = []
    if set(by_episode) != set(REGISTERED_PROBES):
        raise ValueError("probe panel does not match registered program set")
    for episode in REGISTERED_PROBES:
        rows = by_episode[episode]
        values.append(max([0.0] + [float(r["score"]) for r in rows[:cap]]))
    return statistics.fmean(values)


def validate_full_panel_against_summary(
    ledger_actions: dict[str, list[dict]], summary: dict[str, float], path: Path,
) -> None:
    for episode in REGISTERED_PROBES:
        reconstructed = max(
            [0.0] + [float(row["score"]) for row in ledger_actions[episode]]
        )
        if not math.isclose(
            reconstructed, summary[episode],
            rel_tol=0.0, abs_tol=SCORE_TOLERANCE,
        ):
            raise ValueError(
                f"ledger/summary score mismatch for {episode} at {path}: "
                f"ledger={reconstructed} summary={summary[episode]}"
            )


def action_diagnostics(by_episode: dict[str, list[dict]]) -> dict:
    actions = [row for rows in by_episode.values() for row in rows]
    counts = collections.Counter(row["action"] for row in actions)
    total = len(actions)
    return {
        "actions": total,
        "unique_actions": len(counts),
        "unique_per_action": len(counts) / total if total else None,
        "dominant_action": counts.most_common(1)[0][0] if counts else None,
        "dominant_action_count": counts.most_common(1)[0][1] if counts else 0,
        "dominant_action_fraction": (
            counts.most_common(1)[0][1] / total if counts else None
        ),
        "invalid_actions": sum(
            str(row.get("outcome", "")).startswith("INVALID") for row in actions
        ),
        "unpredicted_actions": sum(
            row.get("prediction") is None for row in actions
        ),
    }


def complete_checkpoints(life: Path) -> list[int]:
    checkpoints = []
    for path in life.glob("probe_ep[0-9][0-9][0-9][0-9].ledger.jsonl"):
        match = re.fullmatch(r"probe_ep(\d{4})\.ledger\.jsonl", path.name)
        if not match:
            continue
        checkpoint = int(match.group(1))
        if checkpoint == 0:
            continue
        required = (
            life / f"probe_ep{checkpoint:04d}.json",
            life / f"probe_ep{checkpoint:04d}_adapterOFF.ledger.jsonl",
            life / f"probe_ep{checkpoint:04d}_adapterOFF.json",
        )
        if all(candidate.exists() for candidate in required):
            checkpoints.append(checkpoint)
    return sorted(set(checkpoints))


def normalized_trapezoid(points: list[tuple[int, float]]) -> float | None:
    if not points:
        return None
    if len(points) == 1:
        return points[0][1]
    points = sorted(points)
    width = points[-1][0] - points[0][0]
    if width <= 0:
        return statistics.fmean(value for _, value in points)
    area = sum(
        (right_x - left_x) * (left_y + right_y) / 2
        for (left_x, left_y), (right_x, right_y) in zip(points, points[1:])
    )
    return area / width


def corpus_texts(path: Path) -> list[str]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict) or not isinstance(payload.get("corpus"), list):
        raise ValueError(f"unexpected sleep corpus schema: {path}")
    values = payload["corpus"]
    texts: list[str] = []
    for value in values:
        rows = value if isinstance(value, list) else [value]
        for row in rows:
            if isinstance(row, str):
                texts.append(row)
            elif isinstance(row, dict):
                texts.append("\n".join(
                    str(field) for field in row.values()
                    if isinstance(field, str)
                ))
    return texts


def corpus_marker_diagnostics(lines: list[str]) -> dict:
    """Describe corpus syntax against the checked-in parser source.

    This is only a source-proxy diagnostic: the long-lived process did not
    save an import receipt, so the checked-in regex cannot be asserted to be
    the exact runtime parser bytes used by the legacy run.
    """
    candidates = [line for line in lines if ACTION_LABEL_CANDIDATE_RE.match(line)]
    accepted = []
    near_misses = collections.Counter()
    for line in candidates:
        match = SOURCE_PROXY_MARK_RE.match(line)
        if match and match.group(1) == "ACT":
            accepted.append(line)
            continue
        if re.match(r"^\s*#+\s*ACT\s*:?", line, re.IGNORECASE):
            near_misses["hash_prefixed"] += 1
        elif re.match(r"^\s+ACT\s*:?", line):
            near_misses["indented_uppercase"] += 1
        elif re.match(r"^\s*(?:[#>*+`-]+\s*)?act\s*:?", line):
            near_misses["lowercase"] += 1
        elif re.match(
            r"^\s*(?:[#>*+`-]+\s*)?(?:ACT|ACTION)\s*:?", line,
            re.IGNORECASE,
        ):
            near_misses["decorated_or_action_alias"] += 1
        else:
            near_misses["other"] += 1
    return {
        "action_label_candidate_lines": len(candidates),
        "source_proxy_act_syntax_lines": len(accepted),
        "source_proxy_act_syntax_fraction_of_candidates": (
            len(accepted) / len(candidates) if candidates else None
        ),
        "source_proxy_near_miss_lines": len(candidates) - len(accepted),
        "source_proxy_near_miss_categories": dict(sorted(near_misses.items())),
    }


def sleep_corpus_trajectory(life: Path, consumed: set[Path]) -> list[dict]:
    trajectory = []
    pattern = re.compile(r"sleep_(\d{4})$")
    for path_text in sorted(glob.glob(str(life / "sleep_[0-9][0-9][0-9][0-9]" / "corpus.json"))):
        path = Path(path_text)
        consumed.add(path)
        match = pattern.fullmatch(path.parent.name)
        if not match:
            continue
        texts = corpus_texts(path)
        lines = [line for text in texts for line in text.splitlines()]
        source_proxy = corpus_marker_diagnostics(lines)
        marker_lines = [
            line for line in lines if re.search(r"ACT\s*:", line, flags=re.I)
        ]
        strict_marker_lines = [
            line for line in marker_lines if re.match(r"^ACT:\s*", line)
        ]
        hash_marker_lines = [
            line for line in marker_lines
            if re.match(r"^\s*#+\s*ACT\s*:", line, flags=re.I)
        ]
        decorated_marker_lines = [
            line for line in marker_lines if not re.match(r"^ACT:\s*", line)
        ]
        action_lines = re.findall(
            r"(?:ACT:|Action:|action:)\s*([^\n]+)", "\n".join(texts)
        )
        counts = collections.Counter(
            normalized_action(action) for action in action_lines
        )
        total = len(action_lines)
        trajectory.append({
            "checkpoint": int(match.group(1)),
            "texts": len(texts),
            "parsed_action_lines": total,
            "unique_actions": len(counts),
            "unique_per_action": len(counts) / total if total else None,
            "top1_fraction": (
                counts.most_common(1)[0][1] / total if counts else None
            ),
            "top3_fraction": (
                sum(count for _, count in counts.most_common(3)) / total
                if counts else None
            ),
            "dominant_action": counts.most_common(1)[0][0] if counts else None,
            "action_marker_lines": len(marker_lines),
            "column_zero_act_colon_lines": len(strict_marker_lines),
            "hash_action_marker_lines": len(hash_marker_lines),
            "decorated_action_marker_lines": len(decorated_marker_lines),
            "column_zero_act_colon_fraction": (
                len(strict_marker_lines) / len(marker_lines)
                if marker_lines else None
            ),
            **source_proxy,
        })
    return trajectory


def file_receipt(path: Path, root: Path) -> dict:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "path": str(path.relative_to(root)),
        "bytes": path.stat().st_size,
        "sha256": digest.hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.home() / "v6_out")
    parser.add_argument(
        "--seeds", default="0,1,2",
        help="comma-separated L_B_seed suffixes (default: 0,1,2)",
    )
    parser.add_argument(
        "--checkpoints", default=None,
        help="optional comma-separated checkpoint filter; default discovers all pairs",
    )
    parser.add_argument(
        "--summary-only", action="store_true",
        help="emit compact checkpoint/AUC/corpus-endpoint diagnostics",
    )
    parser.add_argument(
        "--compact-final", action="store_true",
        help=(
            "emit only terminal paired checkpoints, per-life AUC, aggregate "
            "fixed-action-cap scalars, and sleep-corpus endpoints"
        ),
    )
    parser.add_argument(
        "--results-only", action="store_true",
        help="with --compact-final, omit individual artifact-manifest entries",
    )
    parser.add_argument(
        "--manifest-only", action="store_true",
        help="with --compact-final, emit only the complete artifact manifest",
    )
    args = parser.parse_args()

    seeds = tuple(int(item) for item in args.seeds.split(",") if item.strip())
    checkpoint_filter = (
        {int(item) for item in args.checkpoints.split(",") if item.strip()}
        if args.checkpoints else None
    )

    paired = []
    first_action_transitions = collections.Counter()
    first_action_score_deltas: dict[tuple[str, str, str], list[float]] = \
        collections.defaultdict(list)
    action_counts = {"ON": collections.Counter(), "OFF": collections.Counter()}
    first_action_counts = {"ON": collections.Counter(), "OFF": collections.Counter()}
    first_action_programs = {"ON": collections.defaultdict(set),
                             "OFF": collections.defaultdict(set)}

    sleep_trajectories = {}
    consumed_paths: set[Path] = set()
    for seed in seeds:
        life = args.root / f"L_B_seed{seed}"
        checkpoints = complete_checkpoints(life)
        if checkpoint_filter is not None:
            checkpoints = [value for value in checkpoints if value in checkpoint_filter]
        sleep_trajectories[str(seed)] = sleep_corpus_trajectory(
            life, consumed_paths
        )
        for checkpoint in checkpoints:
            prefix = f"probe_ep{checkpoint:04d}"
            paths = {
                "ON": {
                    "ledger": life / f"{prefix}.ledger.jsonl",
                    "summary": life / f"{prefix}.json",
                },
                "OFF": {
                    "ledger": life / f"{prefix}_adapterOFF.ledger.jsonl",
                    "summary": life / f"{prefix}_adapterOFF.json",
                },
            }
            flat_paths = [path for arm in paths.values() for path in arm.values()]
            if not all(path.exists() for path in flat_paths):
                continue
            consumed_paths.update(flat_paths)
            arms = {}
            summaries = {}
            for arm, arm_paths in paths.items():
                arms[arm] = read_actions(arm_paths["ledger"])
                summaries[arm] = read_probe_summary(arm_paths["summary"])
                validate_full_panel_against_summary(
                    arms[arm], summaries[arm], arm_paths["ledger"]
                )
            row = {"seed": seed, "checkpoint": checkpoint}
            for arm, episodes in arms.items():
                row[f"{arm}_acts"] = sum(map(len, episodes.values()))
                row[f"{arm}_diagnostics"] = action_diagnostics(episodes)
                for program, actions in episodes.items():
                    for action in actions:
                        action_counts[arm][action["action"]] += 1
                    if actions:
                        first = actions[0]["action"]
                        first_action_counts[arm][first] += 1
                        first_action_programs[arm][first].add(program)
                for cap in CAPS:
                    row[f"{arm}_k{cap}"] = capped_panel(episodes, cap)
                row[f"{arm}_full"] = capped_panel(episodes, 10**9)
                summary_mean = statistics.fmean(summaries[arm].values())
                if not math.isclose(
                    row[f"{arm}_full"], summary_mean,
                    rel_tol=0.0, abs_tol=SCORE_TOLERANCE,
                ):
                    raise ValueError(
                        f"panel mean mismatch for seed={seed} "
                        f"checkpoint={checkpoint} arm={arm}"
                    )
            for program in sorted(set(arms["ON"]) | set(arms["OFF"])):
                on_rows = arms["ON"].get(program, [])
                off_rows = arms["OFF"].get(program, [])
                on_action = on_rows[0]["action"] if on_rows else "NO_ACTION"
                off_action = off_rows[0]["action"] if off_rows else "NO_ACTION"
                key = (program, off_action, on_action)
                first_action_transitions[key] += 1
                first_action_score_deltas[key].append(
                    (float(on_rows[0]["score"]) if on_rows else 0.0)
                    - (float(off_rows[0]["score"]) if off_rows else 0.0)
                )
            paired.append(row)

    if not paired:
        raise SystemExit("no complete ON/OFF early probe pairs found")

    caps = {}
    for cap in CAPS:
        diffs = [row[f"ON_k{cap}"] - row[f"OFF_k{cap}"] for row in paired]
        caps[str(cap)] = {
            "n": len(diffs),
            "mean_on_minus_off": statistics.fmean(diffs),
            "median_on_minus_off": statistics.median(diffs),
            "positive_pairs": sum(value > 0 for value in diffs),
            "differences": diffs,
        }

    life_auc = {}
    for seed in seeds:
        rows = sorted(
            (row for row in paired if row["seed"] == seed),
            key=lambda row: row["checkpoint"],
        )
        if not rows:
            continue
        on = normalized_trapezoid([
            (row["checkpoint"], row["ON_full"]) for row in rows
        ])
        off = normalized_trapezoid([
            (row["checkpoint"], row["OFF_full"]) for row in rows
        ])
        life_auc[str(seed)] = {
            "checkpoints": [row["checkpoint"] for row in rows],
            "normalized_trapezoid_on": on,
            "normalized_trapezoid_off": off,
            "on_minus_off": on - off,
            "mean_paired_difference": statistics.fmean(
                row["ON_full"] - row["OFF_full"] for row in rows
            ),
            "positive_pairs": sum(
                row["ON_full"] > row["OFF_full"] for row in rows
            ),
            "negative_pairs": sum(
                row["ON_full"] < row["OFF_full"] for row in rows
            ),
        }

    def top_rows(arm: str, counter: collections.Counter, limit: int = 12) -> list[dict]:
        return [
            {
                "action": action,
                "count": count,
                "distinct_probe_programs_if_first": len(
                    first_action_programs[arm].get(action, set())
                ),
            }
            for action, count in counter.most_common(limit)
        ]

    if args.compact_final:
        if checkpoint_filter is None:
            for seed in seeds:
                observed = tuple(
                    sorted(row["checkpoint"] for row in paired if row["seed"] == seed)
                )
                if observed != EXPECTED_CHECKPOINTS:
                    raise ValueError(
                        f"seed {seed} checkpoints {observed}, "
                        f"expected {EXPECTED_CHECKPOINTS}"
                    )
        terminal_rows = []
        for seed in seeds:
            rows = sorted(
                (row for row in paired if row["seed"] == seed),
                key=lambda row: row["checkpoint"],
            )
            if not rows:
                continue
            row = rows[-1]
            if row["checkpoint"] != 1024:
                raise ValueError(f"seed {seed} lacks terminal checkpoint 1024")
            terminal_rows.append({
                "seed": seed,
                "checkpoint": row["checkpoint"],
                "on": row["ON_full"],
                "off": row["OFF_full"],
                "on_minus_off": row["ON_full"] - row["OFF_full"],
                "on_diagnostics": row["ON_diagnostics"],
                "off_diagnostics": row["OFF_diagnostics"],
                "fixed_action_cap_differences": {
                    str(cap): row[f"ON_k{cap}"] - row[f"OFF_k{cap}"]
                    for cap in CAPS
                },
            })

        cap_scalars = {
            cap: {
                key: value for key, value in payload.items()
                if key != "differences"
            }
            for cap, payload in caps.items()
        }
        caps_by_seed = {}
        for seed in seeds:
            rows = sorted(
                (row for row in paired if row["seed"] == seed),
                key=lambda row: row["checkpoint"],
            )
            caps_by_seed[str(seed)] = {}
            for cap in CAPS:
                diffs = [row[f"ON_k{cap}"] - row[f"OFF_k{cap}"] for row in rows]
                caps_by_seed[str(seed)][str(cap)] = {
                    "n_dependent_checkpoints": len(diffs),
                    "mean_on_minus_off": statistics.fmean(diffs),
                    "median_on_minus_off": statistics.median(diffs),
                    "positive_checkpoints": sum(value > 0 for value in diffs),
                    "negative_checkpoints": sum(value < 0 for value in diffs),
                }
        sleep_endpoints = {
            seed: {
                "first": trajectory[0] if trajectory else None,
                "last": trajectory[-1] if trajectory else None,
            }
            for seed, trajectory in sleep_trajectories.items()
        }
        for seed in seeds:
            life = args.root / f"L_B_seed{seed}"
            observed_sleep_checkpoints = tuple(
                row["checkpoint"] for row in sleep_trajectories[str(seed)]
            )
            if observed_sleep_checkpoints != EXPECTED_SLEEP_CHECKPOINTS:
                raise ValueError(
                    f"seed {seed} sleep checkpoints {observed_sleep_checkpoints}, "
                    f"expected {EXPECTED_SLEEP_CHECKPOINTS}"
                )
            lifecycle_paths = [life / "LIFE_DONE"]
            for checkpoint in EXPECTED_SLEEP_CHECKPOINTS:
                sleep_dir = life / f"sleep_{checkpoint:04d}"
                lifecycle_paths.extend((
                    sleep_dir / "COMPILED",
                    sleep_dir / "adapter" / "DONE",
                ))
            lifecycle_paths.extend((
                life / "sleep_1024" / "adapter" / "adapter_config.json",
                life / "sleep_1024" / "adapter" / "adapter_model.safetensors",
                life / "sleep_1024" / "adapter" / "train_meta.json",
            ))
            missing = [str(path) for path in lifecycle_paths if not path.exists()]
            if missing:
                raise ValueError(f"seed {seed} missing lifecycle artifacts: {missing}")
            consumed_paths.update(lifecycle_paths)

        manifest_entries = [
            file_receipt(path, args.root) for path in sorted(consumed_paths)
        ]
        manifest_canonical = json.dumps(
            manifest_entries, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        manifest = {
            "schema_version": "fable_v61_remote_analysis_receipt_v3",
            "root": str(args.root),
            "entry_count": len(manifest_entries),
            "total_bytes": sum(row["bytes"] for row in manifest_entries),
            "canonical_entries_sha256": hashlib.sha256(
                manifest_canonical
            ).hexdigest(),
            "entries": manifest_entries,
        }
        if args.manifest_only:
            print(json.dumps(manifest, indent=2, sort_keys=True))
            return

        terminal_diffs = [row["on_minus_off"] for row in terminal_rows]
        compact_output = {
            "schema_version": "fable_v61_terminal_analysis_v3",
            "status": "POSTHOC_DIAGNOSTIC_ONLY",
            "root": str(args.root),
            "terminal_rows": terminal_rows,
            "terminal_aggregate": {
                "n": len(terminal_diffs),
                "mean_on_minus_off": (
                    statistics.fmean(terminal_diffs) if terminal_diffs else None
                ),
                "median_on_minus_off": (
                    statistics.median(terminal_diffs) if terminal_diffs else None
                ),
                "positive_roots": sum(value > 0 for value in terminal_diffs),
                "negative_roots": sum(value < 0 for value in terminal_diffs),
            },
            "post_first_write_probe_window_auc_by_seed": life_auc,
            "fixed_action_caps_pooled_dependent_checkpoints": cap_scalars,
            "fixed_action_caps_by_root": caps_by_seed,
            "sleep_corpus_endpoints": sleep_endpoints,
            "artifact_manifest_summary": {
                key: value for key, value in manifest.items() if key != "entries"
            },
        }
        if not args.results_only:
            compact_output["artifact_manifest"] = manifest_entries
        print(json.dumps(compact_output, indent=2, sort_keys=True))
        return

    if args.summary_only:
        checkpoint_summaries = []
        for row in paired:
            checkpoint_summaries.append({
                "seed": row["seed"],
                "checkpoint": row["checkpoint"],
                "on": row["ON_full"],
                "off": row["OFF_full"],
                "on_minus_off": row["ON_full"] - row["OFF_full"],
                "on_diagnostics": row["ON_diagnostics"],
                "off_diagnostics": row["OFF_diagnostics"],
            })
        sleep_endpoints = {}
        for seed, trajectory in sleep_trajectories.items():
            sleep_endpoints[seed] = {
                "first": trajectory[0] if trajectory else None,
                "last": trajectory[-1] if trajectory else None,
            }
        print(json.dumps({
            "status": "POSTHOC_DIAGNOSTIC_ONLY",
            "root": str(args.root),
            "checkpoint_summaries": checkpoint_summaries,
            "fixed_action_caps": caps,
            "post_first_write_probe_window_auc_by_seed": life_auc,
            "sleep_corpus_endpoints": sleep_endpoints,
        }, indent=2, sort_keys=True))
        return

    output = {
        "status": "POSTHOC_DIAGNOSTIC_ONLY",
        "root": str(args.root),
        "paired_checkpoints": paired,
        "post_first_write_probe_window_auc_by_seed": life_auc,
        "sleep_corpus_trajectories": sleep_trajectories,
        "fixed_action_caps": caps,
        "top_all_actions": {
            arm: top_rows(arm, action_counts[arm]) for arm in ("ON", "OFF")
        },
        "top_first_actions": {
            arm: top_rows(arm, first_action_counts[arm]) for arm in ("ON", "OFF")
        },
        "first_action_transitions": [
            {
                "program": key[0],
                "off_action": key[1],
                "on_action": key[2],
                "count": count,
                "mean_score_delta": statistics.fmean(first_action_score_deltas[key]),
            }
            for key, count in first_action_transitions.most_common()
        ],
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

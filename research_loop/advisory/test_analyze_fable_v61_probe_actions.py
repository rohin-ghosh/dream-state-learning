from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from research_loop.advisory.analyze_fable_v61_probe_actions import (
    REGISTERED_PROBES,
    capped_panel,
    complete_checkpoints,
    corpus_marker_diagnostics,
    corpus_texts,
    read_actions,
    read_probe_summary,
    validate_full_panel_against_summary,
)


class TerminalAnalyzerTests(unittest.TestCase):
    def test_capped_panel_floors_negative_scores_at_zero(self) -> None:
        rows = {episode: [] for episode in REGISTERED_PROBES}
        rows[REGISTERED_PROBES[0]] = [{"score": -0.5}]
        self.assertEqual(capped_panel(rows, 1), 0.0)

    def test_read_actions_requires_every_registered_program(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "probe.jsonl"
            rows = [
                {"kind": "thought", "episode_id": episode}
                for episode in REGISTERED_PROBES[:-1]
            ]
            path.write_text("".join(json.dumps(row) + "\n" for row in rows))
            with self.assertRaisesRegex(ValueError, "expected"):
                read_actions(path)

    def test_read_actions_rejects_truncated_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "probe.jsonl"
            path.write_text('{"kind":"thought"\n')
            with self.assertRaisesRegex(ValueError, "invalid JSONL"):
                read_actions(path)

    def test_summary_requires_exact_programs_and_mean(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "probe.json"
            results = {episode: 0.25 for episode in REGISTERED_PROBES}
            path.write_text(json.dumps({"mean": 0.25, "results": results}))
            self.assertEqual(read_probe_summary(path), results)
            path.write_text(json.dumps({"mean": 0.3, "results": results}))
            with self.assertRaisesRegex(ValueError, "mean mismatch"):
                read_probe_summary(path)

    def test_ledger_scores_must_match_summary(self) -> None:
        rows = {episode: [] for episode in REGISTERED_PROBES}
        summary = {episode: 0.0 for episode in REGISTERED_PROBES}
        rows[REGISTERED_PROBES[0]] = [{"score": 0.5}]
        with self.assertRaisesRegex(ValueError, "score mismatch"):
            validate_full_panel_against_summary(
                rows, summary, Path("synthetic.jsonl")
            )

    def test_corpus_reader_uses_only_training_corpus_field(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corpus.json"
            path.write_text(json.dumps({
                "corpus": ["ACT: trained"],
                "n_new": 1,
                "principles": ["ACT: duplicated metadata"],
            }))
            self.assertEqual(corpus_texts(path), ["ACT: trained"])

    def test_source_proxy_marker_diagnostics_are_case_and_column_sensitive(self) -> None:
        result = corpus_marker_diagnostics([
            "ACT: -gvn",
            "ACT -sroa",
            "### ACT: -licm",
            "  ACT: -mem2reg",
            "act: -instcombine",
            "Action: -constprop",
        ])
        self.assertEqual(result["action_label_candidate_lines"], 6)
        self.assertEqual(result["source_proxy_act_syntax_lines"], 2)
        self.assertEqual(result["source_proxy_near_miss_lines"], 4)
        self.assertEqual(result["source_proxy_near_miss_categories"], {
            "decorated_or_action_alias": 1,
            "hash_prefixed": 1,
            "indented_uppercase": 1,
            "lowercase": 1,
        })

    def test_complete_checkpoint_requires_both_ledgers_and_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            life = Path(directory)
            names = (
                "probe_ep0064.ledger.jsonl",
                "probe_ep0064.json",
                "probe_ep0064_adapterOFF.ledger.jsonl",
                "probe_ep0064_adapterOFF.json",
            )
            for name in names[:-1]:
                (life / name).write_text("x")
            self.assertEqual(complete_checkpoints(life), [])
            (life / names[-1]).write_text("x")
            self.assertEqual(complete_checkpoints(life), [64])


if __name__ == "__main__":
    unittest.main()

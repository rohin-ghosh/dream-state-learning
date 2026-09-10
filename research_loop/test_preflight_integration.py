from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from research_loop.preflight import BranchContext, RetryClass
from research_loop.preflight_integration import (
    IntegrationConfig,
    build_operations,
    reviewer_operation,
    run_config,
    test_operation,
)


class PreflightIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.workflow = self.root / "inactive-workflow.json"
        self.lock = self.root / "existing.lock.json"
        self.workflow.write_text('{"name":"future-preflight"}\n', encoding="utf-8")
        self.lock.write_text('{"files":{}}\n', encoding="utf-8")
        self.config = IntegrationConfig(
            workspace=self.root,
            state_dir=self.root / "future-preflight-state",
            workflow_path=self.workflow,
            lock_path=self.lock,
            spec={"purpose": "inactive adapter test"},
            fable_node={"provider": "fable_mailbox", "prompt_file": "unused", "schema_file": "unused", "timeout_sec": 1},
            sol_node={"provider": "codex", "prompt_file": "unused", "schema_file": "unused", "timeout_sec": 1},
            test_node={"argv": ["fake-tests"], "timeout_sec": 1},
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    @staticmethod
    def context(branch: str = "fable") -> BranchContext:
        return BranchContext(branch, f"{branch}-attempt", Path("/tmp/attempt"), {"schema_version": 1})

    def test_fable_unavailable_is_distinct_from_transient_and_scientific_rejection(self) -> None:
        unavailable = reviewer_operation(
            "fable", self.config.fable_node, self.root,
            agent_runner=lambda *args: (75, None),
        )(self.context())
        self.assertEqual(unavailable.retry_class, RetryClass.UNAVAILABLE)

        transient = reviewer_operation(
            "sol", self.config.sol_node, self.root,
            agent_runner=lambda *args: (75, None),
        )(self.context("sol"))
        self.assertEqual(transient.retry_class, RetryClass.TRANSIENT)

        rejected = reviewer_operation(
            "fable", self.config.fable_node, self.root,
            agent_runner=lambda *args: (0, {"verdict": "reject", "summary": "scientific defect"}),
        )(self.context())
        self.assertEqual(rejected.retry_class, RetryClass.SCIENTIFIC_REJECTION)
        self.assertEqual(rejected.status, "rejected")

    def test_test_command_has_deterministic_evidence_and_explicit_failure_class(self) -> None:
        passed = test_operation(
            self.config.test_node, self.root,
            command_runner=lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "all good\n", ""),
        )(self.context("test"))
        self.assertEqual(passed.status, "passed")
        self.assertEqual(passed.evidence["stdout_sha256"], "8a87c7c88bb013c74959ab4aee7e5f01a9d843bdf7d1a3a8fb517f8d872e127a")

        failed = test_operation(
            self.config.test_node, self.root,
            command_runner=lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, "", "assertion failed"),
        )(self.context("test"))
        self.assertEqual(failed.retry_class, RetryClass.PERMANENT_FAILURE)

    def test_full_inactive_integration_fans_out_and_verifies_receipt_with_fakes(self) -> None:
        calls: list[tuple[str, str]] = []

        def fake_agent(node, workspace, attempt_dir, timeout):
            calls.append((node["provider"], node["request_id"]))
            return 0, {"verdict": "approve", "summary": f"{node['provider']} approved"}

        def fake_command(argv, **kwargs):
            return subprocess.CompletedProcess(argv, 0, "6 tests passed\n", "")

        outcome = run_config(self.config, agent_runner=fake_agent, command_runner=fake_command)
        self.assertTrue(outcome["joined"])
        self.assertIn("verified_receipt", outcome)
        self.assertEqual({provider for provider, _ in calls}, {"fable_mailbox", "codex"})
        self.assertEqual(len({request_id for _, request_id in calls}), 2)
        self.assertEqual(outcome["verified_receipt"]["fable_approval"]["status"], "approved")

    def test_fable_unavailable_uses_sol_fallback_without_real_provider(self) -> None:
        def fake_agent(node, workspace, attempt_dir, timeout):
            if node["provider"] == "fable_mailbox":
                return 75, None
            return 0, {"verdict": "approve", "summary": "approved"}

        outcome = run_config(
            self.config,
            agent_runner=fake_agent,
            command_runner=lambda argv, **kwargs: subprocess.CompletedProcess(argv, 0, "ok", ""),
        )
        self.assertTrue(outcome["joined"])
        self.assertEqual(outcome["results"]["fable"]["retry_class"], RetryClass.UNAVAILABLE.value)
        self.assertIsNotNone(outcome["receipt"])
        self.assertEqual(outcome["verified_receipt"]["quorum"]["branches"]["fable"]["reason"], "unavailable_accepted")


if __name__ == "__main__":
    unittest.main()

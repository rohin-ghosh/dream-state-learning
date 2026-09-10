from __future__ import annotations

import hashlib
import json
import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from research_loop.preflight import BranchResult, ReceiptError, RetryClass, digest_json
from research_loop.supervisor_fanout import PreflightCoordinator, QuorumPolicy


class FanoutSupervisorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        self.workflow = root / "workflow.json"
        self.lock = root / "workflow.lock.json"
        self.workflow.write_text('{"name":"inactive-preflight"}\n', encoding="utf-8")
        self.lock.write_text('{"files":{}}\n', encoding="utf-8")
        self.state = root / "state"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def coordinator(self, **kwargs: object) -> PreflightCoordinator:
        return PreflightCoordinator(self.state, self.workflow, self.lock, {"tests": ["unit"]}, **kwargs)

    @staticmethod
    def approved(branch: str) -> BranchResult:
        return BranchResult("passed" if branch == "test" else "approved", evidence={"branch": branch, "deterministic": True})

    def test_fanout_overlaps_and_receipt_binds_all_evidence(self) -> None:
        starts: dict[str, float] = {}
        release = threading.Event()
        all_started = threading.Event()
        lock = threading.Lock()

        def operation(context):
            with lock:
                starts[context.branch] = time.monotonic()
                if len(starts) == 3:
                    all_started.set()
            self.assertTrue(release.wait(2))
            return self.approved(context.branch)

        coordinator = self.coordinator()
        thread = threading.Thread(target=lambda: coordinator.run_preflight({branch: operation for branch in ("fable", "sol", "test")}))
        thread.start()
        self.assertTrue(all_started.wait(2))
        self.assertFalse(coordinator.receipt_path.exists(), "join must wait for branch terminals")
        self.assertLess(max(starts.values()) - min(starts.values()), 0.25)
        release.set()
        thread.join(2)
        self.assertFalse(thread.is_alive())
        receipt = coordinator.verify_receipt()
        self.assertEqual(receipt["fable_approval"]["status"], "approved")
        self.assertEqual(receipt["sol_approval"]["status"], "approved")
        self.assertEqual(receipt["deterministic_test_evidence"]["branch"], "test")

    def test_unavailable_fable_uses_explicit_sol_fallback_and_is_signed(self) -> None:
        def unavailable(context):
            return BranchResult("failed", RetryClass.UNAVAILABLE, detail="Fable unavailable")

        outcome = self.coordinator().run_preflight({
            "fable": unavailable,
            "sol": lambda context: self.approved("sol"),
            "test": lambda context: self.approved("test"),
        })
        self.assertTrue(outcome["joined"])
        self.assertIsNotNone(outcome["receipt"])
        self.assertEqual(outcome["results"]["fable"].retry_class, RetryClass.UNAVAILABLE)
        self.assertEqual(len(list((self.state / "branches" / "fable" / "attempts").iterdir())), 1)
        receipt = self.coordinator().verify_receipt()
        self.assertEqual(receipt["quorum"]["branches"]["fable"]["reason"], "unavailable_accepted")
        self.assertEqual(receipt["fable_approval"]["retry_class"], RetryClass.UNAVAILABLE.value)

    def test_fable_scientific_rejection_and_explicit_transient_policy_block_join(self) -> None:
        rejected = self.coordinator().run_preflight({
            "fable": lambda context: BranchResult("rejected", RetryClass.SCIENTIFIC_REJECTION),
            "sol": lambda context: self.approved("sol"),
            "test": lambda context: self.approved("test"),
        })
        self.assertFalse(rejected["joined"])

        fallback_state = self.state.parent / "transient-fallback"
        fallback = PreflightCoordinator(
            fallback_state, self.workflow, self.lock, {"tests": ["unit"]}, max_attempts=1,
        )
        exhausted = fallback.run_preflight({
            "fable": lambda context: BranchResult("failed", RetryClass.TRANSIENT),
            "sol": lambda context: self.approved("sol"),
            "test": lambda context: self.approved("test"),
        })
        self.assertTrue(exhausted["joined"])
        receipt = fallback.verify_receipt()
        self.assertEqual(receipt["quorum"]["branches"]["fable"]["reason"], "transient_exhausted_as_unavailable")
        self.assertEqual(receipt["quorum"]["branches"]["fable"]["effective_retry_class"], RetryClass.UNAVAILABLE.value)

        state = self.state.parent / "transient-policy"
        coordinator = PreflightCoordinator(
            state, self.workflow, self.lock, {"tests": ["unit"]}, max_attempts=1,
            quorum_policy=QuorumPolicy(fable_transient_exhaustion="blocking"),
        )
        transient = coordinator.run_preflight({
            "fable": lambda context: BranchResult("failed", RetryClass.TRANSIENT),
            "sol": lambda context: self.approved("sol"),
            "test": lambda context: self.approved("test"),
        })
        self.assertFalse(transient["joined"])
        recorded = json.loads(coordinator.state_path.read_text(encoding="utf-8"))
        self.assertEqual(recorded["quorum"]["branches"]["fable"]["reason"], "transient_exhausted_blocking")

    def test_scientific_rejection_is_never_retried_and_transient_ids_are_distinct(self) -> None:
        rejection_calls = 0

        def rejected(context):
            nonlocal rejection_calls
            rejection_calls += 1
            return BranchResult("rejected", RetryClass.SCIENTIFIC_REJECTION, evidence={"reason": "invalid hypothesis"})

        result = self.coordinator(max_attempts=3).execute_branch("fable", rejected)
        self.assertEqual(result.retry_class, RetryClass.SCIENTIFIC_REJECTION)
        self.assertEqual(rejection_calls, 1)

        retry_state = self.state.parent / "retry-state"
        coordinator = PreflightCoordinator(retry_state, self.workflow, self.lock, {"tests": ["unit"]}, max_attempts=2)
        seen: list[str] = []

        def flaky(context):
            seen.append(context.attempt_id)
            if len(seen) == 1:
                return BranchResult("failed", RetryClass.TRANSIENT)
            return self.approved("sol")

        self.assertEqual(coordinator.execute_branch("sol", flaky).status, "approved")
        self.assertEqual(len(seen), 2)
        self.assertNotEqual(*seen)

    def test_tampering_invalidates_content_addressed_receipt(self) -> None:
        coordinator = self.coordinator()
        coordinator.run_preflight({branch: (lambda context, branch=branch: self.approved(branch)) for branch in ("fable", "sol", "test")})
        receipt = json.loads(coordinator.receipt_path.read_text(encoding="utf-8"))
        receipt["quorum_policy"]["accept_fable_unavailable"] = False
        unsigned = dict(receipt)
        unsigned.pop("receipt_sha256")
        receipt["receipt_sha256"] = digest_json(unsigned)
        coordinator.receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        with self.assertRaises(ReceiptError):
            coordinator.verify_receipt()

    def test_freeze_manifest_is_captured_once(self) -> None:
        coordinator = self.coordinator()
        frozen = coordinator.freeze_once()
        self.workflow.write_text('{"name":"changed-after-freeze"}\n', encoding="utf-8")
        self.assertEqual(coordinator.freeze_once(), frozen)
        self.assertNotEqual(frozen["workflow_sha256"], hashlib.sha256(self.workflow.read_bytes()).hexdigest())

    def test_restart_consumes_terminal_marker_without_duplicate_work(self) -> None:
        first = self.coordinator()
        calls = 0

        def fable(context):
            nonlocal calls
            calls += 1
            return self.approved("fable")

        self.assertEqual(first.execute_branch("fable", fable).status, "approved")
        restarted = self.coordinator()

        def must_not_run(context):
            raise AssertionError("recovery should consume terminal marker")

        outcome = restarted.run_preflight({
            "fable": must_not_run,
            "sol": lambda context: self.approved("sol"),
            "test": lambda context: self.approved("test"),
        })
        self.assertTrue(outcome["joined"])
        self.assertEqual(calls, 1)
        state = json.loads(restarted.state_path.read_text(encoding="utf-8"))
        self.assertTrue(state["branches"]["fable"]["recovered"])


if __name__ == "__main__":
    unittest.main()

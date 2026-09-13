"""In-memory candidate regressions; no materialization or scientific evidence."""

from dataclasses import FrozenInstanceError
from hashlib import sha256
from pathlib import Path
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as source


NODE = "M2AN_BBBBBBBBBBBB"
GOAL = "M2AN_CCCCCCCCCCCC"
HUB = "M2AN_DDDDDDDDDDDD"
QUERY = "M2AQ_BBBBBBBBBBBB"
EVENT = "M2AE_BBBBBBBBBBBB"
PORT = "M2AP_BBBBBBBBBBBB"
RECEIPT = "M2AR_BBBBBBBBBBBB"
ROUTE = "M2AI_BBBBBBBBBBBB"
TASK = f"TASK\nSTART {NODE}\nGOAL {GOAL}\nCURRENT {NODE}"


def block(kind, skin=0):
    if kind == "ROUTES":
        row = (f"ROUTE {ROUTE} AT {NODE} FOR {GOAL} QUERY {QUERY}" if skin == 0
               else f"ROUTE {ROUTE} FOR {GOAL} QUERY {QUERY} AT {NODE}")
        return "ROUTES\n" + "\n".join([row] * 24)
    row = (f"EVENT {EVENT} AT {NODE} FOR {GOAL} DID {PORT} GOT {GOAL} RECOVER {QUERY} EVIDENCE {RECEIPT}"
           if skin == 0 else
           f"EVENT {EVENT} FOR {GOAL} AT {NODE} GOT {GOAL} DID {PORT} RECOVER {QUERY} EVIDENCE {RECEIPT}")
    return "EVENTS\n" + "\n".join([row] * 4)


def session():
    service = source.PassiveRegistry({f"READ RELATION {QUERY}": block("EVENTS")}, skin=0)
    return source.Session(TASK, {(NODE, PORT): HUB, (HUB, PORT): GOAL}, service)


def turn(current_session, raw, **overrides):
    values = dict(generation_request={"max_new_tokens": min(256, 4096 - current_session.state.actual_tokens)},
                  declared_tokens=1, actual_tokens=1, context_tokens=0,
                  truncated=False, finish_reason="stop")
    values.update(overrides)
    return current_session.turn(raw, **values)


class WireTests(unittest.TestCase):
    def test_bound_memo_and_system_bytes_no_science_gates(self):
        memo = Path(__file__).resolve().parents[1] / "research_notes/analysis/2026-09-13_m_combine4_stage2a_binding_successor_v2.md"
        raw = memo.read_bytes()
        self.assertEqual(sha256(raw).hexdigest(), source.MEMO_SHA256)
        section = raw.decode().split("### 2.2 System message, exact bytes\n", 1)[1]
        expected = section.split("```text\n", 1)[1].split("\n```", 1)[0]
        self.assertEqual(source.SYSTEM_MESSAGE, expected)
        self.assertEqual(source.STATUS, "PARTIAL_SOURCE_ONLY")
        self.assertTrue(source.SCIENCE_GATES)
        self.assertFalse(any(source.SCIENCE_GATES.values()))

    def test_exact_actions_including_syntactically_valid_sentinels(self):
        for raw in (f"THINK KEEP {EVENT}", f"THINK REVISE {EVENT}", f"THINK REVISE {QUERY}",
                    f"READ INDEX {NODE}", f"READ RELATION {QUERY}", f"STEP {PORT}", "STOP",
                    "THINK KEEP M2AE_AAAAAAAAAAAA", "READ RELATION M2AQ_AAAAAAAAAAAA"):
            with self.subTest(raw=raw):
                self.assertEqual(source.parse_action(raw).operation, raw.split()[0])

    def test_no_trimming_repair_unicode_fences_or_multiple_actions(self):
        bad = ("STOP\n", "STOP\r", " STOP", "STOP ", "STOP\nSTOP", "```STOP```", "ＳＴＯＰ",
               "STOP\x00", "THINK inspect", f"THINK KEEP {QUERY}", f"READ EVENT {EVENT}",
               f"STEP {NODE}", f"READ  INDEX {NODE}", "", "\ud800", b"STOP", None)
        for raw in bad:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                source.parse_action(raw)

    def test_task_and_world_envelopes(self):
        self.assertEqual(source.parse_task(TASK).current, NODE)
        self.assertEqual(source.parse_world(f"WORLD\nCURRENT {GOAL}"), GOAL)
        for raw in (TASK + "\n", TASK.replace("TASK", "TASK "), TASK.replace(NODE, "M2AN_AAAAAAAAAAAA")):
            with self.assertRaises(ValueError):
                source.parse_task(raw)
        for raw in (f"CURRENT {GOAL}", f"WORLD\nCURRENT {GOAL}\n", f"WORLD\nCURRENT {PORT}"):
            with self.assertRaises(ValueError):
                source.parse_world(raw)

    def test_both_service_skins_exact_counts_order_and_bytes(self):
        for skin in (0, 1):
            for kind, count in (("ROUTES", 24), ("EVENTS", 4)):
                raw = block(kind, skin)
                parsed = source.parse_service(raw, skin=skin)
                self.assertEqual(parsed.raw, raw)
                self.assertEqual(len(parsed.rows), count)
                self.assertEqual(parsed.rows[0].goal, GOAL)
                for bad in (raw + "\n", raw + " ", raw.replace("\n", "\r\n"),
                            "\n".join(raw.split("\n")[:-1]), raw + "\n" + raw.split("\n")[1],
                            raw.replace(NODE, "M2AN_AAAAAAAAAAAA"), raw.replace(" AT ", "  AT ")):
                    with self.subTest(kind=kind, skin=skin, bad=bad), self.assertRaises(ValueError):
                        source.parse_service(bad, skin=skin)
                with self.assertRaises(ValueError):
                    source.parse_service(raw, skin=1-skin)
        for skin in (True, "0", -1, 2):
            with self.assertRaises(ValueError):
                source.parse_service("MISS", skin=skin)

    def test_registry_is_passive_snapshot_with_unknown_miss(self):
        entries = {f"READ INDEX {NODE}": block("ROUTES"), f"READ RELATION {QUERY}": block("EVENTS")}
        registry = source.PassiveRegistry(entries, skin=0)
        entries.clear()
        self.assertEqual(registry.read(f"READ INDEX {NODE}"), block("ROUTES"))
        self.assertEqual(registry.read(f"READ RELATION {QUERY}"), block("EVENTS"))
        self.assertEqual(registry.read(f"READ INDEX {HUB}"), "MISS")
        self.assertEqual(registry.read("READ RELATION M2AQ_AAAAAAAAAAAA"), "MISS")
        with self.assertRaises(TypeError):
            registry.read(f"READ INDEX {NODE}", goal=GOAL)
        for entries in ({"STOP": "MISS"}, {f"READ INDEX {NODE}": block("EVENTS")},
                        {"READ INDEX M2AN_AAAAAAAAAAAA": "MISS"}):
            with self.assertRaises(ValueError):
                source.PassiveRegistry(entries, skin=0)
        for bad in ("STOP", f"READ INDEX {NODE}\n"):
            with self.assertRaises(ValueError):
                registry.read(bad)

    def test_row_order_is_not_repaired_and_mixed_skins_fail(self):
        for skin in (0, 1):
            raw = block("EVENTS", skin)
            lines = raw.split("\n")
            lines[2] = lines[2].replace(EVENT, "M2AE_CCCCCCCCCCCC")
            lines[3] = lines[3].replace(EVENT, "M2AE_DDDDDDDDDDDD")
            varied = "\n".join(lines)
            registry = source.PassiveRegistry({f"READ RELATION {QUERY}": varied}, skin=skin)
            self.assertEqual(registry.read(f"READ RELATION {QUERY}"), varied)
            self.assertEqual([row.event for row in source.parse_service(varied, skin=skin).rows],
                             [EVENT, "M2AE_CCCCCCCCCCCC", "M2AE_DDDDDDDDDDDD", EVENT])
            lines[2] = block("EVENTS", 1-skin).split("\n")[1]
            with self.assertRaises(ValueError):
                source.parse_service("\n".join(lines), skin=skin)


class SessionTests(unittest.TestCase):
    def test_world_not_event_prediction_is_authoritative_exact_stop_required(self):
        current = session()
        read = turn(current, f"READ RELATION {QUERY}")
        self.assertEqual(read.response_bytes, ("SERVICE\n" + block("EVENTS")).encode())
        moved = turn(current, f"STEP {PORT}")
        self.assertEqual(moved.response_bytes, f"WORLD\nCURRENT {HUB}".encode())
        self.assertFalse(current.state.goal_arrival_stop)
        check = turn(current, f"THINK REVISE {EVENT}")
        self.assertEqual(check.response_bytes, b"ACK")
        turn(current, f"STEP {PORT}")
        self.assertFalse(current.state.terminated)
        self.assertFalse(current.state.goal_arrival_stop)
        stopped = turn(current, "STOP")
        self.assertTrue(stopped.accepted)
        self.assertTrue(current.state.goal_arrival_stop)
        self.assertEqual(stopped.response_bytes, b"")
        self.assertEqual(len(current.receipts), 3)
        before = current.state
        rejected = turn(current, "STOP")
        self.assertEqual(rejected.terminal_reason, "session_terminated")
        self.assertFalse(rejected.accepted)
        self.assertEqual(current.state, before)
        self.assertEqual(len(current.attempts), 6)

    def test_miss_is_valid_and_no_host_correction_of_think(self):
        current = session()
        self.assertEqual(turn(current, f"READ INDEX {HUB}").response_bytes, b"SERVICE\nMISS")
        self.assertEqual(turn(current, "THINK KEEP M2AE_AAAAAAAAAAAA").response_bytes, b"ACK")
        self.assertFalse(current.state.terminated)
        self.assertFalse(any(source.SCIENCE_GATES.values()))

    def test_premature_stop_and_invalid_step_fail_without_repair(self):
        current = session()
        stopped = turn(current, "STOP")
        self.assertEqual(stopped.terminal_reason, "premature_stop")
        self.assertFalse(current.state.goal_arrival_stop)
        for raw in ("STEP M2AP_AAAAAAAAAAAA", "STOP\n", "READ HIDDEN whatever"):
            current = session()
            failed = turn(current, raw)
            self.assertFalse(failed.accepted)
            self.assertEqual(failed.response_bytes, b"")
            self.assertEqual(current.state.current, NODE)
            self.assertEqual(current.receipts, ())
            self.assertEqual(failed.capture.raw_bytes, raw.encode())

    def test_capture_precedes_parser_and_is_immutable(self):
        current = session()
        original = source.parse_action
        def inspect_capture(raw):
            self.assertEqual(len(current.raw_attempts), 1)
            self.assertEqual(current.raw_attempts[0].raw_bytes, b"STOP\n")
            self.assertEqual(current.attempts, ())
            return original(raw)
        with patch.object(source, "parse_action", side_effect=inspect_capture):
            failed = turn(current, "STOP\n")
        self.assertIs(failed.capture, current.raw_attempts[0])
        self.assertEqual(failed.parser_disposition, "invalid")
        with self.assertRaises(FrozenInstanceError):
            failed.accepted = True
        with self.assertRaises(FrozenInstanceError):
            failed.capture.call_index = 42

    def test_nonstring_and_invalid_unicode_custody_without_stringification(self):
        raw_values = (None, 17, True, 1.5, b"\xffSTOP", bytearray(b"STOP"),
                      ["STOP", {"raw": b"\xff"}], {"action": "STOP"}, "\ud800", "STÖP")
        for raw in raw_values:
            with self.subTest(raw=raw):
                current = session()
                result = turn(current, raw)
                self.assertFalse(result.accepted)
                self.assertEqual(result.capture.raw, source._freeze(raw))
                self.assertEqual(result.terminal_reason, "malformed_action")
        self.assertEqual(turn(session(), "STÖP").capture.raw_bytes, "STÖP".encode("utf-8"))
        self.assertEqual(turn(session(), b"\xffSTOP").capture.raw_bytes, b"\xffSTOP")
        raw = {"action": ["STOP"]}
        request = {"max_new_tokens": 256, "metadata": ["original"]}
        result = turn(session(), raw, generation_request=request)
        saved = result.capture
        raw["action"].append("changed")
        request["metadata"].clear()
        self.assertNotEqual(saved.raw, source._freeze(raw))
        self.assertNotEqual(saved.generation_request, source._freeze(request))

    def test_unsupported_transport_fails_closed_without_repr_fallback(self):
        current = session()
        with self.assertRaisesRegex(ValueError, "unsupported_custody_transport"):
            turn(current, object())
        self.assertTrue(current.state.terminated)
        cyclic = []
        cyclic.append(cyclic)
        with self.assertRaisesRegex(ValueError, "unsupported_custody_transport"):
            turn(session(), cyclic)

    def test_unsupported_raw_or_metadata_preserves_terminal_success_and_failure(self):
        for success in (False, True):
            for field in ("raw", "generation_request", "declared_tokens", "actual_tokens",
                          "context_tokens", "truncated", "finish_reason"):
                with self.subTest(success=success, field=field):
                    current = session()
                    turn(current, f"READ RELATION {QUERY}")
                    if success:
                        turn(current, f"STEP {PORT}")
                        turn(current, f"STEP {PORT}")
                    turn(current, "STOP")
                    before = current.state
                    history = (current.raw_attempts, current.attempts, current.receipts)
                    self.assertTrue(before.terminated)
                    self.assertEqual(before.goal_arrival_stop, success)
                    overrides = {"raw": "STOP", field: object()}
                    with self.assertRaisesRegex(ValueError, "unsupported_custody_transport"):
                        turn(current, **overrides)
                    self.assertIs(current.state, before)
                    self.assertEqual((current.raw_attempts, current.attempts, current.receipts), history)

    def test_deep_builtin_raw_or_metadata_terminates_active_session(self):
        nested = "STOP"
        for _ in range(1200):
            nested = [nested]
        for field in ("raw", "generation_request", "declared_tokens", "actual_tokens",
                      "context_tokens", "truncated", "finish_reason"):
            with self.subTest(field=field):
                current = session()
                turn(current, f"READ RELATION {QUERY}")
                turn(current, f"STEP {PORT}")
                before = current.state
                history = (current.raw_attempts, current.attempts, current.receipts)
                overrides = {"raw": "STOP", field: nested}
                with self.assertRaisesRegex(ValueError, "unsupported_custody_transport"):
                    turn(current, **overrides)
                self.assertEqual(current.state, source.Snapshot(
                    before.current, before.counts, before.actual_tokens,
                    True, "unsupported_custody_transport", False))
                self.assertEqual((current.raw_attempts, current.attempts, current.receipts), history)

    def test_deep_builtin_raw_or_metadata_preserves_terminal_success_and_failure(self):
        nested = "STOP"
        for _ in range(1200):
            nested = [nested]
        for success in (False, True):
            for field in ("raw", "generation_request", "declared_tokens", "actual_tokens",
                          "context_tokens", "truncated", "finish_reason"):
                with self.subTest(success=success, field=field):
                    current = session()
                    turn(current, f"READ RELATION {QUERY}")
                    if success:
                        turn(current, f"STEP {PORT}")
                        turn(current, f"STEP {PORT}")
                    turn(current, "STOP")
                    before = current.state
                    history = (current.raw_attempts, current.attempts, current.receipts)
                    self.assertEqual(before.goal_arrival_stop, success)
                    overrides = {"raw": "STOP", field: nested}
                    with self.assertRaisesRegex(ValueError, "unsupported_custody_transport"):
                        turn(current, **overrides)
                    self.assertIs(current.state, before)
                    self.assertEqual((current.raw_attempts, current.attempts, current.receipts), history)

    def test_operation_budgets_and_separate_raw_receipts(self):
        cases = ((f"THINK KEEP {EVENT}", 8), (f"READ INDEX {HUB}", 12), (f"STEP {PORT}", 8))
        for raw, limit in cases:
            current = source.Session(TASK, {(NODE, PORT): NODE}, source.PassiveRegistry({}, skin=0))
            for _ in range(limit):
                self.assertTrue(turn(current, raw).accepted)
            failed = turn(current, raw)
            self.assertEqual(failed.terminal_reason, "over_budget")
            self.assertEqual(len(current.raw_attempts), limit + 1)
            self.assertEqual(len(current.attempts), limit + 1)
            self.assertFalse(failed.accepted)

    def test_aggregate_token_and_context_allowances(self):
        current = session()
        for _ in range(8):
            self.assertTrue(turn(current, f"THINK KEEP {EVENT}", declared_tokens=256, actual_tokens=256).accepted)
        for _ in range(8):
            self.assertTrue(turn(current, f"READ INDEX {NODE}", declared_tokens=256, actual_tokens=256).accepted)
        self.assertEqual(current.state.actual_tokens, 4096)
        self.assertEqual(turn(current, "STOP", declared_tokens=0, actual_tokens=0).terminal_reason, "zero_allowance")
        current = session()
        self.assertTrue(turn(current, f"READ INDEX {NODE}", context_tokens=16380,
                             generation_request={"max_new_tokens": 4}, declared_tokens=4, actual_tokens=4).accepted)
        self.assertEqual(turn(session(), "STOP", context_tokens=16384).terminal_reason, "zero_allowance")

    def test_twenty_nine_calls_include_stop_no_retry_after_terminal(self):
        task = TASK.replace(f"GOAL {GOAL}", f"GOAL {NODE}")
        current = source.Session(task, {(NODE, PORT): NODE}, source.PassiveRegistry({}, skin=0))
        for raw, limit in ((f"THINK KEEP {EVENT}", 8), (f"READ INDEX {NODE}", 12), (f"STEP {PORT}", 8)):
            for _ in range(limit):
                self.assertTrue(turn(current, raw).accepted)
        self.assertTrue(turn(current, "STOP").accepted)
        self.assertEqual(len(current.attempts), source.CALL_CAP)
        self.assertEqual(current.attempts[-1].capture.call_index, 28)
        self.assertFalse(turn(current, "STOP").accepted)

    def test_generation_metadata_fails_closed_with_custody(self):
        cases = (
            {"actual_tokens": True}, {"declared_tokens": 2}, {"actual_tokens": -1},
            {"actual_tokens": 257, "declared_tokens": 257}, {"context_tokens": -1},
            {"context_tokens": True}, {"truncated": "false"}, {"truncated": True},
            {"finish_reason": "length"}, {"finish_reason": None},
            {"finish_reason": "unknown"}, {"actual_tokens": 0, "declared_tokens": 0},
            {"generation_request": {"max_new_tokens": 255}},
            {"generation_request": {"max_new_tokens": True}},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                current = session()
                failed = turn(current, "STOP", **overrides)
                self.assertFalse(failed.accepted)
                self.assertEqual(len(current.raw_attempts), 1)
                self.assertEqual(current.receipts, ())
                self.assertEqual(failed.response_bytes, b"")
        self.assertEqual(turn(session(), "STOP", finish_reason="unknown").terminal_reason,
                         "unbound_finish_reason")

    def test_world_mapping_is_copied_and_reserved_allocations_rejected(self):
        transitions = {(NODE, PORT): GOAL}
        current = source.Session(TASK, transitions, source.PassiveRegistry({}, skin=0))
        transitions[NODE, PORT] = HUB
        self.assertEqual(turn(current, f"STEP {PORT}").post_state.current, GOAL)
        with self.assertRaises(ValueError):
            source.Session(TASK, {(NODE, "M2AP_AAAAAAAAAAAA"): GOAL}, source.PassiveRegistry({}, skin=0))


if __name__ == "__main__":
    unittest.main()

"""CPU fixtures only; these are not native model/scientific evidence."""
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from organism_v6 import relation_surface_diagnostic as diagnostic

base = diagnostic.base


class Tokenizer:
    def __init__(self):
        self.pieces = [""]

    def encode(self, text):
        result = []
        for offset in range(0, len(text), 4):
            piece = text[offset:offset + 4]
            if piece not in self.pieces:
                self.pieces.append(piece)
            result.append(self.pieces.index(piece))
        return result

    def decode(self, tokens, **kwargs):
        return "".join(self.pieces[token] for token in tokens)

    def apply_chat_template(self, messages, **kwargs):
        return "<user>" + messages[0]["content"] + "</user><assistant>"


class Backend:
    def __init__(self, identity, tokenizer, diagnostic_text="not a relation"):
        self.source_identity, self.tokenizer = identity, tokenizer
        self.backend = object()
        self.diagnostic_text = diagnostic_text
        self.seen = []

    def identity(self):
        return self.source_identity

    def generate(self, request):
        self.seen.append(copy.deepcopy(request))
        if "surface" in request:
            text = self.diagnostic_text
        elif request["role"] == "wake":
            text = {1: "PREDICT: F\nACT: TRY 2,3,4", 2: "PREDICT: T\nACT: TRY 1,2,3",
                    3: "ACT: TRY 0,1,2", 4: "ACT: QUIZ ?", 5: "ACT: QUIZ T,T,T,T,T,T"}[request["tick"]]
        elif request["role"] in ("parent", "restate"):
            text = "Thank you for participating."
        else:
            fields = json.loads(request["prompt"].split("Observed fields: ")[1].splitlines()[0])
            text = json.dumps(dict({"try": fields["values"]}, observed=fields["observed"],
                                   predicted=fields["predicted"], relation="matched"))
        rendered = self.tokenizer.apply_chat_template([{"role": "user", "content": request["prompt"]}])
        return dict(text=text, rendered_prompt=rendered, prompt_token_ids=self.tokenizer.encode(rendered),
                    output_token_ids=self.tokenizer.encode(text), finish_reason="stop", stop_reason=None)


class RelationSurfaceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.model = self.root / "model"
        self.model.mkdir()
        base.write_json(self.model / "config.json", dict(model_type="qwen2"))
        self.formation = self.root / "formation"
        self.lease = datetime.fromtimestamp(time.time() + 3600, timezone.utc).isoformat()
        self.original = base.prepare(self.formation, self.model, "0", self.lease, "interaction_v2")
        self.identity = base.expected_identity(self.original)
        self.tokenizer = Tokenizer()
        data = self.formation / "formation" / "data"
        data.mkdir(parents=True)
        calls = base.Calls(data / "calls", Backend(self.identity, self.tokenizer), "formation", self.identity, "interaction_v2")
        events = base.Events(data / "events.jsonl")
        base.write_json(data / "result.json", base.run_formation(calls, events))
        base.write_json(data / "identity.json", dict(stage="formation", cell=None, backend=self.identity,
                        model_files=self.original["model_files"], protocol="interaction_v2"))
        base.write_json(data / "usage.json", base.usage(data))
        base.capture_manifest(data)
        for name, value in (("SEALED_MANIFEST", base.digest(data / "manifest.json")),
                            ("SEALED_PLAN", base.digest(self.formation / "plan.json"))):
            context = patch.object(diagnostic, name, value)
            context.start()
            self.addCleanup(context.stop)
        context = patch.object(base, "native_tokenizer", return_value=self.tokenizer)
        context.start()
        self.addCleanup(context.stop)
        self.out = self.root / "diagnostic"

    def prepare(self):
        return diagnostic.prepare(self.formation, self.out, "0", self.lease)

    def test_binding_prompts_and_budget_without_answer_injection(self):
        _, cases = diagnostic.bind(self.formation)
        fixed = diagnostic.requests(cases)
        self.assertEqual(len(fixed), 9)
        self.assertEqual(sum(row["max_tokens"] for row in fixed), 624)
        for index, case in enumerate(cases):
            original, full, token = fixed[index * 3:index * 3 + 3]
            self.assertEqual(original["prompt"], case["original_request"]["prompt"])
            self.assertEqual(full["prompt"], original["prompt"] + "\n" + diagnostic.MAPPING)
            self.assertEqual(token["prompt"], case["prefix"] + diagnostic.MAPPING + "\n" + diagnostic.TOKEN_ONLY)
            self.assertEqual(original["execution_id"], f"P:rule0/astra-minimum-20260912/lesson0/apply#t{index + 1}")
            self.assertEqual([row["surface"] for row in (original, full, token)], list(diagnostic.SURFACES))
        self.assertTrue(all(row["temperature"] == 0 and row["seed"] == 20260912 for row in fixed))
        altered = copy.deepcopy(cases)
        for case in altered:
            case["execution"]["predicted"] = "DO NOT INJECT CPU ANSWERS"
        self.assertEqual(diagnostic.requests(altered), fixed)

    def test_binding_rejects_wrong_link_and_raw_tampering(self):
        data = self.formation / "formation" / "data"
        audit = base.check_capture(data)
        next(row for row in audit["events"] if row.get("call_id") == "0008")["source_call_id"] = "0009"
        with patch.object(base, "check_capture", return_value=audit), self.assertRaisesRegex(ValueError, "binding"):
            diagnostic.bind(self.formation)
        path = data / "calls" / "0008.request.json"
        path.write_text(path.read_text().replace("Actual world response", "Fabricated world response"))
        with self.assertRaises(ValueError):
            diagnostic.bind(self.formation)

    def test_prepare_pins_fresh_roots_and_never_loads_backend(self):
        before = base.tree_hashes(self.formation)
        with patch.object(base, "NativeBackend") as backend:
            plan = self.prepare()
            backend.assert_not_called()
        self.assertEqual(plan["requests"], diagnostic.verify(self.out)[0]["requests"])
        self.assertEqual(base.tree_hashes(self.formation), before)
        with self.assertRaises(ValueError):
            self.prepare()
        (self.model / "new-file").write_text("changed")
        with self.assertRaisesRegex(ValueError, "model pins"):
            diagnostic.verify(self.out)

    def test_parse_failures_preserved_and_native_costs_reduced(self):
        plan = self.prepare()
        path = self.out / "run" / "data"
        path.mkdir(parents=True)
        backend = Backend(self.identity, self.tokenizer)
        closer = Mock(return_value=True)
        diagnostic.capture(plan, path, lambda *args: backend, closer)
        closer.assert_called_once_with(backend.backend)
        stage = self.out / "run" / "worker"
        stage.mkdir()
        base.write_json(stage / "supervision.json", dict(ok=True, reservation_release_verified=True, reserved_seconds=1))
        result = diagnostic.reduce(self.out)
        self.assertEqual(len(result["rows"]), 9)
        self.assertTrue(all(row["unparseable"] and row["mapped_answer"] is None and
                            row["raw_text"] == "not a relation" for row in result["rows"]))
        self.assertEqual([row["expected"] for row in result["rows"]], ["mismatched"] * 3 + ["matched"] * 3 + ["unavailable"] * 3)
        self.assertEqual(result["cost"]["record"]["requests"], 9)
        self.assertEqual(result["cost"]["record"]["output_token_ceiling"], 624)
        self.assertEqual(backend.seen, plan["requests"])

    def test_cleanup_after_generation_failure_preserves_request(self):
        plan = self.prepare()
        path = self.root / "failed"
        path.mkdir()
        backend = Backend(self.identity, self.tokenizer)
        backend.generate = Mock(side_effect=RuntimeError("native failure"))
        closer = Mock(return_value=True)
        with self.assertRaisesRegex(RuntimeError, "native failure"):
            diagnostic.capture(plan, path, lambda *args: backend, closer)
        closer.assert_called_once_with(backend.backend)
        self.assertTrue((path / "calls" / "0000.request.json").exists())
        self.assertFalse((path / "manifest.json").exists())
        self.assertTrue(base.read(path / "backend.cleanup.json")["closed"])

    def test_failed_cleanup_and_loader_failure_are_not_success(self):
        plan = self.prepare()
        path = self.root / "cleanup-failed"
        path.mkdir()
        backend = Backend(self.identity, self.tokenizer)
        with self.assertRaisesRegex(ValueError, "retain reservation"):
            diagnostic.capture(plan, path, lambda *args: backend, Mock(return_value=False))
        self.assertFalse((path / "manifest.json").exists())
        path = self.root / "load-failed"
        path.mkdir()
        closer = Mock(return_value=True)
        with self.assertRaisesRegex(RuntimeError, "load failure"):
            diagnostic.capture(plan, path, Mock(side_effect=RuntimeError("load failure")), closer)
        closer.assert_called_once_with(None)

    def test_explicit_opt_in_and_strict_parsing(self):
        with patch.object(diagnostic, "verify") as verify, self.assertRaises(ValueError):
            diagnostic.run(self.out)
        verify.assert_not_called()
        self.assertEqual(diagnostic.mapped(" matched\n", "tokenclarified"), ("matched", False))
        self.assertEqual(diagnostic.mapped('"matched"', "tokenclarified"), (None, True))
        self.assertEqual(diagnostic.mapped('{"relation":"matched"}', "original"), (None, True))

    def test_run_reuses_single_supervisor_and_cannot_retry(self):
        self.prepare()
        with patch.object(base, "supervise", return_value={"ok": True}) as supervise:
            diagnostic.run(self.out, allow_gpu=True)
            self.assertEqual(supervise.call_count, 1)
            command = supervise.call_args.args[3]
            self.assertIn("organism_v6.relation_surface_diagnostic", command)
            self.assertEqual(base.WORKER_SECONDS, 600)
            with self.assertRaises(ValueError):
                diagnostic.run(self.out, allow_gpu=True)
            self.assertEqual(supervise.call_count, 1)

    def test_parent_watch_signals_only_owned_group_and_restores_handlers(self):
        plan = self.prepare()
        stage = self.out / "run" / "worker"
        stage.mkdir(parents=True)
        base.write_json(stage / "process.json", dict(pid=4242))
        stopped, thread = Mock(), Mock()
        stopped.wait.return_value = False
        def start_thread(target, daemon):
            thread.start.side_effect = target
            return thread
        with patch.object(diagnostic, "verify", return_value=(plan, [])), \
             patch.object(base.supervisor, "selected_device", return_value="0"), \
             patch.object(os, "getpid", return_value=4242), patch.object(os, "getpgrp", return_value=4242), \
             patch.object(os, "getppid", side_effect=[7, 8]), patch.object(os, "killpg") as kill, \
             patch.object(signal, "signal") as handlers, patch.object(diagnostic, "capture") as capture, \
             patch.object(diagnostic.threading, "Event", return_value=stopped), \
             patch.object(diagnostic.threading, "Thread", side_effect=start_thread):
            diagnostic.worker(self.out)
        kill.assert_called_once_with(4242, signal.SIGTERM)
        stopped.set.assert_called_once()
        thread.join.assert_called_once()
        self.assertEqual(handlers.call_count, 4)
        capture.assert_called_once()


if __name__ == "__main__":
    unittest.main()

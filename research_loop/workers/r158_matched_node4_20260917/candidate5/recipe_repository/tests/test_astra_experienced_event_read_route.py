from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from gpu import astra_experienced_event_read_route as runner


class Engine:
    def __init__(self, bank):
        self.bank = bank
        self.disabled = False
        self.model = self
        self.calls = []

    @contextmanager
    def disable_adapter(self):
        self.disabled = True
        try:
            yield
        finally:
            self.disabled = False

    def generate(self, messages):
        self.calls.append((messages, self.disabled))
        prompt = messages[-1]["content"]
        if messages[0]["content"] == runner.source.world.MEMORY_SYSTEM:
            raw = "MISS"
        elif len(messages) == 2:
            address = prompt.split("EVENTS ")[1].split(",")[0]
            raw = "READ EVENT " + address
        else:
            port = messages[1]["content"].split("PORTS ")[1].split(",")[0]
            raw = "ROUTE " + port
        return dict(raw=raw, terminal=True, truncated=False)


class ReadRouteNativeTests(unittest.TestCase):
    def test_reader_only_disable_and_failure_inclusive_denominator(self):
        bank = runner.source.material.build_bank(runner.source.MASTER)
        engine = Engine(bank)
        with TemporaryDirectory() as directory:
            result = runner.evaluate(engine, bank, "FITTED_READER_OFF", Path(directory))
        self.assertEqual(result["denominator"], 4)
        self.assertEqual(result["reached_goal"], 2)
        self.assertEqual(result["model_calls"], 12)
        self.assertEqual(result["reader_calls"], 4)
        self.assertFalse(engine.disabled)
        for messages, disabled in engine.calls:
            self.assertEqual(disabled, messages[0]["content"] == runner.source.world.MEMORY_SYSTEM)

    def test_base_and_fitted_do_not_toggle_adapter(self):
        bank = runner.source.material.build_bank(runner.source.MASTER)
        for arm in ("BASE", "FITTED"):
            engine = Engine(bank)
            with TemporaryDirectory() as directory:
                runner.evaluate(engine, bank, arm, Path(directory))
            self.assertFalse(any(disabled for unused_messages, disabled in engine.calls))

    def test_reject_unknown_arm_before_calls(self):
        engine = Engine([])
        with TemporaryDirectory() as directory, self.assertRaises(ValueError):
            runner.evaluate(engine, [], "OTHER", Path(directory))
        self.assertEqual(engine.calls, [])


if __name__ == "__main__":
    unittest.main()

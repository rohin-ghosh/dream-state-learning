import unittest

from gpu import orch_r119_grid_shared_parent as subject


class SharedParentTests(unittest.TestCase):
    def test_exact_A4_scope_and_historical_pending_preserved(self):
        source = subject.source()
        compile(source, 'shared_broker', 'exec')
        self.assertIn("args.after_parent == 40", source)
        self.assertIn("config['max_parent_calls'] == 298", source)
        self.assertIn("/orch_r115_grid_pair_20260915/A4'", source)
        self.assertIn("'R119_GRID_SHARED_TERMINAL.json'", source)
        self.assertIn('HISTORICAL_NO_REDISPATCH', source)

    def test_clock_source_bindings_and_high_wait600(self):
        source = subject.source()
        self.assertIn("ready['startup_bindings'].values()", source)
        self.assertIn("store.hash(Path(reference['path']))", source)
        self.assertIn("'min(570, deadline - time.time())'", source)
        self.assertIn("\"'high'\"", source)


if __name__ == '__main__':
    unittest.main()

import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location("retire_legacy", Path(__file__).with_name("retire_legacy.py"))
retire = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retire)


class ScopeTests(unittest.TestCase):
    def inputs(self, label="C3"):
        physical, process_id, ticks, control = retire.TARGETS[label]
        plan = dict(root=str(retire.BASE / ("orch_r153_community_" + label + "_20260916_attempt1/life")),
                    physical=physical, source_root=str(retire.BASE / control / "source"))
        actor = dict(pid=process_id, start_ticks=ticks, uid=2524)
        return plan, actor

    def test_four_explicit_targets(self):
        self.assertEqual(set(retire.TARGETS), {"C1", "C3", "C4", "C5"})
        for label in retire.TARGETS:
            self.assertEqual(str(retire.validate_scope(label, *self.inputs(label))), self.inputs(label)[0]["root"])

    def test_C2_rejected(self):
        with self.assertRaises(ValueError):
            retire.validate_scope("C2", *self.inputs())

    def test_judge_rejected(self):
        with self.assertRaises(ValueError):
            retire.validate_scope("judge10x", *self.inputs())

    def test_wrong_root_rejected(self):
        plan, actor = self.inputs()
        plan["root"] = plan["root"].replace("C3", "C2")
        with self.assertRaises(ValueError):
            retire.validate_scope("C3", plan, actor)

    def test_pid_reuse_rejected(self):
        plan, actor = self.inputs()
        actor["start_ticks"] = "1"
        with self.assertRaises(ValueError):
            retire.validate_scope("C3", plan, actor)

    def test_other_slot_rejected(self):
        plan, actor = self.inputs()
        plan["physical"] = 1
        with self.assertRaises(ValueError):
            retire.validate_scope("C3", plan, actor)

    def test_new_source_rejected(self):
        plan, actor = self.inputs()
        plan["source_root"] += "_replacement"
        with self.assertRaises(ValueError):
            retire.validate_scope("C3", plan, actor)


if __name__ == "__main__":
    unittest.main()

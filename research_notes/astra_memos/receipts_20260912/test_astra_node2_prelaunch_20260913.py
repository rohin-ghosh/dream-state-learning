import importlib.util
import unittest

spec = importlib.util.spec_from_file_location("node2_check", "/tmp/astra_node2_prelaunch_20260913.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ExceptionTests(unittest.TestCase):
    def test_exact_daemons_only(self):
        for record in checker.DAEMONS:
            self.assertIsNotNone(checker.exception_reason(record, set()))
            for field in record:
                changed = dict(record)
                changed[field] = record[field] + 1 if isinstance(record[field], int) else record[field] + "x"
                self.assertIsNone(checker.exception_reason(changed, set()))

    def test_own_transport_ancestry_and_hash_required(self):
        record = dict(pid=44, comm="sshd", ppid=43, start_ticks=100, uid=2524,
                      cmdline_sha256=checker.TRANSPORT_COMMAND_SHA)
        self.assertIsNotNone(checker.exception_reason(record, {44}))
        self.assertIsNone(checker.exception_reason(record, {45}))
        self.assertIsNone(checker.exception_reason(dict(record, cmdline_sha256="bad"), {44}))
        self.assertIsNone(checker.exception_reason(dict(record, comm="python"), {44}))
        self.assertIsNone(checker.exception_reason(dict(record, uid=0), {44}))

    def test_reservation_indices_uuids_and_all(self):
        for devices in ("1", "0, 1", "GPU-one", "all"):
            self.assertTrue(checker.selected(devices, 1, "GPU-one"))
        for devices in ("", "10", "GPU-two", "-1"):
            self.assertFalse(checker.selected(devices, 1, "GPU-one"))


if __name__ == "__main__":
    unittest.main()

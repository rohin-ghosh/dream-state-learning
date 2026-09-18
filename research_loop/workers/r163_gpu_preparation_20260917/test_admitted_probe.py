import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location('admitted_probe', Path(__file__).with_name('admitted_probe.py'))
operator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)


class AdmissionTests(unittest.TestCase):
    def test_exact_main_go(self):
        binding = {'hard_end_unix': 1789646400}
        go = dict(schema='R163_NODE3_NUMERICAL_GO_V1', issuer='Main', decision='GO', binding=binding,
                  not_before_unix=1789644700, expires_unix=1789646400)
        operator.validate_go(go, binding, 1789644800)
        for key, value in (('issuer', 'Worker'), ('decision', 'READY'), ('binding', {}),
                           ('expires_unix', 1789644700), ('not_before_unix', 1789644900)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                operator.validate_go(dict(go, **{key: value}), binding, 1789644800)

    def test_thirty_minute_and_six_hour_bounds(self):
        for wall, now in ((1789646400, 1789644000), (1789646401, 1789644800)):
            binding = dict(hard_end_unix=wall)
            go = dict(schema='R163_NODE3_NUMERICAL_GO_V1', issuer='Main', decision='GO', binding=binding,
                      not_before_unix=now, expires_unix=wall)
            with self.subTest(wall=wall), self.assertRaisesRegex(ValueError, 'thirty_minutes'):
                operator.validate_go(go, binding, now)

    def test_no_report_reason_filtering(self):
        report = dict(scanner_euid=0, clear=True, blocking_reasons=[],
                      gpu=dict(uuid=operator.UUID, index=5), device_minor=5)
        operator.validate_admission(report)
        for change in (dict(clear=False), dict(scanner_euid=2524), dict(device_minor=6),
                       dict(blocking_reasons=['process_identity_drift:123']),
                       dict(gpu=dict(uuid=operator.UUID, index=6))):
            with self.subTest(change=change), self.assertRaises(ValueError):
                operator.validate_admission(dict(report, **change))

    def test_write_once_preserves_bytes(self):
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / 'receipt.json'
            operator.write(path, dict(value=1))
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                operator.write(path, dict(value=2))
            self.assertEqual(path.read_bytes(), before)

    def test_symlink_rejected(self):
        with TemporaryDirectory() as temporary:
            target = Path(temporary) / 'original'
            target.write_text('unchanged')
            link = Path(temporary) / 'alias'
            link.symlink_to(target)
            with self.assertRaisesRegex(ValueError, 'canonical_file'):
                operator.sha(link)

    def test_failed_validation_never_dispatches(self):
        with patch.object(operator, 'validate', side_effect=ValueError('invalid_GO')), \
                patch.object(operator.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'invalid_GO'):
                operator.supervise(Path('/not-a-GO'), '0' * 64)
            run.assert_not_called()

    def test_existing_attempt_never_scans_or_retries(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary) / 'root'
            root.mkdir()
            attempt = root / 'attempt1'
            attempt.mkdir()
            with patch.object(operator, 'ROOT', root), patch.object(operator, 'ATTEMPT', attempt), \
                    patch.object(operator, 'validate', return_value=({}, {}, None, None)), \
                    patch.object(operator.subprocess, 'run') as run:
                with self.assertRaises(FileExistsError):
                    operator.supervise(Path('/not-a-GO'), '0' * 64)
                run.assert_not_called()


if __name__ == '__main__':
    unittest.main()

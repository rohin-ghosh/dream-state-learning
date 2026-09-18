import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from service_horizon import CEILING, PROTECTED, service_deadline


class ServiceHorizonTests(unittest.TestCase):
    def test_legacy_behavior_unchanged(self):
        self.assertEqual(service_deadline(None, None, 123), 123)

    def test_resident_alarm_does_not_shorten_authorized_cpu_service(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in PROTECTED:
                control = root / name / 'control'
                control.mkdir(parents=True)
                (control.parent / 'ACTIVE_RUNTIME.json').write_text(json.dumps(dict(control=str(control))))
                (control / 'PLAN.json').write_text(json.dumps(dict(hard_end_unix=100,
                    lease_end_unix=CEILING + 21600)))
                (control / 'GUARD.json').write_text(json.dumps(dict(next_reserved_unix=CEILING + 21600)))
            with patch('service_horizon.time.time', return_value=CEILING - 3600):
                self.assertEqual(service_deadline(root, CEILING, 100), CEILING)
                for value in (float('nan'), float('inf'), CEILING + 1, CEILING - 3600):
                    with self.assertRaises(ValueError):
                        service_deadline(root, value, 100)
                (control / 'GUARD.json').write_text(json.dumps(dict(next_reserved_unix=CEILING + 21599)))
                with self.assertRaisesRegex(ValueError, 'reservation_margin'):
                    service_deadline(root, CEILING, 100)


if __name__ == '__main__':
    unittest.main()

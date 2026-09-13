"""CPU-only launcher contract regression using the original mocked launcher suite."""
import importlib.util
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
SOURCE = Path(os.environ.get('ASTRA_SOURCE_ROOT', '/data/home/rohing/dream-state'))
if not SOURCE.is_absolute():
    raise ValueError('ASTRA_SOURCE_ROOT must be absolute')
SOURCE = SOURCE.resolve(strict=True)
sys.path[:0] = [str(SOURCE), '/tmp']


def load(filename, name):
    specification = importlib.util.spec_from_file_location(name, filename)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


legacy = load('/tmp/test_astra_launch_born_formation_20260912.py', 'projected_legacy_launcher_fixtures')
launcher = load('/tmp/astra_launch_projected_formation_20260913.py', 'projected_launcher_under_test')
driver = load('/tmp/astra_projected_rulegame_formation_run_20260913.py', 'projected_launcher_driver')
legacy.launcher, legacy.driver = launcher, driver


class LauncherTests(legacy.LauncherTests):
    def setUp(self):
        super().setUp()
        self.plan.update(child_mode='AUTH', interface='rulegame_action_projection_v1')

    def test_new_driver_only_and_off_contract_bound_to_plan(self):
        self.assertEqual(launcher.DRIVER, Path('/tmp/astra_projected_rulegame_formation_run_20260913.py'))
        self.plan['child_mode'] = 'OFF'
        popen = self.invoke()
        receipt = driver.read(self.root.with_name(self.root.name+'_launch')/'launch.json')
        self.assertEqual(receipt['protocol'], driver.PROTOCOL)
        self.assertEqual(receipt['plan_sha256'], self.args.plan_sha256)
        self.assertEqual(receipt['command'][2], str(launcher.DRIVER))
        self.assertEqual(receipt['driver_sha256'], self.args.driver_sha256)
        for name in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'PYTHONNOUSERSITE'):
            self.assertEqual(popen.call_args.kwargs['env'][name], '1')
        self.assertEqual(popen.call_args.kwargs['env']['ASTRA_SOURCE_ROOT'], self.plan['source_root'])

    def test_old_driver_digest_cannot_authorize_new_driver(self):
        self.args.driver_sha256 = launcher.digest('/tmp/astra_born_rulegame_formation_run_20260912.py')
        with self.assertRaisesRegex(ValueError, 'frozen driver'):
            self.invoke()
        self.free.assert_not_called()


if __name__ == '__main__':
    print('CPU-only launcher SHA256:', launcher.digest(launcher.SELF), flush=True)
    print('CPU-only driver SHA256:', launcher.digest(launcher.DRIVER), flush=True)
    unittest.main(verbosity=2)

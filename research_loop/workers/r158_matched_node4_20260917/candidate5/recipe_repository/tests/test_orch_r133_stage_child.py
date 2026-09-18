import json
from pathlib import Path
import tempfile
import time
import unittest

from gpu.orch_r133_stage_child import stage


class StageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        source = self.base/'source'
        source.mkdir()
        startup = source/'STARTUP.md'
        startup.write_text('A factual startup.')
        template = self.base/'template.json'
        template.write_text('{}')
        lease = self.base/'lease.json'
        lease.write_text(json.dumps(dict(hard_end_unix=time.time()+600, lease_end_unix=time.time()+1200)))
        cpu = self.base/'cpu.json'
        cpu.write_text(json.dumps(dict(passed=True, tests=1)))
        self.arguments = dict(template_path=template, source=source, control=self.base/'control',
            root=self.base/'run1', startup_path=startup, lease_path=lease, physical=2,
            gpu_uuid='GPU-test', builder_commit='a'*40, cpu_receipt_path=cpu)

    def test_new_plan_is_not_a_launch(self):
        result = stage(**self.arguments)
        self.assertFalse(result['launch_attempted'])
        config = json.loads(Path(result['config_path']).read_text())
        self.assertFalse(config['resume'])
        self.assertEqual(config['plan_sha256'], result['plan_sha256'])

    def test_existing_child_never_reset(self):
        self.arguments['root'].mkdir()
        with self.assertRaisesRegex(ValueError, 'new_life_only_no_reset'):
            stage(**self.arguments)

    def test_existing_control_never_overwritten(self):
        stage(**self.arguments)
        with self.assertRaises(FileExistsError):
            stage(**self.arguments)

    def test_resume_authority_not_reused(self):
        self.arguments['template_path'].write_text('{"authorized_wall_extension":{}}')
        with self.assertRaisesRegex(ValueError, 'fresh_template_without_resume_authority'):
            stage(**self.arguments)


if __name__ == '__main__':
    unittest.main()

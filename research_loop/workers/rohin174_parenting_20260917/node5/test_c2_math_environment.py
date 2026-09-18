"""Candidate command delta tests; never execute a learner request."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c2_math_environment as candidate


class MathEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.bundle = self.root / 'bundle'
        self.bundle.mkdir()
        self.package = self.bundle / 'fake_package.py'
        self.package.write_text('value=7\n')
        self.manifest = self.root / 'MATH_BUNDLE.json'
        self.manifest.write_text(json.dumps(dict(files={'fake_package.py': candidate.sha(self.package)})))
        repo = Path(__file__).resolve().parents[4]
        self.original = (repo / candidate.PROFILE).read_text()
        self.patched = candidate.profile_source(self.original, self.bundle, self.manifest, candidate.sha(self.manifest))
        self.namespace = {'__name__': 'candidate_test_profile'}
        exec(compile(self.patched, candidate.PROFILE, 'exec'), self.namespace)

    def test_only_readonly_mount_and_fixed_bootstrap_change(self):
        root = self.root / 'job'
        old = self.namespace['_r188_base_command'](root, 'orch-r125-cpu-unittest')
        new = self.namespace['command'](root, 'orch-r125-cpu-unittest')
        self.assertEqual(new[-4:-1], ['/usr/bin/python3', '-I', '-c'])
        self.assertIn("runpy.run_path('/job.py',run_name='__main__')", new[-1])
        self.assertNotIn('replace', new[-1])
        normalized = new[:-4] + old[-3:]
        position = next(position for position, value in enumerate(normalized) if value.startswith('--property=BindReadOnlyPaths='))
        normalized[position] = normalized[position].removesuffix(' ' + str(self.bundle) + ':/opt/r188-c2-math')
        self.assertEqual(normalized, old)

    def test_changed_package_rejected(self):
        self.package.write_text('changed=True\n')
        with self.assertRaisesRegex(ValueError, 'package_bytes'):
            self.namespace['command'](self.root / 'job', 'orch-r125-cpu-unittest')

    def test_extra_package_rejected(self):
        (self.bundle / 'unexpected.py').write_text('')
        with self.assertRaisesRegex(ValueError, 'bundle_inventory'):
            self.namespace['command'](self.root / 'job', 'orch-r125-cpu-unittest')

    def test_changed_manifest_rejected(self):
        self.manifest.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'bundle_manifest'):
            self.namespace['command'](self.root / 'job', 'orch-r125-cpu-unittest')

    def test_original_profile_pin_required(self):
        with self.assertRaisesRegex(ValueError, 'original_C2_profile'):
            candidate.profile_source(self.original + '\n', self.bundle, self.manifest, candidate.sha(self.manifest))

    def test_syntax_failure_payload_is_not_repaired(self):
        with self.assertRaises(SyntaxError):
            compile(candidate.SYNTAX_FAILURE, '/job.py', 'exec')


if __name__ == '__main__':
    unittest.main()

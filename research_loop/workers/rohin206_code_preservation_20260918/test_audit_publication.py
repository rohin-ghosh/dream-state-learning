"""CPU-only regressions using constructed public fixtures, never real secrets."""

import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys

from audit_publication import audit_entry, clean_public, path_omission, private_payload
from preserve_latest import digest_bytes
from verify_publication import findings


class PublicationAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.worktree = Path(self.temporary.name)
        self.relative = Path('research_loop/workers/example/receipt.json')
        self.target = self.worktree / self.relative
        self.target.parent.mkdir(parents=True)
        self.cache = {}

    def entry(self, text):
        self.target.write_text(text)
        return dict(path=str(self.relative), published_sha256=digest_bytes(text.encode()), raw_sha256='capture-hash')

    def audit(self, entry):
        return audit_entry(entry, self.worktree, [], self.cache)

    def test_safe_receipt_keeps_original_hash(self):
        entry = self.entry('{"status": "COMPLETE", "count": 4}')
        self.assertEqual(self.audit(entry), (None, False))
        self.assertEqual(entry['raw_sha256'], 'capture-hash')
        self.assertEqual(entry['published_bytes'], self.target.stat().st_size)

    def test_timeout_changed_copy_is_omitted_without_recapture(self):
        entry = self.entry('{"count": 1}')
        self.target.write_text('{"count": 2}')
        self.assertEqual(self.audit(entry)[0], 'changed_or_interrupted_derivative_manifest_only')
        self.assertEqual(self.target.read_text(), '{"count": 2}')

    def test_timeout_missing_copy_is_omitted(self):
        entry = self.entry('{}')
        self.target.unlink()
        self.assertEqual(self.audit(entry)[0], 'missing_after_interrupted_audit_manifest_only')

    def test_private_path_is_rejected_before_open(self):
        entry = dict(path='research_loop/workers/example/sealed/rows.json', published_sha256='unknown')
        self.assertEqual(self.audit(entry)[0], 'private_or_dataset_path_manifest_only')

    def test_private_flag_is_omitted(self):
        entry = self.entry(json.dumps(dict(private_do_not_export_raw=True)))
        self.assertEqual(self.audit(entry)[0], 'explicit_private_payload_classification_manifest_only')

    def test_private_nested_panel_is_omitted(self):
        entry = self.entry(json.dumps(dict(report=dict(reference_panel=['constructed fixture']))))
        self.assertEqual(self.audit(entry)[0], 'private_payload_structure_manifest_only')

    def test_cache_does_not_bypass_json_structure(self):
        text = json.dumps(dict(reference_panel=['constructed fixture']))
        original = self.relative
        self.relative = self.relative.with_suffix('.md')
        self.target = self.worktree / self.relative
        self.assertIsNone(self.audit(self.entry(text))[0])
        self.relative = original
        self.target = self.worktree / original
        self.assertEqual(self.audit(self.entry(text))[0], 'private_payload_structure_manifest_only')

    def test_ambiguous_judge_data_not_public_by_default(self):
        base = Path('research_loop/workers/example/data_judge')
        self.assertEqual(path_omission(base / 'scores.json'), 'ambiguous_judge_payload_manifest_only')
        self.assertIsNone(path_omission(base / 'PUBLIC_METADATA.json'))

    def test_symlink_not_followed(self):
        entry = self.entry('{}')
        other = self.target.with_suffix('.txt')
        self.target.rename(other)
        self.target.symlink_to(other)
        self.assertEqual(self.audit(entry)[0], 'nonregular_publication_path_manifest_only')

    def test_escape_rejected(self):
        self.assertEqual(path_omission(Path('/tmp/receipt.json')), 'unsafe_publication_path')
        self.assertEqual(path_omission(Path('research_loop/workers/../../receipt.json')), 'unsafe_publication_path')

    def test_redaction_is_hash_bound_and_idempotent(self):
        fake_address = '.'.join(['192', '0', '2', '41'])
        entry = self.entry(json.dumps(dict(host=fake_address, status='COMPLETE')))
        self.assertEqual(self.audit(entry), (None, True))
        self.assertNotIn(fake_address, self.target.read_text())
        self.assertEqual(entry['published_sha256'], digest_bytes(self.target.read_bytes()))
        self.assertEqual(clean_public(self.target.read_text(), [])[0], self.target.read_text())

    def test_additional_token_prefixes(self):
        for prefix in ['hf_', 'gho_', 'ASIA']:
            fake = prefix + 'A' * (16 if prefix == 'ASIA' else 32)
            self.assertNotIn(fake, clean_public(fake, [])[0])

    def test_long_nonemail_receipt_does_not_change(self):
        text = 'A' * 200000
        self.assertEqual(clean_public(text, [])[0], text)

    def test_invalid_json_fails_closed(self):
        self.assertEqual(self.audit(self.entry('{unfinished'))[0], 'unparseable_json_manifest_only')

    def test_hash_only_panel_metadata_is_not_payload(self):
        self.assertFalse(private_payload(dict(reference_panel_sha256='digest', count=8)))

    def test_embedded_panel_is_omitted_without_raw_output(self):
        raw = json.dumps(dict(output=json.dumps(dict(reference_panel=['constructed fixture'])))).encode()
        self.assertIn('embedded_private_payload', findings(self.relative, raw, []))

    def test_public_label_does_not_authorize_caption_rows(self):
        path = Path('research_loop/workers/example/data_judge/PUBLIC_METADATA.json')
        self.assertIn('caption_payload_not_public_aggregate', findings(path, b'{"rows": [1]}', []))

    def test_caption_source_literal_fixture_is_conservatively_omitted(self):
        path = Path('research_loop/workers/example/data_judge/example.py')
        raw = b"example = {'reference_panel': ['constructed fixture']}"
        self.assertIn('literal_caption_payload_in_source', findings(path, raw, []))

    def test_encoded_binary_is_not_published_as_text(self):
        self.assertIn('encoded_blob', findings(self.relative, json.dumps(dict(data='A' * 512)).encode(), []))

    def test_prefixed_secret_json_is_not_missed(self):
        key_name = '_'.join(['EXAMPLE', 'API', 'KEY'])
        raw = json.dumps({key_name: 'constructed-' + 'fixture'}).encode()
        self.assertIn('literal_credential_assignment', findings(self.relative, raw, []))

    def test_redacted_secret_is_not_residual_secret(self):
        raw = json.dumps({'EXAMPLE_API_KEY': '[REDACTED_SECRET]'}).encode()
        self.assertNotIn('literal_credential_assignment', findings(self.relative, raw, []))

    def test_unquoted_secret_assignment_is_not_missed(self):
        raw = ('EXAMPLE_API_KEY=' + 'A' * 32).encode()
        self.assertIn('unquoted_credential_assignment', findings(self.relative, raw, []))

    def test_url_password_is_detected_even_at_end(self):
        raw = ('https' + '://' + 'fixture:constructed' + '@localhost').encode()
        self.assertIn('url_user_password', findings(self.relative, raw, []))

    def run_fixture_audit(self, report):
        publication = self.worktree / 'research_loop/workers/rohin206_code_preservation_20260918'
        publication.mkdir(parents=True, exist_ok=True)
        (publication / 'PRESERVATION_RECEIPT.json').write_text(json.dumps(report))
        command = [sys.executable, '-B', str(Path(__file__).with_name('audit_publication.py')),
                   '--root', str(self.worktree), '--worktree', str(self.worktree)]
        return subprocess.run(command, capture_output=True, text=True, timeout=20), publication

    def test_incomplete_capture_cannot_be_audited(self):
        result, publication = self.run_fixture_audit({})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('worker_snapshot_not_complete', result.stderr)
        self.assertFalse((publication / 'PUBLICATION_ALLOWLIST.json').exists())

    def test_completed_audit_never_allowlists_interrupted_orphan(self):
        entry = self.entry('{"count": 1}')
        self.target.write_text('{"count": 2}')
        manifest = self.target.parent / 'PRESERVATION_MANIFEST_20260918.jsonl'
        manifest.write_text(json.dumps(entry) + '\n')
        (self.worktree / 'research_loop/COORDINATION.md').write_text('Public fixture only.\n')
        report = dict(complete_utc='2026-09-18T06:09:35+00:00', coordinate={},
                      directories=[dict(directory='example')])
        result, publication = self.run_fixture_audit(report)
        self.assertEqual(result.returncode, 0, result.stderr)
        allowlist = json.loads((publication / 'PUBLICATION_ALLOWLIST.json').read_text())
        receipt = json.loads((publication / 'PRESERVATION_RECEIPT.json').read_text())
        self.assertEqual(allowlist['files'], {})
        self.assertTrue(receipt['publication_safety_audit'])
        self.assertEqual(self.target.read_text(), '{"count": 2}')

    def test_second_screen_prunes_encoded_orphan_and_binds_coordination(self):
        safe_entry = self.entry('{"count": 1}')
        self.relative = self.relative.with_name('encoded.json')
        self.target = self.worktree / self.relative
        encoded_entry = self.entry(json.dumps(dict(data='A' * 512)))
        manifest = self.target.parent / 'PRESERVATION_MANIFEST_20260918.jsonl'
        manifest.write_text(''.join(json.dumps(entry) + '\n' for entry in [safe_entry, encoded_entry]))
        (self.worktree / 'research_loop/COORDINATION.md').write_text('Public fixture only.\n')
        report = dict(complete_utc='2026-09-18T06:09:35+00:00', coordinate={},
                      directories=[dict(directory='example')])
        first, publication = self.run_fixture_audit(report)
        self.assertEqual(first.returncode, 0, first.stderr)
        for name in ['audit_publication.py', 'preserve_latest.py', 'audit_snapshot.py',
                     'verify_publication.py', 'test_audit_publication.py']:
            (publication / name).write_bytes(Path(__file__).with_name(name).read_bytes())
        second = subprocess.run([sys.executable, '-B', str(publication / 'verify_publication.py'),
            '--root', str(self.worktree), '--worktree', str(self.worktree), '--prune'],
            capture_output=True, text=True, timeout=20)
        self.assertEqual(second.returncode, 0, second.stderr)
        allowlist = json.loads((publication / 'PUBLICATION_ALLOWLIST.json').read_text())
        self.assertEqual(set(allowlist['files']), {safe_entry['path']})
        self.assertEqual((self.worktree / allowlist['coordinate_path']).read_text(), 'Public fixture only.\n')
        self.assertTrue(self.target.exists())
        screened = [json.loads(line) for line in manifest.read_text().splitlines()]
        self.assertNotIn('published_sha256', screened[1])


if __name__ == '__main__':
    unittest.main()

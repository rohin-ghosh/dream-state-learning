"""Version 2 test-only repair: deterministic mutation fixtures; original verifier unchanged."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

MODULE_PATH = Path('/tmp/astra_q0_tar_custody_20260913.py')
spec = importlib.util.spec_from_file_location('q0_tar_custody', MODULE_PATH)
custody = importlib.util.module_from_spec(spec)
spec.loader.exec_module(custody)


def encoded(value):
    return (json.dumps(value, sort_keys=True) + '\n').encode()


class CustodyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='q0_tar_custody_cpu_', dir='/tmp')
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.archive = self.directory / 'fixture.tar'
        self.seal_path = self.directory / 'seal.json'
        self.payloads = {'data/file.txt': b'bounded payload\n', 'FAILED.json': encoded({'preserve_partial': True})}
        self.reseal()

    def reseal(self):
        self.seal_bytes = encoded({'files': {name: custody.sha256(data) for name, data in self.payloads.items()}})
        self.finalized = encoded({'seal_sha256': custody.sha256(self.seal_bytes)})
        self.seal_path.write_bytes(self.seal_bytes)

    def entries(self):
        return [('root/' + name, data, tarfile.REGTYPE) for name, data in self.payloads.items()] + [('root/SEAL.json', self.seal_bytes, tarfile.REGTYPE), ('root/FINALIZED.json', self.finalized, tarfile.REGTYPE)]

    def build(self, entries=None, format=tarfile.GNU_FORMAT, root=True):
        with tarfile.open(self.archive, 'w', format=format) as archive:
            if root:
                member = tarfile.TarInfo('root/')
                member.type = tarfile.DIRTYPE
                archive.addfile(member)
            for name, data, kind in self.entries() if entries is None else entries:
                member = tarfile.TarInfo(name)
                member.type = kind
                member.size = len(data)
                if kind in (tarfile.LNKTYPE, tarfile.SYMTYPE):
                    member.linkname = '/outside/target'
                archive.addfile(member, io.BytesIO(data))
        return self.archive

    def verify(self, **overrides):
        arguments = dict(archive=self.archive, expected_archive_sha256=custody.sha256(self.archive.read_bytes()), seal=self.seal_path)
        arguments.update(overrides)
        return custody.verify_archive(**arguments)

    def reject(self, fragment, entries=None, **overrides):
        self.build(entries)
        report = self.verify(**overrides)
        self.assertEqual(report['status'], 'FAIL_CUSTODY')
        self.assertIn(fragment, ' '.join(error['message'] for error in report['errors']))
        return report

    def test_valid_custody_including_failed_run_does_not_reclassify(self):
        self.build()
        before = (self.archive.read_bytes(), self.seal_path.read_bytes())
        report = self.verify()
        self.assertEqual(report['status'], 'PASS_CUSTODY', report['errors'])
        self.assertEqual(report['counts']['regular_files'], 4)
        self.assertEqual(report['counts']['sealed_files_verified'], 2)
        self.assertTrue(report['inputs_unchanged'])
        self.assertFalse(report['promotion_or_reclassification'])
        self.assertEqual(before, (self.archive.read_bytes(), self.seal_path.read_bytes()))

    def test_full_root_matches_exact_gnu_find_sort_checksum_pipeline(self):
        self.payloads.update({'space name': b'space', "quote'\"name": b'quote', 'UpperCase': b'upper', '-leading': b'leading'})
        self.reseal()
        self.build()
        fixture = self.directory / 'full-root'
        fixture.mkdir()
        full = dict(self.payloads, **{'SEAL.json': self.seal_bytes, 'FINALIZED.json': self.finalized})
        for name, data in full.items():
            path = fixture / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        result = subprocess.run(['bash', '-o', 'pipefail', '-c', 'find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum'], cwd=fixture, env=dict(os.environ, LC_ALL='C'), capture_output=True, text=True, check=True)
        expected = result.stdout.split()[0]
        report = self.verify(expected_root_stream_sha256=expected)
        self.assertEqual(report['status'], 'PASS_CUSTODY', report['errors'])
        self.assertTrue(report['full_root_stream_matches_expected'])

    def test_wrong_full_root_digest_rejected(self):
        self.reject('full-root stream expected', expected_root_stream_sha256='0' * 64)

    def test_finalized_bytes_change_full_root_digest_even_with_same_seal(self):
        self.build()
        original = self.verify()['full_root_stream_sha256']
        self.finalized = encoded({'seal_sha256': custody.sha256(self.seal_bytes), 'witness': 'changed publication'})
        self.reject('full-root stream expected', expected_root_stream_sha256=original)

    def test_valid_optional_abort_included_in_full_root(self):
        abort = encoded({'seal_sha256': custody.sha256(self.seal_bytes), 'finalized_sha256': custody.sha256(self.finalized)})
        self.build(self.entries() + [('root/FINALIZATION_ABORT.json', abort, tarfile.REGTYPE)])
        report = self.verify()
        self.assertEqual(report['status'], 'PASS_CUSTODY', report['errors'])
        self.assertEqual(report['full_root_regular_files'], 5)

    def test_bad_abort_seal_binding_rejected(self):
        self.reject('FINALIZATION_ABORT seal binding', self.entries() + [('root/FINALIZATION_ABORT.json', encoded({'seal_sha256': '0' * 64}), tarfile.REGTYPE)])

    def test_bad_abort_finalized_binding_rejected(self):
        self.reject('FINALIZATION_ABORT finalized binding', self.entries() + [('root/FINALIZATION_ABORT.json', encoded({'seal_sha256': custody.sha256(self.seal_bytes), 'finalized_sha256': '0' * 64}), tarfile.REGTYPE)])

    def test_archive_expected_hash_mismatch_rejected(self):
        self.reject('archive expected SHA256', expected_archive_sha256='0' * 64)

    def test_standalone_expected_hash_mismatch_rejected(self):
        self.reject('standalone seal expected', expected_seal_sha256='0' * 64)

    def test_sealed_payload_hash_mismatch_rejected(self):
        entries = self.entries()
        entries[0] = (entries[0][0], b'changed', tarfile.REGTYPE)
        self.reject('sealed payload hash mismatch', entries)

    def test_missing_sealed_file_rejected(self):
        self.reject('missing sealed files', self.entries()[1:])

    def test_additional_regular_file_rejected(self):
        self.reject('additional unsealed', self.entries() + [('root/extra', b'extra', tarfile.REGTYPE)])

    def test_missing_seal_rejected(self):
        self.reject('missing archive SEAL', [entry for entry in self.entries() if entry[0] != 'root/SEAL.json'])

    def test_missing_finalized_rejected(self):
        self.reject('missing archive FINALIZED', [entry for entry in self.entries() if entry[0] != 'root/FINALIZED.json'])

    def test_finalized_wrong_seal_binding_rejected(self):
        self.finalized = encoded({'seal_sha256': '0' * 64})
        self.reject('FINALIZED does not bind')

    def test_finalized_nonobject_rejected(self):
        self.finalized = b'[]\n'
        self.reject('FINALIZED does not bind')

    def test_seal_exact_bytes_not_just_json_equivalence(self):
        entries = self.entries()
        index = next(index for index, entry in enumerate(entries) if entry[0] == 'root/SEAL.json')
        entries[index] = ('root/SEAL.json', self.seal_bytes[:-1] + b' ', tarfile.REGTYPE)
        self.reject('archive seal exact bytes differ', entries)

    def test_duplicate_regular_member_rejected(self):
        self.reject('duplicate archive member', self.entries() + [self.entries()[0]])

    def test_duplicate_directory_rejected(self):
        self.reject('duplicate archive member', [('root/', b'', tarfile.DIRTYPE)] + self.entries())

    def test_second_top_directory_rejected(self):
        self.reject('multiple top-level', [('other/', b'', tarfile.DIRTYPE)] + self.entries())

    def test_regular_file_outside_top_directory_rejected(self):
        self.build([('root', b'content', tarfile.REGTYPE)], root=False)
        self.assertIn('outside the single', self.verify()['errors'][0]['message'])

    def test_unsafe_paths_rejected(self):
        for name in ('/absolute', 'root/../escape', 'root/./alias', 'root//alias', 'root/back\\slash', 'root/line\nbreak', 'root/carriage\rreturn', 'root/nonasciié', 'C:/drive', 'root/trailing/'):
            with self.subTest(name=name):
                self.build([(name, b'bad', tarfile.REGTYPE)] + self.entries())
                self.assertEqual(self.verify()['status'], 'FAIL_CUSTODY')

    def test_links_and_special_types_rejected(self):
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE, tarfile.CHRTYPE, tarfile.BLKTYPE, tarfile.GNUTYPE_SPARSE, tarfile.CONTTYPE, tarfile.GNUTYPE_LONGLINK, tarfile.XGLTYPE):
            with self.subTest(kind=kind):
                self.build([('root/special', b'', kind)] + self.entries())
                self.assertEqual(self.verify()['status'], 'FAIL_CUSTODY')

    def test_regular_parent_conflict_rejected(self):
        self.payloads = {'parent': b'parent', 'parent/child': b'child'}
        self.reseal()
        self.reject('regular file used as directory')

    def test_late_regular_parent_conflict_rejected(self):
        self.payloads = {'parent/child': b'child', 'parent': b'parent'}
        self.reseal()
        self.reject('regular file conflicts')

    def test_directory_payload_rejected(self):
        self.reject('directory member has payload', [('root/dir/', b'bad', tarfile.DIRTYPE)] + self.entries())

    def test_duplicate_seal_json_keys_rejected(self):
        self.seal_path.write_bytes(b'{"files":{},"files":{}}')
        self.reject('duplicate JSON key')

    def test_duplicate_mapping_json_keys_rejected(self):
        self.seal_path.write_bytes(b'{"files":{"x":"' + b'0' * 64 + b'","x":"' + b'0' * 64 + b'"}}')
        self.reject('duplicate JSON key')

    def test_malformed_digest_and_manifest_paths_rejected(self):
        for files in ({'x': True}, {'x': 'A' * 64}, {'../x': '0' * 64}, {'x\\y': '0' * 64}, {'x': 'short'}):
            with self.subTest(files=files):
                self.seal_path.write_bytes(encoded({'files': files}))
                self.build()
                self.assertEqual(self.verify()['status'], 'FAIL_CUSTODY')

    def test_nonfinite_json_rejected(self):
        self.seal_path.write_bytes(b'{"files":{},"unexpected":NaN}')
        self.reject('nonfinite JSON')

    def test_gnu_long_names_supported(self):
        self.payloads['nested/' + 'long' * 40] = b'long name'
        self.reseal()
        self.build()
        report = self.verify()
        self.assertEqual(report['status'], 'PASS_CUSTODY', report['errors'])
        self.assertGreater(report['counts']['gnu_longname_headers'], 0)

    def test_pax_long_names_supported(self):
        self.payloads['nested/' + 'long' * 40] = b'long name'
        self.reseal()
        self.build(format=tarfile.PAX_FORMAT)
        report = self.verify()
        self.assertEqual(report['status'], 'PASS_CUSTODY', report['errors'])
        self.assertGreater(report['counts']['pax_headers'], 0)

    def test_ustar_prefix_supported(self):
        self.payloads['prefix' * 15 + '/file'] = b'ustar'
        self.reseal()
        self.build(format=tarfile.USTAR_FORMAT)
        self.assertEqual(self.verify()['status'], 'PASS_CUSTODY')

    def test_local_pax_size_override_rejected(self):
        with tarfile.open(self.archive, 'w', format=tarfile.PAX_FORMAT) as archive:
            member = tarfile.TarInfo('root/file')
            member.pax_headers = {'size': '1'}
            member.size = 1
            archive.addfile(member, io.BytesIO(b'x'))
        self.assertIn('unsupported/duplicate PAX key', self.verify()['errors'][0]['message'])

    def test_bad_header_checksum_rejected(self):
        self.build()
        data = bytearray(self.archive.read_bytes())
        data[0] ^= 1
        self.archive.write_bytes(data)
        self.assertEqual(self.verify()['status'], 'FAIL_CUSTODY')

    def test_truncated_payload_rejected(self):
        self.build()
        self.archive.write_bytes(self.archive.read_bytes()[:1025])
        self.assertEqual(self.verify()['status'], 'FAIL_CUSTODY')

    def test_missing_end_blocks_rejected(self):
        self.build()
        data = self.archive.read_bytes()
        self.archive.write_bytes(data.rstrip(b'\0'))
        self.assertEqual(self.verify()['status'], 'FAIL_CUSTODY')

    def test_hidden_trailing_tar_or_nonzero_data_rejected(self):
        self.build()
        original = self.archive.read_bytes()
        for suffix in (b'x' * 512, original):
            with self.subTest(suffix_size=len(suffix)):
                self.archive.write_bytes(original + suffix)
                self.assertIn('nonzero trailing', self.verify()['errors'][0]['message'])

    def test_unaligned_zero_trailer_rejected(self):
        self.build()
        self.archive.write_bytes(self.archive.read_bytes() + b'\0')
        self.assertIn('unaligned', self.verify()['errors'][0]['message'])

    def test_bounded_reads_and_no_extraction_api(self):
        self.payloads['large'] = b'x' * (custody.CHUNK * 3 + 10)
        self.reseal()
        self.build()
        with patch.object(tarfile.TarFile, 'extract', side_effect=AssertionError('extraction forbidden')), patch.object(tarfile.TarFile, 'extractall', side_effect=AssertionError('extraction forbidden')):
            self.assertEqual(self.verify()['status'], 'PASS_CUSTODY')

    def test_inputs_cannot_be_symlinks(self):
        self.build()
        alias = self.directory / 'alias.tar'
        alias.symlink_to(self.archive)
        self.assertEqual(self.verify(archive=alias)['status'], 'FAIL_CUSTODY')

    def test_input_change_detection(self):
        self.build()
        original = custody.scan_tar
        def changed(reader, expected, seal_bytes, report):
            original(reader, expected, seal_bytes, report)
            before = self.archive.stat()
            os.utime(self.archive, ns=(before.st_atime_ns, before.st_mtime_ns + 2000000000))
            self.assertNotEqual(self.archive.stat().st_mtime_ns, before.st_mtime_ns)
        with patch.object(custody, 'scan_tar', side_effect=changed):
            report = self.verify()
        self.assertEqual(report['status'], 'FAIL_CUSTODY')
        self.assertFalse(report['inputs_unchanged'])
        self.assertIn('input changed/replaced', report['errors'][0]['message'])

    def test_archive_append_after_scan_detected(self):
        self.build()
        original = custody.scan_tar
        def changed(reader, expected, seal_bytes, report):
            original(reader, expected, seal_bytes, report)
            before = self.archive.stat().st_size
            with self.archive.open('ab') as stream:
                stream.write(b'changed')
            self.assertGreater(self.archive.stat().st_size, before)
        with patch.object(custody, 'scan_tar', side_effect=changed):
            report = self.verify()
        self.assertEqual(report['status'], 'FAIL_CUSTODY')
        self.assertFalse(report['inputs_unchanged'])

    def test_archive_inode_replacement_same_bytes_detected(self):
        self.build()
        original = custody.scan_tar
        def changed(reader, expected, seal_bytes, report):
            original(reader, expected, seal_bytes, report)
            before = self.archive.stat()
            replacement = self.directory / 'replacement.tar'
            replacement.write_bytes(self.archive.read_bytes())
            os.utime(replacement, ns=(before.st_atime_ns, before.st_mtime_ns))
            os.replace(replacement, self.archive)
            self.assertNotEqual(self.archive.stat().st_ino, before.st_ino)
        with patch.object(custody, 'scan_tar', side_effect=changed):
            report = self.verify()
        self.assertEqual(report['status'], 'FAIL_CUSTODY')
        self.assertFalse(report['inputs_unchanged'])

    def test_noop_after_scan_does_not_fabricate_mutation(self):
        self.build()
        original = custody.scan_tar
        def unchanged(reader, expected, seal_bytes, report):
            original(reader, expected, seal_bytes, report)
            self.assertEqual(custody.fingerprint(self.archive.stat()), report['input_before']['archive'])
        with patch.object(custody, 'scan_tar', side_effect=unchanged):
            report = self.verify()
        self.assertEqual(report['status'], 'PASS_CUSTODY', report['errors'])
        self.assertTrue(report['inputs_unchanged'])

    def test_seal_append_after_scan_detected(self):
        self.build()
        original = custody.scan_tar
        def changed(reader, expected, seal_bytes, report):
            original(reader, expected, seal_bytes, report)
            before = self.seal_path.stat().st_size
            with self.seal_path.open('ab') as stream:
                stream.write(b' ')
            self.assertGreater(self.seal_path.stat().st_size, before)
        with patch.object(custody, 'scan_tar', side_effect=changed):
            report = self.verify()
        self.assertEqual(report['status'], 'FAIL_CUSTODY')
        self.assertFalse(report['inputs_unchanged'])

    def test_same_size_payload_change_restored_mtime_rejected(self):
        self.build()
        original = self.archive.read_bytes()
        details = self.archive.stat()
        changed = original.replace(b'bounded payload', b'changed payload', 1)
        self.assertNotEqual(original, changed)
        self.assertEqual(len(original), len(changed))
        self.archive.write_bytes(changed)
        os.utime(self.archive, ns=(details.st_atime_ns, details.st_mtime_ns))
        report = self.verify(expected_archive_sha256=custody.sha256(original))
        self.assertEqual(report['status'], 'FAIL_CUSTODY')
        self.assertIn('sealed payload hash mismatch', report['errors'][0]['message'])

    def test_cli_writes_exclusive_new_receipt_and_preserves_it(self):
        self.build()
        output = self.directory / 'receipt.json'
        arguments = [sys.executable, '-B', str(MODULE_PATH), '--archive', str(self.archive), '--archive-sha256', custody.sha256(self.archive.read_bytes()), '--seal', str(self.seal_path), '--out', str(output)]
        result = subprocess.run(arguments, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        original = output.read_bytes()
        result = subprocess.run(arguments, capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_bytes(), original)

    def test_cli_cannot_overwrite_input(self):
        self.build()
        original = self.archive.read_bytes()
        result = subprocess.run([sys.executable, '-B', str(MODULE_PATH), '--archive', str(self.archive), '--archive-sha256', custody.sha256(original), '--seal', str(self.seal_path), '--out', str(self.archive)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.archive.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()

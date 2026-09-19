"""Offline deployed-contract probes; no network, judge, native, or live writes."""

import ast
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from gpu.ny_caption_life import child_act, latest_own_think
from gpu.ny_caption_life_service import LifeSession
from gpu.orch_r125_stream_journal import _digest
from research_loop.workers.post_reboot_node3_parents_20260919.test_bounded_failure import actual_chain
from research_loop.workers.rohin221_continuous_caption_20260918 import journal_bundle, journal_transport
from research_loop.workers.rohin221_continuous_caption_20260918.generation_origin import validate_generation_origin
from research_loop.workers.rohin221_continuous_caption_20260918.shared_scorer import Hub


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def envelope_record(record):
    raw = json.dumps(record).encode()
    return dict(index=record['index'], file_sha256=hashlib.sha256(raw).hexdigest(),
        raw=base64.b64encode(raw).decode('ascii'))


def source_callback(request, raw, *, identifier, think_resolver):
    return dict(request=request, raw_act=raw, identifier=identifier, think=think_resolver())


class ProjectionContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root/'original'
        self.mirror = self.root/'mirror'
        self.origin = actual_chain(self.source)
        self.records = journal_bundle.export_records(self.source, self.origin, 'journal')
        self.request = dict(origin=self.origin, metrics=dict(THINK=1, ACT=1, LEARN=0))
        self.session = LifeSession.__new__(LifeSession)
        self.session.life_root = self.mirror
        self.session.process_verified = Mock(side_effect=source_callback)
        self.hub = Hub.__new__(Hub)
        self.hub.registry = dict(fork=dict(journal=dict(journal_id='journal'), life_root=str(self.source)))
        self.hub.sessions = dict(fork=self.session)

    def native(self, records):
        return self.hub.native(dict(session_id='fork', request=self.request, records=records))

    def assert_source_parity(self, result):
        self.assertEqual(result['request'], self.request)
        self.assertEqual(result['identifier'], self.origin['record_sha256'])
        self.assertEqual(result['raw_act'], child_act(self.source, self.origin))
        self.assertEqual(result['think'], latest_own_think(self.source, self.origin))
        self.assertEqual(result['think']['stage'], 'THINK')
        self.assertEqual(result['think']['origin']['record_index'], 0)
        self.assertNotIn('receipt_sha256', result)

    def test_contracts_are_pinned_to_deployed_sources(self):
        evidence = json.loads((HERE/'DEPLOYED_PROJECTION_CONTRACT.json').read_bytes())
        for relative, expected in evidence['files'].items():
            if expected['local_full_source_matches']:
                with self.subTest(source=relative):
                    self.assertTrue(expected['manifest_pinned'])
                    self.assertEqual(hashlib.sha256((REPO/relative).read_bytes()).hexdigest(), expected['sha256'])
        relative = 'gpu/ny_caption_life.py'
        definitions = {node.name:node for node in ast.walk(ast.parse((REPO/relative).read_text()))
            if isinstance(node, ast.FunctionDef)}
        for name, expected in evidence['files'][relative]['definitions'].items():
            with self.subTest(definition=name):
                digest = hashlib.sha256(ast.dump(definitions[name], include_attributes=False).encode()).hexdigest()
                self.assertTrue(expected['local_ast_matches'])
                self.assertEqual(digest, expected['ast_sha256'])

    def test_full_originals_preserve_exact_ACT_THINK_callback_inputs(self):
        result = self.native(self.records)
        self.assert_source_parity(result)
        self.session.process_verified.assert_called_once()

    def test_existing_short_envelope_requires_preimported_full_originals(self):
        journal_bundle.import_records(self.mirror, self.records[:-1], 'journal')
        result = self.native(self.records[-1:])
        self.assert_source_parity(result)
        for record in self.records:
            original = self.source/'stream/records'/f"{record['index']:020d}.json"
            mirrored = self.mirror/'stream/records'/original.name
            self.assertEqual(original.read_bytes(), mirrored.read_bytes())

    def test_short_envelope_cannot_replace_missing_original_ancestry(self):
        with self.assertRaisesRegex(ValueError, 'bounded_regular_journal_record'):
            self.native(self.records[-1:])
        self.session.process_verified.assert_not_called()

    def test_projection_endpoint_not_in_native_wire_schema(self):
        projection = dict(raw_act=child_act(self.source, self.origin),
            think=latest_own_think(self.source, self.origin),
            record_hashes=[record['file_sha256'] for record in self.records])
        for envelope in (
            dict(session_id='fork', request=self.request, projection=projection),
            dict(session_id='fork', request=self.request, records=self.records, projection=projection),
        ):
            with self.subTest(keys=sorted(envelope)):
                with self.assertRaisesRegex(ValueError, 'trusted_proxy_envelope_only'):
                    self.hub.native(envelope)
        self.session.process_verified.assert_not_called()

    def test_projection_cannot_be_hidden_in_request_or_record(self):
        request = dict(self.request, raw_act='projected')
        with self.assertRaisesRegex(ValueError, 'native_request_schema'):
            self.hub.native(dict(session_id='fork', request=request, records=self.records))
        record = dict(self.records[0], origin=self.origin)
        with self.assertRaisesRegex(ValueError, 'exact_record_envelope'):
            self.native([record])
        self.session.process_verified.assert_not_called()

    def test_file_byte_tamper_is_rejected_before_callback(self):
        records = deepcopy(self.records)
        records[0]['raw'] = base64.b64encode(base64.b64decode(records[0]['raw'])+b' ').decode()
        with self.assertRaisesRegex(ValueError, 'exact_transferred_record_bytes'):
            self.native(records)
        self.session.process_verified.assert_not_called()

    def test_stripped_checkpoints_cannot_retain_original_record_hash(self):
        for index in (1, 3, 4, 6):
            with self.subTest(index=index):
                records = deepcopy(self.records)
                record = json.loads(base64.b64decode(records[index]['raw']))
                del record['document']['state']
                records[index] = envelope_record(record)
                with self.assertRaisesRegex(ValueError, 'same_bound_journal_and_record_hash'):
                    self.native(records)
        self.session.process_verified.assert_not_called()

    def test_rehashed_checkpoint_breaks_original_descendant_chain(self):
        records = deepcopy(self.records)
        record = json.loads(base64.b64decode(records[4]['raw']))
        del record['document']['state']
        record['sha256'] = _digest({key:value for key,value in record.items() if key != 'sha256'})
        records[4] = envelope_record(record)
        with self.assertRaisesRegex(ValueError, 'contiguous_actual_records'):
            self.native(records)
        self.session.process_verified.assert_not_called()

    def test_rehashing_entire_projection_invalidates_original_ACT_origin(self):
        records, previous = [], 'seed'
        for item in self.records:
            record = json.loads(base64.b64decode(item['raw']))
            record['document'].pop('state', None)
            record['previous_sha256'] = previous
            record['sha256'] = _digest({key:value for key,value in record.items() if key != 'sha256'})
            records.append(envelope_record(record))
            previous = record['sha256']
        with self.assertRaisesRegex(ValueError, 'same_child_RESPONSE'):
            self.native(records)
        self.session.process_verified.assert_not_called()

    def test_skipping_intermediate_checkpoint_fails_contiguity(self):
        with self.assertRaisesRegex(ValueError, 'contiguous_actual_records'):
            self.native(self.records[:4]+self.records[5:])
        self.session.process_verified.assert_not_called()

    def test_existing_mirror_cannot_be_rewritten_with_projected_record(self):
        journal_bundle.import_records(self.mirror, self.records, 'journal')
        record = json.loads(base64.b64decode(self.records[4]['raw']))
        del record['document']['state']
        record['sha256'] = _digest({key:value for key,value in record.items() if key != 'sha256'})
        with self.assertRaisesRegex(ValueError, 'no_mirror_rewrite'):
            journal_bundle.import_records(self.mirror, [envelope_record(record)], 'journal')

    def test_native_origin_cannot_be_relabelled_as_standalone_generation(self):
        with self.assertRaisesRegex(ValueError, 'standalone_origin_schema'):
            validate_generation_origin(self.origin, receipt_root=self.source,
                expected_binding={}, expected_backend_state={})

    def test_aggregate_export_guard_remains_64MiB(self):
        self.assertEqual(journal_transport.MAX_TOTAL_BYTES, 67108864)
        self.assertEqual(journal_transport.MAX_ENVELOPE_BYTES, 100663296)


if __name__ == '__main__':
    unittest.main()

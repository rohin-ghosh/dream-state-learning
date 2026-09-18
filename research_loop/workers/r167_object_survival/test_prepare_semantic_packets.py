import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research_loop.workers.r167_object_survival import prepare_semantic_packets as packets


protocol = packets.protocol


class PacketTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'ledger').mkdir()
        self.context = dict(system_prompt='Help.', birth_prompt='Begin.')
        fingerprint = dict(context=self.context, definitions={'8': dict(record_index=100,
            object=dict(anchors=[['test']], training_grams=[['example']]),
            behavior=dict(anchors=[['observe']], training_grams=[['example']]))})
        fingerprint_ref = protocol.write(self.root / 'FINGERPRINTS.private.json', fingerprint)
        freeze = protocol.write(self.root / 'FREEZE.json', dict(fingerprints=fingerprint_ref))
        self.plan = dict(freeze=freeze, slots=['8_LORA_ON', '8_LORA_OFF'])
        self.plan_path = self.root / 'PLAN.json'
        protocol.write(self.plan_path, self.plan)
        self.rubric = protocol.write(self.root / 'RUBRIC.md', b'Frozen private semantic methods.')
        for key in self.plan['slots']:
            directory = self.root / 'attempts' / key / 'sealed'
            directory.mkdir(parents=True)
            reservation = protocol.write(self.root / 'ledger' / (key + '.RESERVED.json'),
                                         dict(execution=dict(sha256='fixed')))
            protocol.write(self.root / 'ledger' / (key + '.COMPLETE.json'), dict(reservation=reservation))
            receipts = {}
            for position in range(3):
                path = directory / f'{position}.RAW.private.json'
                receipts[path.name] = protocol.write(path, dict(messages=protocol.messages(self.context, protocol.PROBES[position]),
                    raw='PRIVATE SYNTHETIC ANSWER', truncated=True, terminal=False))['sha256']
            protocol.write(directory / 'COMPLETE.json', dict(execution_sha256='fixed', receipts=receipts))
        self.addCleanup(patch.stopall)
        patch.object(protocol, 'CAMPAIGN', self.root).start()
        patch.object(protocol, 'make_plan', return_value=self.plan).start()

    def test_opaque_packets_exclude_condition_checkpoint_flags_and_mapping(self):
        output = self.root / 'private_appendices/new'
        result = packets.prepare(self.plan_path, output, self.rubric)
        self.assertEqual((result['blind_packets'], result['completed_outputs'], result['provider_calls']), (6, 6, 0))
        self.assertNotIn('PRIVATE SYNTHETIC ANSWER', json.dumps(result))
        for path in (output / 'packets').glob('*.json'):
            packet = protocol.read(path)
            for forbidden in ('LORA_ON', 'LORA_OFF', 'record_index', 'comparison_sleep', 'lexical', str(self.root)):
                self.assertNotIn(forbidden, json.dumps(packet))
            self.assertEqual(packet['response'], 'PRIVATE SYNTHETIC ANSWER')
        self.assertTrue((output / 'unblinding/MAP.private.json').is_file())

    def test_uncompleted_output_is_not_adjudication_or_negative(self):
        (self.root / 'ledger/8_LORA_OFF.COMPLETE.json').unlink()
        result = packets.prepare(self.plan_path, self.root / 'private_appendices/partial', self.rubric)
        self.assertEqual(result['completed_outputs'], 3)
        self.assertEqual(result['status'], 'PRIVATE_BLIND_PACKETS_READY_NOT_ADJUDICATED')

    def test_changed_raw_refuses_without_returning_content(self):
        (self.root / 'attempts/8_LORA_ON/sealed/0.RAW.private.json').write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError, 'immutable_completed_raw'):
            packets.prepare(self.plan_path, self.root / 'private_appendices/failure', self.rubric)

    def test_changed_rubric_or_existing_output_cannot_refreeze(self):
        output = self.root / 'private_appendices/new'
        packets.prepare(self.plan_path, output, self.rubric)
        with self.assertRaises(ValueError):
            packets.prepare(self.plan_path, output, self.rubric)
        Path(self.rubric['path']).write_bytes(b'changed')
        with self.assertRaises(ValueError):
            packets.prepare(self.plan_path, self.root / 'private_appendices/new2', self.rubric)


if __name__ == '__main__':
    unittest.main()

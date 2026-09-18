import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import enrich


class EnrichmentTests(unittest.TestCase):
    def test_response_joins_request_document_not_journal_envelope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'math_d1').mkdir()
            publication = dict(number=1, publication={'id': 'synthetic'}, floor=0, text='Synthetic parent.')
            (root / 'math_d1/PARENT_1.json').write_text(json.dumps(publication))
            document = dict(messages=[dict(role='user', content='Astra: Synthetic parent.')],
                            started_unix=1, segment=5, render_receipt={'all_history_tokens_masked': True})
            request = dict(index=1, kind='REQUEST', document=dict(document, resume_state={'synthetic': True}))
            request['sha256'] = enrich.digest(request)
            response = dict(index=2, kind='RESPONSE', previous_sha256=request['sha256'], document=dict(request_sha256=enrich.digest(document),
                finished_unix=2, response={'raw': 'Actual synthetic reply.'}))
            response['sha256'] = enrich.digest(response)
            paths = []
            for record in (request, response):
                path = root / (str(record['index']) + '.json')
                path.write_text(json.dumps(record))
                paths.append((path, record))
            with patch.object(enrich, 'HERE', root), patch.object(enrich, 'identity', return_value=({'native': {}}, root)), patch.object(enrich, 'recent', return_value=paths):
                result = enrich.verify('math_d1')['publications'][0]
            self.assertEqual(result['responses'][0]['raw'], 'Actual synthetic reply.')
            self.assertTrue(result['all_history_tokens_masked'])

    def test_peer_capsule_is_attributed_without_metadata_markers(self):
        import peer_once
        from organism_v6.orch_r125_plain_context import has_scaffolding
        record = dict(kind='R184_LEARN_COMPLETE', document=dict(cycle=64,
            working_state=dict(revision=3, entries=[dict(kind='uncertainty', text='Synthetic question.')])))
        for arm in enrich.ARMS:
            text = peer_once.capsule(arm, record)
            self.assertIn('Synthetic question.', text)
            self.assertIn(arm, text)
            self.assertIn('not an unparented comparison', text)
            self.assertFalse(has_scaffolding('Tool: ' + text))
        with self.assertRaises(ValueError):
            peer_once.capsule('original_C2', record)

    def test_four_bounded_object_openers(self):
        from organism_v6.orch_r125_plain_context import has_scaffolding
        for arm in enrich.ARMS:
            text = enrich.first_text(arm)
            self.assertIn('at most two', text)
            self.assertIn('84*(26 + 3*V)/30', text)
            self.assertIn(enrich.OBJECTS[arm], text)
            self.assertFalse(has_scaffolding('Astra: ' + text))

    def test_verified_record_rejects_modified_content(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'record.json'
            record = dict(index=10, kind='RESPONSE', document=dict(response=dict(raw='Synthetic.')))
            record['sha256'] = enrich.digest(record)
            path.write_text(json.dumps(record))
            self.assertEqual(enrich.verified(path), record)
            record['document']['response']['raw'] = 'Changed.'
            path.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, 'record_hash_mismatch'):
                enrich.verified(path)

    def test_copy_checks_commit_and_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = root / 'raw/checkpoints/sleep_000057'
            (checkpoint / 'adapter').mkdir(parents=True)
            (checkpoint / 'adapter/adapter_model.safetensors').write_bytes(b'synthetic adapter')
            (checkpoint / 'optimizer_rng.pt').write_bytes(b'synthetic optimizer')
            commit = dict(adapter_files={'adapter_model.safetensors': enrich.file_sha(checkpoint / 'adapter/adapter_model.safetensors')},
                          checkpoint_sha256={'optimizer': enrich.file_sha(checkpoint / 'optimizer_rng.pt')})
            (checkpoint / 'COMMIT.json').write_text(json.dumps(commit))
            complete = dict(index=50, sha256='synthetic', document=dict(cycle=57, checkpoint=commit))
            receipt = enrich.preserve(root, complete, root / 'preserved')
            self.assertEqual(receipt['cycle'], 57)
            self.assertEqual((root / 'preserved/optimizer_rng.pt').read_bytes(), b'synthetic optimizer')

    def test_existing_intent_prevents_duplicate_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'math_d1').mkdir()
            (root / 'math_d1/INTENT_1.json').write_text('{}')
            with patch.object(enrich, 'HERE', root), patch.object(enrich, 'identity', return_value=({}, root)):
                with self.assertRaisesRegex(ValueError, 'publication_intent_exists'):
                    enrich.publish('math_d1', 1, 'Synthetic parent input.')


class LanguageRouteTests(unittest.TestCase):
    def capsule(self):
        import hashlib
        raw = 'Synthetic dialogue: A full-width word，unchanged.'
        response = dict(index=10, kind='RESPONSE', journal_id='synthetic',
                        document=dict(response=dict(raw=raw)))
        response['sha256'] = enrich.digest(response)
        stage = dict(index=12, kind='R184_STAGE', journal_id='synthetic', document=dict(stage='THINK'))
        stage['sha256'] = enrich.digest(stage)
        return dict(sender=dict(life='r203_creative_structured_a4', node='node1', physical=4),
                    receiver=dict(life='creative_d1', node='node2', physical=4), requested_delivery_stage='THINK',
                    child_only_source=True, child_text_modified=False, operator_paraphrase=False, P7_suspended=True,
                    source_record=response, source_stage_record=stage, span=dict(start=0, end=len(raw)),
                    text=raw, text_sha256=hashlib.sha256(raw.encode()).hexdigest())

    def test_exact_language_capsule_preserves_raw_and_stays_visible(self):
        import r211_receive
        from organism_v6.orch_r125_plain_context import has_scaffolding
        capsule = self.capsule()
        text = r211_receive.validate(capsule)
        self.assertIn(capsule['text'], text)
        self.assertFalse(has_scaffolding('Tool: ' + text))

    def test_p7_and_other_routes_are_rejected(self):
        import r211_receive
        for sender in ('creative_b1', 'P7', 'math_transfer_c1'):
            capsule = self.capsule()
            capsule['sender']['life'] = sender
            with self.assertRaisesRegex(ValueError, 'only_active_A4_to_D1'):
                r211_receive.validate(capsule)

    def test_normalized_span_and_changed_record_are_rejected(self):
        import r211_receive
        capsule = self.capsule()
        capsule['text'] = capsule['text'].replace('，', ',')
        with self.assertRaisesRegex(ValueError, 'exact_unchanged_child_span'):
            r211_receive.validate(capsule)
        capsule = self.capsule()
        capsule['source_record']['document']['response']['raw'] = 'Changed.'
        with self.assertRaisesRegex(ValueError, 'source_record_hash_mismatch'):
            r211_receive.validate(capsule)

    def test_r212_blocks_handoff_before_any_process_controls(self):
        import ast
        source = Path(enrich.__file__).with_name('filter_stage.py').read_text()
        tree = ast.parse(source)
        handoff = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'handoff')
        self.assertIsInstance(handoff.body[0], ast.Raise)
        self.assertIn('R212_NO_PAUSES', ast.unparse(handoff.body[0]))


if __name__ == '__main__':
    unittest.main()

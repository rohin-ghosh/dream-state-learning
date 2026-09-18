"""Small CPU fixtures: portable files, pinned source identity, no ancestor reads."""

import argparse
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from gpu import astra_portable_actor_bundle as bundle


def fixture(root):
    options = argparse.Namespace(**{name: str(root / name) for name in (
        'base_after', 'campaign', 'audit_root', 'repair_root', 'cycle_root', 'lesson_root',
        'transfer_root', 'prior_collection_root', 'output')})
    lesson, model = Path(options.lesson_root), root / 'model'
    adapter = lesson / 'train/adapter'
    adapter.mkdir(parents=True)
    model.mkdir()
    bundle.source.write(adapter / 'adapter_config.json', dict(r=8))
    (adapter / 'adapter_model.safetensors').write_bytes(b'fixture-only-not-model-weights')
    bundle.source.write(model / 'config.json', dict(model_type='qwen2', hidden_size=3584, num_hidden_layers=28))
    (model / 'model.safetensors').write_bytes(b'fixture-base')
    for name in ('tokenizer.json', 'tokenizer_config.json'):
        bundle.source.write(model / name, dict(fixture=True))
    parent = dict(trained_state=bundle.PARENT_STATE, source_commit=bundle.transfer.SOURCE_COMMIT,
        parent=dict(expected_base_sha256='b' * 64), trained_adapter_dir=str(adapter),
        trained_adapter_files={path.name: bundle.source.file_hash(path) for path in adapter.iterdir()},
        base_files=bundle.transfer.base_files(model), recorded_training_binding={})
    for phase, field in (('train', 'training_result_sha256'), ('after', 'after_result_sha256'), ('collect', 'lessons_result_sha256')):
        directory = lesson / phase
        directory.mkdir(exist_ok=True)
        bundle.source.write(directory / 'RESULT.json', dict(private_teacher_plan='DO_NOT_EXPORT', phase=phase))
        parent[field] = bundle.source.file_hash(directory / 'RESULT.json')
    (lesson / 'launch').mkdir()
    (lesson / 'launch/source_commit.txt').write_text(bundle.transfer.SOURCE_COMMIT + '\n')
    (lesson / 'source/organism_v6').mkdir(parents=True)
    for field, filename in (('lesson_helper_sha256', 'experienced_event_two_hop_lesson.py'),
                            ('actor_helper_sha256', 'experienced_event_two_hop.py')):
        path = lesson / 'source/organism_v6' / filename
        path.write_text('fixture captured source\n')
        parent['recorded_training_binding'][field] = bundle.source.file_hash(path)
    exposed = Path(options.prior_collection_root) / 'expose'
    exposed.mkdir(parents=True)
    bundle.source.write(exposed / 'RESULT.json', dict(PROBE_outcome='DO_NOT_EXPORT'))
    inputs = dict(parent=parent, arguments=dict(model_dir=str(model), expected_base_sha256='b' * 64, private='DO_NOT_EXPORT'),
        old_ids=['E_A', 'N_B'], binding=dict(state=bundle.PARENT_STATE, old_ids=['E_A', 'N_B'],
            prior_exposure_result_sha256=bundle.source.file_hash(exposed / 'RESULT.json'), scores='DO_NOT_EXPORT'),
        worlds=dict(PROBE='DO_NOT_EXPORT'))
    return options, inputs


class PortableActorTests(unittest.TestCase):
    def test_export_read_relocated_without_ancestors_and_explicit_base_check(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            options, inputs = fixture(root)
            before = {str(path): bundle.source.file_hash(path) for path in root.rglob('*') if path.is_file()}
            with patch.object(bundle.collector, 'load_inputs', return_value=inputs) as loader:
                argv = [item for key, value in vars(options).items() for item in ('--' + key.replace('_', '-'), value)]
                receipt = bundle.main(argv)
                self.assertEqual(vars(loader.call_args.args[0]), vars(options))
            output = Path(options.output)
            self.assertEqual({path.name for path in output.iterdir()}, {'adapter', 'MANIFEST.json'})
            manifest = bundle.source.read(output / 'MANIFEST.json')
            self.assertNotIn('DO_NOT_EXPORT', (output / 'MANIFEST.json').read_text())
            self.assertEqual(manifest['old_ids'], inputs['old_ids'])
            self.assertEqual(manifest['engine_arguments'], {key: inputs['arguments'][key] for key in ('model_dir', 'expected_base_sha256')})
            for path, digest in before.items():
                self.assertEqual(bundle.source.file_hash(path), digest)
            moved, cache = root / 'portable', root / 'local-cache'
            output.rename(moved)
            Path(inputs['arguments']['model_dir']).rename(cache)
            Path(options.lesson_root).rename(root / 'offline-ancestors')
            Path(options.prior_collection_root).rename(root / 'offline-prior')
            with patch.object(bundle.collector, 'load_inputs', side_effect=AssertionError('no ancestor loader')):
                arguments = bundle.read_bundle(moved, expected_manifest_sha256=receipt['manifest_sha256'],
                    model_dir=cache, device='cuda:0', gpu_uuid='fixture-uuid')
                self.assertEqual(vars(arguments), dict(model_dir=str(cache), adapter_dir=str(moved / 'adapter'),
                    phase='readout', device='cuda:0', gpu_uuid='fixture-uuid', expected_base_sha256='b' * 64))
                self.assertTrue(bundle.verify_base_files(moved, cache, expected_manifest_sha256=receipt['manifest_sha256'])['verified'])
                (cache / 'model.safetensors').write_bytes(b'wrong-base')
                with self.assertRaisesRegex(ValueError, 'local_base_file_inventory_drift'):
                    bundle.verify_base_files(moved, cache, expected_manifest_sha256=receipt['manifest_sha256'])

    def test_manifest_adapter_inventory_and_source_tampering_fail(self):
        for change in ('manifest', 'weights', 'extra', 'symlink', 'source', 'state', 'tokenizer'):
            with self.subTest(change=change), TemporaryDirectory() as temporary:
                root = Path(temporary)
                options, inputs = fixture(root)
                with patch.object(bundle.collector, 'load_inputs', return_value=inputs):
                    receipt = bundle.export_bundle(options)
                output = Path(options.output)
                digest = receipt['manifest_sha256']
                if change in ('manifest', 'state', 'source'):
                    manifest = bundle.source.read(output / 'MANIFEST.json')
                    if change == 'source':
                        manifest['source_contract']['engine_sha256'] = '0' * 64
                    else:
                        manifest['parent_state'] = '0' * 64
                    (output / 'MANIFEST.json').unlink()
                    bundle.source.write(output / 'MANIFEST.json', manifest)
                    if change != 'manifest':
                        digest = bundle.source.file_hash(output / 'MANIFEST.json')
                elif change == 'weights':
                    (output / 'adapter/adapter_model.safetensors').write_bytes(b'wrong')
                elif change == 'extra':
                    (output / 'adapter/extra.json').write_text('{}')
                elif change == 'symlink':
                    path = output / 'adapter/adapter_model.safetensors'
                    path.unlink()
                    path.symlink_to(Path(inputs['parent']['trained_adapter_dir']) / path.name)
                else:
                    (Path(inputs['arguments']['model_dir']) / 'tokenizer.json').write_text('wrong')
                with self.assertRaises(ValueError):
                    if change == 'tokenizer':
                        bundle.verify_base_files(output, inputs['arguments']['model_dir'], expected_manifest_sha256=digest)
                    else:
                        bundle.read_manifest(output, expected_manifest_sha256=digest)

    def test_export_wrong_parent_receipt_existing_output_and_overlap_fail(self):
        for change in ('parent', 'base', 'receipt', 'existing', 'overlap', 'unvalidated'):
            with self.subTest(change=change), TemporaryDirectory() as temporary:
                root = Path(temporary)
                options, inputs = fixture(root)
                if change == 'parent':
                    inputs['parent']['trained_state'] = '0' * 64
                elif change == 'base':
                    inputs['parent']['parent']['expected_base_sha256'] = '0' * 64
                elif change == 'receipt':
                    inputs['parent']['training_result_sha256'] = '0' * 64
                elif change == 'existing':
                    Path(options.output).mkdir()
                elif change == 'overlap':
                    options.output = str(Path(inputs['parent']['trained_adapter_dir']) / 'new')
                with patch.object(bundle.collector, 'load_inputs', return_value=inputs,
                                  side_effect=ValueError('unvalidated') if change == 'unvalidated' else None):
                    with self.assertRaises(ValueError):
                        bundle.export_bundle(options)
                self.assertFalse((Path(options.output) / 'MANIFEST.json').exists())

    def test_import_contract_without_ml(self):
        script = '''
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from gpu import astra_portable_actor_bundle as bundle
assert bundle.contract()['runtime']['peft'] == '0.20.0'
'''
        result = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()

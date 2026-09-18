"""Synthetic CPU stress of the unchanged native callback and real read accountant."""

import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile


HERE = Path(__file__).resolve().parent
WORKER = HERE.parent
sys.path.insert(0, str(WORKER))
import preparation_io as common
import r176_runner as runner


def main():
    observation = json.loads((HERE / 'RECEIVING_OBSERVATION.json').read_bytes())
    source = (WORKER / 'r176_runner.py').read_bytes()
    assert hashlib.sha256(source).hexdigest() == observation['runner_sha256']
    tree = ast.parse(source)
    native = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'native_run')
    callback = next(node for node in native.body if isinstance(node, ast.FunctionDef) and node.name == 'check')
    factory = ast.parse('def make_checker():\n calls = 0\n return None\n')
    factory.body[0].body[1:] = [callback, ast.Return(value=ast.Name(id='check', ctx=ast.Load()))]
    common.time.time = lambda: common.END - 3600
    cap = 48 * common.MIB if sys.argv[1] == 'repaired' else 24 * common.MIB
    baseline = max(proof['charged_bytes']['metadata'] for proof in observation['proofs'])
    original_observation = json.loads((WORKER / 'REVIEW_R179_RECEIVING_READONLY_20260917T1730Z.json').read_bytes())
    additional_source_pass = original_observation['source_bytes_total']
    config_bytes = max(observation['config_bytes_unmapped'])
    with tempfile.TemporaryDirectory(prefix='callback_fixture_', dir=HERE) as temporary:
        root = Path(temporary).resolve()
        config_path = root / 'synthetic_config.json'
        payload = {'review_fixture_only': True, 'padding': ''}
        payload['padding'] = 'x' * (config_bytes - len(common.canonical(payload)))
        config_path.write_bytes(common.canonical(payload))
        assert config_path.stat().st_size == config_bytes
        config = {field: {'path': str(root / (field + '.json'))} for field in (
            'source', 'cpu_gate', 'runner_cpu_gate', 'capture', 'lease')}
        config.update(python=str(root / 'python'), service_path=str(root / 'service'), execution=runner.reference(config_path))
        reader = common.Reader(root / 'accounting', {'metadata': {'document': {'bytes': cap}, 'reference': {}}}, [])
        runner.ROOT, runner.PAYLOAD = root, root / 'payload'
        runner.charge_open_reads(reader, root / 'model_source', config)
        namespace = {'common': common, 'time': common.time, 'reference': runner.reference,
            'config_path': config_path, 'config': config, 'reservation': {'deadline_unix': common.END - 1}}
        exec(compile(ast.fix_missing_locations(factory), '<unchanged_native_check_fixture>', 'exec'), namespace)
        check = namespace['make_checker']()
        callback_count = 0
        status, reason = 'PASS', None
        try:
            reader.charge(root / 'actual_validator_cost_seed', 'metadata', baseline)
            reader.charge(root / 'synthetic_extra_entire_source_pass', 'metadata', additional_source_pass)
            for label in ('base_hash', 'base_hash'):
                check(label)
                callback_count += 1
            for prompt_index in range(3):
                for label in ('call', 'generation'):
                    check(label)
                    callback_count += 1
                for token_index in range(512):
                    check('forward')
                    callback_count += 1
            for label in ('base_hash', 'complete'):
                check(label)
                callback_count += 1
        except ValueError as error:
            status, reason = 'REFUSED', str(error)
        print(json.dumps({'status': status, 'reason': reason, 'metadata_cap_bytes': cap,
            'metadata_charged_bytes': reader.charged['metadata'], 'callbacks': callback_count,
            'config_bytes': config_bytes, 'actual_validator_cost_seed': baseline,
            'synthetic_extra_entire_source_pass_bytes': additional_source_pass,
            'headroom_bytes': cap - reader.charged['metadata'], 'runner_sha256': observation['runner_sha256'],
            'uses_unchanged_native_check_AST': True, 'real_Reader_charge_and_audit_hook': True,
            'all_fixture_data_synthetic': True, 'model_gpu_provider_calls': 0, 'signals': 0,
            'actual_receiving_state_writes': 0}, sort_keys=True))


if __name__ == '__main__':
    main()

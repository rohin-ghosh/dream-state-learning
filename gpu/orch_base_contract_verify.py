"""CPU-only replay of every raw prompt, token, target and safe-checker receipt."""

import argparse
import json
from pathlib import Path

from gpu import astra_portable_actor_bundle as portable
from gpu.orch_base_contract_screen import serialization
from organism_v6 import orch_base_contract as policy


def main():
    parser = argparse.ArgumentParser()
    for name in ('freeze', 'raw', 'model-dir'):
        parser.add_argument('--' + name, required=True)
    options = parser.parse_args()
    entries = json.loads(Path(options.freeze).read_text())['entries']
    tokenizer = portable.source.native.load_local_tokenizer(options.model_dir)
    count = 0
    for shard in range(4):
        history = {}
        for path in sorted((Path(options.raw) / f'shard{shard}').glob('CALL_*.json')):
            row = json.loads(path.read_text())
            entry = entries[row['position']]
            key = row['position'], row['state']
            previous = history.get(key)
            assert row['kind'] == ('solution' if previous is None else 'record')
            assert previous is None or previous['outcome_pass']
            messages, student = policy.prompt(entry, previous)
            assert messages == row['call']['messages'] and student == row['student_prefix']
            assert serialization(tokenizer, messages) == row['serialization']
            result = row['call']
            token_ids = result['token_ids']
            terminal = bool(token_ids) and token_ids[-1] == tokenizer.eos_token_id
            assert terminal == result['terminal']
            raw = tokenizer.decode(token_ids[:-1] if terminal else token_ids, skip_special_tokens=False,
                                   clean_up_tokenization_spaces=False)
            assert raw == result['raw'] == row['target']
            reconstructed = policy.capture(entry, result, student, previous)
            for field in ('target_sha256', 'outcome_pass', 'feedback', 'generated_tokens', 'token_contract'):
                assert reconstructed[field] == row[field], (path, field)
            history[key] = reconstructed
            count += 1
    print(json.dumps(dict(status='PASS', verified_calls=count, model_calls=0, gpu_assignment=None)))


if __name__ == '__main__':
    main()

"""CPU replay of immutable PERSIST-CODE native receipts, without semantic labels."""

import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from organism_v6 import orch_persist_code as ledger
from gpu import orch_persist_code_screen as driver


def read(path):
    return json.loads(path.read_text())


def replay(root):
    summary = {}
    for arm in ('RICH', 'TERSE'):
        directory = root / arm
        result = read(directory / 'RESULT.json')
        assert result['status'] == 'COMPLETE' and not (directory / 'FAILED.json').exists()
        assert result['state_before'] == result['state_after'] == driver.STATE
        assert result['frozen_base_unchanged'] and result['fits'] == result['updates'] == 0
        tasks = read(directory / 'TASKS.json')
        assert tasks == ledger.build_tasks(count=8)
        assert ledger.digest(tasks) == result['binding']['task_roster_sha256']
        assert hashlib.sha256(Path(ledger.__file__).read_bytes()).hexdigest() == result['binding']['helper_sha256']
        captures = [read(path) for path in sorted(directory.glob('CALL_*.json'))]
        assert [call['id'] for call in captures] == list(range(result['model_calls']))
        assert [call_id for episode in result['episodes'] for call_id in episode['calls']] == list(range(len(captures)))
        assert all(len(episode['calls']) <= 6 for episode in result['episodes'])
        indexed = {task['id']: task for task in tasks}
        with tempfile.TemporaryDirectory() as temporary:
            codebase = ledger.Codebase(Path(temporary) / 'codebase')
            for call in captures:
                response = call['response']
                assert response['messages'] == call['messages']
                assert response['prompt_tokens'] <= 1536 and len(response['token_ids']) <= 512
                assert response['prompt_tokens'] + len(response['token_ids']) <= 2048
                assert call['student_prefix'] == call['messages'][1:]
                if 'action' in call:
                    assert ledger.parse_action(response['raw'])[0] == call['action']
                if 'oracle_after' in call:
                    replayed = codebase.patch(indexed[call['task_id']], call['action']['expression'])
                    assert replayed == call['oracle_after']
                if call['phase'] == 'record' and 'format_or_oracle_error' not in call:
                    codebase.record(call['task_id'], call['action']['record'], call['id'])
            assert (codebase.directory / 'ledger.py').read_bytes() == (directory / 'codebase/ledger.py').read_bytes()
            assert codebase.records == read(directory / 'codebase/records.json')
            assert result['successes'] == len(codebase.functions)
            assert result['own_records'] == len(codebase.records)
        summary[arm] = dict(successes=result['successes'], tasks=len(tasks), calls=len(captures),
                            records=result['own_records'], corrections=result['corrections'],
                            generated_tokens=sum(len(call['response']['token_ids']) for call in captures),
                            prompt_tokens=sum(call['response']['prompt_tokens'] for call in captures),
                            narrative_tokens=[call.get('narrative_tokens') for call in captures],
                            length_ok=sum(call.get('rich_length_ok', False) for call in captures),
                            reference_successes=result['reference_successes'],
                            outcomes=[episode['success'] for episode in result['episodes']],
                            native_elapsed_seconds=result['finished_epoch'] - result['started_epoch'],
                            raw_result_sha256=hashlib.sha256((directory / 'RESULT.json').read_bytes()).hexdigest(),
                            source_commit=result['binding']['source_commit'],
                            replay='PASS', semantic='NOT_AUTOMATICALLY_ADMITTED')
    summary['rich_minus_terse_tasks'] = summary['RICH']['successes'] - summary['TERSE']['successes']
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    options = parser.parse_args()
    options.output.write_text(json.dumps(replay(options.root), indent=2, sort_keys=True))

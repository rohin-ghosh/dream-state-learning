import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from organism_v6 import level1_prediction_transfer as material_api


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def audit(unpacked):
    results = []
    for seed in range(3):
        attempt = 2 if seed in (0,1) else 1
        root = unpacked / f'prediction_transfer_seed{seed}_20260913_attempt{attempt}'
        collection_root = unpacked / (root.name + '_collected')
        plan, material = read(root / 'plan.json'), read(root / 'material.json')
        complete, calls = read(root / 'capture_complete.json'), read(root / 'calls.json')
        collection, scores = read(collection_root / 'collection.json'), read(collection_root / 'scores.json')
        assert not (root / 'controller_failure.json').exists()
        assert not (collection_root / 'collection_failure.json').exists()
        assert plan['learner_seed'] == seed and plan['fits'] == plan['updates'] == 0
        assert digest(root / 'plan.json') == scores['plan_sha256'] == collection['plan_sha256'] == complete['plan_sha256']
        assert digest(root / 'capture_complete.json') == scores['completion_sha256'] == collection['completion_sha256']
        assert digest(collection_root / 'scores.json') == collection['scores_sha256']
        assert material['material_sha256'] == '150bc6b4431a2ad80205ee17e04f3f2d99c4f8e19e917ce7d6bbb8210e537d29'
        assert material == material_api.build_material(original_material_path=material['original_material']['path'])
        assert scores['calls'] == complete['calls'] == 96
        for name, checksum in plan['input_hashes'].items():
            assert digest(root / name) == checksum
        summaries = {}
        for state in ('OFF', 'post'):
            directory = root / 'run' / state
            assert not (directory / 'failure.json').exists() and not (directory / 'stage_failure.json').exists()
            closed, released, exited, identity = (read(directory / name) for name in ('closed.json', 'released.json', 'exit.json', 'identity.json'))
            assert closed['calls'] == 48 and exited['returncode'] == 0 and released['owned_group_released'] is True
            assert released['identity'] == exited['identity'] == identity['worker']
            assert identity['route'] == (None if state == 'OFF' else {'name':'level1_skill','id':1,'path':plan['adapter']})
            assert identity['adapter_files'] == ({} if state == 'OFF' else plan['adapter_files'])
            for name, checksum in closed['files'].items():
                assert digest(directory / name) == checksum
            for label in ('pre', 'post'):
                for name, field in (('gpu','empty'), ('cvd','clear'), ('queue','matched')):
                    assert read(directory / f'{label}_{name}.json')['value'][field] is True
            assert len(list(directory.glob('*.response.json'))) == 48
            recomputed = []
            for index, row in enumerate(material['rows']):
                call = calls[index]
                request = read(directory / f'call_{index:02d}.request.json')
                response_path = directory / f'call_{index:02d}.response.json'
                response = read(response_path)
                assert request == call and call['row_id'] == row['row_id'] and call['messages'] == row['input_messages']
                assert response['actual_prompt_token_ids'] == call['native']['prompt_token_ids'] == response['prompt_token_ids']
                assert response['lora_request'] == identity['route'] and response['decoded_output'] == response['text']
                assert len(response['output_token_ids']) <= 192 and response['finish_reason'] in ('stop','length')
                score = material_api.score_response(row, response['text'], response['finish_reason'], original_material_path=material['original_material']['path'])
                observed = scores['cells'][state][index]
                assert observed['score'] == score and observed['response_sha256'] == digest(response_path)
                assert observed['raw'] == response['text'] and observed['row_id'] == row['row_id']
                assert observed['prompt_tokens'] == len(response['actual_prompt_token_ids']) and observed['output_tokens'] == len(response['output_token_ids'])
                recomputed.append((row, score, response['finish_reason']))
            summaries[state] = {}
            for view in ('FULL','MINIMAL'):
                selected = [entry for entry in recomputed if entry[0]['view'] == view]
                summary = scores['summaries'][state][view]
                assert len(selected) == summary['denominator'] == 24
                assert sum(score['content_correct'] for _,score,_ in selected) == summary['content_correct']
                assert sum(score['strict'] for _,score,_ in selected) == summary['strict']
                assert dict(Counter(finish for _,_,finish in selected)) == summary['finish_reasons']
                summaries[state][view] = summary
        differences = {view:summaries['post'][view]['content_correct']-summaries['OFF'][view]['content_correct'] for view in ('FULL','MINIMAL')}
        assert all(differences[view] == scores['post_minus_OFF'][view]['post_minus_OFF'] for view in differences)
        results.append({'seed':seed,'attempt':attempt,'summaries':summaries,'post_minus_OFF':differences,'costs':scores['costs'],
            'controller_elapsed_seconds':scores['controller_elapsed_seconds'],'collection':{'path':str(collection_root / 'collection.json'),'sha256':digest(collection_root / 'collection.json')}})
    return {'status':'AUDITED_DEV_ONLY','calls':288,'additional_failed_attempt_calls':192,'total_attempted_calls':480,'fits':0,'seeds':results,
        'continuation_rule_met':all(result['summaries']['post']['MINIMAL']['content_correct'] >= 20 and result['post_minus_OFF']['MINIMAL'] > 0 for result in results),
        'limits':'Shared authored cases and repeated frozen OFF; no matched-trained parenting control, new-family transfer, retention or H1/P1/H2 claim.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('unpacked', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = audit(args.unpacked)
    with args.output.open('x') as stream:
        json.dump(result,stream,indent=2,sort_keys=True,allow_nan=False)
        stream.write('\n')
    print(json.dumps({'status':result['status'],'calls':result['calls'],'continuation_rule_met':result['continuation_rule_met'],
        'seeds':[{'seed':value['seed'],'post_minus_OFF':value['post_minus_OFF']} for value in result['seeds']]}))

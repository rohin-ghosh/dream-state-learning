import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile


def checksum(raw):
    return hashlib.sha256(raw).hexdigest()


archive_path = Path('gpu_artifacts_local/l2_public_record_20260913/astra_l2_high_seed2_greedy_20260913_attempt1.tar')
assert checksum(archive_path.read_bytes()) == '94b4c06968744cd9ef3b79b40e7e61363167a88ae04394827aab85a2120fd124'
root = 'l2_high_seed2_greedy_20260913_attempt1'
with tarfile.open(archive_path) as archive:
    members = archive.getmembers()
    assert len({member.name for member in members}) == len(members)
    assert all(not PurePosixPath(member.name).is_absolute() and '..' not in PurePosixPath(member.name).parts
               and (member.isfile() or member.isdir()) for member in members)
    files = {member.name: archive.extractfile(member).read() for member in members if member.isfile()}


def read(name):
    return json.loads(files[name])


prepared = read(root + '/prepared.json')
assert checksum(files[root + '/prepared.json']) == '1d08018f9614d975d83e6f83d0990cf0d007769f833f1170a7c83c710efb588e'
report = read(root + '_collected/report.json')
assert checksum(files[root + '_collected/report.json']) == '62c01302d039093aef7e87ff2dfe5b28e5633c700d2d78ea3c775decf8d3b062'
original_path = Path('gpu_artifacts_local/l2_public_record_20260913/astra_l2_lr_seed2_high_attempt1.tar')
assert checksum(original_path.read_bytes()) == 'd5f91bc56a57a48aad204e1dd3dd8b972c58b97f16d518627e726f8f8cf7082c'
with tarfile.open(original_path) as original:
    world = json.load(original.extractfile('l2_lr_seed2_high_20260913_attempt1/world.json'))['value']['fields']
actions = world['public']['fields']['actions']['tuple']
truth = world['success_actions']['tuple']
capture = read(root + '/capture_complete.json')
hf = json.loads(Path('/tmp/astra_l2_access_high_seed2_report_20260913.json').read_bytes())
replayed, disagreements = {}, []
verified_stage_files = 0
for state in ('OFF', 'fit2_PROMOTE'):
    for relative, expected in capture['states'][state].items():
        assert checksum(files[f'{root}/{state}/{relative}']) == expected
        verified_stage_files += 1
    panels = {'train': [], 'readout': []}
    costs = dict(calls=32, prompt_tokens=0, output_tokens=0, generation_seconds=0)
    for index, row in enumerate(prepared['rows']):
        request = read(f'{root}/{state}/{index:02d}.request.json')
        response = read(f'{root}/{state}/{index:02d}.response.json')
        assert request['messages'] == row['messages'] and request['native'] == row['native']
        assert response['route'] == prepared['routes'][state]
        assert response['returned_prompt_token_ids'] == row['native']['prompt_token_ids']
        raw = bytes.fromhex(response['raw_hex'])
        assert response['text'].encode() == raw
        choices = [action for action in actions if raw in (action.encode(), (action + '\n').encode())]
        assert len(choices) <= 1
        choice = choices[0] if choices else None
        item = dict(slot_id=row['slot_id'], slot_index=row['slot_index'], choice=choice,
                    correct=choice == truth[row['slot_index']], exact_archived_target=raw.hex() == row['archived_target_hex'],
                    finish_reason=response['finish_reason'], output_tokens=len(response['output_token_ids']))
        panels[row['view']].append(item)
        costs['prompt_tokens'] += len(response['returned_prompt_token_ids'])
        costs['output_tokens'] += len(response['output_token_ids'])
        costs['generation_seconds'] += response['ended'] - response['started']
        forced = hf['states'][state][row['view']]['rows'][row['slot_index']]
        assert forced['slot_id'] == row['slot_id']
        if item['correct'] != forced['first_correct']:
            disagreements.append(dict(state=state, view=row['view'], slot_index=row['slot_index'],
                                      native_correct=item['correct'], hf_first_correct=forced['first_correct'],
                                      hf_first_gold_margin=forced['gold_first_margin']))
    for view, rows in panels.items():
        result = dict(rows=rows, total=16, old_total=8, new_total=8,
                      correct=sum(item['correct'] for item in rows),
                      old_correct=sum(item['correct'] for item in rows[:8]),
                      new_correct=sum(item['correct'] for item in rows[8:]),
                      legal=sum(item['choice'] is not None for item in rows),
                      malformed=sum(item['choice'] is None for item in rows),
                      exact_archived_targets=sum(item['exact_archived_target'] for item in rows),
                      stop_correct=sum(item['correct'] and item['finish_reason'] == 'stop' for item in rows),
                      length_outputs=sum(item['finish_reason'] == 'length' for item in rows))
        assert result == report['states'][state][view]
    assert costs == report['costs'][state]
    replayed[state] = {view: {key: value for key, value in report['states'][state][view].items() if key != 'rows'} for view in panels}
result = dict(status='PASS_RAW_RECEIPT_REPLAY', generation_calls=64, verified_stage_files=verified_stage_files,
              archive_members=len(members), states=replayed, hf_native_correctness_disagreements=disagreements,
              claim='Local archive/hash, native-prefix, original-world scoring and cost replay only; no fresh generation or numerical parity claim.')
with Path('/tmp/astra_greedy_receipt_replay_20260913.json').open('x') as output:
    json.dump(result, output, sort_keys=True, indent=2)
    output.write('\n')
print(json.dumps(result, sort_keys=True))

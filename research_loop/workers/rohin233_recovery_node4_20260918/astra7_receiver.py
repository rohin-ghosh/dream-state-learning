"""Renew only the CPU bridge binding to Jason's actual recovered incarnation."""

import hashlib
import json
import os
from pathlib import Path
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r229_Astra7_20260918')
OPERATOR = ROOT / 'node4_bridge/operator'
EPOCH = ROOT / 'node4_bridge/r233_recovery'
JOURNAL = '6a2fa591a1304fd8b3eff24f65e5caff'
LOADED_SHA = '1454621c60943dea4399858b30ee195418f4406e2201c19e5a891965621e28f1'
RECEIVER_SHA = 'a829156ed6341b96ca17754e2335bc51f1c029271e1b8c9a86641a7aa232da16'
PLAN_SHA = '29322446a88ee4e7a82d8b4cba2aee08601d2d98b51dd3a2a7b410cd55e30a5a'
GUARD_SHA = 'c2678d44a20ab286ec3fde0a2b86143ba59905498d6719062f64c880497ff87d'


def renewed_matches(matches, current_publications):
    return [entry for entry in matches if entry['publication']['id'] in current_publications]


def install():
    sys.path.insert(0, str(OPERATOR))
    import r229_astra7_endpoint as old

    def status():
        source, life = ROOT / 'source_r233_recovery', ROOT / 'raw'
        guard_path, plan_path = [ROOT / 'control_r233_recovery' / name for name in ('GUARD.json', 'PLAN.json')]
        old.require(os.getuid() == 2524 and old.read(life / 'stream/JOURNAL.json')['journal_id'] == JOURNAL,
            'actual_same_Astra7_user_and_journal')
        old.require(hashlib.sha256(guard_path.read_bytes()).hexdigest() == GUARD_SHA
            and hashlib.sha256(plan_path.read_bytes()).hexdigest() == PLAN_SHA, 'Jason_renewed_guard_plan_hashes')
        guard, plan = old.read(guard_path), old.read(plan_path)
        receiver = source / 'gpu/r229_p7_inbox.py'
        old.require(hashlib.sha256(receiver.read_bytes()).hexdigest() == RECEIVER_SHA
            and guard['source_pins']['gpu/r229_p7_inbox.py'] == RECEIVER_SHA
            and guard['plan_sha256'] == PLAN_SHA, 'unchanged_authenticated_P7_receiver')
        process = Path('/proc/762967')
        fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
        old.require(fields[19] == '98059264' and fields[0] != 'Z'
            and os.readlink(process / 'cwd') == str(source), 'actual_recovered_Astra7_PID_start_source')
        loaded = old.check_record(old.read(life / 'stream/records/00000000000000003128.json'), JOURNAL, 'LOADED')
        old.require(loaded['sha256'] == LOADED_SHA and loaded['document']['pid'] == 762967
            and time.time() < plan['hard_end_unix'], 'actual_recovered_Astra7_LOAD_and_current_budget')
        sys.path.insert(0, str(source))
        from gpu.r229_p7_inbox import publish_p7
        return dict(journal_id=JOURNAL, physical_root=str(life), source_root=str(source),
            native_pid=762967, native_start_ticks='98059264', loaded=True, loaded_record=loaded,
            logical_root=plan['root'], hard_end_unix=plan['hard_end_unix'], receiver_imported=callable(publish_p7),
            receiver_supported_stages=['ACT'], source_receiver_sha256=RECEIVER_SHA,
            frontier_index=max(int(path.stem) for path in (life / 'stream/records').glob('[0-9]' * 20 + '.json')),
            observed_unix=time.time(), learner_signals=[])

    old.status = status
    original_reply = old.actual_parent_reply

    def actual_parent_reply(life, projection):
        matches = original_reply(life, projection)
        current = {old.read(path)['publication']['id'] for path in (EPOCH / 'published').glob('*.json')}
        matches = renewed_matches(matches, current)
        projection['capsule'].pop('reply_to', None)
        if matches:
            projection['capsule']['reply_to'] = matches
            projection['publication_key'] = old.digest(projection['capsule'])
        return matches

    old.actual_parent_reply = actual_parent_reply
    return old


def main(request):
    endpoint = install()
    if request['op'] == 'receive':
        endpoint.require(request['capsule']['source_stage']['document']['stage'] == 'ACT', 'receiver_ACT_only')
    result = endpoint.main(request)
    if request['op'] == 'receive':
        endpoint.write_once(EPOCH / 'published' / (endpoint.digest(request['capsule']) + '.json'), result)
    return result


if __name__ == '__main__':
    print(json.dumps(main(json.loads(sys.stdin.read())), ensure_ascii=False))

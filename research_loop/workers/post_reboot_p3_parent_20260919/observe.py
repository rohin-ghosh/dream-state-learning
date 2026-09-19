"""Sanitized last-three MODEL-parent evidence, never static-turn attribution."""

import json
import os
from pathlib import Path
import subprocess
import time

import runner


CONTRACT = runner.HERE.parent / 'post_recovery_correction_hourly_20260918/contract'


def model_attempt(folder):
    result_path = folder / 'RESULT.json'
    if not result_path.exists():
        return None
    result = json.loads(result_path.read_text())
    if result['status'] != 'PUBLISHED':
        return None
    for name in ('API_REQUEST.json', 'stdout.json', 'PUBLISH_INTENT.json', 'SOURCE.json', 'DISPATCH.json'):
        if not (folder / name).is_file():
            raise ValueError('provider_publication_requires_full_original_ledger')
    request = json.loads((folder / 'API_REQUEST.json').read_text())
    response = json.loads((folder / 'stdout.json').read_text())
    intent = json.loads((folder / 'PUBLISH_INTENT.json').read_text())
    source = json.loads((folder / 'SOURCE.json').read_text())
    dispatch = json.loads((folder / 'DISPATCH.json').read_text())
    if not (request['model'] == response['model'] == result['model'] == runner.MODEL
            and request['reasoning'] == {'effort': 'xhigh'} and response['status'] == 'completed'
            and not response.get('error') and request['tools'] == [] and request['store'] is False):
        raise ValueError('exact_existing_xhigh_model_no_tool_response_required')
    texts = [part['text'] for item in response['output'] if item['type'] == 'message'
        for part in item['content'] if part['type'] == 'output_text']
    if len(texts) != 1:
        raise ValueError('one_actual_model_output')
    body = texts[0]
    if body.startswith('```json\n') and body.endswith('\n```'):
        body = body[8:-4]
    actual = json.loads(body)
    if not (actual['speak'] is True and actual['message'] == result['message'] == intent['message']
            and intent['speaker'] == 'Astra' and result['source_sha256'] == runner.sha(folder / 'SOURCE.json')):
        raise ValueError('provider_message_intent_source_result_exact_join_required')
    import hashlib
    return dict(attempt=folder.name, model=request['model'], reasoning_effort=request['reasoning']['effort'],
        API_REQUEST_utc=dispatch['utc'], provider_created_utc=runner.utc(response['created_at']),
        provider_response_file_utc=runner.utc((folder/'stdout.json').stat().st_mtime),
        published_result_utc=runner.utc(result_path.stat().st_mtime),
        publication_id=result['publication']['id'], publication_sha256=result['publication']['sha256'],
        message_sha256=hashlib.sha256(result['message'].encode()).hexdigest(),source_head_sha256=source['head_sha256'],
        journal_id=source['journal_id'],provider_response_completed=True,
        artifact_sha256={name:runner.sha(folder/name) for name in
            ('RESULT.json','SOURCE.json','API_REQUEST.json','stdout.json','PUBLISH_INTENT.json','DISPATCH.json')})


def main():
    os.umask(0o077)
    selected = []
    for folder in sorted((runner.LEDGER / 'turns').glob('parent_*'), reverse=True):
        result_path = folder/'RESULT.json'
        if result_path.exists() and json.loads(result_path.read_text()).get('status') == 'PUBLISHED':
            selected.append(model_attempt(folder))
            if len(selected) == 3:
                break
    selected.reverse()
    if len(selected) != 3:
        raise ValueError('three_actual_model_publications_required')
    code = (CONTRACT/'reader.py').read_text() + '\n' + (CONTRACT/'audit.py').read_text()
    code += '\n' + (runner.HERE/'trace_remote.py').read_text() + '\nprint(json.dumps(trace(' + repr(selected) + ')))\n'
    repo = runner.HERE.parents[2]
    completed = subprocess.run(['bash', str(repo/'gpu/a40r_ssh.sh'), 'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B -'],
        input=code,text=True,capture_output=True,timeout=150)
    if completed.returncode:
        runner.save(runner.HERE/'TRACE_ERROR.json', dict(observed_utc=runner.utc(time.time()),returncode=completed.returncode,
            stderr_sha256=__import__('hashlib').sha256(completed.stderr.encode()).hexdigest()))
        raise ValueError('trace_failed_no_raw_error_export')
    trace = json.loads(completed.stdout)
    by_attempt = {row['attempt']:row for row in trace.pop('rows')}
    rows = [dict(item,chain=by_attempt[item['attempt']]) for item in selected]
    state = json.loads((runner.HERE/'PROCESS.json').read_text())
    current = runner.process(state['process']['pid'])
    same = bool(current and current['state'] != 'Z' and all(current[key] == state['process'][key]
        for key in ('boot_id','pid','start_ticks','command_sha256')))
    boot_unix = next(int(line.split()[1]) for line in Path('/proc/stat').read_text().splitlines() if line.startswith('btime '))
    from datetime import datetime
    report = dict(trace,rows=rows,actual_parent=current,same_parent_identity_alive=same,local_boot_utc=runner.utc(boot_unix),
        model_publications_after_reboot=sum(datetime.fromisoformat(row['published_result_utc']).timestamp() > boot_unix for row in rows),
        model_ACT_chains_after_reboot=sum(datetime.fromisoformat(row['published_result_utc']).timestamp() > boot_unix
            and row['chain']['status']=='PROVIDER_TO_EXACT_REQUEST_TO_COMMITTED_ACT_VERIFIED' for row in rows),
        existing_parent_lock_holders=[line for line in Path('/proc/locks').read_text().splitlines() if '00:24:3352924' in line],
        contract_sha256={name:runner.sha(CONTRACT/name) for name in ('reader.py','audit.py')},
        semantic_quality_or_retention_claim=False,node_local_bridge_not_model_parent=True)
    runner.save(runner.HERE/'LAST3_PROVIDER_REQUEST_ACT.json',report)
    runner.save(runner.HERE/'receipts'/('LAST3_'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'.json'),report)
    print(json.dumps(dict(parent=current,model_publications_after_reboot=report['model_publications_after_reboot'],
        model_ACT_chains_after_reboot=report['model_ACT_chains_after_reboot'],rows=[dict(attempt=row['attempt'],published=row['published_result_utc'],
        request=row['chain'].get('first_request_utc'),ACT=row['chain'].get('ACT_response_utc'),status=row['chain']['status']) for row in rows])))


if __name__ == '__main__':
    main()

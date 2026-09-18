"""One asynchronous, TRAIN-only Astra conversation parent per continual branch."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time

from gpu.orch_route_parent_campaign_providers import STRONG, strong


PROGRAMMES = {'emotional_support', 'brain_lecture', 'creative_writing', 'raw_parented', 'repo_reader'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as output:
        json.dump(value, output, sort_keys=True, indent=2, allow_nan=False)
        output.flush()
        os.fsync(output.fileno())


def validate(config):
    require(config.get('schema') == 'R133_PROGRAMME_PARENT_V1', 'parent_config_schema')
    require(config.get('node') in ('ovx2', 'a40r', 'ovx3', 'a100'), 'known_wrapper_only')
    require(config.get('programme') in PROGRAMMES, 'explicit_programme')
    require(re.fullmatch(r'[A-Za-z0-9_-]{1,64}', config.get('branch', '')), 'branch_label')
    for name in ('root', 'source_root'):
        path = Path(config[name])
        require(path.is_absolute() and '..' not in path.parts
                and str(path).startswith('/localhome/local-rohing/orch_'), 'node_local_branch_path')
    for name in ('programme_path', 'principles_path'):
        require(sha(config[name]) == config[name.replace('_path', '_sha256')], 'fixed_parent_source')
    require(type(config.get('cadence_responses')) is int and config['cadence_responses'] >= 1,
            'positive_parent_cadence')
    require(config.get('cadence_label', 'SPARSE') in ('SPARSE', 'PERSISTENT'), 'known_cadence_label')
    if config.get('cadence_label') == 'PERSISTENT':
        require(config['cadence_responses'] == 1, 'persistent_every_boundary')
        require(type(config.get('minimum_duration_seconds')) is int
                and config['minimum_duration_seconds'] >= 3600, 'persistent_hour_minimum')
    require(type(config.get('parent_style', 'responsive')) is str
            and 0 < len(config.get('parent_style', 'responsive')) <= 300, 'bounded_parent_style')
    require(config.get('parent_reasoning_effort') in (None, 'low', 'medium', 'high', 'xhigh'),
            'known_parent_effort')
    require(type(config.get('poll_interval_seconds', 5)) in (int, float)
            and 0.25 <= config.get('poll_interval_seconds', 5) <= 30,
            'bounded_parent_poll_interval')
    require(type(config.get('start_after_response_count', 0)) is int
            and config.get('start_after_response_count', 0) >= 0, 'valid_parent_resume_cursor')
    require(config.get('schedule_on', 'response') in ('response', 'request'), 'known_parent_clock')
    if config.get('schedule_on') == 'request':
        require(config.get('cadence_label') == 'PERSISTENT', 'prefetch_only_for_persistent')
        require(type(config.get('start_after_request_count', 0)) is int
                and config.get('start_after_request_count', 0) >= 0, 'valid_request_cursor')
    require(type(config.get('hard_end_unix')) in (int, float)
            and time.time() < config['hard_end_unix'], 'parent_wall')
    return config


def remote(repository, config, script):
    wrapper = Path(repository)/'gpu'/(config['node'] + '_ssh.sh')
    command = 'PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=' + shlex.quote(config['source_root'])
    command += ' python3 -c ' + shlex.quote(script)
    result = subprocess.run(['bash', str(wrapper), command], capture_output=True, text=True, timeout=45)
    require(result.returncode == 0, 'node_transport_failed_no_implicit_retry')
    return json.loads(result.stdout)


def snapshot(repository, config):
    script = '''import json,re
from pathlib import Path
from gpu.orch_r125_stream_console import _open_stream_directory,_read_record
root=ROOT
events=[]; consumed={}; boundaries=[]; parent_consumptions=[]; response_count=0; request_count=0; previous='0'*64
with _open_stream_directory(root,'records') as (directory,unused):
 index=0
 while True:
  record=_read_record(directory,index)
  if record is None: break
  if index: assert record['previous_sha256']==previous
  previous=record['sha256']; document=record['document']
  if record['kind']=='REQUEST':
   request_count+=1
   if boundaries and boundaries[-1]['next_request_index'] is None:
    boundaries[-1]['next_request_index']=index
  if record['kind']=='RESPONSE':
   response_count+=1
   boundaries.append(dict(response_count=response_count,record_index=index,next_request_index=None))
   events.append(dict(actor='child',text=document['response']['raw'],record_index=index,record_sha256=record['sha256']))
  elif record['kind']=='INBOX':
   message=document['message']
   consumed[message['id']]=dict(record_index=index,record_sha256=record['sha256'])
   if message['actor']=='parent':
    parent_consumptions.append(dict(record_index=index,speaker=message.get('speaker'),inbox_id=message['id']))
   events.append(dict(actor=message['actor'],speaker=message.get('speaker'),text=message['text'],record_index=index,record_sha256=record['sha256']))
  index+=1
print(json.dumps(dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1',response_count=response_count,
 record_count=index,request_count=request_count,head_sha256=previous,events=events[-8:],consumed_inbox=consumed,
 boundaries=boundaries,parent_consumptions=parent_consumptions)))
'''.replace('ROOT', repr(config['root']))
    return remote(repository, config, script)


def prompt(config, state):
    require(state.get('schema') == 'R133_TRAIN_PARENT_SNAPSHOT_V1', 'training_snapshot_only')
    instruction = ('You are Astra, a conversational parent for a continual language-model learner. '
        'Attend to its actual activity, metacognition, self-reflection, judgment, perception, and '
        'reported confidence, surprise or frustration. Do not assert subjective feelings or consciousness. '
        'Add, stop or steer behavior when useful, not only after failure. Do not prescribe a recurring '
        'thought format, reward length, fabricate execution, give hidden evaluator answers, or diagnose '
        'a human patient. You never see held evaluations. Ask useful questions, explain, challenge and '
        'help the learner investigate; allow initiative and useful silence. The child keeps generating '
        'while you answer. Return only JSON: speak(boolean), message(string, at most90 words), '
        'rationale(short string). If silent, message must be empty. No tools.\n\n'
        + '\nParent style: ' + config.get('parent_style', 'responsive')
        + ('\nThis is the PERSISTENT arm: offer a brief, responsive contribution at every generation boundary. '
           'Vary your intervention with the actual activity; do not repeat a slogan or require longer output. '
           'A useful acknowledgment or a precise question is sufficient; silence is recorded as an uncovered slot. '
           if config.get('cadence_label') == 'PERSISTENT' else '')
        + ('\nThe child is generating while you respond. Prepare guidance for the next boundary from '
           'the latest completed observations shown here; do not invent its unfinished response. '
           if config.get('schedule_on') == 'request' else '')
        + '\n' + Path(config['principles_path']).read_text() + '\n\nProgramme:\n'
        + Path(config['programme_path']).read_text())
    recent = []
    for event in state['events']:
        require(event['actor'] in ('child', 'parent', 'environment'), 'visible_train_actor')
        text = event['text']
        recent.append(dict(event, text=text[:6000] + ('\n[Parent-view excerpt truncated]' if len(text) > 6000 else '')))
    return instruction, json.dumps(dict(programme=config['programme'], branch=config['branch'],
        visible_training_events=recent), ensure_ascii=False)


def publish(repository, config, message):
    script = ('import json; from gpu.orch_r127_pilot_console import publish_parent; '
              + 'print(json.dumps(publish_parent(' + repr(config['root']) + ", 'Astra', "
              + repr(message) + ')))')
    return remote(repository, config, script)


def record_deliveries(output, state):
    for path in Path(output).glob('parent_*/RESULT.json'):
        result = json.loads(path.read_text())
        if result.get('status') != 'PUBLISHED' or (path.parent/'DELIVERED.json').exists():
            continue
        identifier = result['inbox_publication']['id']
        if identifier in state['consumed_inbox']:
            write(path.parent/'DELIVERED.json', dict(status='COMPLETE', speaker='Astra',
                programme=result['programme'], branch=result['branch'], inbox_id=identifier,
                consumption=state['consumed_inbox'][identifier], observed_unix=time.time(),
                observation_time_not_exact_consumption_time=True, result_sha256=sha(path)))


def boundary_coverage(state, baseline):
    boundaries = [item for item in state.get('boundaries', [])
                  if item['response_count'] > baseline and item['next_request_index'] is not None]
    parent_indices = [event['record_index'] for event in state.get('parent_consumptions', [])]
    covered = sum(any(item['record_index'] < index < item['next_request_index']
                      for index in parent_indices) for item in boundaries)
    return dict(closed_boundaries=len(boundaries), covered_boundaries=covered,
                missing_boundaries=len(boundaries)-covered,
                coverage_basis='registered_parent_INBOX_before_next_REQUEST_not_verified_rendered_exposure')


def resume_cursor(config):
    count_key = 'request_count' if config.get('schedule_on') == 'request' else 'response_count'
    cursor = config.get('start_after_' + count_key, 0)
    predecessor = config.get('predecessor_output')
    if predecessor is None:
        return cursor
    predecessor = Path(predecessor)
    require(predecessor.is_absolute() and predecessor.is_dir(), 'existing_parent_predecessor')
    require(sha(predecessor/'STARTED.json') == config.get('predecessor_started_sha256'),
            'pinned_parent_predecessor')
    started = json.loads((predecessor/'STARTED.json').read_text())
    require(started['branch'] == config['branch'] and started['programme'] == config['programme'],
            'same_parent_branch_predecessor')
    reserved = 0
    for path in predecessor.glob('parent_*/SOURCE.json'):
        reserved = max(reserved, json.loads(path.read_text())[count_key])
    require(cursor >= reserved, 'no_replay_of_reserved_parent_sources')
    return cursor


def serve(config_path, repository, output, once=False):
    config_path, output = Path(config_path), Path(output)
    config = validate(json.loads(config_path.read_text()))
    if config.get('cadence_label') == 'PERSISTENT':
        require(time.time()+config['minimum_duration_seconds'] < config['hard_end_unix'],
                'time_for_full_persistent_segment')
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    write(output/'STARTED.json', dict(pid=os.getpid(), started_unix=time.time(), config_sha256=sha(config_path),
                                    model=STRONG, programme=config['programme'], branch=config['branch'],
                                    schedule_on=config.get('schedule_on', 'response')))
    last_count = resume_cursor(config)
    calls = 0
    baseline = None
    while time.time() < config['hard_end_unix']:
        validate(config)
        state = snapshot(repository, config)
        if baseline is None:
            baseline = config.get('start_after_response_count', 0)
            write(output/'SEGMENT.json', dict(started_unix=time.time(), baseline_response_count=baseline,
                cadence_label=config.get('cadence_label', 'SPARSE'),
                parent_style=config.get('parent_style', 'responsive'),
                minimum_duration_seconds=config.get('minimum_duration_seconds', 0)))
        if config.get('cadence_label') == 'PERSISTENT':
            coverage_path = output/('COVERAGE_' + str(state['record_count']) + '.json')
            if not coverage_path.exists():
                write(coverage_path, dict(observed_unix=time.time(), **boundary_coverage(state, baseline)))
        record_deliveries(output, state)
        clock = state['request_count'] if config.get('schedule_on') == 'request' else state['response_count']
        if clock < max(1, last_count + config['cadence_responses']):
            if once:
                return
            time.sleep(config.get('poll_interval_seconds', 5))
            continue
        last_count = clock
        directory = output/f'parent_{calls:06d}'
        directory.mkdir()
        calls += 1
        write(directory/'SOURCE.json', state)
        instruction, payload = prompt(config, state)
        (directory/'SYSTEM.txt').write_text(instruction)
        (directory/'PROMPT.txt').write_text(payload)
        receipt = dict(speaker='Astra', programme=config['programme'], branch=config['branch'],
                       source_response_count=state['response_count'], source_head_sha256=state['head_sha256'],
                       schedule_on=config.get('schedule_on', 'response'), schedule_count=last_count,
                       started_unix=time.time(), status='MISSING', retry=False)
        write(directory/'DISPATCH_INTENT.json', dict(source_response_count=state['response_count'],
            schedule_on=config.get('schedule_on', 'response'), schedule_count=last_count,
            source_sha256=sha(directory/'SOURCE.json'), system_sha256=sha(directory/'SYSTEM.txt'),
            prompt_sha256=sha(directory/'PROMPT.txt'), created_unix=time.time(),
            uncertainty_requires_reconciliation=True, retries=0))
        try:
            response, model, usage = strong(payload, directory,
                min(config['hard_end_unix'], time.time()+120), instruction,
                reasoning_effort=config.get('parent_reasoning_effort'))
            receipt.update(actual_model=model, usage=usage, response=response)
            require(time.time() < config['hard_end_unix'], 'late_reply_not_delivered')
            if response['speak']:
                receipt['sent_unix'] = time.time()
                receipt['inbox_publication'] = publish(repository, config, response['message'])
                receipt['status'] = 'PUBLISHED'
                receipt['consumption_not_yet_verified'] = True
            else:
                receipt['status'] = 'SILENT'
        except Exception as error:
            receipt.update(error_type=type(error).__name__, error_code='parent_call_or_delivery_failed')
        receipt['finished_unix'] = time.time()
        write(directory/'RESULT.json', receipt)
        if once:
            return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--once', action='store_true')
    arguments = parser.parse_args()
    serve(arguments.config, arguments.repository, arguments.output, arguments.once)

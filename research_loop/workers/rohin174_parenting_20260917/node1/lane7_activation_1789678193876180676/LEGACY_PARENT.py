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


PROGRAMMES = {'emotional_support', 'brain_lecture', 'creative_writing', 'raw_parented'}


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
events=[]; consumed={}; response_count=0; previous='0'*64
with _open_stream_directory(root,'records') as (directory,unused):
 index=0
 while True:
  record=_read_record(directory,index)
  if record is None: break
  if index: assert record['previous_sha256']==previous
  previous=record['sha256']; document=record['document']
  if record['kind']=='RESPONSE':
   response_count+=1
   events.append(dict(actor='child',text=document['response']['raw'],record_index=index,record_sha256=record['sha256']))
  elif record['kind']=='INBOX':
   message=document['message']
   consumed[message['id']]=dict(record_index=index,record_sha256=record['sha256'])
   events.append(dict(actor=message['actor'],speaker=message.get('speaker'),text=message['text'],record_index=index,record_sha256=record['sha256']))
  index+=1
print(json.dumps(dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1',response_count=response_count,
 record_count=index,head_sha256=previous,events=events[-8:],consumed_inbox=consumed)))
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
        'while you answer. Return only JSON: speak(boolean), message(string, at most 90 words), '
        'rationale(short string). If silent, message must be empty. No tools.\n\n'
        + Path(config['principles_path']).read_text() + '\n\nProgramme:\n'
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


def serve(config_path, repository, output, once=False):
    config_path, output = Path(config_path), Path(output)
    config = validate(json.loads(config_path.read_text()))
    require(config.get("r167_parent_resume") == {'branch': 'a100_7_classroom_support', 'old_output': '/data/home/rohing/dream-state-orch/research_notes/analysis/orch_r136_node1_20260916/parent7', 'programme': 'emotional_support', 'reserved_response_count': 80, 'root': '/localhome/local-rohing/orch_r136_a100_classroom_support_20260916_attempt1/run1', 'schema': 'R167_A100_PARENT_CURSOR_HANDOFF_V1', 'started_sha256': 'a1daa7ebe13386ff0f5ad5c362a9e04d42207d17929f3f92b2afa85f24f06198'}, "bound_parent_resume")
    require(config["root"] == '/localhome/local-rohing/orch_r136_a100_classroom_support_20260916_attempt1/run1' and config["branch"] == 'a100_7_classroom_support' and config["programme"] == 'emotional_support', "same_parented_life")
    require(output.resolve() != Path('/data/home/rohing/dream-state-orch/research_notes/analysis/orch_r136_node1_20260916/parent7').resolve(), "new_parent_output_only")
    require(sha(Path('/data/home/rohing/dream-state-orch/research_notes/analysis/orch_r136_node1_20260916/parent7')/"STARTED.json") == 'a1daa7ebe13386ff0f5ad5c362a9e04d42207d17929f3f92b2afa85f24f06198', "preserved_predecessor_started")
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    write(output/'STARTED.json', dict(pid=os.getpid(), started_unix=time.time(), config_sha256=sha(config_path),
                                    model=STRONG, programme=config['programme'], branch=config['branch']))
    last_count = 80
    calls = 0
    while time.time() < config['hard_end_unix']:
        validate(config)
        state = snapshot(repository, config)
        record_deliveries(output, state)
        if state['response_count'] < max(1, last_count + config['cadence_responses']):
            if once:
                return
            time.sleep(5)
            continue
        last_count = state['response_count']
        directory = output/f'parent_{calls:06d}'
        directory.mkdir()
        calls += 1
        write(directory/'SOURCE.json', state)
        instruction, payload = prompt(config, state)
        (directory/'SYSTEM.txt').write_text(instruction)
        (directory/'PROMPT.txt').write_text(payload)
        receipt = dict(speaker='Astra', programme=config['programme'], branch=config['branch'],
                       source_response_count=last_count, source_head_sha256=state['head_sha256'],
                       started_unix=time.time(), status='MISSING', retry=False)
        try:
            response, model, usage = strong(payload, directory,
                min(config['hard_end_unix'], time.time()+120), instruction)
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

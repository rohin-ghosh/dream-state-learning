"""Language-native caption actions with synchronous, source-bound local feedback."""

from copy import deepcopy
import json
from pathlib import Path
import re
import socket
import unicodedata

from gpu import ny_caption_data as data
from gpu.orch_r125_stream_journal import _decode, _digest
from gpu.orch_r189_outcome_allocation import counts


POLICY = 'R210_LANGUAGE_NATIVE_CAPTION_BATCH_V1'
LIMIT = 262144
HELP = (
    'This is a humour contest: write funny captions or jokes for the cartoon scenes. '
    'A judge ranks each caption against 64 human captions from the same contest. '
    'This environment accepts captions, not Python. In ACT choose one numbered scene, a direction, '
    'and a guess count. Use plain lines: Scene: 1; Direction: your chosen approach; Count: 2; '
    'then one Caption: your literal caption per line. Put each field on its own line. '
    'The number of Caption lines must equal Count. Start with at most 10; later increase by at '
    'most twice your last count on that scene, up to 100. Each caption is at most 50 words. '
    'Do not copy opaque contest IDs. Feedback arrives before LEARN. Your objective is distinct '
    'accepted jokes over the token budget, not acceptance rate or one highest-scoring caption. '
    'The rank and relevance rule is provisional. No code will execute in this environment.'
)


def parse_batch(raw, scene_ids):
    data.require(isinstance(raw, str) and len(raw.encode()) <= 65536, 'bounded_ACT_text')
    fields, captions = {}, []
    for line in raw.splitlines():
        match = re.fullmatch(r'\s*([A-Za-z]+)\s*[:：][ \t]?(.*)', line)
        if match is None:
            continue
        name, value = match.group(1).lower(), match.group(2)
        if name == 'caption':
            captions.append(value)
        elif name in ('scene', 'direction', 'count'):
            data.require(name not in fields, 'duplicate_action_field')
            fields[name] = value
    data.require(set(fields) == {'scene', 'direction', 'count'}, 'missing_action_fields')
    scene = unicodedata.normalize('NFKC', fields['scene']).strip()
    count = unicodedata.normalize('NFKC', fields['count']).strip()
    data.require(re.fullmatch(r'[0-9]+', scene) and re.fullmatch(r'[0-9]+', count),
                 'numbered_scene_and_count_required')
    data.require(1 <= int(scene) <= len(scene_ids), 'unknown_numbered_scene')
    data.require(1 <= int(count) <= 100 and len(captions) == int(count), 'caption_count_mismatch')
    data.require(fields['direction'].strip() and len(fields['direction'].encode()) <= 2048,
                 'bounded_child_direction')
    data.require(all(caption.strip() and len(caption.split()) <= 50 and len(caption.encode()) <= 4096
                     for caption in captions), 'bounded_literal_captions')
    return dict(tool='caption_batch', contest_id=scene_ids[int(scene) - 1],
                direction=fields['direction'], count=int(count), captions=captions)


def extract_batch(raw, scene_ids):
    action, fault = None, None
    try:
        action = parse_batch(raw, scene_ids)
    except ValueError as error:
        fault = str(error)
    data.require(isinstance(raw, str) and len(raw.encode()) <= 65536, 'bounded_ACT_text')
    fields, candidates, unprefixed = {}, [], 0
    ambiguous_scene = False
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith('```'):
            continue
        match = re.fullmatch(r'\s*([A-Za-z]+)\s*[:：][ \t]?(.*)', line)
        name, value = (match.group(1).lower(), match.group(2)) if match else (None, line)
        if name in ('scene', 'direction', 'count'):
            if name == 'scene' and name in fields and fields[name] != value:
                ambiguous_scene = True
            fields[name] = value
        elif name == 'caption':
            candidates.append(value)
        elif name not in ('check', 'incorporation', 'explanation') and ('scene' in fields or candidates):
            candidates.append(line)
            unprefixed += 1
    if action is not None and not unprefixed:
        return action, dict(format_fault=False, recovered_count=action['count'], unprefixed_lines=0)
    scene = unicodedata.normalize('NFKC', fields.get('scene', '')).strip()
    diagnostics = dict(format_fault=True, strict_error=fault or 'additional_unprefixed_caption_lines', unprefixed_lines=unprefixed,
                       declared_count=fields.get('count'), recovered_count=len(candidates),
                       candidate_lines=candidates, caption_text_normalized=False)
    if ambiguous_scene or not re.fullmatch(r'[0-9]+', scene) or not 1 <= int(scene) <= len(scene_ids):
        return None, dict(diagnostics, unscored_reason='scene_not_unambiguously_identified')
    captions, unscored = [], []
    for ordinal, caption in enumerate(candidates, 1):
        if not caption.strip() or len(caption.split()) > 50 or len(caption.encode()) > 4096:
            unscored.append(dict(ordinal=ordinal, reason='caption_bounds', text=caption))
        elif len(captions) == 100:
            unscored.append(dict(ordinal=ordinal, reason='batch_bounds', text=caption))
        else:
            captions.append(caption)
    diagnostics.update(recovered_count=len(captions), unscored_lines=unscored)
    if not captions:
        return None, dict(diagnostics, unscored_reason='no_readable_bounded_caption_lines')
    return dict(tool='caption_batch', contest_id=scene_ids[int(scene) - 1],
                direction=fields.get('direction', '').strip()[:2048] or 'Direction not stated',
                count=len(captions), captions=captions), diagnostics


def child_act(life_root, origin):
    data.require(type(origin) is dict and set(origin) == {'kind', 'record_index', 'record_sha256'}
                 and origin['kind'] == 'TRAIN_CHILD_RESPONSE'
                 and type(origin['record_index']) is int and origin['record_index'] >= 0,
                 'explicit_child_RESPONSE_origin')
    records = Path(life_root) / 'stream' / 'records'

    def read(index):
        path = records / f'{index:020d}.json'
        data.require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 33554432,
                     'bounded_regular_journal_record')
        record = _decode(path.read_bytes())
        data.require(record['index'] == index and record['sha256'] ==
                     _digest({key: value for key, value in record.items() if key != 'sha256'}),
                     'journal_record_hash')
        return record

    record = read(origin['record_index'])
    data.require(record['kind'] == 'RESPONSE' and record['sha256'] == origin['record_sha256'],
                 'same_child_RESPONSE')
    source_sha = _digest(record['document'])
    previous, committed = record, False
    for index in range(record['index'] + 1, record['index'] + 33):
        current = read(index)
        data.require(current['journal_id'] == record['journal_id']
                     and current['previous_sha256'] == previous['sha256'], 'contiguous_child_stage_chain')
        document = current['document']
        if current['kind'] == 'COMMITTED':
            data.require(document['source_sha256'] == source_sha, 'same_committed_response')
            committed = True
        if current['kind'] == 'R184_STAGE':
            data.require(committed and document['stage'] == 'ACT'
                         and document['source_sha256'] == source_sha, 'committed_ACT_not_THINK_or_LEARN')
            return record['document']['response']['raw']
        data.require(current['kind'] not in ('REQUEST', 'RESPONSE'), 'no_other_generation_before_ACT')
        previous = current
    raise ValueError('ACT_commit_not_found')


def request(socket_path, origin, metrics):
    payload = data.canonical(dict(origin=origin, metrics=metrics)) + b'\n'
    data.require(len(payload) <= LIMIT, 'bounded_local_request')
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(120)
        connection.connect(str(socket_path))
        connection.sendall(payload)
        with connection.makefile('rb') as reader:
            raw = reader.readline(LIMIT + 1)
    data.require(raw.endswith(b'\n') and len(raw) <= LIMIT, 'bounded_local_reply')
    result = _decode(raw)
    data.require(result.get('policy') == POLICY and result.get('origin') == origin,
                 'same_origin_environment_reply')
    return result


def observed_counts(report):
    feedback = report.get('feedback', [])
    requested = report.get('requested_count', len(feedback))
    result = counts(requested=requested, not_dispatched=requested)
    for item in feedback:
        result['not_dispatched'] -= 1
        receipt = item.get('result', {})
        if not receipt.get('ok') or type(receipt.get('accepted')) is not bool:
            result['unknown'] += 1
        elif receipt.get('replayed'):
            result['cached'] += 1
        else:
            result['evaluated'] += 1
            result['quality_accepted'] += int(receipt['accepted'])
            result['successes'] += int(receipt.get('status') == 'new_pixel')
            result['repeats'] += int(receipt.get('status') == 'repeat')
    return counts(**result)


def activate(socket_path):
    from gpu import orch_r184_think_act_learn as stages
    from organism_v6.orch_r124_train_history import TrainEvent

    def act(self):
        self.cycle_phase = 'ACT'
        self.stream.history.append(stages.runtime_event(self.config['trial_id'], len(self.stream.rows),
                                                        'CAPTION_ACTION', HELP))
        generated = self.generate_stage('ACT')
        raw_act = self.stream.rows[-1]['target']
        try:
            result = request(socket_path, self.last_response, self.cycle_metrics)
            outcome = dict(status='PUBLISHED', executed=True, environment=result)
        except Exception as error:
            result = dict(policy=POLICY, origin=self.last_response,
                          report=dict(ok=False, error='ENVIRONMENT_OUTCOME_UNKNOWN_NO_RETRY',
                                      error_type=type(error).__name__, feedback=[]))
            outcome = dict(status='ENVIRONMENT_OUTCOME_UNKNOWN_NO_RETRY', executed=None, environment=result)
        text = json.dumps(result, ensure_ascii=False, sort_keys=True)
        self.stream.history.append(TrainEvent(event_id='caption:' + self.last_response['record_sha256'],
            actor='environment', text=text, split='TRAIN', phase='feedback', episode_id='caption_development',
            source_id='runtime:' + POLICY, source_sha256=stages.digest(result), origin='TRAIN_COLLECTION'))
        self.last_act_evidence = dict(act_source_sha256=generated['source_sha256'],
                                     response_origin=deepcopy(self.last_response), outcome=deepcopy(outcome))
        self.journal.record('R184_ACT', dict(schema=stages.SCHEMA, segment=generated['segment'],
            source_sha256=generated['source_sha256'], origin=self.last_response, outcome=outcome))
        if self.allocation is not None:
            self.outcome_reader = lambda origin, unused: dict(observation=observed_counts(result['report']),
                                                               receipt=result.get('receipt_sha256', stages.digest(result)))
            self.record_outcome(outcome, dispatched=outcome['executed'] is True)
        self.cycle_phase = 'FEEDBACK_COMPLETE_OR_EXPLICIT_UNKNOWN'
        self.record_corrections(outcome, raw_act)
        if self.dataset is not None:
            self.export_stage(*self.last_stage_export, outcome=outcome, committed=True)
        return outcome

    stages.ThinkActLearn.act = act

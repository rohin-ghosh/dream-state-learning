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
from research_loop.workers.rohin221_continuous_caption_20260918.freeform import (
    FORMAT_POLICY, extract_batch, extract_batches,
)


POLICY = 'R210_LANGUAGE_NATIVE_CAPTION_BATCH_V1'
LIMIT = 262144
HELP = (
    'This is a humour contest: write funny captions or jokes for the cartoon scenes. '
    'A judge ranks each caption against 64 human captions from the same contest. '
    'Use freeform language: name or number the scene for each actual caption. Multiple scenes and '
    'ordinary questions are welcome. JSON, Direction, Count and Caption fields are NOT required; '
    'there is no fixed number of guesses. Unparsed lines receive clarification, not a life stop. '
    'Explicit candidates from your own latest committed THINK may be salvaged when ACT is unclear, '
    'with the actual THINK source recorded. Each caption is at most50 words and a response '
    'at most100 candidates. Internal scorer chunking retains all validated candidates; '
    'your caption count is not rejected for exceeding a previous count. '
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


def _child_stage(life_root, origin, expected_stage):
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
            data.require(committed and document['stage'] == expected_stage
                         and document['source_sha256'] == source_sha, 'committed_ACT_not_THINK_or_LEARN')
            return record['document']['response']['raw']
        data.require(current['kind'] not in ('REQUEST', 'RESPONSE'), 'no_other_generation_before_ACT')
        previous = current
    raise ValueError('ACT_commit_not_found')


def child_act(life_root, origin):
    return _child_stage(life_root, origin, 'ACT')


def latest_own_think(life_root, act_origin):
    child_act(life_root, act_origin)
    records = Path(life_root) / 'stream' / 'records'

    def read(index):
        path = records / f'{index:020d}.json'
        data.require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 33554432,
                     'bounded_regular_journal_record')
        record = _decode(path.read_bytes())
        data.require(record['index'] == index and record['sha256'] ==
                     _digest({key:value for key,value in record.items() if key != 'sha256'}), 'journal_record_hash')
        return record

    anchor = read(act_origin['record_index'])
    data.require(anchor['sha256'] == act_origin['record_sha256'], 'same_ACT_anchor')
    previous, source, stage_index = anchor, None, None
    for index in range(anchor['index'] - 1, max(-1, anchor['index'] - 257), -1):
        record = read(index)
        data.require(record['journal_id'] == anchor['journal_id'] and
                     previous['previous_sha256'] == record['sha256'], 'same_life_contiguous_THINK_ancestry')
        if record['kind'] in ('LOADED', 'SLEEP_COMPLETE', 'R184_LEARN_COMPLETE', 'TERMINAL'):
            return None
        if record['kind'] == 'R184_STAGE':
            if record['document'].get('stage') != 'THINK' or source is not None:
                return None
            source, stage_index = record['document']['source_sha256'], index
        if source is not None and record['kind'] == 'RESPONSE':
            data.require(stage_index-index <= 32 and _digest(record['document']) == source,
                         'same_latest_THINK_response')
            origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=index, record_sha256=record['sha256'])
            return dict(raw=_child_stage(life_root, origin, 'THINK'), origin=origin, stage='THINK',
                        source_sha256=source, journal_id=record['journal_id'])
        previous = record
    return None


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


def caption_feedback_payload(result):
    report = result.get('report', {})
    origin = result.get('origin', {})
    sources = report.get('caption_sources', [])
    observations = []
    for position, entry in enumerate(report.get('feedback', []), 1):
        returned = entry.get('result', {})
        index = entry.get('caption_source_index')
        source = sources[index] if type(index) is int and 0 <= index < len(sources) else {}
        observation = dict(item=position, source_stage=source.get('stage', 'ACT'),
            source_span={key:source[key] for key in ('start','end','line') if key in source},
            text_digest=source.get('text_sha256'),
            **{key:deepcopy(returned[key]) for key in ('ok','rank','reference_count','top_k',
                'accepted','status','replayed','rejection_reason','relevance_score','relevance_threshold',
                'pixel_id','raw_score','q') if key in returned})
        observations.append(observation)
    metrics = report.get('format_metrics', {})
    if metrics.get('no_caption_act'):
        clarification = ('No caption found in your output—write the captions themselves, one per line, '
                         'for the scene you choose. This is a suggestion, not a required format.')
    elif metrics.get('ambiguous_caption_lines'):
        clarification = 'The scorer could not identify the scene for some candidate lines. Clarify the scene in a new ACT; no fixed format or count is required.'
    elif metrics.get('clarification_needed'):
        clarification = 'The scorer reports unparsed lines and requests clarification. Already-scored results remain unchanged.'
    else:
        clarification = None
    return dict(kind='caption game feedback; observed data, not runtime control',
        response_record=origin.get('record_index'), response_digest=origin.get('record_sha256'),
        scorer_receipt=result.get('receipt_sha256'), raw_result_retained=True,
        raw_result_location='Original native action outcome and scorer result receipt',
        ok=report.get('ok'), error=str(report['error']).replace('_',' ') if report.get('error') else None,
        observations=observations, clarification=clarification,
        format_status={key:metrics[key] for key in ('format_fault','no_caption_act','ambiguous_caption_lines',
            'unparsed_line_count','recovered_count','salvaged_THINK_count') if key in metrics},
        requested_candidates=report.get('requested_count'), not_dispatched=report.get('not_dispatched_count'),
        projection='Per-caption outcomes and provenance digests; raw scaffolding, transport paths and caption echoes are not repeated here.')


def attributed_tool_feedback(result):
    return 'Tool: ' + json.dumps(caption_feedback_payload(result), ensure_ascii=False, sort_keys=True)


def activate(socket_path, *, max_act_attempts=3):
    from gpu import orch_r184_think_act_learn as stages
    from organism_v6.orch_r124_train_history import TrainEvent
    data.require(type(max_act_attempts) is int and 1 <= max_act_attempts <= 3, 'bounded_ACT_repair_allowance')

    def act_attempt(self, charged_metrics):
        self.cycle_phase = 'ACT'
        self.stream.history.append(stages.runtime_event(self.config['trial_id'], len(self.stream.rows),
                                                        'CAPTION_ACTION', HELP))
        generated = self.generate_stage('ACT')
        raw_act = self.stream.rows[-1]['target']
        try:
            metrics = {key:self.cycle_metrics[key] - charged_metrics[key] for key in self.cycle_metrics}
            result = request(socket_path, self.last_response, metrics)
            outcome = dict(status='PUBLISHED', executed=True, environment=result)
        except Exception as error:
            result = dict(policy=POLICY, origin=self.last_response,
                          report=dict(ok=False, error='ENVIRONMENT_OUTCOME_UNKNOWN_NO_RETRY',
                                      error_type=type(error).__name__, feedback=[]))
            outcome = dict(status='ENVIRONMENT_OUTCOME_UNKNOWN_NO_RETRY', executed=None, environment=result)
        text = attributed_tool_feedback(result)
        self.stream.history.append(TrainEvent(event_id='caption:' + self.last_response['record_sha256'],
            actor='environment', text=text, split='TRAIN', phase='feedback', episode_id='caption_development',
            source_id='runtime:' + POLICY, source_sha256=stages.digest(result), origin='TRAIN_COLLECTION'))
        self.last_act_evidence = dict(act_source_sha256=generated['source_sha256'],
                                     response_origin=deepcopy(self.last_response), outcome=deepcopy(outcome))
        self.journal.record('R184_ACT', dict(schema=stages.SCHEMA, segment=generated['segment'],
            source_sha256=generated['source_sha256'], origin=self.last_response, outcome=outcome,
            feedback_view=dict(schema='R227_ATTRIBUTED_CAPTION_TOOL_FEEDBACK_V1',
                text_sha256=stages.digest(text), raw_result_sha256=stages.digest(result),
                original_raw_result_preserved=True, view_is_not_a_training_target=True)))
        self.cycle_phase = 'FEEDBACK_COMPLETE_OR_EXPLICIT_UNKNOWN'
        if self.dataset is not None:
            self.export_stage(*self.last_stage_export, outcome=outcome, committed=True)
        return outcome, raw_act

    def act(self):
        charged_metrics = {key:0 for key in self.cycle_metrics}
        attempts, aggregate = [], counts()
        for ordinal in range(1, max_act_attempts + 1):
            outcome, raw_act = act_attempt(self, charged_metrics)
            charged_metrics = dict(self.cycle_metrics)
            result = outcome['environment']
            observed = observed_counts(result['report'])
            aggregate = {key:aggregate[key] + observed[key] for key in aggregate}
            attempts.append(dict(attempt=ordinal, origin=deepcopy(self.last_response),
                status=outcome['status'], receipt_sha256=result.get('receipt_sha256'),
                next_stage=result['report'].get('next_stage')))
            if outcome['executed'] is not True or result['report'].get('next_stage') != 'ACT':
                break
        self.journal.record('R223_CAPTION_OPPORTUNITY', dict(attempts=attempts,
            max_act_attempts=max_act_attempts, token_metrics=dict(self.cycle_metrics),
            observation=aggregate, clarification_exhausted=attempts[-1]['next_stage'] == 'ACT',
            life_continues=True, no_historical_resubmission=True))
        if self.allocation is not None:
            self.outcome_reader = lambda origin, unused: dict(observation=aggregate, receipt=stages.digest(attempts))
            self.record_outcome(outcome, dispatched=any(item['status'] == 'PUBLISHED' for item in attempts))
        self.record_corrections(outcome, raw_act)
        return outcome

    stages.ThinkActLearn.act = act

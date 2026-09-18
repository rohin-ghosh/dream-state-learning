"""Project existing C0 reading observations into explicit public metadata only."""

import argparse
import hashlib
import json
from pathlib import Path


def select(document, names):
    return {name: document[name] for name in names if name in document}


def turn(document):
    result = select(document, ('number', 'action', 'excerpt', 'step', 'after_cycle',
        'created_utc', 'published_utc', 'operator_authored', 'text_sha256'))
    if 'render' in document:
        result['render'] = (select(document['render'], ('index', 'sha256', 'started_utc', 'prompt_tokens',
            'all_history_tokens_masked', 'story_verbatim_in_request', 'adapter_memory_claim',
            'explicit_context_carryover_not_controlled')) if document['render'] is not None else None)
    if document.get('publication') is not None:
        result['publication'] = select(document['publication'], ('id', 'sha256'))
    return result


def project(observation):
    service = observation['service']
    result = dict(schema='R226_C0_READING_PUBLIC_OBSERVATION_V1', observed_utc=observation['observed_utc'],
        service=select(service, ('pid', 'start_ticks', 'started_utc', 'deadline_unix', 'baseline_sha256',
            'protocol_sha256', 'source_sha256', 'sleep_spacing', 'first_reading_after_completed_cycle',
            'memory', 'original_math_parent_kept', 'signals', 'model_calls', 'grading', 'child_history_modified')),
        state=select(observation['state'], ('completed_cycle', 'excerpt', 'step', 'next_reading_after_cycle',
            'last_publication_cycle', 'memory_after_cycle', 'publications', 'record_cursor', 'retry_reason')),
        identities=[select(item, ('pid', 'state', 'start_ticks')) for item in observation['identities']],
        publications=[turn(item['document']) for item in observation['publications']],
        turns=[], cycles=[], raw_child_text_published=False, story_or_answer_in_memory_prompt=False,
        private_observation_sha256=hashlib.sha256(json.dumps(observation, sort_keys=True,
            separators=(',', ':'), allow_nan=False).encode()).hexdigest(), adapter_retention_claim=False,
        failure_receipts_present=bool(observation['failures']))
    if observation['state'].get('pending'):
        result['state']['pending'] = turn(observation['state']['pending'])
    for item in observation['turns']:
        document = item['document']
        result['turns'].append(dict(pending=turn(document['pending']),
            actual_response=select(document['actual_response'], ('index', 'sha256', 'finished_utc', 'awake_cycle')),
            stage_index=document['stage_index'], stage_sha256=document['stage_sha256'],
            fulfilled=document['fulfilled'], interpretation=document['interpretation']))
    for item in observation['cycles']:
        document = item['document']
        row = select(document, ('cycle', 'sleep_complete_index', 'sleep_complete_sha256',
            'configured_objects', 'reading_rendered', 'actual_object_not_inferred_from_schedule'))
        row['events'] = [select(event, ('kind', 'index', 'sha256', 'raw_sha256', 'actual_object', 'action',
            'started_utc', 'prompt_tokens', 'all_history_tokens_masked', 'story_verbatim_in_request',
            'adapter_memory_claim', 'explicit_context_carryover_not_controlled')) for event in document['events']]
        result['cycles'].append(row)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = project(json.loads(args.input.read_bytes()))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')

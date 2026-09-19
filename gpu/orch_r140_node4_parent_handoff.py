"""Raw3 parent-only English phase handoff; never signal a native child."""

import argparse
from copy import deepcopy
from pathlib import Path

from gpu import orch_r136_node4_parent as adapter
from gpu import orch_r137_parent_latency_handoff as idle


def reservation(output, config):
    idle.require(config.get('physical') == 3 and config.get('node') == 'a40r'
        and config.get('schedule_on', 'response') == 'response', 'raw3_response_clock_only')
    cursor = config.get('start_after_response_count', 0)
    receipts = []
    for directory in sorted(Path(output).glob('parent_*')):
        idle.require(directory.is_dir() and not directory.is_symlink(), 'regular_call_directory')
        source_path, result_path = directory / 'SOURCE.json', directory / 'RESULT.json'
        idle.require(source_path.is_file() and result_path.is_file(), 'unfinished_parent_call')
        source, result = idle.read(source_path), idle.read(result_path)
        count = source['response_count']
        idle.require(type(count) is int and count >= cursor + config['cadence_responses'], 'strict_sparse_source_reservations')
        idle.require(result.get('schedule_on', 'response') == 'response'
            and result.get('source_response_count') == count
            and result.get('schedule_count', count) == count
            and result.get('source_head_sha256') == source['head_sha256'], 'result_matches_source_reservation')
        idle.require(result.get('branch') == config['branch'] and result.get('programme') == config['programme'], 'same_parent_result')
        idle.require(result.get('status') in ('PUBLISHED', 'SILENT', 'MISSING')
            and result.get('finished_unix', 0) >= result.get('started_unix', float('inf')), 'terminal_result_required')
        if result['status'] == 'PUBLISHED':
            idle.require(bool(result.get('inbox_publication')), 'published_receipt_required')
        cursor = count
        receipts.append(dict(directory=str(directory), response_count=count, status=result['status'],
            source_sha256=idle.sha(source_path), result_sha256=idle.sha(result_path)))
    return dict(response_cursor=cursor, receipts=receipts)


def successor_config(spec, state):
    config = deepcopy(idle.read(spec['old_config']))
    idle.require(config.get('physical') == 3 and config.get('node') == 'a40r'
        and config.get('cadence_responses') == 3 and config.get('cadence_label') == 'SPARSE'
        and config.get('parent_style') == 'Socratic', 'unchanged_raw3_sparse3_programme')
    config.update(programme_path=spec['english_programme_path'], programme_sha256=spec['english_programme_sha256'],
        parent_language='English', language_phase='R140_RAW3_ENGLISH_PARENT_V1',
        start_after_response_count=state['response_cursor'], predecessor_output=spec['old_output'],
        predecessor_started_sha256=spec['old_started_sha256'])
    return adapter.validate(config)


def handoff(spec):
    old = idle.read(spec['old_config'])
    adapter.validate(old)
    idle.require(old.get('physical') == 3 and old.get('node') == 'a40r', 'only_raw3_parent_handoff')
    idle.require(spec.get('idle_wait_seconds', 90) <= 180, 'bounded_parent_idle_wait')
    idle.require(idle.sha(spec['english_programme_path']) == spec['english_programme_sha256'], 'pinned_English_programme')
    prior = idle.MODULE, idle.reservation, idle.successor_config
    idle.MODULE = 'gpu.orch_r136_node4_parent'
    idle.reservation = reservation
    idle.successor_config = successor_config
    try:
        return idle.handoff(spec)
    finally:
        idle.MODULE, idle.reservation, idle.successor_config = prior


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True)
    options = parser.parse_args()
    handoff(idle.read(options.spec))

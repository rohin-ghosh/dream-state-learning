"""R210 source-bound THINK exchange, with no imported training targets."""

import hashlib
import json
from pathlib import Path


ROOT = Path('/localhome/local-rohing/orch_r205_node3_20260918')
GROUPS = {'peer_math': ('peer_repo',), 'peer_repo': ('peer_math',),
    'p32': ('lr03', 'lr3'), 'lr03': ('p32', 'lr3'), 'lr3': ('p32', 'lr03')}


def capsule(sender, record, response):
    if sender not in GROUPS or record['kind'] != 'R184_ACT' or response['kind'] != 'RESPONSE':
        raise ValueError('actual_named_peer_ACT_and_RESPONSE_required')
    for item in (record, response):
        canonical = json.dumps({key: value for key, value in item.items() if key != 'sha256'},
            sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
        if hashlib.sha256(canonical).hexdigest() != item['sha256']:
            raise ValueError('actual_peer_record_hash')
    origin = record['document']['origin']
    if origin['record_index'] != response['index'] or origin['record_sha256'] != response['sha256']:
        raise ValueError('ACT_response_origin_binding')
    text = ('R210 peer context from ' + sender + '. This is the peer\'s actual authored output, '
        'not your verified result, a parent instruction, or an execution receipt. '
        'The recorded tool outcome is ' + record['document']['outcome']['status'] + '.\n\n'
        + response['document']['response']['raw']
        + '\n\nDuring THINK, predict what might transfer to your different working object and '
        'check a concrete case honestly. No executor is connected. Only your own eligible restatement '
        'may train; this entire peer input is masked context. Do not treat a peer assertion as a tool result.')
    if len(text.encode()) > 6000:
        raise ValueError('peer_context_exceeds_bound_no_truncation')
    return text


def receive_group(driver):
    from gpu.orch_r127_pilot_console import _inbox
    from gpu.r209_node3_audit import metadata, read_record
    receiver = Path(driver.child.plan['source_root']).parents[1].name
    if receiver not in GROUPS:
        return None
    seen = getattr(driver, '_r210_peer_seen', set())
    for sender in GROUPS[receiver]:
        arm = ROOT / sender
        boundary = arm / 'r210_enrichment/PRESERVED_COMPLETE.json'
        if not boundary.exists():
            continue
        first = json.loads(boundary.read_bytes())['complete_index']
        paths = sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))
        path = next((path for path in reversed(paths) if int(path.stem) > first and metadata(path) == 'R184_ACT'), None)
        if path is None:
            continue
        record = read_record(path)
        if record['sha256'] in seen:
            continue
        origin = record['document']['origin']
        response_path = arm / 'raw/stream/records' / f'{origin["record_index"]:020d}.json'
        response = read_record(response_path)
        try:
            text = capsule(sender, record, response)
        except ValueError as error:
            if str(error) == 'peer_context_exceeds_bound_no_truncation':
                continue
            raise
        publication = _inbox(Path(driver.child.plan['root']), 'Tool', text,
            dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        seen.add(record['sha256'])
        driver._r210_peer_seen = seen
        return dict(sender=sender, receiver=receiver, source_record_sha256=record['sha256'],
            response_record_sha256=response['sha256'], publication=publication, text=text,
            imported_training_rows=0, phase='R210_PARENTED_COMPLEMENTARY_EXPERIENCE')
    return None


def main():
    from gpu import r205_runtime as runtime
    original_install = runtime.install_runtime

    def install_resume(plan):
        from gpu import orch_r184_think_act_learn as driver
        original_loop = driver.run_loop
        original_install(plan)
        driver.run_loop = original_loop
        runtime.receive_peer = receive_group

    runtime.MODULE = 'gpu.r210_node3_runtime'
    runtime.install_runtime = install_resume
    runtime.main()


if __name__ == '__main__':
    main()

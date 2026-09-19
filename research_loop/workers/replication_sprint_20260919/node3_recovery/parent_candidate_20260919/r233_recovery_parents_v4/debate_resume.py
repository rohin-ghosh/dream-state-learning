"""Resume the frozen debate with authenticated, already-published parent turns."""

import argparse
import importlib
import json
import os
from pathlib import Path
import sys

from retirement import save, sha


MODULE_SHA = '2c1722b0b0603469625e39559bff2e1e32d1fbc0e8df0209ac70c5214ea6d4c6'


def pending_parents(module, root, directory, upper, divisor, exchange):
    expected = {'parents/' + name + suffix for name in module.MEMBERS
        for suffix in ('.json', '.intent.json')}
    actual = {str(path.relative_to(directory)) for path in directory.rglob('*') if path.is_file()}
    if actual and actual != expected:
        raise ValueError('only_complete_previously_published_parent_pairs_supported')
    receipts = {}
    for name in module.MEMBERS if actual else ():
        intent_path = directory / 'parents' / (name + '.intent.json')
        publication_path = directory / 'parents' / (name + '.json')
        intent = json.loads(intent_path.read_bytes())
        publication = json.loads(publication_path.read_bytes())
        text = module.prompt(name, upper, divisor, exchange)
        inbox_path = root / name / 'raw/stream/inbox' / (publication['id'] + '.json')
        if (intent != dict(life=name, text=text) or publication['text'] != text
                or Path(publication['path']).resolve() != inbox_path.resolve()
                or sha(inbox_path) != publication['sha256']):
            raise ValueError('pending_parent_identity_and_source_must_match')
        inbox = json.loads(inbox_path.read_bytes())
        if inbox['speaker'] != 'Astra' or inbox['text'] != text or inbox['id'] != publication['id']:
            raise ValueError('exact_Astra_parent_not_human_or_peer')
        receipts[name] = dict(id=publication['id'], sha256=publication['sha256'],
            publication_sha256=sha(publication_path), intent_sha256=sha(intent_path))
    return receipts


def resume_exchange(module, root, result_path):
    result = json.loads(result_path.read_bytes())
    phase = int(result_path.parent.parent.name.removeprefix('phase_'))
    exchange = int(result_path.parent.name.removeprefix('exchange_'))
    if not 1 <= exchange < module.MAX_EXCHANGES or set(result['replies']) != set(module.MEMBERS):
        raise ValueError('completed_bounded_exchange_required')
    if result['resolution']['status'] != 'UNRESOLVED':
        raise ValueError('resume_only_unresolved_exchange')
    floors = {}
    for name, reply in result['replies'].items():
        records = root / name / 'raw/stream/records'
        response = module.read_record(records / f"{reply['response']['index']:020d}.json")
        act = module.read_record(records / f"{reply['act']['index']:020d}.json")
        origin = act['document']['origin']
        if (module.reference(response) != reply['response'] or module.reference(act) != reply['act']
                or response['kind'] != 'RESPONSE' or act['kind'] != 'R184_ACT'
                or response['document']['response']['raw'] != reply['raw']
                or origin['kind'] != 'TRAIN_CHILD_RESPONSE'
                or origin['record_index'] != response['index'] or origin['record_sha256'] != response['sha256']):
            raise ValueError('source_bound_completed_exchange_required')
        floors[name] = act['index']
    pending = pending_parents(module, root, result_path.parent.parent / f'exchange_{exchange + 1}',
        result['upper'], result['divisor'], exchange + 1)
    return dict(phase=phase, exchange=exchange + 1, upper=result['upper'], divisor=result['divisor'],
        floors=floors, previous_result_sha256=sha(result_path), reused_parent_receipts=pending)


def run(root, output, initial, result):
    source = root / 'r231_math_operator_v2'
    if sha(source / 'r229_math_parents.py') != MODULE_SHA:
        raise ValueError('exact_frozen_debate_source_required')
    previous = json.loads((output / 'STARTED.json').read_bytes())
    if Path('/proc', str(previous['pid'])).exists():
        raise ValueError('old_debate_cpu_must_be_absent')
    sys.path[:0] = [str(source), str(root)]
    module = importlib.import_module('r229_math_parents')
    module.resume_exchange = lambda current_root, path: resume_exchange(module, current_root, path)
    original_save = module.save

    def preserved_save(path, document):
        if path == output / 'STARTED.json':
            path = output / 'attachments' / (str(os.getpid()) + '.json')
            document = dict(document, adapter_sha256=sha(Path(__file__)),
                original_started_sha256=sha(output / 'STARTED.json'), provider_requests=0)
        return original_save(path, document)

    module.save = preserved_save
    module.run(root, output, initial, result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('root', 'output', 'initial', 'result'):
        parser.add_argument('--' + name, required=True, type=Path)
    options = parser.parse_args()
    run(options.root, options.output, options.initial, options.result)

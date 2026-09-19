"""One bounded read-only collection of five already-running source epochs."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
WORKERS = HERE.parent
REPO = HERE.parents[2]
OBSERVER = WORKERS / 'post_recovery_correction_hourly_20260918'
CUTOFF = datetime(2026, 9, 19, 1, 39, 59, tzinfo=timezone.utc).timestamp()


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, document):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix(path.suffix + '.next')
    temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    temporary.replace(path)


def configuration():
    config_path = OBSERVER / 'private/CONFIG.json'
    bindings = {item['label']: item['binding'] for item in read(config_path)['entries'] if 'binding' in item}
    entries = []
    pair = WORKERS / 'post_reboot_pair_parents_20260919'
    for arm, label in [('learner', 'FRESH_R231'), ('frozen', 'R232_SIBLING_FROZEN')]:
        state_path = pair / 'private' / arm / 'STATE.json'
        state = read(state_path)
        deliveries = state['deliveries'][:3]
        entries.append(dict(label=arm, binding=bindings[label], after=deliveries[0]['inbox']['index'] - 1,
            maximum=275 if arm == 'learner' else 165,
            publications=[item['receipt']['publication'] for item in deliveries],
            owner_evidence=dict(path=str(state_path), sha256=sha(state_path))))
    related = WORKERS / 'post_reboot_c2_p7_20260919'
    c2_receipt = read(related / 'C2_DELIVERY.json')
    c2_paths = [related / 'c2_session1/parent' / ('parent_' + str(number).zfill(6)) / 'RESULT.json' for number in (2, 3, 4)]
    entries.append(dict(label='C2', binding=bindings['C2'], after=c2_receipt['inbox']['index'] - 1, maximum=275,
        publications=[c2_receipt['publication']] + [read(path)['inbox_publication'] for path in c2_paths],
        owner_evidence=[dict(path=str(path), sha256=sha(path)) for path in c2_paths]))
    p3_path = WORKERS / 'post_reboot_p3_parent_20260919/FRESH_PROVIDER_REQUEST_ACT.json'
    p3 = read(p3_path)['row']
    entries.append(dict(label='P3', binding=bindings['GAME1_P3'], after=p3['chain']['source_anchor_index'], maximum=165,
        publications=[dict(id=p3['publication_id'], sha256=p3['publication_sha256'])],
        owner_evidence=dict(path=str(p3_path), sha256=sha(p3_path))))
    old_p7_path = WORKERS / 'rohin233_recovery_node4_20260918/P7_CONTINUATION_STATUS.json'
    old_p7 = read(old_p7_path)
    p7_receipt = read(related / 'P7_MODEL_DELIVERY_373151.json')
    p7_paths = sorted((related / 'p7').glob('turn_*/NEXT.json'))[1:4]
    p7_binding = dict(pid=old_p7['native']['pid'], start_ticks=old_p7['native']['start_ticks'],
        source=old_p7['source_root'], root=old_p7['root'], guard_sha256=old_p7['guard_sha256'],
        journal_id=old_p7['journal_id'], loaded_index=old_p7['loaded']['index'],
        loaded_sha256=old_p7['loaded']['sha256'], until_unix=old_p7['hard_end_unix'],
        boot_id=bindings['GAME1_P3']['boot_id'], wrapper='a40r_ssh.sh', owner_receipt_sha256=sha(old_p7_path))
    entries.append(dict(label='P7', binding=p7_binding, after=p7_receipt['inbox']['index'] - 1, maximum=240,
        publications=[read(path)['publication'] for path in p7_paths],
        owner_evidence=[dict(path=str(path), sha256=sha(path)) for path in p7_paths]))
    return dict(cutoff_unix=CUTOFF, binding_config_sha256=sha(config_path), entries=entries)


def collect_one(entry, code):
    invocation = code + '\nprint(json.dumps(project(' + ','.join(repr(value) for value in
        (entry['binding'], entry['publications'], entry['after'], entry['maximum'], CUTOFF)) + '),ensure_ascii=False))\n'
    result = subprocess.run(['bash', str(REPO / 'gpu' / entry['binding']['wrapper']),
        'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B -'],
        input=invocation, text=True, capture_output=True, timeout=180)
    if result.returncode:
        save(HERE / (entry['label'] + '_ERROR.json'), dict(returncode=result.returncode,
            stderr_sha256=hashlib.sha256(result.stderr.encode()).hexdigest(),
            error_type=result.stderr.strip().splitlines()[-1].split(':', 1)[0] if result.stderr.strip() else 'NO_STDERR'))
        return dict(label=entry['label'], status='READ_FAILED_NO_SEMANTIC_GRADE')
    document = json.loads(result.stdout)
    save(HERE / 'evidence' / (entry['label'] + '.json'), document)
    return dict(label=entry['label'], status='BOUNDED_EVIDENCE_READY', frames=len(document['frames']),
        ACTs=sum(frame['stage'] == 'ACT' for frame in document['frames']), bytes_read=document['bytes_read'])


def main():
    os.umask(0o077)
    config = configuration()
    save(HERE / 'CONFIG.json', config)
    sources = [OBSERVER / 'contract/reader.py', OBSERVER / 'contract/audit.py', OBSERVER / 'remote.py', HERE / 'project.py']
    save(HERE / 'SOURCE_PINS.json', {str(path): sha(path) for path in sources})
    code = '\n'.join(path.read_text() for path in sources)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda entry: collect_one(entry, code), config['entries']))
    save(HERE / 'COLLECTION.json', results)
    print(json.dumps(results))


if __name__ == '__main__':
    main()

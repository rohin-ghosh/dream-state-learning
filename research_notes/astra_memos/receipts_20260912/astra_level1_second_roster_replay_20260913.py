import hashlib
import importlib.util
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import sys
import tarfile
import time


BASE = Path('/tmp/astra_level1_second_scores_20260913')
REPLAY = BASE / 'scorer_replay'
REPORT = Path('/tmp/astra_level1_second_roster_analysis_20260913.json')
REPORT_PIN = '106568ff148ce44d90b79c357c2078931a1a793aaf5938121021befaf4e34eea'
DEADLINE_SECONDS = 165


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    checksum = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            checksum.update(block)
    return checksum.hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stage(path, raw):
    if path.exists():
        require(path.read_bytes() == raw, 'staged source differs: ' + str(path))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)


def main():
    started = time.monotonic()
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU-only environment required')
    require(os.environ.get('ASTRA_LEVEL1_SOURCE_ROOT') == str(REPLAY / 'sources'), 'explicit archived source root required')
    require(digest(REPORT) == REPORT_PIN, 'pre-replay analysis pin differs')
    REPLAY.mkdir()
    report = json.loads(REPORT.read_bytes())
    receipt = dict(sequence='SEQ146', status='RUNNING', started_utc=datetime.now(timezone.utc).isoformat(),
                   analysis_before_replay_sha256=REPORT_PIN, protocol='exact archived material.score_row(row, response[text], response[finish_reason])',
                   native_collection_invoked=False, generation_invoked=False, dataset_regenerated=False,
                   scorer_bytes_modified=False, cells=[], scorer_sources={}, mismatches=[])
    modules = {}
    rows_replayed = 0
    try:
        for archive_key, archive_info in report['archives'].items():
            archive_path = Path(archive_info['archive_path'])
            require(digest(archive_path) == archive_info['archive_sha256'], 'archive changed')
            manifest_path = archive_path.parent / (archive_key.split('_')[0] + '_archive_manifest.json')
            require(digest(manifest_path) == archive_info['manifest_sha256'], 'manifest changed')
            manifest = json.loads(manifest_path.read_bytes())
            with tarfile.open(archive_path, 'r:') as archive:
                def payload(name, expected=None):
                    member = archive.getmember(name)
                    require(member.isfile() and name in manifest['files'], 'unmanifested payload')
                    raw = archive.extractfile(member).read()
                    pin = manifest['files'][name]
                    require(len(raw) == pin['bytes'] and sha(raw) == pin['sha256'], 'payload changed')
                    require(expected is None or sha(raw) == expected, 'bound payload pin differs')
                    return raw

                for evidence in manifest['cells']:
                    root = evidence['root'].lstrip('/')
                    plan = json.loads(payload(root + '/plan.json', evidence['plan_sha256']))
                    material_raw = payload(root + '/material.json', plan['input_hashes']['material.json'])
                    dataset = json.loads(material_raw)
                    saved = json.loads(payload(root + '_collected/scores.json', evidence['scores_sha256']))
                    calls = json.loads(payload(root + '/calls.json', plan['input_hashes']['calls.json']))
                    call_map = {call['call_id']: call for call in calls}
                    scorer_spec = plan['specification']['material']
                    scorer_raw = payload(scorer_spec['path'].lstrip('/'), scorer_spec['sha256'])
                    scorer_path = REPLAY / 'modules' / (scorer_spec['sha256'] + '.py')
                    stage(scorer_path, scorer_raw)
                    dependencies = {}
                    for relative, expected in plan['specification']['source_files'].items():
                        if relative.endswith('/train_adapter_v3.py'):
                            continue
                        raw = payload((Path(plan['source']) / relative).as_posix().lstrip('/'), expected)
                        stage(REPLAY / 'sources' / relative, raw)
                        dependencies[relative] = expected
                    receipt['scorer_sources'][scorer_spec['sha256']] = dict(native_path=scorer_spec['path'], staged_path=str(scorer_path), dependencies=dependencies)
                    if scorer_spec['sha256'] not in modules:
                        spec = importlib.util.spec_from_file_location('archived_scorer_' + scorer_spec['sha256'], scorer_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        modules[scorer_spec['sha256']] = module
                    module = modules[scorer_spec['sha256']]
                    cell = dict(name=evidence['name'], node=evidence['node'], root=evidence['root'],
                                scores_sha256=evidence['scores_sha256'], material_sha256=sha(material_raw),
                                scorer_sha256=scorer_spec['sha256'], panels={}, rows=[])
                    for state in ('OFF', 'post'):
                        cell['panels'][state] = {}
                        for panel in ('held', 'canary'):
                            saved_panel = saved['cells'][state][panel]
                            saved_rows = {row['row_id']: row for row in saved_panel['rows']}
                            require(len(saved_rows) == len(dataset['evaluation'][panel]) == saved_panel['total'], 'row count mismatch')
                            scores = []
                            for index, row in enumerate(dataset['evaluation'][panel]):
                                require(time.monotonic() - started < DEADLINE_SECONDS, 'local replay deadline exceeded')
                                call_id = f'{panel}_{index:02d}'
                                call = call_map[call_id]
                                require(call['row_id'] == row['row_id'] and call['messages'] == row['input_messages'] and call['panel'] == panel, 'call/material binding mismatch')
                                saved_row = saved_rows[row['row_id']]
                                response_raw = payload(root + f'/run/{state}/{call_id}.response.json', saved_row['response_sha256'])
                                response = json.loads(response_raw)
                                require(response['text'] == saved_row['raw'] and response['finish_reason'] == saved_row['finish_reason'], 'saved score/raw response mismatch')
                                fresh = module.score_row(row, response['text'], response['finish_reason'])
                                equal = encoded(fresh) == encoded(saved_row['score'])
                                if not equal:
                                    receipt['mismatches'].append(dict(cell=evidence['name'], state=state, panel=panel, row_id=row['row_id'], saved=saved_row['score'], replayed=fresh))
                                cell['rows'].append(dict(state=state, panel=panel, row_id=row['row_id'], response_sha256=sha(response_raw),
                                                         replayed_score_sha256=sha(encoded(fresh)), saved_score_sha256=sha(encoded(saved_row['score'])), exact_score_object_match=equal))
                                scores.append(fresh)
                                rows_replayed += 1
                            counts = dict(total=len(scores), passed=sum(score['passed'] for score in scores),
                                          content_correct=sum(score['content_correct'] for score in scores), strict=sum(score['strict'] for score in scores),
                                          format_counts=dict(Counter(score['format'] for score in scores)))
                            expected = {key: saved_panel[key] for key in counts}
                            if counts != expected:
                                receipt['mismatches'].append(dict(cell=evidence['name'], state=state, panel=panel, saved_counts=expected, replayed_counts=counts))
                            cell['panels'][state][panel] = dict(replayed=counts, saved=expected, exact_match=counts == expected)
                    receipt['cells'].append(cell)
        require(rows_replayed == 1440 and len(receipt['cells']) == 12, 'replay cardinality differs')
        require(not any(name.split('.')[0] in ('torch', 'transformers', 'vllm') for name in sys.modules), 'unexpected model framework import')
        require(not receipt['mismatches'], 'frozen scorer replay differs')
        receipt['status'] = 'PASS'
    except Exception as error:
        receipt['status'] = 'FAIL'
        receipt['error_type'] = type(error).__name__
        receipt['error'] = str(error)
        raise
    finally:
        receipt['rows_replayed'] = rows_replayed
        receipt['elapsed_seconds'] = time.monotonic() - started
        receipt['finished_utc'] = datetime.now(timezone.utc).isoformat()
        with (REPLAY / 'receipt.json').open('x') as stream:
            json.dump(receipt, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write('\n')
        print(json.dumps({key: receipt[key] for key in ('sequence', 'status', 'rows_replayed', 'elapsed_seconds')}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()

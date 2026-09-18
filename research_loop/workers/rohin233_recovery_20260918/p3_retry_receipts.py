"""Incremental read-only post-LOAD proof; never publishes or controls a life."""

from datetime import datetime, timezone
import importlib.util
import inspect
import json
from pathlib import Path
import shlex
import subprocess

import p3_retry_observe as observer
import p3_renewed_receipts as previous


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CACHE = HERE / 'P3_RETRY_EVIDENCE.private.json'
MAXIMUM = 40


def learning_projection(record):
    document = record['document']
    result = {key: record[key] for key in ('index', 'kind', 'sha256')}
    for key in ('learn_row_policy', 'active_semantic_filters', 'semantic_row_exclusion',
            'historical_row_annotations', 'technical_provenance_and_encoding_checks',
            'policy', 'new_rows', 'selected_old_rows', 'new_presentations'):
        if key in document:
            result[key] = document[key]
    if record['kind'] == 'TARGET_ELIGIBILITY':
        result.update(eligible_new=len(document['new_row_sha256']),
            eligible_rehearsal=len(document['rehearsal_row_sha256']),
            excluded_count=len(document['excluded']), raw_modified=document['raw_modified'])
    if record['kind'] == 'SLEEP_COMPLETE':
        result.update(cycle=document['cycle'], status=document['status'],
            optimizer_steps=document['total_optimizer_steps'],
            checkpoint_sha256=document['checkpoint_sha256'], durable_binary_rehash=False)
    return result


def merge(prior, chunk, anchor):
    if chunk['journal_id'] != anchor['journal_id']:
        raise ValueError('same_retry_journal_required')
    expected = prior['through'] if prior else dict(index=anchor['loaded_index'], sha256=anchor['loaded_sha256'])
    if chunk['continuity'] and (chunk['continuity'][0]['index'] != expected['index'] + 1
            or chunk['continuity'][0]['previous_sha256'] != expected['sha256']):
        raise ValueError('exact_incremental_post_LOAD_chain')
    if prior and prior['loaded_sha256'] != anchor['loaded_sha256']:
        raise ValueError('never_reuse_other_incarnation_evidence')
    head = chunk.get('head') or {}
    caught_up = chunk['caught_up'] or (not chunk['continuity'] and
        all(head.get(key) == expected[key] for key in ('index', 'sha256')))
    return dict(journal_id=anchor['journal_id'], loaded_sha256=anchor['loaded_sha256'],
        through=chunk['through'] or expected, caught_up=caught_up,
        bytes_read=(prior['bytes_read'] if prior else 0) + chunk['bytes_read'],
        records=(prior['records'] if prior else []) + chunk['records'],
        learning=(prior['learning'] if prior else []) + chunk['learning'])


def actual_parent_attempts(started_unix):
    result = []
    preload_path = HERE / 'P3_RETRY_PRELOAD_RESULT.json'
    preload = observer.read(preload_path) if preload_path.is_file() else None
    for path in sorted(previous.p3_receipts.PARENT.glob('parent_*/RESULT.json')):
        is_preload = bool(preload and preload.get('status') == 'PUBLISHED' and preload['attempt'] == path.parent.name)
        if path.stat().st_mtime < started_unix and not is_preload:
            continue
        if is_preload:
            observer.require(observer.digest(path) == preload['result_sha256'], 'same_original_preload_ledger_result')
        row = observer.read(path)
        evidence = dict(attempt=path.parent.name, status=row['status'],
            result_sha256=observer.digest(path), provider_request=False, provider_response=False,
            generation_phase='PRELOAD_PARENT_QUEUE' if is_preload else 'POST_LOAD_PARENT')
        request_path, response_path = path.parent / 'API_REQUEST.json', path.parent / 'stdout.json'
        if request_path.is_file():
            request = observer.read(request_path)
            evidence.update(provider_request=True, api_request_sha256=observer.digest(request_path),
                requested_model=request['model'], requested_reasoning=request.get('reasoning'))
        if response_path.is_file():
            response = observer.read(response_path)
            evidence.update(provider_response=True, api_response_sha256=observer.digest(response_path),
                provider_status=response.get('status'))
        if row['status'] == 'PUBLISHED':
            intent = observer.read(path.parent / 'PUBLISH_INTENT.json')
            if intent['message'] != row['message'] or intent['speaker'] != 'Astra':
                raise ValueError('same_original_Astra_provider_publication')
            evidence['publication'] = row['publication']
        result.append(evidence)
    return result


def process_alive(receipt):
    try:
        fields = Path('/proc', str(receipt['pid']), 'stat').read_text().rsplit(') ', 1)[1].split()
    except FileNotFoundError:
        return False
    return fields[19] == receipt['start_ticks'] and fields[0] not in ('Z', 'X')


def main():
    binding = observer.read(HERE / 'P3_RETRY_BINDING.json')
    prior = observer.read(CACHE) if CACHE.is_file() else None
    after = prior['through']['index'] if prior else binding['loaded_index']
    reader_path = previous.AUDIT / 'reader.py'
    code = reader_path.read_text() + '\n' + inspect.getsource(learning_projection)
    code += '\nroot = ' + repr(str(observer.ROOT / 'life'))
    code += '\nresult = collect(root, ' + repr(binding['journal_id']) + ', maximum=40, after=' + str(after) + ')'
    code += '\nresult["learning"] = []\nfor reference in result["continuity"]:\n'
    code += ' if reference["kind"] in ("SLEEP_RECIPE", "TARGET_ELIGIBILITY", "SLEEP_COMPLETE"):\n'
    code += '  record, receipt = verified(Path(root) / "stream/records" / ("%020d.json" % reference["index"]), result["journal_id"])\n'
    code += '  result["learning"].append(learning_projection(record))\n'
    code += '\nimport sys\nsys.path.insert(0, ' + repr(str(observer.CPU)) + ')\nimport p3_retry_observe as identity\n'
    code += 'binding = identity.read(identity.BINDING)\nactual = identity.process(binding["pid"])\n'
    code += 'result["native_alive_same_incarnation"] = identity.same_process(actual, binding)\n'
    code += 'result["native"] = {key: actual[key] for key in ("pid", "start_ticks", "state", "command_sha256")} if actual else None\n'
    code += 'exit_path = identity.CONTROL / "EXIT.json"\n'
    code += 'result["native_exit"] = {key: value for key, value in identity.read(exit_path).items() if key in ("exit_code", "finished_unix", "no_retry")} if exit_path.is_file() else None\n'
    code += 'print(json.dumps(result))\n'
    response = subprocess.run(['bash', str(REPO / 'gpu/a40r_ssh.sh'), 'python3 -B -c ' + shlex.quote(code)],
        capture_output=True, text=True, check=True, timeout=120)
    chunk = json.loads(response.stdout)
    evidence = merge(prior, chunk, binding)
    temporary = CACHE.with_suffix('.next')
    temporary.write_text(json.dumps(evidence, sort_keys=True) + '\n')
    temporary.replace(CACHE)
    specification = importlib.util.spec_from_file_location('p3_retry_readiness_audit', previous.AUDIT / 'audit.py')
    audit = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(audit)
    frames = audit.frames(evidence)
    loaded = dict(original_journal_id=binding['journal_id'], loaded=dict(index=binding['loaded_index']))
    started_path = HERE / 'P3_RETRY_PARENT_STARTED.json'
    started = observer.read(started_path) if started_path.is_file() else None
    parents = actual_parent_attempts(started['started_unix'] if started else float('inf'))
    for parent in parents:
        if 'publication' in parent:
            parent['delivery'] = previous.proof(parent.pop('publication'), 'parent', evidence, frames, loaded)
    report = dict(observed_utc=datetime.now(timezone.utc).isoformat(), node='node4', life='P3',
        loaded_index=binding['loaded_index'], loaded_sha256=binding['loaded_sha256'],
        through=evidence['through'], caught_up=evidence['caught_up'],
        parent_alive=process_alive(started) if started else False,
        parent_process={key: started[key] for key in ('pid', 'start_ticks')} if started else None,
        parent_turns=parents, native=chunk['native'], native_exit=chunk['native_exit'],
        native_alive_same_incarnation=chunk['native_alive_same_incarnation'],
        tool_notice=previous.proof(previous.TOOL, 'environment', evidence, frames, loaded),
        learning=evidence['learning'], incremental_after=after, maximum_new_records=MAXIMUM,
        bytes_read_this_chunk=chunk['bytes_read'], reader_sha256=observer.digest(reader_path),
        remote_writes=0, native_signals=[], publication_actions=0,
        quality_or_learning_success_claim=False, raw_text_exported=False)
    temporary = HERE / 'P3_RETRY_ACTUAL.next'
    temporary.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    temporary.replace(HERE / 'P3_RETRY_ACTUAL.json')
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()

"""Bounded TRAIN-only candidate observations; never stops or changes a learner."""

import ast
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import textwrap
import time


HELPERS = Path('/localhome/local-rohing/orch_r179_node4_r181journal_20260917t2220z/r144_helpers.py')
BLOCK = re.compile(r'(?m)^[ \t]*```(?P<label>[^\n`]*)\n(?P<source>.*?)'
    r'(?:(?P<closing>^[ \t]*```[ \t]*(?:\n|$))|\Z)', re.S)


def text_metrics(raw):
    tokens = re.findall(r'\S+', raw)
    grams = Counter(tuple(tokens[index:index + 5]) for index in range(max(0, len(tokens) - 4)))
    blocks = list(BLOCK.finditer(raw))
    python_blocks = [block for block in blocks
        if block['label'].strip().lower().split()[:1] == ['python']]
    selected = python_blocks[0] if python_blocks else None
    result = dict(characters=len(raw), words=len(tokens),
        fullwidth_ascii_count=sum('\uff01' <= character <= '\uff5e' for character in raw),
        replacement_character_count=raw.count('\ufffd'),
        repeated_fivegram_fraction=(sum(count - 1 for count in grams.values()) / sum(grams.values()) if grams else 0),
        normalized_text_sha256=hashlib.sha256(' '.join(tokens).encode()).hexdigest(),
        cost_line_echo=bool(re.search(r'latest segment used|tokens.*since.*sleep|context.*out of.*tokens', raw, re.I)),
        summary_opening=bool(re.search(r'summary|distil|总结|總結', raw[:140], re.I)),
        python_block_count=len(python_blocks), first_python_block=None,
        first_fenced_block=(dict(language=blocks[0]['label'].strip(),
            source_excerpt=blocks[0]['source'][:240],
            fullwidth_ascii_count=sum('\uff01' <= character <= '\uff5e' for character in blocks[0]['source']),
            closed=blocks[0]['closing'] is not None) if blocks else None))
    if selected is not None:
        source = selected['source']
        block = dict(source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            fullwidth_ascii_count=sum('\uff01' <= character <= '\uff5e' for character in source),
            closed=selected['closing'] is not None,
            syntax_error=None)
        try:
            ast.parse(textwrap.dedent(source))
        except SyntaxError as error:
            block['syntax_error'] = dict(message=error.msg, line=error.lineno,
                text=(error.text or '').strip()[:180])
        result['first_python_block'] = block
    return result


def summarize(rows):
    hashes = Counter(row['metrics']['normalized_text_sha256'] for row in rows)
    blocks = [row['metrics']['first_python_block'] for row in rows if row['metrics']['first_python_block']]
    closed = [block for block in blocks if block['closed']]
    return dict(response_count=len(rows), with_python_block=len(blocks), closed_python_blocks=len(closed),
        fullwidth_responses=sum(row['metrics']['fullwidth_ascii_count'] > 0 for row in rows),
        fullwidth_python_blocks=sum(block['fullwidth_ascii_count'] > 0 for block in blocks),
        syntax_error_closed_python_blocks=sum(block['syntax_error'] is not None for block in closed),
        unclosed_python_blocks=sum(not block['closed'] for block in blocks),
        cost_line_echo_responses=sum(row['metrics']['cost_line_echo'] for row in rows),
        summary_opening_responses=sum(row['metrics']['summary_opening'] for row in rows),
        max_same_normalized_response=max(hashes.values(), default=0),
        max_repeated_fivegram_fraction=max((row['metrics']['repeated_fivegram_fraction'] for row in rows), default=0))


def assess_life(binding, helpers):
    process = Path('/proc') / str(binding['native']['pid'])
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    helpers.require(fields[19] == binding['native']['start_ticks'] and fields[0] not in ('Z', 'X'),
        'same_live_native_identity')
    helpers.require(helpers.sha(binding['guard_path']) == binding['guard_sha256'], 'unchanged_guard')
    plan = binding['plan']
    root = Path(plan['root'])
    backing = root.resolve(strict=True)
    helpers.require(str(backing) == binding['backing_root'], 'same_backing_root')
    paths = helpers.records(backing)
    records = []
    boundaries = []
    for path in reversed(paths[-1400:]):
        record = helpers.read(path)
        if record['kind'] == 'SLEEP_COMPLETE':
            boundaries.append(record)
        records.append(record)
        if len(boundaries) == 11:
            break
    helpers.require(len(boundaries) >= 6, 'five_completed_sleep_windows_available')
    first_index = boundaries[-1]['index']
    last_index = boundaries[0]['index']
    middle_index = boundaries[5]['index']
    latest = boundaries[0]
    saved = latest['document']['resume_state']
    helpers.require(helpers.digest(saved['state']) == saved['sha256'], 'saved_boundary_digest')
    commit_logical = root / 'checkpoints' / f"sleep_{latest['document']['cycle']:06d}" / 'COMMIT.json'
    commit = helpers.read(commit_logical.resolve(strict=True))
    response_rows = []
    train_requests = {}
    tool_records = []
    for record in reversed(records):
        if not first_index < record['index'] <= last_index:
            continue
        kind = record['kind']
        document = record['document']
        helpers.require(record['sha256'] == helpers.digest({key: value for key, value in record.items() if key != 'sha256'}),
            'observed_record_digest')
        if kind == 'REQUEST' and document.get('split') == 'TRAIN':
            request_sha = helpers.digest({key: value for key, value in document.items() if key != 'resume_state'})
            train_requests[request_sha] = record['index']
        elif kind == 'RESPONSE' and document.get('request_sha256') in train_requests:
            response = document['response']
            raw = response['raw']
            response_rows.append(dict(index=record['index'], record_sha256=record['sha256'],
                request_index=train_requests[document['request_sha256']],
                window='latest_five' if record['index'] > middle_index else 'preceding_five',
                metrics=text_metrics(raw),
                finish_metadata={key: response[key] for key in ('finish_reason', 'stop_reason', 'tokens', 'generated_tokens')
                    if key in response}, excerpt_start=raw[:260], excerpt_end=raw[-120:]))
        elif kind in ('R184_ACT', 'CPU_RESULT', 'EXPERIMENT_RESULT', 'TOOL_RESULT'):
            tool_records.append(dict(index=record['index'], kind=kind, record_sha256=record['sha256']))
    recent = [row for row in response_rows if row['window'] == 'latest_five']
    earlier = [row for row in response_rows if row['window'] == 'preceding_five']
    checkpoint_keys = ('adapter_path', 'optimizer_rng_path', 'optimizer_steps', 'adapter_state_sha256',
                       'adapter_files', 'checkpoint_sha256')
    return dict(life=binding['life'], physical=plan['physical'], native=binding['native'],
        logical_root=str(root), backing_root=str(backing), hard_end_unix=plan['hard_end_unix'],
        observed_head_index=int(paths[-1].stem), scan_first_index=first_index,
        latest_complete=dict(cycle=latest['document']['cycle'], record_index=latest['index'],
            record_sha256=latest['sha256'], state_sha256=saved['sha256'],
            record_path=str(root / 'stream/records' / f"{latest['index']:020d}.json"),
            checkpoint_path=str(commit_logical), checkpoint_file_sha256=helpers.sha(commit_logical.resolve()),
            checkpoint={key: commit[key] for key in checkpoint_keys if key in commit},
            no_pending=saved['state']['pending'] is None,
            frontier_complete=saved['state']['sleep_frontier'] == len(saved['state']['rows']),
            history_events=len(saved['state']['history'].get('events', [])), rows=len(saved['state']['rows'])),
        latest_five_cycles=[record['document']['cycle'] for record in reversed(boundaries[:5])],
        preceding_five_cycles=[record['document']['cycle'] for record in reversed(boundaries[5:10])],
        latest_five=summarize(recent), preceding_five=summarize(earlier),
        responses=response_rows, tool_record_metadata=tool_records,
        checkpoint_verification='COMMIT_AND_SAVED_DIGEST_ONLY_NO_TENSOR_READ',
        mutation_count=0, sealed_or_final_reads=0)


def assess(bindings):
    specification = importlib.util.spec_from_file_location('existing_node4_helpers', HELPERS)
    helpers = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(helpers)
    helpers.current_node('a40r')
    result = dict(observed_unix=time.time(), scope='MSG201_READONLY_CANDIDATES_NOT_RETIREMENT',
        learners=[], errors=[], mutation_count=0)
    for binding in bindings:
        try:
            result['learners'].append(assess_life(binding, helpers))
        except Exception as error:
            result['errors'].append(dict(life=binding['life'], error_type=type(error).__name__, message=str(error)))
    print(json.dumps(result, sort_keys=True, indent=2))


def verify_candidate_checkpoints(bindings):
    specification = importlib.util.spec_from_file_location('existing_node4_helpers', HELPERS)
    helpers = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(helpers)
    helpers.current_node('a40r')
    rows = []
    for binding in bindings:
        process = Path('/proc') / str(binding['native']['pid'])
        fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
        helpers.require(fields[19] == binding['native']['start_ticks'] and fields[0] not in ('Z', 'X'),
            'same_native_still_live')
        helpers.require(str((process / 'cwd').resolve()) == binding['plan']['source_root'], 'same_native_source')
        root = Path(binding['plan']['root'])
        helpers.require(str(root.resolve()) == binding['backing_root'], 'unchanged_root_alias')
        paths = helpers.records(root.resolve())
        latest = next(record for path in reversed(paths[-350:])
            if (record := helpers.read(path))['kind'] == 'SLEEP_COMPLETE')
        helpers.require(latest['sha256'] == helpers.digest({key: value for key, value in latest.items()
            if key != 'sha256'}), 'latest_complete_record_digest')
        envelope = latest['document']['resume_state']
        state = envelope['state']
        helpers.require(helpers.digest(state) == envelope['sha256'] and state['pending'] is None
            and state['sleep_frontier'] == len(state['rows']), 'exact_complete_saved_state')
        checkpoint_path = root / 'checkpoints' / f"sleep_{latest['document']['cycle']:06d}" / 'COMMIT.json'
        checkpoint_hash = helpers.sha(checkpoint_path.resolve())
        checkpoint = helpers.read(checkpoint_path.resolve())
        optimizer_path = Path(checkpoint['optimizer_rng_path'])
        optimizer_sha = helpers.sha(optimizer_path.resolve())
        adapter = Path(checkpoint['adapter_path'])
        adapter_shas = {path.name: helpers.sha(path.resolve()) for path in adapter.iterdir() if path.is_file()}
        helpers.require(adapter_shas == checkpoint['adapter_files'], 'exact_adapter_files')
        helpers.require(optimizer_sha == checkpoint['checkpoint_sha256']['optimizer']
            == checkpoint['checkpoint_sha256']['rng'], 'exact_optimizer_rng_bytes')
        helpers.require(helpers.digest(checkpoint['checkpoint_sha256']) == state['model_state_sha256'],
            'saved_state_model_binding')
        helpers.require(helpers.sha(checkpoint_path.resolve()) == checkpoint_hash, 'commit_unchanged_during_read')
        rows.append(dict(life=binding['life'], physical=binding['plan']['physical'],
            native_pid=binding['native']['pid'], native_start_ticks=fields[19],
            observed_unix=time.time(), latest_complete_cycle=latest['document']['cycle'],
            record_index=latest['index'], record_sha256=latest['sha256'],
            state_sha256=envelope['sha256'], optimizer_steps=checkpoint['optimizer_steps'],
            checkpoint_path=str(checkpoint_path), checkpoint_file_sha256=checkpoint_hash,
            optimizer_rng_path=str(optimizer_path), optimizer_rng_sha256=optimizer_sha,
            adapter_path=str(adapter), adapter_files=adapter_shas,
            saved_rows=len(state['rows']), saved_history_events=len(state['history'].get('events', [])),
            hard_end_unix=state['deadline_unix'], checkpoint_unchanged_during_read=True,
            bytes_hashed_without_tensor_load=True, retirement_authorized=False, mutation_count=0))
    print(json.dumps(dict(observed_unix=time.time(), candidates=rows, mutation_count=0,
        note='Existing immutable checkpoints verified in place; learners continue and may advance. No archive or stop performed.'),
        sort_keys=True, indent=2))

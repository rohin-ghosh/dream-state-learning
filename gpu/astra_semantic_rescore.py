"""Supplementary equal-shape scoring of immutable Q0 adapters; never train."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time

from organism_v6 import semantic_writer_diagnostic as diagnostic
from organism_v6 import run_reasoning_neutral as supervisor


ORIGINAL_MANIFEST_SHA256 = 'f6fa9060e9ea794309839a8651adc728989c283663070b348c3200acca57a830'
STATES = ['OFF', *diagnostic.STATES]
require = diagnostic.w0.require
read = diagnostic.read_json
file_hash = diagnostic.w0.file_hash
write = diagnostic.w0.write_once


def verify_original(root):
    root = Path(root).resolve(strict=True)
    manifest = read(root / 'manifest.json')
    require(file_hash(root / 'manifest.json') == ORIGINAL_MANIFEST_SHA256, 'fixed original Q0 manifest required')
    require(manifest['output_root'] == str(root) and (root / 'SEAL.json').is_file()
            and not (root / 'FAILED.json').exists(), 'original terminal run required')
    for path, expected in manifest['sources'].items():
        require(file_hash(Path(path)) == expected, 'original frozen source changed')
    for name, expected in manifest['artifacts'].items():
        require(file_hash(root / name) == expected, 'original prepared artifact changed')
    require(diagnostic.pin_inputs(manifest['config']) == manifest['input_pins'], 'original base/environment drift')
    requests = read(root / 'requests.json')
    diagnostic.validate_counts(requests)
    return manifest, requests


def source_pins():
    return {str(Path(__file__).resolve()): file_hash(Path(__file__)), **diagnostic.sources()}


def verify_supplement(out):
    out = Path(out).resolve(strict=True)
    supplement = read(out / 'supplement.json')
    require(supplement['sources'] == source_pins(), 'supplement source changed')
    original = Path(supplement['original'])
    manifest, requests = verify_original(original)
    require(supplement['original_report_sha256'] == file_hash(original / 'report.json'), 'original report changed')
    return out, supplement, original, manifest, requests


def worker(out, state):
    out, supplement, original, manifest, requests = verify_supplement(out)
    require(state in STATES and time.time() < supplement['deadline'], 'valid state/deadline required')
    directory = out / state
    directory.mkdir(exist_ok=False)
    config = manifest['config']
    torch = diagnostic.w0.configure_torch(config, 0)
    if state == 'OFF':
        adapter_sha, lora_sha = 'OFF', 'OFF'
    else:
        fitted = read(original / 'stages' / ('fit_' + state) / 'DONE.json')['result']
        adapter_sha, lora_sha = fitted['adapter_sha256'], fitted['final_lora_sha256']
    model = diagnostic.load_eval_model(config, torch, original, state, adapter_sha, lora_sha)
    write(directory, 'LOAD.json', dict(state=state, adapter_sha256=adapter_sha, lora_sha256=lora_sha,
        dtype=str(next(model.parameters()).dtype), original_manifest_sha256=ORIGINAL_MANIFEST_SHA256))
    selected = [row for row in requests if row['state'] == state and row['operation'] == 'score']
    require(len(selected) == (192 if state == 'OFF' else 160), 'fixed scoring denominator')
    with (directory / 'records.jsonl').open('x') as stream:
        for request in selected:
            require(time.time() < supplement['deadline'] - 5, 'supplement deadline')
            started = time.monotonic()
            output = diagnostic.carrier.score(torch, model, request)
            diagnostic.score_sums(request, output)
            torch.cuda.synchronize()
            record = dict(request_id=request['request_id'], request_sha256=diagnostic.w0.digest(request),
                adapter_sha256=adapter_sha, attempts=1, seconds=time.monotonic() - started,
                output=output, supplementary_equal_shape=True)
            stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + '\n')
            stream.flush()
    require(source_pins() == supplement['sources'], 'source changed during worker')
    if state != 'OFF':
        require(diagnostic.w0.tree_hash(original / 'stages' / ('fit_' + state) / 'adapter') == adapter_sha,
            'original adapter changed')
    write(directory, 'DONE.json', dict(state=state, count=len(selected),
        records_sha256=file_hash(directory / 'records.jsonl'), finished=time.time()))


def merge_records(original, out, requests):
    rescored = {}
    for state in STATES:
        directory = out / state
        done = read(directory / 'DONE.json')
        require(done['records_sha256'] == file_hash(directory / 'records.jsonl'), 'rescore records changed')
        rows = [json.loads(line) for line in (directory / 'records.jsonl').read_text().splitlines()]
        require(len(rows) == done['count'] and len({row['request_id'] for row in rows}) == len(rows), 'duplicate/missing score')
        for row in rows:
            require(row['request_id'] not in rescored, 'duplicate state score')
            rescored[row['request_id']] = row
    require(len(rescored) == 832, '832 supplementary scores required')
    combined = []
    for request in requests:
        if request['operation'] == 'score':
            combined.append(rescored[request['request_id']])
        else:
            stage = 'off_generate' if request['state'] == 'OFF' else 'eval_' + request['state'] + '_generate'
            combined.append(read(original / 'stages' / stage / 'raw' / (request['request_id'] + '.json')))
    return combined


def execute(original, out):
    original, out = Path(original).resolve(strict=True), Path(out).absolute()
    manifest, requests = verify_original(original)
    require(not out.exists() and not out.is_relative_to(original) and not original.is_relative_to(out), 'fresh separate supplement root')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == manifest['config']['gpu_uuid'], 'Main reserved original GPU required')
    out.mkdir(parents=True, exist_ok=False)
    started = time.time()
    write(out, 'supplement.json', dict(status='SUPPLEMENT_NOT_REPLACEMENT', original=str(original),
        original_manifest_sha256=ORIGINAL_MANIFEST_SHA256, original_report_sha256=file_hash(original / 'report.json'),
        sources=source_pins(), started=started, deadline=started + 3600, states=STATES,
        new_fits=0, generation='unchanged original executed generation records', scoring='BF16 equal total sequence shape',
        caveat='Original likelihood metrics are not overwritten; no registered-gate rescue or selective-writer certification.'))
    try:
        for state in STATES:
            supervisor.run_worker([sys.executable, '-B', '-m', 'gpu.astra_semantic_rescore', '--worker',
                '--out', str(out), '--state', state], log_path=out / (state + '.log'), timeout=600,
                device=supervisor.selected_device())
        tokenizer = diagnostic.w0.load_local_tokenizer(manifest['config'])
        report = diagnostic.reduce_records(read(original / 'material.json'), requests, merge_records(original, out, requests), tokenizer)
        verify_supplement(out)
        write(out, 'supplementary_report.json', report)
        write(out, 'COMPLETED.json', dict(status='SUPPLEMENTARY_SCORE_DIAGNOSTIC_ONLY', finished=time.time(),
            seconds=time.time() - started, new_fits=0, new_scores=832, reused_generations=880,
            report_sha256=file_hash(out / 'supplementary_report.json')))
    except BaseException as error:
        write(out, 'FAILED.json', dict(error_type=type(error).__name__, error=str(error), preserve_attempt=True))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original')
    parser.add_argument('--out', required=True)
    parser.add_argument('--state', choices=STATES)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--allow-gpu', action='store_true')
    args = parser.parse_args()
    if args.worker:
        worker(args.out, args.state)
    else:
        require(args.allow_gpu and args.original, 'Main explicit launch required')
        execute(args.original, args.out)


if __name__ == '__main__':
    main()

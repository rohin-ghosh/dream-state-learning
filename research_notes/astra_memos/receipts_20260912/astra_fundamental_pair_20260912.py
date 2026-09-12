import argparse
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
import sys

from organism_v6 import fundamental_teaching_corpus as corpus
from organism_v6 import rulegame_parenting_diagnostic as base
from organism_v6 import train_adapter_v3 as trainer

ROOT = Path.home() / 'astra_diagnostics/astra_fundamental_teaching_20260912_attempt1'
MODEL = str(Path.home() / '.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28')
CONFIG = trainer.TrainConfig(rank=8, alpha=16, dropout=.05, lr=3e-4, epochs=4,
    seed=0, batch_size=4, grad_accum=1, pack=False, max_len=512, model=MODEL)

def source_hashes():
    result = base.sources()
    result.update({name: base.digest(base.REPO / 'organism_v6' / name)
        for name in ('fundamental_teaching_corpus.py', 'train_adapter_v3.py')})
    result['launcher_script'] = base.digest(__file__)
    return result

def prepare():
    base.require(not ROOT.exists(), 'fresh root required')
    old = base.read(Path.home() / 'astra_diagnostics/astra_relation_surface_20260912_attempt1/plan.json')
    files = base.model_hashes(MODEL)
    base.require(files == old['model_files'] and MODEL == old['model'], 'local model differs')
    tokenizer = base.native_tokenizer(MODEL)
    candidate = corpus.build_candidate()
    events = {row['id']: row for row in candidate['source_records']}
    alternatives = []
    for label in corpus.RESULT_LABEL_VARIANTS:
        lengths = []
        for teach, control in zip(candidate['train_teach'], candidate['train_control']):
            response = control['response']
            if teach['kind'] == 'addition':
                event = events[teach['source_event_ids'][0]]
                response = corpus.arithmetic_response(event['left'], event['right'], 'control', label)
            lengths.append((len(tokenizer.encode(teach['response'], add_special_tokens=False)),
                            len(tokenizer.encode(response, add_special_tokens=False))))
        alternatives.append(dict(label=label, matched=all(left == right for left, right in lengths), lengths=lengths))
    selected = next((row['label'] for row in alternatives if row['matched']), None)
    base.require(selected == 'COMPUTED', 'no expected global truthful token match')
    ROOT.mkdir()
    corpus.emit_candidate(ROOT / 'candidate')
    exports, audits = {}, {}
    for arm in ('teach', 'control'):
        records, checks = [], []
        for index, row in enumerate(candidate['train_' + arm]):
            response = row['response']
            if arm == 'control' and row['kind'] == 'addition':
                event = events[row['source_event_ids'][0]]
                response = corpus.arithmetic_response(event['left'], event['right'], arm, selected)
            context = tokenizer.apply_chat_template([dict(role='user', content=row['context'])],
                tokenize=False, add_generation_prompt=True)
            item = dict(spans=[[context, False, 'context'], [response, True, 'authored_birth_target']],
                group=row['case_id'], view=row['kind'], order=index,
                meta=dict(source_event_ids=row['source_event_ids']))
            normalized = trainer.normalize_items([item])
            encoded = trainer.encode_item_segments(normalized[0], tokenizer, 512, False, True, index)
            base.require(len(encoded) == 1 and encoded[0].context_dropped == encoded[0].target_dropped == 0,
                'split/truncated training example')
            prefix = tokenizer.encode(context, add_special_tokens=False)
            target = tokenizer.encode(response, add_special_tokens=False) + [tokenizer.eos_token_id]
            batch = trainer.collate([encoded], tokenizer.pad_token_id)
            base.require(batch['input_ids'] == [prefix + target] and
                batch['labels'] == [[-100] * len(prefix) + target], 'native label boundary mismatch')
            checks.append(dict(case_id=row['case_id'], input_tokens=len(prefix + target),
                target_tokens=len(target), labels_sha256=base.value_hash(batch['labels'])))
            records.append(item)
        exports[arm] = dict(corpus=records)
        audits[arm] = checks
        base.write_json(ROOT / (arm + '.json'), exports[arm])
    base.require([(row['case_id'], row['input_tokens'], row['target_tokens']) for row in audits['teach']] ==
        [(row['case_id'], row['input_tokens'], row['target_tokens']) for row in audits['control']], 'paired tokens unequal')
    plan = dict(model=MODEL, model_files=files, source_hashes=source_hashes(), config=asdict(CONFIG),
        selected_control_label=selected, alternatives=alternatives, row_audits=audits,
        corpus_sha256={arm: base.digest(ROOT / (arm + '.json')) for arm in exports},
        tokens={arm: dict(input_tokens=sum(row['input_tokens'] for row in rows),
                         target_tokens=sum(row['target_tokens'] for row in rows)) for arm, rows in audits.items()},
        lease_end=base.datetime.fromisoformat('2026-09-25T21:03:00+00:00').timestamp(),
        material_role='OPEN_LOOP_AUTHORED_BIRTH_POSITIVE_CONTROL_NOT_CHILD_SLEEP',
        model_origin='UNRESOLVED_LOCAL_HASHES_ONLY', status='NATIVE_ENCODER_AND_PAIRED_TOKENS_VERIFIED',
        fits_authorized_by_script=False, eval_dev_ids=[f'eval-addition-{index:03d}' for index in range(32)] +
            [f'eval-memory-{index:03d}-0' for index in range(16)])
    base.write_json(ROOT / 'plan.json', plan)
    base.write_json(ROOT / 'plan.sha256.json', dict(sha256=base.digest(ROOT / 'plan.json')))
    return dict(root=str(ROOT), status=plan['status'], selected=selected, tokens=plan['tokens'])

def verify():
    plan = base.read(ROOT / 'plan.json')
    base.require(base.digest(ROOT / 'plan.json') == base.read(ROOT / 'plan.sha256.json')['sha256'], 'plan changed')
    base.require(plan['source_hashes'] == source_hashes() and plan['config'] == asdict(CONFIG), 'source/config changed')
    base.require(base.model_hashes(MODEL) == plan['model_files'], 'model bytes changed')
    for arm in ('teach', 'control'):
        base.require(base.digest(ROOT / (arm + '.json')) == plan['corpus_sha256'][arm], 'corpus changed')
    return plan

def fit(arm, device, allow_gpu):
    base.require(allow_gpu and (arm, device) in (('teach', '0'), ('control', '1')), 'explicit paired allocation required')
    plan = verify()
    stage = base.fresh_directory(ROOT / ('fit_' + arm), MODEL)
    adapter = stage / 'adapter'
    command = [sys.executable, '-B', '-m', 'organism_v6.train_adapter_v3', '--corpus', str(ROOT / (arm + '.json')),
        '--out', str(adapter), '--model', MODEL, '--rank', '8', '--alpha', '16', '--dropout', '0.05',
        '--lr', '0.0003', '--epochs', '4', '--seed', '0', '--batch-size', '4', '--grad-accum', '1',
        '--no-pack', '--max-len', '512']
    supervision = base.supervise(ROOT, dict(plan, device=device), stage / 'worker', command)
    verify()
    manifest = base.read(adapter / 'train_manifest.json')
    base.require(manifest['config'] == plan['config'], 'actual trainer config mismatch')
    base.require((adapter / 'DONE').is_file() and manifest['steps'] == 80 and manifest['nonfinite_batches'] == 0
        and math.isfinite(manifest['final_loss']), 'fit incomplete/nonfinite')
    base.require(manifest['corpus']['sha256'] == plan['corpus_sha256'][arm] and
        manifest['corpus']['n_items'] == manifest['corpus']['n_encoded'] == 80 and
        manifest['corpus']['n_skipped_no_target'] == 0, 'actual material mismatch')
    base.require(all(manifest['truncation'][name] == 0 for name in
        ('items_truncated', 'context_tokens_dropped', 'target_tokens_dropped', 'items_split')), 'actual truncation')
    tokens = plan['tokens'][arm]
    base.require(manifest['tokens']['total'] == tokens['input_tokens'] and
        manifest['tokens']['target'] == tokens['target_tokens'] and
        manifest['train_tokens_seen'] == 4 * tokens['input_tokens'], 'actual training tokens differ')
    saved = base.read(adapter / 'adapter_config.json')
    base.require(saved['r'] == 8 and saved['lora_alpha'] == 16 and saved['lora_dropout'] == .05, 'adapter config differs')
    result = dict(status='FIT_COMPLETE_PENDING_PAIRED_READOUT', arm=arm, device=device,
        adapter=str(adapter), adapter_files=base.tree_hashes(adapter), manifest=manifest,
        supervised=supervision, model_origin=plan['model_origin'], material_role=plan['material_role'])
    base.write_json(stage / 'result.json', result)
    return dict(status=result['status'], arm=arm, adapter=str(adapter), steps=manifest['steps'],
        final_loss=manifest['final_loss'])

parser = argparse.ArgumentParser()
parser.add_argument('stage', choices=('prepare', 'fit'))
parser.add_argument('--arm', choices=('teach', 'control'))
parser.add_argument('--device', choices=('0', '1'))
parser.add_argument('--allow-gpu', action='store_true')
if __name__ == '__main__':
    args = parser.parse_args()
    print(json.dumps(prepare() if args.stage == 'prepare' else fit(args.arm, args.device, args.allow_gpu), sort_keys=True))

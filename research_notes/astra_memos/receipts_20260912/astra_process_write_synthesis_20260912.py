"""SEQ115 offline capsule synthesis; never loads a model or queries a device."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tarfile

sys.dont_write_bytecode = True
BASE = Path('/tmp/astra_process_write_synthesis_20260912')
CAPSULE = Path('/tmp/astra_process_write_terminal_20260912.tgz')
VALIDATION = Path('/tmp/astra_process_write_terminal_validation_20260912.json')
EXPECTED = '9db826c86b306ba5a92bcfc2902e0baaaed83318f1c70b029cb0ca062ec17e5a'
PLAN_SHA = '67f2b89a769dd1f21e2ae3f048aa2d3743a5761f0574dcca3f47e1a8c51b0f44'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path, pin, name):
    require(digest(path) == pin, 'frozen implementation mismatch')
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def analyze():
    collector = load('/tmp/astra_rulegame_process_write_collect_20260912.py',
        'e23160132bf4eac82f220b8066c49de3cf8461e50929f9a82f3eac5e12906892', 'seq115_collector')
    driver = load('/tmp/astra_rulegame_process_write_20260912.py',
        'a73dd6074fdd099cea19f46cfed94bf31f22b2ce02b8741ac2f224413ee514d9', 'seq115_writer')
    validation = collector.read(VALIDATION)
    require(digest(CAPSULE) == validation['archive_sha256'] == EXPECTED, 'capsule hash mismatch')
    require(validation['collector_sha256'] == digest(collector.__file__) and validation['plan_sha256'] == PLAN_SHA
        and validation['status'] == 'COLLECTED_PAIRED_WRITE' and validation['full_release'] is True
        and validation['aggregate_available'] is True and validation['weights_in_capsule'] is False, 'collection not accepted')
    collector.validate_archive(CAPSULE, validation['files'])
    with tarfile.open(CAPSULE) as archive:
        members = {member.name: archive.extractfile(member).read() for member in archive}
    def read(name):
        return json.loads(members[name], object_pairs_hook=collector.unique)
    def member_hash(name):
        return hashlib.sha256(members[name]).hexdigest()
    plan = read('metadata/run/plan.json')
    require(member_hash('metadata/run/plan.json') == read('metadata/run/plan.sha256.json')['sha256'] == PLAN_SHA, 'plan join mismatch')
    require(plan['protocol'] == driver.WRITE_PROTOCOL and plan['material_protocol'] == driver.PROTOCOL and plan['schema'] == 2
        and plan['init_adapter'] is None and plan['model_origin'] == driver.ORIGIN and plan['claims'] == driver.CLAIMS, 'plan lineage mismatch')
    audit = read('metadata/collection/audit.json')
    custody = read('metadata/collection/custody.json')
    summary = read('metadata/collection/material_summary.json')
    terminal = read('metadata/run/run/result.json')
    require(terminal['status'] == 'PAIRED_ADAPTERS_SAVED_READOUT_PENDING' and set(terminal['arms']) == {'P','A'}
        and terminal['claims'] == driver.CLAIMS and terminal['readout'] == 'OUT_OF_SCOPE', 'terminal mismatch')
    pair_path = Path('/tmp/astra_process_pair_v2_20260912.json')
    preflight_path = Path('/tmp/astra_process_native_pair_preflight_20260912.log')
    preflight = [json.loads(line) for line in preflight_path.read_text().splitlines()]
    pair_pin = next(row['sha256'] for row in preflight if row.get('artifact') == 'pair')
    require(digest(pair_path) == pair_pin, 'preflight pair hash mismatch')
    pair = collector.read(pair_path)
    candidate_path = Path(plan['fixed_candidate_path'])
    review_path = Path(plan['main_review_path'])
    require(digest(candidate_path) == plan['fixed_candidate_sha256'] and digest(review_path) == plan['main_review_sha256'], 'Main/candidate raw hash mismatch')
    candidate, review = collector.read(candidate_path), collector.read(review_path)
    require(candidate == pair['audit']['candidate'] and candidate['candidate_sha256'] == plan['candidate_sha256'] == summary['candidate_sha256'], 'candidate join mismatch')
    require(candidate['candidate_sha256'] == hashlib.sha256(driver.encoded({key:value for key,value in candidate.items() if key!='candidate_sha256'})).hexdigest(), 'candidate self hash mismatch')
    driver.check_native_review(review, pair)
    require(review['actor'] == 'Main' and review['protocol'] == driver.PROTOCOL and review['context_distillation_acknowledged'] is True
        and len(review['reviews']) == 4 and all(row['decision']=='accept' and row['notes'].strip() for row in review['reviews']), 'Main source review incomplete')
    require(preflight[-1]['totals'] == pair['audit']['token_totals'], 'preflight totals differ')
    arms = {}
    for arm in ('P','A'):
        prefix = f'metadata/run/fits/{arm}'
        manifest = read(prefix+'/adapter/train_manifest.json')
        fit_seal = read(prefix+'/manifest.json')['files']
        receipt = read(prefix+'/receipt.json')
        before = read(prefix+'/pre_update_trainability.json')
        after = read(prefix+'/post_update_trainability.json')
        adapter = read(prefix+'/adapter/adapter_config.json')
        supervision = read(f'metadata/run/run/{arm}/supervision.json')
        process = read(f'metadata/run/run/{arm}/process.json')
        attempt = read(prefix+'/attempt.json')
        for relative, checksum in fit_seal.items():
            name = prefix+'/'+relative
            actual = member_hash(name) if name in members else custody['excluded_native_files'][name]['sha256']
            require(actual == checksum, 'fit member custody mismatch: '+name)
        for relative, checksum in receipt['files'].items():
            name = prefix+'/adapter/'+relative
            actual = member_hash(name) if name in members else custody['excluded_native_files'][name]['sha256']
            require(actual == checksum, 'adapter file custody mismatch')
        require(terminal['arms'][arm] == dict(receipt, fit_manifest_sha256=member_hash(prefix+'/manifest.json'),
            supervision_sha256=member_hash(f'metadata/run/run/{arm}/supervision.json')), 'terminal/fit receipt join differs')
        require(member_hash(prefix+'/receipt.json') == audit['arms'][arm]['fit_receipt_sha256'], 'collector/fit receipt differs')
        require(manifest['config'] == plan['config'] and manifest['base_model'] == plan['model'] and 'warm_start' not in manifest,
            'fit recipe/base/warmstart differs')
        require(manifest['steps'] == manifest['micro_batches'] == manifest['epochs_run'] == receipt['steps'] == receipt['observed_forward_batches'] == 12,
            'incomplete update counts')
        require(manifest['nonfinite_batches'] == 0 and math.isfinite(manifest['final_loss']) and len(manifest['mean_loss_per_epoch']) == 12
            and all(math.isfinite(value) for value in manifest['mean_loss_per_epoch']), 'nonfinite loss')
        require(manifest['corpus'] == dict(file=arm+'.json',sha256=plan['material_files']['corpora/'+arm+'.json'],n_items=2,n_encoded=2,n_skipped_no_target=0), 'corpus count/hash mismatch')
        require(manifest['tokens'] == plan['tokens'][arm]['tokens'] and manifest['train_tokens_seen'] == plan['tokens'][arm]['train_tokens_seen'], 'token exposure mismatch')
        require(all(manifest['truncation'][key] == 0 for key in ('items_truncated','context_tokens_dropped','target_tokens_dropped','items_split','segments_from_splits'))
            and manifest['packing']['mode']=='one_item_per_sequence' and manifest['packing']['n_sequences']==2, 'mask/drop/packing failure')
        require(before == after and before['base_frozen'] is True and before['adapter_count']==1 and before['init_adapter'] is None
            and attempt['init_adapter'] is None and attempt['pid']==process['pid']==process['pgid'], 'lineage/trainability mismatch')
        for name, parameter in before['parameters'].items():
            require(parameter['requires_grad'] == name.endswith(('.lora_A.default.weight','.lora_B.default.weight')), 'non-LoRA trainable parameter')
        require(adapter['r']==8 and adapter['lora_alpha']==16 and adapter['lora_dropout']==.05 and adapter['bias']=='none'
            and adapter['base_model_name_or_path']==plan['model'] and before['trainable_params']==20185088
            and len(before['adapters'])==392 and manifest['lora']['n_layers']==28, 'LoRA coverage mismatch')
        finite = audit['arms'][arm]['finite_weights']
        require(finite['sha256']==receipt['files']['adapter_model.safetensors'] and finite['finite'] is True
            and len(finite['tensors'])==392 and all(row['finite'] for row in finite['tensors']), 'native finite-weight receipt differs')
        raw_rows = []
        for index, raw in enumerate(pair['audit']['receipts'][arm]):
            transformed = raw['transformed_training']
            context, target = transformed['context_token_ids'], transformed['raw_target_token_ids']
            eos = transformed['target_with_eos'][-1]
            require(eos not in target and transformed['target_with_eos']==target+[eos]
                and transformed['input_ids']==context+target+[eos] and transformed['labels']==[-100]*len(context)+target+[eos]
                and transformed['first_target_predictor']==len(context)-1, 'preflight causal mask/EOS mismatch')
            item = pair['corpora'][arm]['corpus'][index]
            expected = summary['rows'][arm][index]
            require(hashlib.sha256(item['spans'][0][0].encode()).hexdigest()==expected['context_sha256']
                and hashlib.sha256(item['spans'][1][0].encode()).hexdigest()==expected['raw_target_sha256']
                and item['meta']['source_call_id']==expected['source_call_id'], 'preflight raw-context/target join differs')
            require(item['spans'][0][1:] == [False,'parent_removed_wake_context'] and item['spans'][1][1:] == [True,'complete_own_raw_wake'], 'loss span differs')
            raw_rows.append(dict(expected,context_tokens=len(context),first_target_predictor=len(context)-1))
        for index in range(12):
            forward=read(prefix+f'/forwards/{index+1:04d}.json')
            require(forward['forward']==index+1 and sorted(forward['row_order'])==[0,1]
                and forward['batch_exposure']==plan['tokens'][arm]['per_batch_exposure'][index], 'forward batch exposure differs')
            for position,row_index in enumerate(forward['row_order']):
                row=forward['rows'][position]
                require(all(row[key]==raw_rows[row_index][key] for key in ('input_tokens','context_tokens','target_tokens','raw_target_tokens','first_target_predictor','slot_id')),
                    'forward/preflight row mismatch')
        require(supervision['returncode']==0 and supervision['error'] is None and all(supervision[key] is True for key in
            ('ok','owned_group_empty','gpu_processes_absent','reservation_release_verified')), 'worker cleanup failed')
        arms[arm]=dict(steps=12,epochs=12,micro_batches=12,forward_receipts=12,rows=raw_rows,
            tokens=manifest['tokens'],exposure=receipt['exposure'],train_tokens_seen=manifest['train_tokens_seen'],
            epoch_losses=manifest['mean_loss_per_epoch'],final_loss=manifest['final_loss'],nonfinite_batches=0,
            trainable_lora_parameters=before['trainable_params'],saved_lora_tensors=len(before['adapters']),
            adapter_weight_sha256=finite['sha256'],native_weight_finiteness_attested=True,weight_bytes_locally_rescanned=False,
            training_seconds=manifest['train_seconds'],trainer_wall_seconds=manifest['wall_seconds'],
            worker_reserved_seconds=supervision['reserved_seconds'],worker_pid=process['pid'],
            fit_manifest_sha256=member_hash(prefix+'/manifest.json'),fit_receipt_sha256=member_hash(prefix+'/receipt.json'))
    release=read('metadata/collection/release.json')
    launch=read('metadata/launch/launch.json')
    controller=read('metadata/run/run/controller.json')
    require(member_hash('metadata/launch/launch.json')==release['launch_sha256'], 'launch receipt hash differs')
    require(member_hash('metadata/collection/release.xml')==release['xml_sha256'], 'vacancy XML differs')
    collector.check_uuid(release['gpu'],members['metadata/collection/release.xml'],launch['gpu']['gpu_uuid'])
    require(controller['pid']==launch['pid'] and set(release['owned_ids'])=={launch['pid'],arms['P']['worker_pid'],arms['A']['worker_pid']}, 'release/owned IDs differ')
    require(terminal['controller_seconds']==audit['controller_seconds']<=1200 and validation['collection_seconds']<=300, 'wall-clock bounds exceeded')
    require(sum(arms[arm]['worker_reserved_seconds'] for arm in arms)==audit['observed_verified_worker_seconds'], 'worker subtotal differs')
    require(abs(validation['final_vacancy']['observed_wall']-collector.utc(launch['started_utc'])-validation['full_launch_to_final_vacancy_seconds'])<1e-6, 'full wall-clock accounting differs')
    raw_paths=dict(capsule=str(CAPSULE),validation=str(VALIDATION),pair=str(pair_path),preflight_receipts=str(preflight_path),
        candidate=str(candidate_path),final_main_review=str(review_path),native_root=plan['out'],native_source=plan['source_root'],
        archive_members=sorted(members),native_excluded_files=custody['excluded_native_files'])
    inputs={str(path):digest(path) for path in (CAPSULE,VALIDATION,pair_path,preflight_path,candidate_path,review_path,Path(collector.__file__),Path(driver.__file__))}
    limitations=[
        'Metadata capsule contains no adapter weights or base files; finite-weight scans are native collector attestations, not local re-scans.',
        'Full actual forward tensor arrays and training-token files are excluded. Preflight causal labels/EOS and archived forward row/exposure joins are checked; actual tensor hashes are retained evidence, not entirely recomputed here.',
        'Final vacancy XML is not in the capsule. Initial vacancy XML is verified directly; final process/queue/vacancy claim is bound to supplied validation JSON, not a fresh local query.',
        'Raw pair/candidate/final Main review were checked locally, but native formation and source/model bytes were not re-opened on node3. Hash custody is not authenticated model origin.',
        'Context distillation uses teacher-influenced own raw wakes under teacher-removed conditioning; lexical exclusion/Main review do not establish semantic nonleakage or clean lineage.',
        'V2 is after-inventory exploratory amendment 96a71289. Frozen V1 shortage, fixed slots, native TRY aliases and wrong predictions are preserved.',
        'Two rows per arm, one seed, unequal targets/input exposure; training losses are in-sample fit statistics, not comparable behavioral utility scores.',
        'No reload/readout/retention/generalization/action-quality evidence is included. No G3/P1/G5/H1/H2, clean-lineage or efficacy claim follows.',
        'This is author-side custody synthesis, not fresh independent implementation review. The validation JSON is supplied provenance, not an external signature.'
    ]
    return dict(sequence='SEQ115',date='2026-09-12',status='VERIFIED_PAIRED_FINITE_WRITE_METADATA_NO_BEHAVIORAL_CLAIM',
        claim='Two independently fresh-base LoRA fits completed finite 12-update writes on the four bound process-v2 wakes; behavioral usefulness is untested.',
        capsule_sha256=EXPECTED,plan_sha256=PLAN_SHA,archive_members_verified=len(members),input_sha256=inputs,
        candidate_sha256=plan['candidate_sha256'],main_review_sha256=plan['main_review_sha256'],
        recipe=plan['config'],base_model=plan['model'],model_origin=plan['model_origin'],source_root=plan['source_root'],
        init_adapter=None,conditioning=plan['conditioning'],claims=plan['claims'],arms=arms,aggregate=audit['aggregate'],
        costs=dict(controller_seconds=audit['controller_seconds'],worker_subtotal_seconds=audit['observed_verified_worker_seconds'],
            collector_seconds=validation['collection_seconds'],full_launch_to_final_vacancy_seconds=validation['full_launch_to_final_vacancy_seconds'],
            launch_utc=launch['started_utc'],final_vacancy_observed_wall=validation['final_vacancy']['observed_wall'],
            accounting='Trainer loops within workers; workers/cleanup and CPU gaps within controller; collection/wait within full observed launch-to-release interval. Never add these nested costs.'),
        raw_paths=raw_paths,limitations=limitations)


def markdown(result):
    rows=[]
    for arm, report in result['arms'].items():
        rows.append(f"| {arm} | 12 / 12 | {report['epoch_losses'][0]:.5f} | {report['final_loss']:.12g} | {report['tokens']['total']} / {report['tokens']['target']} | {report['train_tokens_seen']} / {report['exposure']['full_target_tokens_seen']} | {report['worker_reserved_seconds']:.6f} |")
    costs=result['costs']
    text=f"""# SEQ115 — completed process-v2 write synthesis

**2026-09-12; bounded offline author-side synthesis.** {result['claim']}

## Verified result

- Capsule SHA256 `{result['capsule_sha256']}` matches the supplied validation seal; all **{result['archive_members_verified']} members** match exact names/hashes and safe archive checks.
- Plan SHA256 `{result['plan_sha256']}`. Source snapshot `4c3064c1c3eef068951e9c3b2ca46630754564e7`.
- Both fit manifests/adapter metadata/attempts/receipts join the controller terminal and native collector audit. No partial-pair aggregate was accepted.
- Each arm: two own-wake rows, seed2, fresh unadapted base, rank8/alpha16/dropout0.05, AdamW LR1e-4, batch2, grad_accum1, 12 epochs/12 updates/12 microbatches/12 observed forwards. No warmstart, packing, splits, drops or skipped target rows.
- Before/after trainability inventories agree: frozen non-LoRA parameters, 20,185,088 trainable LoRA parameters across all seven projections in 28 layers; 392 saved LoRA tensors per arm. Native collector attests all saved weight values finite; **weights are not in this capsule**.

| Arm | Epochs / updates | First rounded epoch loss | Exact final loss | Corpus input / target+EOS | Presented input / target+EOS | Worker+cleanup seconds |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

All 12 epoch losses for each arm are finite; zero nonfinite batches. Full epoch arrays are in the JSON. These are repeated in-sample training losses, not behavioral measurements; lower P loss is **not** evidence P is more useful than A.

## Masks, exposure and lineage

Final Main review SHA256 `{result['main_review_sha256']}` and candidate SHA256 `{result['candidate_sha256']}` match the raw local files and native preflight pair. Four source slots/calls remain P lesson0/1 `0009/0024`, A lesson0/1 `0039/0054`.

Preflight rendered-context/raw-target hashes match the capsule summary and exact Main native-review bindings. Context labels are -100; complete unchanged own raw target is loss-bearing with exactly one EOS. First-target predictor positions: P 363/363; A 362/363. Raw target lengths P 15/15, A 14/15; including EOS P 16/16, A 15/16. Input lengths P 380/380, A 378/380. All 24 forward receipts agree with these rows and per-batch exposure, including actual row permutations.

P has no padding; A has two masked padding positions per batch, 24 over 12 batches. Both perform 9,120 padded input positions, but unpadded exposure differs (9,120/9,096). Totals: **24 updates, 18,216 unpadded input tokens, 18,240 padded positions, 756 supervised labels** including 48 EOS labels. Raw-target exposure is 360 P / 348 A. This is not token matched.

Both fits start from the same locally hash-pinned Qwen2.5-7B-Instruct base with `init_adapter=None`; neither uses the other arm or the earlier record-write adapter as a warmstart. This is **{result['conditioning']}**, not proof the child generated the target independently of teacher influence. Origin remains **{result['model_origin']}**; no clean-lineage claim.

## Costs — nested, not additive

- P training loop 38.5s; trainer wall 53.7s; supervised worker+cleanup 148.841920s.
- A training loop 9.4s; trainer wall 10.0s; supervised worker+cleanup 103.036209s.
- Worker-window subtotal **{costs['worker_subtotal_seconds']:.6f}s**, contained within controller **{costs['controller_seconds']:.6f}s** (1200s limit; workers <=600s; cleanup reserve140s).
- Collector **{costs['collector_seconds']:.6f}s** (300s limit). Full observed launch-to-final-vacancy **{costs['full_launch_to_final_vacancy_seconds']:.6f}s**, including waiting/CPU gaps/collection. **Do not add worker + controller + collector + full interval.**
- Initial archived vacancy XML/hash is verified. Final release is the supplied collector's process/session/vacancy/queue attestation, not a new query performed here. Timing asymmetry is recorded, not explained as an arm effect.

## Raw evidence paths

- Local capsule: `{CAPSULE}`; validation: `{VALIDATION}`.
- Native preflight: `/tmp/astra_process_native_pair_preflight_20260912.log`; raw pair: `/tmp/astra_process_pair_v2_20260912.json`.
- Candidate: `{result['raw_paths']['candidate']}`; **final** Main native review: `{result['raw_paths']['final_main_review']}`. The earlier `/tmp/astra_process_main_review_v2_20260912.json` is preliminary and is not substituted for the final review.
- Native writer root: `{result['raw_paths']['native_root']}`.
- Capsule members: `metadata/run/plan.json`; `metadata/run/run/result.json`; `metadata/run/run/{{P,A}}/{{process,supervision}}.json`; `metadata/run/fits/{{P,A}}/{{manifest,receipt,pre_update_trainability,post_update_trainability}}.json`; `metadata/run/fits/{{P,A}}/adapter/{{train_manifest,train_meta,adapter_config}}.json`; `metadata/run/fits/{{P,A}}/forwards/0001.json` through `0012.json`; `metadata/collection/{{audit,custody,material_summary,release}}.json`, `release.xml`; `metadata/launch/launch.json`.
- Exact member inventory, all supplied input hashes and native-only excluded-file hashes are in the synthesis JSON. Native weight hashes are listed per arm there; excluded weight bytes were not transferred or locally rescanned.

## Limitations and claim boundary

"""
    return text+'\n'.join('- '+item for item in result['limitations'])+'\n\n**Conclusion:** SEQ115 supports completed finite process-v2 writes with the specified masked exposures and fresh-base lineage. It does not support behavioral utility, transfer, better decisions, retention, or scientific promotion. No repo/Git/SSH/GPU or model execution; Main owns logging/archive.\n'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    result=analyze()
    result['synthesis_script_sha256']=digest(__file__)
    if args.write:
        outputs={BASE.with_suffix('.json'):json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',BASE.with_suffix('.md'):markdown(result)}
        require(all(not path.exists() for path in outputs),'synthesis outputs already exist; no overwrite')
        patch='*** Begin Patch\n'+''.join('*** Add File: '+str(path)+'\n'+''.join('+'+line+'\n' for line in text.splitlines()) for path,text in outputs.items())+'*** End Patch\n'
        subprocess.run(['apply_patch',patch],check=True)
    print(json.dumps(dict(status=result['status'],archive_members_verified=result['archive_members_verified'],arms={arm:row['final_loss'] for arm,row in result['arms'].items()},costs=result['costs']),sort_keys=True))


if __name__=='__main__':
    main()

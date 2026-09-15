"""Four independent native fits and fresh readouts under one global deadline."""

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time
from types import SimpleNamespace

from gpu import astra_portable_actor_bundle as portable
from gpu import orch_guided_native as native
from gpu import orch_oracle_repair_guard as guard
from gpu.orch_l2_rich_math_bootstrap import BUNDLE_SHA, read, sha, write
from gpu.orch_l2_shared_run import legacy_encode
from gpu.orch_math_rich_source import verify_archive
from gpu.orch_rich_intensity_screen import Engine as RichEngine
from organism_v6 import orch_guided_bridge as bridge
from organism_v6 import orch_l1_bootstrap_transfer as transfer
from organism_v6 import orch_l2_rich_math as encoding
from organism_v6 import orch_l2_shared as existing
from organism_v6 import orch_rich_breadth_bootstrap as policy


ROOT = Path('/localhome/local-rohing/orch_rich_breadth_bootstrap_20260915_attempt1')
COHORT_SHA = '24854584450f918ec0dd94c5525d7b26db27526fb918379c81126fc003fe3b55'
RECIPE = {key: existing.RECIPE[key] for key in ('optimizer', 'optimizer_kwargs', 'learning_rate', 'seed')}
PROGRAM = 'gpu.orch_rich_breadth_bootstrap_run'


class ReadoutEngine(RichEngine):
    def generate(self, messages, *, max_new_tokens):
        if max_new_tokens == policy.LEGACY_CAP:
            return portable.source.Engine.generate(self, messages, max_new_tokens=max_new_tokens)
        assert max_new_tokens == policy.MATH_CAP, 'only_bound_readout_caps'
        return super().generate(messages, max_new_tokens=max_new_tokens)


def layout_for(cell):
    assert cell in policy.CELLS
    return policy.BreadthLayout(16 if cell.startswith('ORIGINAL16_') else 26)


def replay_arm(cell):
    assert cell in policy.CELLS
    return 'FULL_TARGET' if cell.endswith('_FULL') else 'NEW_TRAJECTORY_LOSS_OFF'


def packet_name(cell):
    return 'FIRST16.json' if layout_for(cell).new_trajectory_rows == 16 else 'COMBINED26.json'


def validate_packet_files(root):
    packet = root / 'PACKET'
    assert sha(packet / 'MANIFEST.json') == policy.MANIFEST_SHA
    manifest = read(packet / 'MANIFEST.json')
    assert all(sha(packet / name) == entry['sha256'] for name, entry in manifest['files'].items())
    assert sha(packet / 'FIRST16.json') == policy.FIRST_SHA
    assert sha(packet / 'ADDITIONAL10.json') == policy.ADDITIONAL_SHA
    assert sha(packet / 'COMBINED26.json') == policy.COMBINED_SHA
    return policy.validate_packets(*(read(packet / name) for name in
        ('FIRST16.json', 'ADDITIONAL10.json', 'COMBINED26.json')))


def token_audit(encoded, layout, pad_id):
    reference_total = active_total = legacy_total = new_total = 0
    for update in range(1, layout.updates + 1):
        indexes, full, reference, active, scale = native.training_batch(
            encoded, layout, update, pad_id=pad_id)
        off_indexes, off, off_reference, off_active, off_scale = native.training_batch(
            encoded, layout, update, pad_id=pad_id, replay_arm='NEW_TRAJECTORY_LOSS_OFF')
        assert indexes == off_indexes and full['input_ids'] == off['input_ids']
        assert full['attention_mask'] == off['attention_mask'] and reference == off_reference
        assert scale == 1.0 and reference == active and off_scale == off_active / reference
        for position, index in enumerate(indexes):
            count = sum(label != -100 for label in full['labels'][position][1:])
            if index < 222:
                assert full['labels'][position] == off['labels'][position]
                legacy_total += count
            else:
                assert all(label == -100 for label in off['labels'][position])
                new_total += count
        reference_total += reference
        active_total += off_active
    assert reference_total == legacy_total + new_total and active_total == legacy_total
    return dict(full_supervised_tokens=reference_total, off_supervised_tokens=active_total,
        legacy_supervised_tokens=legacy_total, new_supervised_tokens=new_total,
        token_definition='Nonmasked next-token labels after causal shift; EOS included.',
        full_off_inputs_identical=True, full_off_legacy_labels_identical=True,
        full_off_new_labels_only_masked=True)


def prepare(root):
    assert root == ROOT and socket.gethostname() == 'ipp2-ovx-p6-09'
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == '' and not (root / 'PREPARE.json').exists()
    validation = validate_packet_files(root)
    assert sha(root / 'COHORT.json') == COHORT_SHA
    provenance = read(root / 'DATA_PROVENANCE.json')
    assert provenance['anscombe_outcomes_read'] is False
    assert all(sha(root / name) == digest for name, digest in provenance['legacy_files'].items())
    manifest = portable.read_manifest(guard.BUNDLE, expected_manifest_sha256=BUNDLE_SHA)
    base = portable.verify_base_files(guard.BUNDLE, guard.MODEL, expected_manifest_sha256=BUNDLE_SHA)
    identity = bridge.AdapterIdentity(str(Path(guard.BUNDLE) / 'adapter'), portable.PARENT_STATE,
        manifest['expected_base_sha256'], tuple(manifest['adapter_files'].items())).verify()
    tokenizer = native.source.native.load_local_tokenizer(guard.MODEL)
    legacy = legacy_encode(root, tokenizer)
    first = encoding.encode_packet(read(root / 'PACKET/FIRST16.json'), tokenizer)
    combined = encoding.encode_rows(read(root / 'PACKET/COMBINED26.json'), tokenizer)
    assert combined[:16] == first and len(combined) == 26
    write(root / 'ENCODER_CHECK.json', dict(status='PASS', rows=26, first16_exact=True,
        native_calls=0, model_loaded=False, target_bytes_unchanged=True,
        row_masks=[asdict(row) for row in combined]))
    audits = {}
    for size, new in ((16, first), (26, combined)):
        layout = policy.BreadthLayout(size)
        encoded = native.assemble_replay(legacy, new, layout, legacy_reference=legacy,
            eos_token_id=tokenizer.eos_token_id)
        audits[str(size)] = token_audit(encoded, layout, tokenizer.pad_token_id)
        audits[str(size)]['layout'] = layout.manifest('FULL_TARGET')
    assert audits['16']['legacy_supervised_tokens'] == audits['26']['legacy_supervised_tokens']
    prompts = read(root / 'COHORT.json')['prompts']
    prompt_lengths = [len(tokenizer.apply_chat_template(messages, tokenize=True,
        add_generation_prompt=True, return_dict=False)) for messages in prompts]
    assert len(prompt_lengths) == 32 and max(prompt_lengths) <= 2048
    legacy_readout = read(root / 'LEGACY_READOUT.json')
    assert len(legacy_readout['old_bank']) == len(legacy_readout['old_episodes']) == 16
    assert len(legacy_readout['held']['cases']) == 16
    write(root / 'TOKEN_AUDIT.json', audits)
    names = ('COHORT.json', 'DATA_PROVENANCE.json', 'LEGACY_MATERIAL.json', 'OLD_MASKS.json',
        'LEGACY_READOUT.json', 'PROTOCOL.md', 'SERVICE_IDENTITY.json', 'ENCODER_CHECK.json', 'TOKEN_AUDIT.json')
    prepared = dict(status='CPU_PREPARED_NO_MODEL', native_calls=0, fits=0,
        source_sha256=sha(root / 'source.tar'), source_files=verify_archive(root / 'source.tar', root / 'source'),
        files={name: sha(root / name) for name in names}, packet_validation=validation,
        initial=identity.document(), bundle=guard.BUNDLE, model_dir=guard.MODEL, base_verification=base,
        recipe=RECIPE, cells=policy.CELLS, math_prompt_lengths=prompt_lengths,
        seconds=policy.SECONDS, assigned_gpu_hours=policy.GPU_HOURS, readout_calls=policy.CALLS_TOTAL,
        training_generation=0, parent_calls=0, retries=0, prepared_unix=time.time())
    write(root / 'PREPARE.json', prepared)
    print(json.dumps(dict(status=prepared['status'], prepare_sha256=sha(root / 'PREPARE.json'),
        encoder_sha256=sha(root / 'ENCODER_CHECK.json'), token_audit_sha256=sha(root / 'TOKEN_AUDIT.json'),
        token_exposures={size: {key: value for key, value in audit.items() if key.endswith('_tokens')}
            for size, audit in audits.items()}), indent=2))


def validate_inputs(root):
    assert root == ROOT and socket.gethostname() == 'ipp2-ovx-p6-09' and not root.is_symlink()
    prepared = read(root / 'PREPARE.json')
    assert prepared['status'] == 'CPU_PREPARED_NO_MODEL' and prepared['native_calls'] == 0
    assert sha(root / 'source.tar') == prepared['source_sha256']
    assert verify_archive(root / 'source.tar', root / 'source') == prepared['source_files']
    assert all(sha(root / name) == digest for name, digest in prepared['files'].items())
    validate_packet_files(root)
    assert prepared['recipe'] == RECIPE and prepared['initial']['state_sha256'] == portable.PARENT_STATE
    return prepared


def check_deadline(lifetime, label):
    assert time.time() < lifetime['native_deadline_unix'], 'global_deadline:' + label


def train(root, cell):
    prepared = validate_inputs(root)
    lifetime = read(root / 'LIFETIME.json')
    uuid = policy.DEVICES[cell][1]
    assert os.environ['CUDA_VISIBLE_DEVICES'] == uuid
    assert ('CUDA_VISIBLE_DEVICES=' + uuid).encode() in Path('/proc/self/environ').read_bytes().split(b'\0')
    output = root / cell / 'fit'
    output.mkdir(parents=True, exist_ok=False)
    identity = bridge.AdapterIdentity.from_document(prepared['initial'])
    binding = bridge.StageBinding(root.name, bridge.ARMS[2], 0, 'training', identity,
        False, False, sha(root / 'PREPARE.json'))
    plan = SimpleNamespace(binding=lambda unused: binding,
        contract=SimpleNamespace(manifest=lambda unused: dict(recipe=RECIPE)),
        lineage=SimpleNamespace(arm=bridge.ARMS[2]))
    started = time.time()
    write(output / 'REQUEST.json', dict(cell=cell, input_adapter=identity.document(),
        process=native.process_identity(), uuid=uuid, started_unix=started, fresh_optimizer=True))
    try:
        loaded = native.load_training(plan, model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=uuid,
            context=native.StageContext(), check=lambda label: check_deadline(lifetime, label))
        write(output / 'LOADED.json', dict(process=loaded.process, observed=loaded.observed.document(),
            uuid=uuid, loaded_unix=time.time()))
        new = encoding.encode_rows(read(root / 'PACKET' / packet_name(cell)), loaded.engine.tokenizer)
        expected_masks = read(root / 'ENCODER_CHECK.json')['row_masks'][:len(new)]
        assert encoding.digest([asdict(row) for row in new]) == encoding.digest(expected_masks)
        legacy = legacy_encode(root, loaded.engine.tokenizer)
        layout = layout_for(cell)
        encoded = native.assemble_replay(legacy, new, layout, legacy_reference=legacy,
            eos_token_id=loaded.engine.tokenizer.eos_token_id)
        write(output / 'RECIPE.json', dict(recipe=RECIPE, layout=layout.manifest(replay_arm(cell)),
            packet_sha256=sha(root / 'PACKET' / packet_name(cell)), input_adapter=identity.document()))
        torch = loaded.engine.torch
        parameters = {name: parameter for name, parameter in loaded.engine.model.named_parameters() if native.is_lora(name)}
        total_active = total_reference = 0
        with (output / 'LOSSES.jsonl').open('x') as stream:
            for update in range(1, layout.updates + 1):
                check_deadline(lifetime, 'update')
                indexes, batch, reference, active, scale = native.training_batch(encoded, layout, update,
                    pad_id=loaded.engine.tokenizer.pad_token_id, replay_arm=replay_arm(cell))
                tensors = {name: torch.tensor(value, dtype=torch.long, device=loaded.engine.device)
                    for name, value in batch.items()}
                loaded.optimizer.zero_grad(set_to_none=True)
                with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                    loss = loaded.engine.model(**tensors, use_cache=False).loss * scale
                assert bool(torch.isfinite(loss))
                loss.backward()
                assert all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
                    for parameter in parameters.values())
                loaded.optimizer.step()
                total_active += active
                total_reference += reference
                record = dict(update=update, loss=loss.item(), rows=indexes, reference=reference,
                    active=active, scale=scale, finished_unix=time.time())
                stream.write(json.dumps(record) + '\n')
                stream.flush()
                if update == 1:
                    write(output / 'FIRST_UPDATE.json', record)
        assert all(bool(torch.isfinite(parameter).all()) for parameter in parameters.values())
        audit = read(root / 'TOKEN_AUDIT.json')[str(layout.new_trajectory_rows)]
        assert total_reference == audit['full_supervised_tokens']
        assert total_active == audit['full_supervised_tokens' if cell.endswith('_FULL') else 'off_supervised_tokens']
        loaded.engine.verify_base()
        loaded.engine.model.save_pretrained(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
        saved = bridge.AdapterIdentity(str(output / 'adapter'), native.state_hash(parameters), identity.base_sha256,
            tuple((path.name, sha(path)) for path in sorted((output / 'adapter').iterdir()) if path.is_file())).verify()
        assert native.observe_adapter(loaded.engine, saved) == saved
        write(output / 'COMPLETE.json', dict(status='COMPLETE', input_adapter=identity.document(),
            output_adapter=saved.document(), process=loaded.process, started_unix=started,
            finished_unix=time.time(), updates=layout.updates, training_generation=0, parent_calls=0,
            supervised_tokens=total_active, reference_tokens=total_reference,
            layout=layout.manifest(replay_arm(cell)), unchanged=saved.state_sha256 == identity.state_sha256))
    except BaseException as error:
        write(output / 'FAILED.json', dict(type=type(error).__name__, message=str(error), finished_unix=time.time()))
        raise


def reserve(output, position, messages, cap, metadata):
    assert type(position) is int and 0 <= position < policy.CALLS_PER_CELL
    assert cap == (policy.MATH_CAP if position < policy.MATH_TASKS else policy.LEGACY_CAP)
    path = output / f'CALL_{position:03d}.json'
    record = dict(position=position, messages=messages, max_new_tokens=cap,
        metadata=metadata, started_unix=time.time(), status='RESERVED')
    with path.open('x') as stream:
        json.dump(record, stream, indent=2)
    return path, record


def readout(root, cell):
    from gpu import astra_goal_quality_train as old

    prepared, lifetime = validate_inputs(root), read(root / 'LIFETIME.json')
    uuid = policy.DEVICES[cell][1]
    assert os.environ['CUDA_VISIBLE_DEVICES'] == uuid
    assert ('CUDA_VISIBLE_DEVICES=' + uuid).encode() in Path('/proc/self/environ').read_bytes().split(b'\0')
    fit = read(root / cell / 'fit/COMPLETE.json')
    assert fit['status'] == 'COMPLETE' and fit['updates'] == layout_for(cell).updates and fit['input_adapter'] == prepared['initial']
    output = root / cell / 'readout'
    output.mkdir(exist_ok=False)
    loaded = None
    count = 0
    failures = []
    try:
        identity = bridge.AdapterIdentity.from_document(fit['output_adapter'])
        binding = bridge.StageBinding(root.name, bridge.ARMS[1], 0, 'sealed_readout', identity,
            False, True, sha(root / 'PREPARE.json'))
        loaded = native.load_stage(binding, model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=uuid,
            context=native.StageContext(), check=lambda label: check_deadline(lifetime, label),
            predecessor_processes=(tuple(fit['process']),), engine_factory=ReadoutEngine)
        write(output / 'LOADED.json', dict(process=loaded.process, observed=loaded.observed.document(),
            uuid=uuid, loaded_unix=time.time(), parent_present=False, predecessor=fit['process']))

        def generate(messages, **metadata):
            nonlocal count
            check_deadline(lifetime, 'reserve')
            cap = policy.MATH_CAP if count < policy.MATH_TASKS else policy.LEGACY_CAP
            path, record = reserve(output, count, messages, cap, metadata)
            count += 1
            try:
                response = loaded.engine.generate(messages, max_new_tokens=cap)
                record.update(response=response, status='COMPLETE')
                return response
            except BaseException as error:
                failures.append(str(error))
                record.update(error=dict(type=type(error).__name__, message=str(error)), status='FAILED')
                raise
            finally:
                record['finished_unix'] = time.time()
                write(path, record)
                if count == 1:
                    write(output / 'FIRST_CALL.json', dict(path=path.name, sha256=sha(path),
                        status=record['status'], finished_unix=record['finished_unix']))

        cohort = read(root / 'COHORT.json')
        rows = []
        for task, messages in zip(cohort['tasks'], cohort['prompts']):
            response = generate(messages, purpose='math', task_id=task['id'])
            rows.append(dict(task_id=task['id'], family=task['family'], **transfer.score(task, response)))
            write(output / 'MATH_ROWS.json', rows)
        assert count == policy.MATH_TASKS
        legacy = read(root / 'LEGACY_READOUT.json')
        events = [dict(event=fact['event'], raw=episode['event']['raw'])
            for fact, episode in zip(legacy['old_bank'], legacy['old_episodes'])]
        retention = old.memory.recall(events, generate, output, 'OLD')
        audit = old.memory.audit.collect_cases(legacy['held'],
            lambda messages: generate(messages, purpose='audit'), coached=False)
        write(output / 'AUDIT.json', audit)
        assert count == policy.CALLS_PER_CELL and not failures, 'readout_calls_failed_or_incomplete_no_retry'
        observed = loaded.verify_unchanged()
        write(output / 'AFTER.json', dict(process=loaded.process, observed=observed.document(),
            unchanged=True, finished_unix=time.time()))
        write(output / 'COMPLETE.json', dict(status='COMPLETE', math_correct=sum(row['outcome_pass'] for row in rows),
            math_denominator=policy.MATH_TASKS, retention=retention, audit=audit['summary'], calls=count,
            process=loaded.process, fits=0, updates=0, parent_calls=0, finished_unix=time.time()))
    except BaseException as error:
        write(output / 'FAILED.json', dict(type=type(error).__name__, message=str(error), calls=count,
            finished_unix=time.time()))
        raise


def process_identity(pid):
    directory = Path('/proc') / str(pid)
    return dict(pid=pid, uid=directory.stat().st_uid,
        start_ticks=(directory / 'stat').read_text().rsplit(')', 1)[1].split()[19],
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def stop_owned(child, identity):
    if child.poll() is not None:
        return
    assert process_identity(child.pid) == identity and identity['uid'] == os.getuid()
    assert os.getpgid(child.pid) == child.pid
    os.killpg(child.pid, signal.SIGTERM)
    try:
        child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        assert process_identity(child.pid) == identity
        os.killpg(child.pid, signal.SIGKILL)
        child.wait(timeout=10)


def launch(root, original_started_unix=None):
    prepared = validate_inputs(root)
    assert os.geteuid() != 0 and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    ready = read(root / 'READY.json')
    publication = read(root / 'PUBLICATION.json')
    assert ready['prepare_sha256'] == sha(root / 'PREPARE.json') and ready['cpu_tests_passed']
    assert ready['source_sha256'] == prepared['source_sha256']
    assert ready['cpu_test_log_sha256'] == sha(root / 'CPU_TESTS.log')
    assert publication['ready_sha256'] == sha(root / 'READY.json')
    assert publication['dated_builder_line'].startswith('[Builder — RICH_BREADTH_BOOTSTRAP] ')
    assert publication['coordination_append_verified'] is True
    started = time.time() if original_started_unix is None else original_started_unix
    assert 0 < started <= time.time() < started + policy.SECONDS - 360
    assert started + policy.SECONDS < guard.LEASE_CUTOFF
    lifetime = dict(started_unix=started, hard_deadline_unix=started + policy.SECONDS,
        native_deadline_unix=started + policy.SECONDS - 360,
        assigned_gpu_hours_ceiling=policy.GPU_HOURS, readout_call_cap=policy.CALLS_TOTAL,
        training_generation=0, parent_calls=0, publication=publication, ready_sha256=sha(root / 'READY.json'))
    with (root / 'LIFETIME.json').open('x') as stream:
        json.dump(lifetime, stream, indent=2)
    children, logs, phases = {}, [], {}
    status = 'FAILED'

    def interrupted(signum, frame):
        raise SystemExit(128 + signum)

    def spawn(cell, phase):
        check_deadline(lifetime, 'launch_' + phase)
        index, uuid = policy.DEVICES[cell]
        log = (root / f'{cell}_{phase}.log').open('x')
        logs.append(log)
        command = [guard.PYTHON, '-B', '-m', PROGRAM, phase,
            '--root', str(root), '--cell', cell]
        child = subprocess.Popen(command, cwd=root / 'source', stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES=uuid, PYTHONPATH=str(root / 'source'),
                HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1'))
        identity = process_identity(child.pid)
        children[cell] = (child, identity)
        phases[cell] = phase
        write(root / f'{cell}_{phase}_LAUNCH.json', dict(identity=identity, phase=phase, cell=cell,
            uuid=uuid, index=index, command=command, started_unix=time.time()))

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        for cell, (index, uuid) in policy.DEVICES.items():
            snapshot = guard.scan(index, root / 'SERVICE_IDENTITY.json')
            write(root / f'{cell}_ADMISSION.json', snapshot)
            assert snapshot['clear'], ('fresh_ownership_blocked', cell, snapshot['blocking_reasons'])
        for cell in policy.CELLS:
            spawn(cell, 'train')
        while any(phase in ('train', 'readout') for phase in phases.values()):
            check_deadline(lifetime, 'supervise')
            for cell, (child, identity) in list(children.items()):
                if phases[cell] not in ('train', 'readout') or child.poll() is None:
                    continue
                phase = phases[cell]
                write(root / f'{cell}_{phase}_EXIT.json', dict(returncode=child.returncode, finished_unix=time.time()))
                if child.returncode != 0:
                    phases[cell] = 'FAILED'
                    continue
                if phase == 'train':
                    snapshot = guard.scan(policy.DEVICES[cell][0], root / 'SERVICE_IDENTITY.json')
                    write(root / f'{cell}_READOUT_ADMISSION.json', snapshot)
                    if not snapshot['clear']:
                        phases[cell] = 'OWNERSHIP_BLOCKED'
                        continue
                    spawn(cell, 'readout')
                else:
                    phases[cell] = 'COMPLETE'
            time.sleep(1)
        status = 'COMPLETE' if all(phase == 'COMPLETE' for phase in phases.values()) else 'CELL_FAILURE'
    except BaseException as error:
        write(root / 'LAUNCH_FAILED.json', dict(type=type(error).__name__, message=str(error), finished_unix=time.time()))
        raise
    finally:
        for child, identity in children.values():
            stop_owned(child, identity)
        for log in logs:
            log.close()
        release = {}
        for cell, (index, uuid) in policy.DEVICES.items():
            try:
                snapshot = guard.scan(index, root / 'SERVICE_IDENTITY.json')
                write(root / f'{cell}_RELEASE.json', snapshot)
                release[cell] = snapshot['clear']
            except Exception as error:
                release[cell] = False
                write(root / f'{cell}_RELEASE_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        if not all(release.values()):
            status = 'RELEASE_UNVERIFIED'
        write(root / 'TERMINAL.json', dict(status=status, cells=phases, release=release,
            started_unix=started, finished_unix=time.time(),
            conservative_assigned_gpu_hours=len(policy.CELLS) * (time.time() - started) / 3600,
            readout_calls=sum(len(list((root / cell / 'readout').glob('CALL_*.json'))) for cell in policy.CELLS),
            training_generation=0, parent_calls=0, retry=False, promotion=False))
    assert status == 'COMPLETE', status


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'train', 'readout', 'launch'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--cell', choices=policy.CELLS)
    options = parser.parse_args()
    if options.phase == 'prepare':
        prepare(options.root)
    elif options.phase == 'train':
        train(options.root, options.cell)
    elif options.phase == 'readout':
        readout(options.root, options.cell)
    else:
        launch(options.root)

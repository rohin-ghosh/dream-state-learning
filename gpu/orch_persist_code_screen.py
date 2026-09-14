"""Bounded, readonly portable-37ec persistent-code L1 screen."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tarfile
import time

from organism_v6 import orch_persist_code as ledger


MANIFEST_SHA = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'
STATE = '37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0'
PROTOCOL = 'research_notes/analysis/orch_persist_code_protocol.md'


def verify_archive(archive, directory):
    directory = Path(directory).resolve()
    checked = 0
    with tarfile.open(archive, 'r:gz') as packed:
        for member in packed.getmembers():
            path = directory / member.name
            if member.isfile():
                if not path.resolve().is_relative_to(directory) or path.is_symlink():
                    raise ValueError('archive source path escape')
                if hashlib.sha256(packed.extractfile(member).read()).digest() != hashlib.sha256(path.read_bytes()).digest():
                    raise ValueError('archive source byte drift: ' + member.name)
                checked += 1
            elif member.issym() and (not path.is_symlink() or os.readlink(path) != member.linkname):
                raise ValueError('archive symlink drift')
    if not checked:
        raise ValueError('empty source archive')
    return checked


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.partial')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True))
    temporary.replace(path)


def collect(engine, tokenizer, output, arm, tasks):
    codebase = ledger.Codebase(output / 'codebase')
    calls, episodes = [], []
    for task in tasks:
        previous, feedback, success = None, None, False
        episode = dict(task_id=task['id'], family=task['family'], calls=[], success=False,
                       correction=False, record=False, semantic='UNREVIEWED', admitted=False)
        for turn in range(6):
            records = deepcopy(codebase.records[-2:])
            messages, prefix = ledger.messages(task, records, arm, previous, feedback, record=success)
            while len(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)) > 1536 and records:
                records.pop(0)
                messages, prefix = ledger.messages(task, records, arm, previous, feedback, record=success)
            input_tokens = len(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True))
            if input_tokens > 1536:
                episode['stop'] = 'context_bound_no_truncation'
                break
            call = dict(id=len(calls), task_id=task['id'], turn=turn, arm=arm,
                        phase='record' if success else 'repair', messages=messages,
                        student_prefix=prefix, parent_guidance_in_student_prefix=False,
                        loss_policy='child_target_only_no_fit', response=None,
                        feedback_before=feedback, visible_record_ids=[item['call_id'] for item in records],
                        semantic='UNREVIEWED', admitted=False)
            calls.append(call)
            episode['calls'].append(call['id'])
            try:
                response = engine.generate(deepcopy(messages), max_new_tokens=512)
                call['response'] = response
                if response['prompt_tokens'] != input_tokens or len(response['token_ids']) > 512:
                    raise RuntimeError('native token accounting mismatch')
                if not response['terminal'] or response['truncated']:
                    raise ValueError('unfinished child response')
                action, narrative = ledger.parse_action(response['raw'])
                narrative_tokens = len(tokenizer.encode(narrative, add_special_tokens=False))
                call['narrative_tokens'] = narrative_tokens
                call['rich_length_ok'] = arm != 'RICH' or 150 <= narrative_tokens <= 400
                call['action'] = action
                if success:
                    if set(action) != {'record'}:
                        raise ValueError('successful repair now requires own record')
                    codebase.record(task['id'], action['record'], call['id'])
                    episode['record'] = True
                    episode['stop'] = 'own_record_written'
                else:
                    if set(action) != {'expression'}:
                        raise ValueError('repair requires expression')
                    new_feedback = codebase.patch(task, action['expression'])
                    call['oracle_after'] = new_feedback
                    if new_feedback['success']:
                        episode['correction'] = bool(feedback and 'expected' in feedback and not feedback['success']
                                                     and previous != action['expression'])
                        success = episode['success'] = True
                    previous, feedback = action['expression'], new_feedback
            except (ValueError, SyntaxError, TypeError, KeyError) as error:
                call['format_or_oracle_error'] = str(error)
                feedback = dict(success=False, error=str(error))
            finally:
                write(output / f'CALL_{call["id"]:03d}.json', call)
            if episode['record'] or (not success and turn == 4):
                break
        episode.setdefault('stop', 'repair_budget_exhausted' if not success else 'record_missing')
        episodes.append(episode)
        write(output / 'PROGRESS.json', dict(episodes=episodes, calls=len(calls)))
    return dict(episodes=episodes, model_calls=len(calls), tasks=len(tasks),
                successes=sum(item['success'] for item in episodes),
                own_records=sum(item['record'] for item in episodes),
                corrections=sum(item['correction'] and item['record'] for item in episodes),
                reference_successes=sum(ledger.check_expression(task, 'sum(values)')['success'] for task in tasks),
                semantic_admitted_rows=0, fit_ready=False, trainingAllowed=False,
                claim='L1_EXPOSED_DEV_COLLECTION_NOT_LEARNING_OR_TRANSFER')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--model-dir', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--arm', choices=('RICH', 'TERSE'), required=True)
    parser.add_argument('--gpu-uuid')
    parser.add_argument('--deadline-epoch', type=float)
    parser.add_argument('--prepare', action='store_true')
    options = parser.parse_args(argv)
    from gpu import astra_portable_actor_bundle as portable
    from gpu import astra_experienced_event_microloop as source

    output = Path(options.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    tasks = ledger.build_tasks(count=8)
    started = time.time()
    binding = dict(source_commit=options.source_commit, manifest_sha256=MANIFEST_SHA,
                   driver_sha256=source.file_hash(__file__), helper_sha256=source.file_hash(ledger.__file__),
                   protocol_sha256=source.file_hash(Path(__file__).resolve().parents[1] / PROTOCOL),
                   task_roster_sha256=ledger.digest(tasks), partition=ledger.PARTITION)
    result = dict(binding=binding, arm=options.arm, started_epoch=started, fits=0, updates=0,
                  native_calls_cap=48, input_cap=1536, generated_cap=512, total_context_cap=2048,
                  parent_present=False, richness_scaffold=options.arm == 'RICH', args=vars(options))
    write(output / 'REQUEST.json', result)
    write(output / 'TASKS.json', tasks)

    def check(label):
        if time.time() >= options.deadline_epoch:
            raise RuntimeError('hard deadline: ' + label)

    try:
        portable.verify_base_files(options.bundle, options.model_dir, expected_manifest_sha256=MANIFEST_SHA)
        if options.prepare:
            result.update(status='PREPARED_NO_MODEL', model_calls=0, finished_epoch=time.time())
            write(output / 'RESULT.json', result)
            return result
        if os.environ.get('CUDA_VISIBLE_DEVICES') != options.gpu_uuid or not options.gpu_uuid:
            raise ValueError('exact assigned UUID visibility required')
        if not options.deadline_epoch or not 0 < options.deadline_epoch - time.time() <= 1740:
            raise ValueError('bounded deadline required')
        if os.environ.get('HF_HUB_OFFLINE') != '1' or os.environ.get('TRANSFORMERS_OFFLINE') != '1':
            raise ValueError('offline local loading required')
        arguments = portable.read_bundle(options.bundle, expected_manifest_sha256=MANIFEST_SHA,
                                         model_dir=options.model_dir, device='cuda:0', gpu_uuid=options.gpu_uuid)
        tokenizer = source.native.load_local_tokenizer(options.model_dir)
        engine = source.Engine(arguments, tokenizer, check=check)
        from organism_v6.pcfl_vertical_train import _state_hash

        parameters = {name: value for name, value in engine.model.named_parameters()
                      if '.lora_A.' in name or '.lora_B.' in name}
        if not parameters or _state_hash(parameters) != STATE:
            raise ValueError('37ec loaded-state mismatch')
        if any(value.requires_grad for value in engine.model.parameters()):
            raise ValueError('readonly parameters required')
        write(output / 'NATIVE.json', dict(runtime=engine.runtime, pid=os.getpid(), gpu_uuid=options.gpu_uuid,
                                         state_before=STATE, loaded_epoch=time.time()))
        result.update(collect(engine, tokenizer, output, options.arm, tasks))
        engine.verify_base()
        if _state_hash(parameters) != STATE:
            raise ValueError('readonly state changed')
        if source.file_hash(__file__) != binding['driver_sha256'] or source.file_hash(ledger.__file__) != binding['helper_sha256']:
            raise ValueError('source drift')
        result.update(status='COMPLETE', state_before=STATE, state_after=STATE,
                      frozen_base_unchanged=True, finished_epoch=time.time())
        write(output / 'RESULT.json', result)
        return result
    except BaseException as error:
        result.update(status='FAILED', error=repr(error), finished_epoch=time.time())
        write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()

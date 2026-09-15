"""Read-only canonical C1-C4 TRAIN delivery and realized-dose reduction."""

import argparse
import ast
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path


ROOT = Path('/tmp/orch_route_parent_campaign_20260915_canonical102')
TOKENIZER = Path('/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28/tokenizer.json')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoding_check(row):
    inputs, labels, target = row['input_ids'], row['labels'], row['target_ids']
    require(len(inputs) == len(labels) and target, 'encoding_shape')
    active = [index for index, label in enumerate(labels) if label != -100]
    require(active and active == list(range(active[0], active[-1]+1)), 'single_target_interval')
    require([labels[index] for index in active] == target, 'exact_supervised_target')
    require([inputs[index] for index in active] == target, 'label_input_correspondence')
    require(active[0] > 0 and active[-1] < len(inputs)-1, 'masked_prefix_and_suffix')
    return len(target)


def dose_reduction(masks, losses):
    sizes = [encoding_check(row) for row in masks]
    counts = [0]*len(masks)
    for update, loss in enumerate(losses, 1):
        require(loss['update'] == update and len(loss['rows']) == 4, 'actual_update_sequence')
        for index in loss['rows']:
            require(type(index) is int and 0 <= index < len(masks), 'actual_row_index')
            counts[index] += 1
        require(sum(sizes[index] for index in loss['rows']) == loss['active'], 'actual_active_token_count')
    return dict(updates=len(losses), actual_row_presentations=counts,
        total_supervised_token_presentations=sum(size*count for size,count in zip(sizes,counts)),
        new_supervised_token_presentations=sum(sizes[index]*counts[index] for index in range(222,len(masks))),
        legacy_supervised_token_presentations=sum(sizes[index]*counts[index] for index in range(min(222,len(masks)))),
        new_target_tokens_including_eot=sizes[222:],
        new_target_presentations=sum(counts[222:]), legacy_row_presentations=sum(counts[:222]))


def reflection_prefix(record, instruction):
    evidence = dict(task=record['task'], messages=record['messages'], reads=record['reads'],
        routes=record['routes'], terminal_reason=record['terminal_reason'],
        outcome='SUCCESS' if record['correct'] else 'FAILURE_NOT_CORRECT_ANSWER',
        attempted_actions_are_not_gold=True,
        attempts=[dict(response={key: capture['response'][key] for key in
            ('raw','terminal','truncated','token_ids') if key in capture['response']}
            if capture['response'] else None, error=capture['error']) for capture in record['captures']])
    return [dict(role='system',content=instruction),
        dict(role='user',content=json.dumps(evidence,sort_keys=True))]


def parent_presence(messages, parent):
    return any(parent in message['content'] for message in messages)


def target_text_binding(row, capture, tokenizer):
    raw = capture['response']['raw']
    expected = raw+'<|im_end|>'
    require(tokenizer.decode(row['target_ids'],skip_special_tokens=False)==expected, 'supervised_child_bytes')
    require(tokenizer.decode(capture['response']['token_ids'],skip_special_tokens=False)==expected,
        'generated_child_bytes')
    require(row['target_ids']==tokenizer.encode(raw,add_special_tokens=False).ids+
        [tokenizer.token_to_id('<|im_end|>')], 'canonical_reencoding_of_child_bytes')
    return row['target_ids']==capture['response']['token_ids']


def audit(root):
    require(root == ROOT, 'canonical_train_root_only')
    from tokenizers import Tokenizer
    tokenizer = Tokenizer.from_file(str(TOKENIZER))
    require(file_hash(TOKENIZER)=='c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539', 'bound_native_tokenizer')
    references = {}
    bounded_refs = set()

    def read(path):
        require(path.is_relative_to(root), 'root_scope')
        relative = path.relative_to(root)
        require('readout' not in relative.parts and path.name not in ('SOURCE.json','COHORT.json'), 'train_only')
        if path.name.startswith('CALL_') or 'parent_queue' in relative.parts:
            bounded_refs.add(str(relative))
            require(len(bounded_refs) <= 100, 'parent_call_reference_cap')
        references[str(relative)] = file_hash(path)
        return json.loads(path.read_text())

    prepare = read(root/'PREPARE.json')
    sources = {}
    for name in ('gpu/orch_route_parent_campaign_run.py', 'organism_v6/orch_l2_guided.py',
            'gpu/orch_guided_native.py', 'organism_v6/orch_guided_bridge.py',
            'organism_v6/orch_route_parent_campaign.py', 'organism_v6/orch_route_parent_campaign_canonical.py',
            'organism_v6/experienced_event_goal_replay_layout.py'):
        source = root/'source'/name
        sources[name] = file_hash(source)
        require(sources[name] == prepare['source_files'][name], 'frozen_source_binding')
    tree = ast.parse((root/'source/organism_v6/orch_route_parent_campaign.py').read_text())
    constants = {target.id: ast.literal_eval(node.value) for node in tree.body
        if isinstance(node,ast.Assign) for target in node.targets
        if isinstance(target,ast.Name) and target.id in ('GUIDANCE','REFLECTION')}
    rows = []
    initial = {}
    task_orders = {}
    initial_prefixes = {}
    prior_output = {}
    legacy_hash = None
    training_sources = {}
    for arm in ('GUIDED','UNPARENTED'):
        for cycle in range(1,5):
            folder = root/arm/f'cycle{cycle}'
            experience = folder/'experience'
            request = read(experience/'REQUEST.json')
            loaded = read(experience/'LOADED.json')
            require(loaded['parent_present']==(arm=='GUIDED'), 'loaded_parent_visibility')
            complete = read(experience/'COMPLETE.json')
            sleep = read(folder/'sleep/COMPLETE.json')
            dose = read(folder/'sleep/DOSE_EXPOSURE.json')
            require(complete['status'] == sleep['status'] == 'COMPLETE', 'completed_train_stages')
            if cycle == 1:
                initial[arm] = request['input_adapter']
            else:
                require(request['input_adapter'] == prior_output[arm], 'saved_child_to_next_training')
            require(sleep['input_adapter'] == request['input_adapter'], 'collection_sleep_identity')
            prior_output[arm] = sleep['output_adapter']
            episodes = [read(path) for path in sorted(experience.glob('EPISODE_*.json'))]
            require(len(episodes) == 2, 'two_train_episodes')
            master = f'ORCH-ROUTE-PARENT-20260915-CANONICAL102-TRAIN-C{cycle-1}-W0'
            source_path = root/'source_capture'/(master+'.json')
            source_collection = read(source_path)
            require(source_collection['world']['master']==master, 'exact_train_source_world')
            store = {record['edge']['event']:record['event']['raw'] for record in source_collection['records']
                if record['accepted']}
            available_events = {record['edge']['event'] for record in source_collection['records']}
            require(all(set(episode['task']['events'])==available_events for episode in episodes), 'same_train_source_tasks')
            feedback_matches = 0
            for episode in episodes:
                for index,message in enumerate(episode['messages'][:-1]):
                    if message['role'] != 'assistant':
                        continue
                    command = message['content'].rstrip('\n').splitlines()[-1]
                    if command.startswith('READ EVENT '):
                        address = command[len('READ EVENT '):]
                        if address in store:
                            require(episode['messages'][index+1]==dict(role='user',content=store[address]),
                                'actual_public_feedback_matches_shared_source')
                            feedback_matches += 1
            training_sources[cycle] = dict(path=str(source_path),sha256=file_hash(source_path),
                store_sha256=digest(store),accepted_events=len(store),total_events=len(available_events))
            tasks = [digest(episode['task']) for episode in episodes]
            task_orders[(arm,cycle)] = tasks
            initial_prefixes[(arm,cycle)] = [digest(episode['captures'][0]['student_prefix']) for episode in episodes]
            parents = []
            for path in sorted((root/'parent_queue').glob(f'*_{arm}_C{cycle}.request.json')):
                parent_request = read(path)
                response = read(path.with_name(path.name.replace('.request.json','.response.json')))
                require(response['id'] == parent_request['id'] and response['request_sha256'] == digest(parent_request),
                    'completed_parent_request_response_binding')
                require(digest(parent_request['payload']['task']) in tasks, 'parent_train_task_binding')
                parents.append((parent_request,response['result']))
            call_paths = sorted(experience.glob('CALL_*.json'))
            require(len(call_paths) == sum(len(record['captures']) for record in episodes)+2, 'call_sequence_inventory')
            cursor = 0
            selected = []
            action_captures = 0
            responses_with_parent = 0
            interventions_delivered = 0
            reflection_guidance_delivered = 0
            parent_speak = sum(result.get('speak') is True for unused,result in parents)
            parent_silent = sum(result.get('speak') is False for unused,result in parents)
            reflection_failures = Counter()
            admitted = complete['reflections']
            new_targets = []
            for ordinal, record in enumerate(episodes,1):
                task_parents = [(req,result) for req,result in parents if digest(req['payload']['task']) == tasks[ordinal-1]]
                action_parents = [result for req,result in task_parents if req['payload']['turn'] != 6]
                coaches = [result for req,result in task_parents if req['payload']['turn'] == 6]
                require(action_parents == record['parent_messages'], 'parent_result_to_episode')
                if arm == 'GUIDED':
                    require(len(coaches)==1, 'one_reflection_coach')
                    require(read(experience/f'SLEEP_COACH_{ordinal:02d}.json')==coaches[0], 'coach_result_binding')
                else:
                    require(not task_parents and not record['parent_messages'], 'unparented_no_parent_records')
                private = [constants['GUIDANCE']] if arm == 'GUIDED' else []
                private += [result['message'] for result in action_parents+coaches
                    if result.get('speak') and result.get('message')]
                for capture in record['captures']:
                    action_captures += 1
                    expected = deepcopy(capture['student_prefix'])
                    for intervention in capture['parent_messages']:
                        if intervention.get('speak') and intervention.get('message'):
                            expected[-1]['content'] += '\n\nPARENT LEARNING COACH:\n'+intervention['message']
                    require(expected == capture['messages'], 'exact_action_parent_assembly')
                    if capture.get('response'):
                        require(capture['response']['messages']==expected, 'actual_generation_messages')
                        responses_with_parent += bool(capture['parent_messages'] and
                            any(item.get('speak') and item.get('message') for item in capture['parent_messages']))
                for intervention in action_parents:
                    if intervention.get('speak') and intervention.get('message'):
                        require(any(capture.get('response') and parent_presence(capture['response']['messages'],intervention['message'])
                            for capture in record['captures']), 'parent_completed_but_not_delivered')
                        interventions_delivered += 1
                reflection = read(experience/f'REFLECTION_{ordinal:02d}.json')
                require(reflection['episode_sha256']==digest(record), 'reflection_episode_binding')
                neutral = reflection_prefix(record,constants['REFLECTION'])
                expected = deepcopy(neutral)
                if private:
                    expected[-1]['content'] += '\nTRAINING WHEELS (not evidence, do not quote):\n'+'\n'.join(private)
                require(reflection['response']['messages']==expected, 'actual_reflection_private_input')
                reflection_guidance_delivered += bool(private)
                for index,response in ((cursor,record['captures'][0]['response']),
                        (cursor+len(record['captures']),reflection['response'])):
                    actual = read(call_paths[index])
                    require(actual['response']==response and actual['messages']==response['messages'], 'sample_call_crosscheck')
                    selected.append(call_paths[index].name)
                cursor += len(record['captures'])+1
                if not reflection['admitted']:
                    reflection_failures[reflection.get('error','unknown')] += 1
                    continue
                item = next(item for item in admitted if item['episode_sha256']==digest(record))
                require(item['sha256']==digest(item['capture']) and item['capture']['response']==reflection['response'], 'admitted_child_binding')
                require(item['private']==private and item['capture']['student_prefix']==neutral, 'neutral_supervision_prefix')
                require(all(not parent_presence(neutral,lesson) and lesson not in reflection['response']['raw']
                    for lesson in private), 'private_parent_text_in_training_data')
                target_words = ' '.join(reflection['response']['raw'].split())
                require(all(not any(' '.join(lesson.split()[start:start+8]) in target_words
                    for start in range(max(0,len(lesson.split())-7))) for lesson in private), 'private_eight_word_span_in_target')
                new_targets.append(item['capture'])
            if sleep['updates']:
                masks = read(folder/'sleep/MASKS.json')
                require(len(masks[222:])==len(new_targets), 'actual_target_row_count')
                different_tokenizations = 0
                for mask,capture in zip(masks[222:],new_targets):
                    different_tokenizations += not target_text_binding(mask,capture,tokenizer)
                    first_target = next(index for index,label in enumerate(mask['labels']) if label != -100)
                    expected_prefix = ''.join('<|im_start|>'+message['role']+'\n'+message['content']+
                        '<|im_end|>\n' for message in capture['student_prefix'])+'<|im_start|>assistant\n'
                    require(tokenizer.decode(mask['input_ids'][:first_target],skip_special_tokens=False)==expected_prefix,
                        'actual_encoded_neutral_prefix')
                    capture_private = next(item['private'] for item in admitted if item['capture']==capture)
                    require(all(lesson not in expected_prefix for lesson in capture_private), 'parent_not_encoded_in_prefix')
                losses_path = folder/'sleep/LOSSES.jsonl'
                references[str(losses_path.relative_to(root))] = file_hash(losses_path)
                losses = [json.loads(line) for line in losses_path.read_text().splitlines()]
                measured = dose_reduction(masks,losses)
                require(measured['actual_row_presentations']==dose['actual_row_presentations'], 'reported_actual_presentations')
                require(measured['updates']==sleep['updates'] and measured['new_target_presentations']==dose['actual_new_target_presentations'], 'dose_receipt_agreement')
                current_legacy_hash = digest(masks[:222])
                if legacy_hash is None:
                    legacy_hash = current_legacy_hash
                require(current_legacy_hash==legacy_hash, 'legacy_encoded_rows_identical')
                recipe = read(folder/'sleep/RECIPE.json')
                recipe_summary = {key:recipe[key] for key in ('optimizer','learning_rate','batch_size','seed','trajectory_presentations')}
            else:
                require(not admitted and not (folder/'sleep/MASKS.json').exists(), 'zero_yield_no_fit')
                measured = dose_reduction([],[])
                recipe_summary = None
                different_tokenizations = 0
            measured.pop('actual_row_presentations')
            rows.append(dict(arm=arm,cycle=cycle,training_task_hashes_in_order=tasks,
                input_state_sha256=request['input_adapter']['state_sha256'],output_state_sha256=sleep['output_adapter']['state_sha256'],
                parent_completed_response_bindings=len(parents),parent_speak=parent_speak,parent_silent=parent_silent,
                completed_action_interventions_in_generation=interventions_delivered,
                reflection_coaches_in_generation=sum(result.get('speak') is True for unused,result in parents if unused['payload']['turn']==6),
                all_action_capture_count=action_captures,actual_action_responses_with_parent=responses_with_parent,
                reflection_calls_with_private_guidance=reflection_guidance_delivered,
                independent_call_file_sample=selected,all_call_files_available=len(call_paths),
                admitted_targets=len(admitted),reflection_rejections=dict(reflection_failures),
                private_prefix_and_exact_target_checks=True,recipe=recipe_summary,realized_dose=measured))
            rows[-1]['same_text_different_generated_vs_reencoded_token_sequences'] = different_tokenizations
            rows[-1]['public_read_feedback_matches_shared_source'] = feedback_matches
            rows[-1]['initial_public_prefix_hashes_in_order'] = initial_prefixes[(arm,cycle)]
            rows[-1]['loaded_parent_present'] = loaded['parent_present']
            rows[-1]['complete_parent_free_field'] = complete['parent_free']
    require(initial['GUIDED']==initial['UNPARENTED']==prepare['initial'], 'identical_initial_child')
    source_request = read(root/'source_capture/REQUEST.json')
    require(source_request['input_adapter']==initial['GUIDED'], 'shared_initial_source_child')
    for name,expected in initial['GUIDED']['files']:
        require(file_hash(Path(initial['GUIDED']['path'])/name)==expected, 'initial_adapter_actual_bytes')
    require(all(task_orders[('GUIDED',cycle)]==task_orders[('UNPARENTED',cycle)] for cycle in range(1,5)), 'matched_training_task_order')
    require(all(initial_prefixes[('GUIDED',cycle)]==initial_prefixes[('UNPARENTED',cycle)] for cycle in range(1,5)), 'matched_initial_public_prefixes')
    totals = {}
    for arm in ('GUIDED','UNPARENTED'):
        selected = [row for row in rows if row['arm']==arm]
        totals[arm] = {key:sum(row['realized_dose'][key] for row in selected) for key in
            ('updates','total_supervised_token_presentations','new_supervised_token_presentations',
             'legacy_supervised_token_presentations','new_target_presentations','legacy_row_presentations')}
        totals[arm].update(parent_completed=sum(row['parent_completed_response_bindings'] for row in selected),
            admitted_targets=sum(row['admitted_targets'] for row in selected),
            action_captures=sum(row['all_action_capture_count'] for row in selected),
            action_captures_with_parent=sum(row['actual_action_responses_with_parent'] for row in selected))
    return dict(schema='R127_TRAIN_PARENTING_DELIVERY_AND_DOSE_V1',native_root=str(root),
        scope='GUIDED/UNPARENTED TRAIN C1-C4 only; no readout, FINAL, new assay, model/provider/GPU operations',
        initial=initial['GUIDED'],same_task_order=True,same_initial_public_prefixes=True,legacy_encoded_rows_sha256=legacy_hash,
        shared_training_sources=training_sources,initial_adapter_files_verified=True,
        source_capture_initial_identity_verified=True,
        source_hashes=sources,rows=rows,totals=totals,references=references,
        tokenizer=dict(path=str(TOKENIZER),sha256=file_hash(TOKENIZER),CPU_only=True,no_model_loaded=True),
        coverage=dict(episodes=16,reflections=16,parent_request_response_and_call_file_refs=len(bounded_refs),
            reference_cap=100,selection='All 32 TRAIN parent request+response pairs (64 files); first action and reflection CALL per episode (32 files). All action capture messages checked in all 16 episode records.',
            bounded_file_refs=sorted(bounded_refs)),
        limits=['Tokenizer-only native verification checks exact decoded child bytes, canonical target re-encoding, neutral prefix and masks; generated token segmentation can differ while decoding to identical bytes.',
            'No semantic paraphrase detector or causal dependence inference from textual presence.',
            'Historical code constructs a fresh AdamW optimizer for each sleep, while carrying adapter weights.',
            'Historical experience COMPLETE.parent_free is false for both arms because it records the readout-phase predicate, not actual parent visibility. LOADED and actual generation messages establish parent absence here.',
            'Equal update and row-presentation counts do not imply equal target-token exposure or matched generated experiences.',
            'One trajectory per arm; no independent training replicas. This audit does not establish transfer benefit.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=ROOT)
    args = parser.parse_args()
    print(json.dumps(audit(args.root),sort_keys=True,indent=2))

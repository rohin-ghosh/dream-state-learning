def checked_state(wrapped):
    require(wrapped['sha256'] == digest(wrapped['state']), 'wrapped_state_digest')
    return wrapped['state']


def committed_triple(request_record, response_record, commit_record):
    require([item['kind'] for item in [request_record, response_record, commit_record]] ==
            ['REQUEST', 'RESPONSE', 'COMMITTED'], 'real_generation_triple')
    requested = request_record['document']
    request = {key: value for key, value in requested.items() if key != 'resume_state'}
    response = response_record['document']
    committed = commit_record['document']
    before = checked_state(requested['resume_state'])
    after = checked_state(committed['state'])
    require(request['split'] == 'TRAIN' and request['render_receipt']['all_history_tokens_masked'] is True
        and before['pending'] == digest(request) == response['request_sha256'], 'original_REQUEST_RESPONSE_binding')
    require(after['pending'] is None and after['rows'][:-1] == before['rows']
        and len(after['rows']) == len(before['rows']) + 1, 'committed_own_row_only')
    row = after['rows'][-1]
    require(committed['segment'] == request['segment'] == len(before['rows'])
        and committed['source_sha256'] == row['source_sha256'] == digest(response)
        and row['prefix'] == request['messages'] and row['target'] == response['response']['raw']
        and row['token_ids'] == response['response']['token_ids'] and row['actor'] == 'child'
        and row['split'] == 'TRAIN' and row['prefix_loss'] is False and row['target_loss'] is True,
        'exact_own_child_target_and_mask')
    require(after['sleep_frontier'] == before['sleep_frontier']
        and after['sleep_receipts'] == before['sleep_receipts']
        and after['model_state_sha256'] == before['model_state_sha256'], 'generation_not_training_or_sleep')
    return dict(segment=committed['segment'], row_count=len(after['rows']),
        request_index=request_record['index'], response_index=response_record['index'],
        commit_index=commit_record['index'], original_target_binding=True,
        prefix_masked=True, semantic_correctness_or_learning_claim=False)


def recover(request):
    life = request['life']
    require(life['life_id'] == 'C5' and life['node'] == 'ovx3', 'only_exact_C5_scope')
    reader = Reader()
    reader.metadata_bytes = request['prior_reads']['metadata_bytes']
    reader.journal_bytes = request['prior_reads']['journal_bytes']
    reader.record_count = request['prior_reads']['record_count']
    result = dict(life_id='C5', status='RECOVERY_WITNESS_INCOMPLETE', source_root=life['storage_root'])
    references = {}
    try:
        before, argv = identity(life['inventory_identity']['pid'])
        require(before['start_ticks'] == life['inventory_identity']['start_ticks'], 'exact_recovered_native')
        documents = {}
        for label, expected in request['metadata_refs'].items():
            document, actual = reader.document(expected['path'])
            require(actual['sha256'] == expected['sha256'], 'same_recovery_metadata:' + label)
            documents[label] = document
            references[label] = actual
        config, plan = documents['config'], documents['plan']
        require(config['resume'] is True and config['plan_path'] == references['plan']['path']
            and config['plan_sha256'] == references['plan']['sha256']
            and plan['root'] == life['storage_root'] == life['process_plan_root']
            and plan['source_root'] == request['expected_runtime_source'] == before['cwd']
            and argv[argv.index('--config') + 1] == references['config']['path'], 'same_recovered_root_plan_source')
        go, ready, execution = documents['go'], documents['ready'], documents['execution']
        ref_pair = lambda value: {key: value[key] for key in ['path', 'sha256']}
        require(go['schema'] == 'R166_C5_RETIRED_RECOVERY_MAIN_GO_V1'
            and go['issuer'] == 'Main' and go['decision'] == 'GO'
            and go['binding'] == ready['required_GO_binding']
            and go['binding']['request'] == ref_pair(references['request'])
            and go['binding']['plan'] == ref_pair(references['readiness_plan'])
            and references['readiness_plan']['sha256'] == references['plan']['sha256']
            and documents['readiness_plan'] == plan
            and go['binding']['cpu_proof'] == ref_pair(references['preflight_cpu_proof'])
            and documents['preflight_cpu_proof'] == documents['proof']
            and go['binding']['recovery_custody'] == ref_pair(references['custody']), 'consumed_recovery_GO_binding')
        require(execution['go'] == ref_pair(references['go'])
            and execution['custody'] == ref_pair(references['custody'])
            and execution['prepared'] == ref_pair(references['prepared'])
            and execution['prior_retirement'] == ref_pair(references['retirement'])
            and execution['no_retirement_performed'] is True and execution['no_retry'] is True,
            'authentic_retired_recovery_execution')
        launch = documents['launch']
        require(documents['prepared']['plan'] == ref_pair(references['plan'])
            and documents['prepared']['config'] == ref_pair(references['config']), 'prepared_control_copy_binding')
        require(launch['plan_sha256'] == references['plan']['sha256']
            and launch['guard_sha256'] == references['config']['sha256']
            and go['not_before_unix'] <= launch['started_unix'] <= go['expires_unix'], 'historical_launch_GO_window')
        root = Path(life['storage_root'])
        manifest, manifest_ref = reader.document(root / 'stream/JOURNAL.json')
        records, record_refs = {}, {}
        previous = None
        for index in range(2899, 2911):
            value, reference = record(reader, root, index, manifest)
            if previous is not None:
                require(value['previous_sha256'] == previous, 'recovery_to_committed_contiguous_chain')
            if str(index) in request['record_refs']:
                require(reference['record']['sha256'] == request['record_refs'][str(index)]['sha256'],
                        'same_Banach_retained_record')
            previous = value['sha256']
            records[index], record_refs[str(index)] = value, reference
        saved, loaded = records[2899]['document'], records[2900]['document']
        proof, checkpoint = documents['proof'], documents['saved_commit']
        state = checked_state(saved['resume_state'])
        receipt = {key: value for key, value in saved.items() if key != 'resume_state'}
        require(records[2899]['kind'] == 'SLEEP_COMPLETE' and saved['cycle'] == 28
            and saved['status'] == 'COMPLETE' and saved['checkpoint'] == checkpoint
            and state['sleep_frontier'] == len(state['rows']) and len(state['sleep_receipts']) == 28
            and state['sleep_receipts'][-1] == receipt
            and state['model_state_sha256'] == digest(checkpoint['checkpoint_sha256']), 'authentic_saved28_boundary')
        require(proof['stream_sha256'] == saved['resume_state']['sha256']
            and proof['checkpoint_sha256'] == references['saved_commit']['sha256']
            and proof['checkpoint_path'] == references['saved_commit']['path']
            and proof['bundle_sha256'] == checkpoint['checkpoint_sha256']
            and proof['optimizer_steps'] == checkpoint['optimizer_steps'] == 2478
            and proof['adapter_state_sha256'] == checkpoint['adapter_state_sha256'], 'saved28_loader_proof_COMMIT')
        require(records[2900]['kind'] == 'LOADED' and loaded['pid'] == before['pid']
            and loaded['resume'] is True and loaded['optimizer_steps'] == 2478
            and loaded['adapter_sha256'] == proof['adapter_state_sha256'], 'actual_same_native_saved28_LOADED')
        triples = [committed_triple(records[start], records[start + 1], records[start + 2])
                   for start in [2901, 2904, 2908]]
        policy = documents['policy']
        invitation = policy['invitation']
        invitation_hash = hashlib.sha256(invitation.encode()).hexdigest()
        invocation = records[2907]['document']
        require(records[2907]['kind'] == 'PRESLEEP_RETELLING_INVITATION'
            and invocation['scope']['root'] == str(root)
            and invocation['invitation_sha256'] == policy['invitation_sha256'] == invitation_hash,
            'actual_invitation_source_binding')
        require(any(message.get('role') == 'user' and isinstance(message.get('content'), str)
            and invitation in message['content'] for message in records[2908]['document']['messages']),
            'actual_invitation_in_own_request')
        after, unused = identity(before['pid'])
        require(all(before[key] == after[key] for key in ['pid', 'start_ticks', 'boot_id', 'argv_sha256', 'cwd']),
                'same_recovered_native_after_proof')
        result.update(status='EXACT_RECOVERY_COMMITTED', native_identity={key: after[key]
                for key in ['pid', 'start_ticks', 'boot_id']}, observed_unix=time.time(),
            witness_kind='INDEPENDENT_BOUNDED_SOURCE_METADATA_VERIFICATION', journal=manifest_ref,
            birth_plan=life['birth_plan'], runtime_source_root=plan['source_root'],
            saved_completed_sleep=28, saved_optimizer_steps=2478, loaded_index=2900,
            real_committed_generations=triples, actual_invitation_record=2907,
            actual_invitation_request=2908, actual_invitation_commit=2910,
            invitation_sha256=invitation_hash, records=record_refs,
            no_new_sleep_required_for_recovery_release=True, semantic_correctness_claim=False,
            grants_source_copy_or_GPU_authority=False)
    except Exception as error:
        result['error'] = dict(type=type(error).__name__, reason=str(error))
    result.update(metadata_refs=references, reads=dict(metadata_bytes=reader.metadata_bytes,
        journal_bytes=reader.journal_bytes, record_count=reader.record_count))
    return result


def collect_c5(request):
    release = recover(request)
    print(json.dumps(dict(kind='recovery_release', document=release), sort_keys=True), flush=True)
    if release['status'] != 'EXACT_RECOVERY_COMMITTED':
        return
    life = request['life']
    source = finish(life, dict(reads=release['reads']))
    print(json.dumps(dict(kind='runtime_source', document=source), sort_keys=True), flush=True)
    if source.get('all_checked_pins_match') is not True:
        return
    life['prior_metadata_bytes'] = source['cumulative_metadata_bytes']
    life['prior_journal_bytes'] = release['reads']['journal_bytes']
    life['prior_record_count'] = release['reads']['record_count']
    custody = observe_life(life)
    print(json.dumps(dict(kind='current_frontier', document=custody), sort_keys=True), flush=True)


if __name__ == 'c5_collector':
    collect_c5(json.loads(sys.argv[1]))

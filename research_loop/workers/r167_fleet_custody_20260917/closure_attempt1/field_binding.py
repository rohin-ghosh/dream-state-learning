request = json.loads(sys.argv[1])
reader = Reader()
reader.metadata_bytes = request['prior_metadata_bytes']
reader.journal_bytes = request['prior_journal_bytes']
reader.record_count = request['prior_record_count']
root = Path(request['source_root'])
before, unused = identity(request['native_identity']['pid'])
require(all(before[key] == request['native_identity'][key] for key in ['pid', 'start_ticks', 'boot_id']),
        'same_run1_native')
manifest, manifest_ref = reader.document(root / 'stream/JOURNAL.json')
birth, birth_ref = record(reader, root, 0, manifest)
wrapped = birth['document']['state']
require(wrapped['sha256'] == digest(wrapped['state']) and not wrapped['state']['rows'], 'bound_initial_state')
context = {key: wrapped['state']['history'][key] for key in ['system_prompt', 'birth_prompt']}
initial, initial_ref = reader.document(root / 'checkpoints/initial/COMMIT.json')
require(initial['optimizer_steps'] == 0 and digest(initial['checkpoint_sha256']) ==
        wrapped['state']['model_state_sha256'], 'exact_initial_checkpoint_binding')
comparisons = []
for reference in request['plans']:
    plan, actual = reader.document(reference['path'])
    require(actual['sha256'] == reference['sha256'], 'same_PLAN_bytes')
    comparisons.append(dict(plan=actual, root_matches=plan.get('root') == str(root),
        fields={key: dict(plan_sha256=hashlib.sha256(plan.get(key, '').encode()).hexdigest(),
            initial_history_sha256=hashlib.sha256(value.encode()).hexdigest(),
            plan_bytes=len(plan.get(key, '').encode()), initial_history_bytes=len(value.encode()),
            exact_equal=plan.get(key) == value, stripped_equal=plan.get(key, '').strip() == value.strip())
            for key, value in context.items()}))
after, unused = identity(before['pid'])
require(all(before[key] == after[key] for key in ['pid', 'start_ticks', 'boot_id', 'argv_sha256']),
        'same_native_after_birth_comparison')
print(json.dumps(dict(life_id='continual_run1', observed_unix=time.time(), comparisons=comparisons,
    initial_record=birth_ref, initial_commit=initial_ref, initial_checkpoint_binding=True,
    reads=dict(metadata_bytes=reader.metadata_bytes, journal_bytes=reader.journal_bytes,
               record_count=reader.record_count), no_raw_context_returned=True), sort_keys=True))

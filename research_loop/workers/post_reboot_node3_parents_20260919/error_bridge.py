"""Only already-recorded, undispatched errors; never a scorer request."""

def handle_failure(value, bridge, functions):
    import json
    from pathlib import Path
    import sys
    import time
    retirement, adaptive, helper, bindings = bridge['load_helpers']()
    exact = bridge['exact_bindings'](retirement,helper,bindings)
    if exact != value['bindings']:
        raise ValueError('native_incarnation_changed_no_rebind')
    raw = value['transport_raw'].encode()
    if functions['digest_bytes'](raw) != value['transport_file_sha256']:
        raise ValueError('exact_VM_transport_failure_file_required')
    transport = json.loads(raw)
    name = transport['session_id']
    if name not in bridge['CAPTIONS'] or not value['restored_unix'] <= transport['unix'] <= time.time():
        raise ValueError('five_caption_post_restoration_failures_only')
    binding = exact[name]
    if time.time() >= min(binding['deadline'],1790272760):
        raise ValueError('original_transport_deadline_elapsed')
    if transport['origin']['record_index'] <= binding['loaded']['index']:
        raise ValueError('current_native_incarnation_only')
    sys.path.insert(0,binding['source'])
    root = bridge['ROOT']/name/'raw'
    response = json.loads((root/'stream/records'/f"{transport['origin']['record_index']:020d}.json").read_bytes())
    journal_id = response['journal_id']
    destination = bridge['ROOT']/'post_reboot_node3_operational_errors_20260919'/name
    key = transport['origin']['record_sha256']
    lookup = destination/(key+'.lookup.json')
    if lookup.exists():
        saved = json.loads(lookup.read_bytes())
        return functions['receipt'](root,saved,journal_id)
    window = functions['minimal_window'](root,transport['origin'],journal_id)
    act, reference = None, None
    previous = window['records'][-1]['sha256']
    for index in range(window['final']+1,transport['origin']['record_index']+65):
        path = root/'stream/records'/f'{index:020d}.json'
        if not path.exists():
            return dict(status='WAITING_FOR_NATIVE_FAILURE_RECORD',window=window)
        current, current_reference = functions['record'](root,index,journal_id)
        if current['previous_sha256'] != previous:
            raise ValueError('same_native_ACT_chain_required')
        if current['kind']=='R184_ACT':
            act, reference = current, current_reference
            break
        if current['kind'] in ('REQUEST','RESPONSE'):
            raise ValueError('no_other_generation_before_native_failure')
        previous = current['sha256']
    if act is None:
        raise ValueError('actual_native_failure_record_required')
    functions['validate_failure'](transport,act,journal_id)
    if not window['exceeds_bound']:
        return dict(status='NOT_AN_AGGREGATE_BOUND_FAILURE_NO_PUBLICATION',window=window,ACT_record=reference)
    projection = dict(schema=functions['POLICY'],origin=transport['origin'],ACT_record=reference,
        journal_id=journal_id,window=window,transport_failure=transport,
        transport_file_sha256=value['transport_file_sha256'],text=functions['message'](transport['origin'],window),
        scoring_calls=0,scorer_receipt=False,no_rank_or_acceptance_decision=True,
        no_dropped_records=True,no_ACT_replay=True,target_rows_written=0)
    if value['mode']=='diagnose':
        return dict(status='CONFIRMED_MINIMUM_WINDOW_EXCEEDS_UNCHANGED_BOUND',projection=projection)
    if value['mode']!='publish':
        raise ValueError('unsupported_failure_operation')
    saved = functions['publish_once'](root,destination,projection)
    functions['immutable'](lookup,saved)
    return functions['receipt'](root,saved,journal_id)

"""Read-only canonical provider-publication to exact ACT exposure joins."""


def exact_event(event, item, rendered_sha256):
    return (event['actor'] == 'parent' and event['event_id'] == 'parent:inbox:' + item['publication_id']
        and event['source_sha256'] == item['publication_sha256'] and text_sha(event['text']) == rendered_sha256)


def trace(inputs):
    import sys
    from datetime import datetime, timezone
    root = Path('/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/SCALE_physical3')
    sys.path.insert(0, str(root / 'r233_recovery'))
    import p3_retry_endpoint as endpoint
    unused, binding = endpoint.configure()
    before = endpoint.observer.process(binding['pid'])
    paths = sorted((root / 'life/stream/records').glob('[0-9]' * 20 + '.json'))
    if len(paths) > 50000:
        raise ValueError('bounded_journal_listing')
    source_heads = {item['source_head_sha256'] for item in inputs}
    anchors = {}
    for path in paths:
        value = metadata(path)
        if value['sha256'] in source_heads:
            row, unused = verified(path, binding['journal_id'])
            anchors[value['sha256']] = row['index']
    rows = []
    def instant(stamp):
        return datetime.fromtimestamp(stamp, timezone.utc).isoformat()
    for item in inputs:
        if item['source_head_sha256'] not in anchors:
            raise ValueError('provider_source_head_must_be_canonical')
        anchor = anchors[item['source_head_sha256']]
        inbox_path = root / 'life/stream/inbox' / (item['publication_id'] + '.json')
        inbox_raw, unused = read_stable(inbox_path)
        inbox = json.loads(inbox_raw)
        if not (hashlib.sha256(inbox_raw).hexdigest() == item['publication_sha256']
                and inbox['actor'] == 'parent' and inbox['speaker'] == 'Astra' and inbox['split'] == 'TRAIN'
                and inbox['id'] == item['publication_id'] and text_sha(inbox['text']) == item['message_sha256']):
            raise ValueError('provider_message_exact_published_inbox_join')
        rendered_sha256 = text_sha(inbox['speaker'] + ': ' + inbox['text'])
        evidence = collect(root / 'life', binding['journal_id'], maximum=200, after=anchor)
        requests = [row for row in evidence['records'] if row['kind'] == 'REQUEST'
            and row['masked'] and any(exact_event(event, item, rendered_sha256) for event in row['external'])]
        acts = [frame for frame in frames(evidence) if frame['stage'] == 'ACT'
            and any(exact_event(event, item, rendered_sha256) for event in frame['request']['external'])]
        result = dict(attempt=item['attempt'], publication_id=item['publication_id'],
            published_inbox_file_sha256=hashlib.sha256(inbox_raw).hexdigest(), rendered_message_sha256=rendered_sha256,
            rendering='Existing attributed inbox renderer: speaker + colon-space + exact provider message.',
            source_anchor_index=anchor, scanned_through=evidence['through'], bytes_read=evidence['bytes_read'],
            status='PUBLISHED_NO_EXACT_RENDER_IN_BOUNDED_WINDOW', semantic_uptake=None)
        if requests:
            request = min(requests, key=lambda row: row['index'])
            result.update(status='EXACT_REQUEST_RENDER_ACT_PENDING', first_request=ref(request),
                first_request_utc=instant(request['time_unix']), all_history_tokens_masked=True)
        if acts:
            frame = min(acts, key=lambda value: value['request']['index'])
            result.update(status='PROVIDER_TO_EXACT_REQUEST_TO_COMMITTED_ACT_VERIFIED',
                ACT_request=ref(frame['request']), ACT_request_utc=instant(frame['request']['time_unix']),
                ACT_response=ref(frame['response']), ACT_response_utc=instant(frame['response']['time_unix']),
                ACT_text_sha256=text_sha(frame['response']['text']), committed=ref(frame['commit']),
                stage_receipt=ref(frame['stage_receipt']), parent_exact_text_in_ACT=True)
        rows.append(result)
    endpoint.verify_live(binding)
    if endpoint.observer.process(binding['pid']) != before:
        after = endpoint.observer.process(binding['pid'])
        if any(after[key] != before[key] for key in ('pid','start_ticks','source','command_sha256')):
            raise ValueError('native_identity_changed_during_trace')
    return dict(observed_utc=instant(time.time()), native=before,
        node_boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        journal_id=binding['journal_id'], native_guard_sha256=binding['guard_sha256'],
        loaded_index=binding['loaded_index'], loaded_sha256=binding['loaded_sha256'], rows=rows,
        timestamp_basis='Canonical record file mtime, not inferred from uptime.',
        remote_writes=0, provider_calls=0, native_signals=0, raw_text_exported=False)

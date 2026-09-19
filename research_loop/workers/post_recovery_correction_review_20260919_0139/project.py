"""Bounded semantic-review projection; never export a full request/stream."""


def excerpt(text, maximum=3500):
    selected = text[:maximum]
    return dict(text=selected, start=0, end=len(selected), total_characters=len(text),
        truncated=len(selected) != len(text), text_sha256=text_sha(text),
        excerpt_sha256=text_sha(selected))


def publication_exposed(events, publication):
    return any(event['actor'] == 'parent'
        and event['event_id'] == 'parent:inbox:' + publication['id']
        and event['source_sha256'] == publication['sha256']
        and text_sha(event['text']) == publication['rendered_sha256'] for event in events)


def project(target, publications, after, maximum, cutoff):
    before = identity(target)
    root = Path(target['root'])
    loaded, unused = verified(root / 'stream/records' / f'{target["loaded_index"]:020d}.json', target['journal_id'])
    if loaded['kind'] != 'LOADED' or loaded['sha256'] != target['loaded_sha256'] or loaded['document']['pid'] != target['pid']:
        raise ValueError('exact_loaded_native_required')
    parents = []
    for item in publications:
        path = root / 'stream/inbox' / (item['id'] + '.json')
        raw, information = read_stable(path, 32768)
        message = json.loads(raw)
        if hashlib.sha256(raw).hexdigest() != item['sha256'] or message['actor'] != 'parent' or message['split'] != 'TRAIN':
            raise ValueError('exact_TRAIN_parent_publication_required')
        if message['id'] != item['id']:
            raise ValueError('exact_publication_id_required')
        parents.append(dict(item, text=excerpt(message['text'], 2400),
            rendered_sha256=text_sha(message['speaker'] + ': ' + message['text']),
            publication_mtime_unix=information.st_mtime))
    evidence = collect(root, target['journal_id'], maximum=maximum, after=after)
    evidence['records'] = [row for row in evidence['records'] if row['time_unix'] <= cutoff]
    actual = frames(evidence)
    if len(actual) > 24:
        raise ValueError('maximum_24_committed_outputs_per_window')
    selected, additions, seen = [], [], set()
    new_external_count = 0
    for frame in actual:
        external = frame['request']['external']
        event_ids = []
        for event in external:
            key = event['event_id'] + ':' + event['source_sha256']
            event_ids.append(key)
            if key not in seen:
                if selected:
                    new_external_count += 1
                    if len(additions) < 100:
                        additions.append(dict(first_request=ref(frame['request']), key=key,
                            actor=event['actor'], text=excerpt(event['text'], 1200)))
                seen.add(key)
        selected.append(dict(stage=frame['stage'], request=ref(frame['request']),
            request_utc=frame['request']['time_unix'], response=ref(frame['response']),
            response_utc=frame['response']['time_unix'], committed=ref(frame['commit']),
            stage_receipt=ref(frame['stage_receipt']), cycle=frame['request']['cycle'],
            masked=frame['request']['masked'], output=excerpt(frame['response']['text']),
            visible_publications=[item['id'] for item in parents if publication_exposed(external, item)],
            external_event_keys=event_ids[:120], external_event_key_count=len(event_ids),
            external_event_keys_sha256=digest(event_ids), external_keys_complete=len(event_ids) <= 120))
    inboxes = [dict(ref(row), event_id=row['event_id'], source_sha256=row['source_sha256'])
        for row in evidence['records'] if row['kind'] == 'INBOX']
    after_identity = identity(target)
    if after_identity != before:
        raise ValueError('source_epoch_changed_during_review')
    epoch = dict(target, observed_source_manifest_sha256=before['source_manifest_sha256'],
        observed_boot_id=before['boot_id'])
    return dict(observed_unix=time.time(), source_epoch=epoch, source_epoch_sha256=digest(epoch),
        identity=before, cutoff_unix=cutoff, selection_after=after, maximum_records=maximum,
        bytes_read=evidence['bytes_read'], coverage_start=evidence['coverage_start'], through=evidence['through'],
        head=evidence['head'], caught_up=evidence['caught_up'], parents=parents, frames=selected,
        inboxes=inboxes, new_external_events=additions, new_external_count=new_external_count,
        new_external_projection_complete=new_external_count == len(additions),
        continuity=evidence['continuity'], all_request_bodies_exported=False,
        process_changes=0, messages_sent=0, model_calls=0, remote_writes=0,
        private_scores_read=False, checkpoints_read=False)

"""Bounded scorer-receipt projections; trusted read/accounting helpers injected."""


def scorer_receipts(sessions):
    if not 1 <= len(sessions) <= 8 or len(set(sessions)) != len(sessions):
        raise ValueError('bounded_distinct_scorer_sessions_required')
    receipts = []
    for session in sessions:
        paths = sorted(Path(session).glob('attempts/*/RESULT.json'))
        if len(paths) > 512:
            raise ValueError('bounded_512_receipts_per_session')
        for path in paths:
            payload, information = read_bytes(path, limit=16 * 1024 * 1024)
            document = json.loads(payload)
            origin = document.get('origin', {})
            report = document.get('report', {})
            identifier = hashlib.sha256(payload).hexdigest()
            record = dict(index=origin.get('record_index'), sha256=identifier,
                          document=dict(origin=origin, outcome=dict(environment=dict(
                              origin=origin, receipt_sha256=identifier, report=report))))
            counted = native_outcome_row(record, document['unix'])
            counts = {key: counted[key] for key in ('parsed', 'scored', 'accepted', 'new_pixels',
                                                   'judge_rejected', 'cached', 'format_fault',
                                                   'no_caption_act', 'routing_ambiguity')}
            selections = []
            actions = document.get('actions') or [document.get('action')]
            if not isinstance(actions, list):
                actions = []
            for action in actions[:100]:
                if not isinstance(action, dict):
                    continue
                for key, kind in (('contest_id', 'scene'), ('direction', 'direction')):
                    value = action.get(key)
                    if isinstance(value, str) and 0 < len(value) <= 1024:
                        normalized = ' '.join(value.strip().casefold().split())
                        selections.append(dict(kind=kind, identifier_sha256=hashlib.sha256(
                            (kind + '\0' + normalized).encode()).hexdigest(),
                            basis='SCORER_PARSED_CHILD_SELECTION_NOT_NOVELTY_PROOF'))
            receipts.append(dict(receipt_sha256=identifier,
                                 session_sha256=hashlib.sha256(session.encode()).hexdigest(),
                                 origin={key: origin.get(key) for key in ('record_index', 'record_sha256')},
                                 raw_act_sha256=hashlib.sha256(document.get('raw_act', '').encode()).hexdigest(),
                                 observed_unix=time.time(), saved_unix=document['unix'],
                                 file_mtime_unix=information.st_mtime,
                                 counts=counts, selections=selections,
                                 feedback_present=isinstance(report.get('feedback'), list)))
    return receipts

"""Verify the local bounded review artifacts; never contacts a living source."""

from datetime import datetime, timezone
import hashlib
import os

from collect_review import HERE, read, save, sha
import review


def main():
    report = read(HERE / 'REVIEW.json')
    checked_quotes = 0
    checked_proofs = 0
    for row in report['rows']:
        path = HERE / row['evidence_path']
        assert sha(path) == row['evidence_sha256']
        document = read(path)
        assert document['source_epoch_sha256'] == row['source_epoch_sha256']
        assert document['remote_writes'] == document['messages_sent'] == document['model_calls'] == 0
        assert not document['private_scores_read'] and not document['checkpoints_read']
        frames = {frame['response']['index']: frame for frame in document['frames']}
        for proof in row['proofs']:
            actual = frames[proof['response']['index']]
            assert all(actual[key] == value for key, value in proof.items())
            assert actual['masked']
            assert actual['request']['index'] < actual['response']['index'] < actual['committed']['index'] < actual['stage_receipt']['index']
            assert actual['response_utc'] <= document['cutoff_unix']
            checked_proofs += 1
        for quote in row['quotes']:
            reference = quote['reference']
            if 'publication_id' in reference:
                parent = next(item for item in document['parents'] if item['id'] == reference['publication_id'])
                assert reference['source_sha256'] == parent['sha256']
                text = parent['text']['text']
                assert not parent['text']['truncated']
            else:
                frame = frames[reference['index']]
                assert frame['response'] == reference and not frame['output']['truncated']
                text = frame['output']['text']
            assert text[quote['start']:quote['end']] == quote['text']
            assert hashlib.sha256(text.encode()).hexdigest() == quote['full_text_sha256']
            assert hashlib.sha256(quote['text'].encode()).hexdigest() == quote['span_sha256']
            checked_quotes += 1
        review.validate_grade(row['best_supported_level'], row['flags'])
    assert report['reference_checks'] == review.numeric_checks()
    predecessor = report['frozen_predecessor_evidence']
    assert sha(HERE / predecessor['path']) == predecessor['sha256']
    for path, expected in read(HERE / 'SOURCE_PINS.json').items():
        assert sha(__import__('pathlib').Path(path)) == expected
    secret = os.environ.get('NVIDIA_API_KEY', '').encode()
    assert secret, 'credential_presence_required_for_exact_leak_scan'
    files = [path for path in HERE.rglob('*') if path.is_file()]
    assert not any(secret in path.read_bytes() for path in files)
    receipt = dict(verified_utc=datetime.now(timezone.utc).isoformat(), status='PASS',
        quote_spans_checked=checked_quotes, proof_frames_checked=checked_proofs,
        no_credential_bytes_found=True, files_scanned=len(files),
        levels={row['label']: row['best_supported_level'] for row in report['rows']},
        report_sha256=sha(HERE / 'REVIEW.json'), review_logic_sha256=sha(HERE / 'review.py'),
        no_second_reviewer_claim=True, native_contacts=0, model_calls=0, messages_sent=0)
    save(HERE / 'VERIFICATION.json', receipt)
    print(__import__('json').dumps(receipt))


if __name__ == '__main__':
    main()

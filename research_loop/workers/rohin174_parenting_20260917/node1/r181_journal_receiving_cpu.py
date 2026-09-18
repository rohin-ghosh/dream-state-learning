"""Actual receiving-source cache smoke plus unchanged saved-state CPU checks."""

from pathlib import Path
import tempfile
from unittest.mock import patch

import r181_receiving_cpu as original


BEHAVIORAL = original.behavioral
JOURNAL_SHA = 'd57c318baa509c009f12328b566f391f79a3948e497b6fdbc04bd2d1d274c9fd'


def behavioral(source):
    result = BEHAVIORAL(source)
    from gpu import orch_r125_stream_journal as journal_module
    path = Path(journal_module.__file__).resolve()
    assert path == source / 'gpu/orch_r125_stream_journal.py'
    assert original.sha(path) == JOURNAL_SHA
    with tempfile.TemporaryDirectory(prefix='r181-journal-receiving-') as temporary:
        root = Path(temporary) / 'stream'
        with journal_module.StreamJournal(root, create=True) as journal:
            with patch.object(journal, '_reload_state', side_effect=AssertionError('unexpected_full_replay')):
                first = journal.record('CACHE_SMOKE', {'sequence': 1})
                second = journal.record('CACHE_SMOKE', {'sequence': 2})
                assert journal.read_inbox() == []
                assert second['index'] == first['index'] + 1
            expected = journal.audit()
            assert expected == {'record_count': 2, 'head_sha256': second['sha256']}
        with journal_module.StreamJournal(root) as reopened:
            assert reopened.audit() == expected
    result['cases'].extend(['actual_cached_append_and_inbox_no_full_replay', 'actual_audit_and_fresh_open'])
    result['passed'] = len(result['cases'])
    result['journal_sha256'] = JOURNAL_SHA
    return result


if __name__ == '__main__':
    original.behavioral = behavioral
    original.main()

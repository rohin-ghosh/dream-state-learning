"""Cut off P7 parent publication and preserve any immutable retraction evidence."""

import fcntl
import json
import os
from pathlib import Path
import time

from math_c import HOME, host, read, require, sha, write
from r206_handoff import records, root_for


def run():
    host()
    root = root_for(7)
    target = root / 'r210'
    output = root / 'r211'
    output.mkdir(exist_ok=True)
    with (target / 'PARENT_PUBLICATION.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        cutoff_path = target / 'R211_ISOLATION.json'
        stop = read(HOME.parent / 'R211_PARENT7_STOPPED.json')
        require(stop['stopped'] and stop['no_child_signals'] and stop['physical'] == 7, 'exact_owned_parent_stopped')
        if not cutoff_path.exists():
            write(cutoff_path, dict(phase='R211_ISOLATION', physical=7, root=str(root / 'life'),
                parent_cutoff_unix=stop['cutoff_unix'], publication_cutoff_unix=time.time(),
                parent_pid=stop['pid'], parent_stopped=True, R205_console_preserved=True,
                cluster_membership='SUSPENDED_NO_INBOUND_PEERS_OR_LANGUAGE_PARENTS'))
            os.chmod(cutoff_path, 0o400)
        history = records(root)
        registered = {entry['document']['message']['id']: entry for entry in history if entry['kind'] == 'INBOX'}
        astra, rohin, other = [], [], []
        for path in sorted((root / 'life/stream/inbox').glob('*.json')):
            message = read(path)
            detail = dict(id=message['id'], sha256=sha(path), speaker=message['speaker'], actor=message['actor'], path=str(path))
            entry = registered.get(message['id'])
            detail['registered_record'] = entry['index'] if entry else None
            if message['speaker'] == 'Rohin':
                rohin.append(detail)
                continue
            if message['actor'] != 'parent' or message['speaker'] != 'Astra':
                other.append(detail)
                continue
            if entry:
                detail.update(action='PRESERVED_ALREADY_JOURNAL_REGISTERED_NO_RETRACTION', record_sha256=entry['sha256'])
            else:
                detail.update(action='PRESERVED_UNREGISTERED_LIVE_READER_RACE_NO_UNSAFE_RETRACTION')
            copy = output / (message['id'] + '.immutable.json')
            if not copy.exists():
                with copy.open('xb') as handle:
                    handle.write(path.read_bytes())
                    handle.flush()
                    os.fsync(handle.fileno())
                os.chmod(copy, 0o400)
            require(sha(copy) == detail['sha256'], 'immutable_parent_copy')
            detail['immutable_copy'] = str(copy)
            astra.append(detail)
        report = dict(phase='R211_ISOLATION', observed_unix=time.time(), publication_cutoff=read(cutoff_path),
            actual_parent_stop=stop, last_record_index=history[-1]['index'], last_record_sha256=history[-1]['sha256'],
            Astra=astra, Rohin_preserved=rohin, other_inbox_metadata=other, retracted_count=0,
            no_journal_edits=True, no_child_signals=True, no_other_life_changes=True,
            interpretation='Prior queued R210 messages already registered cannot be undone; isolation is prospective, with carry-in documented.')
        receipt = output / f'ISOLATION_{time.time_ns()}.json'
        write(receipt, report)
        os.chmod(receipt, 0o400)
        print(json.dumps(dict(receipt=str(receipt), **report)), flush=True)


if __name__ == '__main__':
    run()

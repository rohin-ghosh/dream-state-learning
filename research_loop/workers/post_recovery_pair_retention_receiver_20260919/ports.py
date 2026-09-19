"""Return reviewed source-port bytes/deltas; never modify a staged source tree."""

import hashlib
from pathlib import Path


SEAM = '        journal_module.StreamJournal = FrozenJournal if physical == 1 else LearnerJournal\n'
REPLACEMENT = SEAM + ('        from gpu.pair_retention_runtime import bind_journal\n'
    '        journal_module.StreamJournal = bind_journal(journal_module.StreamJournal, plan)\n')


def proposed_ports(source, tested_tail_runtime):
    source = Path(source)
    path = source / 'gpu/r232_recovery.py'
    original = path.read_bytes()
    if original.count(SEAM.encode()) != 1 or b'pair_retention_runtime' in original:
        raise ValueError('one_exact_unported_pair_journal_install_seam')
    proposed = {
        'gpu/r232_recovery.py': original.replace(SEAM.encode(), REPLACEMENT.encode()),
        'gpu/pair_retention_runtime.py': Path(__file__).with_name('pair_retention_runtime.py').read_bytes(),
        'gpu/checkpoint_tail_runtime.py': Path(tested_tail_runtime).read_bytes(),
    }
    changes = {}
    for name, content in proposed.items():
        previous = source / name
        before = hashlib.sha256(previous.read_bytes()).hexdigest() if previous.exists() else None
        after = hashlib.sha256(content).hexdigest()
        if before != after:
            changes[name] = dict(before=before, after=after)
    return proposed, changes

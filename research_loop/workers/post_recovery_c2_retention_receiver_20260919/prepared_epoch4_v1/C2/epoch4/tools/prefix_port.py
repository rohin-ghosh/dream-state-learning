"""Exact-source opt-in port. Return candidate bytes; never modify the input."""

import argparse
import hashlib
from pathlib import Path


ORIGINAL_SHA256 = '972456b7d6cb026cc922e067114701d4f157fa6ed775e4406ecb52c86eef7d3e'
EDITS = (
    ('def scan(journal, selection):\n',
     'def scan(journal, selection, *, prefix_proof=None):\n'),
    ('    headers = {}\n    previous = _digest(journal._manifest)\n',
     '    verified_prefix = None\n'
     '    if prefix_proof is not None:\n'
     '        from gpu.immutable_prefix_proof import prepare\n'
     '        verified_prefix = prepare(journal, selection, prefix_proof)\n'
     '    headers = {}\n    previous = _digest(journal._manifest)\n'),
    ('    inbox = {}\n    decoded_prefix = []\n',
     '    inbox = {} if verified_prefix is None else deepcopy(verified_prefix.inbox)\n'
     '    decoded_prefix = []\n'),
    ('        header, hashed = hash_record(journal, index)\n',
     '        if verified_prefix is None:\n'
     '            header, hashed = hash_record(journal, index)\n'
     '        else:\n'
     '            header, hashed = verified_prefix.record(index, hash_record)\n'),
    ("        if index <= anchor_index and header['kind'] == 'INBOX':\n",
     "        if index <= anchor_index and header['kind'] == 'INBOX' and (\n"
     "                verified_prefix is None or index >= verified_prefix.prefix_count):\n"),
    ("    require(set(os.listdir(journal._records_fd)) == names, 'journal_changed_during_scan')\n",
     "    require(set(os.listdir(journal._records_fd)) == names, 'journal_changed_during_scan')\n"
     '    if verified_prefix is not None:\n        verified_prefix.finish()\n'),
    ('        source_admission_unchanged=True, prefix_rewritten=False, pending_preserved=True)\n    return state\n',
     '        source_admission_unchanged=True, prefix_rewritten=False, pending_preserved=True)\n'
     '    if verified_prefix is not None:\n'
     '        journal.checkpoint_tail_receipt.update(verified_prefix.receipt())\n'
     '    return state\n'),
)


def port(original):
    if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA256:
        raise ValueError('prefix_port_requires_exact_original_source')
    candidate = original
    for before, after in EDITS:
        if candidate.count(before.encode()) != 1:
            raise ValueError('prefix_port_requires_one_exact_seam')
        candidate = candidate.replace(before.encode(), after.encode(), 1)
    compile(candidate, '<opt_in_prefix_reader_candidate>', 'exec')
    return candidate


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('output', type=Path)
    arguments = parser.parse_args()
    candidate = port(arguments.original.read_bytes())
    with arguments.output.open('xb') as destination:
        destination.write(candidate)
    print(hashlib.sha256(candidate).hexdigest())

"""Explicit C39 contextual lineage forks; never a fresh or independent ancestry."""

import hashlib
import json
from pathlib import Path
import shutil


def original_prefix(data, digest):
    prefix = b''
    if hashlib.sha256(prefix).hexdigest() == digest:
        return prefix
    for line in data.splitlines(keepends=True):
        prefix += line
        if hashlib.sha256(prefix).hexdigest() == digest:
            return prefix
    raise ValueError('recorded_precontinuation_ledger_prefix_missing')


def prepare_fork(life, ancestor, destination, physical, uuid):
    if physical not in (1, 2, 3) or not uuid.startswith('GPU-'):
        raise ValueError('allocated_fork_slot_required')
    recipe = life.read(life.directory(ancestor, 'node1_7') / 'RECOVERY.json')
    checkpoint = recipe['checkpoint']
    if Path(checkpoint['path']).name != 'CHECKPOINT_C39.json':
        raise ValueError('exact_C39_ancestor_required')
    if life.sha(checkpoint['path']) != checkpoint['sha256']:
        raise ValueError('ancestor_checkpoint_changed')
    ledger = original_prefix((ancestor / 'RESERVATIONS.jsonl').read_bytes(),
                             recipe['old_reservations']['sha256'])
    destination.mkdir(exist_ok=False)
    prior = ancestor / 'recovery_r113_v1/campaign_node1_7'
    ready = life.read(prior / 'READY.json')
    for name in set(ready['files']) | {'ALLOCATION.md'}:
        shutil.copyfile(ancestor / name, destination / name)
    (destination / 'source').symlink_to(ancestor / 'source', target_is_directory=True)
    (destination / 'RESERVATIONS.jsonl').write_bytes(ledger)
    target_prior = destination / 'recovery_r113_v1/campaign_node1_7'
    target_prior.mkdir(parents=True)
    for name in ('READY.json', 'STATUS.json', 'RECOVERY.json', 'CHECKPOINT_C39.json'):
        shutil.copyfile(prior / name, target_prior / name)
    namespace = destination / life.VERSION
    namespace.mkdir()
    relocation = life.read(ancestor / life.VERSION / 'RELOCATION.json')
    relocation.update(target_physical=physical, target_uuid=uuid)
    life.write(namespace / 'RELOCATION.json', relocation)
    ancestry = dict(label='FORK_OF_C39', ancestor_root=str(ancestor),
                    checkpoint=checkpoint, prior_recipe=life.reference(prior / 'RECOVERY.json'),
                    inherited_ledger_sha256=hashlib.sha256(ledger).hexdigest(),
                    next_cycle=recipe['first_cycle'], inherited_counters=recipe['counters'],
                    independent_preexisting_lineage=False, new_budget_reset=False,
                    authorization='Main explicit C39 fork permission 2026-09-15 after17:23')
    life.write(destination / 'FORK_OF_C39.json', ancestry)
    runtime = life.load_runtime(destination, 'node1_7')
    result = life.prepare(destination, 'node1_7', runtime)
    return dict(result, ancestry=life.reference(destination / 'FORK_OF_C39.json'))

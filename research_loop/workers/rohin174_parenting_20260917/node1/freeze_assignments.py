"""Bind Main's explicit R175 node1 assignments without changing live parents."""

import json
from pathlib import Path
import time

from inventory_node1 import HERE, Reader, digest, require
from stage_node1 import revalidate_inputs, reserved_cursor


ASSIGNMENTS = {
    'teach_replay': ('A', 1),
    'teach_perception': ('B', 2),
    'teach_parenting': ('C', 3),
    'classroom_brain': ('B', 2),
    'classroom_creative': ('C', 3),
    'classroom_support': ('D', 3),
}
INVENTORY_NAME = 'INVENTORY_1789676984968119786.json'
INVENTORY_SHA256 = '8c06417b4a5cde89b7540a7411356e34191bc24e2538b22524669b5eccd54c20'


def write(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, indent=2, sort_keys=True)
    return dict(path=str(path), sha256=digest(Path(path).read_bytes()))


def main():
    reader = Reader()
    raw = reader.raw(HERE / INVENTORY_NAME)
    require(digest(raw) == INVENTORY_SHA256, 'exact_current_inventory')
    inventory = json.loads(raw)
    revalidate_inputs(inventory, reader)
    parents = [row for row in inventory['parents'] if row['physical'] >= 2]
    require({row['label'] for row in parents} == set(ASSIGNMENTS) and len(parents) == 6,
            'exact_main_named_six_learning_lives')
    directory = HERE / ('ACTIVATION_PREP_' + str(time.time_ns()))
    directory.mkdir()
    rows = []
    for row in parents:
        lane = directory / ('lane' + str(row['physical']))
        lane.mkdir()
        frozen = {}
        for field, filename in (('config', 'ORIGINAL_CONFIG.json'), ('source', 'ORIGINAL_SOURCE.py'),
                                ('binding', 'ORIGINAL_BINDING.json')):
            source = reader.raw(row[field]['path'])
            require(digest(source) == row[field]['sha256'], 'exact_original_' + field)
            destination = lane / filename
            with destination.open('xb') as stream:
                stream.write(source)
            destination.chmod(0o444)
            frozen[field] = dict(path=str(destination), sha256=digest(source))
        arm, cadence = ASSIGNMENTS[row['label']]
        rows.append(dict(physical=row['physical'], label=row['label'], arm=arm,
                         cadence_responses=cadence, parent_word_cap=90, schedule_on='response',
                         baseline='C2_OBSERVATION_TO_ACTION', wait_for_c2_success=False,
                         root=row['fields']['root'], old_parent=row['parent'],
                         old_parent_binding=row['binding'], original=frozen,
                         old_output=row['output'], previous_output=row['previous_output'],
                         original_hard_end_unix=row['fields']['hard_end_unix'],
                         observed_reserved_response_count=reserved_cursor(row),
                         native=row['natives'][0], preparation_directory=str(lane),
                         no_child_restart=True, runtime_sleep_r179_unchanged=True,
                         three_sleep_check_starts_at='FIRST_VERIFIED_ASSIGNED_PARENT_REQUEST_EXPOSURE',
                         retirement_authorized=False))
    assignment = write(directory / 'ASSIGNMENTS.json', dict(
        schema='ROHIN175_NODE1_MAIN_ASSIGNMENTS_V1', observed_unix=time.time(),
        authority='Main explicit six-label activation assignment in this conversation', rows=rows,
        inventory=dict(path=str(HERE / INVENTORY_NAME), sha256=INVENTORY_SHA256),
        controls=dict(physical=[0, 1], no_update=True, label='FROZEN_NO_UPDATE_CONTROLS',
                      parent_switch_selected=False),
        required_common_api='gpu/orch_r175_parent_arms.py', common_policy_sha256=None,
        parent_switch_performed=False, no_key_reads=True, no_sealed_reads=True))
    peers = [row for row in rows if row['label'] in ('classroom_brain', 'classroom_creative')]
    peer = write(directory / 'STATE_ONLY_PEER_PAIR.json', dict(
        schema='ROHIN175_NODE1_PEER_PAIR_STAGING_V1', status='STAGED_NO_RELAY',
        assignment=assignment, directions=[dict(sender=sender['label'], sender_root=sender['root'],
                                              receiver=receiver['label'], receiver_root=receiver['root'])
                                          for sender in peers for receiver in peers if sender is not receiver],
        payload_kind='actual_state_only', full_transcripts_allowed=False,
        speculative_results_allowed=False, actual_source_record_hash_required=True,
        attributed_peer_message_required=True, messages_sent=0,
        learner_sources_and_inboxes_unchanged=True))
    print(json.dumps(dict(assignment=assignment, peer_pair=peer, directory=str(directory))))


if __name__ == '__main__':
    main()

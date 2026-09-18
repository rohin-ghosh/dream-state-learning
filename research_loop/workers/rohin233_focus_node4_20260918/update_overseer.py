"""One atomic hot-read brief update; no publisher or learner control."""

import hashlib
import json
import os
from pathlib import Path
import socket
import time

from inventory import BASE, HOST_SHA, identity, read
from retire import OUTPUT, WALL, require, sha, write


def main():
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA
        and os.getuid() == 2524 and time.time() < WALL, 'same_node4_owner_and_wall')
    actor = identity(1100592)
    require(actor['start_ticks'] == '28670738' and actor['cwd'] == str(BASE / 'SCALE_physical7/r224_language_v3/source'), 'kept_P7_current_incarnation')
    target = BASE / 'MATH_C/R230_OVERSEER_CURRICULUM.json'
    before = target.read_bytes()
    document = json.loads(before)
    require(document['policy'] == 'R230_DIVERSE_CURRICULUM_THROUGH_P7_OVERSEER_V1', 'existing_hot_read_curriculum')
    addition = read(OUTPUT / 'overseer_adjustment.json')
    require(addition['policy'] == 'R233_P7_CONVERGENCE_GUIDANCE_V1'
        and addition['new_exclusions'] == [] and addition['native_controls'] is False
        and addition['direct_Astra7_messages'] is False, 'parent_only_no_exclusion_adjustment')
    require('R233_convergence_adjustment' not in document, 'one_prospective_adoption')
    with (OUTPUT / 'OVERSEER_CONFIG_BEFORE.json').open('xb') as stream:
        stream.write(before)
    document['R233_convergence_adjustment'] = addition
    encoded = (json.dumps(document, sort_keys=True, indent=2) + '\n').encode()
    require(target.read_bytes() == before, 'same_config_before_atomic_write')
    temporary = target.with_name('R233_OVERSEER_CURRICULUM.next')
    with temporary.open('xb') as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, target)
    require(identity(1100592)['start_ticks'] == actor['start_ticks'], 'native_unchanged')
    result = dict(status='HOT_READ_CONFIG_WRITTEN_AWAITING_ACTUAL_PARENT_INPUT',
        changed_unix=time.time(), policy=addition['policy'], before_sha256=hashlib.sha256(before).hexdigest(),
        after_sha256=sha(target), adjustment_sha256=sha(OUTPUT / 'overseer_adjustment.json'),
        native_signals=[], publisher_started=False, parent_restarted=False, bridge_restarted=False,
        native_policy_changes=[], P3_changes=[])
    write(OUTPUT / 'OVERSEER_CONFIG_ADOPTION.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()

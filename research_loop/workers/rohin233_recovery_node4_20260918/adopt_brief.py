"""P7-only atomic hot-read parent brief update; no process or learner controls."""

import hashlib
import json
import os
from pathlib import Path
import time


BASE = Path('/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET')
OUTPUT = Path('/localhome/local-rohing/orch_r233_p7_recovery_20260918')
TARGET = BASE / 'MATH_C/R230_OVERSEER_CURRICULUM.json'
WALL = 1789754400
BEFORE_SHA = '6ae326980e2e86139e9b888ab447f58752c15d450a2e9a0d5e08306bec6af81c'
JOURNAL = 'e9d22d1e26234c4bbac761922929365f'
LOADED_SHA = '68cbee223e0ba397c970209dee232ec49bc83be8ceabe358835364fa40f9b076'
KEY = 'R233_RECOVERY_ENGLISH_REGROUNDING'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def identity():
    process = Path('/proc/1100592')
    stat = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    require(stat[19] == '28670738'
        and os.readlink(process / 'cwd') == str(BASE / 'SCALE_physical7/r224_language_v3/source'),
        'same_existing_P7_incarnation')
    return dict(pid=1100592, start_ticks=stat[19], state=stat[0])


def merge(before, brief):
    require(before['policy'] == 'R230_DIVERSE_CURRICULUM_THROUGH_P7_OVERSEER_V1', 'existing_parent_only_brief')
    require(KEY not in before, 'one_prospective_adoption')
    require(brief['policy'] == 'R233_ENGLISH_REGROUNDING_NO_EXCLUSIONS_V1'
        and brief['native_policy_changes'] == [] and brief['signals'] == []
        and brief['direct_Astra7_messages'] is False, 'no_exclusions_signals_or_direct_child_messages')
    require(brief['current_route_status'] == 'EXPIRED_BINDING_NO_CURRENT_RECEIVER_VERIFIED', 'no_false_live_route_claim')
    require(len(brief['next_turn_requested_text'].split()) <= 160, 'existing_parent_word_budget')
    result = dict(before)
    result[KEY] = brief
    return result


def write_once(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def main():
    require(os.getuid() == 2524 and time.time() < WALL, 'current_owner_and_unextended_wall')
    actor = identity()
    record_path = BASE / 'SCALE_physical7/life/stream/records/00000000000000001986.json'
    loaded = json.loads(record_path.read_text())
    require(loaded['journal_id'] == JOURNAL and loaded['sha256'] == LOADED_SHA
        and loaded['sha256'] == digest({key: value for key, value in loaded.items() if key != 'sha256'}),
        'same_source_bound_loaded_life')
    before = TARGET.read_bytes()
    require(hashlib.sha256(before).hexdigest() == BEFORE_SHA, 'same_expected_hot_read_config')
    packet = json.loads((OUTPUT / 'BRIEF.json').read_text())
    after = (json.dumps(merge(json.loads(before), packet), sort_keys=True, indent=2) + '\n').encode()
    with (OUTPUT / 'BEFORE.json').open('xb') as stream:
        stream.write(before)
        stream.flush()
        os.fsync(stream.fileno())
    temporary = OUTPUT / 'HOT_BRIEF.next'
    with temporary.open('xb') as stream:
        stream.write(after)
        stream.flush()
        os.fsync(stream.fileno())
    require(TARGET.read_bytes() == before, 'unchanged_before_atomic_adoption')
    require(identity()['start_ticks'] == actor['start_ticks'], 'same_live_P7_before_write')
    os.replace(temporary, TARGET)
    result = dict(status='HOT_BRIEF_WRITTEN_NOT_YET_PUBLICATION_OR_RENDER', changed_unix=time.time(),
        native=actor, policy=packet['policy'], before_sha256=BEFORE_SHA,
        after_sha256=hashlib.sha256(after).hexdigest(), brief_sha256=hashlib.sha256((OUTPUT / 'BRIEF.json').read_bytes()).hexdigest(),
        unchanged_hard_end_unix=WALL, learner_signals=[], parent_signals=[], extra_publishers=[],
        native_policy_changes=[], P3_changes=[], direct_Astra7_messages=False)
    write_once(OUTPUT / 'ADOPTION.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()

"""Fast actual-source R181 checks and the unchanged R179 saved-state restoration check."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def behavioral(source):
    from gpu import orch_r125_continual_native as native
    import torch
    assert Path(native.__file__).resolve() == source / 'gpu/orch_r125_continual_native.py'
    old = [object(), object()]
    assert native.select_rehearsal_rows({'rehearsal_presentations': 0}, old) == []
    assert native.select_rehearsal_rows({'rehearsal_presentations': 1}, old) is old
    cases = ['actual_zero_old_selection', 'legacy_one_compatibility']
    for invalid in (True, -1, 2):
        try:
            native.select_rehearsal_rows({'rehearsal_presentations': invalid}, old)
        except ValueError:
            continue
        raise AssertionError('invalid_rehearsal_accepted')
    cases.append('invalid_schedule_rejected')

    class Captured(Exception):
        pass

    def record(kind, document):
        assert kind == 'SLEEP_RECIPE' and document['selected_old_rows'] == 0
        assert document['available_old_rows'] == 2 and document['new_rows'] == 3
        assert document['new_presentations'] == 16 and document['anchor_lambda'] == .25
        raise Captured()

    try:
        native.NativeChild.sleep(SimpleNamespace(plan={'rehearsal_presentations': 0}), [1, 2, 3], old, [], record)
    except Captured:
        cases.append('actual_sleep_selects_before_encoding_or_training')
    assert len(cases) == 4
    known = SimpleNamespace(event_id='known', actor='parent')
    fresh = SimpleNamespace(event_id='fresh', actor='parent')
    history = SimpleNamespace(events=[known])
    steps = []
    logs = []

    def step(generate, count_tokens, record, incoming):
        steps.append(incoming)
        history.events.extend(incoming)

    stream = SimpleNamespace(pending=None, sleep_due=True, history=history, step=step)
    journal = SimpleNamespace(read_inbox=lambda: [known, fresh], record=lambda kind, value: logs.append((kind, value)))
    child = SimpleNamespace(generate=None, count_tokens=None)
    assert native.respond_to_presleep_inbox(child, stream, journal, 5) is True
    assert native.respond_to_presleep_inbox(child, stream, journal, 5) is False
    assert len(steps) == 1 and steps[0] == [fresh] and len(logs) == 1
    cases.append('unseen_parent_only_one_extra_response_no_duplicate_drain')
    assert not torch.cuda.is_initialized()
    return dict(passed=len(cases), cases=cases, cuda_initialized=False,
                native_sha256=sha(source / 'gpu/orch_r125_continual_native.py'), observed_unix=time.time())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--boundary', type=Path)
    arguments = parser.parse_args()
    if arguments.boundary:
        original = Path('/localhome/local-rohing/orch_r179_node1_20260917_attempt2/operator/receiving_cpu.py')
        assert sha(original) == '189aeecf76ec62b6c5ad1ad7ea5cb30e9e5b0b735edfd81590cea967a284497e'
        specification = importlib.util.spec_from_file_location('unchanged_saved_state_receiver', original)
        loaded = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(loaded)
        result = loaded.boundary_cpu(arguments.source, arguments.output, arguments.boundary)
    else:
        result = behavioral(arguments.source)
    print(json.dumps(result))


if __name__ == '__main__':
    main()

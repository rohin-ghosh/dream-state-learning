"""Load a tested history overlay in this CPU observer only, not in a live native."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def execute(request_path, request_sha256, overlay_path, overlay_sha256, helper_path, helper_sha256):
    for path, expected in ((request_path, request_sha256), (overlay_path, overlay_sha256),
                           (helper_path, helper_sha256)):
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError('all_CPU_observer_inputs_must_be_pinned')
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('CPU_only_observer_required')
    request = json.loads(Path(request_path).read_bytes())
    sys.path.insert(0, request['source'])
    import organism_v6
    name = 'organism_v6.orch_r124_train_history'
    specification = importlib.util.spec_from_file_location(name, overlay_path)
    history = importlib.util.module_from_spec(specification)
    sys.modules[name] = history
    specification.loader.exec_module(history)
    setattr(organism_v6, 'orch_r124_train_history', history)
    started = time.monotonic()
    original = request['candidate']['resume_state']['state']['history']
    restored = history.TrainHistory.restore(original, expected_sha256=original['state_sha256'])
    if restored.checkpoint() != original:
        raise ValueError('real_checkpoint_history_bytes_changed')
    check_seconds = time.monotonic() - started
    specification = importlib.util.spec_from_file_location('isolated_cost_probe', helper_path)
    helper = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(helper)
    result = helper.probe(request_path, request_sha256)
    return dict(result, observer_only_history_overlay_sha256=overlay_sha256,
                checkpoint_history_byte_equivalent=True, history_restore_seconds=check_seconds,
                original_receiving_source_untouched=True, deployed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('request', 'request-sha256', 'overlay', 'overlay-sha256', 'helper', 'helper-sha256'):
        parser.add_argument('--' + field, required=True)
    arguments = parser.parse_args()
    print(json.dumps(execute(arguments.request, arguments.request_sha256,
                             arguments.overlay, arguments.overlay_sha256,
                             arguments.helper, arguments.helper_sha256), sort_keys=True))

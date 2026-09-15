"""CPU-only author evidence observer; never emits inputs to a parent."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import time


def observe(root, campaign_names=None):
    specification = importlib.util.spec_from_file_location('math_author_evidence', Path(__file__).with_name('orch_math_pipeline_l2_evidence.py'))
    evidence = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(evidence)
    written = []
    for campaign in sorted(root.glob('campaign_*')):
        if campaign_names is not None and campaign.name not in campaign_names:
            continue
        for arm in ('GUIDED_SLEEP', 'UNPARENTED_SLEEP', 'FROZEN'):
            cycles = sorted(int(path.name[5:]) for path in (campaign / arm).glob('cycle*')
                            if path.is_dir() and path.name[5:].isdigit() and int(path.name[5:]) >= 2)
            for cycle in cycles:
                output = campaign / f'AUTHOR_TAUGHT_NEXT_{arm}_C{cycle - 1}_C{cycle}.json'
                if output.exists():
                    continue
                joined = evidence.join_transition(campaign, arm, cycle)
                if joined['captured'] == joined['planned_denominator'] and joined['prior_learning_complete']:
                    joined['observed_unix'] = time.time()
                    with output.open('x') as stream:
                        json.dump(joined, stream, indent=2, sort_keys=True)
                        stream.write('\n')
                    written.append(str(output))
    return written


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    options = parser.parse_args()
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    lifetime = json.loads((options.root / 'LIFETIME.json').read_text())
    while time.time() < lifetime['hard_deadline_unix']:
        for path in observe(options.root):
            print(json.dumps(dict(measurement=path, new_native_calls=0)), flush=True)
        time.sleep(15)

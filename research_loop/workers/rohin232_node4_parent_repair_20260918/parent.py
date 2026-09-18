"""Read-only validation by default; serving is exclusively a later Main action."""

import argparse
import importlib
import json
import sys
import time
from pathlib import Path

import repair


def load_runtime(physical):
    config = repair.load_config(physical)
    repair.require(not any(name == 'gpu' or name.startswith('gpu.') or name == 'organism_v6'
        or name.startswith('organism_v6.') or name in ('parent_c', 'r210_parent', 'parent_repairs')
        for name in sys.modules), 'fresh_process_per_parent_required')
    sys.path.insert(0, str(repair.FLEET))
    module = importlib.import_module('r210_parent')
    binding = repair.read(repair.FLEET / f'r210_parent{physical}/BINDING.json')
    module.base.BUNDLE = Path(binding['bundle'])
    frozen = module.base.runtime()
    policy = repair.adapt(frozen, config)
    return module, frozen, policy, config


def describe(physical, config):
    return dict(policy=repair.POLICY, physical=physical, classification='NON_MATERIAL_REPAIR',
        config_path=str(repair.HERE / f'physical{physical}/CONFIG.json'),
        config_sha256=repair.sha(repair.HERE / f'physical{physical}/CONFIG.json'),
        source_pins_sha256=repair.sha(repair.HERE / 'SOURCE_PINS.json'),
        effective_cadence_responses=1, original_cadence_responses=config['cadence_responses'],
        delivered_counts='PRESERVED', arm=config['r175_arm'], word_limit=config['r175_word_limit'],
        hard_end_unix=config['hard_end_unix'], learner_signals=[], deployed=False)


def serve(physical, module, policy, config, reviewed_config_sha256):
    config_path = repair.HERE / f'physical{physical}/CONFIG.json'
    repair.require(reviewed_config_sha256 == repair.sha(config_path), 'Main_reviewed_exact_config_required')
    repair.require(time.time() < min(config['hard_end_unix'], module.base.WALL), 'unchanged_hard_end')
    output = repair.FLEET / f'r210_parent{physical}'
    repair.require((output / 'SEED.json').is_file() and (output / 'turns').is_dir(),
        'existing_parent_history_required_no_new_seed_or_opening')
    policy.local_attempts(output / 'turns')
    original_path = output / 'CONFIG.json'
    original_read, original_sha = module.base.read, module.base.sha
    module.base.read = lambda path: original_read(config_path if Path(path) == original_path else path)
    module.base.sha = lambda path: original_sha(config_path if Path(path) == original_path else path)
    module.base.runtime = lambda: policy
    original_remote = module.remote

    def existing_parent_only(physical_id, request):
        repair.require(physical_id == physical and request.get('op') in ('poll', 'publish'),
            'existing_CPU_parent_poll_publish_only_no_opening')
        observation = original_remote(physical_id, request)
        if request['op'] == 'poll':
            repair.require(observation['opening_published'], 'existing_remote_opening_required')
        return observation

    module.remote = existing_parent_only
    module.serve(physical)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('validate', 'serve'))
    parser.add_argument('--physical', type=int, choices=repair.ALLOWED, required=True)
    parser.add_argument('--reviewed-config-sha256')
    options = parser.parse_args()
    module, unused_frozen, policy, config = load_runtime(options.physical)
    if options.action == 'validate':
        policy.validate(config)
        print(json.dumps(describe(options.physical, config), sort_keys=True))
    else:
        serve(options.physical, module, policy, config, options.reviewed_config_sha256)


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    main()

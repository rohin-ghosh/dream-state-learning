"""Source-bound R233 P3-only parent treatment; no learner controls."""

import argparse
import hashlib
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PREDECESSOR = REPO / 'research_loop/workers/rohin232_node4_parent_repair_20260918'
sys.path.insert(0, str(PREDECESSOR))
import parent as previous
import repair


POLICY = 'R233_P3_STRONG_DIVERSE_PARENT_V1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind(policy, brief):
    original_prompt = policy.prompt
    original_strong = policy.parent.strong

    def prompt(*arguments, **keywords):
        instruction, payload = original_prompt(*arguments, **keywords)
        return instruction + '\n\n' + brief, payload

    def strong(*arguments, **keywords):
        keywords['reasoning_effort'] = 'xhigh'
        return original_strong(*arguments, **keywords)

    policy.prompt = prompt
    policy.parent.strong = strong
    return policy


def load():
    module, unused_frozen, policy, config = previous.load_runtime(3)
    brief_path = HERE / 'P3_BRIEF.md'
    policy = bind(policy, brief_path.read_text())
    policy.validate(config)
    manifest = dict(policy=POLICY, physical=3,
        entrypoint_sha256=sha(HERE / 'p3_parent.py'), brief_sha256=sha(brief_path),
        handoff_sha256=sha(HERE / 'p3_handoff.py'),
        predecessor_entrypoint_sha256=sha(PREDECESSOR / 'parent.py'),
        predecessor_adapter_sha256=sha(PREDECESSOR / 'repair.py'),
        predecessor_config_sha256=sha(PREDECESSOR / 'physical3/CONFIG.json'),
        effective_reasoning_effort='xhigh', previous_reasoning_effort=config['parent_reasoning_effort'],
        model='existing_bound_Astra_provider_unchanged', cadence_responses=1,
        hard_end_unix=min(config['hard_end_unix'], module.base.WALL), learner_signals=[])
    return module, policy, config, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('validate', 'serve'))
    parser.add_argument('--manifest-sha256')
    options = parser.parse_args()
    module, policy, config, manifest = load()
    if options.action == 'validate':
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return
    approved = HERE / 'P3_MANIFEST.json'
    if options.manifest_sha256 != sha(approved) or json.loads(approved.read_text()) != manifest:
        raise ValueError('exact_reviewed_R233_manifest_required')
    previous.serve(3, module, policy, config, manifest['predecessor_config_sha256'])


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    main()

"""Non-material P3 parent validator repair: mathematics is not a foreign script."""

import argparse
import json
import sys
import types
import unicodedata

import p3_parent as predecessor
from p3_parent import HERE, PREDECESSOR, REPO, previous, repair, sha


POLICY = 'R233_P3_MATH_SYMBOL_VALIDATOR_REPAIR_V2'


def english_output(message, evidence_quotes):
    prose = message
    for quote in evidence_quotes:
        for opening, closing in (('"', '"'), ('“', '”'), ('`', '`')):
            prose = prose.replace(opening + quote + closing, '')
    repair.require(all(ord(character) < 128 or 'LATIN' in unicodedata.name(character, '')
        or unicodedata.category(character).startswith(('P', 'Z'))
        or unicodedata.category(character) == 'Sm' for character in prose),
        'English_prose_script_validation_failed_not_language_proof')


def load():
    module, frozen, policy, config = previous.load_runtime(3)
    policy = predecessor.bind(policy, (HERE / 'P3_BRIEF.md').read_text())
    community = types.SimpleNamespace(**vars(frozen.community))
    community.decision = repair.project(frozen.community.decision, repair.DECISION_EDITS, {})
    decision = repair.project(frozen.decision, (),
        dict(community=community, english_output=english_output))
    policy.decision = decision
    policy.tick = repair.project(frozen.tick, repair.TICK_EDITS,
        dict(validate=policy.validate, decision=decision,
             prompt=lambda *arguments, **keywords: policy.prompt(*arguments, **keywords)))
    policy.validate(config)
    predecessor_manifest = repair.read(HERE / 'P3_MANIFEST.json')
    repair.require(predecessor_manifest['entrypoint_sha256'] == sha(HERE / 'p3_parent.py')
        and predecessor_manifest['brief_sha256'] == sha(HERE / 'P3_BRIEF.md')
        and predecessor_manifest['handoff_sha256'] == sha(HERE / 'p3_handoff.py'),
        'unchanged_R233_treatment')
    manifest = dict(predecessor_manifest, policy=POLICY,
        classification='NON_MATERIAL_PARENT_VALIDATOR_REPAIR',
        entrypoint_sha256=sha(HERE / 'p3_parent_v2.py'),
        handoff_sha256=sha(HERE / 'p3_validation_handoff.py'),
        predecessor_manifest_sha256=sha(HERE / 'P3_MANIFEST.json'),
        parent_message_bytes='UNCHANGED', child_training='UNCHANGED',
        only_validator_delta='ALLOW_UNICODE_MATH_SYMBOL_CATEGORY_Sm_IN_PARENT_PROSE')
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
    approved = HERE / 'P3_VALIDATION_MANIFEST.json'
    if options.manifest_sha256 != sha(approved) or repair.read(approved) != manifest:
        raise ValueError('exact_reviewed_R233_validator_manifest_required')
    previous.serve(3, module, policy, config, manifest['predecessor_config_sha256'])


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    main()

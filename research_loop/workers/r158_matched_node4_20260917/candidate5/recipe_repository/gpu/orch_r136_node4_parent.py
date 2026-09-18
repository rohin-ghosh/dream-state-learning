"""Node4-only adapter for the existing TRAIN parent; no other parent is changed."""

import argparse
import hashlib
import json
from pathlib import Path
import unicodedata

from gpu import orch_r133_programme_parent as parent


ENGLISH_POLICY = (
    'Prospective parent-language phase: English only. Write every parent message and rationale in English, '
    'even when the child writes another language. Do not mirror its language or quote foreign-script passages; '
    'paraphrase necessary evidence in English. This is not a language-learning programme. '
    'Keep the existing sparse3 Socratic style and leave the child free to choose its own language. '
    'Do not rewrite, translate, sanitize or replay historical messages. '
    'Use Latin-script words and identifiers; publication rejects non-Latin alphabetic characters. '
    'That script check is not a complete English-language classifier. No retry after rejection.'
)


def validate(config):
    slots = {
        3: ('raw_parented_seed1', 'raw_parented', 3, 'Socratic'),
        4: ('kernel_parented', 'kernel', 2, 'experimental-coach'),
    }
    physical = config.get('physical')
    if type(physical) is not int or physical not in slots or config.get('node') != 'a40r':
        raise ValueError('only_owned_node4_parented_slots3_4')
    label, programme, cadence, style = slots[physical]
    prefix = f'/localhome/local-rohing/orch_r136_{label}_a40r{physical}_20260916_attempt1'
    sources = {prefix+'/source1'}
    if physical == 3:
        sources.add(prefix+'/source2')
    if (config.get('root') != prefix+'/run1' or config.get('source_root') not in sources
            or config.get('programme') != programme or config.get('cadence_responses') != cadence
            or config.get('parent_style') != style or config.get('cadence_label') != 'SPARSE'):
        raise ValueError('exact_R137_branch_cadence_style')
    if hashlib.sha256(Path(parent.__file__).read_bytes()).hexdigest() != config.get('parent_module_sha256'):
        raise ValueError('pinned_parent_module_required')
    if 'parent_language' in config:
        if (physical != 3 or config['parent_language'] != 'English'
                or config.get('language_phase') != 'R140_RAW3_ENGLISH_PARENT_V1'
                or ENGLISH_POLICY not in Path(config['programme_path']).read_text()):
            raise ValueError('exact_raw3_English_programme_phase')
    parent.PROGRAMMES = set(parent.PROGRAMMES) | {'kernel'}
    return parent.validate(config)


def require_english_message(message):
    if not isinstance(message, str) or not message.strip():
        raise ValueError('nonempty_English_parent_message')
    if any(character.isalpha() and 'LATIN' not in unicodedata.name(character, '')
           for character in message):
        raise ValueError('English_parent_policy_nonLatin_script_no_publish')


def serve(config_path, repository, output, once=False):
    config = validate(json.loads(Path(config_path).read_text()))
    original_publish = parent.publish

    def publish_english(repository, config, message):
        require_english_message(message)
        return original_publish(repository, config, message)

    if config.get('parent_language') == 'English':
        parent.publish = publish_english
    try:
        return parent.serve(config_path, repository, output, once=once)
    finally:
        parent.publish = original_publish


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'repository', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    options = parser.parse_args()
    serve(options.config, options.repository, options.output)


if __name__ == '__main__':
    main()

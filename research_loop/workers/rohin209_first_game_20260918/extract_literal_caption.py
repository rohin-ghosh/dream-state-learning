"""Preserve one observed container typo; never rewrite a child's caption string."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import time


STRING = r'"(?:[^"\\\x00-\x1f]|\\.)*"'
PATTERN = re.compile(r'\s*\[\s*\{\s*"contest_id"\s*:\s*(' + STRING +
                     r')\s*,\s*"text"\s*:\s*(' + STRING + r')\s*\)\s*\]\s*')


def extract(raw, allowed):
    match = PATTERN.fullmatch(raw)
    if not match:
        raise ValueError('only_exact_single_object_wrong_closing_parenthesis_is_supported')
    contest, caption = (json.loads(match.group(index)) for index in (1, 2))
    if contest not in allowed or not caption.strip() or len(caption.split()) > 50:
        raise ValueError('released_contest_and_bounded_literal_caption_required')
    return dict(contest_id=contest, text=caption), dict(contest_id_span=match.span(1), text_span=match.span(2))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(root, destination):
    root, destination = Path(root).resolve(), Path(destination).resolve()
    generated = json.loads((root / 'ACT_GENERATION.json').read_text())
    bound = json.loads((root / 'INPUT.json').read_text())
    loaded = json.loads((root / 'LOADED.json').read_text())
    if not generated['terminal'] or generated['truncated'] or loaded['adapter_state_sha256'] != bound['provenance']['adapter_state_sha256']:
        raise ValueError('complete_actual_frozen_C2_generation_required')
    action, spans = extract(generated['raw'], {scene['contest_id'] for scene in bound['factual_scenes']})
    action['origin'] = dict(actor='C2', stage='ACT', source_complete=51, model_generated=True,
                           raw_generation_sha256=digest(root / 'ACT_GENERATION.json'),
                           checkpoint_sha256=bound['provenance']['checkpoint']['sha256'],
                           adapter_state_sha256=loaded['adapter_state_sha256'], text_repaired=False,
                           original_wire_format_valid=False, wire_format_failure_retained=str(root / 'FAILED.json'),
                           extraction_policy='R209_SINGLE_OBJECT_LITERAL_FIELDS_CLOSING_PAREN_V1', **spans)
    destination.mkdir(parents=True, mode=0o700, exist_ok=False)
    (destination / 'actions.json').write_text(json.dumps([action], ensure_ascii=False, sort_keys=True))
    (destination / 'RECEIPT.json').write_text(json.dumps(dict(status='LITERAL_CAPTION_FIELDS_EXTRACTED',
        completed_unix=time.time(), original_wire_failure_count=1, original_caption_text_unchanged=True,
        malformed_generation_sha256=digest(root / 'ACT_GENERATION.json'),
        actions_sha256=digest(destination / 'actions.json'), raw_generation_changed=False), sort_keys=True))
    print(json.dumps(dict(status='LITERAL_CAPTION_FIELDS_EXTRACTED', count=1, text_repaired=False)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    run(args.root, args.output)

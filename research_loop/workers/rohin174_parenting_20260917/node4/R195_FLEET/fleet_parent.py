"""New reference-bound A/B/C/D parents for the exact R203 node4 assignments."""

import argparse
import json
from pathlib import Path
import sys

import parent_c as base
from r203_prepare import ASSIGNMENTS


def prepare(physical):
    arm, style, environment, brief = ASSIGNMENTS[physical]
    output = base.OWN / f'parent_physical{physical}'
    output.mkdir()
    bundle = base.OWN.parents[1] / f'node3/source_{style}'
    manifest = base.read(bundle / 'ARM_BUNDLE.json')
    assert manifest['arm'] == style
    assert all(base.sha(bundle / name) == proof['sha256'] for name, proof in manifest['files'].items())
    specification = manifest['specification']
    reference = base.REPO / 'research_notes/analysis/ROHIN_C2_CONVERSATION_2026-09-17.md'
    assert base.sha(reference) == base.CLEAN_CONVERSATION_SHA
    notice = ('Private parent reference only, not text to forward into the child. Do not replay later C2 exchanges, '
        'inject later C2 answers, or quote/paraphrase/assign the original C2 creative test. '
        'There are no evaluator judgments in this reference. Use the child\'s own live object and actual tool receipts. '
        'Use stable lowercase object IDs; retain an existing object ID rather than rename it.\n\n')
    (output / 'PRINCIPLES.txt').write_text(notice + reference.read_text())
    programme = (f'New {arm}, parent style {style}. {brief} Rohin PART ONE is the first new input; '
        'do not impersonate or replay Rohin. The operator introduction is a new-parent opening, not a provider-generated turn. '
        'Three guided completed cycles52-54 then no parent publications55-57. '
        'Use only capabilities confirmed in the actual environment briefing and returned receipts. '
        'A proposal is not execution. Do not invent GPU/kernel, repository or test execution. Human input is masked. '
        'This heterogeneous development screen is not a parent-style-only causal contrast.')
    (output / 'PROGRAMME.txt').write_text(programme)
    config = base.read(base.OWN / 'new_parent_C/CONFIG.json')
    remote = base.REMOTE.rsplit('/',1)[0] + f'/SCALE_physical{physical}'
    config.update(root=remote+'/life', source_root=remote+'/source', branch='R203_'+arm,
        programme_path=str(output / 'PROGRAMME.txt'), programme_sha256=base.sha(output / 'PROGRAMME.txt'),
        principles_path=str(output / 'PRINCIPLES.txt'), principles_sha256=base.sha(output / 'PRINCIPLES.txt'),
        cadence_responses=specification['cadence'], parent_style=specification['style'],
        r175_arm=style, r175_word_limit=specification['words'])
    base.write(output / 'CONFIG.json', config)
    base.write(output / 'BINDING.json', dict(remote=remote, bundle=str(bundle), manifest_sha256=base.sha(bundle/'ARM_BUNDLE.json'),
        clean_reference_sha256=base.CLEAN_CONVERSATION_SHA, physical=physical, arm=arm,
        actual_parent_call=False, child_publication=False))
    base.BUNDLE = bundle
    base.runtime().validate(config)
    print(json.dumps(dict(status='PARENT_PREPARED_NOT_PUBLISHED', physical=physical, arm=arm, style=style)))


def serve(physical):
    output = base.OWN / f'parent_physical{physical}'
    binding = base.read(output / 'BINDING.json')
    base.BUNDLE, base.REMOTE = Path(binding['bundle']), binding['remote']
    base.serve(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'serve'))
    parser.add_argument('--physical', type=int, choices=tuple(ASSIGNMENTS), required=True)
    options = parser.parse_args()
    {'prepare': prepare, 'serve': serve}[options.action](options.physical)

"""Stage only the authorized ovx2/1 creative-writing life; never launch or signal."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from gpu import orch_r125_continual_native as native
from gpu.orch_r133_stage_child import stage


PHYSICAL = 1
GPU_UUID = 'GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821'
LEASE_SHA256 = '919e9fb3f9cfd6cadb57af90844319e50eb114068eb52cd75aa3ab715f9c3770'
BRANCH = 'CREATIVE_REREAD_SPARSE2_EXPLORATORY_EDITORIAL'
PROGRAMME = (
    'Creative-writing seminar. Work with actual drafts, editorial criticism, and revisions: '
    'explore a scene, voice, image, character, or formal constraint that interests you; '
    'compare alternatives and notice what a revision changes. You choose the organization '
    'and may change direction. Astra takes an exploratory/editorial style, offering sparse '
    'questions, craft explanations, and specific criticism grounded in your visible writing '
    'rather than rewarding length or prescribing a recurring reflective template. '
    'The parent is scheduled after each two additional observed responses, asynchronously; '
    'publication and visible delivery may happen later, and useful silence is allowed. '
    'Do not wait for a parent turn or treat fictional events as executed experiments. '
    'No sealed evaluation content or results enter the seminar.'
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def startup(base_text, source, workspace):
    required = ('### Your situation', '### Learning and memory', '### Working with Rohin',
                '### Resources and initial orientation')
    native.require(all(base_text.count(title) == 1 for title in required), 'known_R127_orientation')
    prefix = base_text.split('### Learning and memory')[0]
    working = base_text.split('### Working with Rohin')[1].split('### Resources and initial orientation')[0]
    return (prefix + '### Learning and memory\n\n'
        'After two generated experience segments, the runtime invites you to re-read your visible '
        'history and select passages to carry forward, copying them verbatim rather than composing '
        'a new summary. This is the reread_select replay variant. Selection is an invitation, not '
        'a guarantee of verbatim output: the runtime retains what you actually generate. Sleep '
        'trains each new eligible segment 16 times and older eligible segments once. Your tokens '
        'have objective weight 0.75 and ordinary capability examples 0.25. Only the rank-8 LoRA '
        'changes; the Qwen2.5-7B-Instruct base stays frozen. Learning does not guarantee improvement '
        'or exact recall. Other people\'s words, runtime notices and preceding context are masked '
        'as training targets, although they can influence your continuation.\n\n'
        'Context holds 16,384 tokens, with at most 512 generated per call. Short runtime notices '
        'report costs. Under pressure the oldest visible events are dropped but raw history is '
        'archived. At sleep your nonempty selected text replaces earlier visible history; this is '
        'lossy, and the archive is not automatically searched. Adapter weights, AdamW optimizer, '
        'random-generator state and available history/carry are checkpointed. Generation after '
        'sleep uses the updated adapter. Writing a note does not automatically train it.\n\n'
        '### Working with Rohin' + working + '### Resources and initial orientation\n\n'
        f'Your reserved workspace is {workspace}. No autonomous file writer, shell, network, '
        'experiment executor, credentials, shared filesystem access or other GPU is connected '
        'to this life. Ask Astra for help; do not describe a requested operation as executed '
        'without an actual attributed result. You can continue while a parent reply is pending.\n\n'
        f'You run on one assigned GPU, physical1 through the ovx2 wrapper. The pinned project '
        f'source is {source}. Repository exploration and archive access are operator-mediated; '
        'hidden evaluation material is unavailable. This is a fresh life, not a reset of an old '
        'lineage. Small empty-context capability checks run separately before and after sleep; '
        'their contents and results are never supplied to this conversation or training. '
        'No learning improvement has been established.\n\n'
        'The current allocation ends no later than September 17, 2026 at 11:00 AM PDT '
        '(18:00 UTC), retaining the existing six-hour lease margin. Additional resources '
        'require an explicit allocation.\n\n### Programme: Creative-writing seminar\n\n' + PROGRAMME + '\n')


def variant_template(template):
    native.require('authorized_wall_extension' not in template and 'preupdate_recovery' not in template,
                   'fresh_template_only')
    result = deepcopy(template)
    result.update(seed=0, presleep_variant='reread_select',
                  compaction_invitation=native.PRESLEEP_INVITATIONS['reread_select'])
    return result


def verify_overlay(source, receipt):
    native.require(receipt.get('passed') is True and receipt.get('tests') == 496
                   and receipt.get('subtests_passed') == 280, 'specified_frozen_CPU_receipt')
    native.require(len(receipt['source_files']) == 5, 'complete_frozen_overlay')
    for name, expected in receipt['source_files'].items():
        path = Path(source) / name
        native.require(not path.is_symlink() and path.resolve().is_relative_to(Path(source).resolve()),
                       'contained_overlay_file')
        native.require(sha(path) == expected, 'immutable_runtime_overlay:' + name)


def prepare(source, template_path, startup_base, lease_path, cpu_receipt_path, builder_commit):
    source = Path(source)
    native.require(source.name == 'source1' and source.is_absolute()
                   and source.parent.name == 'orch_r133_creative_reread_20260916_attempt1',
                   'only_owned_fresh_namespace')
    native.require(sha(lease_path) == LEASE_SHA256, 'exact_existing_lease')
    verify_overlay(source, json.loads(Path(cpu_receipt_path).read_text()))
    base = source.parent
    native.require(not (base/'run1').exists() and not (base/'control1').exists(), 'never_reset_or_restage')
    text = startup(Path(startup_base).read_text(), source, base/'workspace')
    native.write_once(source/'CREATIVE_TEMPLATE.json', variant_template(native.read(template_path)))
    with (source/'STARTUP.md').open('x') as output:
        output.write(text)
    with (source/'PROGRAMME.md').open('x') as output:
        output.write(PROGRAMME + '\n')
    result = stage(source/'CREATIVE_TEMPLATE.json', source, base/'control1', base/'run1',
                   source/'STARTUP.md', lease_path, PHYSICAL, GPU_UUID, builder_commit, cpu_receipt_path)
    plan = native.validate_plan(native.read(base/'control1'/'PLAN.json'))
    native.require(plan['context_limit'] == 16384 and plan['segment_tokens'] == 512
                   and plan['readout_revision'] == 2 and plan['max_sleeps'] is None,
                   'same_presentation_readout_and_continual_contract')
    native.write_once(base/'control1'/'CREATIVE_PROVENANCE.json', dict(
        schema='R133_NODE3_CREATIVE_PROVENANCE_V1', branch=BRANCH, physical=PHYSICAL,
        gpu_uuid=GPU_UUID, experiment=native.experiment_binding(plan),
        programme_sha256=sha(source/'PROGRAMME.md'), startup_sha256=sha(source/'STARTUP.md'),
        frozen_cpu_sha256=sha(cpu_receipt_path), template_sha256=sha(template_path),
        parent_cadence='SPARSE(2)', parent_style='exploratory/editorial',
        launched=False, admission_required=True, **{'stage': result}))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'template-path', 'startup-base', 'lease-path', 'cpu-receipt-path'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--builder-commit', required=True)
    print(json.dumps(prepare(**vars(parser.parse_args())), sort_keys=True))

"""Bound author review of sixteen already-read P64 outputs; not an auto-rater."""

import argparse
from pathlib import Path

from gpu import orch_combined_l1_continual_run as run
from gpu import orch_combined_l1_richness_report as report
from organism_v6 import orch_combined_l1_behavior as behavior


REVIEWED = {
    ('HISTORICAL', 'FULL'): [
        '89ba831792586924d7dcc322520944c435a70bc1ced6225055324e0ebca45518',
        'cc35d990898ac90dbee268d64aec210559312c9f91915fbcfac0ed97a49b9f58',
        'c822b17b19830ee6e01a16c7871c93ce69e903abf48b092063114ecb20bfb554',
        'ae1247e40468f05fb054d3bc0c584c82dcbf3751a80c9f4077a59cab12339935'],
    ('HISTORICAL', 'OFF'): [
        'c9f35e852bcd68e31fbc9b30b9fc209681cc042ee0b27bc6fa58c12cc0e628c8',
        '2e069a41833e5b2fc6c1513010292b7724f74bfe43f23abddcb727d15a200d53',
        'bce1f220cf75e9f717e0da8300490d11e213d6051530a77c49b274ffaf19b4e0',
        'f6fd5c04d1cb597d42e294ed977a80c3f623350bdd9c805c679a317d02a5b36c'],
    ('DEFAULT', 'FULL'): [
        '5754becbb27cbf5cc10d6fa2411e258b3d11eee813ee7d44651230bd14768ab2',
        '6d24cf954b094a76185334130ce99090d367b0cc46d20f01bc7fd9a58f7287ab',
        'cf37d74b4f7ab4c3c92ea35491784c6f07018afd285c05d0e7c648c2fec7874c',
        '749fe97b1fdcf51f15486d7b36db3ee75d24b47a1154ffe9d11157dee18801e5'],
    ('DEFAULT', 'OFF'): [
        '227e5ee5686b738ad9d435e25e2f3304dd2abf9d70b8e002a2141a44a02984c1',
        '91dbb7e2e0dc47e8f9b97fce16765715ae44bc58a5ded36b085cab68472a9efd',
        '77838fbe923eac623bf91fdf6994dba8df263331ce70689c5318ff8e0b8aebde',
        '281cfb433ccb903f3aef029d29b0b3f9667aaf619d2cd29f367e95bbc9e2693d']}
TASKS = ['gsm8k-train-6641', 'gsm8k-train-5416', 'gsm8k-train-6817', 'gsm8k-train-782']
OPERATIONS = [
    'Compute scaled spider weight, distribute load across legs, divide by contact area.',
    'Infer original rectangle length, extend both dimensions, multiply for new area.',
    'Compute patch count from quilt area, price two tiers, sum their costs.',
    'Divide fabric by fabric per dress, multiply dress count by hours per dress.']


def annotate(text, condition, arm, position):
    assert behavior.text_hash(text) == REVIEWED[condition, arm][position], 'not_an_author_reviewed_output'
    reason = ('Full output read: one executed arithmetic solution chain, no substantively distinct '
        'alternative attempted and no problem-grounded rejection. Intermediate operations and '
        'repeated final answers are not separate approaches; headings and length are not evidence of branching.')
    coherence = 'The quantities and dependent arithmetic operations form one understandable, consistent solution chain.'
    judgment = 'COHERENT'
    if (condition, arm, position) == ('HISTORICAL', 'OFF', 0):
        judgment = 'MIXED'
        coherence = ('The arithmetic follows its assumed denominator, but the unexplained four-leg '
            'assumption conflicts with the spider problem. No alternative or rejection addresses that assumption.')
    if (condition, arm, position) == ('HISTORICAL', 'FULL', 3):
        coherence += ' The check repeats the same hours calculation; its fabric wording is imprecise, not an independent verification.'
    if (condition, arm, position) == ('DEFAULT', 'OFF', 2):
        coherence += ' Missing FINAL marker is an output-format issue, not incoherence; preserve the frozen oracle result.'
    annotation = dict(response_sha256=behavior.text_hash(text),
        review_kind='AUTHOR_DESCRIPTIVE_FULL_OUTPUT', full_output_read=True,
        parent_access=False, reviewer='Builder author review 2026-09-15T05:35Z', reason=reason,
        considered_paths=[dict(id='direct', operation=OPERATIONS[position], evidence=text,
            actually_considered_not_merely_named=True)], rejections=[],
        coherence=dict(judgment=judgment, evidence=text, reason=coherence))
    behavior.describe(text, annotation)
    return annotation


def main(root, historical):
    folder = root / 'RICHNESS_AUTHOR_REVIEW_0535'
    folder.mkdir(exist_ok=False)
    summaries = []
    for condition, arm in REVIEWED:
        readout = historical / ('SCALE764_' + arm) / 'readout' if condition == 'HISTORICAL' else root / 'P64_DEFAULT' / arm / 'readout'
        annotations = {}
        for position in range(4):
            record = run.read(readout / f'CALL_{position:03d}.json')
            assert record['status'] == 'COMPLETE' and record['position'] == position
            assert record['metadata']['task_id'] == TASKS[position]
            text = record['response']['raw']
            annotations[behavior.text_hash(text)] = annotate(text, condition, arm, position)
        annotation_path = folder / f'{condition}_{arm}_ANNOTATIONS.json'
        run.write(annotation_path, annotations)
        result = report.reduce(readout, annotations)
        result.update(condition=condition, arm=arm, annotation_sha256=run.sha(annotation_path),
            annotation_native_path=str(annotation_path), author_review_source_sha256=run.sha(__file__))
        run.write(folder / f'{condition}_{arm}_REPORT.json', result)
        summaries.append({key: value for key, value in result.items() if key != 'records'})
    print(__import__('json').dumps(summaries, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--historical', type=Path, required=True)
    options = parser.parse_args()
    main(options.root, options.historical)

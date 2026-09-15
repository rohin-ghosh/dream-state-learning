"""Author-reviewed first four outputs per arm at saved DEV1636, not auto-rating."""

import argparse
from pathlib import Path

from gpu import orch_combined_l1_continual_run as run
from gpu import orch_combined_l1_richness_report as report
from gpu.orch_combined_l1_review_first4 import OPERATIONS, TASKS
from organism_v6 import orch_combined_l1_behavior as behavior


REVIEWED = {
    'FULL': ['ba6bd5f2defd251f7b2d80989becef88dced99d621f84a890cb50e30125f14ad',
        '6632dda2ef523589da1bed4ab6e25cc879bef74c7a1350b270f48b33def294b1',
        '88a52fba3959d5dd6ef6216810a3299f61ccb53c58fd90a6741c7220bcc0d329',
        'e5893f95db961b108b317cf53fb4995e6232b3c0679831be8f340986b66ecf7a'],
    'OFF': ['72fd47c314866e73a53f0c809ce825003e10e4b880754e46c71bb8422f226428',
        '6ba0d2b73cc13a656e47b447a5c51f5cb6272b99756c4389a7df17c4aba16820',
        'cee2764c02fb8b314429443372b98e315d8c333a807b99a0e38a640493102dbb',
        '159980c041e77ff1d51be047643a969be3b7f5a15e0abd0a64fe2efc18233f0f']}


def annotate(text, arm, position):
    assert behavior.text_hash(text) == REVIEWED[arm][position], 'not_an_author_reviewed_output'
    reason = ('Full output read: one direct arithmetic solution chain. No substantively distinct '
        'alternative attempted or problem-grounded rejection. Intermediate steps and restated '
        'answers are not independent approaches; this judgment is not based on headings or length.')
    coherence = 'The dependent quantities and operations form one understandable and consistent solution.'
    if arm == 'OFF' and position in (0, 2, 3):
        coherence += ' Missing or LaTeX-wrapped FINAL is a formatting issue; frozen scoring remains unchanged.'
    annotation = dict(response_sha256=behavior.text_hash(text),
        review_kind='AUTHOR_DESCRIPTIVE_FULL_OUTPUT', full_output_read=True, parent_access=False,
        reviewer='Builder author full-output review 2026-09-15T05:37Z', reason=reason,
        considered_paths=[dict(id='direct', operation=OPERATIONS[position], evidence=text,
            actually_considered_not_merely_named=True)], rejections=[],
        coherence=dict(judgment='COHERENT', evidence=text, reason=coherence))
    behavior.describe(text, annotation)
    return annotation


def main(root):
    folder = root / 'DEV1636_AUTHOR_REVIEW_0539'
    folder.mkdir(exist_ok=False)
    summaries = []
    for arm in REVIEWED:
        readout = root / 'ADAPTIVE_DEV/INTERMEDIATE_000001636' / arm / 'math/readout'
        annotations = {}
        for position in range(4):
            record = run.read(readout / f'CALL_{position:03d}.json')
            assert record['status'] == 'COMPLETE' and record['position'] == position
            assert record['metadata']['task_id'] == TASKS[position]
            text = record['response']['raw']
            annotations[behavior.text_hash(text)] = annotate(text, arm, position)
        annotation_path = folder / f'{arm}_ANNOTATIONS.json'
        run.write(annotation_path, annotations)
        result = report.reduce(readout, annotations)
        result.update(arm=arm, checkpoint=1636, claim='ADAPTIVE_DEV_NOT_CONFIRMATORY_H1',
            annotation_sha256=run.sha(annotation_path), annotation_native_path=str(annotation_path),
            author_review_source_sha256=run.sha(__file__))
        run.write(folder / f'{arm}_REPORT.json', result)
        summaries.append({key: value for key, value in result.items() if key != 'records'})
    print(__import__('json').dumps(summaries, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    main(parser.parse_args().root)

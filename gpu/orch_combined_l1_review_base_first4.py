"""Bound author review of the prospective first four true BASE outputs."""

import argparse
from pathlib import Path

from gpu import orch_combined_l1_continual_run as run
from gpu import orch_combined_l1_richness_report as report
from gpu.orch_combined_l1_review_first4 import OPERATIONS, TASKS
from organism_v6 import orch_combined_l1_behavior as behavior


REVIEWED = ['b96c98aeb2dd83de0c71ec4b5c732e9263a1777420e4dfd1c601dd4b0b1b9c63',
    '998846e4523977c9b7a48a846779e8cda9cc8283df8bc95788ec0926a83593fa',
    '2f77eba9963eabc8de94c0f87e453eed40adf1910290c4624cef565d3d2ab0e4',
    '189dcb28ccf5e210d3f2cee8a1972a93d2a3774993fae01de5529e8759d13a55']


def annotate(text, position):
    assert behavior.text_hash(text) == REVIEWED[position], 'not_an_author_reviewed_output'
    annotation = dict(response_sha256=behavior.text_hash(text),
        review_kind='AUTHOR_DESCRIPTIVE_FULL_OUTPUT', full_output_read=True, parent_access=False,
        reviewer='Builder author full-output review 2026-09-15T05:43Z',
        reason='One direct executed arithmetic solution; intermediate steps are not distinct approaches. No alternative or grounded rejection considered. Full output read, not headings or length classification.',
        considered_paths=[dict(id='direct', operation=OPERATIONS[position], evidence=text,
            actually_considered_not_merely_named=True)], rejections=[],
        coherence=dict(judgment='COHERENT', evidence=text,
            reason='Dependent quantities and arithmetic form a coherent solution; no substantive contradiction or abandoned path.'))
    behavior.describe(text, annotation)
    return annotation


def main(root):
    readout = root / 'P64_DEFAULT/BASE/readout'
    identity = run.read(readout / 'LOADED.json')
    assert identity['adapter'] is None and identity['active_lora'] is False
    assert identity['training_updates'] == 0 and identity['parent_present'] is False
    annotations = {}
    for position in range(4):
        record = run.read(readout / f'CALL_{position:03d}.json')
        assert record['status'] == 'COMPLETE' and record['position'] == position
        assert record['metadata']['task_id'] == TASKS[position]
        text = record['response']['raw']
        annotations[behavior.text_hash(text)] = annotate(text, position)
    folder = root / 'BASE_AUTHOR_REVIEW_0543'
    folder.mkdir(exist_ok=False)
    path = folder / 'ANNOTATIONS.json'
    run.write(path, annotations)
    result = report.reduce(readout, annotations)
    result.update(arm='BASE', condition='MINIMAL_DEFAULT_TRUE_NO_ADAPTER', identity=identity,
        annotation_sha256=run.sha(path), annotation_native_path=str(path),
        author_review_source_sha256=run.sha(__file__))
    run.write(folder / 'REPORT.json', result)
    print(__import__('json').dumps({key: value for key, value in result.items() if key != 'records'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    main(parser.parse_args().root)

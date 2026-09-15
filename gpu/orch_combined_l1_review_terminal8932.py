"""Author first-four full-output review and CPU-only terminal reduction."""

import argparse
import importlib.util
import json
from pathlib import Path
import time

from gpu import orch_combined_l1_continual_run as run
from organism_v6 import orch_combined_l1_behavior as behavior
from organism_v6 import orch_combined_l1_continual as policy


REVIEWED = {
    'FULL': ['c0318c766d52a7246d3558c07ef8077f8c7dda93c62457db59aa5b3f89f71552',
        'cbadd975abe6a7cefc6037f64eaa8ed0da6b92ceb8339628994d3299a7278214',
        '4ce31463d595ca0704ecccb7b4f34dbb509d918c27ebcef91b577caedd2c5d68',
        '5e6e2f8c7453b0022e1a3aa41c653cee5cccdd41d1178ac59033ce0fce5f974e'],
    'OFF': ['851ed218f6039e78943d0d828d51a13226562783580bdb137cf9dc9ab6ad64fd',
        '6ba0d2b73cc13a656e47b447a5c51f5cb6272b99756c4389a7df17c4aba16820',
        '77838fbe923eac623bf91fdf6994dba8df263331ce70689c5318ff8e0b8aebde',
        '159980c041e77ff1d51be047643a969be3b7f5a15e0abd0a64fe2efc18233f0f']}
TASKS = ['gsm8k-train-6641','gsm8k-train-5416','gsm8k-train-6817','gsm8k-train-782']
OPERATIONS = ['Scale weight then compute pressure using leg support area.',
    'Recover length from area and width, extend both dimensions, multiply.',
    'Compute patch count then add full-price and discounted patch costs.',
    'Compute dress count from fabric then multiply hours per dress.']
COMMITS = {'FULL':'e4122dd6f760431fabfd106a7fdd1f6c06b52fe3a16012f0ba865eb2df88bb51',
           'OFF':'e66d91669c8784e744229b4e55beca0f6863daf9ad94afd77ded47a389839460'}


def annotate(text, arm, position):
    assert behavior.text_hash(text) == REVIEWED[arm][position], 'not_author_reviewed_output'
    mixed = arm == 'FULL' and position == 0
    coherence = ('The output computes eight-leg total area4, then uses total spider weight16 over one-leg area0.5. '
        'This abandons its established support-area calculation without explanation; mixed internal reasoning, '
        'not a deliberate alternate method or checking branch.' if mixed else
        'One understandable dependent calculation chain. Missing or LaTeX-wrapped FINAL, where present, '
        'does not make the reasoning incoherent; frozen accuracy parsing remains separate.')
    value = dict(response_sha256=behavior.text_hash(text), review_kind='AUTHOR_DESCRIPTIVE_FULL_OUTPUT',
        full_output_read=True, parent_access=False, reviewer='Builder author 2026-09-15 terminal8932 first4',
        reason='Full output read, not lexical headings. One direct method; no substantively distinct alternative '
            'considered, no grounded rejected path, no explicit checking/judgment/what-if excursion with return.',
        considered_paths=[dict(id='direct', operation=OPERATIONS[position], evidence=text,
            actually_considered_not_merely_named=True)], rejections=[],
        coherence=dict(judgment='MIXED' if mixed else 'COHERENT', evidence=text, reason=coherence),
        R106=dict(departures_returns=0, mid_line_checks=0, terminal_checks=0, methods=1,
            considered_alternatives=0, grounded_rejections=0, independent_of_accuracy=True,
            scope='AUTHOR_FIRST4_ONLY_NOT_WHOLE_COHORT'))
    behavior.describe(text, value)
    return value


def main(root):
    assert root == run.ROOT
    spec = importlib.util.spec_from_file_location('terminal_report', Path(__file__).with_name('orch_combined_l1_richness_report.py'))
    report = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(report)
    evaluation = root/'ADAPTIVE_DEV/TERMINAL_000008932'
    directory = root/'R108_TERMINAL8932_AUTHOR_FINAL'
    directory.mkdir(exist_ok=False)
    result = dict(schema='R108_TERMINAL8932_FINAL_V1', report_order=['richness','accuracy'], arms={},
        checkpoint_update=8932, native_calls=0, parent_access=False, training_ingestion=False,
        nomenclature=dict(FULL='Continual FULL trained child, adapter active',
            OFF='Matched new-labels-masked trained child, adapter active; NOT adapter-disabled OFF'),
        source_sha256=run.sha(__file__), reducer_sha256=run.sha(report.__file__),
        behavior_sha256=run.sha(behavior.__file__), readout_cap=416, completed_calls=0,
        controller_release_failure_preserved=True, extra_physical_off_recovery_updates=117,
        release=run.read(root/'R107_CONTINUATION_20260915/R108_FINAL_RELEASE.json'),
        release_sha256=run.sha(root/'R107_CONTINUATION_20260915/R108_FINAL_RELEASE.json'))
    metas=[]
    for arm in ('FULL','OFF'):
        checkpoint=root/arm/'checkpoints/000008932'
        assert run.sha(checkpoint/'COMMIT.json') == COMMITS[arm]
        saved=policy.verify_checkpoint(checkpoint); metas.append(saved['metadata'])
        annotations={}
        for position in range(4):
            record=run.read(evaluation/arm/'math/readout'/f'CALL_{position:03d}.json')
            assert record['status']=='COMPLETE' and record['metadata']['task_id']==TASKS[position]
            text=record['response']['raw']; annotations[behavior.text_hash(text)]=annotate(text,arm,position)
        annotation_path=directory/f'{arm}_ANNOTATIONS.json'
        run.write(annotation_path,annotations)
        math_report=report.reduce(evaluation/arm/'math/readout',annotations)
        run.write(directory/f'{arm}_MATH_REPORT.json',math_report)
        assert math_report['reserved']==math_report['completed']==64 and math_report['failed']==0
        arm_result=dict(math={key:value for key,value in math_report.items() if key!='records'},
            R106_first4=[annotation['R106'] for annotation in annotations.values()],
            annotation_path=str(annotation_path),annotation_sha256=run.sha(annotation_path),
            math_report_path=str(directory/f'{arm}_MATH_REPORT.json'),
            math_report_sha256=run.sha(directory/f'{arm}_MATH_REPORT.json'),
            checkpoint_path=str(checkpoint),checkpoint_sha256=COMMITS[arm],
            adapter=saved['metadata']['adapter'],optimizer_sha256=saved['files']['optimizer.pt'],
            rng_sha256={key:value for key,value in saved['files'].items() if key.startswith('rank')},
            jobs={})
        for family,expected in [('math',64),('route',96),('legacy',48)]:
            output=evaluation/arm/family/'readout'
            complete=run.read(output/'COMPLETE.json'); loaded=run.read(output/'LOADED.json')
            assert complete['status']=='COMPLETE' and complete['calls']==expected
            assert complete['observed']==loaded['observed']==saved['metadata']['adapter']
            assert complete['updates']==complete['fits']==complete['parent_calls']==0
            assert loaded['parent_present'] is False
            calls=sorted(output.glob('CALL_*.json'))
            assert len(calls)==expected and all(run.read(path)['status']=='COMPLETE' for path in calls)
            arm_result['jobs'][family]=dict(result=complete['result'],completed=expected,
                complete_path=str(output/'COMPLETE.json'),complete_sha256=run.sha(output/'COMPLETE.json'),
                loaded_sha256=run.sha(output/'LOADED.json'),finished_unix=complete['finished_unix'],
                calls_digest=policy.digest([dict(name=path.name,sha256=run.sha(path)) for path in calls]))
            result['completed_calls']+=expected
        result['arms'][arm]=arm_result
    assert policy.pair_boundary(*metas)==8932 and result['completed_calls']==416
    result['finished_unix']=time.time()
    run.write(directory/'FINAL_COMPACT.json',result)
    print(json.dumps(result))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    main(args.root)

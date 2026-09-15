"""Prospective atomic append using the frozen C2 native reviewer/encoder unchanged."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import time
from types import FunctionType, SimpleNamespace

try:
    import orch_r109_l1_feed as feed
except ImportError:
    from gpu import orch_r109_l1_feed as feed


require, read, sha, write = feed.require, feed.read, feed.sha, feed.write


def validate_extension(previous_rows, rows, previous_encoded, encoded):
    require(len(rows)>len(previous_rows) and rows[:len(previous_rows)]==previous_rows,
            'preserve_every_previous_row_in_order')
    require(set(encoded)==set(previous_encoded), 'same_source_buckets')
    require(all(encoded[key]==value for key,value in previous_encoded.items() if key!='eligible'),
            'rehearsal_and_anchor_bytes_unchanged')
    require(encoded['eligible'][:len(previous_rows)]==previous_encoded['eligible'] and
            len(encoded['eligible'])==len(rows), 'preserve_previous_encoding')
    require(len({row['target_sha256'] for row in rows})==len(rows) and
            len({row['source_task_id'] for row in rows})==len(rows), 'no_duplicate_target_or_task')
    for row in rows[len(previous_rows):]:
        require(row['source_label']==feed.experience.SOURCE_LABEL and row['split']=='TRAIN'
                and row['teacher_or_l2'] is False and row['target_actor']=='CHILD'
                and row['parent_text_masked'] is True, 'same_self_TRAIN_source_only')


def verify(root):
    from gpu.orch_math_rich_source import verify_archive
    root=Path(root)
    require(root.parent==feed.ORIGIN and root.name.startswith('experience_feed_append_'), 'owned_append_root')
    manifest=read(root/'MANIFEST.json')
    require(sha(__file__)==manifest['source_sha256'] and sha(root/'source.tar')==manifest['archive_sha256']
            and verify_archive(root/'source.tar',root/'source')==manifest['source_files'], 'append_source_archive')
    require(sha(root/'REVIEWS.json')==manifest['reviews_sha256'] and
            sha(feed.ROOT/'RUNTIME.json')==manifest['feed_runtime_sha256'], 'frozen_review_and_runtime')
    feed.runtime()
    version=manifest['version']
    require(type(version) is int and version>=2, 'prospective_append_version')
    parent=feed.ROOT/'versions'/f'{version-1:03d}'
    require(sha(parent/'PLAN.json')==manifest['parent_plan_sha256'], 'exact_previous_cohort')
    feed.version_verify(parent)
    return manifest,parent


def prepare(root):
    manifest,parent=verify(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU_only_append')
    previous_rows=read(parent/'ELIGIBLE.json')['rows']
    previous_encoded=read(parent/'ENCODED.json')
    require(len(read(root/'REVIEWS.json')['batches'])==1,'one_reviewed_batch_per_append')
    proxy=SimpleNamespace(**dict(feed.experience.__dict__,ROOT=parent))
    namespace=dict(feed.__dict__,ROOT=root,experience=proxy,runtime=lambda:feed.runtime())
    runner=FunctionType(feed.prepare.__code__,namespace,'prepare_append',feed.prepare.__defaults__)
    runner()
    folder=root/'versions/000'
    rows,encoded=read(folder/'ELIGIBLE.json')['rows'],read(folder/'ENCODED.json')
    validate_extension(previous_rows,rows,previous_encoded,encoded)
    plan=read(folder/'PLAN.json')
    plan.update(cohort_id=f'R109_EXPERIENCE_C2_B{manifest["version"]:03d}',batch_number=manifest['version'],
        cohort_archive_sha256=read(feed.ROOT/'RUNTIME.json')['archive_sha256'],
        append_manifest_sha256=sha(root/'MANIFEST.json'),append_source_archive_sha256=manifest['archive_sha256'])
    write(folder/'PLAN.json',plan)
    decisions=read(root/'ADMISSION_DECISIONS.json')
    for row in decisions['decisions']:
        row['batch']=manifest['version']
    decisions.update(previous_eligible_rows=len(previous_rows),published_at_segment_boundary_only=True)
    write(folder/'APPEND_ADMISSIONS.json',decisions)
    prepared=read(folder/'PREPARED.json')
    prepared.update(plan_sha256=sha(folder/'PLAN.json'),append_admissions_sha256=sha(folder/'APPEND_ADMISSIONS.json'))
    write(folder/'PREPARED.json',prepared)
    print(json.dumps(dict(version=manifest['version'],new_rows=len(rows)-len(previous_rows),total=len(rows),
                          prepared_sha256=sha(folder/'PREPARED.json'),not_published=True)))


def publish(root):
    manifest,parent=verify(root)
    receipt=read(root/'PRE_GPU.json')
    require(receipt['cpu_passed'] and receipt['builder_line'].startswith('[Builder]') and
            receipt['manifest_sha256']==sha(root/'MANIFEST.json') and
            receipt['tests_sha256']==sha(root/'CPU_TESTS.log'), 'append_preGPU_receipt')
    require(time.time()<feed.CUTOFF-600,'original_cutoff')
    versions=feed.ROOT/'versions'
    require(sorted(int(path.name) for path in versions.iterdir() if path.is_dir())==list(range(manifest['version'])),
            'append_next_only_no_replacement')
    pending=root/'versions/000'
    feed.version_verify(pending)
    prepared=read(pending/'PREPARED.json')
    require(prepared['append_admissions_sha256']==sha(pending/'APPEND_ADMISSIONS.json'),'append_decision_binding')
    validate_extension(read(parent/'ELIGIBLE.json')['rows'],read(pending/'ELIGIBLE.json')['rows'],
                       read(parent/'ENCODED.json'),read(pending/'ENCODED.json'))
    destination=versions/f'{manifest["version"]:03d}'
    require(not destination.exists(),'immutable_destination_absent')
    before={arm:read(feed.ROOT/('HEARTBEAT_'+arm+'.json')) for arm in feed.SLOTS}
    os.rename(pending,destination)
    result=dict(version=manifest['version'],destination=str(destination),published_unix=time.time(),
        plan_sha256=sha(destination/'PLAN.json'),manifest_sha256=sha(root/'MANIFEST.json'),
        preGPU_sha256=sha(root/'PRE_GPU.json'),prior_plan_sha256=sha(parent/'PLAN.json'),
        active_bindings_unchanged=True,before=before,signals_sent=0,optimizer_reset=False)
    write(root/'PUBLISHED.json',result)
    print(json.dumps(result))


def status():
    try:
        import orch_r109_l1_feed_status as observer
    except ImportError:
        from gpu import orch_r109_l1_feed_status as observer
    result=observer.snapshot(feed.ROOT)
    decisions=read(feed.ROOT/'ADMISSION_DECISIONS.json')['decisions']
    bound=[]
    for path in sorted((feed.ROOT/'versions').glob('*/APPEND_ADMISSIONS.json')):
        require(sha(path)==read(path.parent/'PREPARED.json')['append_admissions_sha256'],'published_admission_hash')
        decisions+=read(path)['decisions']
        bound.append(dict(path=str(path),sha256=sha(path)))
    result['admissions']=observer.admission_rate(decisions,result['observed_unix'])
    result['append_admission_bindings']=bound
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','publish','status'))
    parser.add_argument('--root',type=Path)
    parser.add_argument('--watch',action='store_true')
    args=parser.parse_args()
    if args.action=='prepare':
        prepare(args.root)
    elif args.action=='publish':
        publish(args.root)
    else:
        while True:
            document=status()
            if not args.watch:
                print(json.dumps(document,indent=2))
                break
            write(args.root/'PROGRESS.json',document)
            if time.time()>=feed.END:
                break
            time.sleep(min(60,max(0,feed.END-time.time())))

"""Hash/count-only actual C3 consumer evidence, never a readout-score gate."""

import argparse
import hashlib
import json
from pathlib import Path
import time


def digest(data):
    return hashlib.sha256(data).hexdigest()


def actual_selections(losses, new_targets):
    result = {target['target_sha256']:dict(source_task_id=target['source_task_id'],
        presentations=0, active_tokens=0, updates=[]) for target in new_targets.values()}
    for record in losses:
        for source, position in record['selections']:
            if source == 'eligible' and position in new_targets:
                target = new_targets[position]
                entry = result[target['target_sha256']]
                entry['presentations'] += 1
                entry['active_tokens'] += record['eligible_supervised_tokens']
                entry['updates'].append(record['update'])
    return result


def snapshot(root):
    read = lambda path:json.loads(path.read_text())
    config = read(root/'CAMPAIGN.json')
    report = dict(observed_unix=time.time(),campaign_sha256=digest((root/'CAMPAIGN.json').read_bytes()),
        activation_update=config['activation_update'],published_new_rows=3,arms={},
        score_claim=False,readout_scores_not_read=True)
    for arm in ('FULL','CONTROL'):
        summaries=[]
        for stage in sorted((root/arm).glob('segment*')):
            binding=read(stage/'BINDING.json')
            assert binding['campaign_sha256']==report['campaign_sha256']
            cohort=Path(binding['cohort_record']['path'])
            plan=read(cohort/'PLAN.json')
            eligible_bytes=(cohort/'ELIGIBLE.json').read_bytes()
            assert digest(eligible_bytes)==plan['eligible_sha256']
            rows=json.loads(eligible_bytes)['rows']
            targets={index:row for index,row in enumerate(rows) if index>=19}
            folder=stage/'fit'/arm/stage.name
            loss_path=folder/'RANK0_LOSSES.jsonl'
            losses=[]
            loss_hash=None
            if loss_path.exists():
                data=loss_path.read_bytes()
                complete=data[:data.rfind(b'\n')+1]
                loss_hash=digest(complete)
                losses=[json.loads(line) for line in complete.splitlines()]
            loaded=folder/'RANK0_LOADED.json'
            entry=dict(segment=stage.name,cohort=binding['cohort'],start_update=binding['start_update'],
                native_loaded=loaded.exists(),optimizer_updates=len(losses),
                latest_update=losses[-1]['update'] if losses else None,loss_prefix_sha256=loss_hash,
                newly_selected_targets=actual_selections(losses,targets),
                checkpoint_complete=(folder/'COMPLETE.json').exists(),
                paired_complete=(stage/'PAIRED_COMPLETE.json').exists(),
                readout_complete={condition:(folder/'readout'/condition/'COMPLETE.json').exists() for condition in ('ON','OFF')})
            if loaded.exists():
                document=read(loaded)
                assert document['eligible_sha256']==plan['eligible_sha256']
                entry['restore']={key:document[key] for key in ('update','optimizer_restored','rng_restored','global_cursor_preserved','state_sha256')}
                entry['loaded_sha256']=digest(loaded.read_bytes())
            summaries.append(entry)
        heartbeat=root/('HEARTBEAT_'+arm+'.json')
        report['arms'][arm]=dict(released=(root/('RELEASED_'+arm+'.json')).exists(),
            heartbeat=read(heartbeat) if heartbeat.exists() else None,segments=summaries,
            actual_C3_loaded=any(item['cohort']=='C3' and item['native_loaded'] for item in summaries),
            actual_C3_new_target_presentations=sum(target['presentations'] for item in summaries if item['cohort']=='C3'
                for target in item['newly_selected_targets'].values()),
            actual_C3_new_target_active_tokens=sum(target['active_tokens'] for item in summaries if item['cohort']=='C3'
                for target in item['newly_selected_targets'].values()))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    options=parser.parse_args()
    print(json.dumps(snapshot(options.root),indent=2,sort_keys=True))

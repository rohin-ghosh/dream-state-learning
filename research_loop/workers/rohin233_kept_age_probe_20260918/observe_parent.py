"""Report source-bound parent rendering, not only endpoint setup."""

import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess


CODE = '''import hashlib,json,pathlib,time
from tokenizers import Tokenizer
root=pathlib.Path('/localhome/local-rohing/orch_r233_base_parent_20260918')
player=pathlib.Path('/localhome/local-rohing/orch_r224_continuous_base_20260918/player')
def sha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def proc(pid):
 path=pathlib.Path('/proc')/str(pid)/'stat'
 return path.exists() and path.read_text().rsplit(')',1)[1].split()[0]!='Z'
state=json.loads((player/'private/state.json').read_bytes())
active=json.loads((root/'ACTIVE.json').read_bytes())
receipts=[json.loads(path.read_bytes()) for path in (root/'receipts').glob('*.json')]
guides={row['guidance_sha256']:row for row in receipts}
tokenizer=Tokenizer.from_file('/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28/tokenizer.json')
guide_tokens={key:len(tokenizer.encode(row['guidance'],add_special_tokens=False).ids) for key,row in guides.items()}
rendered=[]
for entry in state.get('generations',[]):
 if entry['finished_unix']<active['unix']:continue
 path=player/'private/generations'/(entry['request_id']+'.json')
 value=json.loads(path.read_bytes());request=value['request'];generated=value['generated']
 assert sha(request)==entry['request_id'] and generated['messages']==request['messages']
 contents=[message['content'] for message in request['messages']]
 occurrences={key:sum(content.count(row['guidance']) for content in contents) for key,row in guides.items()}
 matched=[key for key,count in occurrences.items() if count]
 if matched:
  rendered.append(dict(request_id=entry['request_id'],request_sha256=sha(request),response_sha256=sha(generated),
   generation_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),stage=request['stage'],
   opportunity=request['opportunity'],finished_unix=value['finished_unix'],guidance_sha256=matched,
   actual_generated_tokens=len(generated['token_ids']),actual_prompt_tokens=generated['prompt_tokens'],
   rendered_guidance_span_tokens=sum(guide_tokens[key]*occurrences[key] for key in matched)))
rendered.sort(key=lambda row:row['finished_unix'])
phase_counts={name:dict(ACT_attempts=0,parsed=0,scored=0,accepted=0,new_pixels=0,cached=0,faults=0) for name in ['historical_unparented','R233_parented']}
for event in state['events']:
 treated=bool(rendered) and event['finished_unix']>rendered[0]['finished_unix']
 totals=phase_counts['R233_parented' if treated else 'historical_unparented']
 totals['ACT_attempts']+=1
 for key,field in [('parsed','parsed'),('scored','scored'),('accepted','accepted'),('new_pixels','novel'),('cached','cached'),('faults','fault')]:
  totals[key]+=int(event.get(field,0) or 0)
now=time.time()
first_unix=min(row['finished_unix'] for row in state['generations'])
hourly=[]
for start in range(int(first_unix//3600)*3600,int(now//3600)*3600+1,3600):
 end=min(start+3600,now)
 selected=[row for row in state['events'] if start<=row['finished_unix']<end]
 generations=[row for row in state['generations'] if start<=row['finished_unix']<end]
 tokens={stage:sum(row['generated_tokens'] for row in generations if row['stage']==stage) for stage in ['THINK','ACT','LEARN']}
 per_phase={phase:dict(ACT_attempts=0,scored=0,accepted=0,new_pixels=0) for phase in ['historical_unparented','R233_parented']}
 for row in selected:
  phase='R233_parented' if rendered and row['finished_unix']>rendered[0]['finished_unix'] else 'historical_unparented'
  per_phase[phase]['ACT_attempts']+=1
  for key,field in [('scored','scored'),('accepted','accepted'),('new_pixels','novel')]:per_phase[phase][key]+=int(row.get(field,0) or 0)
 hourly.append(dict(start_unix=start,end_unix=end,partial=end<start+3600 or first_unix>start,
  ACT_attempts=len(selected),parsed=sum(row['parsed'] for row in selected),
  scored=sum(row['scored'] for row in selected),accepted=sum(row['accepted'] for row in selected),
  new_pixels=sum(row['novel'] for row in selected),cached=sum(row['cached'] for row in selected),
  faults=sum(bool(row['fault']) for row in selected),planned_unknown=sum(row.get('planned') is None for row in selected),
  no_caption_ACTs=sum(row.get('no_caption_act') is True for row in selected),
  routing_ambiguity_ACTs=sum(row.get('routing_ambiguity') is True for row in selected),
  generation_count=len(generations),child_generated_tokens=sum(tokens.values()),tokens_by_stage=tokens,
  acceptance_per_new_score=(sum(row['accepted'] for row in selected)/sum(row['scored'] for row in selected)) if sum(row['scored'] for row in selected) else None,
  treatment_breakdown=per_phase))
token_sum=sum(row['generated_tokens'] for row in state['generations'])
result=dict(schema='R233_PARENT_RENDER_EVIDENCE_V1',unix=time.time(),epoch='R233_PARENT_v1',
 bridge_pid=active['pid'],bridge_live=proc(active['pid']),player_pid=162813,player_live=proc(162813),
 scorer_pid=162806,scorer_live=proc(162806),source_process_signals=[],guidance_deliveries=len(receipts),
 bridge_errors=len(list((root/'errors').glob('*.json'))),
 first_actual_parented_generation=rendered[0] if rendered else None,rendered_generations=rendered,
 treatment_boundary='first request_id with actual completed generation containing exact guidance; finished_unix is completion not start',
 completed_opportunities=state['completed_opportunities'],cumulative_child_tokens=state['total_generated_tokens'],
 parent_tokens=None,parent_tokens_status='guidance_spans_measured_below_not_full_chat_wrapper_overhead',model_updates=0,
 distinct_guidance_texts=len(guides),delivered_guidance_text_tokens=sum(guide_tokens[row['guidance_sha256']] for row in receipts),
 rendered_guidance_span_tokens=sum(row['rendered_guidance_span_tokens'] for row in rendered),
 guidance_tokenizer_backend_sha256=hashlib.sha256(tokenizer.to_str().encode()).hexdigest(),
 phase_counts=phase_counts,raw_counts_not_literal_humor_review=True,hourly_rows=hourly,
 token_accounting=dict(retained_generation_tokens=token_sum,controller_total_tokens=state['total_generated_tokens'],
  exact_retained_coverage=token_sum==state['total_generated_tokens'],counts_as_of_finished_generation=True),
 hourly_definition='UTC half-open windows; ACT attempts by completed feedback event; all child tokens by completed generation; partial windows explicit; not an hourly rate',
 planned_unknown_definition='declared output cardinality absent, not unknown judge score',
 no_matched_adapter_scaffold_claim=True,parent_free_age_probes_unchanged=True)
print(json.dumps(result))
'''


def main():
    result = subprocess.run(['bash', 'gpu/ovx4_ssh.sh', '/localhome/local-rohing/v2/venv/bin/python -B -'], input=CODE,
        text=True, capture_output=True, timeout=40)
    if result.returncode:
        raise RuntimeError(result.stderr[-1000:])
    receipt = json.loads(result.stdout)
    root = Path(__file__).resolve().parent
    (root / 'PARENT_RENDER_LATEST.json').write_text(json.dumps(receipt, indent=2) + '\n')
    lines = ['# Continuous frozen-base hourly ACT and token receipt', '',
        'Observed UTC: ' + datetime.fromtimestamp(receipt['unix'], timezone.utc).isoformat(), '',
        'Existing read-only receipt only; no new hourly daemon. ACT means completed-feedback attempt. '
        'Tokens count all completed child generations, charged on completion. Partial windows are not hourly rates.', '',
        '| UTC window | ACT attempts | Scored strings | Raw accepted | New pixels | Faults | THINK tokens | ACT tokens | Total tokens |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for row in receipt['hourly_rows']:
        start = datetime.fromtimestamp(row['start_unix'], timezone.utc).strftime('%H:%M:%S')
        end = datetime.fromtimestamp(row['end_unix'], timezone.utc).strftime('%H:%M:%S')
        label = start + '–' + end + (' partial' if row['partial'] else '')
        lines.append(f"| {label} | {row['ACT_attempts']} | {row['scored']} | {row['accepted']} | {row['new_pixels']} | "
            f"{row['faults']} | {row['tokens_by_stage']['THINK']} | {row['tokens_by_stage']['ACT']} | {row['child_generated_tokens']} |")
    lines += ['', 'Retained token reconciliation: ' + json.dumps(receipt['token_accounting'], sort_keys=True), '',
        '10–11UTC is verified inactivity during the known stopped epoch, not missing collection. '
        '11–12UTC includes both the real gap before11:25 continuation and the R233 policy change; not a full active hour or single treatment.',
        'R233 first actual guidance-bearing THINK completed11:51:03.269701UTC; exact request3756bc63… is the boundary. '
        'Treatment-separated counts are in PARENT_RENDER_LATEST.json / phase_counts and hourly_rows / treatment_breakdown.',
        'Accepted strings are not certified literal jokes or novel ideas; repetitions and parser commentary may remain. '
        'No historical rescore. planned_unknown means missing declared cardinality, not unknown score. '
        'Guidance-span tokens are separately measured and unmatched; wrappers are not included. Main owns aggregate/hourly publication.']
    (root / 'BASE_HOURLY.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({key: value for key, value in receipt.items() if key not in ('rendered_generations', 'hourly_rows')}))


if __name__ == '__main__':
    main()

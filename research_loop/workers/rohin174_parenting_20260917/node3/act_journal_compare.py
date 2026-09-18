"""Bounded read-only ACT journal audit; never dispatch or execute learner code."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

import takeover as base


PARSER_SHA = 'a7bd5a92be9937845f3653687af710a9a26d0276c3317e7c5c4c291ad117bdf1'
OUTPUT = base.HERE / 'r194_act_comparison'
SPECS = {
    'copies': dict(wrapper='gpu/ovx_ssh.sh', host='[REDACTED_HOST]', lives=[
        dict(label='explicit1', root='/localhome/local-rohing/orch_r153_r184_node2_20260917/explicit1/raw',
             source='/localhome/local-rohing/orch_r153_r184_node2_20260917/explicit1/source', cutoff=5520),
        dict(label='brief1', root='/localhome/local-rohing/orch_r153_r184_node2_20260917/brief1/raw',
             source='/localhome/local-rohing/orch_r153_r184_node2_20260917/brief1/source', cutoff=5520)]),
    'original': dict(wrapper='gpu/ovx3_ssh.sh', host='[REDACTED_HOST]', lives=[
        dict(label='original_C2', root='/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life',
             source='/localhome/local-rohing/orch_r153_r193_C2_20260917_recovery1/source', cutoff=5751)])}

REMOTE = r'''
import ast,hashlib,io,json,re,socket,string,sys,time,tokenize,unicodedata
from pathlib import Path
assert socket.gethostname()==spec['host']
began=time.monotonic(); bytes_read=0
def raw(path):
 global bytes_read
 assert path.is_file() and not path.is_symlink()
 size=path.stat().st_size
 assert size<=16*1024*1024 and bytes_read+size<=64*1024*1024
 assert time.monotonic()-began<60
 result=path.read_bytes();bytes_read+=len(result)
 return result
def digest(document):
 return hashlib.sha256(json.dumps(document,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def record(path):
 data=raw(path);document=json.loads(data)
 assert document['sha256']==digest({key:value for key,value in document.items() if key!='sha256'})
 return document,dict(path=str(path),file_sha256=hashlib.sha256(data).hexdigest(),record_sha256=document['sha256'],index=document['index'],kind=document['kind'],mtime_unix=path.stat().st_mtime)
def metadata(path):
 global bytes_read
 with path.open('rb') as stream:
  stream.seek(max(0,path.stat().st_size-4096));data=stream.read(4096)
 bytes_read+=len(data)
 assert bytes_read<=64*1024*1024 and time.monotonic()-began<60
 offset=data.rfind(b',"index":');assert offset>=0
 return json.loads(b'{'+data[offset+1:])
def syntax(source):
 if source is None:return dict(status='NO_EXECUTABLE_SOURCE')
 try:
  tree=ast.parse(source)
  bare=[dict(line=node.lineno,name=node.value.id) for node in tree.body if isinstance(node,ast.Expr) and isinstance(node.value,ast.Name)]
  return dict(status='PARSES',bare_name_statements=bare)
 except SyntaxError as error:
  return dict(status='SYNTAX_ERROR',message=error.msg,line=error.lineno,column=error.offset,text=(error.text or '').strip()[:300])
output=dict(observed_unix=time.time(),host=socket.gethostname(),static_python=sys.version,code_executions=0,signals=0,publications=0,live_changes=0,lives=[])
for item in spec['lives']:
 root=Path(item['root']); source=Path(item['source']);records=root/'stream/records'
 parser_path=source/'gpu/orch_r153_code_blocks.py';parser=raw(parser_path)
 assert hashlib.sha256(parser).hexdigest()==parser_sha
 namespace={'__name__':'verified_pure_code_block_parser'}
 exec(compile(parser,str(parser_path),'exec'),namespace)
 paths=[records/('%020d.json'%index) for index in range(5129,item['cutoff']+1)]
 assert len(paths)<=1600 and all(path.exists() for path in paths)
 catalog=[metadata(path) for path in paths]
 selected={};refs={}
 for path,meta in zip(paths,catalog):
  if meta['kind'] in ('LOADED','R184_STAGE','R184_ACT','R184_SLEEP_NOTICE','SLEEP_COMPLETE','TERMINAL','WALL_EXTENDED'):
   entry,reference=record(path);selected[entry['index']]=entry;refs[entry['index']]=reference
 notices=[(index,entry['document']['cycle']) for index,entry in selected.items() if entry['kind']=='R184_SLEEP_NOTICE']
 completed=[(index,entry['document']['cycle']) for index,entry in selected.items() if entry['kind']=='SLEEP_COMPLETE']
 stages=[entry for entry in selected.values() if entry['kind']=='R184_STAGE' and entry['document']['stage']=='ACT']
 outcomes=[entry for entry in selected.values() if entry['kind']=='R184_ACT']
 life=dict(**item,parser_sha256=parser_sha,head=metadata(paths[-1]),start_record=5129,
     source_pins={name:hashlib.sha256(raw(source/name)).hexdigest() for name in ('gpu/orch_r184_think_act_learn.py','gpu/orch_r153_community_transport.py')},
     source_pin_scope='current source only; historical origin bound separately by RESPONSE/R184_STAGE/R184_ACT hashes',
     loaded=[dict(refs[entry['index']],document=entry['document']) for entry in selected.values() if entry['kind']=='LOADED'],
     completed_cycles=[cycle for index,cycle in completed],acts=[])
 for stage in stages:
  stage_index=stage['index'];stage_doc=stage['document']
  candidates=[entry for entry in outcomes if entry['document']['segment']==stage_doc['segment'] and entry['index']>stage_index]
  outcome_entry=min(candidates,key=lambda entry:entry['index']) if candidates else None
  outcome=outcome_entry['document']['outcome'] if outcome_entry else dict(status='ACT_STAGE_WITHOUT_OUTCOME',executed=None)
  response_index=outcome_entry['document']['origin']['record_index'] if outcome_entry else stage_index-2
  response,response_ref=record(records/('%020d.json'%response_index));assert response['kind']=='RESPONSE'
  if outcome_entry:assert response['sha256']==outcome_entry['document']['origin']['record_sha256']
  document=response['document']['response'];text=document['raw'];report=namespace['extract'](text)
  raw_code=report.get('raw_source');normalized=report.get('source')
  assert raw_code is None or len(raw_code.encode())<=128*1024
  transformations=report.get('transformations',[]);fullwidth=[]
  for change in transformations:
   if 0xff01<=ord(change['original'])<=0xff65:
    before=raw_code[:change['offset']];line=before.count('\n')+1
    fullwidth.append(dict(change,line=line,column=len(before.rsplit('\n',1)[-1])+1,codepoint='U+%04X'%ord(change['original']),line_text=raw_code.splitlines()[line-1][:200]))
  dot_assignments=[dict(line=position+1,text=line[:240]) for position,line in enumerate((normalized or raw_code or '').splitlines()) if re.match(r'^\s*\.\s*[A-Za-z_]\w*\s*=',line)]
  next_notice=next(((index,cycle) for index,cycle in notices if index>stage_index),None)
  prior_complete=max([(index,cycle) for index,cycle in completed if index<stage_index],default=(5128,41))
  cycle=next_notice[1] if next_notice else prior_complete[1]+1
  row=dict(cycle=cycle,cycle_basis='following_R184_SLEEP_NOTICE' if next_notice else 'preceding_COMPLETE_plus_one_pending',
      trial_id=stage_doc.get('trial_id'),stage=refs[stage_index],response=response_ref,
      segment=stage_doc['segment'],raw_text_sha256=hashlib.sha256(text.encode()).hexdigest(),truncated=document.get('truncated'),
      generation_metadata={key:document[key] for key in ('terminal','finish_reason','stop_reason','token_count') if key in document},
      extraction={key:value for key,value in report.items() if key not in ('source','raw_source')},raw_code=raw_code,execution_source=normalized,
      raw_syntax=syntax(raw_code),execution_syntax=syntax(normalized),fullwidth_syntactic_candidates=fullwidth,
      leading_dot_assignments=dot_assignments,outcome={key:value for key,value in outcome.items() if key not in ('result',)},
      outcome_record=refs[outcome_entry['index']] if outcome_entry else None)
  if raw_code is None:row['raw_excerpt']=text[:240]+'\n[...bounded...]\n'+text[-360:]
  publication=outcome.get('publication')
  if publication:
   inbox_path=root/'stream/inbox'/(publication['id']+'.json');inbox_raw=raw(inbox_path)
   assert hashlib.sha256(inbox_raw).hexdigest()==publication['sha256']
   inbox=json.loads(inbox_raw);assert inbox['speaker']=='Tool' and inbox['split']=='TRAIN'
   result_path=root/'community_cpu/spool'/outcome['request_id']/'RESULT.json';result_raw=raw(result_path)
   assert hashlib.sha256(result_raw).hexdigest()==outcome['result_sha256']==inbox['source_receipt']['sha256']
   result=json.loads(result_raw)
   row['tool_receipt']=dict(path=str(result_path),sha256=hashlib.sha256(result_raw).hexdigest(),
       fields={key:result[key] for key in ('status','returncode','exit_code','launch_attempted','execution_attempted','started_unix','finished_unix','source_sha256') if key in result},
       result_keys=sorted(result),feedback_excerpt=inbox['text'][:3000])
  life['acts'].append(row)
 life['outcome_count']=len(outcomes);life['act_stage_count']=len(stages)
 assert len(outcomes)<=len(stages)
 life['generation_truncation_unknown_count']=sum(row['truncated'] is None for row in life['acts'])
 output['lives'].append(life)
output['bytes_read']=bytes_read;output['elapsed_seconds']=time.monotonic()-began
print(json.dumps(output,ensure_ascii=False))
'''


def collect(group):
    spec = SPECS[group]
    script = 'spec=' + repr(spec) + '\nparser_sha=' + repr(PARSER_SHA) + '\n' + REMOTE
    result = subprocess.run(['bash', str(base.REPO / spec['wrapper']), 'python3 -B -'],
        input=script, text=True, capture_output=True, timeout=80)
    base.require(result.returncode == 0, 'readonly_ACT_audit:' + result.stderr[-800:])
    document = json.loads(result.stdout)
    document['collector'] = base.reference(__file__)
    path = OUTPUT / (group + '_' + str(time.time_ns()) + '.json')
    base.write(path, document)
    print(json.dumps(dict(receipt=base.reference(path),bytes_read=document['bytes_read'],
        rows=[dict(label=life['label'],acts=life['act_stage_count'],cycles=[row['cycle'] for row in life['acts']]) for life in document['lives']])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('group', choices=tuple(SPECS))
    collect(parser.parse_args().group)

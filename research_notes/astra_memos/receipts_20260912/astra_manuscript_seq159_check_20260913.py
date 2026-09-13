"""Read-only source/manuscript checks; writes fresh /tmp evidence only."""
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

BASE=Path('/tmp/astra_manuscript_seq159_baseline_20260913.json')
RECEIPTS=Path('research_notes/astra_memos/receipts_20260912')
snapshot=json.loads(BASE.read_text())
checks=[]


def verify(condition, message):
    assert condition,message
    checks.append(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def create(path, text):
    assert not path.exists(),str(path)
    patch='*** Begin Patch\n*** Add File: '+str(path)+'\n'
    patch+=''.join('+'+line+'\n' for line in text.splitlines())+'*** End Patch\n'
    subprocess.run(['apply_patch'],input=patch,text=True,check=True)


pins={
 'astra_own_replay_repair_analysis_result_20260913_attempt1/analysis.json':'03ac63e35c3e912533b62474ba4590dee21bbac02ca790511491d3305022bc6a',
 'astra_own_replay_repair_analysis_result_20260913_attempt1/analysis.md':'2dcd00d35aef27ca9a3c97883c0324b97c732d58858043870fdd32eb76c884a6',
 'astra_own_replay_repair_analysis_execution_20260913_attempt1.md':'6614a09dd98f501c3f8f93e141a74a7a1ee166378b8c00f149fb65cb4645fa6e',
 'astra_own_replay_repair_analysis_20260913.py':'ba039742485f8292e7caf9d728f0b5c9b1c3a0ca03a52ff39b8d4b14814a84cb',
 'astra_own_replay_repair_analysis_20260913_orderfix.py':'4c06d8ded8ab58814a94f0aab40780a54fa2cf76ca0c7d858d1ab639483b03ab',
 'test_astra_own_replay_repair_analysis_20260913_orderfix.py':'2aef15b05fdcb434640dd3f6ef12318308451873c8ef36c4f7cbb0b4b2f315f2',
 'astra_own_source_capture_audit_20260913.json':'38435b38985f8b2b40bf8e0a7c183f6be76bbbf318ffcfc7d14baa7a1f7f6621',
}
for name,expected in pins.items():verify(digest(RECEIPTS/name)==expected,'source pin '+name)
original=(RECEIPTS/'astra_own_replay_repair_analysis_20260913.py').read_text()
fixed=(RECEIPTS/'astra_own_replay_repair_analysis_20260913_orderfix.py').read_text()
verify(original.count('for checksum, raw in candidates.items():')==1,'one ordering site')
verify(original.replace('for checksum, raw in candidates.items():','for checksum, raw in sorted(candidates.items()):')==fixed,'exact ordering-only source change; not executed')
result=json.loads((RECEIPTS/'astra_own_replay_repair_analysis_result_20260913_attempt1/analysis.json').read_text())
capture=json.loads((RECEIPTS/'astra_own_source_capture_audit_20260913.json').read_text())
verify(capture['unique_sources_across_seeds']==capture['unique_raw_targets_across_seeds']==24,'24shared capture sources/targets')
verify(result['totals']=={'calls':480,'fits':6,'updates':1632},'SEQ159 incremental costs')
verify(result['all_three_pairs_available'] is True and result['automatic_pass'] is False,'complete roster without automatic promotion')
rows=[];paired=[];training=[]
for seed in result['seeds']:
    index=seed['seed']; denominator=[14,8,8][index]
    verify(seed['counts']=={'memory':denominator,'replay':24,'rows_per_arm':denominator+24},'seed source denominators '+str(index))
    for variant in ('exact','paraphrase'):
        verify(seed['best_constant']['variants'][variant]['oracle_best_content_correct']==[6,4,4][index],'constant diagnostic '+str(index)+variant)
    for arm in ('REPLAY','EXTRA_MEMORY'):
        entry=seed['arms'][arm]; panels=entry['panels']; screen=entry['screen']; dose=entry['training']
        exact=panels['exact']['totals']; paraphrase=panels['paraphrase']['totals']; held=panels['held']['totals']
        losses=len(screen['lr0_correct_regressions']['held'])
        rows.append([index,arm,exact['production_eligible'],paraphrase['production_eligible'],denominator,held['content_correct'],losses,screen['passed']])
        verify(exact['content_correct']==exact['production_eligible'] and paraphrase['content_correct']==paraphrase['production_eligible'],'source-faithful metric '+str(index)+arm)
        verify(held['content_correct']==held['strict'] and panels['canary']['totals']['content_correct']==panels['canary']['totals']['strict']==12,'held/canary policy '+str(index)+arm)
        verify(screen['threshold']==[8,7,5][index] and not screen['lr0_correct_regressions']['canary'],'frozen exact floor/canary loss '+str(index)+arm)
        verify(dose['updates']==[304,256,256][index],'matched updates '+str(index)+arm)
        memory=dose['per_kind']['memory']['presentations']+dose['per_kind']['extra_memory']['presentations']
        replay=dose['per_kind']['observation_replay']['presentations']
        verify(memory==([112,64,64][index] if arm=='REPLAY' else [304,256,256][index]) and replay==(192 if arm=='REPLAY' else 0),'unequal memory exposure '+str(index)+arm)
        training.append({'seed':index,'arm':arm,'memory_presentations':memory,'observation_presentations':replay,'supervised':dose['actual_supervised_tokens'],'context':dose['actual_context_tokens']})
    for panel in ('exact','paraphrase','held'):
        counts=seed['paired_replay_minus_extra'][panel]['content_correct']['counts']
        paired.append([index,panel,counts['first_only'],counts['second_only']])
verify(rows==[[0,'REPLAY',10,10,14,47,0,True],[0,'EXTRA_MEMORY',13,10,14,47,0,True],[1,'REPLAY',6,6,8,48,0,False],[1,'EXTRA_MEMORY',7,6,8,46,2,False],[2,'REPLAY',5,3,8,48,0,True],[2,'EXTRA_MEMORY',7,7,8,42,6,False]],'all six table rows')
verify(paired==[[0,'exact',1,4],[0,'paraphrase',0,0],[0,'held',0,0],[1,'exact',0,1],[1,'paraphrase',0,0],[1,'held',2,0],[2,'exact',0,2],[2,'paraphrase',0,4],[2,'held',6,0]],'paired wins/losses')
verify(sum(row['supervised'] for row in training)==46728 and sum(row['context'] for row in training)==334800,'training token totals')

files={};diffs=[]
for name,baseline in snapshot['files'].items():
    path=Path(name);text=path.read_text();original=baseline['text']
    diff=list(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
    diffs.extend(diff)
    additions=[line[1:].rstrip('\n') for line in diff if line.startswith('+') and not line.startswith('+++')]
    verify(all(line==line.rstrip() for line in additions),'added whitespace '+name)
    verify('Current evidence through SEQ159' in text or 'Current evidence through SEQ-159' in text,'current159cut '+name)
    added='\n'.join(additions)
    for phrase in ('C11 remains deferred','raw-chronological LoRA','CPU','UNSENT'):
        verify(phrase in added,'new boundary '+name+':'+phrase)
    verify('C95' in added and '2/3' in added and '1/3' in added,'new claim/screen contrast '+name)
    entry={'sha256':digest(path),'baseline_sha256':baseline['sha256'],'added_lines':len(additions),'removed_lines':sum(line.startswith('-') and not line.startswith('---') for line in diff)}
    if path.suffix=='.tex':
        pattern=r'\\begin\{tabular\}.*?\\end\{tabular\}'
        before=Counter(re.findall(pattern,original,re.S));after=Counter(re.findall(pattern,text,re.S))
        verify(not before-after and sum(after.values())==sum(before.values())+1,'all prior tabular blocks preserved, one new '+name)
        entry['historical_tabular_blocks_preserved']=sum(before.values())
        citation=r'\\cite\w*\*?(?:\[[^\]]*\])*\{[^}]*\}'
        verify(Counter(re.findall(citation,text))==Counter(re.findall(citation,original)),'literature citations unchanged '+name)
        labels=re.findall(r'\\label\{([^}]+)\}',text)
        verify(len(labels)==len(set(labels)) and 'sec:seq159-replay' in labels and 'tab:seq159-replay' in labels,'unique/new labels '+name)
        verify('EXTRA_MEMORY' not in added,'new TeX underscore escaping '+name)
        stripped=re.sub(r'(?<!\\)%[^\n]*','',text);stack=[];depth=0
        for match in re.finditer(r'\\(begin|end)\{([^}]+)\}',stripped):
            action,environment=match.groups()
            if action=='begin':stack.append(environment)
            else:assert stack and stack.pop()==environment,(name,environment)
        verify(not stack,'TeX environment balance '+name)
        for position,character in enumerate(stripped):
            if character not in '{}':continue
            preceding=position-1;escapes=0
            while preceding>=0 and stripped[preceding]=='\\':escapes+=1;preceding-=1
            if escapes%2:continue
            depth+=1 if character=='{' else -1
            assert depth>=0,name
        verify(depth==0,'TeX brace balance '+name)
    else:
        link=r'\[[^\]]+\]\(([^)]+)\)'
        new_links=Counter(re.findall(link,text))-Counter(re.findall(link,original))
        for target in new_links:
            if '://' not in target:verify((path.parent/target.split('#')[0]).exists(),'new local link '+name+':'+target)
    if path.name!='astra_sprint_abstract_20260912.md':
        for seed,arm,exact,paraphrase,denominator,held,losses,screen in rows:
            label='Meets' if screen else 'Misses recall' if arm=='REPLAY' else 'Fails retention'
            if path.suffix=='.tex':
                arm_text=arm.replace('_',r'\_')
                expected=f'{seed} & {arm_text} & {exact}/{denominator} & {paraphrase}/{denominator} & {held} & {losses} & {label}'
            else:expected=f'| {seed} | {arm} | {exact}/{denominator} | {paraphrase}/{denominator} | {held} | {losses} | {label} |'
            verify(expected in text,'source-derived manuscript table row '+name+':'+str(seed)+arm)
    files[name]=entry
verify(digest('gpu/codex/dream_state.rules')==snapshot['rules_sha256'],'unrelated rules unchanged')
record={'status':'PASS_BOUNDED_MANUSCRIPT_CHECKS_NOT_SCIENTIFIC_APPROVAL','scope':'SEQ159 only; no alignment outcomes read',
        'baseline':str(BASE),'files':files,'source_pins':{str(RECEIPTS/name):value for name,value in pins.items()},
        'six_rows':rows,'paired':paired,'training':training,'checks':checks,'check_count':len(checks),
        'rules_sha256':snapshot['rules_sha256'],'checker_sha256':digest(__file__),
        'command':'python3 -B /tmp/astra_manuscript_seq159_check_20260913.py',
        'tex_tools':{name:shutil.which(name) for name in ('pdflatex','latexmk','tectonic')},
        'limitations':['No Git/native/network/GPU/collector/scorer execution; original code read only.',
                       'Main16testsPASS3.095s reported from notebook; not rerun here.',
                       'No PDF build, layout validation or new literature review.',
                       'Three learner pairs; exposed DEV; historical controls noncontemporaneous.',
                       'Next alignment status from assignment only; no alignment outcomes inspected.']}
create(Path('/tmp/astra_manuscript_seq159_validation_20260913.json'),json.dumps(record,indent=2)+'\n')
create(Path('/tmp/astra_manuscript_seq159_diff_20260913.patch'),''.join(diffs))
print(record['status'],len(checks),'checks')
for name,entry in files.items():print(entry['sha256'],name)

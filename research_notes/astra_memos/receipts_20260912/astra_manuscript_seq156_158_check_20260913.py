"""Local manuscript/source checks only; no original runner/scorer execution."""
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

BASE = Path('/tmp/astra_manuscript_seq156_158_baseline_20260913.json')
RECEIPTS = Path('research_notes/astra_memos/receipts_20260912')
snapshot = json.loads(BASE.read_text())
checks = []


def check(condition, message):
    assert condition, message
    checks.append(message)


def checksum(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def add_file(path, body):
    check(not path.exists(), 'exclusive output ' + str(path))
    patch = '*** Begin Patch\n*** Add File: ' + str(path) + '\n'
    patch += ''.join('+' + line + '\n' for line in body.splitlines()) + '*** End Patch\n'
    subprocess.run(['apply_patch'], input=patch, text=True, check=True)


source_pins = {
    'astra_contrastive_full_dose_analysis_20260913_results.json': '204fcb1e40041e3057d1fdd9300b924d6d1a9aa94b80d2a513f07b428f500c60',
    'astra_contrastive_full_dose_analysis_20260913_results_handoff.md': 'e1bf5b55911c65da56ef75fef074e34d988ef3808320f8dbdfcadb7957625b6b',
    'astra_own_source_capture_audit_20260913.json': '38435b38985f8b2b40bf8e0a7c183f6be76bbbf318ffcfc7d14baa7a1f7f6621',
    'astra_own_source_capture_audit_20260913.md': '93542f4eb200e579626ab4bc9b4ada9cbbdfc591d5d7e5a7ce973adb069acdf5',
    'astra_parented_record_analysis_result_20260913_attempt1/analysis.json': '2b87fd61fd196b82692f6c580bf8824e50a0b4c52f4f3e5f11790d9ad890a9ed',
    'astra_parented_record_analysis_result_20260913_attempt1/analysis.md': 'b384d671cace74ea48e210e33b3d29d0f80c825690e7566a31293fb75e74c836',
    'astra_parented_record_analysis_inputs_20260913_attempt1.json': 'df245557fc9c11f1ddc6bf08506e53b77ff189a8f0414658ef5e2e5a87c76edd',
    'astra_parented_retention_rescore_20260913_results.json': 'f217f480f9a42f983fde87f381f497bd63d811ff4baf909b46a57764dbec4d30',
    'astra_parented_retention_rescore_20260913_handoff.md': '206398326448eee0c4cc525962a9e1da70b0eec3e077276bbcbe990c1969a909',
    'astra_coaching_runtime_profile_20260913.json': '94b7c019263f053d53cf5dbb0bdef84338adb3e16bb46e43f158d37452294630',
}
for name, expected in source_pins.items():
    check(checksum(RECEIPTS / name) == expected, 'source pin ' + name)

contrast = json.loads((RECEIPTS / 'astra_contrastive_full_dose_analysis_20260913_results.json').read_text())
capture = json.loads((RECEIPTS / 'astra_own_source_capture_audit_20260913.json').read_text())
cohort = json.loads((RECEIPTS / 'astra_parented_record_analysis_result_20260913_attempt1/analysis.json').read_text())
retention = json.loads((RECEIPTS / 'astra_parented_retention_rescore_20260913_results.json').read_text())
contrast_rows, cohort_rows = [], []
for seed in contrast['seeds']:
    plain, treatment = seed['states']['plain'], seed['states']['contrastive']
    paired = seed['paired']['contrastive_minus_plain']['held']['content']['counts']
    row = [seed['seed'], plain['held']['content'], treatment['held']['content'],
           treatment['held']['content'] - plain['held']['content'],
           treatment['panels']['D1']['content'], treatment['panels']['D2']['content'],
           paired['wins'], paired['losses'], plain['panels']['C-record']['content'], treatment['panels']['C-record']['content']]
    contrast_rows.append(row)
    for state in (plain, treatment):
        check(state['held']['content'] == state['held']['strict'] == sum(state['panels'][panel]['exact_target_bytes'] for panel in ('D1', 'D2')), 'C92 content/strict/bytes seed ' + str(seed['seed']))
check(contrast_rows == [[0,17,19,2,11,8,2,0,6,11], [1,14,20,6,12,8,6,0,7,11], [2,19,19,0,11,8,1,1,7,11]], 'C92 all table numerators/paired counts')
check(contrast['roster']['original_screen_by_seed'] == [False]*3, 'C92 all frozen screens fail')
check(contrast['total_new_cost'] == {'calls':288,'fits':6,'presentations':8064,'updates':2016}, 'C92 cost')
check(capture['unique_sources_across_seeds'] == capture['unique_raw_targets_across_seeds'] == 24, 'C93 shared24not72')
check(capture['costs']['calls'] == 72 and capture['costs']['fits'] == capture['costs']['updates'] == 0, 'C93 no-fit capture')
for seed in capture['seeds']:
    check([seed[key] for key in ('independent_passes','requested','source_supported','source_population')] == [24,24,48,96], 'C93 denominators seed ' + str(seed['seed']))
    check(set(seed['field_correct'].values()) == {24}, 'C93 all four fields seed ' + str(seed['seed']))
for seed in cohort['seeds']:
    parented, neutral = seed['arms']['P'], seed['arms']['N']
    summaries = seed['summaries']
    row = [seed['seed'], parented['source_counts']['admitted_rows'], neutral['source_counts']['admitted_rows'],
           parented['dose']['updates'], neutral['dose']['updates'],
           *[summaries[arm+'_held']['production_eligible'] for arm in ('P','N','ORIGINAL')],
           parented['retention']['held']['metrics']['content_correct']['current'],
           neutral['retention']['held']['metrics']['content_correct']['current'],
           parented['retention']['held']['metrics']['content_correct']['original'],
           len(parented['retention']['held']['metrics']['content_correct']['losses']),
           len(neutral['retention']['held']['metrics']['content_correct']['losses'])]
    cohort_rows.append(row)
    check(seed['held_P_minus_N_over16'] == 0, 'C94 zero held contrast seed ' + str(seed['seed']))
    check([summaries[arm+'_held']['strict_canonical'] for arm in ('P','N','ORIGINAL')] == ([4,0,11] if seed['seed']==0 else [0,0,0]), 'C94 fresh canonical policy seed ' + str(seed['seed']))
    for arm in ('P','N','ORIGINAL'):
        check(summaries[arm+'_held']['executions'] == 16, 'C94 held executions ' + str(seed['seed']) + arm)
    for arm in ('P','N'):
        check(seed['arms'][arm]['retention']['canary']['metrics']['content_correct']['current'] == 12, 'C94 canaries ' + str(seed['seed']) + arm)
check(cohort_rows == [[0,16,14,128,112,16,16,11,47,47,47,0,0], [1,16,11,128,88,16,16,8,47,47,48,1,1], [2,11,13,88,104,13,13,8,44,46,48,4,2]], 'C94 all table numerators/doses/itemwise losses')
check({key:sum(seed['totals'][key] for seed in cohort['seeds']) for key in ('calls','fits','updates')} == {'calls':900,'fits':6,'updates':648}, 'C94 cost')
for stage in ('P_formation','P_held','N_held'):
    failures=[row for row in cohort['seeds'][2]['rows'][stage] if not row['score']['production_eligible']]
    check(len(failures)==(5 if stage=='P_formation' else 3), 'C94 seed2 failure count ' + stage)
    check(all('try' not in json.loads(row['record_raw']) and 'unavailable' in json.loads(row['record_raw']) for row in failures), 'C94 missing key rather than copied wrong triple ' + stage)
check(retention['item_count']==360 and retention['readout_count']==6 and retention['all_scores_equal'] is True and retention['discrepancy_count']==0 and retention['discrepancies']==[], 'C94 exact frozen360rescore closure')

files, patch_chunks = {}, []
for name, baseline in snapshot['files'].items():
    path=Path(name); text=path.read_text(); original=baseline['text']
    diff=list(difflib.unified_diff(original.splitlines(True), text.splitlines(True), fromfile='a/'+name, tofile='b/'+name))
    patch_chunks.extend(diff)
    added=[line[1:] for line in diff if line.startswith('+') and not line.startswith('+++')]
    check(all(line.rstrip('\n').rstrip()==line.rstrip('\n') for line in added), 'added whitespace ' + name)
    check('Current evidence through SEQ158' in text or 'Current evidence through SEQ-158' in text, 'current cut ' + name)
    check('raw-chronological LoRA' in text and 'compiler utility' in text or 'extraction/compiler' in text, 'compiler attribution bound ' + name)
    check('rescore pending' not in text and 'incorporation remains pending' not in text and 'rescore incorporation is pending' not in text, 'rescore stale status removed ' + name)
    check('repair remains CPU-only' not in text and 'repair is predeclared CPU development only' not in text, 'repair launch status updated ' + name)
    check('UNSENT' in text, 'collaborator status ' + name)
    if '1127.793/1087.217/1063.341' in text:
        check('1127.793/1087.217/1063.341s controller' not in text and
              'not postlaunch controller runtime' in text, 'preparation-inclusive budget clock label ' + name)
    entry={'baseline_sha256':baseline['sha256'],'sha256':checksum(path),'added_lines':len(added),
           'removed_lines':sum(line.startswith('-') and not line.startswith('---') for line in diff)}
    if path.suffix=='.tex':
        table_pattern=r'\\begin\{(table\*?|longtable)\}.*?\\end\{\1\}'
        old_tables=Counter(match.group(0) for match in re.finditer(table_pattern,original,re.S))
        new_tables=Counter(match.group(0) for match in re.finditer(table_pattern,text,re.S))
        check(not (old_tables-new_tables), 'all historical tables byte-preserved ' + name)
        entry['historical_tables_preserved']=sum(old_tables.values())
        check(sum(new_tables.values())==sum(old_tables.values())+2, 'exactly two new result tables ' + name)
        citation_pattern=r'\\cite\w*\*?(?:\[[^\]]*\])*\{[^}]*\}'
        check(Counter(re.findall(citation_pattern,text))==Counter(re.findall(citation_pattern,original)), 'verified citations unchanged ' + name)
        labels=re.findall(r'\\label\{([^}]+)\}',text)
        check(len(labels)==len(set(labels)), 'unique labels ' + name)
        stripped=re.sub(r'(?<!\\)%[^\n]*','',text)
        stack=[]
        for match in re.finditer(r'\\(begin|end)\{([^}]+)\}',stripped):
            action,environment=match.groups()
            if action=='begin': stack.append(environment)
            else: check(bool(stack) and stack.pop()==environment, 'environment close ' + name + ':' + environment)
        check(not stack, 'environment balance ' + name)
        depth=0
        for position, character in enumerate(stripped):
            if character not in '{}':
                continue
            backslashes=0
            previous=position-1
            while previous>=0 and stripped[previous]=='\\':
                backslashes+=1
                previous-=1
            if backslashes%2:
                continue
            depth += 1 if character=='{' else -1
            assert depth>=0, ('brace underflow',name)
        check(depth==0, 'brace balance ' + name)
        for label in ('tab:seq156-contrastive','tab:seq158-coaching','sec:seq158-extension'):
            check(label in labels,'new bounded label ' + name + ':' + label)
        for row in contrast_rows:
            seed,plain,treated,delta,d1,d2,wins,losses,record_plain,record_treated=row
            expected=f'{seed} & {plain}/{treated} & {"+" if delta>0 else ""}{delta} & {d1}/{d2} & {wins}/{losses} & {record_plain}/{record_treated} & Fail'
            check(expected in text, 'C92 source-derived TeX row ' + name + ':' + str(seed))
        for row in cohort_rows:
            seed,mat_p,mat_n,upd_p,upd_n,fresh_p,fresh_n,fresh_o,old_p,old_n,old_o,lost_p,lost_n=row
            expected=f'{seed} & {mat_p}/{mat_n} & {upd_p}/{upd_n} & {fresh_p}/{fresh_n}/{fresh_o} & {old_p}/{old_n}/{old_o} & {lost_p}/{lost_n} & 0'
            check(expected in text, 'C94 source-derived TeX row ' + name + ':' + str(seed))
    else:
        link_pattern=r'\[[^\]]+\]\(([^)]+)\)'
        links=Counter(re.findall(link_pattern,text))-Counter(re.findall(link_pattern,original))
        for target in links:
            if '://' not in target:
                filename=target.split('#',1)[0]
                check((path.parent/filename).exists(), 'added source link ' + name + ':' + target)
        entry['new_local_links_checked']=sum(links.values())
    files[name]=entry

check(checksum('gpu/codex/dream_state.rules')==snapshot['rules_sha256'], 'unrelated rules sentinel unchanged')
tools={name:shutil.which(name) for name in ('pdflatex','latexmk','tectonic')}
record={'status':'PASS_LOCAL_MANUSCRIPT_SOURCE_CHECKS_NOT_SCIENTIFIC_APPROVAL',
        'scope':'SEQ156-158 only, plus Main-reported prospective repair launch without outcomes',
        'files':files,'baseline_path':str(BASE),'source_pins':{str(RECEIPTS/name):value for name,value in source_pins.items()},
        'contrastive_rows':contrast_rows,'coaching_rows':cohort_rows,'retention_rescore':{'items':360,'score_discrepancies':0},
        'checks':checks,'rules_sha256':snapshot['rules_sha256'],'tex_tools':tools,
        'audit_command':'python3 -B /tmp/astra_manuscript_seq156_158_check_20260913.py',
        'validation_script_sha256':checksum(__file__),
        'limits':['No Git/native/network/scorer execution or build/install.','Main-reported25/14/13/22reducer tests, not rerun by this manuscript writer.',
                  'No PDF build/layout verification.','Watcher audits consistency-only; archived raw-derived reports control counts and error descriptions.',
                  'No extraction/compiler benefit without same-child same-history raw-chronological LoRA control.']}
add_file(Path('/tmp/astra_manuscript_seq156_158_validation_20260913_final.json'),json.dumps(record,indent=2)+'\n')
add_file(Path('/tmp/astra_manuscript_seq156_158_diff_20260913_final.patch'),''.join(patch_chunks))
print(record['status'],len(checks),'checks')
for name,entry in files.items(): print(entry['sha256'],name)
print('TEX_TOOLS',tools)

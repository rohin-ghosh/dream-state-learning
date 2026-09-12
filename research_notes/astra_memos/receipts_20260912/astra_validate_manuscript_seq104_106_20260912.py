from pathlib import Path
from collections import Counter
import datetime
import difflib
import hashlib
import json
import re
import shutil
import tarfile

root = Path('/data/home/rohing/dream-state')
backup = Path('/tmp/astra_manuscript_seq104_106_backup_20260912_TNtF2e')
paths = [
    'paper_prototype/main.tex',
    'paper_prototype/README.md',
    'paper_prototype/astra_sprint_draft_20260912.tex',
    'paper_prototype/astra_sprint_abstract_20260912.md',
    'research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md',
    'research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md',
]
before = {path: (backup / path).read_text() for path in paths}
after = {path: (root / path).read_text() for path in paths}
checks = []

def check(name, condition, details=None):
    checks.append({'check': name, 'pass': bool(condition), 'details': details})
    if not condition:
        print('FAIL:', name, details)

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def section(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]

main = paths[0]
original_abstract = section(before[main], '\\begin{abstract}', '\\end{abstract}')
check('canonical abstract byte-identical', original_abstract == section(after[main], '\\begin{abstract}', '\\end{abstract}'))
restored = re.sub(r'\\paragraph\{First-phase plasticity across teaching roots \(SEQ-104; C48\)\.\}.*?(?=\\section\{Discussion\})', '', after[main], count=1, flags=re.S)
restored = restored.replace('SEQ-104 below extends only the first phase to initial teaching seeds1/2; this four-phase result remains seed0-only.', 'No outcomes from the later 19:21 UTC replication launch are included.')
restored = restored.replace('\n\n\n\\section{Discussion}', '\n\n\\section{Discussion}')
check('canonical changes only new result block and stale C46 status', restored == before[main])
check('canonical discussion through appendix byte-identical', after[main].split('\\section{Discussion}', 1)[1] == before[main].split('\\section{Discussion}', 1)[1])

table_counts = {}
for path in paths:
    if path.endswith('.tex'):
        old_tables = [match.group(0) for match in re.finditer(r'\\begin\{(table\*?|longtable)\}.*?\\end\{\1\}', before[path], re.S)]
        new_tables = [match.group(0) for match in re.finditer(r'\\begin\{(table\*?|longtable)\}.*?\\end\{\1\}', after[path], re.S)]
    else:
        old_tables = re.findall(r'(?:^\|[^\n]*\n)+', before[path], re.M)
        new_tables = re.findall(r'(?:^\|[^\n]*\n)+', after[path], re.M)
    position = 0
    preserved = True
    for table in old_tables:
        found = after[path].find(table, position)
        if found < 0:
            preserved = False
            break
        position = found + len(table)
    check('prior tables byte-preserved and ordered: ' + path, preserved)
    table_counts[path] = {'before': len(old_tables), 'after': len(new_tables)}

draft_abstract = section(after[paths[2]], '\\begin{abstract}', '\\end{abstract}')
md_abstract = section(after[paths[3]], '## Abstract\n', '\n## Evidence and interpretation boundaries')
normalize = lambda text: ' '.join(text.split())
check('normalized companion TeX/Markdown abstract parity', normalize(draft_abstract) == normalize(md_abstract))
word_count = len(normalize(md_abstract).split())
check('companion abstract at most 250 whitespace words', word_count <= 250, word_count)

claim_map = after[paths[4]]
old_claims = re.findall(r'^## (C\d{2})\b', before[paths[4]], re.M)
new_claims = re.findall(r'^## (C\d{2})\b', claim_map, re.M)
check('C48-C50 consecutive unique additions', new_claims == old_claims + ['C48', 'C49', 'C50'] and len(set(new_claims)) == len(new_claims))
for claim in old_claims[1:]:
    pattern = rf'^## {claim}\b.*?(?=^## C\d{{2}}\b|\Z)'
    old_section = re.search(pattern, before[paths[4]], re.M | re.S).group(0).rstrip()
    new_section = re.search(pattern, claim_map, re.M | re.S).group(0).rstrip()
    if claim == 'C46':
        new_section = new_section.replace('is unresolved; the positive rates are tied at the measured resolution. C48\nnow extends the first phase only to teaching roots1/2, not the four-phase trajectory.', 'is unresolved; the positive rates are tied at the measured resolution. No\noutcomes from the later19:21UTC seed1/2 replication launch are included.')
    check('prior claim preserved except allowed C46 stale status: ' + claim, old_section == new_section)

def stripped_tex(text):
    text = re.sub(r'\\begin\{verbatim\}.*?\\end\{verbatim\}', '', text, flags=re.S)
    return re.sub(r'(?<!\\)%[^\n]*', '', text)

for path in (paths[0], paths[2]):
    text = stripped_tex(after[path])
    stack = []
    problems = []
    for match in re.finditer(r'\\(begin|end)\{([^}]+)\}', text):
        operation, environment = match.groups()
        if operation == 'begin':
            stack.append(environment)
        elif not stack or stack.pop() != environment:
            problems.append(environment)
    check('TeX environment nesting: ' + path, not stack and not problems, {'open': stack, 'mismatches': problems})
    depth = 0
    negative = False
    for match in re.finditer(r'[{}]', text):
        cursor = match.start() - 1
        backslashes = 0
        while cursor >= 0 and text[cursor] == '\\':
            backslashes += 1
            cursor -= 1
        if backslashes % 2:
            continue
        depth += 1 if match.group() == '{' else -1
        negative |= depth < 0
    check('TeX brace balance: ' + path, depth == 0 and not negative, depth)
    labels = re.findall(r'\\label\{([^}]+)\}', text)
    refs = re.findall(r'\\(?:ref|eqref|pageref)\{([^}]+)\}', text)
    check('TeX label references and uniqueness: ' + path, len(labels) == len(set(labels)) and set(refs) <= set(labels), sorted(set(refs) - set(labels)))
    citations = lambda value: set(re.findall(r'\\cite\w*\*?(?:\[[^\]]*\])*\{([^}]+)\}', stripped_tex(value)))
    check('citation-key inventory unchanged: ' + path, citations(before[path]) == citations(after[path]))
    old_commands = set(re.findall(r'\\[A-Za-z]+', stripped_tex(before[path])))
    new_commands = set(re.findall(r'\\[A-Za-z]+', text))
    standard_math_commands = {'\\geq'}
    check('new TeX control words accounted for: ' + path, not (new_commands - old_commands - standard_math_commands), {'new': sorted(new_commands - old_commands), 'standard_math_allowed': sorted(standard_math_commands)})

referenced = set(re.findall(r'\bC\d{2}\b', '\n'.join(after.values())))
check('all evidence IDs resolve', referenced <= set(new_claims), sorted(referenced - set(new_claims)))
check('collaborator remains UNSENT', '**UNSENT' in after[paths[5]])
check('no stale SEQ106 pending review', not re.search(r'(?:review.{0,20}(?:is|remains) pending|separate raw-call review\s+pending)', '\n'.join(after.values()), re.I))
check('no incorrect shared ACT-final order claim', all('both orders end in ACT' not in after[path] and 'both before ACT' not in after[path] for path in paths))

receipt_root = root / 'research_notes/astra_memos/receipts_20260912'
datasets = {
    'plasticity_replications': ('e777a34fd115002b399c848ad8590e50282d6037a110c583a7981db03ddc0ab4', 746, (2023.382487, 1512.304214, 976.997025)),
    'memory_only': ('8400de86e541573a73803b8ee821e753d3ba644e8346a13f85f6a26a691b1a0a', 501, (1666.592415, 1101.776900, 785.153102)),
    'two_habit': ('9f1409c8a4bda08e2c8c0ec9ec0e60b6d695303baaa34f5ec100fa716b5eb824', 254, (799.928952, 537.610627, 381.280358)),
}
analyses = {}
evidence_hashes = {}
for kind, (expected_hash, expected_files, times) in datasets.items():
    archive = receipt_root / f'astra_{kind}_terminal_20260912.tgz'
    validation = json.loads(Path(str(archive) + '.validation.json').read_text())
    extracted = Path(f'/tmp/astra_{kind}_terminal_20260912')
    analysis_path = Path(f'/tmp/astra_{kind}_analysis_20260912.json')
    archived_analysis = receipt_root / analysis_path.name
    analysis = json.loads(analysis_path.read_text())
    analyses[kind] = analysis
    check(kind + ' archive SHA256 binding', digest(archive) == expected_hash == validation['sha256'] == analysis['capsule_sha256'])
    check(kind + ' supplied/archived analysis byte equality', analysis_path.read_bytes() == archived_analysis.read_bytes())
    expected_inventory = validation['files']
    check(kind + ' inventory denominator', len(expected_inventory) == expected_files == analysis['verified_files'])
    actual_inventory = {str(path.relative_to(extracted)): digest(path) for path in extracted.rglob('*') if path.is_file()}
    check(kind + ' extracted inventory exact set/hash equality', actual_inventory == expected_inventory)
    with tarfile.open(archive, 'r:gz') as bundle:
        payload = {member.name.removeprefix('./'): hashlib.sha256(bundle.extractfile(member).read()).hexdigest() for member in bundle.getmembers() if member.isfile()}
    check(kind + ' archive payload exact set/hash equality', payload == expected_inventory)
    check(kind + ' nested clocks match rounded source', tuple(round(analysis[field], 6) for field in ('full_reservation_seconds', 'controller_seconds', 'worker_seconds')) == times)
    check(kind + ' no new OFF or confirmation', analysis['new_off_calls'] == analysis['confirmation_calls'] == 0)
    evidence_hashes[kind] = {'archive': digest(archive), 'analysis': digest(archived_analysis), 'validation': digest(Path(str(archive) + '.validation.json')), 'payload_files': expected_files}

plasticity = analyses['plasticity_replications']
expected_memory = {'seed1-rate-0': 7, 'seed1-rate-3e-5': 6, 'seed1-rate-1e-4': 5, 'seed2-rate-0': 3, 'seed2-rate-3e-5': 3, 'seed2-rate-1e-4': 4}
for branch in plasticity['branches']:
    zero = branch['branch'].endswith('-rate-0')
    check('SEQ104 branch ' + branch['branch'], branch['optimizer_seed'] == 0 and branch['new_updates'] == 16 and branch['counts']['addition']['correct_action'] == 32 and branch['counts']['addition']['adherence'] == (32 if zero else 0) and branch['exact_correct_act_only'] == (0 if zero else 32) and branch['parameter_state_unchanged'] == zero and branch['counts']['memory']['correct'] == expected_memory[branch['branch']])
check('SEQ104 new work counts', plasticity['new_fits'] == 6 and plasticity['new_calls'] == 288)

memory = analyses['memory_only']
for seed in memory['seeds']:
    number = seed['seed']
    dev = seed['panels']['dev']['counts']
    exact = seed['panels']['exact']['counts']
    check('SEQ105 seed ' + str(number), seed['baseline']['memory']['correct'] == [4, 7, 3][number] and dev['memory']['correct'] == exact['correct'] == [14, 16, 16][number] and dev['addition']['adherence'] == dev['addition']['correct_action'] == [0, 0, 32][number] and dev['addition']['invalid_action'] == [32, 32, 0][number] and dev['memory']['invalid'] == exact['invalid'] == 0)
check('SEQ105 capped seed1 calls', memory['seeds'][1]['panels']['dev']['finish_reasons']['length'] == 23)
check('SEQ105 new work counts', memory['new_fits'] == 3 and memory['new_calls'] == 192 and memory['new_updates'] == 240)

two = analyses['two_habit']
for arm, evidence in two['arms'].items():
    counts = evidence['counts']
    check('SEQ106 arm ' + arm, counts['addition']['own_order_success'] == counts['addition']['input_correct'] == counts['addition']['original_adherence'] == counts['addition']['act_success'] == 32 and counts['addition']['opposite_order_count'] == 0 and counts['memory']['correct'] == 4 and counts['memory']['invalid'] == counts['memory']['tag_spill'] == 0 and evidence['gate_pass'])
check('SEQ106 legacy after joint zero, own pass', two['arms']['input_after']['counts']['addition']['joint'] == 0 and two['arms']['input_after']['counts']['addition']['own_order_success'] == 32)
check('SEQ106 work and one-root counts', two['new_fits'] == 2 and two['new_calls'] == 96 and two['new_updates'] == 160 and two['original_parent_seeds'] == [0])

review = Path('/tmp/astra_two_habit_result_review_20260912.md')
archived_review = receipt_root / review.name
review_hash = '79d2fbb6bba749a439bfddea521ca4d75e1de473f758a3d2ce16dcb5f0a9436a'
check('observed SEQ106 review supplied/archived hash equality', digest(review) == digest(archived_review) == review_hash)
check('SEQ106 review actual PASS and exact line orders read', '**PASS:' in review.read_text() and 'PREDICT→ACT→INPUT' in review.read_text())

new_claim_text = claim_map.split('## C48', 1)[1]
source_paths = set(re.findall(r'`((?:research_notes/|/tmp/)[^`]+)`', new_claim_text))
missing_paths = []
for value in source_paths:
    candidate = Path(value) if value.startswith('/') else root / value
    if not candidate.exists():
        missing_paths.append(value)
check('new claim-map source links exist', not missing_paths, missing_paths)
for _, (expected_hash, _, _) in datasets.items():
    check('capsule digest present in claim map: ' + expected_hash[:12], expected_hash in new_claim_text)

tools = {name: shutil.which(name) for name in ('python3', 'apply_patch', 'pdflatex', 'tectonic', 'latexmk', 'xelatex', 'lualatex', 'bibtex', 'chktex')}
check('build limitation based on actual tool discovery', not any(tools[name] for name in ('pdflatex', 'tectonic', 'latexmk', 'xelatex', 'lualatex', 'bibtex', 'chktex')), tools)
file_hashes = {path: {'before': digest(backup / path), 'after': digest(root / path)} for path in paths}
report = {'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'checks': checks, 'pass': all(item['pass'] for item in checks), 'abstract_words': word_count, 'table_counts': table_counts, 'tools': tools, 'backup': str(backup), 'file_hashes': file_hashes, 'evidence_hashes': evidence_hashes, 'seq106_review_sha256': review_hash}
Path('/tmp/astra_manuscript_seq104_106_static_checks_20260912.json').write_text(json.dumps(report, indent=2) + '\n')
diff = ''.join(''.join(difflib.unified_diff(before[path].splitlines(True), after[path].splitlines(True), fromfile=str(backup / path), tofile=str(root / path))) for path in paths)
Path('/tmp/astra_manuscript_seq104_106_changes_20260912.diff').write_text(diff)
print(json.dumps({'pass': report['pass'], 'checks': len(checks), 'failed': sum(not item['pass'] for item in checks), 'abstract_words': word_count, 'table_counts': table_counts}, indent=2))
raise SystemExit(0 if report['pass'] else 1)

# Manuscript companion handoff — verified through SEQ127

Date: September 13, 2026. Filename retains the requested seq126 name; scope is
SEQ125, SEQ126 **and SEQ127**. Complete existing prose patches, not a new outline.
Main retains independent review, integration and all operations. This handoff
does not gate ongoing science and is not external publication authorization.

## Ownership and changes

Only the following six repository files and this handoff were edited for this
assignment. No executor/tests, canonical evidence, receipts, bibliography or
other collaborator files were changed. No Git, network, literature search,
model/tensor access, native inference, GPU operation or live-result inspection.
Applicable root AGENTS instructions were supplied/read; no nested AGENTS were
found in the scoped directories or /tmp.

- `paper_prototype/README.md`: current complete SEQ125–127 evidence summary,
  measured-versus-unmeasured Q0 accounting, primary-versus-secondary anchor
  interpretation, source pointers and historical-cut labels.
- `paper_prototype/astra_sprint_abstract_20260912.md`: current abstract-level
  prose extension through127; historical Abstract block unchanged.
- `paper_prototype/astra_sprint_draft_20260912.tex`: full Q0 result and separate
  OFF anchor subsection, current opening and closing evidence status.
- `paper_prototype/main.tex`: bounded Q0 and anchor result paragraphs before
  Discussion; characterization abstract and entire appendix unchanged.
- `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md`: complete
  UNSENT current update, provenance/review limits, no external send.
- `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md`: C70/C71/C72
  dispositions with exact canonical/receipt bindings and interpretation limits;
  C01–C69 byte-preserved.

### Scientific boundaries

SEQ125 is immutable NONREPORTABLE_RUNTIME_ABORT, not a scientific canary result
or a replicate. SEQ126 is EARLY_XOR_QUARTET_STOP_AUTH, with the three registered
qualifiers preserved: BOTH_MAP_FIRST_STEP_MISS, EARLY_UNARY_TOOL_STOP and
OPAQUE_TOOL_WRITE_FAILURE_THIS_RECIPE. Three fits each receive one quartet
update. Projection passes2/4 per arm; observed changes pass3/4,1/4,2/4. No fit
completes128 updates and no ON readout exists. Nonzero initial directions do not
become a zero-gradient claim; empty readout fields are not zero final accuracy,
measured complementarity failure or perfect locality. No general impossibility,
completed unary/XOR comparison or Q0 confirmation/relay promotion is claimed.
Main's native replay, non-blinded bounded metadata review and archive byte custody
are attributed separately, not presented as this manuscript writer's rerun.

SEQ127 is n=1 no-fit OFF, strict absent0/12 versus present10/12. All12 absent
outputs are fenced JSON; all12 present outputs are bare JSON. Secondary content
is11/12 absent versus10/12 present;11/12 paired objects are identical and one
worsens. Those secondary counts are attributed to the supplied bounded raw
analysis, not independently rescored here. Primary scores remain unchanged;
no invalid-score rescue. The treatment replaces the tokenizer-inserted generic
helper system with the procedural anchor, not no-system versus system or an
append-only intervention. No observation learning, persistence, L2, general
perception or H1/H2 evidence follows. The separate seed0 two-fit/six-readout
study is mentioned **only at Main's supplied planning cut** as live, with learner
replicas planned; no live fitted metrics/results are included or inspected.
Disabled-LoRA OFF is not substituted for its LoRA-enabled matched OFF controls.

Prior through124 evidence, thesis/H1/H2, author intent and historical origin
labels remain intact. No source ancestry is cleaned by prospective model
identity. All108 existing tables, both TeX abstracts, the historical Markdown
Abstract, main appendix and C01–C69 have matching pre-edit baseline hashes.

## Final file SHA256

```text
6e7d2823c88d46f2929e9a2175a41b9696e55b2196a264c2e51ffb31101e1b91  paper_prototype/README.md
bd6b1c22521acfca6a245b39241f0bb184b0099377ec9b4f23fb442967c02ef9  paper_prototype/astra_sprint_abstract_20260912.md
ef76f190fd13cce90c66ad8b97ea5d64fe8b0231152f3f1bf5e22d0ee9d725c1  paper_prototype/astra_sprint_draft_20260912.tex
fcfe8d927547b670892a79f496837b676debef25d81e9b18c7bb94d5c9a986d3  paper_prototype/main.tex
75552bc85996c0c92d9e5e95b3289a0d4c0c234a05e97707f85576c6656237df  research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md
b6470221ed6da4b3dabfae42299a1848f533b384c81e76eb768b575f0b039381  research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md
```

Canonical and returned receipt SHA256 values are bound in C70–C72 and checked
again by the reproducible script below. The Q0 report-object digest is compact
sorted JSON **including a trailing newline**, unlike its whole-file digest.
The SEQ127 collection report's `archive_sha256` is the **member-index** digest
7a1db115…, not the compressed capsule digest471f1302…. Capsule digests are
recorded identities; this manuscript task did not open/hash full capsules.

## Validation commands and results

From `/data/home/rohing/dream-state`, execute the single Python block in this
handoff without creating any further file:

```sh
python3 - <<'PY'
from pathlib import Path
handoff = Path('/tmp/astra_manuscript_seq126_handoff_20260913.md').read_text()
script = handoff.split('```python\n', 1)[1].split('\n```', 1)[0]
exec(compile(script, '<manuscript-through127-validation>', 'exec'))
PY
sha256sum paper_prototype/README.md paper_prototype/astra_sprint_abstract_20260912.md paper_prototype/astra_sprint_draft_20260912.tex paper_prototype/main.tex research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md /tmp/astra_manuscript_seq126_handoff_20260913.md
```

Final validation: eight PASS groups, no assertion failures. Compiler availability
is reported separately: pdflatex, latexmk, tectonic and chktex unavailable. No
PDF build or layout validation was performed. No mock tests or static checks are
called native scientific proof. Two preliminary check-script assertions were
corrected without changing evidence or manuscript results: a naive TeX escaped-
brace regex ignored escape parity; an initial report hash omitted the required
trailing newline. The final script incorporates both fixes.

```python
import hashlib
import json
import re
import shutil
from pathlib import Path

def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()

files = [
    'paper_prototype/README.md',
    'paper_prototype/astra_sprint_abstract_20260912.md',
    'paper_prototype/astra_sprint_draft_20260912.tex',
    'paper_prototype/main.tex',
    'research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md',
    'research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md',
]
texts = [Path(path).read_text() for path in files]
baselines = [
    (39, '618251f97859f047b02cf8c3a9287ec94f593f9d121805de12b169e26056f571'),
    (0, 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    (25, 'fc53bf90a10d134240ca0576d28806f0558cc8e2203b5aa84de6b60bf8143b39'),
    (8, '170c99cd9ca818af043a1c562d6e530ffbd849a14293d185f74d22d9696d4482'),
    (0, 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    (36, '509d0b65d06c4cb922fd39087b625f5fe5926d080a65d686755f02ca0ce846e1'),
]
for path, text, expected in zip(files, texts, baselines):
    if path.endswith('.tex'):
        tables = [match.group(0) for match in re.finditer(r'\\begin\{(table\*?|longtable)\}[\s\S]*?\\end\{\1\}', text)]
    else:
        tables = re.findall(r'(?m)(?:^\|[^\n]*\n)+', text)
    assert (len(tables), sha('\n'.join(tables))) == expected, path
print('PASS 1: 108 existing tables unchanged')
for index, expected in [
    (2, 'cd03d064e14701457c1c833dd9bfb2dd1a700362e5f35233994d8f2828bad740'),
    (3, '301ed1d6ffc2ad99a03442e7f6fbea1ca3571c4656d63cc872a9026409d00cb6'),
]:
    abstract = re.search(r'\\begin\{abstract\}[\s\S]*?\\end\{abstract\}', texts[index]).group(0)
    assert sha(abstract) == expected
assert sha(texts[1][texts[1].index('## Abstract\n'):texts[1].index('## Evidence and interpretation boundaries\n')]) == 'c8376c450b622f525db16de9bd56773250ee25fdaf4d5b06f6c6b50d94457797'
assert sha(texts[3][texts[3].index('\\appendix'):]) == '19639c81a69f4da1b9f81ac6d493ea89312fc729e2de863adc9890b65072b445'
assert sha(texts[5][texts[5].index('## C01'):texts[5].index('\n## C70')]) == '4dfb2829983477450f7aa5492bc65530ef70cebf6f842f40eea6d3b8eebfeb2a'
print('PASS 2: historical abstracts, main appendix and C01-C69 unchanged')
for path, text in zip(files, texts):
    normalized = text.replace('\\_', '_')
    for required in ['NONREPORTABLE_RUNTIME_ABORT', 'EARLY_XOR_QUARTET_STOP_AUTH', 'C72', '11/12', '10/12', '0/12', 'secondary', 'no live fitted outcomes']:
        assert required.lower() in normalized.lower(), (path, required)
    assert not re.search(r'no SEQ127 perception result', text, re.I), path
for claim in ['C70', 'C71', 'C72']:
    assert len(re.findall(r'^## ' + claim + r'\b', texts[5], re.M)) == 1
assert '**UNSENT**' in texts[4] and texts[4].startswith('# DRAFT ONLY — unsent')
print('PASS 3: six-file current boundaries, unique C70-C72 and UNSENT')
for index in [2, 3]:
    depth = 0
    clean = []
    for line in texts[index].splitlines():
        for match in re.finditer(r'([\\]*)([{}%])', line):
            escapes, token = match.groups()
            if len(escapes) % 2:
                continue
            if token == '%':
                line = line[:match.start()]
                break
            depth += 1 if token == '{' else -1
            assert depth >= 0, files[index]
        clean.append(line)
    assert depth == 0, (files[index], depth)
    stack = []
    for match in re.finditer(r'\\(begin|end)\{([^}]+)\}', '\n'.join(clean)):
        if match.group(1) == 'begin':
            stack.append(match.group(2))
        else:
            assert stack and stack.pop() == match.group(2), files[index]
    assert not stack
print('PASS 4: escape-parity-aware LaTeX brace/environment balance')
base = Path('research_notes/astra_memos')
source_hashes = {
    'ASTRA_Q0_FIRST_UPDATE_STOP_2026-09-13.md': 'e8fa45555718b643d74a078405dd342ceef5b4d9f0c2ef14014bb400b6b17901',
    'receipts_20260912/astra_q0_attempt2_separate_replay_20260913.json': '1a850b0eed265ed027159747025ea64335b25601944c938b0bcccba55e120a4f',
    'receipts_20260912/astra_q0_attempt2_bounded_review_20260913.md': '822197cef2c732700cc91530b2f537af7881013c51b6d36d2a137a5ebcde2776',
    'receipts_20260912/astra_q0_attempt2_custody_20260913.json': '265c91f161c446854cb652ddb2cca56300c696f872c2a7d91814a733ee847e98',
    'ASTRA_PERCEPTION_ANCHOR_OFF_2026-09-13.md': 'ec13a83cb2abae356856a480ec6db229c3b5c85718b9becec427f649c29b9fb1',
    'receipts_20260912/astra_perception_anchor_raw_analysis_20260913.md': '6e067148b25f34bd8d4f9ad2f0afe5e527af37b7695986894a1fdaaecf787e37',
    'receipts_20260912/astra_perception_anchor_20260913_attempt3_report.json': 'bfcfebee88dbac507affaa822dd6e8a7acb1c79862e1a6aca3b238744f461244',
}
for path, expected in source_hashes.items():
    assert hashlib.sha256((base / path).read_bytes()).hexdigest() == expected, path
print('PASS 5: seven canonical/receipt SHA256 identities')
q0 = json.loads((base / 'receipts_20260912/astra_q0_attempt2_separate_replay_20260913.json').read_text())
report = q0['report']
assert sha(json.dumps(report, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n') == q0['report_sha256'] == '250e67b36c16325f5b8042e7731dd71c615cd0387c1f1f6d092b68e8188c87e5'
assert report['label'] == 'EARLY_XOR_QUARTET_STOP_AUTH'
assert report['attempted_fits'] == 3 and report['updates'] == 3 and report['training_forwards'] == 12
assert report['generations'] == 296 and report['generated_tokens'] == 2065 and report['prefix_readouts'] == 288
assert report['counters'] == {'model_forward_calls': 2925, 'natural_prefix_forwards': 860}
assert report['qualifiers'] == ['BOTH_MAP_FIRST_STEP_MISS', 'EARLY_UNARY_TOOL_STOP', 'OPAQUE_TOOL_WRITE_FAILURE_THIS_RECIPE']
assert not report['cells'] and not report['checkpoint_curves']
assert round(report['resource']['elapsed_seconds'], 6) == 1373.552545
assert round(report['durable_completion']['elapsed_seconds'], 6) == 1378.080670
print('PASS 6: Q0 report-object SHA, terminal, work counters, timing and absent readouts')
anchor = json.loads((base / 'receipts_20260912/astra_perception_anchor_20260913_attempt3_report.json').read_text())
assert len(anchor['pairs']) == 12 and len({pair['row_id'] for pair in anchor['pairs']}) == 12
assert anchor['passed_counts'] == {'absent': 0, 'present': 10}
for condition in ['absent', 'present']:
    assert len(anchor['scores'][condition]) == 12
    decisions = [score['passed'] for score in anchor['scores'][condition]]
    assert decisions == [pair[condition] for pair in anchor['pairs']]
    assert sum(decisions) == anchor['passed_counts'][condition]
assert anchor['present_minus_absent'] == 10
assert anchor['learned_skill_claim'] is False and anchor['science_pass'] is None
assert anchor['archive_sha256'] == '7a1db115d8783940ae6afa0325bb0b715e12a867198915f68c08128fd1f8f59b'
assert anchor['plan_sha256'] == 'f57769c71eeb0ecc55283749d7a00e864861c232561fef976f91f19fb61f690c'
print('PASS 7: SEQ127 12 pairs/24 decisions, counts, claim limits and index/plan IDs')
final_hashes = [
    '6e7d2823c88d46f2929e9a2175a41b9696e55b2196a264c2e51ffb31101e1b91',
    'bd6b1c22521acfca6a245b39241f0bb184b0099377ec9b4f23fb442967c02ef9',
    'ef76f190fd13cce90c66ad8b97ea5d64fe8b0231152f3f1bf5e22d0ee9d725c1',
    'fcfe8d927547b670892a79f496837b676debef25d81e9b18c7bb94d5c9a986d3',
    '75552bc85996c0c92d9e5e95b3289a0d4c0c234a05e97707f85576c6656237df',
    'b6470221ed6da4b3dabfae42299a1848f533b384c81e76eb768b575f0b039381',
]
for path, expected in zip(files, final_hashes):
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
print('PASS 8: six final manuscript file SHA256 identities')
print('TeX tools:', {tool: shutil.which(tool) for tool in ['pdflatex', 'latexmk', 'tectonic', 'chktex']})
```

## Remaining review and limitations

Main: review prose independently and integrate. No code/native scheduling work
is requested by this manuscript task. A TeX-capable environment still needs to
compile/inspect layout; static syntax balance cannot substitute. No new
references were added or searched. Returned reports and bounded raw analysis
support this update; no numerical/scientific replay was performed by the writer.
No missing fitted outcomes are filled in and no live-study result is implied.

EDITSTOP

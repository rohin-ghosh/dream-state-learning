import hashlib
import json
from pathlib import Path


ROOT = Path('/data/home/rohing/dream-state/research_notes/astra_memos/receipts_20260912')
OUTPUT = Path('/tmp/astra_parented_record_prior_ids_20260913.json')
MANIFEST = Path('/tmp/astra_parented_record_prior_ids_20260913_manifest.json')
identifiers = set()
sources = []


def visit(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in ('episode_id', 'task_id') and isinstance(child, str) and child:
                identifiers.add(child)
            elif key in ('episode_ids', 'task_ids') and isinstance(child, list):
                identifiers.update(item for item in child if isinstance(item, str) and item)
            visit(child)
    elif isinstance(value, list):
        for child in value:
            visit(child)


for path in sorted(ROOT.rglob('*.json')):
    raw = path.read_bytes()
    before = len(identifiers)
    visit(json.loads(raw))
    sources.append(dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(raw).hexdigest(), newly_seen_ids=len(identifiers)-before))
with OUTPUT.open('x') as stream:
    stream.write(json.dumps(sorted(identifiers), ensure_ascii=False) + '\n')
report = dict(source_root=str(ROOT), source_files=sources, count=len(identifiers),
              output_sha256=hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
              scope='Conservative IDs in archived JSON receipts; includes fixtures/authored IDs, not a global exposure census or clean-ancestry certification.')
with MANIFEST.open('x') as stream:
    stream.write(json.dumps(report, sort_keys=True, ensure_ascii=False) + '\n')
print(json.dumps(dict(count=len(identifiers), files=len(sources), output_sha256=report['output_sha256'], manifest_sha256=hashlib.sha256(MANIFEST.read_bytes()).hexdigest())))

"""Explain the first strict delivery ambiguity without relaxing or rerunning any parent."""

import json
from pathlib import Path
import shlex
import subprocess
import time

from console_baseline import read, ref, require, write
from diagnose_snapshot import CASES


HERE = Path(__file__).resolve().parent
SCRIPT = '''import hashlib,json
from gpu import orch_r166_parent_snapshot as snapshot
from gpu import orch_r127_pilot_transcript as transcript
root=ROOT
state=snapshot.genesis(root)
stats=dict(source_bytes=0,journal_id=None,head_sha256=None)
answer=dict(status='NO_AMBIGUITY_FOUND')
inbox_indices={}
for record,mtime,file_hash in transcript._records(root,stats,transcript.MAX_RECORDS,transcript.MAX_RECORD_BYTES,transcript.MAX_TOTAL_BYTES):
 if record['kind']=='INBOX': inbox_indices[record['document']['message']['id']]=record['index']
 try:
  snapshot._reduce(state,record)
 except ValueError as error:
  if str(error)!='ambiguous_delivery': raise
  visible,ambiguous=transcript._visible(record['document']['messages'],state['inbox'])
  answer=dict(status='STRICT_READER_REFUSAL_PRESERVED',record_index=record['index'],record_sha256=record['sha256'],
   request_count_before=state['request_count'],response_count_before=state['response_count'],
   ambiguous=[dict(identifier=identifier,speaker=state['inbox'][identifier]['speaker'],
    inbox_record_index=inbox_indices[identifier],inbox_sha256=state['inbox'][identifier]['inbox_source_sha256'],
    text_sha256=hashlib.sha256(state['inbox'][identifier]['visible_text'].encode()).hexdigest(),
    already_exactly_delivered=identifier in state['delivered'],in_current_predecessor_ledger=identifier in PUBLICATIONS)
    for identifier in sorted(ambiguous)],
   all_already_exactly_delivered=ambiguous<=state['delivered'].keys(),
   any_current_predecessor_publication=bool(ambiguous&set(PUBLICATIONS)))
  break
print(json.dumps(answer))
'''


def main():
    rows = []
    for name, label in CASES:
        manifest = read(HERE / name / (label + '_MANIFEST.json'))
        config = read(manifest['predecessor']['config']['path'])
        publications = []
        for result_path in Path(manifest['predecessor']['output_path']).glob('parent_*/RESULT.json'):
            result = read(result_path)
            publication = result.get('publication') or result.get('inbox_publication')
            if publication:
                publications.append(publication['id'])
        script = SCRIPT.replace('ROOT', repr(config['root'])).replace('PUBLICATIONS', repr(publications))
        command = 'PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=' + shlex.quote(manifest['remote_source'])
        command += ' python3 -B -c ' + shlex.quote(script)
        result = subprocess.run(['bash', str(Path(manifest['source']) / 'gpu/ovx3_ssh.sh'), command],
                                capture_output=True, text=True, timeout=45)
        require(result.returncode == 0, 'metadata_ambiguity_probe_failed:' + result.stderr[-180:])
        rows.append(dict(label=label, evidence=json.loads(result.stdout), source_pins=manifest['source_pins']))
    receipt = HERE / ('AMBIGUITY_TRACE_' + str(time.time_ns()) + '.json')
    write(receipt, dict(observed_unix=time.time(), rows=rows, refusal_preserved=True,
        no_signals=True, no_parent_calls=True, no_journal_writes=True, no_sealed_content=True))
    print(json.dumps(dict(receipt=ref(receipt), rows=[dict(label=row['label'], evidence=row['evidence']) for row in rows])))


if __name__ == '__main__':
    main()

"""Archive current unsealed TRAIN evidence before authoring a console baseline."""

import argparse
import json
from pathlib import Path
import time

from inventory_node1 import HERE, digest, identity, require, unchanged
from parent_custody import write
from parent_runner import load


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--physical', type=int, choices=range(3, 8), required=True)
    arguments = parser.parse_args()
    activations = list(HERE.glob('lane' + str(arguments.physical) + '_activation_*/PARENT_ACTIVATED.json'))
    require(len(activations) == 1, 'one_actual_assigned_parent')
    activation_path = activations[0]
    activation = json.loads(activation_path.read_text())
    spec_path = activation_path.parent / 'SPEC.json'
    spec = json.loads(spec_path.read_text())
    require(unchanged(activation['actor'], identity(Path('/proc') / str(activation['actor']['pid']))),
            'actual_current_parent_identity')
    parent, config, unused_provider, unused_selected = load(spec)
    source = parent['snapshot'](Path(spec['repository']), config)
    children = [event for event in source['events'] if event['actor'] == 'child'][-2:]
    require(children, 'actual_visible_child_source_required')
    evidence = [dict(record_index=event['record_index'], record_sha256=event['record_sha256'],
                     text_sha256=digest(event['text'].encode())) for event in children]
    script = '''import json,os,stat
from gpu.orch_r125_stream_console import _open_stream_directory,_read_record
from gpu.orch_r125_stream_journal import _digest
remaining=67108864
root=ROOT
with _open_stream_directory(root,'records') as (directory,unused):
 def read(index):
  global remaining
  metadata=os.stat(f'{index:020d}.json',dir_fd=directory,follow_symlinks=False)
  assert stat.S_ISREG(metadata.st_mode) and metadata.st_size<=16777216 and metadata.st_size+1<=remaining
  remaining-=metadata.st_size+1
  return _read_record(directory,index)
 head=read(HEAD_INDEX)
 assert head['sha256']==HEAD_SHA
 checked=[]
 for entry in EVIDENCE:
  record=read(entry['record_index']); committed=read(entry['record_index']+1)
  assert record['kind']=='RESPONSE' and record['sha256']==entry['record_sha256']
  assert committed['kind']=='COMMITTED' and committed['previous_sha256']==record['sha256']
  assert committed['document']['source_sha256']==_digest(record['document'])
  import hashlib
  assert hashlib.sha256(record['document']['response']['raw'].encode()).hexdigest()==entry['text_sha256']
  checked.append(dict(entry,committed_index=committed['index'],committed_sha256=committed['sha256']))
 print(json.dumps(dict(latest_kind=head['kind'],head_index=head['index'],head_sha256=head['sha256'],
                      verified_child_commits=checked,bytes_charged=67108864-remaining)))
'''.replace('ROOT', repr(spec['root'])).replace('HEAD_INDEX', repr(source['record_count'] - 1))
    script = script.replace('HEAD_SHA', repr(source['head_sha256'])).replace('EVIDENCE', repr(evidence))
    verified = parent['remote'](Path(spec['repository']), config, script)
    directory = HERE / ('BASELINE_SOURCE_' + str(arguments.physical) + '_' + str(time.time_ns()))
    directory.mkdir(mode=0o700)
    write(directory / 'SOURCE.json', source)
    write(directory / 'RECEIPT.json', dict(physical=arguments.physical, label=activation['label'],
          active_spec=str(spec_path), active_spec_sha256=digest(spec_path.read_bytes()), arm=spec['arm'],
          source_path=str(directory / 'SOURCE.json'), source_sha256=digest((directory / 'SOURCE.json').read_bytes()),
          verification=verified, observed_unix=time.time(), provider_calls=0, child_actions=0,
          source_operator_sha256=digest(Path(__file__).read_bytes())))
    print(json.dumps(dict(directory=str(directory), label=activation['label'], response_count=source['response_count'],
                          latest_kind=verified['latest_kind'], child_sources=children)), flush=True)


if __name__ == '__main__':
    main()

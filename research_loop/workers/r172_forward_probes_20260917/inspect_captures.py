"""Bounded, resource-only source capture observation; never read TRAIN text."""

import json
import os

import prep_common as common
import prepare


def main():
    os.umask(0o077)
    scope, proposal, ledger = prepare.setup()
    for node in ('a100', 'ovx2', 'ovx3', 'a40r'):
        launch = common.read(prepare.PREP / 'capture_launches' / (node + '.json'))
        lives = [life['life_id'] for life in proposal['lives'] if life['node'] == node
            and (prepare.PREP / 'enrollment' / (life['life_id'] + '.json')).exists()
            and common.read(prepare.PREP / 'enrollment' / (life['life_id'] + '.json'))['status']
            == 'REGISTERED_PRIVATE_CUSTODY_NO_GPU_GO']
        operation = 'capture_resource_observation1_' + node
        reservation = ledger.reserve(operation, '_campaign', 'metadata', prepare.MIB, discovery=True)
        script = f'''import json,time
from pathlib import Path
root=Path({str(common.REMOTE_ROOT)!r})
used=0
def read(path):
 global used
 size=path.stat().st_size
 assert path==path.resolve() and size<=65536 and used+size<=1048576
 used+=size
 return json.loads(path.read_bytes())
identity={launch['identity']!r}
try:
 fields=Path('/proc')/str(identity['pid'])/'stat'
 fields=fields.read_text().rsplit(')',1)[1].split()
 live=fields[0] not in ('Z','X') and fields[19]==str(identity['start_ticks']) and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==identity['boot_id']
except FileNotFoundError:live=False
rows=[]
for name in {lives!r}:
 life=root/'lives'/name
 plan=read(root/'source_controls'/name/'QUEUE_PLAN.json')
 expected=[0]+list(range(plan['first_sleep'],plan['first_sleep']+3))
 completed=[sleep for sleep in expected if (life/'captures'/f'{{sleep:06d}}'/'COMPLETE.json').exists()]
 failed=[sleep for sleep in expected if (life/'captures'/f'{{sleep:06d}}'/'FAILED.json').exists()]
 held=root/'capture_operation1'/{node!r}/name/'HELD.json'
 readings=[read(path) for path in (life/'reads').glob('*.json')]
 rows.append(dict(life_id=name,expected_checkpoints=expected,captured_checkpoints=completed,failed_checkpoints=failed,
  held=held.exists(),hold_error_type=read(held).get('error_type') if held.exists() else None,
  metadata_charged=sum(item['reserved_bytes'] for item in readings if item['kind']=='metadata'),
  adapter_charged=sum(item['reserved_bytes'] for item in readings if item['kind']=='adapter')))
result=dict(status='CAPTURE_RESOURCE_METADATA_ONLY',node={node!r},identity=identity,live=live,rows=rows,
 terminal_exists=(root/'capture_operation1'/{node!r}/'TERMINAL.json').exists(),observed_unix=time.time(),
 metadata_bytes_read=used,model_calls=0,provider_calls=0,sealed_text_reads=0)
print(json.dumps(result,sort_keys=True))
'''
        result = json.loads(prepare.wrapper(node, operation, 'python3 -B -', script.encode()))
        evidence = common.write(prepare.PREP / 'capture_observations' / (node + '_01.json'),
            dict(result, reservation=reservation))
        print(json.dumps(dict(node=node, live=result['live'], observed_unix=result['observed_unix'],
            lives=len(result['rows']), captured=sum(len(row['captured_checkpoints']) for row in result['rows']),
            failed=sum(len(row['failed_checkpoints']) for row in result['rows']),
            held=sum(row['held'] for row in result['rows']), evidence=evidence)))


if __name__ == '__main__':
    main()

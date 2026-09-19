"""Read only pinned node2 source and six selected receipt shapes; never scan a journal."""

import hashlib
import json
from pathlib import Path
import subprocess
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
REMOTE = r'''
import hashlib,json,os,stat,time
from pathlib import Path

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def bounded(path,limit):
    descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(descriptor,'rb') as stream:
        before=os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size>limit:
            raise ValueError('bounded_regular_file')
        raw=stream.read(limit+1)
        after=os.fstat(stream.fileno())
    fields=('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')
    if len(raw)!=before.st_size or any(getattr(before,key)!=getattr(after,key) for key in fields):
        raise ValueError('file_changed')
    return raw

def shape(value,depth=0):
    if isinstance(value,dict) and depth<4:
        return {key:shape(item,depth+1) for key,item in value.items()}
    return dict(type=type(value).__name__,length=len(value) if isinstance(value,(dict,list,str)) else None,
        canonical_sha256=hashlib.sha256(canonical(value)).hexdigest())

sources=('gpu/orch_r125_continual_native.py','gpu/orch_r125_stream_journal.py',
    'organism_v6/orch_r125_continual_stream.py','organism_v6/orch_r124_train_history.py',
    'gpu/orch_r184_think_act_learn.py','gpu/r233_node2_recovery.py','gpu/r205_runtime.py',
    'gpu/r213_recovery_runtime.py','gpu/astra_experienced_event_microloop.py','gpu/orch_guided_native.py')
lives=(('C0','/localhome/local-rohing/orch_r216_C0_20260918_attempt2',
    'acf4d2d015874af1cc9585a25de63827e7d7ec36acd7a4509bce09671985f6c2',(6637,6638,6710)),
    ('Astra7','/localhome/local-rohing/orch_r229_Astra7_20260918',
    'fae6f4ede1e9c80be060aeca8dd494cbb24a6228b9225e33856b62ec3c0047f6',(7753,7754,7807)))
report=[]
for life,base,expected,indices in lives:
    guard_path=Path(base)/'control_r233_lease_continuation/GUARD.json'
    raw=bounded(guard_path,16*1024**2)
    if hashlib.sha256(raw).hexdigest()!=expected:
        raise ValueError('exact_original_guard')
    guard=json.loads(raw)
    plan_raw=bounded(guard['plan_path'],16*1024**2)
    if hashlib.sha256(plan_raw).hexdigest()!=guard['plan_sha256']:
        raise ValueError('exact_original_plan')
    plan=json.loads(plan_raw)
    files=[]
    for name in sources:
        path=Path(plan['source_root'])/name
        raw=bounded(path,2*1024**2)
        actual=hashlib.sha256(raw).hexdigest()
        if actual!=guard['source_pins'][name]:
            raise ValueError('exact_guard_source_pin:'+name)
        files.append(dict(relative_path=name,remote_path=str(path),sha256=actual,text=raw.decode()))
    records=[]
    for index,expected_kind in zip(indices,('REQUEST','RESPONSE','UPDATE')):
        path=Path(guard['copy_raw'])/'stream/records'/f'{index:020d}.json'
        raw=bounded(path,64*1024**2)
        value=json.loads(raw)
        if value['kind']!=expected_kind:
            raise ValueError('selected_receipt_kind')
        if value['sha256']!=hashlib.sha256(canonical({key:item for key,item in value.items() if key!='sha256'})).hexdigest():
            raise ValueError('canonical_selected_record')
        intent=json.loads(bounded(path.with_name(f'{index:020d}.intent.json'),16384))
        if intent!=dict(schema=value['schema'],journal_id=value['journal_id'],index=index,
                previous_sha256=value['previous_sha256'],record_sha256=value['sha256']):
            raise ValueError('selected_intent')
        records.append(dict(path=str(path),index=index,kind=value['kind'],record_sha256=value['sha256'],
            file_sha256=hashlib.sha256(raw).hexdigest(),document_shape=shape(value['document']),
            update_document=value['document'] if value['kind']=='UPDATE' else None))
    report.append(dict(life=life,guard_path=str(guard_path),guard_sha256=expected,
        source_root=plan['source_root'],plan_path=guard['plan_path'],plan_sha256=guard['plan_sha256'],
        source_files=files,selected_records=records))
print(json.dumps(dict(schema='NODE2_REPLAY_SOURCE_READ_ONLY_V1',observed_unix=time.time(),lives=report,
    journal_scan=False,source_code_executed=False,models_loaded=False,node_writes=[],native_actions=[])))
'''


def main():
    output = HERE / ('source_evidence_' + str(time.time_ns()))
    result = subprocess.run(['bash', str(REPO / 'gpu/ovx_ssh.sh'),
        'PYTHONDONTWRITEBYTECODE=1 python3 -B -'], input=REMOTE, capture_output=True, text=True, timeout=90)
    if result.returncode:
        raise RuntimeError(result.stderr[:3000])
    report = json.loads(result.stdout)
    output.mkdir()
    for life in report['lives']:
        for source in life['source_files']:
            raw = source.pop('text').encode()
            if hashlib.sha256(raw).hexdigest() != source['sha256']:
                raise ValueError('exact_received_source')
            path = output / life['life'] / source['relative_path']
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(raw)
            source['local_path'] = str(path)
    report['inspector_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report['transport_sha256'] = hashlib.sha256((REPO / 'gpu/ovx_ssh.sh').read_bytes()).hexdigest()
    with (output / 'RECEIPT.json').open('x') as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(receipt=str(output / 'RECEIPT.json'),
        sha256=hashlib.sha256((output / 'RECEIPT.json').read_bytes()).hexdigest(),
        source_files=sum(len(life['source_files']) for life in report['lives']),
        selected_receipts=sum(len(life['selected_records']) for life in report['lives']),node_writes=[])))


if __name__ == '__main__':
    main()

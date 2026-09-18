"""Transfer only byte-bound registered inbox inputs from the saved41 prefix."""
import hashlib,json,sys,tarfile
from pathlib import Path

packet=Path('/localhome/local-rohing/orch_r184_C2_sleep41_1789684294308387719')
registered={}
for path in sorted((packet/'stream/records').glob('[0-9]'*20+'.json')):
    record=json.loads(path.read_bytes())
    if record['kind']=='INBOX':
        document=record['document']
        registered[document['source_id']]=document['source_sha256']
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as output:
    for name,expected in registered.items():
        path=Path(name)
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected:
            raise ValueError('registered_inbox_hash_changed')
        output.add(path,arcname=path.name,recursive=False)

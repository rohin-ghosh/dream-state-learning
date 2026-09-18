"""Publish Main's exact authorized first clone input, once, with no parent yet."""

import hashlib
import json
from pathlib import Path
import shlex
import subprocess


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[4]
REMOTE = '/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET/creative_b1'


def main():
    path = REPO / 'research_notes/analysis/R202_CLONE_PART_ONE_2026-09-17.txt'
    text = path.read_text()
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    code = f'''import hashlib,json,pathlib,sys,time
root=pathlib.Path({REMOTE!r});sys.path.insert(0,str(root/'source'))
from gpu.orch_r127_pilot_console import publish_parent
proof=json.loads((root/'FIXED_PREFIX_READY.json').read_bytes())
assert proof['full_receiving_journal_and_intents_verified'] and proof['full_journal_records']==5847
assert not (root/'R202_PART_ONE_INTENT.json').exists()
assert not (root/'control/DISPATCH_ONCE').exists()
text={text!r}
assert hashlib.sha256(text.encode()).hexdigest()=={expected!r}
intent=dict(text_sha256={expected!r},authorized_speaker='Rohin',new_clone_input_ordinal=1,
 first_new_parent_opening_must_wait_for_Rohin_render=True,created_unix=time.time())
with (root/'R202_PART_ONE_INTENT.json').open('x') as output:json.dump(intent,output,sort_keys=True)
with (root/'R202_PART_ONE.txt').open('x') as output:output.write(text)
receipt=publish_parent(str(root/'life'),'Rohin',text)
receipt.update(status='PUBLISHED_NOT_CONSUMED',published_unix=time.time(),text_sha256={expected!r},
 speaker='Rohin',new_clone_input_ordinal=1,original_C2_calls=0,parent_opening_published=False)
with (root/'R202_PART_ONE_PUBLICATION.json').open('x') as output:json.dump(receipt,output,sort_keys=True,indent=2)
print(json.dumps(receipt,sort_keys=True))
'''
    result = subprocess.run(['bash', 'gpu/a100_ssh.sh', 'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c ' + shlex.quote(code)],
                            cwd=REPO, capture_output=True, text=True, timeout=30)
    with (OWN / 'R202_PART_ONE_PUBLICATION.stdout').open('x') as output:
        output.write(result.stdout)
    with (OWN / 'R202_PART_ONE_PUBLICATION.stderr').open('x') as output:
        output.write(result.stderr)
    if result.returncode:
        raise RuntimeError('one_shot_input_publication_uncertain_reconcile_do_not_retry')
    print(result.stdout)


if __name__ == '__main__':
    main()

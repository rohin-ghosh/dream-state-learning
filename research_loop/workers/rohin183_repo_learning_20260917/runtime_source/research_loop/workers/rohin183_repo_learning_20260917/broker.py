"""Incremental TRAIN response broker using existing native journal records."""

import argparse
import json
import os
from pathlib import Path
import time

from gpu.orch_r125_stream_console import _open_stream_directory,_read_record
from gpu.orch_r125_stream_journal import _digest,SCHEMA
from research_loop.workers.rohin183_repo_learning_20260917 import tools
from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import require,write,digest


def serve(config_path):
    raw=Path(config_path).read_bytes()
    config=json.loads(raw)
    root=Path(config['root']);output=Path(config['receipts'])
    require(config['schema']=='R183_REPO_TOOLS_V1' and time.time()<config['hard_end_unix'],'bound_new_child_tool_config')
    require(root.parent==Path(config['workspace']).parent and not output.exists(),'own_root_and_once_only_broker')
    output.mkdir(mode=0o700,parents=True)
    Path(config['workspace']).mkdir(mode=0o700,parents=True,exist_ok=True)
    tools.manifest(config)
    write(output/'STARTED.json',dict(pid=os.getpid(),started_unix=time.time(),config_sha256=digest(raw),
        protected_prompt_carry_implemented=False,tools_available=['read','list','note','propose','workspace_read']))
    while time.time()<config['hard_end_unix'] and not (root/'stream/JOURNAL.json').exists():
        time.sleep(1)
    require(time.time()<config['hard_end_unix'],'journal_appears_inside_lease')
    journal=json.loads((root/'stream/JOURNAL.json').read_bytes())
    require(journal['schema']==SCHEMA,'actual_native_journal')
    previous,index,sequence=_digest(journal),0,0
    while time.time()<config['hard_end_unix'] and sequence<tools.ACTION_LIMIT:
        with _open_stream_directory(root,'records') as (directory,unused):
            record=_read_record(directory,index)
        if record is None:
            time.sleep(1)
            continue
        require(record['previous_sha256']==previous and record['journal_id']==journal['journal_id'],'incremental_journal_chain')
        if record['kind']=='RESPONSE':
            origin=dict(actor='child',split='TRAIN',record_index=index,record_sha256=record['sha256'])
            if not (output/'FIRST_TURN.json').exists():
                write(output/'FIRST_TURN.json',dict(origin=origin,observed_unix=time.time(),response_text_not_exported=True))
            try:
                action=tools.request(record['document']['response']['raw'])
                if action is not None:
                    write(output/f'INTENT_{sequence:06d}.json',dict(action=action,origin=origin,observed_unix=time.time()))
                    reference=tools.execute(config,action,origin,sequence)
                    write(output/f'COMPLETE_{sequence:06d}.json',dict(receipt=reference,action=action['action'],
                        observed_unix=time.time(),origin=origin))
                    sequence+=1
            except (ValueError,FileNotFoundError,FileExistsError,UnicodeError) as error:
                write(output/f'REJECTED_{index:020d}.json',dict(origin=origin,error_type=type(error).__name__,
                    reason=str(error)[:300],observed_unix=time.time()))
                sequence+=1
        previous=record['sha256'];index+=1
    write(output/'EXIT.json',dict(observed_unix=time.time(),records_seen=index,actions=sequence,reason='bounded_wall_or_actions'))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',required=True)
    serve(parser.parse_args().config)

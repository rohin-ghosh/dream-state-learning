"""Explicit resumed, charged preparation repair, never a same-attempt retry."""

import base64
import json
import os
from pathlib import Path
import shlex
import subprocess
import time

import preparation_io as common
from launch_c2_capture1 import BOOTSTRAP


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DIRECTIVE = ('Status/priority interrupt (preserve all active remote jobs, do not restart): '
    'R176 C2/C5 prep authorized at PREPARATION_SCOPE.json '
    'SHA745921c838ae4190f5d633d30ba01375ad2c995a27d08134caa055503c5318d6; '
    'scope2GiBmetadata16GiBadapters2GiBreceiver, fixed12slots72maxfuturecalls but0GO now. '
    'Rawls V3 APPROVES repairedtransfercomponents transfer.py '
    'e8b3aed5abe19cfc195ac4fde318e8316834c582d883e9dcfce892b02f19bb2e '
    'prep_common f6751d157bb283627a185ecf14321d571673512b61f17aedac3b056ef5410aee;'
    '4independent+70focused tests pass. Resume earliest actual C2 custody/capture/receiving path, '
    'independently of C5/generalizedfleet. Rohin160/161 gamebuildrunsparallel not cancelprobes. '
    'Reply IMMEDIATELY concise factualcurrentstatus/firstreadycellblockingartifact, then continue '
    'implementationandCPU/custody. Mainblindsealedcontents. No GPU without MainboundGO.')


def main():
    os.umask(0o077)
    controls = common.validate_controls(HERE)
    operation = HERE/'preparation1/source_capture2'
    operation.mkdir(parents=True, mode=0o700, exist_ok=False)
    failed = HERE/'preparation1/source_capture1/PUBLIC_METADATA.json'
    repair = common.write(operation/'RESUMED_PREPARATION.json',dict(
        classification='NON_MATERIAL_PATH_CHECK_REPAIR_DISTINCT_ATTEMPT',
        directive_verbatim=DIRECTIVE,scope_sha256=common.SCOPE_SHA,
        failed_receipt=dict(path=str(failed),sha256=common.sha(failed.read_bytes())),
        failed_operation='C2_sleep33_original_capture',new_operation='C2_sleep33_original_capture_repair1',
        failed_reservations_preserved=True,new_adapter_reservation_bytes=128*common.MIB,
        full_grid_plus_repair_envelope_bytes=15*common.GIB+128*common.MIB,
        scope_budget_expansion=False,model_calls=0,provider_calls=0,recorded_unix=time.time()))
    ledger = common.Ledger(HERE/'preparation1/global_ledger')
    stage = ledger.reserve('C2_capture2_control_transport','_campaign','metadata',4*common.MIB,discovery=True)
    allowances = dict(
        metadata=ledger.reserve('C2_capture2_metadata','C2','metadata',32*common.MIB),
        discovery=ledger.reserve('C2_capture2_native_discovery','C2','metadata',2*common.MIB,discovery=True),
        adapter=ledger.reserve('C2_sleep33_original_capture_repair1','C2','adapter',128*common.MIB,
            sleep=33,read_pass='original_capture',repair_authority=repair))
    inventory = json.loads((HERE.parent/'r172_forward_probes_20260917/preparation1/discovery/ovx3.json').read_bytes())
    native = next(row['native_identity'] for row in inventory['rows'] if row['life_id']=='C2')
    sources = {name:(HERE/name).read_bytes() for name in ('preparation_io.py','c2_capture.py')}
    request = dict(scope=controls['PREPARATION_SCOPE.json'],allowances=allowances,native_identity=native,
        life_id='C2',sleep=33,model_calls=0,provider_calls=0,repair_authority=repair,
        source_pins={name:common.sha(raw) for name,raw in sources.items()})
    common.write(operation/'REQUEST.json',request)
    for name, raw in sources.items():
        common.write(operation/'author_source'/name,raw)
    files = {'source/'+name:raw for name,raw in sources.items()}
    files.update({'control/'+name:(HERE/name).read_bytes() for name in controls})
    files['REQUEST.json'] = common.canonical(request)
    payload = common.canonical(dict(stage_allowance=stage,
        files={name:base64.b64encode(raw).decode() for name,raw in files.items()}))
    common.require(len(payload)<2*common.MIB,'bounded_staging_payload')
    common.write(operation/'LAUNCH.json',dict(started_unix=time.time(),payload_bytes=len(payload),
        stage_allowance=stage,wrapper='gpu/ovx3_ssh.sh',model_calls=0,provider_calls=0))
    try:
        completed = subprocess.run(['bash',str(REPO/'gpu/ovx3_ssh.sh'),
            'python3 -c '+shlex.quote(BOOTSTRAP.replace('/source_capture1','/source_capture2'))],
            input=payload,capture_output=True,timeout=180)
        common.require(len(completed.stdout)<common.MIB and len(completed.stderr)<common.MIB,'bounded_operation_output')
        if completed.stdout.strip():
            result = json.loads(completed.stdout)
        else:
            result = dict(status='WRAPPER_OR_SOURCE_FAILURE_PRESERVED_NO_RETRY',returncode=completed.returncode,
                stderr_bytes=len(completed.stderr),stderr_sha256=common.sha(completed.stderr),
                observed_unix=time.time(),model_calls=0,provider_calls=0)
        result['wrapper_returncode'] = completed.returncode
    except Exception as error:
        result = dict(status='LAUNCH_FAILED_OR_UNCERTAIN_NO_RETRY',error_type=type(error).__name__,
            observed_unix=time.time(),model_calls=0,provider_calls=0)
    common.write(operation/'PUBLIC_METADATA.json',result)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':
    main()

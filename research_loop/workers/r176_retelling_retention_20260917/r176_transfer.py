"""Fixed C2 closure transport using reviewed exact-stream and disk primitives."""

import argparse
import json
import os
from pathlib import Path
import struct
import sys
import time

import preparation_io as common
import reviewed_prep_common as reviewed


REVIEWED_SHA = 'f6751d157bb283627a185ecf14321d571673512b61f17aedac3b056ef5410aee'
FIXED_COMPLETE_SHA = 'c7ec6afb15ebf082f78867fd2f459441b2a22a300b2e9c982ef455e26d2896de'
CAPTURE = common.REMOTE/'source_capture2/capture'
REQUIRED = {'COMMIT.original.json','MANIFEST.json','BIRTH.private.json','TRAIN_WITNESSES.private.json',
    'BOUNDARY.json','evidence/CUSTODY.json','evidence/ORIGINAL_PLAN.private.json','evidence/JOURNAL.json',
    'evidence/BIRTH_RECORD.private.json','evidence/BIRTH_INTENT.json','evidence/INITIAL_COMMIT.json',
    'evidence/SLEEP_RECORD.private.json','evidence/SLEEP_INTENT.json'}


class DiskLedger(reviewed.DiskLedger):
    CAPS = dict(receiving=2*common.GIB)


class AllowanceLedger:
    def __init__(self, reader):
        self.reader = reader

    def reserve(self, operation, life_id, kind, amount):
        common.require(life_id == 'C2', 'exact_transfer_life')
        self.reader.charge(operation, kind, amount)


def validate_complete(raw):
    common.require(common.sha(raw) == FIXED_COMPLETE_SHA, 'source_complete_exact_bytes')
    document = json.loads(raw)
    common.require(document['status'] == 'FIXED_C2_SLEEP33_SOURCE_CAPTURE_VERIFIED' and
        document['scope_sha256'] == common.SCOPE_SHA and document['proposal_sha256'] == common.PINS['PROPOSAL.json']
        and document['slots_sha256'] == common.PINS['SLOTS.json'] and document['life_id'] == 'C2'
        and document['sleep'] == 33 and document['model_calls'] == document['provider_calls'] == 0,
        'fixed_capture_scope_identity')
    files = document['files']
    common.require(REQUIRED <= set(files) and 15 <= len(files) <= 24, 'complete_private_source_closure')
    for name, reference in files.items():
        path = Path(name)
        common.require(name in REQUIRED or (len(path.parts) == 2 and path.parts[0] == 'adapter'
            and path.name not in ('.','..')), 'closure_member_allowlist')
        common.require(reference['path'] == str(CAPTURE/path) and type(reference['bytes']) is int
            and 0 <= reference['bytes'] <= (128 if name.startswith('adapter/') else 32)*common.MIB
            and isinstance(reference['sha256'],str) and len(reference['sha256']) == 64, 'bounded_source_member')
    common.require(sum(value['bytes'] for name,value in files.items() if name.startswith('adapter/'))
        <= 128*common.MIB, 'fixed_adapter_size')
    return document


def validate_closure(metadata, complete):
    from c2_capture import BASE, COMMIT_SHA, RECORD_SHA, validate_sleep
    commit = json.loads(metadata['COMMIT.original.json'])
    common.require(common.sha(metadata['COMMIT.original.json']) == COMMIT_SHA and
        commit['base_sha256'] == BASE and commit['schema'] == 'R125_NATIVE_CONTINUITY_V1', 'original_native_commit')
    inventory = {name.split('/',1)[1]:reference['sha256'] for name,reference in complete['files'].items()
        if name.startswith('adapter/')}
    common.require(inventory == commit['adapter_files'] and common.digest(inventory) == commit['checkpoint_sha256']['adapter'],
        'complete_adapter_inventory_binding')
    common.require(json.loads(metadata['MANIFEST.json']) == dict(schema='R130_CHECKPOINT_MANIFEST_V1',
        adapter_path='adapter',commit_path='COMMIT.original.json',commit_sha256=COMMIT_SHA), 'native_manifest_original_bytes')
    context = json.loads(metadata['BIRTH.private.json'])
    common.require(set(context) == {'system_prompt','birth_prompt'}, 'empty_history_original_context')
    original = json.loads(metadata['evidence/BIRTH_RECORD.private.json'])
    state = original['document']['state']
    common.require(original['index'] == 0 and original['kind'] == 'COMMITTED' and
        original['document']['kind'] == 'BIRTH' and not state['state']['rows'] and
        state['sha256'] == common.digest(state['state']) and
        all(state['state']['history'][field] == context[field] for field in context), 'copied_birth_state_join')
    record_raw = metadata['evidence/SLEEP_RECORD.private.json']
    common.require(common.sha(record_raw) == RECORD_SHA, 'selected_sleep_record')
    history = validate_sleep(json.loads(record_raw),commit,context)
    witness = json.loads(metadata['TRAIN_WITNESSES.private.json'])
    expected = [dict(event_index=index,text=event['text'],text_sha256=common.sha(event['text'].encode()))
        for index,event in enumerate(history['events']) if event.get('actor') == 'child']
    common.require(witness['witnesses'] == expected and witness['context'] == context and
        witness['parent_access'] is False, 'exact_child_only_witness')


def verify_authorities(authorities, read_pass):
    for kind in ('metadata','adapter'):
        entry = authorities[kind]
        common.require(common.digest(entry['document']) == entry['reference']['sha256'] and
            entry['document']['status'] == 'PRECHARGED_NO_REFUND' and
            entry['document']['scope_sha256'] == common.SCOPE_SHA and entry['document']['kind'] == kind and
            entry['document']['life_id'] == 'C2', 'explicit_global_precharge')
    common.require(authorities['adapter']['document']['read_pass'] == read_pass and
        authorities['adapter']['document']['sleep'] == 33, 'distinct_named_transfer_pass')


def export(request, operation):
    verify_authorities(request['export_allowances'],'source_export')
    reader = common.Reader(operation,request['export_allowances'],[CAPTURE/'COMPLETE.json'])
    common.write(operation/'ONCE.json',dict(started_unix=time.time(),model_calls=0,provider_calls=0))
    raw = reader.raw(CAPTURE/'COMPLETE.json')
    complete = validate_complete(raw)
    output = sys.stdout.buffer
    output.write(struct.pack('!Q',len(raw)))
    output.write(raw)
    metadata = {}
    for name, reference in sorted(complete['files'].items()):
        source = CAPTURE/name
        reader.allowed_paths.add(source)
        kind = 'adapter' if name.startswith('adapter/') else 'metadata'
        raw = reader.raw(source,kind,128*common.MIB if kind == 'adapter' else 32*common.MIB)
        common.require(len(raw) == reference['bytes'] and common.sha(raw) == reference['sha256'], 'export_member_hash')
        if kind == 'metadata':
            metadata[name] = raw
        output.write(raw)
    validate_closure(metadata,complete)
    output.write(b'R176END1')
    output.flush()
    result = dict(status='FIXED_C2_SLEEP33_EXPORT_COMPLETE',observed_unix=time.time(),model_calls=0,provider_calls=0,
        charged_bytes=reader.charged,actual_bytes=reader.actual,files=len(complete['files']))
    common.write(operation/'EXPORT_PUBLIC_METADATA.json',result)
    print(json.dumps(result,sort_keys=True),file=sys.stderr)


def receive(request):
    verify_authorities(request['receive_allowances'],'receiver_stream')
    root = common.REMOTE
    disk = DiskLedger(root,'receiving')
    operation = root/'receiving_transfers/C2_000033'
    with reviewed.lock(disk.directory/'disk.lock'):
        operation.mkdir(parents=True,mode=0o700,exist_ok=False)
        common.write(operation/'ONCE.json',dict(life_id='C2',sleep=33,started_unix=time.time(),no_retry=True))
        try:
            disk._reserve_locked(str(operation)+':control',2*common.MIB)
        except BaseException as error:
            common.write(operation/'FAILED.json',dict(status='FAILED_TRANSFER_PRESERVED_NO_RETRY',error_type=type(error).__name__))
            raise
    try:
        accounting = common.Reader(operation,request['receive_allowances'],[])
        stream = reviewed.ChargedStream(sys.stdin.buffer.raw,AllowanceLedger(accounting),'C2','receive1')
        size = struct.unpack('!Q',stream.exact(8))[0]
        common.require(0 < size <= common.MIB, 'bounded_capture_header')
        raw = stream.exact(size)
        complete = validate_complete(raw)
        payload_bytes = sum(((entry['bytes']+4095)//4096)*4096 for entry in complete['files'].values())+16*common.MIB
        common.require(payload_bytes+2*common.MIB <= request['storage_allowance']['document']['bytes'],
            'precharged_receiver_storage')
        disk.reserve(str(operation)+':payload',payload_bytes)
        common.write(operation/'SOURCE_COMPLETE.json',raw)
        destination = operation/'payload'
        destination.mkdir(mode=0o700)
        metadata = {}
        for name, reference in sorted(complete['files'].items()):
            kind = 'adapter' if name.startswith('adapter/') else 'metadata'
            raw = stream.exact(reference['bytes'],kind)
            common.require(common.sha(raw) == reference['sha256'], 'receiving_member_hash')
            common.write(destination/name,raw)
            if kind == 'metadata':
                metadata[name] = raw
        common.require(stream.exact(8) == b'R176END1','complete_transport_trailer')
        accounting.charge('transport_EOF','metadata',1)
        common.require(sys.stdin.buffer.raw.read(1) == b'', 'no_extra_transport_members')
        validate_closure(metadata,complete)
        result = dict(status='FIXED_C2_SLEEP33_RECEIVING_COPY_VERIFIED',life_id='C2',sleep=33,
            observed_unix=time.time(),model_calls=0,provider_calls=0,payload_path=str(destination),
            original_complete_sha256=FIXED_COMPLETE_SHA,charged_bytes=accounting.charged,
            wire_bytes_read=stream.bytes,files=len(complete['files']),receiving_CPU_pass=False,
            execution_authorized=False)
        common.write(operation/'PUBLIC_METADATA.json',result)
        common.write(operation/'COMPLETE.json',dict(status='RECEIVING_COPY_COMPLETE',source_complete_sha256=FIXED_COMPLETE_SHA,
            payload_path=str(destination),files=complete['files'],parent_access=False,observed_unix=time.time()))
        print(json.dumps(result,sort_keys=True))
    except BaseException as error:
        common.write(operation/'FAILED.json',dict(status='FAILED_TRANSFER_PRESERVED_NO_RETRY',error_type=type(error).__name__))
        raise


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('mode',choices=('export','receive'))
    parser.add_argument('--request',required=True)
    arguments = parser.parse_args()
    common.require(common.sha(Path(reviewed.__file__).read_bytes()) == REVIEWED_SHA, 'reviewed_component_source_pin')
    request = json.loads(Path(arguments.request).read_bytes())
    if arguments.mode == 'export':
        export(request,Path(arguments.request).parent)
    else:
        receive(request)


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps(dict(status='FAILED_TRANSFER_PRESERVED_NO_RETRY',error_type=type(error).__name__,
            reason=str(error) if isinstance(error,ValueError) else 'TRANSFER_FAILURE',
            observed_unix=time.time(),model_calls=0,provider_calls=0)),file=sys.stderr)
        sys.exit(2)

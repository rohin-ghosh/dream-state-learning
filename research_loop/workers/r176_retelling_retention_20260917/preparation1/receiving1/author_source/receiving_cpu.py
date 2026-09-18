"""Actual receiver-only CPU proof; no model load, provider, scheduler or GPU."""

import hashlib
import io
import json
import os
from pathlib import Path
import socket
import sys
import time
import unittest

import preparation_io as common


def main():
    os.umask(0o077)
    source = Path(__file__).resolve().parent
    root = source.parent
    operation = common.REMOTE/'receiving_cpu1'
    operation.mkdir(mode=0o700,exist_ok=False)
    request = json.loads((root/'REQUEST.json').read_bytes())
    common.write(operation/'ONCE.json',dict(started_unix=time.time(),model_calls=0,provider_calls=0))
    reader = common.Reader(operation,request['cpu_allowances'],[])
    busy = False

    def audit(event,arguments):
        nonlocal busy
        if busy or event != 'open' or not arguments or not isinstance(arguments[0],(str,bytes)):
            return
        path = Path(os.fsdecode(arguments[0])).absolute()
        mode = arguments[1] if len(arguments)>1 else None
        if isinstance(mode,str) and any(marker in mode for marker in ('w','a','x','+')):
            return
        if not (path.is_relative_to(source) or path.is_relative_to(common.REMOTE/'receiving_transfers')):
            return
        if not path.exists() or not path.is_file():
            return
        busy = True
        try:
            common.require(path == path.resolve(), 'CPU_read_exact_path')
            kind = 'adapter' if '/payload/adapter/' in str(path) else 'metadata'
            reader.charge(path,kind,path.stat().st_size)
        finally:
            busy = False

    sys.addaudithook(audit)
    common.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and
        common.sha(socket.gethostname().encode()) == '0e183169e60b06badac84e0eca6036a53b7ad90c433b8cd69b2a9aaf9159389b',
        'actual_node2_CPU_only')
    for name, checksum in request['source_pins'].items():
        common.require(common.sha((source/name).read_bytes()) == checksum,'frozen_receiving_source')
    from gpu import orch_r130_checkpoint_benchmark as native
    from gpu import orch_r167_fleet_eval as prior
    import c2_capture
    common.require(Path(native.__file__).resolve() == source/'gpu/orch_r130_checkpoint_benchmark.py' and
        Path(prior.__file__).resolve() == source/'gpu/orch_r167_fleet_eval.py' and
        common.sha(Path(prior.__file__).read_bytes()) == '383415b6b37f8ff237c95b053439f6919f7ee47c452b3ffd015e606ff1962011',
        'unchanged_generator_actual_import_path')
    payload = common.REMOTE/'receiving_transfers/C2_000033/payload'
    complete = json.loads((payload.parent/'COMPLETE.json').read_bytes())
    common.require(complete['status'] == 'RECEIVING_COPY_COMPLETE', 'receiving_complete_before_CPU')
    manifest = json.loads((payload/'MANIFEST.json').read_bytes())
    checkpoint = native.verify_checkpoint(manifest,payload)
    common.require(checkpoint['commit_sha256'] == c2_capture.COMMIT_SHA and checkpoint['base_sha256'] == c2_capture.BASE,
        'actual_native_checkpoint_verifier')
    context = json.loads((payload/'BIRTH.private.json').read_bytes())
    common.require(set(context) == {'system_prompt','birth_prompt'},'actual_birth_only_context')
    for prompt in prior.queue.PROBES:
        messages = prior.protocol.messages(context,prompt)
        common.require(len(messages) == 3 and [entry['content'] for entry in messages] ==
            [context['system_prompt'],context['birth_prompt'],prompt], 'actual_independent_empty_context')
    rubric = common.write(operation/'RUBRIC.private.json',dict(methods=prior.METHODS,parent_access=False,
        provider_calls=0,source_generator_sha256=common.sha(Path(prior.__file__).read_bytes()),
        frozen_unix=time.time(),budget_authority='R176_SEPARATE_NOT_LEGACY_METHODS_CALL_CAP'))
    suite = unittest.defaultTestLoader.loadTestsFromNames(['test_candidate','test_preparation_io','test_r176_transfer',
        'tests.test_orch_r167_fleet_eval'])
    output = io.StringIO()
    tests = unittest.TextTestRunner(stream=output,verbosity=2).run(suite)
    log = common.write(operation/'CPU_TESTS.txt',output.getvalue().encode())
    result = dict(status='ACTUAL_C2_SLEEP33_RECEIVING_CPU_PASS' if tests.wasSuccessful() else 'RECEIVING_CPU_TEST_FAILURE',
        observed_unix=time.time(),life_id='C2',sleep=33,tests_run=tests.testsRun,
        failures=len(tests.failures),errors=len(tests.errors),charged_bytes=reader.charged,
        original_native_verifier_pass=True,original_birth_context_pass=True,private_rubric_ref=rubric,
        source_freeze=request['source_pins'],python=request['runtime']['python'],
        python_sha256=request['runtime']['python_sha256'],CPU_output=log,
        model_calls=0,provider_calls=0,execution_authorized=False,independent_integration_review_pending=True)
    common.write(operation/'PUBLIC_METADATA.json',result)
    print(json.dumps({key:value for key,value in result.items() if key != 'source_freeze'},sort_keys=True))
    return 0 if tests.wasSuccessful() else 2


if __name__=='__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print(json.dumps(dict(status='RECEIVING_CPU_FAILURE_PRESERVED_NO_RETRY',error_type=type(error).__name__,
            reason=str(error) if isinstance(error,ValueError) else 'CPU_PROOF_FAILURE',
            model_calls=0,provider_calls=0,observed_unix=time.time())))
        sys.exit(2)

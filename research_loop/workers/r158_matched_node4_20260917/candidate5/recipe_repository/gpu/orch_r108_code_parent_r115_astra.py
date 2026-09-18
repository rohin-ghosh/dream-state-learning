"""F3 CODE Astra counterpart using the existing qualified provider transport."""

import argparse
import json
from pathlib import Path
import time
from types import FunctionType

from gpu import orch_r110_claude_broker as transport
from gpu import orch_route_parent_campaign_providers as existing
from gpu import orch_r118_astra_slots as http_slots


MODEL = existing.STRONG


def parse(envelope, task_id=''):
    transport.require(envelope.get('model') == MODEL and envelope.get('status') == 'completed'
                      and not envelope.get('error') and bool(envelope.get('usage')), 'actual_astra_completed')
    transport.require(all(item.get('type') in ('reasoning', 'message') for item in envelope.get('output', [])),
                      'no_tools_in_parent')
    texts = [part['text'] for item in envelope.get('output', []) if item.get('type') == 'message'
             for part in item.get('content', []) if part.get('type') == 'output_text']
    transport.require(len(texts) == 1, 'one_parent_text')
    text = texts[0].strip()
    if text.startswith('```json\n') and text.endswith('\n```'):
        text = text[8:-4]
    reply = '[SILENT]' if text == '[SILENT]' else transport.loads(text)
    plan, metadata = transport.adapt_plan(reply, 'code', task_id)
    return dict(status='SILENT' if metadata['silent'] else 'COMPLETE', plan=plan,
                parent_metadata=metadata, actual_model=MODEL, usage=envelope['usage'])


def authorize(config, launch, now):
    transport.require(launch.get('authorized') is True
        and launch.get('authorization') == 'BUILDER_PUBLISHED_PAIRED_ASTRA'
        and launch.get('config_sha256') == transport.digest(config)
        and bool(launch.get('source_reference'))
        and launch.get('not_before_unix', now+1) <= now < config['deadline_unix'],
        'explicit_astra_counterpart_publication')


def evaluate(request, directory, deadline, *, config, launch, prompt_root, principles_path,
             runner=None, memory=transport.backend.available_memory, slot_root=http_slots.ROOT):
    transport.validate_config(config)
    transport.require(config['branch'] == 'F3' and config['family'] == 'code', 'F3_code_only')
    authorize(config, launch, time.time())
    directory = Path(directory)
    transport.require(directory.resolve().is_relative_to(Path('/tmp')), 'bounded_tmp_packet_only')
    directory.mkdir(parents=True, exist_ok=False)
    transport.write(directory/'REQUEST.json', request)
    result = None
    dispatched = False
    binding = None
    try:
        transcript = transport.validate_request(request, config)
        cutoff = min(deadline, config['deadline_unix'], request['lane_deadline_unix']-30)
        with http_slots.acquire(cutoff, root=slot_root) as slot_receipt:
            transport.write(directory/'HTTP_SLOT.json', slot_receipt)
            transport.require(memory() >= config.get('min_available_bytes', transport.backend.MIN_AVAILABLE_BYTES),
                              'vm_memory_floor')
            system, prompt_bytes, binding = transport.build_system(transcript, config, prompt_root, principles_path)
            (directory/'PARENT_PROMPT.md').write_bytes(prompt_bytes)
            (directory/'SYSTEM.txt').write_text(system)
            transport.write(directory/'PROMPT_BINDING.json', binding)
            transport.require(time.time() < cutoff, 'parent_cutoff_no_dispatch')
            authorize(config, launch, time.time())
            if runner is None:
                runner = FunctionType(existing.strong.__code__, dict(existing.strong.__globals__, parse_strong=lambda envelope: parse(envelope, transcript['task_id'])),
                                      existing.strong.__name__, existing.strong.__defaults__)
            dispatched = True
            result = runner('Respond to the supplied TRAIN transcript using the transport contract.',
                            directory, cutoff, system)
            transport.require(time.time() < cutoff, 'late_parent_missing')
    except (ValueError, RuntimeError, OSError) as error:
        result = dict(status='MISSING', plan=None, parent_metadata=None, actual_model=None,
                      error=dict(type=type(error).__name__, code='captured_failure_no_retry'))
    result.update(id=request.get('id'), request_sha256=transport.digest(request),
                  payload_sha256=request.get('payload_sha256'), lane_deadline_unix=request.get('lane_deadline_unix'),
                  provider_dispatched=dispatched, retry=False, finished_unix=time.time(), prompt_binding=binding)
    transport.write(directory/'RESULT.json', result)
    return result


def serve(config_path, launch_path, prompt_root, principles_path):
    namespace = dict(transport.serve.__globals__, evaluate=evaluate, validate_launch=authorize)
    namespace['process_request'] = FunctionType(transport.process_request.__code__, namespace,
                                               'process_request', transport.process_request.__defaults__)
    serve_bound = FunctionType(transport.serve.__code__, namespace, 'serve', transport.serve.__defaults__)
    return serve_bound(config_path, launch_path, prompt_root, principles_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--launch-receipt', type=Path, required=True)
    parser.add_argument('--prompt-root', type=Path, required=True)
    parser.add_argument('--principles', type=Path, required=True)
    arguments = parser.parse_args()
    serve(arguments.config, arguments.launch_receipt, arguments.prompt_root, arguments.principles)

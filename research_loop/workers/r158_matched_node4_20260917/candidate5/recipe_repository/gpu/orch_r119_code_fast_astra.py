"""Independent A3 short low-effort HTTP parents; no child wait or shared session."""

import argparse
import inspect
from pathlib import Path
import shlex
import time
from types import FunctionType

from gpu import orch_r108_code_parent_r118_astra_shared as inherited


def fast_runner(provider, task_id):
    source = inspect.getsource(provider.existing.strong)
    replacements = {'max_output_tokens=4096': 'max_output_tokens=512',
        "reasoning=dict(effort=config['model_reasoning_effort'])": "reasoning=dict(effort='low')",
        'maximum_output_tokens=4096': 'maximum_output_tokens=512'}
    for before, after in replacements.items():
        provider.transport.require(source.count(before) == 1, 'exact_existing_HTTP_budget_binding')
        source = source.replace(before, after)
    namespace = dict(provider.existing.strong.__globals__,
        parse_strong=lambda envelope: provider.parse(envelope, task_id))
    exec(compile(source, __file__ + ':bounded_HTTP', 'exec'), namespace)
    return namespace['strong']


def queue_listing(root):
    return ('find ' + shlex.quote(str(Path(root) / 'parent_queue'))
        + ' -maxdepth 1 -type f -name "*.request.json" -printf "%f\\n"')


def pending_listing(root):
    source = ('from pathlib import Path;root=Path(' + repr(str(Path(root) / 'parent_queue')) +
        ');print("\\n".join(sorted(path.name for path in root.glob("*.request.json") '
        'if not path.with_name(path.name.removesuffix(".request.json")+".response.json").exists())))')
    return 'python3 -c ' + shlex.quote(source)


def serve(config_path, launch_path, definition_path, definition_sha256, prompt_root, principles_path):
    provider = inherited.astra
    transport = provider.transport
    config = transport.loads(Path(config_path).read_text())
    launch = transport.loads(Path(launch_path).read_text())
    root = Path(config['remote_root'])
    transport.require(root == inherited.ROOT and config['max_output_tokens'] == 512,
        'same_A3_short_intervention_budget')
    store = transport.Store(transport.ROOT)
    transport.require(store.hash(definition_path) == definition_sha256, 'exact_independent_definition')
    document = transport.loads(store.shell('cat ' + shlex.quote(str(definition_path))).stdout)
    service = Path(document['service'])
    transport.require(document['schema'] == 'R119_CODE_INDEPENDENT_ELICITATION_V1'
        and document['root'] == str(root) and document['shared_barrier'] is False
        and document['optimizer_updates'] == 0 and document['parent_nonblocking'] is True
        and config['deadline_unix'] == document['train_end_unix'], 'explicit_independent_parent_scope')

    def evaluate(request, directory, deadline, **kwargs):
        if request.get('payload', {}).get('phase') != 'experience':
            directory = Path(directory)
            directory.mkdir(parents=True, exist_ok=False)
            result = dict(id=request['id'], status='MISSING', plan=None, parent_metadata=None,
                actual_model=None, provider_dispatched=False, retry=False,
                request_sha256=transport.digest(request), payload_sha256=request['payload_sha256'],
                lane_deadline_unix=request['lane_deadline_unix'], finished_unix=time.time(),
                error=dict(code='PER_EPISODE_ONLY_NO_PROVIDER_FOR_AUXILIARY_PHASE'))
            transport.write(directory / 'REQUEST.json', request)
            transport.write(directory / 'RESULT.json', result)
            return result
        return provider.evaluate(request, directory, deadline,
            runner=fast_runner(provider, request['payload']['task_id']), **kwargs)

    def mapped(path):
        path = Path(path)
        if path in (root / 'TERMINAL.json', root / 'SHARED_TERMINAL.json'):
            return service / 'GUARD_TERMINAL.json'
        if path == root / 'parent_claude/CONFIG.json':
            return service / 'FAST_ASTRA_LEDGER_CONFIG.json'
        return path

    class Store(transport.Store):
        def exists(self, path):
            return super().exists(mapped(path))

        def hash(self, path):
            return super().hash(mapped(path))

        def copy(self, source, destination):
            if str(destination).startswith('NODE:'):
                destination = 'NODE:' + str(mapped(str(destination)[5:]))
            return super().copy(source, destination)

        def shell(self, script, check=True):
            if script == queue_listing(root):
                script = pending_listing(root)
            return super().shell(script, check=check)

    provider.authorize(config, launch, time.time())
    namespace = dict(transport.serve.__globals__, evaluate=evaluate,
        validate_launch=provider.authorize, Store=Store)
    namespace['process_request'] = FunctionType(transport.process_request.__code__, namespace,
        'process_request', transport.process_request.__defaults__)
    FunctionType(transport.serve.__code__, namespace, 'serve', transport.serve.__defaults__)(
        config_path, launch_path, prompt_root, principles_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'launch-receipt', 'definition', 'prompt-root', 'principles'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--definition-sha256', required=True)
    args = parser.parse_args()
    serve(args.config, args.launch_receipt, args.definition, args.definition_sha256,
        args.prompt_root, args.principles)

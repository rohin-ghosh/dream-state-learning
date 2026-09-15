"""Prospective low-effort Astra sidecar for independent nonblocking A4."""

import importlib.util
from pathlib import Path


def source():
    path = Path(__file__).with_name('orch_r119_grid_shared_parent.py')
    spec = importlib.util.spec_from_file_location('previous_shared_parent', path)
    previous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    text = previous.source()
    changes = {
        "('shared_continuation_r119',)": "('independent_r119_v1',)",
        "('R119_GRID_SHARED_TERMINAL.json',)": "('R119_GRID_INDEPENDENT_TERMINAL.json',)",
        "config['max_parent_calls'] == 298": "config['max_parent_calls'] == ready['parent_cap']",
        '"config[\'model_reasoning_effort\']", "\'high\'"':
            '"config[\'model_reasoning_effort\']", "\'low\'"',
        '    strong_source = inspect.getsource(astra.existing.strong)':
            '    strong_source = inspect.getsource(astra.existing.strong)\n'
            '    strong_source = replace_one(strong_source, "max_output_tokens=4096", "max_output_tokens=1024")\n'
            '    strong_source = replace_one(strong_source, "maximum_output_tokens=4096", "maximum_output_tokens=1024")',
        '    def evaluate(*values, **kwargs):\n        return http.evaluate(*values, **kwargs, runner=strong_namespace[\'strong\'])':
            '    def evaluate(request, directory, deadline, **kwargs):\n'
            '        if request.get("payload", {}).get("phase") != "experience":\n'
            '            transport.validate_request(request, kwargs["config"])\n'
            '            directory = Path(directory)\n'
            '            directory.mkdir(parents=True, exist_ok=False)\n'
            '            transport.write(directory / "REQUEST.json", request)\n'
            '            result = dict(id=request["id"], status="MISSING", plan=None, parent_metadata=None,\n'
            '                actual_model=None, provider_dispatched=False, retry=False,\n'
            '                request_sha256=transport.digest(request), payload_sha256=request["payload_sha256"],\n'
            '                lane_deadline_unix=request["lane_deadline_unix"], finished_unix=transport.time.time(),\n'
            '                error=dict(code="non_episode_cadence_skip_no_provider_call"))\n'
            '            transport.write(directory / "RESULT.json", result)\n'
            '            return result\n'
            '        return http.evaluate(request, directory, deadline, **kwargs, runner=strong_namespace["strong"])',
        "        return original(store, config, launch, name, buffer, prompt_root, principles_path)":
            "        if store.exists(root / 'parent_claude' / (identifier + '.claim')):\n"
            "            return 'EXISTING_CLAIM_NO_RETRY'\n"
            "        return original(store, config, launch, name, buffer, prompt_root, principles_path)",
    }
    for before, after in changes.items():
        if text.count(before) != 1:
            raise ValueError('exact_fast_parent_delta')
        text = text.replace(before, after)
    return text


if __name__ == '__main__':
    exec(compile(source(), __file__, 'exec'), {'__name__': '__main__', '__file__': __file__})

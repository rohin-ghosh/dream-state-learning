import argparse
import ast
import gc
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback


EXPECTED_UUID = "GPU-ff5f84e9-c70e-272d-a8e0-eb20aad05ac6"
REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
BINDING = Path("/tmp/astra_qwen_public_binding_receipt_20260913_attempt1.json")
BINDING_SHA256 = "e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019"
TOOLS = Path("/tmp/astra_a100_toolchain_smoke_20260913.py")
TOOLS_SHA256 = "fd0628c850dd76c53b8660b83f9e1fac6a13460a569c1deb61b12d904e828c2e"
RUNTIME = Path("/tmp/astra_level1_skill_run_20260913.py")
RUNTIME_SHA256 = "6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e"
PUBLIC = Path("/tmp/astra_birth_skill_probe_run_20260913.py")
PUBLIC_SHA256 = "59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c"
MESSAGES = [{"role": "user", "content": "Please reply with OK."}]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pinned_module(path, pin, name):
    require(digest(path) == pin, "helper source pin mismatch")
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def runtime_settings():
    require(digest(RUNTIME) == RUNTIME_SHA256, "Level1 runtime source pin mismatch")
    settings = {}
    for node in ast.parse(RUNTIME.read_text()).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ("ENGINE", "PARAMS"):
                require(name not in settings and isinstance(node.value, ast.Call) and
                        isinstance(node.value.func, ast.Name) and node.value.func.id == "dict" and
                        not node.value.args and all(keyword.arg for keyword in node.value.keywords),
                        "unsupported runtime constant schema")
                settings[name] = {keyword.arg: ast.literal_eval(keyword.value) for keyword in node.value.keywords}
    require(set(settings) == {"ENGINE", "PARAMS"}, "runtime settings absent")
    settings["PARAMS"]["max_tokens"] = 4
    return settings["ENGINE"], settings["PARAMS"]


def read_binding():
    require(digest(BINDING) == BINDING_SHA256, "official binding receipt pin mismatch")
    binding = json.loads(BINDING.read_text())
    require(binding["repository"] == "Qwen/Qwen2.5-7B-Instruct" and
            binding["revision"] == REVISION and binding["file_count"] == len(binding["files"]) == 14,
            "official 14-file binding identity differs")
    return binding


def verify_model_files(model, binding):
    rows = {}
    for name, expected in binding["files"].items():
        require(Path(name).name == name and name not in (".", ".."), "unsafe model filename")
        path = model / name
        row = {"expected_sha256": expected["sha256"], "expected_size": expected["size"], "match": False}
        rows[name] = row
        try:
            before = path.stat()
            actual = digest(path)
            after = path.stat()
            stable = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (
                after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
            row.update(sha256=actual, size=after.st_size, stable=stable,
                       match=stable and actual == expected["sha256"] and after.st_size == expected["size"])
        except OSError as error:
            row["error_type"] = type(error).__name__
    return dict(files=rows, expected_file_count=14,
                all_match=len(rows) == 14 and all(row["match"] for row in rows.values()))


def check_response(outputs, prompt_tokens):
    require(len(outputs) == 1 and len(outputs[0].outputs) == 1, "readout cardinality differs")
    response = outputs[0].outputs[0]
    tokens = list(response.token_ids)
    require(1 <= len(tokens) <= 4 and all(type(token) is int and token >= 0 for token in tokens),
            "readout token count/type differs")
    require(list(outputs[0].prompt_token_ids) == prompt_tokens, "actual prompt tokens differ")
    require(isinstance(response.text, str) and response.finish_reason in ("stop", "length"),
            "readout text/finish status differs")
    return dict(text=response.text, output_token_ids=tokens, output_tokens=len(tokens),
                actual_prompt_token_ids=list(outputs[0].prompt_token_ids),
                finish_reason=response.finish_reason, stop_reason=response.stop_reason,
                lora_request=None, semantic_scoring=False)


def run_native(model, engine, params, probe, output, support, record):
    import torch
    from vllm import LLM, SamplingParams

    require(torch.cuda.is_available() and torch.cuda.device_count() == 1, "exactly one CUDA device required")
    properties = torch.cuda.get_device_properties(0)
    runtime_uuid = str(properties.uuid)
    if not runtime_uuid.startswith("GPU-"):
        runtime_uuid = "GPU-" + runtime_uuid
    require(runtime_uuid == EXPECTED_UUID and "A100" in properties.name, "runtime GPU identity differs")
    model_instance = None
    try:
        record["phase"] = "OFF_engine_load"
        model_instance = LLM(model=str(model), tokenizer=str(model), **engine)
        tokenizer = model_instance.get_tokenizer()
        expected_template = json.loads((model / "tokenizer_config.json").read_text())["chat_template"]
        require(tokenizer.chat_template == expected_template, "bound chat template differs")
        request = probe.render(tokenizer, MESSAGES)
        support.write_json(output / "request.json", dict(messages=MESSAGES, **request, lora_request=None))
        record["phase"] = "OFF_four_token_readout"
        with torch.inference_mode():
            outputs = model_instance.generate([request["rendered_prompt"]], SamplingParams(**params),
                                              lora_request=None, use_tqdm=False)
        response = check_response(outputs, request["prompt_token_ids"])
        support.write_json(output / "response.json", response)
        return dict(route="OFF", model_loads=1, generation_calls=1,
                    output_tokens=response["output_tokens"], max_tokens=4, semantic_scoring=False)
    finally:
        if model_instance is not None:
            shutdown = getattr(model_instance, "shutdown", None)
            record["engine_shutdown_method_available"] = callable(shutdown)
            if callable(shutdown):
                shutdown()
            del model_instance
            gc.collect()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Main-only OFF model readiness; requires external <=600s process-group timeout.")
    parser.add_argument("--allow-gpu", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args(argv)
    if not arguments.allow_gpu or os.environ.get("CUDA_VISIBLE_DEVICES") != EXPECTED_UUID:
        print(json.dumps({"status": "REFUSED", "reason": "explicit --allow-gpu and exact GPU0 UUID required"}))
        return 2
    try:
        support = pinned_module(TOOLS, TOOLS_SHA256, "a100_readiness_tools")
    except Exception as error:
        print(json.dumps({"status": "REFUSED", "error_type": type(error).__name__}))
        return 2
    output = arguments.output.resolve()
    try:
        output.mkdir(mode=0o700)
    except OSError as error:
        print(json.dumps({"status": "REFUSED", "error_type": type(error).__name__}))
        return 2
    record = dict(status="RUNNING_NOT_RESULT", started_utc=support.timestamp(), phase="preflight",
                  gpu_uuid=EXPECTED_UUID, script_sha256=digest(__file__), infrastructure_only=True,
                  scientific_pass=None, route="OFF", required_external_cap_seconds=600)
    support.write_json(output / "started.json", record)
    home = Path.home()
    model = home / ".cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots" / REVISION
    try:
        require(Path(sys.prefix).resolve() == (home / "v2/venv").resolve(), "use existing v2 venv interpreter")
        require(not any(name in sys.modules for name in ("torch", "vllm", "flashinfer")), "native library imported before environment setup")
        engine, params = runtime_settings()
        probe = pinned_module(PUBLIC, PUBLIC_SHA256, "a100_readiness_public")
        binding = read_binding()
        before = verify_model_files(model, binding)
        support.write_json(output / "model_before.json", before)
        require(before["all_match"], "official model payload mismatch before load")
        (output / "tmp").mkdir()
        environment = support.smoke_environment(home, output)
        environment.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1")
        with support.process_environment(environment):
            tools = support.inspect_tools(dict(os.environ), home)
            support.write_json(output / "tools.json", dict(tools=tools,
                path_directories=[support.display_path(path, home) for path in environment["PATH"].split(os.pathsep)],
                cuda_home=environment["CUDA_HOME"]))
            require(all(tool["ready"] for tool in tools.values()), "toolchain lookup/version check failed")
            support.write_json(output / "identity.json", dict(
                model=support.display_path(model, home), repository=binding["repository"], revision=REVISION,
                binding_sha256=BINDING_SHA256, tool_helper_sha256=TOOLS_SHA256,
                runtime_settings_source_sha256=RUNTIME_SHA256, rendering_helper_sha256=PUBLIC_SHA256,
                engine=engine, params=params, messages=MESSAGES, lora_request=None,
                inherited_runtime_delta={"max_tokens": {"was": 192, "now": 4}}))
            with support.private_native_output(output, record):
                record["readout"] = run_native(model, engine, params, probe, output, support, record)
        record["phase"] = "post_load_payload_recheck"
        after = verify_model_files(model, binding)
        support.write_json(output / "model_after.json", after)
        require(after["all_match"], "official model payload mismatch after readout")
        record.update(status="OFF_NATIVE_READINESS_PASS", phase="complete", official_files_matched=14)
    except Exception as error:
        record.update(status="OFF_NATIVE_READINESS_FAILED", error_type=type(error).__name__,
                      error_message=support.sanitize_diagnostic(str(error)),
                      error_trace=support.sanitize_diagnostic("".join(traceback.format_exception(error))))
    record["finished_utc"] = support.timestamp()
    support.write_json(output / "result.json", record)
    print(json.dumps({"status": record["status"], "scientific_pass": None}))
    return 0 if record["status"] == "OFF_NATIVE_READINESS_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

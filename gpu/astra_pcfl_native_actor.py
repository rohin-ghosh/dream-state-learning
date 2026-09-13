"""Lazy C0-only PCFL actor; outer controller owns authorization and hard timeout.

The native path follows the frozen public probe's LLM/get_tokenizer/render/
generate pattern, without its scientific rows or fixed 192-token decode cap.
Import and construction never load a tokenizer/model or create output files.
"""

import copy
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import sys
import threading
import time
from collections.abc import Mapping


SCHEMA = "pcfl.c0_native_actor.v1"
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
ENGINE = dict(max_model_len=16384, tensor_parallel_size=1, seed=0,
              gpu_memory_utilization=0.85, enforce_eager=True, enable_lora=False,
              enable_prefix_caching=False, dtype="bfloat16", trust_remote_code=False)
SAMPLING = dict(temperature=0.0, top_p=1.0, top_k=-1, n=1,
                presence_penalty=0.0, frequency_penalty=0.0,
                repetition_penalty=1.0, ignore_eos=False)
PACKAGES = ("vllm", "torch", "transformers", "tokenizers", "safetensors", "huggingface-hub")
TOKENIZER_FILES = {"tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt"}
CONFIG_FIELDS = {"schema", "model_path", "model_binding", "source_files", "tokenizer_files",
                 "chat_template_sha256", "tokenizer_probe", "environment", "gpu_uuid", "engine",
                 "output_dir", "deadline", "device_seconds_cap", "max_input_tokens", "max_output_tokens", "max_calls"}


class ActorError(ValueError):
    pass


class _NativeOutputError(ActorError):
    def __init__(self, captures):
        super().__init__("native generation cardinality differs")
        self.captures = captures


def require(condition, message):
    if not condition:
        raise ActorError(message)


def canonical(value):
    def check(item):
        if type(item) is dict:
            require(all(type(key) is str for key in item), "non-string JSON key")
            for nested in item.values():
                check(nested)
        elif type(item) is list:
            for nested in item:
                check(nested)
        else:
            require(item is None or type(item) in (str, int, float, bool), "non-JSON value")
            require(type(item) is not float or math.isfinite(item), "nonfinite JSON value")
    check(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None, "invalid SHA256")


def number(value, positive=False):
    require(type(value) in (int, float) and math.isfinite(value) and (value > 0 if positive else value >= 0), "invalid time/cap")


def token_ids(value):
    require(isinstance(value, (list, tuple)) and all(type(token) is int and token >= 0 for token in value), "invalid token IDs")
    return list(value)


def file_signature(path):
    path = Path(path)
    link = path.lstat()
    target = path.stat()
    require(path.is_file(), "identity path is not a regular file")
    return [str(path.resolve()), link.st_dev, link.st_ino, link.st_mtime_ns,
            target.st_dev, target.st_ino, target.st_size, target.st_mtime_ns, target.st_ctime_ns]


def environment_identity():
    return {"python": str(Path(sys.executable).resolve()), "version": sys.version,
            "packages": {name: importlib.metadata.version(name) for name in PACKAGES}}


def _native_loader(config):
    for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY", "VLLM_NO_USAGE_STATS"):
        require(os.environ.get(key) == "1", "native offline/telemetry configuration missing: " + key)
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == config["gpu_uuid"], "outer single-GPU binding differs")
    from vllm import LLM, SamplingParams

    class Session:
        def __init__(self):
            self.llm = LLM(model=config["model_path"], tokenizer=config["model_path"], **config["engine"])

        @property
        def tokenizer(self):
            return self.llm.get_tokenizer()

        def generate(self, prompt, sampling):
            import torch
            with torch.inference_mode():
                outputs = self.llm.generate([prompt], SamplingParams(**sampling), lora_request=None, use_tqdm=False)
            if len(outputs) != 1 or len(outputs[0].outputs) != 1:
                captures = [{"prompt_token_ids": list(result.prompt_token_ids),
                             "outputs": [{"text": output.text, "output_token_ids": list(output.token_ids),
                                          "finish_reason": output.finish_reason, "stop_reason": output.stop_reason}
                                         for output in result.outputs]} for result in outputs]
                raise _NativeOutputError(captures)
            output = outputs[0].outputs[0]
            return {"text": output.text, "output_token_ids": list(output.token_ids),
                    "prompt_token_ids": list(outputs[0].prompt_token_ids),
                    "finish_reason": output.finish_reason, "stop_reason": output.stop_reason}

        def close(self):
            shutdown = getattr(self.llm, "shutdown", None)
            available = callable(shutdown)
            if available:
                shutdown()
            return {"shutdown_method_available": available, "shutdown_returned": available}

    return Session()


class NativeActor:
    """No release gate, collector or retries. Explicit execution starts at start,
    generate or count_tokens. Inject loader/environment_reader only for CPU tests.

    close reports engine shutdown, never asserts owned-process/GPU vacancy.
    The frozen scripted runtime is intentionally not enabled by this adapter.
    """

    scripted = False

    def __init__(self, config, *, loader=None, environment_reader=environment_identity, clock=time.monotonic):
        canonical(config)
        require(type(config) is dict and set(config) == CONFIG_FIELDS and config["schema"] == SCHEMA, "actor config schema")
        self._config = copy.deepcopy(config)
        self._config_hash = digest(config)
        self._loader = _native_loader if loader is None else loader
        self._kind = "NATIVE" if loader is None else "INJECTED_CPU_TEST"
        self._environment_reader = environment_reader
        self._clock = clock
        self._lock = threading.Lock()
        self._session = None
        self._root = None
        self._failed = False
        self._closed = False
        self._started = False
        self._ids = set()
        self._signatures = {}
        self._seconds = 0.0
        self._count_calls = 0
        self._close_receipt = None
        self._validate_config()

    def _validate_config(self):
        config = self._config
        require(config["engine"] == ENGINE, "C0 engine constants differ; LoRA/remote code prohibited")
        for name in ("model_path", "output_dir"):
            require(type(config[name]) is str and Path(config[name]).is_absolute(), "absolute path required")
        require(config["model_path"] != config["output_dir"], "output/model overlap")
        require(type(config["gpu_uuid"]) is str and config["gpu_uuid"].startswith("GPU-"), "GPU UUID required")
        for name, maximum in (("max_input_tokens", ENGINE["max_model_len"]), ("max_output_tokens", 2048), ("max_calls", 1952)):
            require(type(config[name]) is int and 0 < config[name] <= maximum, "invalid " + name)
        for name in ("deadline", "device_seconds_cap"):
            number(config[name], positive=True)
        require(config["device_seconds_cap"] <= 36000, "zero-fit inference cap exceeds v2.2")
        binding = config["model_binding"]
        require(type(binding) is dict and set(binding) == {"path", "sha256"} and Path(binding["path"]).is_absolute(), "model receipt binding")
        sha(binding["sha256"])
        require(type(config["source_files"]) is dict and str(Path(__file__).resolve()) in config["source_files"], "pin actually imported actor source")
        for path, expected in config["source_files"].items():
            require(Path(path).is_absolute(), "absolute source pin required")
            sha(expected)
        require(type(config["tokenizer_files"]) is dict and set(config["tokenizer_files"]) == TOKENIZER_FILES, "tokenizer file inventory")
        for expected in config["tokenizer_files"].values():
            sha(expected)
        sha(config["chat_template_sha256"])
        probe = config["tokenizer_probe"]
        require(type(probe) is dict and set(probe) == {"text", "token_ids"} and type(probe["text"]) is str, "tokenizer probe binding")
        token_ids(probe["token_ids"])
        env = config["environment"]
        require(type(env) is dict and set(env) == {"python", "version", "packages"}
                and set(env["packages"]) == set(PACKAGES), "environment identity schema")

    def _check(self, deadline):
        require(not self._closed and not self._failed, "actor closed/failed; no retry")
        require(digest(self._config) == self._config_hash, "actor config drift")
        now = self._clock()
        number(now)
        require(now < min(deadline, self._config["deadline"]), "actor deadline exhausted")
        require(self._seconds < self._config["device_seconds_cap"], "actor elapsed-device budget exhausted")

    def _write(self, name, payload):
        data = canonical(payload)
        destination = self._root / name
        with destination.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        return hashlib.sha256(data).hexdigest()

    def _hash_file(self, path, deadline):
        before = file_signature(path)
        hasher = hashlib.sha256()
        with Path(path).open("rb") as stream:
            while True:
                self._check(deadline)
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                hasher.update(chunk)
        require(file_signature(path) == before, "file changed during identity hash")
        self._signatures[str(path)] = before
        return hasher.hexdigest()

    def _verify_identity(self, deadline):
        config = self._config
        model = Path(config["model_path"])
        require(model.is_dir(), "local model directory missing; no remote fallback")
        for path, expected in config["source_files"].items():
            require(self._hash_file(path, deadline) == expected, "source identity drift")
        binding = config["model_binding"]
        require(self._hash_file(binding["path"], deadline) == binding["sha256"], "model receipt hash drift")
        receipt = json.loads(Path(binding["path"]).read_bytes())
        require(receipt["repository"] == MODEL_NAME and receipt["revision"] == REVISION
                and receipt["status"] == "PUBLIC_REVISION_FILES_MATCHED_PROSPECTIVE_BINDING"
                and Path(receipt["model"]).resolve() == model.resolve(), "official C0 receipt/path differs")
        files = receipt["files"]
        require(receipt["file_count"] == len(files) == 14, "official 14-file manifest required")
        actual = {str(path.relative_to(model)) for path in model.rglob("*") if path.is_file()}
        require(actual == set(files), "local model file inventory differs")
        for name, entry in files.items():
            relative = Path(name)
            require(not relative.is_absolute() and ".." not in relative.parts and "adapter" not in name.lower(), "invalid base file path")
            require(entry["public_match"] in ("GIT_BLOB_SHA1", "LFS_SHA256"), "unmatched public model file")
            sha(entry["sha256"])
            require((model / name).stat().st_size == entry["size"], "model file size drift")
            require(self._hash_file(model / name, deadline) == entry["sha256"], "model file hash drift")
        require(json.loads((model / "config.json").read_bytes()).get("model_type") == "qwen2", "wrong model architecture")
        require(all(files[name]["sha256"] == expected for name, expected in config["tokenizer_files"].items()), "tokenizer/model receipt mismatch")
        environment = self._environment_reader()
        require(environment == config["environment"], "native interpreter/package identity differs")
        return {"repository": MODEL_NAME, "revision": REVISION, "model_binding_sha256": binding["sha256"],
                "model_files": {name: entry["sha256"] for name, entry in files.items()},
                "source_files": config["source_files"], "environment": environment,
                "gpu_uuid_expected": config["gpu_uuid"], "mount": "C0", "lora_request": None,
                "clean_lineage_certified": False}

    def _unchanged_files(self):
        for path, signature in self._signatures.items():
            require(file_signature(path) == signature, "verified local file changed")

    def _start(self, deadline):
        self._check(deadline)
        if self._started:
            self._unchanged_files()
            return
        root = Path(self._config["output_dir"])
        require(not root.exists() and not root.is_symlink(), "output directory must be fresh")
        require(root.parent.is_dir() and root.parent.resolve() == root.parent, "output parent must exist without symlink aliases")
        model = Path(self._config["model_path"]).resolve()
        require(model not in root.parents and root not in model.parents, "output and model must be disjoint")
        root.mkdir()
        self._root = root
        self._write("config.json", self._config)
        started = self._clock()
        try:
            identity = self._verify_identity(deadline)
            self._write("identity.json", {"kind": self._kind, "config_sha256": self._config_hash,
                                          "pid": os.getpid(), "identity": identity})
            self._check(deadline)
            self._unchanged_files()
            load_started = self._clock()
            self._session = self._loader(copy.deepcopy(self._config))
            tokenizer = self._session.tokenizer
            require(Path(tokenizer.name_or_path).resolve() == model, "loaded tokenizer path differs")
            require(type(tokenizer.chat_template) is str and text_hash(tokenizer.chat_template) == self._config["chat_template_sha256"], "loaded chat template drift")
            probe = self._config["tokenizer_probe"]
            require(token_ids(tokenizer.encode(probe["text"], add_special_tokens=False)) == probe["token_ids"], "loaded tokenizer probe differs")
            self._unchanged_files()
            self._check(deadline)
            self._started = True
            self._write("load.json", {"operation_started": started, "model_load_started": load_started,
                                      "ready_at": self._clock(), "kind": self._kind,
                                      "mount": "C0", "lora_request": None})
        except Exception as error:
            self._failed = True
            self._write("load_error.json", {"error_type": type(error).__name__, "status": "FAILED_NO_RETRY"})
            raise

    def _acquire(self):
        require(self._lock.acquire(blocking=False), "concurrent actor calls prohibited")

    def start(self):
        self._acquire()
        started = self._clock()
        try:
            self._start(min(self._config["deadline"], started + self._config["device_seconds_cap"] - self._seconds))
        except Exception:
            self._failed = True
            raise
        finally:
            self._seconds += max(0, self._clock() - started)
            self._lock.release()

    def _request(self, request, limits):
        canonical(request)
        require(type(request) is dict and set(request) == {"id", "messages", "seed", "mount"}, "public request fields only")
        require(type(request["id"]) is str and bool(request["id"]) and len(request["id"]) <= 512, "request ID required")
        require(request["mount"] == "C0", "only C0 mount is permitted")
        require(type(request["seed"]) is int and 0 <= request["seed"] < 2**63, "invalid request seed")
        messages = request["messages"]
        require(type(messages) is list and len(messages) >= 2 and len(messages) % 2 == 0, "system and alternating public history required")
        for index, message in enumerate(messages):
            role = "system" if index == 0 else "user" if index % 2 else "assistant"
            require(type(message) is dict and set(message) == {"role", "content"} and message["role"] == role
                    and type(message["content"]) is str and bool(message["content"]), "public message fields/order differ")
        fields = {"output_tokens", "returned_tokens", "remaining_reads", "deadline", "device_seconds"}
        require(type(limits) is dict and fields <= set(limits) <= fields | {"input_tokens"}, "runtime limits schema")
        for key in ("output_tokens", "returned_tokens", "remaining_reads"):
            require(type(limits[key]) is int and limits[key] >= 0, "invalid token/read limit")
        require(0 < limits["output_tokens"] <= self._config["max_output_tokens"]
                and limits["returned_tokens"] <= 4096 and limits["remaining_reads"] <= 12, "task cap exceeds fixed ceiling")
        if "input_tokens" in limits:
            require(type(limits["input_tokens"]) is int and 0 < limits["input_tokens"] <= self._config["max_input_tokens"], "input cap differs")
        number(limits["deadline"], positive=True)
        number(limits["device_seconds"], positive=True)

    def _render(self, messages):
        tokenizer = self._session.tokenizer
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        require(type(prompt) is str, "rendered prompt must be text")
        templated = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
        if isinstance(templated, Mapping):
            templated = templated.get("input_ids")
        ids = token_ids(templated)
        require(ids and ids == token_ids(tokenizer.encode(prompt, add_special_tokens=False)), "template/encode token disagreement")
        match = re.match(r"\A<\|im_start\|>system\n(.*?)<\|im_end\|>\n", prompt, re.S)
        require(match is not None and match[1] == messages[0]["content"], "actual system segment differs")
        return prompt, ids

    def generate(self, request, limits):
        request, limits = copy.deepcopy(request), copy.deepcopy(limits)
        self._request(request, limits)
        self._acquire()
        started = self._clock()
        name = None
        try:
            deadline = min(limits["deadline"], started + limits["device_seconds"],
                           started + self._config["device_seconds_cap"] - self._seconds)
            self._check(deadline)
            require(request["id"] not in self._ids, "request already consumed; no retry")
            require(len(self._ids) < self._config["max_calls"], "actor call cap exhausted")
            self._ids.add(request["id"])
            name = f"call_{len(self._ids) - 1:04d}"
            self._start(deadline)
            self._write(name + ".request.json", {"request": request, "limits": limits,
                                                "request_sha256": digest(request), "started": started})
            prompt, prompt_ids = self._render(request["messages"])
            require(len(prompt_ids) <= limits.get("input_tokens", self._config["max_input_tokens"]), "prompt input-token cap exceeded")
            require(len(prompt_ids) + limits["output_tokens"] <= self._config["engine"]["max_model_len"], "context window exceeded")
            sampling = {**SAMPLING, "seed": request["seed"], "max_tokens": limits["output_tokens"]}
            self._write(name + ".render.json", {"rendered_prompt": prompt, "prompt_token_ids": prompt_ids,
                                               "sampling": sampling, "mount": "C0", "lora_request": None})
            self._check(deadline)
            require(self._clock() - started < limits["device_seconds"], "call budget exhausted before generation")
            self._unchanged_files()
            generation_started = self._clock()
            try:
                raw = self._session.generate(prompt, copy.deepcopy(sampling))
            except _NativeOutputError as error:
                self._write(name + ".raw.json", {"kind": self._kind, "request_sha256": digest(request),
                                                "invalid_cardinality_captures": error.captures,
                                                "operation_started": started, "generation_started": generation_started,
                                                "generation_ended": self._clock(),
                                                "mount": "C0", "lora_request": None})
                raise
            ended = self._clock()
            self._write(name + ".raw.json", {"kind": self._kind, "request_sha256": digest(request),
                                            "raw": raw, "operation_started": started,
                                            "generation_started": generation_started, "generation_ended": ended,
                                            "mount": "C0", "lora_request": None})
            require(type(raw) is dict and set(raw) == {"text", "output_token_ids", "prompt_token_ids", "finish_reason", "stop_reason"}, "native raw receipt fields")
            require(type(raw["text"]) is str and token_ids(raw["prompt_token_ids"]) == prompt_ids, "actual prompt IDs differ")
            output_ids = token_ids(raw["output_token_ids"])
            require(len(output_ids) <= limits["output_tokens"] and (output_ids or not raw["text"]), "actual output token cap/receipt")
            require(raw["finish_reason"] in ("stop", "length") and (raw["stop_reason"] is None or type(raw["stop_reason"]) in (int, str)), "unexpected generation termination")
            decoded = self._session.tokenizer.decode(output_ids, skip_special_tokens=True)
            require(decoded == raw["text"], "output text/token decode differs")
            self._unchanged_files()
            self._check(deadline)
            elapsed = self._clock() - started
            require(elapsed <= limits["device_seconds"] and self._seconds + elapsed <= self._config["device_seconds_cap"], "call/aggregate elapsed-device cap exceeded")
            response = {"request_sha256": digest(request), "text": raw["text"], "prompt_tokens": len(prompt_ids),
                        "output_tokens": len(output_ids), "device_seconds": elapsed}
            self._write(name + ".response.json", {"response": response, "raw_utf8_sha256": text_hash(raw["text"]),
                                                 "raw_hex": raw["text"].encode("utf-8").hex(), "decoded": decoded})
            return copy.deepcopy(response)
        except Exception as error:
            self._failed = True
            if name is not None and self._root is not None:
                if not (self._root / (name + ".request.json")).exists():
                    self._write(name + ".request.json", {"request": request, "limits": limits,
                                                        "request_sha256": digest(request), "started": started})
                self._write(name + ".error.json", {"error_type": type(error).__name__, "status": "FAILED_NO_RETRY"})
            raise
        finally:
            self._seconds += max(0, self._clock() - started)
            self._lock.release()

    def count_tokens(self, text):
        require(type(text) is str, "count_tokens accepts text only")
        self._acquire()
        started = self._clock()
        try:
            deadline = min(self._config["deadline"], started + self._config["device_seconds_cap"] - self._seconds)
            self._start(deadline)
            ids = token_ids(self._session.tokenizer.encode(text, add_special_tokens=False))
            self._check(deadline)
            self._write(f"count_{self._count_calls:04d}.json", {"text": text, "sha256": text_hash(text), "token_ids": ids})
            self._count_calls += 1
            return len(ids)
        except Exception:
            self._failed = True
            raise
        finally:
            self._seconds += max(0, self._clock() - started)
            self._lock.release()

    def close(self):
        self._acquire()
        try:
            if self._closed:
                return copy.deepcopy(self._close_receipt)
            started = self._clock()
            shutdown = None
            error_type = None
            try:
                if self._session is not None:
                    shutdown = self._session.close()
            except Exception as error:
                error_type = type(error).__name__
            self._seconds += max(0, self._clock() - started)
            receipt = {"kind": self._kind, "shutdown": shutdown, "error_type": error_type,
                       "failed": self._failed, "calls_consumed": len(self._ids), "token_count_calls": self._count_calls,
                       "elapsed_actor_seconds": self._seconds, "outer_release_required": True,
                       "owned_group_released": None, "gpu_vacant": None,
                       "time_basis": "single-GPU actor operation wall intervals; not GPU active time",
                       "budget_exceeded": self._seconds > self._config["device_seconds_cap"]}
            self._closed = True
            self._close_receipt = receipt
            if self._root is not None:
                self._write("close.json", receipt)
            return copy.deepcopy(receipt)
        finally:
            self._lock.release()

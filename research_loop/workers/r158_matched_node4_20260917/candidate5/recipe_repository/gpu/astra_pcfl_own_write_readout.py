"""Cold, source-withdrawn own-write READs; outer owns processes and hard timeout.

Only explicit start/generate loads anything. No scorer, corpus, formation
history, training, resource allocation, retries, or GPU-release assertion.
"""

import copy
import hashlib
import inspect
import json
import os
from pathlib import Path
import threading
import time

from gpu import astra_pcfl_native_actor as native
from organism_v6 import pcfl_vertical_dev as core


SCHEMA = "pcfl.own_write_readout.v1"
ENGINE = {**native.ENGINE, "enable_lora": True, "max_lora_rank": 8}
ARMS = ("NO_WRITE_C0", "AUTH_WRITE")
CONFIG_FIELDS = native.CONFIG_FIELDS | {"arm", "adapter", "roster", "roster_sha256", "shutdown_binding"}
SCOPE = Path(__file__).resolve().parents[1] / "research_notes/astra_memos/ASTRA_PCFL_OWN_WRITE_SCOPE_2026-09-13.md"
canonical, digest, require = native.canonical, native.digest, native.require
_native_started = False


def required_source_paths():
    return tuple(str(Path(path).resolve()) for path in (__file__, native.__file__, core.__file__, SCOPE))


def route_identity(config):
    adapter = config["adapter"]
    return {"arm": config["arm"], "lora_request": None if adapter is None else
            {"name": adapter["name"], "id": adapter["id"], "path": adapter["path"]},
            "adapter_files_sha256": None if adapter is None else digest(adapter["files"])}


def public_messages(row):
    require(type(row) is dict and set(row) == {"id", "request", "view", "seed", "output_tokens"}, "closed read roster fields")
    core.parse_read(row["request"])
    require(type(row["view"]) is int and 0 <= row["view"] <= 8, "W0..W8 view required")
    return [{"role": "system", "content": core.MEMORY_SYSTEM},
            {"role": "user", "content": core.WRAPPERS[row["view"]].replace("{REQUEST}", row["request"])}]


def _lora_identity(request):
    return None if request is None else {"name": request.lora_name, "id": request.lora_int_id, "path": request.lora_path}


def _native_loader(config):
    global _native_started
    require(not _native_started, "one cold native readout engine per process; use a fresh process")
    for name in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY", "VLLM_NO_USAGE_STATS"):
        require(os.environ.get(name) == "1", "offline flag required: " + name)
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == config["gpu_uuid"], "allocated GPU differs")
    _native_started = True
    from vllm import LLM, SamplingParams
    from vllm.lora.request import LoRARequest

    class Session:
        def __init__(self):
            self.route = route_identity(config)
            request = self.route["lora_request"]
            self.lora = None if request is None else LoRARequest(request["name"], request["id"], request["path"])
            require(_lora_identity(self.lora) == request, "constructed LoRARequest differs")
            self.llm = LLM(model=config["model_path"], tokenizer=config["model_path"], **config["engine"])

        @property
        def tokenizer(self):
            return self.llm.get_tokenizer()

        def generate(self, prompt, sampling):
            import torch
            require(_lora_identity(self.lora) == self.route["lora_request"], "LoRARequest changed")
            with torch.inference_mode():
                outputs = self.llm.generate([prompt], SamplingParams(**sampling), lora_request=self.lora, use_tqdm=False)
            captures = [{"prompt_token_ids": list(result.prompt_token_ids),
                         "outputs": [{"text": output.text, "output_token_ids": list(output.token_ids),
                                      "finish_reason": output.finish_reason, "stop_reason": output.stop_reason}
                                     for output in result.outputs]} for result in outputs]
            if len(outputs) != 1 or len(outputs[0].outputs) != 1:
                raise native._NativeOutputError(captures)
            output = outputs[0].outputs[0]
            return {"text": output.text, "output_token_ids": list(output.token_ids),
                    "prompt_token_ids": list(outputs[0].prompt_token_ids), "finish_reason": output.finish_reason,
                    "stop_reason": output.stop_reason, "route": {**self.route, "lora_request": _lora_identity(self.lora)}}

        def verify_shutdown(self):
            method = self.llm.llm_engine.engine_core.shutdown
            require(callable(method), "EngineCore shutdown unavailable")
            inspect.signature(method).bind()
            path = Path(inspect.getsourcefile(method)).resolve()
            binding = config["shutdown_binding"]
            require(str(path) == binding["path"] and hashlib.sha256(path.read_bytes()).hexdigest() == binding["sha256"],
                    "installed EngineCore shutdown source differs")
            return {"method": "llm.llm_engine.engine_core.shutdown", "source": binding}

        def close(self):
            receipt = self.verify_shutdown()
            self.llm.llm_engine.engine_core.shutdown()
            return {**receipt, "shutdown_returned": True}

    return Session()


class ReadoutActor:
    """Each ID consumes one frozen roster row; no caller-supplied model messages."""

    scripted = False
    _acquire = native.NativeActor._acquire
    _check = native.NativeActor._check
    _write = native.NativeActor._write
    _hash_file = native.NativeActor._hash_file
    _unchanged_files = native.NativeActor._unchanged_files
    _render = native.NativeActor._render
    start = native.NativeActor.start

    def __init__(self, config, *, loader=None, environment_reader=native.environment_identity, clock=time.monotonic):
        canonical(config)
        require(type(config) is dict and set(config) == CONFIG_FIELDS and config["schema"] == SCHEMA, "readout config schema")
        self._config = copy.deepcopy(config)
        self._config_hash = digest(self._config)
        self._loader = _native_loader if loader is None else loader
        self._kind = "NATIVE_OWN_WRITE_READOUT" if loader is None else "INJECTED_CPU_TEST"
        self._environment_reader, self._clock = environment_reader, clock
        self._lock = threading.Lock()
        self._session = self._root = self._close_receipt = None
        self._failed = self._closed = self._started = False
        self._ids, self._signatures = set(), {}
        self._seconds = 0.0
        self._validate_config()
        self._route = route_identity(self._config)

    def _validate_config(self):
        config = self._config
        require(config["arm"] in ARMS and config["engine"] == ENGINE, "arm or identical LoRA-enabled engine differs")
        for name in ("model_path", "output_dir"):
            require(type(config[name]) is str and Path(config[name]).is_absolute(), "absolute paths required")
        require(type(config["gpu_uuid"]) is str and config["gpu_uuid"].startswith("GPU-"), "GPU UUID required")
        for name, maximum in (("max_input_tokens", ENGINE["max_model_len"]), ("max_output_tokens", 2048), ("max_calls", 1952)):
            require(type(config[name]) is int and 0 < config[name] <= maximum, "invalid " + name)
        for name in ("deadline", "device_seconds_cap"):
            native.number(config[name], positive=True)
        require(config["device_seconds_cap"] <= 36000, "readout cap exceeds 10 hours")
        for name in ("model_binding", "shutdown_binding"):
            binding = config[name]
            require(type(binding) is dict and set(binding) == {"path", "sha256"}
                    and Path(binding["path"]).is_absolute(), "closed absolute " + name)
            native.sha(binding["sha256"])
        sources = config["source_files"]
        require(type(sources) is dict and set(required_source_paths()) <= set(sources), "readout/native/core/scope source pins required")
        for path, expected in sources.items():
            require(Path(path).is_absolute(), "absolute source pin required")
            native.sha(expected)
        require(type(config["tokenizer_files"]) is dict and set(config["tokenizer_files"]) == native.TOKENIZER_FILES, "tokenizer file inventory")
        for expected in config["tokenizer_files"].values():
            native.sha(expected)
        native.sha(config["chat_template_sha256"])
        probe = config["tokenizer_probe"]
        require(type(probe) is dict and set(probe) == {"text", "token_ids"} and type(probe["text"]) is str, "tokenizer probe")
        require(native.token_ids(probe["token_ids"]), "empty tokenizer probe")
        environment = config["environment"]
        require(type(environment) is dict and set(environment) == {"python", "version", "packages"}
                and set(environment["packages"]) == set(native.PACKAGES), "environment identity schema")
        roster = config["roster"]
        require(type(roster) is list and len(roster) == config["max_calls"] and digest(roster) == config["roster_sha256"], "frozen roster/count/hash differs")
        seen = set()
        for row in roster:
            public_messages(row)
            require(type(row["id"]) is str and 0 < len(row["id"]) <= 512 and row["id"] not in seen, "unique read IDs required")
            require(type(row["seed"]) is int and 0 <= row["seed"] < 2**63, "read seed")
            require(type(row["output_tokens"]) is int and 0 < row["output_tokens"] <= config["max_output_tokens"], "frozen output cap")
            seen.add(row["id"])
        adapter = config["adapter"]
        if config["arm"] == "NO_WRITE_C0":
            require(adapter is None, "NO_WRITE_C0 cannot mount an adapter")
        else:
            require(type(adapter) is dict and set(adapter) == {"name", "id", "path", "files"}, "closed adapter binding")
            require(adapter["name"] == "pcfl-own-write" and type(adapter["id"]) is int and adapter["id"] == 1, "fixed LoRARequest name/id")
            require(type(adapter["path"]) is str and Path(adapter["path"]).is_absolute(), "absolute adapter path")
            files = adapter["files"]
            require(type(files) is dict and {"adapter_config.json", "adapter_model.safetensors"} <= set(files)
                    <= {"adapter_config.json", "adapter_model.safetensors", "README.md"}, "saved LoRA file map")
            for entry in files.values():
                require(type(entry) is dict and set(entry) == {"size", "sha256"}
                        and type(entry["size"]) is int and entry["size"] > 0, "adapter file size/hash")
                native.sha(entry["sha256"])

    def _verify_identity(self, deadline):
        base = native.NativeActor._verify_identity(self, deadline)
        base.pop("mount")
        base.pop("lora_request")
        binding = self._config["shutdown_binding"]
        require(self._hash_file(binding["path"], deadline) == binding["sha256"], "shutdown source drift")
        adapter = self._config["adapter"]
        if adapter is not None:
            root = Path(adapter["path"])
            require(root.is_dir(), "saved adapter missing")
            paths = list(root.rglob("*"))
            require(all(path.is_file() and not path.is_symlink() for path in paths)
                    and {str(path.relative_to(root)) for path in paths} == set(adapter["files"]), "adapter inventory differs")
            for name, entry in adapter["files"].items():
                require((root / name).stat().st_size == entry["size"]
                        and self._hash_file(root / name, deadline) == entry["sha256"], "adapter file drift")
            metadata = json.loads((root / "adapter_config.json").read_bytes())
            require(type(metadata.get("r")) is int and metadata["r"] == 8 and metadata.get("lora_alpha") == 16
                    and metadata.get("lora_dropout") == 0.05 and metadata.get("peft_type") == "LORA"
                    and metadata.get("bias") == "none" and not metadata.get("modules_to_save")
                    and not metadata.get("rank_pattern") and not metadata.get("alpha_pattern")
                    and not metadata.get("use_dora") and not metadata.get("use_rslora"), "not the scoped rank8/alpha16/dropout.05 LoRA")
        return {"base_identity": base, "route": self._route, "engine": self._config["engine"],
                "adapter": adapter, "roster_sha256": self._config["roster_sha256"], "shutdown_binding": binding}

    def _start(self, deadline):
        self._check(deadline)
        if self._started:
            self._unchanged_files()
            return
        root = Path(self._config["output_dir"])
        require(not root.exists() and not root.is_symlink() and root.parent.is_dir()
                and root.parent.resolve() == root.parent, "fresh unaliased output required")
        protected = [Path(self._config["model_path"]).resolve()]
        if self._config["adapter"] is not None:
            protected.append(Path(self._config["adapter"]["path"]).resolve())
            require(not protected[0].is_relative_to(protected[1]) and not protected[1].is_relative_to(protected[0]), "base/adapter overlap")
        require(all(not root.is_relative_to(path) and not path.is_relative_to(root) for path in protected), "output/artifact overlap")
        root.mkdir()
        self._root = root
        self._write("config.json", self._config)
        try:
            identity = self._verify_identity(deadline)
            self._write("identity.json", {"kind": self._kind, "pid": os.getpid(), "config_sha256": self._config_hash, "identity": identity})
            self._check(deadline)
            self._unchanged_files()
            started = self._clock()
            self._session = self._loader(copy.deepcopy(self._config))
            tokenizer = self._session.tokenizer
            require(Path(tokenizer.name_or_path).resolve() == protected[0], "loaded tokenizer path differs")
            require(type(tokenizer.chat_template) is str and native.text_hash(tokenizer.chat_template) == self._config["chat_template_sha256"], "loaded template drift")
            probe = self._config["tokenizer_probe"]
            require(native.token_ids(tokenizer.encode(probe["text"], add_special_tokens=False)) == probe["token_ids"], "loaded tokenizer probe differs")
            require(self._session.route == self._route, "loaded adapter route differs")
            shutdown = self._session.verify_shutdown()
            self._unchanged_files()
            self._check(deadline)
            self._started = True
            self._write("load.json", {"kind": self._kind, "route": self._route, "engine": self._config["engine"],
                                      "model_load_started": started, "ready_at": self._clock(), "shutdown": shutdown})
        except Exception as error:
            self._failed = True
            self._write("load_error.json", {"error_type": type(error).__name__, "status": "FAILED_NO_RETRY", "route": self._route})
            raise

    def generate(self, request, limits):
        request, limits = copy.deepcopy(request), copy.deepcopy(limits)
        require(type(request) is dict and set(request) == {"id"}, "readout accepts roster ID only; no messages/targets/history")
        require(type(limits) is dict and set(limits) == {"deadline", "device_seconds"}, "readout time limits only; token caps are frozen")
        for value in limits.values():
            native.number(value, positive=True)
        self._acquire()
        started, name = self._clock(), None
        try:
            deadline = min(limits["deadline"], started + limits["device_seconds"],
                           started + self._config["device_seconds_cap"] - self._seconds)
            self._check(deadline)
            require(len(self._ids) < self._config["max_calls"], "read roster exhausted; no retry")
            row = self._config["roster"][len(self._ids)]
            require(request["id"] == row["id"] and request["id"] not in self._ids, "next frozen roster ID required; no skip/retry")
            self._ids.add(request["id"])
            name = f"call_{len(self._ids) - 1:04d}"
            self._start(deadline)
            messages = public_messages(row)
            self._write(name + ".request.json", {"request": request, "row": row, "messages": messages, "limits": limits,
                                                "route": self._route, "roster_sha256": self._config["roster_sha256"], "started": started})
            prompt, prompt_ids = self._render(messages)
            require(len(prompt_ids) <= self._config["max_input_tokens"]
                    and len(prompt_ids) + row["output_tokens"] <= ENGINE["max_model_len"], "input/context cap exceeded")
            sampling = {**native.SAMPLING, "seed": row["seed"], "max_tokens": row["output_tokens"]}
            self._write(name + ".render.json", {"rendered_prompt": prompt, "prompt_token_ids": prompt_ids,
                                               "sampling": sampling, "route": self._route})
            self._check(deadline)
            self._unchanged_files()
            generation_started = self._clock()
            try:
                raw = self._session.generate(prompt, copy.deepcopy(sampling))
            except native._NativeOutputError as error:
                self._write(name + ".raw.json", {"kind": self._kind, "route": self._route,
                                                "invalid_cardinality_captures": error.captures,
                                                "generation_started": generation_started, "generation_ended": self._clock()})
                raise
            self._write(name + ".raw.json", {"kind": self._kind, "route": self._route, "raw": raw,
                                            "generation_started": generation_started, "generation_ended": self._clock()})
            require(type(raw) is dict and set(raw) == {"text", "output_token_ids", "prompt_token_ids", "finish_reason", "stop_reason", "route"}, "native raw fields")
            require(raw["route"] == self._route, "actual LoRA route differs")
            require(type(raw["text"]) is str and native.token_ids(raw["prompt_token_ids"]) == prompt_ids, "actual prompt token IDs differ")
            ids = native.token_ids(raw["output_token_ids"])
            require(len(ids) <= row["output_tokens"] and (ids or not raw["text"]), "output token cap/receipt")
            require(raw["finish_reason"] in ("stop", "length") and (raw["stop_reason"] is None or type(raw["stop_reason"]) in (int, str)), "generation termination differs")
            require(self._session.tokenizer.decode(ids, skip_special_tokens=True) == raw["text"], "output decode differs")
            self._unchanged_files()
            self._check(deadline)
            elapsed = self._clock() - started
            response = {"id": row["id"], "request_sha256": digest(request), "roster_sha256": self._config["roster_sha256"],
                        "route": self._route, "text": raw["text"], "prompt_tokens": len(prompt_ids), "output_tokens": len(ids),
                        "finish_reason": raw["finish_reason"], "stop_reason": raw["stop_reason"], "truncated": raw["finish_reason"] == "length",
                        "device_seconds": elapsed}
            self._write(name + ".response.json", {"response": response, "raw_utf8_sha256": native.text_hash(raw["text"]),
                                                 "raw_hex": raw["text"].encode("utf-8").hex()})
            return copy.deepcopy(response)
        except Exception as error:
            self._failed = True
            if name is not None and self._root is not None:
                self._write(name + ".error.json", {"request": request, "limits": limits, "route": self._route,
                                                  "error_type": type(error).__name__, "status": "FAILED_NO_RETRY"})
            raise
        finally:
            self._seconds += max(0, self._clock() - started)
            self._lock.release()

    def close(self):
        self._acquire()
        try:
            if self._closed:
                return copy.deepcopy(self._close_receipt)
            started, shutdown, error_type = self._clock(), None, None
            try:
                if self._session is not None:
                    shutdown = self._session.close()
            except Exception as error:
                error_type = type(error).__name__
            self._seconds += max(0, self._clock() - started)
            receipt = {"schema": SCHEMA + "/close", "kind": self._kind, "route": self._route, "shutdown": shutdown,
                       "error_type": error_type, "failed": self._failed, "calls_consumed": len(self._ids),
                       "planned_calls": self._config["max_calls"], "elapsed_actor_seconds": self._seconds,
                       "budget_exceeded": self._seconds > self._config["device_seconds_cap"] or self._clock() > self._config["deadline"],
                       "outer_release_required": True, "owned_group_released": None, "gpu_vacant": None,
                       "time_basis": "actor operation wall intervals, not GPU active time; outer owns cold-to-release hard timeout"}
            self._closed, self._close_receipt = True, receipt
            if self._root is not None:
                self._write("close.json", receipt)
            return copy.deepcopy(receipt)
        finally:
            self._lock.release()

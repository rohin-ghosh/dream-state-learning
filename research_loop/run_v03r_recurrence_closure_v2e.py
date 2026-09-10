"""One-run v0.3-R recurrence-closure science driver.

This module is deliberately both narrow and boring.  It owns the one resident
Qwen engine and the dynamic execution of the already frozen v2e calibration;
it does not own the benchmark, schemas, selector mathematics, or scoring
definitions.  Those live in :mod:`v03r_recurrence_closure_contract_v2e`.

The public ``science`` command runs raw cognition in a child process, seals it,
then starts a different no-provider child process for offline scoring.  This is
not merely an implementation convenience: it makes the phase-A/phase-B
information barrier an operating-system process boundary.  The remote wrapper
owns the run's exclusive terminal markers; this driver writes only append-only
artifacts beneath ``JOB_DIR/artifacts``.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, is_dataclass
from fractions import Fraction
import gc
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Iterable, Mapping, Sequence
import uuid

from .model_provider_boundary import (
    ExactProviderCall,
    IsolatedModelProviderBoundary,
    ProviderCallArtifact,
    ProviderCallScope,
    ProviderExchange,
    ProviderExpectations,
)


SCHEMA_VERSION = "v03r-recurrence-closure-runner-v2e"
PROVIDER_NAME = "local-resident-vllm"
MODEL_ID = "Qwen/Qwen2.5-32B-Instruct"
MODEL_REVISION = "5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd"
TOKENIZER_ID = MODEL_ID
TOKENIZER_REVISION = MODEL_REVISION
ARMS = ("no_feedback", "own_selector", "matched_distractor")
SCIENCE_PROMPT_LIMITS = {
    "DREAM": 2048,
    "THINK": 8192,
    "FULL_CONTEXT": 8192,
    "RAG": 2048,
}


class RunnerError(RuntimeError):
    """A permanent fail-closed error in this one calibration."""


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hash_json(value: Any) -> str:
    return _sha256(_canonical_json_bytes(value))


def _opaque(*parts: object) -> str:
    material = b"\0".join(str(part).encode("ascii", errors="strict") for part in parts)
    return _sha256(material)


def _token_ids_hash(token_ids: Sequence[int]) -> str:
    encoded = ",".join(str(int(item)) for item in token_ids).encode("ascii")
    return _sha256(encoded)


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _plain(item) for key, item in asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [_plain(item) for item in sorted(value)]
    if isinstance(value, bytes):
        return {"bytes_hex": value.hex(), "sha256": _sha256(value)}
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator}
    if isinstance(value, Path):
        return str(value)
    return value


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    with temporary.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _write_json_once(path: Path, value: Any) -> None:
    if path.exists():
        raise RunnerError(f"refusing to overwrite immutable artifact: {path}")
    _atomic_write(path, _canonical_json_bytes(value))


def _read_exact_json(path: Path) -> Any:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RunnerError(f"invalid exact JSON artifact: {path}") from exc
    if _canonical_json_bytes(value) != raw:
        raise RunnerError(f"artifact is not canonical ASCII JSON: {path}")
    return value


@dataclass(frozen=True)
class ResidentGenerationTelemetry:
    provider_session_id: str
    provider_request_id: str
    supplied_token_count: int
    generated_token_count: int
    supplied_token_ids: tuple[int, ...]
    generated_token_ids: tuple[int, ...]
    supplied_token_ids_sha256: str
    generated_token_ids_sha256: str
    active_sequences_before: int
    active_sequences_after: int
    loaded_idle_allocated_mib: int
    loaded_idle_reserved_mib: int
    peak_allocated_mib: int
    peak_reserved_mib: int
    post_reset_allocated_mib: int
    post_reset_reserved_mib: int
    request_truncated: bool
    prefix_cache_hits: int


class _ResidentFreshSession:
    """A one-use logical session backed by one immutable resident engine."""

    def __init__(self, factory: "ResidentModelFactory", session_id: str) -> None:
        self._factory = factory
        self._session_id = session_id
        self._used = False
        self._closed = False

    def invoke(self, request_bytes: bytes, config_bytes: bytes) -> ProviderExchange:
        if self._closed or self._used:
            raise RunnerError("resident logical session is not fresh")
        self._used = True
        return self._factory._invoke(self._session_id, request_bytes, config_bytes)

    def close(self) -> None:
        if self._closed:
            raise RunnerError("resident logical session closed twice")
        self._closed = True


class ResidentModelFactory:
    """Exactly one resident engine; every call receives empty logical state.

    ``vllm`` is imported lazily so CPU contract tests can import this module.
    The factory never accepts chat history, an adapter, tool state, or a cache
    key.  Prefix caching is disabled at engine construction, and exact prompt
    token IDs are supplied to avoid provider-side truncation or re-tokenizing.
    """

    def __init__(
        self, *, model: str = MODEL_ID, revision: str = MODEL_REVISION,
        engine_kind: str = "vllm", max_model_len: int = 8448,
        gpu_memory_utilization: float = 0.96,
    ) -> None:
        if model != MODEL_ID or revision != MODEL_REVISION:
            raise RunnerError("v2e permits only the exact frozen Qwen model revision")
        if engine_kind not in {"vllm", "transformers"}:
            raise RunnerError("engine_kind must be vllm or transformers")
        self.model = model
        self.revision = revision
        self.engine_kind = engine_kind
        self._nonce = uuid.uuid4().hex
        self._next_session = 0
        self._active = 0
        self._telemetry: dict[str, ResidentGenerationTelemetry] = {}
        self._boundary: IsolatedModelProviderBoundary | None = None

        try:
            from transformers import AutoTokenizer
        except ImportError as exc:  # pragma: no cover - GPU environment only
            raise RunnerError("transformers is required by the resident provider") from exc
        self.tokenizer = AutoTokenizer.from_pretrained(
            model, revision=revision, use_fast=True, trust_remote_code=False,
            local_files_only=True,
        )
        if engine_kind == "vllm":
            try:
                from vllm import LLM
            except ImportError as exc:  # pragma: no cover - GPU environment only
                raise RunnerError("vllm is required by the frozen provider") from exc
            self.engine = LLM(
                model=model,
                revision=revision,
                tokenizer=model,
                tokenizer_revision=revision,
                dtype="bfloat16",
                tensor_parallel_size=1,
                max_model_len=max_model_len,
                gpu_memory_utilization=gpu_memory_utilization,
                enable_prefix_caching=False,
                trust_remote_code=False,
            )
        else:  # pragma: no cover - fallback exercised only on the GPU node
            try:
                import torch
                from transformers import AutoModelForCausalLM
            except ImportError as exc:
                raise RunnerError("torch/transformers are required by the provider") from exc
            self.engine = AutoModelForCausalLM.from_pretrained(
                model, revision=revision, torch_dtype=torch.bfloat16,
                device_map={"": 0}, trust_remote_code=False,
                local_files_only=True,
            ).eval()
        self._loaded_idle = self._cuda_memory()
        self._boundary = IsolatedModelProviderBoundary(self)

    def encode_bytes(self, value: bytes) -> tuple[int, ...]:
        try:
            text = value.decode("ascii", errors="strict")
        except UnicodeDecodeError as exc:
            raise RunnerError("provider input must be exact ASCII") from exc
        return tuple(int(item) for item in self.tokenizer.encode(
            text, add_special_tokens=False,
        ))

    def render_user_request(self, content_bytes: bytes) -> bytes:
        """Apply the pinned Qwen chat template once, without token truncation."""

        try:
            content = content_bytes.decode("ascii", errors="strict")
        except UnicodeDecodeError as exc:
            raise RunnerError("science prompt material must be ASCII") from exc
        rendered = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": content}], tokenize=False,
            add_generation_prompt=True,
        )
        try:
            return rendered.encode("ascii", errors="strict")
        except UnicodeEncodeError as exc:
            raise RunnerError("pinned chat template produced non-ASCII bytes") from exc

    def invoke_boundary(self, call: ExactProviderCall) -> ProviderCallArtifact:
        if self._boundary is None:
            raise RunnerError("resident provider boundary was not initialized")
        return self._boundary.invoke(call)

    def _cuda_memory(self) -> tuple[int, int]:
        try:
            import torch
            if not torch.cuda.is_available():
                return (0, 0)
            torch.cuda.synchronize()
            unit = 1024 * 1024
            return (
                int(torch.cuda.memory_allocated() // unit),
                int(torch.cuda.memory_reserved() // unit),
            )
        except ImportError:
            return (0, 0)

    def open_fresh_session(self) -> _ResidentFreshSession:
        if self._active != 0:
            raise RunnerError("resident engine has an active sequence at session open")
        sequence = self._next_session
        self._next_session += 1
        session_id = _opaque("v2e-session", self._nonce, sequence)
        return _ResidentFreshSession(self, session_id)

    def pop_telemetry(self, provider_session_id: str) -> ResidentGenerationTelemetry:
        try:
            return self._telemetry.pop(provider_session_id)
        except KeyError as exc:
            raise RunnerError("provider telemetry is absent or already consumed") from exc

    @staticmethod
    def _parse_config(config_bytes: bytes) -> dict[str, Any]:
        try:
            config = json.loads(config_bytes.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RunnerError("provider config must be ASCII JSON") from exc
        expected = {
            "temperature", "top_p", "max_new_tokens", "seed",
            "input_token_limit", "ignore_eos",
        }
        if not isinstance(config, dict) or set(config) != expected:
            raise RunnerError("provider config has the wrong exact fields")
        if _canonical_json_bytes(config) != config_bytes:
            raise RunnerError("provider config is not canonical ASCII JSON")
        if isinstance(config["seed"], bool) or not isinstance(config["seed"], int) \
                or config["seed"] < 0:
            raise RunnerError("provider seed must be a non-negative integer")
        if not isinstance(config["max_new_tokens"], int) \
                or not 1 <= config["max_new_tokens"] <= 256:
            raise RunnerError("provider output cap is outside the v2e envelope")
        if config["input_token_limit"] not in {2048, 8192}:
            raise RunnerError("provider input cap is outside the v2e envelope")
        if not isinstance(config["ignore_eos"], bool):
            raise RunnerError("ignore_eos must be Boolean")
        return config

    def _generate_vllm(
        self, token_ids: Sequence[int], config: Mapping[str, Any],
    ) -> tuple[bytes, tuple[int, ...], str]:
        from vllm import SamplingParams
        try:
            from vllm.inputs import TokensPrompt
            prompt: Any = TokensPrompt(prompt_token_ids=list(token_ids))
        except (ImportError, TypeError):  # compatible with older vLLM releases
            prompt = {"prompt_token_ids": list(token_ids)}
        params = SamplingParams(
            temperature=float(config["temperature"]),
            top_p=float(config["top_p"]),
            max_tokens=int(config["max_new_tokens"]),
            seed=int(config["seed"]) % (2**31 - 1),
            ignore_eos=bool(config["ignore_eos"]),
        )
        outputs = self.engine.generate([prompt], params, use_tqdm=False)
        if len(outputs) != 1 or len(outputs[0].outputs) != 1:
            raise RunnerError("resident provider returned non-singleton output")
        generated = outputs[0].outputs[0]
        ids = tuple(int(item) for item in generated.token_ids)
        return generated.text.encode("utf-8"), ids, str(outputs[0].request_id)

    def _generate_transformers(
        self, token_ids: Sequence[int], config: Mapping[str, Any],
    ) -> tuple[bytes, tuple[int, ...], str]:  # pragma: no cover - GPU fallback
        import torch
        inputs = torch.tensor([list(token_ids)], dtype=torch.long, device="cuda:0")
        generator = torch.Generator(device="cuda:0")
        generator.manual_seed(int(config["seed"]) % (2**63 - 1))
        kwargs: dict[str, Any] = {
            "max_new_tokens": int(config["max_new_tokens"]),
            "do_sample": float(config["temperature"]) > 0,
            "generator": generator,
            "use_cache": True,
        }
        if kwargs["do_sample"]:
            kwargs.update(
                temperature=float(config["temperature"]),
                top_p=float(config["top_p"]),
            )
        if config["ignore_eos"]:
            kwargs["eos_token_id"] = None
        with torch.inference_mode():
            output = self.engine.generate(inputs, **kwargs)
        ids = tuple(int(item) for item in output[0, len(token_ids):].tolist())
        text = self.tokenizer.decode(ids, skip_special_tokens=False)
        return text.encode("utf-8"), ids, _opaque("transformers-request", uuid.uuid4().hex)

    def _invoke(
        self, session_id: str, request_bytes: bytes, config_bytes: bytes,
    ) -> ProviderExchange:
        if self._active != 0:
            raise RunnerError("cross-call active sequence detected")
        config = self._parse_config(config_bytes)
        supplied = self.encode_bytes(request_bytes)
        if len(supplied) > int(config["input_token_limit"]):
            raise RunnerError("request would require truncation; provider call refused")
        started = time.time_ns()
        self._active = 1
        try:
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.reset_peak_memory_stats()
            except ImportError:
                pass
            if self.engine_kind == "vllm":
                raw, generated, engine_request_id = self._generate_vllm(supplied, config)
            else:
                raw, generated, engine_request_id = self._generate_transformers(
                    supplied, config,
                )
            peak_allocated, peak_reserved = self._cuda_memory()
        finally:
            self._active = 0
        ended = time.time_ns()
        gc.collect()
        post_allocated, post_reserved = self._cuda_memory()
        request_id = _opaque(
            "v2e-request", self._nonce, session_id, engine_request_id,
            _sha256(request_bytes), _sha256(config_bytes),
        )
        telemetry = ResidentGenerationTelemetry(
            provider_session_id=session_id,
            provider_request_id=request_id,
            supplied_token_count=len(supplied),
            generated_token_count=len(generated),
            supplied_token_ids=tuple(supplied),
            generated_token_ids=tuple(generated),
            supplied_token_ids_sha256=_token_ids_hash(supplied),
            generated_token_ids_sha256=_token_ids_hash(generated),
            active_sequences_before=0,
            active_sequences_after=self._active,
            loaded_idle_allocated_mib=self._loaded_idle[0],
            loaded_idle_reserved_mib=self._loaded_idle[1],
            peak_allocated_mib=peak_allocated,
            peak_reserved_mib=peak_reserved,
            post_reset_allocated_mib=post_allocated,
            post_reset_reserved_mib=post_reserved,
            request_truncated=False,
            prefix_cache_hits=0,
        )
        self._telemetry[session_id] = telemetry
        receipt = {
            "schema_version": "provider-call-receipt-v1.0",
            "provider": PROVIDER_NAME,
            "model": self.model,
            "model_revision": self.revision,
            "provider_session_id": session_id,
            "provider_request_id": request_id,
            "fresh_session": True,
            "turn_index": 0,
            "request_sha256": _sha256(request_bytes),
            "request_byte_count": len(request_bytes),
            "config_sha256": _sha256(config_bytes),
            "config_byte_count": len(config_bytes),
            "raw_response_sha256": _sha256(raw),
            "raw_response_byte_count": len(raw),
            "provider_started_at_unix_ns": started,
            "provider_ended_at_unix_ns": ended,
            "token_evidence": {
                "mode": "TOKEN_ID_HASHES",
                "source": "PROVIDER_RESPONSE",
                "tokenizer_id": TOKENIZER_ID,
                "tokenizer_revision": TOKENIZER_REVISION,
                "supplied_token_count": len(supplied),
                "generated_token_count": len(generated),
                "supplied_token_ids_sha256": _token_ids_hash(supplied),
                "generated_token_ids_sha256": _token_ids_hash(generated),
            },
        }
        return ProviderExchange(raw, _canonical_json_bytes(receipt))


def build_provider(
    *, model: str = MODEL_ID, revision: str = MODEL_REVISION,
    engine_kind: str = "vllm", max_model_len: int = 8448,
) -> ResidentModelFactory:
    """Stable callable used by the remote zero-science preflight."""

    return ResidentModelFactory(
        model=model, revision=revision, engine_kind=engine_kind,
        max_model_len=max_model_len,
    )


def invoke_provider_exact(
    factory: ResidentModelFactory, *, request_bytes: bytes, config: Mapping[str, Any],
    run_id: str, life_id: str, arm: str, stage: str, round_index: int,
    call_index: int,
) -> tuple[ProviderCallArtifact, ResidentGenerationTelemetry]:
    """Execute and fully bind one exact isolated call against a resident base."""

    config_bytes = _canonical_json_bytes(dict(config))
    call_id = _opaque(
        "v2e-call", run_id, life_id, arm, stage, round_index, call_index,
        _sha256(request_bytes), _sha256(config_bytes),
    )
    call = ExactProviderCall(
        scope=ProviderCallScope(
            call_id=call_id, run_id=run_id, life_id=life_id, arm=arm,
            round_index=round_index, stage=stage, call_index=call_index,
        ),
        request_bytes=request_bytes,
        config_bytes=config_bytes,
        expectations=ProviderExpectations(
            provider=PROVIDER_NAME, model=factory.model,
            model_revision=factory.revision, tokenizer_id=TOKENIZER_ID,
            tokenizer_revision=TOKENIZER_REVISION,
        ),
    )
    artifact = factory.invoke_boundary(call)
    telemetry = factory.pop_telemetry(artifact.receipt.provider_session_id)
    return artifact, telemetry


def _provider_artifact_row(
    artifact: ProviderCallArtifact, telemetry: ResidentGenerationTelemetry,
) -> dict[str, Any]:
    """Losslessly serialize provider evidence without pretending bytes are text."""

    artifact.validate()
    return {
        "schema_version": artifact.schema_version,
        "scope": _plain(artifact.scope),
        "expectations": _plain(artifact.expectations),
        "request_hex": artifact.request_bytes.hex(),
        "config_hex": artifact.config_bytes.hex(),
        "raw_response_hex": artifact.raw_response_bytes.hex(),
        "provider_receipt_hex": artifact.provider_receipt_bytes.hex(),
        "request_sha256": artifact.request_sha256,
        "config_sha256": artifact.config_sha256,
        "raw_response_sha256": artifact.raw_response_sha256,
        "provider_receipt_sha256": artifact.provider_receipt_sha256,
        "receipt": _plain(artifact.receipt),
        "boundary_started_at_unix_ns": artifact.boundary_started_at_unix_ns,
        "boundary_ended_at_unix_ns": artifact.boundary_ended_at_unix_ns,
        "boundary_elapsed_monotonic_ns": artifact.boundary_elapsed_monotonic_ns,
        "reset_telemetry": _plain(telemetry),
    }


def _science_config(
    *, temperature: float, top_p: float, max_new_tokens: int,
    input_token_limit: int, seed: int, ignore_eos: bool = False,
) -> dict[str, Any]:
    return {
        "temperature": temperature,
        "top_p": top_p,
        "max_new_tokens": max_new_tokens,
        "seed": seed,
        "input_token_limit": input_token_limit,
        "ignore_eos": ignore_eos,
    }


def _logical_seed_int(*parts: object) -> int:
    return int(_opaque(*parts)[:16], 16)


def _prompt_bytes(template_path: Path, payload: Mapping[str, Any]) -> bytes:
    template = template_path.read_bytes()
    try:
        template.decode("ascii", errors="strict")
    except UnicodeDecodeError as exc:
        raise RunnerError(f"prompt template must be ASCII: {template_path}") from exc
    if not template or template.endswith(b"\n"):
        raise RunnerError(f"prompt template must be non-empty without terminal newline: {template_path}")
    return template + b"\nINPUT_JSON\n" + _canonical_json_bytes(dict(payload))


class _FakeTokenizer:
    """Deterministic byte-tokenizer seam used only by CPU dry-runs."""

    @staticmethod
    def encode_bytes(value: bytes) -> tuple[int, ...]:
        return tuple(value)


class _FakeProvider:
    """CPU schedule fixture.  It is never a model or a scientific result."""

    def __init__(self) -> None:
        self.tokenizer = _FakeTokenizer()
        self.calls: list[dict[str, Any]] = []

    def render_user_request(self, content_bytes: bytes) -> bytes:
        return content_bytes

    def call(
        self, *, request_bytes: bytes, stage: str, seed: int,
        run_id: str, life_id: str, arm: str, round_index: int, call_index: int,
    ) -> tuple[bytes, dict[str, Any]]:
        response = (
            b'{"op":"DEFER","reason_code":"INSUFFICIENT_MEMORY"}'
            if stage == "THINK" else
            b'{"op":"PASS","reason_code":"NO_BOUNDED_UPDATE"}'
        )
        row = {
            "fake": True, "request_sha256": _sha256(request_bytes),
            "raw_response_sha256": _sha256(response), "stage": stage,
            "seed": seed, "run_id": run_id, "life_id": life_id,
            "arm": arm, "round_index": round_index, "call_index": call_index,
        }
        self.calls.append(row)
        return response, row


class _RealProvider:
    def __init__(self, factory: ResidentModelFactory) -> None:
        self.factory = factory
        self.tokenizer = factory

    def render_user_request(self, content_bytes: bytes) -> bytes:
        return self.factory.render_user_request(content_bytes)

    def call(
        self, *, request_bytes: bytes, stage: str, seed: int,
        run_id: str, life_id: str, arm: str, round_index: int, call_index: int,
    ) -> tuple[bytes, dict[str, Any]]:
        if stage == "THINK":
            config = _science_config(
                temperature=0.0, top_p=1.0, max_new_tokens=128,
                input_token_limit=8192, seed=seed,
            )
        elif stage == "FULL_CONTEXT":
            config = _science_config(
                temperature=0.2, top_p=0.95, max_new_tokens=256,
                input_token_limit=8192, seed=seed,
            )
        else:
            config = _science_config(
                temperature=0.2, top_p=0.95, max_new_tokens=256,
                input_token_limit=2048, seed=seed,
            )
        artifact, telemetry = invoke_provider_exact(
            self.factory, request_bytes=request_bytes, config=config,
            run_id=run_id, life_id=life_id, arm=arm, stage=stage,
            round_index=round_index, call_index=call_index,
        )
        return artifact.raw_response_bytes, _provider_artifact_row(artifact, telemetry)


def _zero_science_request(resource: Mapping[str, Any], class_row: Mapping[str, Any], call: Mapping[str, Any]) -> bytes:
    generator = resource["generator"]
    prefix = str(generator["prefix_template"]).format(
        class_id=class_row["class_id"], call_index=call["call_index"],
    )
    rendered = (
        prefix + str(generator["filler_unit"]) * int(call["repetition_count"])
        + str(generator["suffix"])
    ).encode("ascii")
    if len(rendered) != int(call["byte_count"]) \
            or _sha256(rendered) != call["input_bytes_sha256"]:
        raise RunnerError("zero-science envelope byte binding mismatch")
    return rendered


def run_zero_science_batch(args: argparse.Namespace) -> dict[str, Any]:
    resource_path = Path(args.envelope_resource)
    resource_raw = resource_path.read_bytes()
    if args.envelope_sha256 and _sha256(resource_raw) != args.envelope_sha256:
        raise RunnerError("zero-science envelope resource hash mismatch")
    resource = json.loads(resource_raw.decode("ascii"))
    if resource["execution"]["total_calls"] != 8 \
            or resource["execution"]["calls_per_class"] != 2:
        raise RunnerError("zero-science resource does not declare exact 2x4 calls")
    factory = build_provider(
        model=args.model, revision=args.revision, engine_kind=args.engine_kind,
    )
    run_id = _opaque("v2e-zero-science", args.run_id)
    rows: list[dict[str, Any]] = []
    for class_row in resource["classes"]:
        class_id = str(class_row["class_id"])
        for call in class_row["calls"]:
            request = _zero_science_request(resource, class_row, call)
            token_ids = factory.encode_bytes(request)
            if len(token_ids) != int(call["input_token_count"]) \
                    or _token_ids_hash(token_ids) != call["token_ids_ascii_sha256"]:
                raise RunnerError("zero-science tokenizer/token-ID binding mismatch")
            logical_seed_material = (
                b"v2d-zero-science-seed\0" + class_id.encode("ascii") + b"\0"
                + str(call["call_index"]).encode("ascii")
            )
            logical_seed_hash = _sha256(logical_seed_material)
            if logical_seed_hash != call["logical_seed_sha256"]:
                raise RunnerError("zero-science logical seed binding mismatch")
            config = _science_config(
                temperature=float(class_row["temperature"]),
                top_p=float(class_row["top_p"]),
                max_new_tokens=int(class_row["output_token_limit"]),
                input_token_limit=int(class_row["input_token_limit"]),
                seed=int(logical_seed_hash[:16], 16), ignore_eos=True,
            )
            stage = {
                "dream": "DREAM", "think": "THINK",
                "full_context": "FULL_CONTEXT", "rag": "RAG",
            }[class_id]
            artifact, telemetry = invoke_provider_exact(
                factory, request_bytes=request, config=config, run_id=run_id,
                life_id=_opaque("zero-life", class_id), arm="synthetic",
                stage=stage, round_index=int(call["call_index"]),
                call_index=len(rows),
            )
            if telemetry.generated_token_count != int(class_row["output_token_limit"]):
                raise RunnerError("capacity preflight failed to generate exact maximum")
            if telemetry.active_sequences_before != 0 \
                    or telemetry.active_sequences_after != 0 \
                    or telemetry.request_truncated \
                    or telemetry.prefix_cache_hits != 0:
                raise RunnerError("zero-science provider isolation/reset failure")
            rows.append({
                "class_id": class_id, "call_index": int(call["call_index"]),
                "logical_seed_sha256": logical_seed_hash,
                "provider": _provider_artifact_row(artifact, telemetry),
            })
    if len({row["provider"]["receipt"]["provider_session_id"] for row in rows}) != 8 \
            or len({row["provider"]["receipt"]["provider_request_id"] for row in rows}) != 8:
        raise RunnerError("zero-science session/request identifiers are not unique")
    result = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "zero_science_resident_provider_batch",
        "resource_sha256": _sha256(resource_raw),
        "model": args.model, "revision": args.revision,
        "engine_kind": args.engine_kind, "calls": rows,
        "zero_science_preflight": "pass",
    }
    result["artifact_sha256"] = _hash_json(result)
    _write_json_once(Path(args.out), result)
    return result


def _run_child(command: Sequence[str]) -> None:
    completed = subprocess.run(list(command), check=False)
    if completed.returncode != 0:
        raise RunnerError(
            f"isolated phase process failed with exit code {completed.returncode}"
        )


def run_science_parent(args: argparse.Namespace) -> dict[str, Any]:
    if not (
        args.phase_a_before_scorer and args.analysis_scope_after_phase_a
        and args.offline_scorer_only
    ):
        raise RunnerError("all three v2e phase-isolation assertions are mandatory")
    job_dir = Path(args.job_dir).resolve()
    artifacts = job_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    common = [
        "--run-id", args.run_id, "--job-dir", str(job_dir),
        "--model", args.model, "--revision", args.revision,
        "--engine-kind", args.engine_kind,
    ]
    _run_child([
        sys.executable, "-m", __name__, "phase-a", *common,
        *( ["--cpu-fake"] if args.cpu_fake else [] ),
    ])
    _run_child([
        sys.executable, "-m", __name__, "phase-b", *common,
    ])
    result = {
        "schema_version": SCHEMA_VERSION,
        "run_id": args.run_id,
        "phase_a_raw_seal": str(artifacts / "phase_a_raw_seal.json"),
        "phase_b_scored_graph": str(artifacts / "phase_b_scored_graph.json"),
        "science_runner": "complete_human_stop_required",
    }
    print(_canonical_json_bytes(result).decode("ascii"), flush=True)
    return result

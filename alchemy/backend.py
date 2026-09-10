"""Pluggable LLM backends: 'hf' (local smoke, MPS/CPU) and 'vllm' (node).

One interface: generate(prompts, max_tokens, lora_path=None) -> [str].
vLLM serves LoRA arms as adapters (enable_lora); HF applies peft directly.
"""

from __future__ import annotations

import hashlib
import json


def _canonical_bytes(value) -> bytes:
    """Stable bytes for token/output audit hashes across Python versions."""
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256_canonical(value) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _exact_usage(*, prompt_ids, output_ids, original_prompt_tokens: int,
                 prompt_truncated: bool, decoded_output: str) -> dict:
    """Build an auditable usage record from the IDs actually used by a model."""
    supplied = [int(token_id) for token_id in prompt_ids]
    generated = [int(token_id) for token_id in output_ids]
    return {
        "prompt_tokens": len(supplied),
        "output_tokens": len(generated),
        "original_prompt_tokens": int(original_prompt_tokens),
        "prompt_truncated": bool(prompt_truncated),
        "source": "model",
        # Retain the older spelling for consumers which predate the CLI audit
        # bundle, while making the source required by the new adapter.
        "token_count_source": "model_token_ids",
        "prompt_token_ids_sha256": _sha256_canonical(supplied),
        # The trace contract uses this explicit name; retain the shorter alias
        # for external consumers of the backend usage record.
        "supplied_prompt_token_ids_sha256": _sha256_canonical(supplied),
        "output_token_ids": generated,
        "output_token_ids_sha256": _sha256_canonical(generated),
        "decoded_output": decoded_output,
        "decoded_output_sha256": _sha256_canonical(decoded_output),
        "output_sha256": _sha256_text(decoded_output),
    }


class HFBackend:
    def __init__(self, model_name: str, revision=None):
        from alchemy.lora_mem import load_base
        self.model, self.tok = load_base(model_name, revision=revision)
        self._adapters = {}          # path -> peft model (smoke scale only)
        self.last_usage = []

    def _chat(self, p):
        return self.tok.apply_chat_template(
            [{"role": "user", "content": p}],
            tokenize=False, add_generation_prompt=True)

    def load_adapter(self, path: str):
        from peft import PeftModel
        if path not in self._adapters:
            self._adapters[path] = PeftModel.from_pretrained(
                self.model, path).eval()
        return self._adapters[path]

    def generate(self, prompts, max_tokens=64, lora_path=None,
                 temperature=0.0, seed=None):
        import torch
        model = self.load_adapter(lora_path) if lora_path else self.model
        if seed is not None:
            torch.manual_seed(seed)
        outs = []
        self.last_usage = []
        for p in prompts:
            ids = self.tok(self._chat(p), return_tensors="pt"
                           ).to(model.device)
            prompt_ids = ids["input_ids"][0].detach().cpu().tolist()
            generation = {
                "max_new_tokens": max_tokens,
                "do_sample": temperature > 0,
                "pad_token_id": self.tok.eos_token_id,
            }
            if temperature > 0:
                generation["temperature"] = temperature
            with torch.no_grad():
                g = model.generate(**ids, **generation)
            output_ids = g[0][ids["input_ids"].shape[1]:]
            output_id_list = output_ids.detach().cpu().tolist()
            decoded = self.tok.decode(output_id_list, skip_special_tokens=True).strip()
            outs.append(decoded)
            self.last_usage.append(_exact_usage(
                prompt_ids=prompt_ids,
                output_ids=output_id_list,
                original_prompt_tokens=len(prompt_ids),
                prompt_truncated=False,
                decoded_output=decoded,
            ))
        return outs


class VLLMBackend:
    def __init__(self, model_name: str, enable_lora=False, max_len=32768,
                 gpu_util=0.85, max_lora_rank=32, revision=None):
        from vllm import LLM
        from transformers import AutoTokenizer
        self.llm = LLM(model=model_name, dtype="bfloat16",
                       gpu_memory_utilization=gpu_util,
                       max_model_len=max_len, enable_lora=enable_lora,
                       max_lora_rank=max_lora_rank, revision=revision,
                       tokenizer_revision=revision)
        self.tok = AutoTokenizer.from_pretrained(model_name,
                                                  revision=revision)
        self.max_len = max_len
        self._lora_ids = {}
        self.last_usage = []

    def _chat(self, p):
        return self.tok.apply_chat_template(
            [{"role": "user", "content": p}],
            tokenize=False, add_generation_prompt=True)

    def n_tokens(self, text: str) -> int:
        return len(self.tok(text)["input_ids"])

    def _chat_ids(self, prompt: str) -> list[int]:
        encoded = self.tok.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=True, add_generation_prompt=True,
            # Transformers 5.x defaults this to True and returns a
            # BatchEncoding. vLLM expects the actual token-id list; passing
            # the mapping itself makes it consume ``input_ids`` and
            # ``attention_mask`` as string token IDs.
            return_dict=False,
        )
        if hasattr(encoded, "get") and not isinstance(encoded, list):
            encoded = encoded.get("input_ids")
        if hasattr(encoded, "tolist"):
            encoded = encoded.tolist()
        if (not isinstance(encoded, list)
                or any(not isinstance(token_id, int) for token_id in encoded)):
            raise TypeError(
                "chat template must produce a flat list of integer token IDs"
            )
        return encoded

    def _bounded_chat_ids(self, prompt: str, max_tokens: int):
        """Return the exact IDs supplied to vLLM, preserving chat framing."""
        limit = self.max_len - max_tokens
        full_ids = self._chat_ids(prompt)
        if len(full_ids) <= limit:
            return full_ids, len(full_ids), False

        raw_ids = self.tok(
            prompt, add_special_tokens=False
        )["input_ids"]
        low, high = 0, len(raw_ids)
        best = self._chat_ids("")
        while low <= high:
            keep = (low + high) // 2
            tail = raw_ids[-keep:] if keep else []
            candidate = self._chat_ids(self.tok.decode(
                tail, skip_special_tokens=True
            ))
            if len(candidate) <= limit:
                best = candidate
                low = keep + 1
            else:
                high = keep - 1
        if len(best) > limit:
            raise ValueError("chat template alone exceeds the model window")
        return best, len(full_ids), True

    def generate(self, prompts, max_tokens=64, lora_path=None,
                 temperature=0.0, seed=None):
        from vllm import SamplingParams
        sp = SamplingParams(max_tokens=max_tokens, temperature=temperature,
                            seed=seed)
        prepared = [self._bounded_chat_ids(p, max_tokens) for p in prompts]
        prompt_ids = [item[0] for item in prepared]
        req = None
        if lora_path:
            from vllm.lora.request import LoRARequest
            if lora_path not in self._lora_ids:
                self._lora_ids[lora_path] = len(self._lora_ids) + 1
            req = LoRARequest(lora_path, self._lora_ids[lora_path], lora_path)
        outs = self.llm.generate(
            [{"prompt_token_ids": ids} for ids in prompt_ids], sp,
            lora_request=req,
        )
        self.last_usage = []
        texts = []
        for result, supplied, (_, original_count, truncated) in zip(
                outs, prompt_ids, prepared):
            actual_prompt_ids = getattr(result, "prompt_token_ids", None)
            if actual_prompt_ids is not None and list(actual_prompt_ids) != supplied:
                raise RuntimeError("vLLM changed supplied prompt token IDs")
            generated = result.outputs[0]
            output_ids = getattr(generated, "token_ids", None)
            if output_ids is None:
                raise RuntimeError("vLLM did not expose generated token IDs")
            output_id_list = [int(token_id) for token_id in output_ids]
            decoded = self.tok.decode(output_id_list, skip_special_tokens=True).strip()
            texts.append(decoded)
            self.last_usage.append(_exact_usage(
                prompt_ids=supplied,
                output_ids=output_id_list,
                original_prompt_tokens=original_count,
                prompt_truncated=truncated,
                decoded_output=decoded,
            ))
        return texts


def make_backend(kind: str, model_name: str, **kw):
    return (VLLMBackend(model_name, **kw) if kind == "vllm"
            else HFBackend(model_name, **kw))

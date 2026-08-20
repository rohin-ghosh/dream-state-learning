"""Pluggable LLM backends: 'hf' (local smoke, MPS/CPU) and 'vllm' (node).

One interface: generate(prompts, max_tokens, lora_path=None) -> [str].
vLLM serves LoRA arms as adapters (enable_lora); HF applies peft directly.
"""

from __future__ import annotations


class HFBackend:
    def __init__(self, model_name: str):
        from alchemy.lora_mem import load_base
        self.model, self.tok = load_base(model_name)
        self._adapters = {}          # path -> peft model (smoke scale only)

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

    def generate(self, prompts, max_tokens=64, lora_path=None):
        import torch
        model = self.load_adapter(lora_path) if lora_path else self.model
        outs = []
        for p in prompts:
            ids = self.tok(self._chat(p), return_tensors="pt"
                           ).to(model.device)
            with torch.no_grad():
                g = model.generate(**ids, max_new_tokens=max_tokens,
                                   do_sample=False,
                                   pad_token_id=self.tok.eos_token_id)
            outs.append(self.tok.decode(
                g[0][ids["input_ids"].shape[1]:],
                skip_special_tokens=True).strip())
        return outs


class VLLMBackend:
    def __init__(self, model_name: str, enable_lora=False, max_len=32768,
                 gpu_util=0.85, max_lora_rank=32):
        from vllm import LLM
        from transformers import AutoTokenizer
        self.llm = LLM(model=model_name, dtype="bfloat16",
                       gpu_memory_utilization=gpu_util,
                       max_model_len=max_len, enable_lora=enable_lora,
                       max_lora_rank=max_lora_rank)
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.max_len = max_len
        self._lora_ids = {}

    def _chat(self, p):
        return self.tok.apply_chat_template(
            [{"role": "user", "content": p}],
            tokenize=False, add_generation_prompt=True)

    def n_tokens(self, text: str) -> int:
        return len(self.tok(text)["input_ids"])

    def generate(self, prompts, max_tokens=64, lora_path=None):
        from vllm import SamplingParams
        sp = SamplingParams(max_tokens=max_tokens, temperature=0.0)
        req = None
        if lora_path:
            from vllm.lora.request import LoRARequest
            if lora_path not in self._lora_ids:
                self._lora_ids[lora_path] = len(self._lora_ids) + 1
            req = LoRARequest(lora_path, self._lora_ids[lora_path], lora_path)
        outs = self.llm.generate([self._chat(p) for p in prompts], sp,
                                 lora_request=req)
        return [o.outputs[0].text.strip() for o in outs]


def make_backend(kind: str, model_name: str, **kw):
    return (VLLMBackend(model_name, **kw) if kind == "vllm"
            else HFBackend(model_name))

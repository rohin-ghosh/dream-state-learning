"""vLLM generation backend (wake + sleep THINK-calls) with optional LoRA.
One life = one GPU (set CUDA_VISIBLE_DEVICES before launch).
"""
from __future__ import annotations
import os
import hashlib
import json
from pathlib import Path

MODEL = os.environ.get("V6_MODEL", "Qwen/Qwen2.5-7B-Instruct")


def configured_generation_identity(model_path, adapter_path):
    files = {}
    if adapter_path is not None:
        adapter = Path(adapter_path)
        weights = [name for name in ("adapter_model.safetensors", "adapter_model.bin")
                   if (adapter / name).is_file()]
        if len(weights) != 1:
            raise ValueError("generation adapter weights are missing or ambiguous")
        for name in ("adapter_config.json", *weights):
            digest = hashlib.sha256()
            with open(adapter / name, "rb") as source:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(block)
            files[name] = digest.hexdigest()
    return dict(backend="vllm", model_input=str(model_path),
                adapter_input=str(adapter_path) if adapter_path is not None else None,
                adapter_files=files, default_max_tokens=400, default_temperature=0.7,
                scope="configured loader inputs; base authentication requires lineage pins")


class VLLMBackend:
    def __init__(self, adapter_path: str | None = None,
                 max_model_len: int = 16384):
        os.environ.setdefault("VLLM_WORKER_MULTIPROC_METHOD", "spawn")
        from vllm import LLM
        from vllm.lora.request import LoRARequest
        self._LoRARequest = LoRARequest
        self.adapter_path = adapter_path
        self._generation_identity = configured_generation_identity(MODEL, adapter_path)
        self.llm = LLM(model=MODEL, max_model_len=max_model_len,
                       gpu_memory_utilization=0.85, enforce_eager=True,
                       enable_lora=adapter_path is not None,
                       max_lora_rank=32)
        self.tok = self.llm.get_tokenizer()

    def generation_identity(self):
        return json.loads(json.dumps(self._generation_identity))

    def batch(self, prompts: list[str], max_tokens: int = 400,
              temperature: float = 0.7,
              seeds: list[int] | None = None) -> list[str]:
        from vllm import SamplingParams
        chats = [self.tok.apply_chat_template(
            [{"role": "user", "content": p}],
            tokenize=False, add_generation_prompt=True) for p in prompts]
        if seeds is not None:
            sp = [SamplingParams(max_tokens=max_tokens,
                                 temperature=temperature, seed=s)
                  for s in seeds]
        else:
            sp = SamplingParams(max_tokens=max_tokens,
                                temperature=temperature)
        lora = (self._LoRARequest("life", 1, self.adapter_path)
                if self.adapter_path else None)
        outs = self.llm.generate(chats, sp, lora_request=lora, use_tqdm=False)
        return [o.outputs[0].text for o in outs]

    def __call__(self, prompt: str, max_tokens: int = 400,
                 temperature: float = 0.7, seed: int | None = None) -> str:
        return self.batch([prompt], max_tokens=max_tokens,
                          temperature=temperature,
                          seeds=[seed] if seed is not None else None)[0]


def wait_gpu_free(threshold_mb: int = 3000, timeout_s: int = 90) -> bool:
    """Block until this process's visible GPU is actually free (the vLLM
    EngineCore is a separate process; del/gc in the parent cannot reach its
    CUDA context — poll nvidia-smi instead). Returns True if freed."""
    import subprocess as sp
    import time as _t
    idx = os.environ.get("CUDA_VISIBLE_DEVICES", "0").split(",")[0]
    for _ in range(timeout_s // 3):
        try:
            out = sp.run(["nvidia-smi", "-i", idx,
                          "--query-gpu=memory.used",
                          "--format=csv,noheader,nounits"],
                         capture_output=True, text=True, timeout=15).stdout
            if int(out.strip() or "0") < threshold_mb:
                return True
        except Exception:  # noqa: BLE001
            pass
        _t.sleep(3)
    return False


def _descendants(pid: int) -> list[int]:
    """All descendant PIDs of pid via /proc (Linux node only)."""
    kids: dict[int, list[int]] = {}
    for p in os.listdir("/proc"):
        if not p.isdigit():
            continue
        try:
            with open(f"/proc/{p}/stat") as f:
                parts = f.read().rsplit(")", 1)[1].split()
            kids.setdefault(int(parts[1]), []).append(int(p))
        except (OSError, IndexError, ValueError):
            continue
    out, stack = [], [pid]
    while stack:
        for c in kids.get(stack.pop(), []):
            out.append(c)
            stack.append(c)
    return out


def _kill_engine_descendants() -> int:
    """SIGKILL descendant processes that look like vLLM engine workers.
    Measured necessity: llm.shutdown()+del leaves EngineCore holding the
    GPU (nursery gpu_freed=False; R_B OOM at first sleep)."""
    import signal
    n = 0
    for pid in _descendants(os.getpid()):
        try:
            with open(f"/proc/{pid}/cmdline") as f:
                cmd = f.read()
        except OSError:
            continue
        if ("EngineCore" in cmd or "spawn_main" in cmd
                or "vllm" in cmd.lower()):
            try:
                os.kill(pid, signal.SIGKILL)
                n += 1
            except OSError:
                pass
    return n


def close_backend(backend) -> bool:
    """Shut the engine down and wait for the GPU to actually free.
    Escalates: polite shutdown -> gc -> SIGKILL engine descendants."""
    try:
        backend.llm.shutdown()
    except Exception:  # noqa: BLE001
        pass
    import gc
    del backend
    gc.collect()
    try:
        import torch
        torch.cuda.empty_cache()
    except Exception:  # noqa: BLE001
        pass
    if wait_gpu_free(timeout_s=30):
        return True
    n = _kill_engine_descendants()
    freed = wait_gpu_free(timeout_s=60)
    print(f"[close_backend] escalated: killed {n} engine procs, "
          f"freed={freed}", flush=True)
    return freed

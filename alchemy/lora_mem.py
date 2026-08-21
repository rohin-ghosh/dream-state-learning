"""Parametric memory arm: train a LoRA on the dream corpus, read by
generation (SPEC_V2 §6 Read: no tool call — prompt the adapted model).
Retrained from the FULL corpus each cycle; checkpoint per measurement."""

from __future__ import annotations


def load_base(model_name: str, device: str = "auto"):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_name)
    if device == "auto":
        dev = ("cuda" if torch.cuda.is_available()
               else "mps" if torch.backends.mps.is_available() else "cpu")
    else:
        dev = device
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.float32 if dev == "cpu"
        else torch.float16).to(dev)
    return model, tok


def train_lora(base_model, tokenizer, corpus: list, rank: int = 16,
               epochs: int = 4, lr: float = 2e-4, bsz: int = 32,
               max_len: int = 96, log=print, save_dir: str = ""):
    """Causal-LM fine-tune on memory lines. Returns the adapted model.
    Throughput: length-sorted batching (minimal padding) + shuffled batch
    ORDER per epoch (mixing preserved at batch granularity), bsz 32."""
    import torch
    import numpy as np
    from peft import LoraConfig, get_peft_model
    cfg = LoraConfig(r=rank, lora_alpha=2 * rank, lora_dropout=0.05,
                     target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
                     task_type="CAUSAL_LM")
    model = get_peft_model(base_model, cfg)
    model.train()
    dev = next(model.parameters()).device
    opt = torch.optim.AdamW((p for p in model.parameters()
                             if p.requires_grad), lr=lr)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    corpus = sorted(corpus, key=len)          # length-sorted -> tight pads
    starts = list(range(0, len(corpus), bsz))
    rng = np.random.default_rng(0)
    for ep in range(epochs):
        tot, nb = 0.0, 0
        rng.shuffle(starts)                    # shuffle batch order
        for i in starts:
            batch = tokenizer(corpus[i:i + bsz], return_tensors="pt",
                              padding=True, truncation=True,
                              max_length=max_len).to(dev)
            out = model(**batch, labels=batch["input_ids"].masked_fill(
                batch["attention_mask"] == 0, -100))
            out.loss.backward()
            opt.step(); opt.zero_grad()
            tot += float(out.loss.detach()); nb += 1
        log(f"  [lora] epoch {ep + 1}/{epochs} loss {tot / max(nb, 1):.3f}")
    model.eval()
    if save_dir:
        model.save_pretrained(save_dir)
    return model


def read(model, tokenizer, question: str, max_new_tokens: int = 32) -> str:
    """A read IS a generation from the adapted model."""
    import torch
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": question}],
        tokenize=False, add_generation_prompt=True)
    ids = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        gen = model.generate(**ids, max_new_tokens=max_new_tokens,
                             do_sample=False,
                             pad_token_id=tokenizer.eos_token_id)
    return tokenizer.decode(gen[0][ids["input_ids"].shape[1]:],
                            skip_special_tokens=True).strip()

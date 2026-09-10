"""Qwen2 recurrent retrofit with layer-local, sparsely dispatched LoRA banks.

The decoder implementation is pinned to transformers 4.57.6. No KV cache is
shared across recurrent passes; every pass recomputes causal attention.
"""

from __future__ import annotations

import hashlib
from contextlib import contextmanager
from dataclasses import dataclass

import torch
from torch import nn
from torch.nn import functional as F
from transformers import Qwen2Config, Qwen2ForCausalLM


class LowRank(nn.Module):
    def __init__(self, width: int, rank: int):
        super().__init__()
        self.a = nn.Parameter(torch.empty(rank, width))
        self.b = nn.Parameter(torch.zeros(width, rank))
        nn.init.normal_(self.a, std=0.02)
        self.scale = 1 / rank

    def forward(self, x, plastic=True):
        a, b = (self.a, self.b) if plastic else (self.a.detach(), self.b.detach())
        return F.linear(F.linear(x, a), b) * self.scale


class RoutedMLP(nn.Module):
    def __init__(
        self, base: nn.Module, width: int, experts: int, top_k: int, rank: int
    ):
        super().__init__()
        self.base = base
        self.recur = LowRank(width, rank)
        self.router = nn.Linear(width, experts, bias=False)
        self.experts = nn.ModuleList(LowRank(width, rank) for _ in range(experts))
        self.top_k = top_k
        self.allowed = None
        self.ablated: set[int] = set()
        self.traces = []

    def forward(self, x):
        shape = x.shape
        flat = x.reshape(-1, shape[-1])
        probs = self.router(flat).float().softmax(-1)
        weights, indices = probs.topk(self.top_k, dim=-1)
        weights = weights / weights.sum(-1, keepdim=True)
        routed = torch.zeros_like(probs).scatter(-1, indices, weights)
        # These remain attached during training: router and state gradients must flow.
        self.traces.append((probs, routed.reshape(*shape[:-1], -1)))
        delta = torch.zeros_like(flat)
        for e, expert in enumerate(self.experts):
            if e in self.ablated:
                continue
            rows, slots = (indices == e).nonzero(as_tuple=True)
            if rows.numel():
                trainable = self.allowed is None or e in self.allowed
                update = expert(flat[rows], plastic=trainable)
                delta = delta.index_add(
                    0, rows, update * weights[rows, slots, None].to(x.dtype)
                )
        return self.base(x) + self.recur(x) + delta.reshape(shape)


@dataclass
class RecurrentOutput:
    logits: torch.Tensor
    states: list[torch.Tensor]
    routes: dict[int, torch.Tensor]  # layer -> [T, batch, tokens, experts]
    balance_loss: torch.Tensor


class RecurrentQwen(nn.Module):
    def __init__(
        self, base: Qwen2ForCausalLM, start: int, end: int, experts=4, top_k=2, rank=8
    ):
        super().__init__()
        if base.config.model_type != "qwen2":
            raise ValueError("V0 supports dense Qwen2/Qwen2.5 only")
        if not 0 < start < end < len(base.model.layers):
            raise ValueError("Need nonempty prelude, recurrent core, and coda")
        if not 1 <= top_k <= experts or rank < 1:
            raise ValueError("Require 1 <= top_k <= experts and rank >= 1")
        if base.config.use_sliding_window:
            raise ValueError("V0 requires full causal attention")
        self.base = base
        self.start, self.end = start, end
        self.spec = {
            "start": start,
            "end": end,
            "experts": experts,
            "top_k": top_k,
            "rank": rank,
        }
        width = base.config.hidden_size
        for l in range(start, end):
            base.model.layers[l].mlp = RoutedMLP(
                base.model.layers[l].mlp, width, experts, top_k, rank
            )
        self.bridge = nn.Linear(width, width, bias=False)
        nn.init.eye_(self.bridge.weight)
        self.gate_logit = nn.Parameter(torch.tensor(2.0))
        self.to(device=base.device, dtype=base.dtype)
        self.set_phase("experience")

    @property
    def banks(self):
        return {l: self.base.model.layers[l].mlp for l in range(self.start, self.end)}

    def plastic_named_parameters(self):
        for l, bank in self.banks.items():
            for e, expert in enumerate(bank.experts):
                for name, p in expert.named_parameters():
                    yield f"{l}.{e}.{name}", p

    def set_phase(self, phase):
        if phase not in ("retrofit", "experience", "frozen"):
            raise ValueError(phase)
        self.requires_grad_(False)
        for p in self.parameters():
            p.grad = None
        if phase == "retrofit":
            self.bridge.requires_grad_(True)
            self.gate_logit.requires_grad_(True)
            for bank in self.banks.values():
                bank.recur.requires_grad_(True)
                bank.router.requires_grad_(True)
        elif phase == "experience":
            for _, p in self.plastic_named_parameters():
                p.requires_grad_(True)
        self.eval()  # deterministic substrate, including during gradient updates

    def plastic_state(self):
        return {
            name: p.detach().cpu().clone()
            for name, p in self.plastic_named_parameters()
        }

    def load_plastic(self, state):
        params = dict(self.plastic_named_parameters())
        if params.keys() != state.keys():
            raise ValueError("Plastic checkpoint topology mismatch")
        if any(params[n].shape != state[n].shape for n in params):
            raise ValueError("Plastic checkpoint shape mismatch")
        with torch.no_grad():
            for name, p in params.items():
                p.copy_(state[name])

    def stable_digest(self):
        plastic_ids = {id(p) for _, p in self.plastic_named_parameters()}
        digest = hashlib.sha256()
        for name, p in self.named_parameters():
            if id(p) not in plastic_ids:
                digest.update(name.encode())
                digest.update(
                    p.detach()
                    .cpu()
                    .contiguous()
                    .reshape(-1)
                    .view(torch.uint8)
                    .numpy()
                    .tobytes()
                )
        return digest.hexdigest()

    @contextmanager
    def eligibility(self, mask):
        previous = {l: bank.allowed for l, bank in self.banks.items()}
        try:
            for l, bank in self.banks.items():
                bank.allowed = set(mask.get(l, []))
            yield
        finally:
            for l, bank in self.banks.items():
                bank.allowed = previous[l]

    @contextmanager
    def ablate(self, pathways):
        previous = {l: set(bank.ablated) for l, bank in self.banks.items()}
        try:
            for l, e in pathways:
                self.banks[l].ablated.add(e)
            yield
        finally:
            for l, bank in self.banks.items():
                bank.ablated = previous[l]

    def forward(self, input_ids, attention_mask=None, loops=1):
        if loops < 1:
            raise ValueError("loops must be positive")
        for bank in self.banks.values():
            bank.traces = []
        decoder = self.base.model
        h = decoder.embed_tokens(input_ids)
        batch, length = input_ids.shape
        positions = torch.arange(length, device=h.device)
        position_ids = positions.unsqueeze(0)
        # Explicit full causal mask; right padding only. No cross-depth KV cache.
        valid = (
            torch.ones_like(input_ids, dtype=torch.bool)
            if attention_mask is None
            else attention_mask.bool()
        )
        allowed = (positions[:, None] >= positions[None, :])[None, None] & valid[
            :, None, None, :
        ]
        mask = torch.zeros((batch, 1, length, length), dtype=h.dtype, device=h.device)
        mask.masked_fill_(~allowed, torch.finfo(h.dtype).min)
        rope = decoder.rotary_emb(h, position_ids)
        kwargs = {
            "attention_mask": mask,
            "position_ids": position_ids,
            "position_embeddings": rope,
            "cache_position": positions,
            "use_cache": False,
        }
        for layer in decoder.layers[: self.start]:
            h = layer(h, **kwargs)
        h0 = h
        states = [h0]
        for t in range(loops):
            # First pass is the original path, exactly, before retrofit training.
            if t:
                gate = self.gate_logit.sigmoid()
                h = gate * h + (1 - gate) * self.bridge(h0)
            for layer in decoder.layers[self.start : self.end]:
                h = layer(h, **kwargs)
            states.append(h)
        for layer in decoder.layers[self.end :]:
            h = layer(h, **kwargs)
        logits = self.base.lm_head(decoder.norm(h))
        routes = {
            l: torch.stack([r for _, r in bank.traces])
            for l, bank in self.banks.items()
        }
        balance = []
        for bank in self.banks.values():
            for probs, routed in bank.traces:
                active = valid.flatten()
                mean_prob = probs[active].mean(0)
                frequency = (
                    (routed.reshape(-1, routed.shape[-1])[active] > 0)
                    .float()
                    .mean(0)
                    .detach()
                )
                balance.append(len(bank.experts) * (mean_prob * frequency).sum())
            bank.traces = []  # don't retain a graph in module state between examples
        return RecurrentOutput(logits, states, routes, torch.stack(balance).mean())


def tiny_base(vocab_size=128, width=32, layers=4):
    config = Qwen2Config(
        vocab_size=vocab_size,
        hidden_size=width,
        intermediate_size=width * 2,
        num_hidden_layers=layers,
        num_attention_heads=4,
        num_key_value_heads=2,
        max_position_embeddings=512,
        attention_dropout=0.0,
        bos_token_id=1,
        eos_token_id=2,
        pad_token_id=0,
        tie_word_embeddings=False,
    )
    config._attn_implementation = "eager"
    return Qwen2ForCausalLM(config)

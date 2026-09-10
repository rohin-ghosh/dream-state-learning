"""Slow substrate training and offline experiential BPTT, with strict masks."""

from __future__ import annotations

import json
import random
from pathlib import Path

import torch
from torch.nn import functional as F

from .data import Episode, episode_id


def task_loss(logits, labels):
    return F.cross_entropy(
        logits[:, :-1].float().reshape(-1, logits.shape[-1]),
        labels[:, 1:].reshape(-1),
        ignore_index=-100,
    )


def foundation_train(base, codec, examples, steps, lr=1e-3):
    """Only for the random tiny model; never update a pretrained foundation."""
    base.train()
    opt = torch.optim.AdamW(base.parameters(), lr=lr, weight_decay=0)
    losses = []
    for step in range(steps):
        ex = examples[step % len(examples)]
        ids, labels = codec.example(ex.prompt, ex.target, base.device)
        loss = task_loss(base(ids, use_cache=False).logits, labels)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(base.parameters(), 1)
        opt.step()
        losses.append(float(loss.detach()))
    base.eval()
    return losses


def retrofit_train(model, codec, examples, steps, depths, lr=1e-3):
    model.set_phase("retrofit")
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=lr, weight_decay=0)
    device = next(model.parameters()).device
    # Initial one-pass teacher. No deployment experience enters this stage.
    teachers = []
    with torch.no_grad():
        for ex in examples:
            ids, _ = codec.example(ex.prompt, ex.target, device)
            teachers.append(model(ids, loops=1).logits.float().softmax(-1).detach())
    losses = []
    for step in range(steps):
        idx = step % len(examples)
        ex = examples[idx]
        ids, labels = codec.example(ex.prompt, ex.target, device)
        output = model(ids, loops=depths[step % len(depths)])
        kl = (
            F.kl_div(
                output.logits.float().log_softmax(-1), teachers[idx], reduction="sum"
            )
            / ids.numel()
        )
        loss = task_loss(output.logits, labels) + 0.5 * kl + 0.01 * output.balance_loss
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(params, 1)
        opt.step()
        losses.append(float(loss.detach()))
    model.set_phase("experience")
    return losses


def action_ids(codec, states):
    ids = [codec.encode(str(i)) for i in range(states)]
    if any(len(row) != 1 for row in ids):
        raise ValueError("This closed-action benchmark requires single-token digits")
    return [row[0] for row in ids]


@torch.no_grad()
def predict(model, codec, prompt, loops, states):
    ids = codec.prompt(prompt, next(model.parameters()).device)
    output = model(ids, loops=loops)
    choice = output.logits[0, -1, action_ids(codec, states)].argmax().item()
    return str(choice), output


@torch.no_grad()
def collect(model, codec, world, tasks, loops, arm, version, repeats=2, seed=0):
    rng = random.Random(seed)
    episodes = []
    for task in tasks:
        for repeat in range(repeats):
            action, output = predict(model, codec, task.prompt, loops, world.states)
            if rng.random() < 0.1:
                action = str(rng.randrange(world.states))
            outcome = world.observe(task, action)
            episodes.append(
                Episode(
                    episode_id(arm, version, task, repeat),
                    task.key,
                    task.prompt,
                    action,
                    outcome["final_state"],
                    outcome["reward"],
                    version,
                    loops,
                    [
                        {
                            "mean": float(h.float().mean()),
                            "rms": float(h.float().square().mean().sqrt()),
                            "last_token": h[0, -1].float().cpu().tolist(),
                        }
                        for h in output.states
                    ],
                    {
                        l: r[:, 0].float().cpu().tolist()
                        for l, r in output.routes.items()
                    },
                )
            )
    return episodes


def train_cycle(
    model,
    codec,
    new,
    replay,
    retention,
    loops,
    steps,
    seed=0,
    lr=2e-3,
    replay_weight=0.5,
    behavior_weight=0.1,
    dynamics_weight=0.1,
    sparsity_weight=1e-4,
):
    model.set_phase("experience")
    if not new:
        return []
    device = next(model.parameters()).device
    params = dict(model.plastic_named_parameters())
    old = {n: p.detach().clone() for n, p in params.items()}
    # Teacher is the previous experiential version, computed before any update.
    teacher = []
    with torch.no_grad():
        for ex in retention:
            ids = codec.prompt(ex.prompt, device)
            out = model(ids, loops=loops)
            teacher.append(
                (
                    out.logits.float().softmax(-1).detach(),
                    [s.detach() for s in out.states],
                )
            )
    opt = torch.optim.AdamW(params.values(), lr=lr, weight_decay=0)
    rng = random.Random(seed)
    history = []
    for step in range(steps):
        ex = rng.choice(new)
        re = rng.choice(replay) if replay else None
        union = {l: set(ex.eligibility.get(l, [])) for l in model.banks}
        if re:
            for l, eligible in union.items():
                eligible.update(re.eligibility.get(l, []))
        opt.zero_grad(set_to_none=True)
        ids, labels = codec.example(ex.prompt, ex.target, device)
        forward_tokens = ids.numel()
        with model.eligibility(ex.eligibility):
            out = model(ids, loops=loops)
            new_loss = task_loss(out.logits, labels) * ex.weight
        replay_loss = new_loss.new_zeros(())
        if re:
            ids, labels = codec.example(re.prompt, re.target, device)
            forward_tokens += ids.numel()
            with model.eligibility(re.eligibility):
                replay_loss = (
                    task_loss(model(ids, loops=loops).logits, labels) * re.weight
                )
        idx = step % len(retention)
        ids = codec.prompt(retention[idx].prompt, device)
        forward_tokens += ids.numel()
        with model.eligibility(union):
            current = model(ids, loops=loops)
        old_probs, old_states = teacher[idx]
        behavior = (
            F.kl_div(current.logits.float().log_softmax(-1), old_probs, reduction="sum")
            / ids.numel()
        )
        dynamics = torch.stack(
            [
                (a.float() - b.float()).square().mean()
                / b.float().square().mean().clamp_min(1e-6)
                for a, b in zip(current.states[1:], old_states[1:])
            ]
        ).mean()
        # Penalize this cycle's grouped parameter displacement, not absolute LoRA size.
        groups = []
        for l, eligible in union.items():
            for e in eligible:
                diff = torch.cat(
                    [
                        (params[f"{l}.{e}.{n}"] - old[f"{l}.{e}.{n}"]).flatten()
                        for n in ("a", "b")
                    ]
                )
                groups.append(torch.linalg.vector_norm(diff))
        sparsity = torch.stack(groups).sum() if groups else new_loss.new_zeros(())
        loss = (
            new_loss
            + replay_weight * replay_loss
            + behavior_weight * behavior
            + dynamics_weight * dynamics
            + sparsity_weight * sparsity
        )
        if not torch.isfinite(loss):
            model.load_plastic(old)
            raise FloatingPointError("Nonfinite consolidation loss; rolled back cycle")
        if loss.requires_grad:
            loss.backward()  # Full recurrent graph; no hidden-state detach.
            # grad=None also blocks Adam momentum/weight-decay updates outside
            # this step's eligible union. A zero gradient alone is insufficient.
            for name, p in params.items():
                layer, expert, _ = name.split(".")
                if int(expert) not in union[int(layer)]:
                    p.grad = None
            norm = torch.nn.utils.clip_grad_norm_(params.values(), 1)
            if not torch.isfinite(norm):
                model.load_plastic(old)
                raise FloatingPointError(
                    "Nonfinite consolidation gradient; rolled back cycle"
                )
            opt.step()
        history.append(
            {
                "step": step,
                "total": float(loss.detach()),
                "new": float(new_loss.detach()),
                "replay": float(replay_loss.detach()),
                "behavior": float(behavior.detach()),
                "dynamics": float(dynamics.detach()),
                "sparsity": float(sparsity.detach()),
                "core_passes": loops * (3 if re else 2),
                "core_token_passes": loops * forward_tokens,
                "eligible": {l: sorted(v) for l, v in union.items()},
            }
        )
    return history


def save_plastic(model, path, substrate_digest, metadata):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "substrate_digest": substrate_digest,
        "topology": model.spec,
        "metadata": metadata,
        "plastic": model.plastic_state(),
    }
    temp = path.with_suffix(".tmp")
    torch.save(payload, temp)
    temp.replace(path)


def load_plastic(model, path, substrate_digest):
    payload = torch.load(path, map_location="cpu", weights_only=True)
    if (
        payload["schema_version"] != 1
        or payload["substrate_digest"] != substrate_digest
        or payload["topology"] != model.spec
    ):
        raise ValueError("Checkpoint does not match frozen substrate/topology")
    model.load_plastic(payload["plastic"])
    return payload["metadata"]


def restore_substrate(path, device="cpu"):
    """Reconstruct the exact shared substrate without re-downloading a model."""
    from transformers import Qwen2Config, Qwen2ForCausalLM

    from .model import RecurrentQwen

    payload = torch.load(path, map_location="cpu", weights_only=True)
    if payload["schema_version"] != 1:
        raise ValueError("Unsupported substrate checkpoint")
    config = Qwen2Config.from_dict(payload["config"])
    config._attn_implementation = "eager"
    dtype = payload["state_dict"]["base.model.embed_tokens.weight"].dtype
    base = Qwen2ForCausalLM(config).to(device=device, dtype=dtype)
    model = RecurrentQwen(base, **payload["topology"])
    model.load_state_dict(payload["state_dict"], strict=True)
    if model.stable_digest() != payload["substrate_digest"]:
        raise ValueError("Substrate checkpoint checksum mismatch")
    return model


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")

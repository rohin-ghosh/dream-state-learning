"""SVD initialisation of the LoRA subspace (TMEM, Ren et al. arXiv 2606.04536,
Sec. 3.2, eq. 7): for a target weight W in R^{d_out x d_in} with W = U S V^T,

    A0 = S_r V_r^T   (r x d_in; the top-r right singular vectors scaled by
                      their singular values),      B0 = 0,

so Delta_0 = B0 A0 = 0 and training starts at the base policy while B learns
coefficients inside the "high-energy" row space of W. TMEM keeps A frozen
(Table 6: unfreezing gains <= 0.27 F1). Whether S_r is used raw or normalised
is NOT FOUND in the paper: `scale="sigma"` is the stated formula, `"unit"`
uses V_r^T alone (the subspace argument of Theorem 1 without the sigma-squared
step scaling of Remark 1 — which AdamW normalises away anyway).

Default-off everywhere: train_adapter_v3 --svd-init [--freeze-a]. Never
touches the frozen v1 trainer. PEFT's LoRA stores lora_A.weight as
(r, in_features) and lora_B.weight as (out_features, r), so A0 is written
straight into lora_A.weight; B stays at PEFT's zero init.

  from organism_v6.lora_svd_init import svd_subspace, apply_svd_init
  stats = apply_svd_init(peft_model, rank=32, scale="sigma", freeze_a=False)

`svd_subspace` works on numpy arrays (CPU tests, no torch) and torch tensors
(GPU); `--svd-method exact|lowrank` picks torch.linalg.svd or a randomised
torch.svd_lowrank for the 7B's 18944 x 3584 FFN matrices; results are cached
per (module, rank, scale) in --svd-cache when given.
"""
from __future__ import annotations
import hashlib
import json
import os
import time


def svd_subspace(W, rank: int, scale: str = "sigma", method: str = "exact",
                 niter: int = 6, oversample: int = 16):
    """Top-`rank` right singular subspace of W (d_out x d_in) as A0 with shape
    (rank, d_in). numpy in -> numpy out; torch in -> torch out (same device,
    computed in float32)."""
    if scale not in ("sigma", "unit"):
        raise ValueError(f"scale must be sigma|unit, got {scale!r}")
    try:
        import torch
        is_torch = isinstance(W, torch.Tensor)
    except ImportError:          # numpy-only environment
        torch = None
        is_torch = False
    if is_torch:
        Wf = W.detach().to(torch.float32)
        r = int(min(rank, min(Wf.shape)))
        if method == "lowrank":
            q = int(min(min(Wf.shape), r + oversample))
            U, S, V = torch.svd_lowrank(Wf, q=q, niter=niter)     # V: (d_in, q)
            S, V = S[:r], V[:, :r]
            Vt = V.T
        else:
            U, S, Vh = torch.linalg.svd(Wf, full_matrices=False)
            S, Vt = S[:r], Vh[:r]
        A0 = (S[:, None] * Vt) if scale == "sigma" else Vt
        return A0.contiguous()
    import numpy as np
    Wf = np.asarray(W, dtype=np.float32)
    r = int(min(rank, min(Wf.shape)))
    U, S, Vt = np.linalg.svd(Wf, full_matrices=False)
    S, Vt = S[:r], Vt[:r]
    return (S[:, None] * Vt) if scale == "sigma" else Vt


def subspace_energy(W, A0) -> float:
    """rho: fraction of ||W||_F^2 inside the row space of A0 (unit-normalised
    rows), the quantity Theorem 1 conditions on — logged per matrix."""
    import numpy as np
    Wf = np.asarray(getattr(W, "detach", lambda: W)().cpu() if hasattr(W, "cpu") else W, dtype=np.float32)
    A = np.asarray(getattr(A0, "detach", lambda: A0)().cpu() if hasattr(A0, "cpu") else A0, dtype=np.float32)
    norms = np.linalg.norm(A, axis=1, keepdims=True)
    Q = A / np.maximum(norms, 1e-12)
    proj = Wf @ Q.T                                    # (d_out, r)
    tot = float((Wf ** 2).sum())
    return float((proj ** 2).sum() / tot) if tot > 0 else 0.0


def _lora_layers(peft_model):
    """(name, module) for every module carrying lora_A / lora_B dicts."""
    out = []
    for name, mod in peft_model.named_modules():
        if hasattr(mod, "lora_A") and hasattr(mod, "lora_B") and hasattr(mod, "base_layer"):
            out.append((name, mod))
    return out


def apply_svd_init(peft_model, rank: int, scale: str = "sigma", freeze_a: bool = False,
                   method: str = "exact", cache_dir=None, adapter_name: str = "default",
                   log=print) -> dict:
    """Overwrite every LoRA A with the SVD subspace of its base weight; zero B;
    optionally freeze A. Returns per-matrix stats (shape, top/bottom sigma,
    rho, seconds) for the manifest."""
    import torch
    stats = dict(rank=rank, scale=scale, method=method, freeze_a=freeze_a, matrices={},
                 seconds=0.0)
    t0 = time.time()
    for name, mod in _lora_layers(peft_model):
        if adapter_name not in mod.lora_A:
            continue
        W = mod.base_layer.weight
        r = mod.lora_A[adapter_name].weight.shape[0]
        key = None
        A0 = None
        cached = False
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
            h = hashlib.sha1(f"{name}|{tuple(W.shape)}|{r}|{scale}|{method}".encode()).hexdigest()[:16]
            key = os.path.join(cache_dir, f"{h}.pt")
            if os.path.exists(key):
                A0 = torch.load(key, map_location=W.device)
                cached = True
        t1 = time.time()
        if A0 is None:
            A0 = svd_subspace(W, r, scale=scale, method=method)
            if key:
                torch.save(A0.cpu(), key)
        with torch.no_grad():
            mod.lora_A[adapter_name].weight.copy_(A0.to(mod.lora_A[adapter_name].weight.dtype))
            mod.lora_B[adapter_name].weight.zero_()
        mod.lora_A[adapter_name].weight.requires_grad_(not freeze_a)
        sig = torch.linalg.vector_norm(A0.float(), dim=1)
        stats["matrices"][name] = dict(shape=list(W.shape), r=int(r),
                                       row_norm_top=round(float(sig[0]), 4),
                                       row_norm_bottom=round(float(sig[-1]), 4),
                                       seconds=round(time.time() - t1, 3), cached=cached)
    stats["n_matrices"] = len(stats["matrices"])
    stats["seconds"] = round(time.time() - t0, 2)
    n_train = sum(p.numel() for p in peft_model.parameters() if p.requires_grad)
    stats["trainable_params_after"] = int(n_train)
    log(f"[svd-init] {stats['n_matrices']} matrices, rank {rank}, scale {scale}, "
        f"freeze_a={freeze_a}, {stats['seconds']}s, trainable={n_train}")
    return stats


def write_stats(stats: dict, path: str) -> None:
    with open(path, "w") as f:
        json.dump(stats, f, indent=1)

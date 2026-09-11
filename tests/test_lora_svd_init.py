"""lora_svd_init: A0 = Sigma_r V_r^T on numpy (always) and torch (when
importable), the subspace-energy diagnostic, and apply_svd_init on a tiny
PEFT model (frozen A, zero B, cache).

  <python> tests/test_lora_svd_init.py
"""
from __future__ import annotations

import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

from organism_v6 import lora_svd_init as lsi  # noqa: E402

SKIPPED = []


def test_numpy_subspace_is_sigma_scaled_right_singular_vectors():
    import numpy as np
    rng = np.random.default_rng(0)
    U = np.linalg.qr(rng.normal(size=(40, 40)))[0][:, :5]
    V = np.linalg.qr(rng.normal(size=(24, 24)))[0][:, :5]
    S = np.array([9.0, 5.0, 3.0, 1.0, 0.5])
    W = (U * S) @ V.T                              # exact rank 5, d_out 40, d_in 24
    A0 = lsi.svd_subspace(W, 3)
    assert A0.shape == (3, 24)
    G = A0 @ A0.T                                  # rows orthogonal, norms = sigma
    assert np.allclose(G, np.diag(S[:3] ** 2), atol=1e-4)
    # the rows span the top-3 right singular subspace of W
    P = V[:, :3] @ V[:, :3].T
    assert np.allclose(A0 @ P, A0, atol=1e-4)
    A1 = lsi.svd_subspace(W, 3, scale="unit")
    assert np.allclose(A1 @ A1.T, np.eye(3), atol=1e-4)
    # energy: rank-5 W lies entirely in its own top-5 right space; the top-3 space holds most of it
    assert abs(lsi.subspace_energy(W, lsi.svd_subspace(W, 5)) - 1.0) < 1e-4
    rho3 = lsi.subspace_energy(W, A0)
    assert abs(rho3 - float((S[:3] ** 2).sum() / (S ** 2).sum())) < 1e-4
    # rank larger than min(shape) is clipped
    assert lsi.svd_subspace(W, 100).shape == (24, 24)
    try:
        lsi.svd_subspace(W, 3, scale="bogus")
    except ValueError:
        pass
    else:
        raise AssertionError("bad scale accepted")


def _torch_ok():
    try:
        import torch  # noqa: F401
        import peft  # noqa: F401
        return True
    except ImportError:
        return False


def test_torch_matches_numpy_and_lowrank_spans_the_same_space():
    if not _torch_ok():
        SKIPPED.append("torch/peft not importable")
        print("SKIP torch/peft not importable")
        return
    import numpy as np
    import torch
    torch.manual_seed(0)
    W = torch.randn(48, 20)
    A_t = lsi.svd_subspace(W, 4)
    A_n = lsi.svd_subspace(W.numpy(), 4)
    # singular vectors are defined up to sign: compare row-wise up to sign
    for i in range(4):
        d = min(np.abs(A_t[i].numpy() - A_n[i]).max(), np.abs(A_t[i].numpy() + A_n[i]).max())
        assert d < 1e-3, (i, d)
    A_l = lsi.svd_subspace(W, 4, method="lowrank", niter=8)
    # same row space: projecting exact rows onto the lowrank rows loses ~nothing
    Q = torch.linalg.qr(A_l.T)[0]                   # (20, 4) orthonormal basis of the lowrank space
    resid = A_t - (A_t @ Q) @ Q.T
    assert float(resid.abs().max()) < 5e-2, float(resid.abs().max())


def test_apply_svd_init_writes_a_zeroes_b_freezes_and_caches():
    if not _torch_ok():
        SKIPPED.append("torch/peft not importable")
        print("SKIP torch/peft not importable")
        return
    import torch
    from peft import LoraConfig, get_peft_model
    torch.manual_seed(0)
    lin = torch.nn.Sequential()
    lin.add_module("proj", torch.nn.Linear(24, 40, bias=False))
    lin.add_module("other", torch.nn.Linear(40, 8, bias=False))
    W = lin.proj.weight.detach().clone()
    model = get_peft_model(lin, LoraConfig(r=3, lora_alpha=6, target_modules=["proj"]))
    cache = tempfile.mkdtemp(prefix="svdcache_")
    stats = lsi.apply_svd_init(model, 3, scale="sigma", freeze_a=True, cache_dir=cache, log=lambda s: None)
    assert stats["n_matrices"] == 1 and stats["freeze_a"] and os.listdir(cache)
    layer = [m for n, m in model.named_modules() if hasattr(m, "lora_A")][0]
    A = layer.lora_A["default"].weight
    B = layer.lora_B["default"].weight
    assert torch.allclose(A.detach(), lsi.svd_subspace(W, 3), atol=1e-5)
    assert float(B.abs().sum()) == 0.0 and not A.requires_grad and B.requires_grad
    assert stats["trainable_params_after"] == B.numel()
    # the adapted forward equals the base forward (Delta_0 = B0 A0 = 0)
    x = torch.randn(5, 24)
    assert torch.allclose(model(x), lin.other(lin.proj.base_layer(x)) if hasattr(lin.proj, "base_layer")
                          else torch.nn.functional.linear(torch.nn.functional.linear(x, W), lin.other.weight), atol=1e-5)
    # second call hits the cache
    stats2 = lsi.apply_svd_init(model, 3, scale="sigma", freeze_a=False, cache_dir=cache, log=lambda s: None)
    assert list(stats2["matrices"].values())[0]["cached"] and A.requires_grad


if __name__ == "__main__":
    import traceback
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    failed = 0
    for n, f in tests:
        try:
            f()
            print("PASS", n)
        except Exception:  # noqa: BLE001
            failed += 1
            print("FAIL", n)
            traceback.print_exc()
    print(f"{len(tests) - failed}/{len(tests)} passed"
          + (f" ({len(SKIPPED)} skipped: {SKIPPED})" if SKIPPED else ""))
    sys.exit(1 if failed else 0)

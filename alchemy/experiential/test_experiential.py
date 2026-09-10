"""Causal, optimization, and benchmark-integrity regressions; no downloads."""

import copy

import pytest
import torch

from .data import (
    Codec,
    Episode,
    Example,
    HiddenRuleWorld,
    consolidate,
    eligibility_from_routes,
    retention_examples,
)
from .learning import (
    collect,
    load_plastic,
    restore_substrate,
    retrofit_train,
    save_plastic,
    task_loss,
    train_cycle,
)
from .model import RecurrentQwen, tiny_base


@pytest.fixture
def model():
    torch.set_num_threads(1)
    torch.manual_seed(17)
    return RecurrentQwen(tiny_base(width=16), 1, 3, experts=3, top_k=1, rank=2)


def test_single_pass_preserves_stock_model_with_padding():
    torch.manual_seed(5)
    base = tiny_base(width=16).eval()
    clone = copy.deepcopy(base)
    ids = torch.tensor([[10, 11, 12, 13], [10, 15, 0, 0]])
    mask = torch.tensor([[1, 1, 1, 1], [1, 1, 0, 0]])
    expected = clone(ids, attention_mask=mask, use_cache=False).logits
    recurrent = RecurrentQwen(base, 1, 3)
    actual = recurrent(ids, attention_mask=mask, loops=1).logits
    torch.testing.assert_close(
        actual[mask.bool()], expected[mask.bool()], rtol=1e-5, atol=1e-6
    )


def test_recurrence_is_causal_and_finite(model):
    x = torch.tensor([[10, 11, 12, 13]])
    y = torch.tensor([[10, 11, 30, 40]])
    with torch.no_grad():
        for depth in (1, 2, 4, 8, 16):
            a, b = model(x, loops=depth), model(y, loops=depth)
            assert torch.isfinite(a.logits).all()
            torch.testing.assert_close(a.logits[:, :2], b.logits[:, :2])
            assert len(a.states) == depth + 1
            for trace in a.routes.values():
                assert trace.shape[:3] == (depth, 1, 4)
                torch.testing.assert_close(
                    trace.sum(-1), torch.ones_like(trace[..., 0])
                )
                assert ((trace > 0).sum(-1) == 1).all()


def test_bptt_reaches_early_state_and_experiential_parameters(model):
    ids, labels = Codec().example("State: 1.\nAnswer:", "2", "cpu")
    result = model(ids, loops=4)
    result.states[1].retain_grad()
    task_loss(result.logits, labels).backward()
    assert result.states[1].grad.abs().sum() > 0
    assert any(
        p.grad is not None and p.grad.abs().sum() > 0
        for _, p in model.plastic_named_parameters()
    )
    assert all(
        p.grad is None for n, p in model.named_parameters() if not p.requires_grad
    )


def test_eligibility_uses_selected_routes_and_normalized_exposure():
    trace = [[[0.9, 0.1, 0.0], [0.8, 0.2, 0.0]]]
    first = eligibility_from_routes({2: trace}, threshold=0.05, max_experts=1)
    second = eligibility_from_routes({2: trace * 8}, threshold=0.05, max_experts=1)
    assert first == second == {2: [0]}
    assert eligibility_from_routes({2: trace}, threshold=0.95, max_experts=3) == {2: []}


def test_expert_freezing_preserves_input_gradients(model):
    ids = torch.tensor([[10, 11, 12]])
    with model.eligibility({1: [], 2: []}):
        out = model(ids, loops=3)
    assert not out.logits.requires_grad
    bank = model.banks[1]
    x = torch.randn(1, 4, 16, requires_grad=True)
    with model.eligibility({1: [], 2: []}):
        bank(x).square().sum().backward()
    assert x.grad.abs().sum() > 0
    assert all(p.grad is None for _, p in model.plastic_named_parameters())


def test_sparse_adam_steps_and_stable_substrate(model, monkeypatch):
    codec = Codec()
    examples = [
        Example("State: 1.\nAnswer:", "2", {1: [e], 2: [e]}, [str(e)]) for e in range(3)
    ]
    initial = model.plastic_state()
    stable = model.stable_digest()
    original_step = torch.optim.AdamW.step
    checked = []

    def guarded_step(opt, *args, **kwargs):
        inactive = [
            (p, p.detach().clone())
            for group in opt.param_groups
            for p in group["params"]
            if p.grad is None
        ]
        result = original_step(opt, *args, **kwargs)
        for p, before in inactive:
            assert torch.equal(p, before), "Adam changed an ineligible parameter"
        checked.append(len(inactive))
        return result

    monkeypatch.setattr(torch.optim.AdamW, "step", guarded_step)
    losses = train_cycle(
        model, codec, examples, [], retention_examples(3), 3, 9, seed=2, lr=0.01
    )
    assert len(losses) == len(checked) == 9
    assert all(n >= 8 for n in checked)
    assert model.stable_digest() == stable
    assert any(not torch.equal(initial[n], p) for n, p in model.plastic_state().items())


def test_empty_mask_causes_no_update_even_with_regularizers(model):
    before = model.plastic_state()
    ex = Example("Copy: 1.\nAnswer:", "2", {1: [], 2: []}, ["id"])
    train_cycle(model, Codec(), [ex], [], retention_examples(3), 2, 2)
    assert all(torch.equal(before[n], p) for n, p in model.plastic_state().items())


def test_retrofit_changes_only_slow_adapters(model):
    before = {n: p.clone() for n, p in model.named_parameters()}
    plastic = model.plastic_state()
    retrofit_train(model, Codec(), retention_examples(3), 4, [1, 2], lr=0.01)
    assert all(torch.equal(plastic[n], p) for n, p in model.plastic_state().items())
    for n, p in model.named_parameters():
        if not any(
            key in n for key in ("bridge.", "gate_logit", ".recur.", ".router.")
        ):
            assert torch.equal(before[n], p)
    assert any(not torch.equal(before[n], p) for n, p in model.named_parameters())
    assert all("experts." in n for n, p in model.named_parameters() if p.requires_grad)


def test_structural_split_and_outcome_only_consolidation(model):
    world = HiddenRuleWorld(7, 3)
    train, transfer = world.split(7)
    assert not {t.key for t in train} & {t.key for t in transfer}
    pairs = {t.operations for t in train if len(t.operations) == 2}
    assert all(t.operations not in pairs for t in transfer)
    episodes = collect(model, Codec(), world, train[:2], 2, "test", 0)
    examples, rejected = consolidate(episodes, max_experts=1)
    assert len(examples) == 2
    assert not any(rejected.values())
    assert all(set(e.source_ids) <= {r.episode_id for r in episodes} for e in examples)
    assert all(len(es) <= 1 for e in examples for es in e.eligibility.values())
    assert {e.target for e in examples} <= {r.observation for r in episodes}
    assert {e.prompt for e in examples}.isdisjoint({t.prompt for t in transfer})


def test_consolidation_rejects_noise_and_duplicate_support():
    row = Episode("a", "task", "prompt", "0", "1", 0, 0, 1, [], {1: [[[1.0, 0.0]]]})
    assert consolidate([row, row])[1]["insufficient_support"] == 1
    other = copy.deepcopy(row)
    other.episode_id, other.observation = "b", "2"
    assert consolidate([row, other])[1]["conflicting_outcome"] == 1


def test_checkpoint_roundtrip_and_mismatch(model, tmp_path):
    digest = model.stable_digest()
    initial = model.plastic_state()
    path = tmp_path / "v0.pt"
    save_plastic(model, path, digest, {"version": 0})
    with torch.no_grad():
        for _, p in model.plastic_named_parameters():
            p.add_(1)
    assert load_plastic(model, path, digest) == {"version": 0}
    assert all(torch.equal(initial[n], p) for n, p in model.plastic_state().items())
    with pytest.raises(ValueError):
        load_plastic(model, path, "wrong-substrate")


def test_ablation_restores_even_after_exception(model):
    for bank in model.banks.values():
        for e in bank.experts:
            torch.nn.init.normal_(e.b, std=0.1)
    ids = torch.tensor([[10, 11, 12]])
    before = model(ids, loops=3).logits.detach()
    with (
        pytest.raises(RuntimeError),
        model.ablate([(l, e) for l in model.banks for e in range(3)]),
    ):
        during = model(ids, loops=3).logits.detach()
        raise RuntimeError("interrupted intervention")
    assert not torch.equal(before, during)
    torch.testing.assert_close(model(ids, loops=3).logits, before)


def test_full_substrate_restoration(model, tmp_path):
    path = tmp_path / "substrate.pt"
    torch.save(
        {
            "schema_version": 1,
            "config": model.base.config.to_dict(),
            "topology": model.spec,
            "state_dict": model.state_dict(),
            "substrate_digest": model.stable_digest(),
        },
        path,
    )
    restored = restore_substrate(path)
    ids = torch.tensor([[10, 11, 12]])
    torch.testing.assert_close(
        model(ids, loops=4).logits, restored(ids, loops=4).logits
    )
    assert model.stable_digest() == restored.stable_digest()


def test_consolidation_reduces_observed_outcome_loss(model):
    codec = Codec()
    ids, labels = codec.example("Copy: 1.\nAnswer:", "2", "cpu")
    before = float(task_loss(model(ids, loops=3).logits, labels).detach())
    ex = Example("Copy: 1.\nAnswer:", "2", {1: [0, 1, 2], 2: [0, 1, 2]}, ["observed"])
    train_cycle(model, codec, [ex], [], retention_examples(3), 3, 20, lr=0.03)
    after = float(task_loss(model(ids, loops=3).logits, labels).detach())
    assert after < before - 0.05

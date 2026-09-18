"""Tokenizer-fixture checks only: no network, model, GPU, or fits."""
import copy
import json
import random
from unittest.mock import patch

import pytest

from organism_v6 import fundamental_repetition_corpus as corpus
from organism_v6 import train_adapter_v3 as trainer


class TokenizerFixture:
    eos_token_id = 1
    pad_token_id = 0

    def encode(self, text, add_special_tokens=False):
        assert not add_special_tokens
        pieces = text.split(corpus.EOS)
        tokens = []
        for index, piece in enumerate(pieces):
            if index:
                tokens.append(self.eos_token_id)
            tokens.extend(ord(character) + 2 for character in piece)
        return tokens


@pytest.fixture
def sources():
    rows = [dict(group=f"train-{79 - index:03d}", order=index, view="fixture",
                 spans=[[f"user{corpus.EOS}ask {index}{corpus.EOS}assistant", False, "context"],
                        [f"answer {index}", True, "authored_birth_target"]],
                 meta=dict(source_event_ids=[f"event-{index}"], retained="original"))
            for index in range(corpus.ROWS)]
    return dict(teach=rows, control=copy.deepcopy(rows))


@pytest.fixture
def source_paths(tmp_path, sources, monkeypatch):
    paths, hashes = {}, {}
    for arm, rows in sources.items():
        paths[arm] = tmp_path / f"{arm}.json"
        payload = corpus.json_bytes(dict(corpus=rows))
        paths[arm].write_bytes(payload)
        hashes[arm] = corpus.digest(payload)
    monkeypatch.setattr(corpus, "SOURCE_SHA256", hashes)
    return paths


def material(sources):
    return {arm: corpus.build_views(rows) for arm, rows in sources.items()}


def test_copies_bind_originals_without_mutation_or_new_text(sources):
    before = copy.deepcopy(sources)
    views = corpus.build_views(sources["teach"])
    assert sources == before
    assert len(views["short"]) == 1280 and len(views["long"]) == 80
    for index, original in enumerate(sources["teach"]):
        unit = original["spans"] + [[corpus.EOS, True, original["spans"][1][2]]]
        repeated = views["short"][index * 16:(index + 1) * 16]
        assert [row["meta"]["repetition"]["copy_index"] for row in repeated] == list(range(16))
        assert all(row["spans"] == unit for row in repeated)
        assert views["long"][index]["spans"] == unit * 16
        for row in repeated + [views["long"][index]]:
            assert row["group"] == original["group"] and row["order"] == original["order"]
            assert row["view"] == original["view"]
            assert {key: value for key, value in row["meta"].items() if key != "repetition"} == original["meta"]
            assert row["meta"]["repetition"]["source_row_sha256"] == corpus.digest(corpus.json_bytes(original))
    views["short"][0]["spans"][0][0] = "changed"
    assert views["short"][1]["spans"][0][0] != "changed"
    assert sources == before


def test_native_fixture_budget_and_matched_updates(sources):
    report = corpus.validate_material(sources, material(sources), TokenizerFixture(), (0, 1, 17))
    assert len(report["optimizer_update_groups"]["17"]) == 80
    assert all(len(groups) == 4 for groups in report["optimizer_update_groups"]["17"])
    assert report["optimizer_update_groups"]["0"] != report["optimizer_update_groups"]["1"]
    for budgets in report["arms"].values():
        for name in ("input_tokens", "target_tokens"):
            assert budgets["short"][name] == budgets["long"][name] == 16 * budgets["original"][name]


def test_each_copy_eos_masks_and_full_causal_context(sources):
    tokenizer = TokenizerFixture()
    views = corpus.build_views(sources["teach"])
    short = corpus.encode_rows(views["short"][:16], tokenizer, False)
    long = corpus.encode_rows(views["long"][:1], tokenizer, False)[0]
    width = len(short[0].ids)
    assert long.ids == short[0].ids * 16
    assert long.labels == short[0].labels * 16
    assert sum(label == tokenizer.eos_token_id for label in long.labels) == 16
    assert long.ids.count(tokenizer.eos_token_id) == 48
    for copy_index in range(16):
        assert long.labels[(copy_index + 1) * width - 1] == tokenizer.eos_token_id
        assert long.labels[copy_index * width] == trainer.IGNORE
    batch = trainer.collate([[long]], tokenizer.pad_token_id)
    allowed = trainer.block_causal_allowed(batch["segment_ids"][0])
    assert allowed[width][0] and not allowed[0][width]
    assert batch["position_ids"][0] == list(range(16 * width))
    reset = trainer.collate([[row] for row in short], tokenizer.pad_token_id)
    assert all(positions == list(range(width)) for positions in reset["position_ids"])


def test_v3_actual_epoch_group_order_matches_independent_expectation(sources):
    views = material(sources)
    report = corpus.validate_material(sources, views, TokenizerFixture(), (7,))
    expected = []
    for epoch in range(4):
        groups = sorted(row["group"] for row in sources["teach"])
        random.Random(7000 + epoch).shuffle(groups)
        expected.extend([groups[index:index + 4] for index in range(0, 80, 4)])
    assert report["optimizer_update_groups"]["7"] == expected


def test_unsafe_v3_order_is_reported_not_claimed(sources):
    def unsafe(packs, seed, epoch, shuffle_groups):
        shuffled = list(packs)
        random.Random(seed + epoch).shuffle(shuffled)
        return shuffled
    with patch.object(trainer, "epoch_order", unsafe), pytest.raises(ValueError, match="contiguous"):
        corpus.validate_material(sources, material(sources), TokenizerFixture())


@pytest.mark.parametrize("mutation", ["response", "binding", "group", "eos", "order"])
def test_changed_outputs_are_rejected(sources, mutation):
    views = material(sources)
    row = views["teach"]["long"][0]
    if mutation == "response":
        row["spans"][1][0] = "new answer"
    elif mutation == "binding":
        row["meta"]["source_event_ids"] = ["other"]
    elif mutation == "group":
        row["group"] = "other"
    elif mutation == "order":
        row["order"] = 100
    else:
        row["spans"].pop()
    with pytest.raises(ValueError, match="material or source bindings"):
        corpus.validate_material(sources, views, TokenizerFixture())


@pytest.mark.parametrize("mutation", ["count", "duplicate_group", "binding", "target_eos", "loss"])
def test_invalid_originals_rejected(sources, mutation):
    rows = sources["teach"]
    if mutation == "count":
        rows.pop()
    elif mutation == "duplicate_group":
        rows[1]["group"] = rows[0]["group"]
    elif mutation == "binding":
        rows[0]["meta"].clear()
    elif mutation == "target_eos":
        rows[0]["spans"][1][0] += corpus.EOS
    else:
        rows[0]["spans"][0][1] = True
    with pytest.raises(ValueError):
        corpus.build_views(rows)


def test_overlong_fails_without_splitting_or_truncating(sources):
    for rows in sources.values():
        rows[0]["spans"][0][0] = "context" * 30
    with pytest.raises(ValueError, match="would truncate"):
        corpus.validate_material(sources, material(sources), TokenizerFixture())


def test_bad_eos_encoding_fails(sources):
    class BadEOS(TokenizerFixture):
        def encode(self, text, add_special_tokens=False):
            return [8, 9] if text == corpus.EOS else super().encode(text, add_special_tokens)
    with pytest.raises(ValueError, match="exactly the native EOS"):
        corpus.validate_material(sources, material(sources), BadEOS())


def test_arm_budget_mismatch_fails(sources):
    sources["control"][0]["spans"][1][0] += " extra"
    with pytest.raises(ValueError, match="teach/control budgets"):
        corpus.validate_material(sources, material(sources), TokenizerFixture())


def test_fresh_deterministic_export_hashes_and_explicit_recipe(source_paths, tmp_path):
    outputs = [tmp_path / "first", tmp_path / "second"]
    for out in outputs:
        result = corpus.export_material(**source_paths, out=out, tokenizer=TokenizerFixture())
        assert result["recipes"]["short"]["add_eos"] is False
        assert result["recipes"]["long"]["pack"] is False
        assert result["recipes"]["short"]["grad_accum"] == 16
        assert result["recipes"]["long"]["grad_accum"] == 4
        for name, expected_hash in result["output_sha256"].items():
            assert corpus.digest((out / name).read_bytes()) == expected_hash
    assert {path.name: path.read_bytes() for path in outputs[0].iterdir()} == {
        path.name: path.read_bytes() for path in outputs[1].iterdir()}


@pytest.mark.parametrize("kind", ["directory", "file", "symlink", "dangling"])
def test_refuses_existing_output_without_changes(source_paths, tmp_path, kind):
    out = tmp_path / "output"
    if kind == "directory":
        out.mkdir()
    elif kind == "file":
        out.write_text("preserve")
    else:
        out.symlink_to(tmp_path / ("teach.json" if kind == "symlink" else "absent"))
    with pytest.raises(FileExistsError):
        corpus.export_material(**source_paths, out=out)
    if kind == "file":
        assert out.read_text() == "preserve"
    if kind in ("symlink", "dangling"):
        assert out.is_symlink()


def test_hash_mismatch_fails_before_output(source_paths, tmp_path):
    source_paths["control"].write_text('{"corpus": []}')
    with pytest.raises(ValueError, match="actual source hash mismatch"):
        corpus.export_material(**source_paths, out=tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_material_only_export_does_not_claim_native_validation(source_paths, tmp_path):
    out = tmp_path / "output"
    corpus.main(["--teach", str(source_paths["teach"]), "--control", str(source_paths["control"]),
                 "--out", str(out)])
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["status"] == "NATIVE_AUDIT_PENDING" and manifest["audit"] is None


def test_failed_tokenizer_validation_leaves_no_output(source_paths, tmp_path):
    class BadEOS(TokenizerFixture):
        eos_token_id = 99
    with pytest.raises(ValueError, match="exactly one supervised EOS"):
        corpus.export_material(**source_paths, out=tmp_path / "output", tokenizer=BadEOS())
    assert not (tmp_path / "output").exists()


def test_recipes_parse_with_existing_v3_cli():
    for view, recipe in corpus.RECIPES.items():
        args = trainer.build_parser().parse_args([
            "--corpus", f"teach_{view}.json", "--out", "unused", "--rank", "8", "--alpha", "16",
            "--dropout", "0.05", "--lr", "3e-4", "--epochs", "4", "--max-len", "2048",
            "--no-pack", "--no-eos", "--overflow", "truncate", "--optimizer", "adamw",
            "--batch-size", str(recipe["batch_size"]), "--grad-accum", str(recipe["grad_accum"])])
        config = trainer.config_from_args(args)
        assert all(getattr(config, key) == value for key, value in recipe.items())

"""Pure material, native-token fixtures and saved-text scoring; no model calls."""
import copy
from unittest.mock import patch

import pytest

from organism_v6 import fundamental_two_habit_corpus as corpus


class Tokenizer:
    eos_token_id = 900
    pad_token_id = 901

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        assert tokenize is False and add_generation_prompt is True
        assert len(messages) == 1 and messages[0]["role"] == "user"
        return "<|im_start|>user\n" + messages[0]["content"] + "<|im_end|>\n<|im_start|>assistant\n"

    def encode(self, text, *, add_special_tokens):
        assert add_special_tokens is False
        pieces = text.split(corpus.native.EOS)
        tokens = []
        for index, piece in enumerate(pieces):
            if index:
                tokens.append(self.eos_token_id)
            tokens.extend(ord(character) for character in piece)
        return tokens

    def get_vocab(self):
        return {"fixture_eos": self.eos_token_id}


class UnequalTokenizer(Tokenizer):
    def encode(self, text, *, add_special_tokens):
        tokens = super().encode(text, add_special_tokens=add_special_tokens)
        return tokens + [902] if text.startswith("INPUT:") else tokens


@pytest.fixture
def rows():
    tokenizer = Tokenizer()
    return [dict(spans=[[tokenizer.apply_chat_template([dict(role="user", content=row["context"])],
                                                       tokenize=False, add_generation_prompt=True), False, "context"],
                        [row["response"], True, "authored_birth_target"]],
                 group=row["case_id"], view=row["kind"], order=index,
                 meta=dict(source_event_ids=row["source_event_ids"]))
            for index, row in enumerate(corpus.original.build_candidate()["train_teach"])]


@pytest.fixture
def source_file(tmp_path, rows):
    source = tmp_path / "original-teach.json"
    source.write_bytes(corpus.encoded(dict(corpus=rows)))
    fixture_hash = corpus.base.digest(source)
    with patch.object(corpus, "SOURCE_SHA256", fixture_hash):
        pins = dict(source_sha256=fixture_hash, source_code_sha256=corpus.source_hashes(), model_files={})
        yield source, pins


def test_exact_counts_order_inventory_and_no_mutation(rows):
    before = copy.deepcopy(rows)
    material = corpus.build_material(rows)
    assert rows == before
    assert len(material["inventory"]) == 80
    for arm in corpus.ARMS:
        output = material["corpora"][arm]
        assert len(output) == 80
        assert sum(row["view"] == "addition" for row in output) == 64
        assert sum(row["view"] == "memory" for row in output) == 16
        for index, (old, new) in enumerate(zip(rows, output)):
            assert new["spans"][0] == old["spans"][0]
            assert {key: value for key, value in new.items() if key != "spans"} == {
                key: value for key, value in old.items() if key != "spans"}
            assert material["inventory"][index]["source_row_sha256"] == corpus.digest(corpus.encoded(old))
            if old["view"] == "memory":
                assert corpus.encoded(new) == corpus.encoded(old)


def test_targets_are_exact_sourced_line_permutation(rows):
    material = corpus.build_material(rows)
    events = {event["id"]: event for event in material["source_records"]}
    for before, after, inventory in zip(*[material["corpora"][arm] for arm in corpus.ARMS], material["inventory"]):
        assert sorted(before["spans"][1][0].splitlines()) == sorted(after["spans"][1][0].splitlines())
        assert inventory["ordered_lines"]["input_before"] == before["spans"][1][0].splitlines()
        assert inventory["line_inventory"] == sorted(after["spans"][1][0].splitlines())
        if before["view"] == "addition":
            source = events[before["meta"]["source_event_ids"][0]]
            left, right = source["left"], source["right"]
            assert before["spans"][1][0] == f"INPUT: {left}, {right}\nPREDICT: {left + right}\nACT: {left + right}"
            assert after["spans"][1][0] == f"PREDICT: {left + right}\nACT: {left + right}\nINPUT: {left}, {right}"
            assert corpus.score_addition(before["spans"][1][0], left, right)["joint"]
            assert not corpus.score_addition(after["spans"][1][0], left, right)["joint"]
            assert corpus.score_addition(after["spans"][1][0], left, right)["form_a"]


def test_frozen48_original_prompts_and64_unrequested():
    panels = corpus.panels()
    assert panels["dev"] == corpus.readout.selected_cases()
    assert panels["requests"] == corpus.readout.requests(corpus.readout.selected_cases())
    assert len(panels["unrequested_case_ids"]) == 64
    assert not set(panels["unrequested_case_ids"]) & set(corpus.readout.CASE_IDS)
    for request, case in zip(panels["requests"], panels["dev"]):
        assert request["prompt"] == case["context"]
        assert not any(label in request["prompt"] for label in ("INPUT", "PREDICT", "COMPUTED"))
        assert request["temperature"] == 0 and request["seed"] == 20260912 and request["max_tokens"] == 64


def test_train_dev_pairs_disjoint_even_reversed():
    original = corpus.original.build_candidate()
    events = {row["id"]: row for row in original["source_records"]}
    def pairs(rows):
        sources = [events[row["source_event_ids"][0]] for row in rows if row["kind"] == "addition"]
        return {tuple(sorted((row["left"], row["right"]))) for row in sources}
    train = pairs(original["train_teach"])
    dev = pairs(corpus.panels()["dev"])
    assert len(train) == 64 and len(dev) == 32 and train.isdisjoint(dev)


def test_fixed_recipe_budget_and_independent_copies(rows):
    recipe = corpus.RECIPE
    assert recipe["lr"] == 1e-4 and recipe["seeds"] == [0, 1, 2]
    assert (recipe["rank"], recipe["alpha"], recipe["dropout"]) == (8, 16, .05)
    assert recipe["target_modules"] == list(corpus.trainer.ALL_PROJ)
    assert recipe["epochs"] * 80 // recipe["batch_size"] // recipe["grad_accum"] == 80
    assert recipe["initialization"] == "ORIGINAL_TEACHING_PARENT_WEIGHT_ONLY_FRESH_OPTIMIZER"
    assert not recipe["pack"] and recipe["add_eos"] and recipe["max_len"] == 512
    material = corpus.build_material(rows)
    material["corpora"]["input_before"][0]["meta"]["source_event_ids"].append("bad")
    assert material["corpora"]["input_after"][0] == corpus.build_material(rows)["corpora"]["input_after"][0]


@pytest.mark.parametrize("fault", ["missing", "duplicate", "reordered", "group", "source", "response", "mask", "order", "extra"])
def test_source_binding_rejects_drift(rows, fault):
    if fault == "missing":
        rows.pop()
    elif fault == "duplicate":
        rows[1] = copy.deepcopy(rows[0])
    elif fault == "reordered":
        rows[0], rows[1] = rows[1], rows[0]
    elif fault == "group":
        rows[0]["group"] = "eval-addition-000"
    elif fault == "source":
        rows[0]["meta"]["source_event_ids"] = ["new-source"]
    elif fault == "response":
        rows[0]["spans"][1][0] = "ACT: 999"
    elif fault == "mask":
        rows[0]["spans"][0][1] = 0
    elif fault == "order":
        rows[0]["order"] = True
    else:
        rows[0]["extra"] = "not original"
    with pytest.raises(ValueError):
        corpus.build_material(rows)


def test_native_ids_masks_eos_counts_memory_and_orders(rows):
    material = corpus.build_material(rows)
    audit = corpus.audit_native(rows, material, Tokenizer())
    assert not audit["mismatches"]
    assert set(audit["optimizer_update_groups"]) == {"0", "1", "2"}
    for updates in audit["optimizer_update_groups"].values():
        assert len(updates) == 80 and all(len(update) == 4 for update in updates)
        for offset in range(0, 80, 20):
            assert sorted(group for update in updates[offset:offset + 20] for group in update) == sorted(row["group"] for row in rows)
    for before, after in zip(*[audit["arms"][arm]["rows"] for arm in corpus.ARMS]):
        assert before["input_tokens"] == after["input_tokens"]
        assert before["target_tokens"] == after["target_tokens"]
        assert before["context_token_ids"] == after["context_token_ids"]
        for record in (before, after):
            assert record["labels"] == [-100] * len(record["context_token_ids"]) + record["response_token_ids"] + [900]
            assert record["input_ids"] == record["context_token_ids"] + record["response_token_ids"] + [900]
            assert record["input_tokens"] <= 512
            assert record["labels"].count(900) == 1
    assert audit["arms"]["input_before"]["totals"] == audit["arms"]["input_after"]["totals"]


def test_unequal_native_tokens_not_rescued_by_equal_line_inventory(rows):
    material = corpus.build_material(rows)
    with pytest.raises(corpus.TokenMismatch) as caught:
        corpus.audit_native(rows, material, UnequalTokenizer())
    assert len(caught.value.report["mismatches"]) == 64
    assert material == corpus.build_material(rows)
    assert all(row["input_before"]["target_tokens"] == row["input_after"]["target_tokens"] + 1
               for row in caught.value.report["mismatches"])


def test_native_render_mismatch_rejected(rows):
    rows[0]["spans"][0][0] += "INPUT: reminder"
    with pytest.raises(ValueError, match="single-user rendering"):
        corpus.audit_native(rows, corpus.build_material(rows), Tokenizer())


def test_native_overflow_rejected_without_truncation(rows):
    class LongTokenizer(Tokenizer):
        def encode(self, text, *, add_special_tokens):
            result = super().encode(text, add_special_tokens=add_special_tokens)
            return result * 8 if text.startswith("<|im_start|>") else result
    with pytest.raises(ValueError, match="overflow|truncate"):
        corpus.audit_native(rows, corpus.build_material(rows), LongTokenizer())


def test_native_eos_binding_rejected(rows):
    tokenizer = Tokenizer()
    tokenizer.eos_token_id = None
    with pytest.raises(ValueError, match="EOS/pad"):
        corpus.audit_native(rows, corpus.build_material(rows), tokenizer)


def test_material_tampering_rejected(rows):
    material = corpus.build_material(rows)
    material["corpora"]["input_before"][0]["spans"][1][0] += " "
    with pytest.raises(ValueError, match="material/provenance"):
        corpus.audit_native(rows, material, Tokenizer())


def test_fixture_export_hashes_status_counts_and_freshness(source_file, tmp_path):
    source, pins = source_file
    output = tmp_path / "output"
    manifest = corpus.prepare(source, output, pins, tokenizer=Tokenizer())
    assert manifest["status"] == "FIXTURE_ONLY_NOT_NATIVE_VALIDATION"
    assert manifest["model"] is None and manifest["pins"]["model_files"] == {}
    assert not manifest["fits_authorized"]
    assert manifest["counts"] == dict(rows_per_arm=80, arithmetic_per_arm=64, unchanged_memory_per_arm=16,
        dev_cases=48, unrequested_cases=64, planned_fits=6, planned_updates=480, planned_row_presentations=1920,
        planned_readout_calls=288, output_cap_tokens_not_usage=18432)
    assert set(path.name for path in output.iterdir()) == set(manifest["sha256"]) | {"manifest.json"}
    for name, expected in manifest["sha256"].items():
        assert corpus.base.digest(output / name) == expected
    for arm in corpus.ARMS:
        assert len(corpus.base.read(output / (arm + ".json"))["corpus"]) == 80
    with pytest.raises(ValueError, match="fresh output"):
        corpus.prepare(source, output, pins, tokenizer=Tokenizer())


def test_failed_native_match_preserves_audit_not_training_files(source_file, tmp_path):
    source, pins = source_file
    output = tmp_path / "mismatch"
    with pytest.raises(corpus.TokenMismatch):
        corpus.prepare(source, output, pins, tokenizer=UnequalTokenizer())
    assert [path.name for path in output.iterdir()] == ["token_mismatch.json"]
    failure = corpus.base.read(output / "token_mismatch.json")
    assert failure["status"] == "STOP_TOKEN_MISMATCH_REPORT_MAIN"
    assert not failure["corpora_exported"] and not failure["fits_authorized"]
    assert len(failure["audit"]["mismatches"]) == 64
    assert failure["audit"]["arms"]["input_before"]["rows"][0]["input_ids"]


@pytest.mark.parametrize("fault", ["source_bytes", "source_pin", "code_pin", "missing_pin", "fake_model", "symlink"])
def test_prepare_rejects_bindings_before_export(source_file, tmp_path, fault):
    source, pins = source_file
    if fault == "source_bytes":
        source.write_bytes(source.read_bytes() + b"\n")
    elif fault == "source_pin":
        pins["source_sha256"] = "0" * 64
    elif fault == "code_pin":
        pins["source_code_sha256"]["train_adapter_v3.py"] = "0" * 64
    elif fault == "missing_pin":
        pins.pop("model_files")
    elif fault == "fake_model":
        pins["model_files"] = {"config.json": "0" * 64}
    else:
        link = tmp_path / "linked.json"
        link.symlink_to(source)
        source = link
    with pytest.raises(ValueError):
        corpus.prepare(source, tmp_path / "output", pins, tokenizer=Tokenizer())
    assert not (tmp_path / "output").exists()


def test_no_fixture_can_masquerade_as_native(source_file, tmp_path):
    source, pins = source_file
    with pytest.raises(ValueError, match="local model OR fixture"):
        corpus.prepare(source, tmp_path / "output", pins, model=tmp_path, tokenizer=Tokenizer())


def test_saved_source_drift_during_audit_aborts_export(source_file, tmp_path):
    source, pins = source_file
    class MutatingTokenizer(Tokenizer):
        def get_vocab(self):
            source.write_bytes(source.read_bytes() + b"\n")
            return super().get_vocab()
    with pytest.raises(ValueError, match="source changed during"):
        corpus.prepare(source, tmp_path / "output", pins, tokenizer=MutatingTokenizer())
    assert not (tmp_path / "output").exists()


def test_local_model_pin_mismatch_does_not_load_tokenizer(source_file, tmp_path):
    source, pins = source_file
    model = tmp_path / "model"
    model.mkdir()
    (model / "config.json").write_text('{"model_type":"qwen2"}')
    pins["model_files"] = {"config.json": "0" * 64}
    with pytest.raises(ValueError, match="model/tokenizer pin"):
        corpus.prepare(source, tmp_path / "output", pins, model=model)


def test_model_tokenizer_file_drift_during_audit_aborts_export(source_file, tmp_path):
    source, pins = source_file
    model = tmp_path / "model"
    model.mkdir()
    config = model / "config.json"
    config.write_text('{"model_type":"qwen2"}')
    tokens = model / "tokenizer.json"
    tokens.write_text('{}')
    pins["model_files"] = corpus.base.model_hashes(model)
    class MutatingTokenizer(Tokenizer):
        def get_vocab(self):
            tokens.write_text('{"changed":true}')
            return super().get_vocab()
    with patch.object(corpus, "native_tokenizer", return_value=MutatingTokenizer()):
        with pytest.raises(ValueError, match="model/tokenizer changed during"):
            corpus.prepare(source, tmp_path / "output", pins, model=model)
    assert not (tmp_path / "output").exists()


def test_code_pin_drift_during_audit_aborts_export(source_file, tmp_path):
    source, pins = source_file
    with patch.object(corpus, "source_hashes", side_effect=[pins["source_code_sha256"], {}]):
        with pytest.raises(ValueError, match="source changed during"):
            corpus.prepare(source, tmp_path / "output", pins, tokenizer=Tokenizer())
    assert not (tmp_path / "output").exists()


def test_mismatch_report_cannot_claim_stale_source_custody(source_file, tmp_path):
    source, pins = source_file
    class MutatingTokenizer(UnequalTokenizer):
        def get_vocab(self):
            source.write_bytes(source.read_bytes() + b"\n")
            return super().get_vocab()
    with pytest.raises(ValueError, match="source changed during"):
        corpus.prepare(source, tmp_path / "output", pins, tokenizer=MutatingTokenizer())
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("text", ["INPUT: 2, 5\nPREDICT: 7\nACT: 7",
                                   "\n \tINPUT \t: +2 , +5\n\nPREDICT: +7\nACT : 7\t\n"])
def test_strict_joint_accepts_only_allowed_whitespace_and_signed_integers(text):
    result = corpus.score_addition(text, 2, 5)
    assert result["raw_text"] == text
    assert all(result[key] for key in ("joint", "form_a", "form_b", "input_correct", "prediction_correct", "act_success"))


@pytest.mark.parametrize("text", [
    "PREDICT: 7\nACT: 7\nINPUT: 2, 5", "PREDICT: 7\nINPUT: 2, 5\nACT: 7",
    "INPUT: 2, 5\nACT: 7\nPREDICT: 7", "INPUT: 5, 2\nPREDICT: 7\nACT: 7",
    "INPUT: 2, 5\nPREDICT: 7\nACT: 7\nACT: 7", "INPUT: 2, 5\nPREDICT: 7\nPREDICT: 7\nACT: 7",
    "INPUT: 2, 5\nINPUT: 2, 5\nPREDICT: 7\nACT: 7", "input: 2, 5\nPREDICT: 7\nACT: 7",
    "INPUT: 2 5\nPREDICT: 7\nACT: 7", "INPUT: 2, 5\nPREDICT: 7.0\nACT: 7",
    "```\nINPUT: 2, 5\nPREDICT: 7\nACT: 7\n```", "INPUT: 2, 5\nPREDICT: 7\nACT: 7\nDone.",
    "PREDICT: 7\nACT: 7", "", "INPUT: 2, 5\nPREDICT: 7\nACT: bad\nACT: 7",
])
def test_strict_joint_rejects_repair_rescue_prose_duplicates_and_bad_order(text):
    assert not corpus.score_addition(text, 2, 5)["joint"]


def test_prediction_accuracy_and_action_success_separate_from_joint():
    wrong_prediction = corpus.score_addition("INPUT: 2, 5\nPREDICT: 0\nACT: 7", 2, 5)
    assert wrong_prediction["joint"] and wrong_prediction["form_a"] and wrong_prediction["act_success"]
    assert not wrong_prediction["prediction_correct"] and not wrong_prediction["original_score"]["adherence"]
    wrong_action = corpus.score_addition("INPUT: 2, 5\nPREDICT: 7\nACT: 0", 2, 5)
    assert wrong_action["joint"] and wrong_action["prediction_correct"] and not wrong_action["act_success"]


def test_form_a_and_b_have_distinct_source_faithful_interpretation():
    parent = corpus.score_addition("PREDICT: 7\nACT: 7", 2, 5)
    assert parent["form_a"] and not parent["form_b"] and not parent["joint"]
    wrong_input = corpus.score_addition("INPUT: 5, 2\nPREDICT: 7\nACT: 7", 2, 5)
    assert wrong_input["form_b_order"] and not wrong_input["form_b"] and not wrong_input["input_correct"]
    after = corpus.score_addition("PREDICT: 7\nACT: 7\nINPUT: 2, 5", 2, 5)
    assert after["form_a"] and after["input_correct"] and not after["form_b"]


@pytest.mark.parametrize("prefix", ["ACT: bad", "ACT: 0", "ACT: 7"])
def test_first_or_duplicate_act_cannot_be_rescued(prefix):
    result = corpus.score_addition(prefix + "\nINPUT: 2, 5\nPREDICT: 7\nACT: 7", 2, 5)
    assert not result["joint"] and not result["act_success"]
    assert result["field_counts"]["ACT"] == 2


@pytest.mark.parametrize("text", [None, {}, [], 7])
def test_missing_nontext_response_is_not_scored_as_zero(text):
    with pytest.raises(ValueError, match="missing response"):
        corpus.score_addition(text, 2, 5)


def test_negative_source_operands_and_wrong_source_type():
    assert corpus.score_addition("INPUT: -2, +5\nPREDICT: 3\nACT: 3", -2, 5)["joint"]
    with pytest.raises(ValueError, match="source integer"):
        corpus.score_addition("", True, 5)


def test_source_pin_is_actual_original_teach_not_control():
    assert corpus.SOURCE_SHA256 == "2d12bb35d44279c3412323472bb716581c9ed57a966bb829290a49c4d799de7c"
    assert corpus.SOURCE_SHA256 != corpus.native.SOURCE_SHA256["control"]
    assert set(corpus.source_hashes()) == {"fundamental_two_habit_corpus.py", "fundamental_teaching_corpus.py",
        "fundamental_teaching_readout.py", "fundamental_repetition_corpus.py", "train_adapter_v3.py",
        "rulegame_parenting_diagnostic.py", "reasoning_neutral_probe.py"}


def test_saved_response_dispatch_binds_all48_source_keys():
    events = {event["id"]: event for event in corpus.original.build_candidate()["source_records"]}
    for case in corpus.panels()["dev"]:
        event = events[case["source_event_ids"][0]]
        if case["kind"] == "addition":
            raw = f"INPUT: {event['left']}, {event['right']}\nPREDICT: {event['sum']}\nACT: {event['sum']}"
        else:
            raw = case["expected"]
        scored = corpus.score_response(case["id"], raw)
        assert scored["case_id"] == case["id"] and scored["source_event_ids"] == case["source_event_ids"]
        assert scored["score"]["raw_text"] == raw
        if case["kind"] == "addition":
            assert scored["score"]["joint"] and scored["score"]["act_success"]
        else:
            assert scored["score"] == corpus.readout.score_memory(raw, case["expected"])


def test_remaining64_cases_cannot_enter_saved_response_scoring():
    for case_id in corpus.panels()["unrequested_case_ids"]:
        with pytest.raises(ValueError, match="only original48"):
            corpus.score_response(case_id, "ACT: 0")


def test_saved_response_dispatch_does_not_replace_missing_with_zero():
    with pytest.raises(ValueError, match="missing response"):
        corpus.score_response(corpus.readout.CASE_IDS[0], None)
    assert corpus.score_response(corpus.readout.CASE_IDS[0], "")["score"]["joint"] is False

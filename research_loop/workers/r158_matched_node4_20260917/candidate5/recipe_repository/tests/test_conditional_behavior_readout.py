"""CPU mocks only: no tokenizer package, model, GPU, network or scientific evidence."""
import copy
import json
from pathlib import Path
import re
import sys
import time
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from organism_v6 import conditional_behavior_readout as readout


class Tokenizer:
    eos_token_id = 900000
    pad_token_id = 900001

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        assert tokenize is False and add_generation_prompt is True
        assert len(messages) == 1 and set(messages[0]) == {"role", "content"}
        assert messages[0]["role"] == "user"
        return "USER:\n" + messages[0]["content"] + "\nASSISTANT:\n"

    def encode(self, text, add_special_tokens=False):
        return [ord(character) + 100 for character in text]

    def decode(self, tokens, *, skip_special_tokens, clean_up_tokenization_spaces):
        assert skip_special_tokens is True and clean_up_tokenization_spaces is False
        return "".join(chr(token - 100) for token in tokens if token not in (self.eos_token_id, self.pad_token_id))


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))


@pytest.fixture(scope="module")
def prepared(tmp_path_factory):
    root = tmp_path_factory.mktemp("conditional-fixture")
    model = root / "model"
    model.mkdir()
    write(model / "config.json", dict(model_type="qwen2"))
    write(model / "tokenizer.json", dict(fixture=True))
    write(model / "tokenizer_config.json", dict(fixture=True))
    (model / "model.safetensors").write_bytes(b"not-model-weights-cpu-fixture")
    material = root / "material"
    material.mkdir()
    candidate = readout.corpus.build_candidate(0, ("dax", "wug"), ("fep", "nup"))
    native = readout.corpus.audit_tokenizer(candidate, Tokenizer())
    native.update(status="NATIVE_TOKEN_MATCH_VERIFIED", tokenizer_path=str(model), model_weight_origin="NOT_AUTHENTICATED",
                  tokenizer_file_hashes={name: readout.base.digest(model / name) for name in
                                        ("config.json", "tokenizer.json", "tokenizer_config.json")})
    write(material / "candidate.json", candidate)
    write(material / "recipe.json", readout.corpus.training_recipe(learning_rate=1e-4, seed=0))
    write(material / "native_audit.json", native)
    write(material / "teacher_forcing_interface.json", readout.corpus.teacher_forcing_interface(candidate))
    for arm in readout.corpus.ARMS:
        write(material / f"{arm}.json", {"corpus": native["corpora"][arm]})
    write(material / "manifest.json", dict(files={path.name: readout.base.digest(path) for path in material.iterdir()}))
    return dict(root=root, model=model, material=material, candidate=candidate, native=native,
                pins={name: readout.base.digest(material / name) for name in readout.MATERIAL_PINS},
                token_totals=dict(input=native["input_tokens_per_epoch"]["AUTH"], target=native["target_tokens_per_epoch"]["AUTH"]))


@pytest.fixture
def environment(prepared, monkeypatch):
    monkeypatch.setattr(readout, "MATERIAL_PINS", prepared["pins"])
    monkeypatch.setattr(readout, "TOKEN_TOTALS", prepared["token_totals"])
    return prepared


def adapter_fixture(directory, state, environment):
    directory.mkdir()
    material = readout.read_material(environment["material"])
    total, target = environment["token_totals"]["input"], environment["token_totals"]["target"]
    manifest = dict(config=material["recipe"], base_model=str(environment["model"]), empty=False,
                    steps=128, micro_batches=128, epochs_run=4, nonfinite_batches=0, final_loss=.1,
                    corpus=dict(sha256=material["inventory"][f"{state}.json"], n_items=128, n_encoded=128, n_skipped_no_target=0),
                    truncation=dict.fromkeys(("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split"), 0),
                    tokens=dict(total=total, target=target, context=total - target), train_tokens_seen=4 * total)
    write(directory / "train_manifest.json", manifest)
    write(directory / "adapter_config.json", dict(r=8, lora_alpha=16, lora_dropout=.05,
                                                  target_modules=list(readout.corpus.trainer.ALL_PROJ)))
    (directory / "adapter_model.safetensors").write_bytes(("fixture-" + state).encode())
    (directory / "DONE").write_text("ok\n")
    return directory


def prepare_state(tmp_path, environment, state="OFF", phase="generate", adapter=None):
    if state != "OFF" and adapter is None:
        adapter = adapter_fixture(tmp_path / ("adapter-" + state), state, environment)
    out = tmp_path / (state + "-" + phase)
    plan = readout.prepare(environment["material"], out, environment["model"],
                           readout.base.model_hashes(environment["model"]), state, phase, adapter, "0",
                           time.time() + 3600, tokenizer=Tokenizer(),
                           prospect_contrast=readout.PROSPECT_CONTRAST if phase == "score" else None)
    return out, plan


def expected_outputs(candidate, state):
    arm = "DERANGED" if state == "DERANGED" else "AUTH"
    outputs = {}
    for case in candidate["train"]["AUTH"] + candidate["dev"]:
        outputs[case["id"]] = readout.corpus.response_text(case, arm)
    for case in readout.controls():
        outputs[case["id"]] = f"ACT: {case['expected']}\n"
    return outputs


class GenerationBackend:
    def __init__(self, plan, outputs):
        self.plan = plan
        self.outputs = outputs
        self.backend = None

    def identity(self):
        return self.plan["identity"]

    def generate(self, request):
        rendered, prefix = readout.render(Tokenizer(), request["prompt"])
        text = self.outputs[request["case_id"]]
        return dict(text=text, rendered_prompt=rendered, prompt_token_ids=prefix,
                    output_token_ids=Tokenizer().encode(text), finish_reason="stop", stop_reason=None)


class ScoreBackend:
    def __init__(self, plan):
        self.state = plan["state"]
        self.closed = False

    def score(self, request):
        sums = []
        for candidate in request["candidates"]:
            matches_input = candidate["source_case_id"] == request["case_id"]
            if request["operation"] == "REVISE" and self.state == "DERANGED":
                matches_input = not matches_input
            sums.append(-4.0 if self.state == "OFF" else (-2.0 if matches_input else -6.0))
        return dict(token_logprobs=[[total / len(candidate["response_ids"])] * len(candidate["response_ids"])
                                   for total, candidate in zip(sums, request["candidates"], strict=True)])

    def close(self):
        self.closed = True
        return True


def capture_fixture(root, plan, candidate):
    data = root / "run" / "data"
    data.mkdir(parents=True)
    if plan["phase"] == "generate":
        backend = GenerationBackend(plan, expected_outputs(candidate, plan["state"]))
        readout.generic.capture(plan, data, factory=lambda *args: backend, closer=lambda backend: True)
    else:
        readout.capture_scores(plan, data, factory=ScoreBackend)
    worker = root / "run" / "worker"
    worker.mkdir()
    write(worker / "supervision.json", dict(ok=True, reservation_release_verified=True, owned_group_empty=True,
                                           gpu_processes_absent=True, returncode=0, device="0", reserved_seconds=1.0))
    return data


def test_frozen_attempt2_constants():
    assert readout.MATERIAL_PINS["candidate.json"] == "5d1644b90ff7621ee121aba65be7dd7cae7f15168f5a3c3a09a1bc9aa9a7af8c"
    assert readout.TOKEN_TOTALS == dict(input=11248, target=1888)
    assert readout.SETTINGS == dict(temperature=0.0, seed=20260912, max_tokens=64)
    assert readout.RESOURCE_BUDGET["total_a40_seconds"] == 5400
    assert readout.base.WORKER_SECONDS == 600 and readout.base.LOAD_SECONDS == 180 and readout.base.CALL_SECONDS == 120


def test_real_control_source_identity_and_denominators():
    controls = readout.controls()
    original = {row["id"]: row for row in readout.fundamental.build_candidate()["eval"]}
    assert len(controls) == 32
    for index, row in enumerate(controls[:16]):
        source = original[f"eval-addition-{index:03d}"]
        assert row["source"] == source and row["context"] == source["context"] and row["expected"] == source["expected"]
        left, right = map(int, re.search(r"Add (\d+) and (\d+)", row["context"]).groups())
        assert row["expected"] == left + right
    copies = [row for row in readout.carrier.build_items() if row["kind"] == "native_action_copy"]
    assert [row["source"] for row in controls[16:]] == copies
    assert len({row["context"] for row in controls[16:]}) == 8


@pytest.mark.parametrize("state", readout.STATES)
def test_complete_requests_do_not_use_fixed48_ids(prepared, state, monkeypatch):
    monkeypatch.setattr(readout.generic, "selected_cases", Mock(side_effect=AssertionError("fixed48 wrapper used")))
    requests = readout.generation_requests(prepared["candidate"], state)
    assert len(requests) == len({row["case_id"] for row in requests}) == 224
    assert [sum(row["split"] == split for row in requests) for split in ("train", "dev", "control")] == [128, 64, 32]
    assert all({key: row[key] for key in readout.SETTINGS} == readout.SETTINGS for row in requests)
    assert all(row["arm"] == state for row in requests)
    assert [row["case_id"] for row in requests[:128]] == [row["id"] for row in prepared["candidate"]["train"]["AUTH"]]


def test_shared_off_inputs_and_source_projection(prepared):
    panels = [readout.generation_requests(prepared["candidate"], state) for state in readout.STATES]
    assert all([{key: value for key, value in row.items() if key != "arm"} for row in panel] ==
               [{key: value for key, value in row.items() if key != "arm"} for row in panels[0]] for panel in panels)
    assert all(set(row) == {"call_id", "case_id", "split", "role", "arm", "prompt", "temperature", "seed", "max_tokens"}
               for row in panels[0])


@pytest.mark.parametrize("state", readout.STATES)
def test_generation_maps_twins_and_controls(prepared, state):
    result = readout.score_generations(prepared["candidate"], expected_outputs(prepared["candidate"], state), state)
    own = "DERANGED" if state == "DERANGED" else "AUTH"
    for split, count in (("train", 64), ("dev", 32)):
        scored = result["primary"][split][own]
        assert all(row["own_map_strict_joint"] == count for row in scored["operations"].values())
        assert all(row["own_map_strict_passes"] == (32 if split == "train" else 16) for row in scored["twins"].values())
    assert result["controls"]["families"]["copy"]["unique_prompts"] == 8
    assert result["controls"]["families"]["copy"]["unique_all_correct"] == 8
    assert all(row["correct"] == 16 and row["tag_spill"] == 0 for row in result["controls"]["families"].values())
    assert result["shared_off"] == (state == "OFF")


def test_missing_extra_outputs_and_spill_do_not_get_repaired(prepared):
    outputs = expected_outputs(prepared["candidate"], "AUTH")
    outputs.pop(next(iter(outputs)))
    with pytest.raises(ValueError, match="224"):
        readout.score_generations(prepared["candidate"], outputs, "AUTH")
    controls = {row["id"]: f"ACT: {row['expected']}\n" for row in readout.controls()}
    first = readout.controls()[0]
    controls[first["id"]] = f"PREDICT: {first['expected']}\nACT: {first['expected']}"
    result = readout.score_controls(controls)
    assert result["families"]["addition"]["tag_spill"] == 1
    assert result["families"]["addition"]["correct"] == 16
    assert result["families"]["addition"]["exact"] == 15
    controls["unexpected"] = "ACT: 0"
    with pytest.raises(ValueError, match="controls"):
        readout.score_controls(controls)


def test_score_requests_common_input_complete_eos(prepared):
    requests = readout.scoring_requests(prepared["candidate"], "AUTH", Tokenizer(), prospect_contrast=readout.PROSPECT_CONTRAST)
    assert len(requests) == 64
    for request, case in zip(requests, prepared["candidate"]["dev"], strict=True):
        expected_prefix = Tokenizer().encode("USER:\n" + case["context"] + "\nASSISTANT:\n")
        assert request["payload"]["prompt_input_ids"] == expected_prefix
        assert request["rendered_prompt"].endswith("ASSISTANT:\n")
        assert request["assay_version"] == readout.ASSAY_VERSION
        assert len(request["candidates"]) == (4 if case["operation"] == "PROSPECT" else 2)
        for target in request["candidates"]:
            assert target["candidate_id"] in ("AUTH_X0", "AUTH_X1", "DERANGED_X0", "DERANGED_X1")
            assert target["response_ids"] == Tokenizer().encode(target["text"]) + [Tokenizer.eos_token_id]
            assert target["input_ids"] == expected_prefix + target["response_ids"]
            assert target["labels"] == [-100] * len(expected_prefix) + target["response_ids"]


def test_all_states_share_exact_dual_candidate_inputs_and_accounting(prepared):
    panels = [readout.scoring_requests(prepared["candidate"], state, Tokenizer(), prospect_contrast=readout.PROSPECT_CONTRAST)
              for state in readout.STATES]
    normalized = [[{key: value for key, value in row.items() if key != "arm"} for row in panel] for panel in panels]
    assert normalized[0] == normalized[1] == normalized[2]
    for panel in panels:
        assert len(panel) == 64
        assert sum(len(row["candidates"]) for row in panel) == 192
        assert sum(len(readout.scoring_groups(row)) for row in panel) == 96
    assert sum(len(row["candidates"]) for panel in panels for row in panel) == 576


def test_prospect_four_candidate_literal_truth_table(prepared):
    choices = readout.contrast_candidates(prepared["candidate"], prospect_contrast=readout.PROSPECT_CONTRAST)
    first, second = prepared["candidate"]["twins"]["dev"]["belief"][0]
    assert {row["candidate_id"]: row["text"] for row in choices[first]} == {
        "AUTH_X0": "PREDICT: dax -> fep\nACT: dax",
        "AUTH_X1": "PREDICT: wug -> fep\nACT: wug",
        "DERANGED_X0": "PREDICT: wug -> nup\nACT: wug",
        "DERANGED_X1": "PREDICT: dax -> nup\nACT: dax",
    }
    assert choices[first] == choices[second]


@pytest.mark.parametrize("state", readout.STATES)
def test_fixed_candidate_interaction_sign(prepared, state):
    records = {}
    for family in ("belief", "outcome"):
        for first, second in prepared["candidate"]["twins"]["dev"][family]:
            records[first] = dict(AUTH_X0=-2.0, AUTH_X1=-6.0)
            records[second] = dict(AUTH_X0=-6.0, AUTH_X1=-2.0)
            if family == "belief":
                records[first].update(DERANGED_X0=-3.0, DERANGED_X1=-5.0)
                records[second].update(DERANGED_X0=-5.0, DERANGED_X1=-3.0)
    result = readout.score_interactions(prepared["candidate"], records, state, prospect_contrast=readout.PROSPECT_CONTRAST)
    for operation, row in result["operations"].items():
        assert row["total"] == 16 and len(row["pairs"]) == 16
        assert row["map_oriented"]["AUTH"]["mean_nats"] == 8
        assert row["map_oriented"]["DERANGED"]["mean_nats"] == (4 if operation == "PROSPECT" else -8)
        for pair in row["pairs"]:
            assert pair["candidate_pairs"]["AUTH"] == ["AUTH_X0", "AUTH_X1"]
            assert pair["candidate_pairs"]["DERANGED"] == (["DERANGED_X0", "DERANGED_X1"] if operation == "PROSPECT" else ["AUTH_X1", "AUTH_X0"])
    assert result["candidate_forwards"] == 192
    records.pop(next(iter(records)))
    with pytest.raises(ValueError, match="64"):
        readout.score_interactions(prepared["candidate"], records, state, prospect_contrast=readout.PROSPECT_CONTRAST)


def test_native_material_encoding_and_pin_tampering(environment, tmp_path, monkeypatch):
    material = readout.read_material(environment["material"])
    readout.audit_encoding(material, Tokenizer())
    bad = copy.deepcopy(material)
    bad["native"]["rows"]["AUTH"][0]["prefix_ids"][0] += 1
    with pytest.raises(ValueError, match="native rows"):
        readout.audit_encoding(bad, Tokenizer())
    monkeypatch.setattr(readout, "MATERIAL_PINS", dict(environment["pins"], **{"AUTH.json": "0" * 64}))
    with pytest.raises(ValueError, match="attempt2"):
        readout.read_material(environment["material"])
    bad_native = copy.deepcopy(material["native"])
    bad_native["tokenizer_file_hashes"]["tokenizer.json"] = "0" * 64
    with pytest.raises(ValueError, match="tokenizer pin"):
        readout.load_tokenizer(environment["model"], bad_native)


@pytest.mark.parametrize("field", ["source_sha256", "status", "candidate_sha256", "no_truncation"])
def test_material_rejects_unbound_native_audit(environment, tmp_path, field):
    import shutil
    destination = tmp_path / "material"
    shutil.copytree(environment["material"], destination)
    native = readout.base.read(destination / "native_audit.json")
    if field == "source_sha256":
        native[field]["train_adapter_v3.py"] = "wrong"
    else:
        native[field] = False
    write(destination / "native_audit.json", native)
    manifest = readout.base.read(destination / "manifest.json")
    manifest["files"]["native_audit.json"] = readout.base.digest(destination / "native_audit.json")
    write(destination / "manifest.json", manifest)
    with pytest.raises(ValueError):
        readout.read_material(destination)


@pytest.mark.parametrize("change", ["steps", "warm_start", "corpus", "tokens", "recipe", "truncation", "adapter_config"])
def test_fit_contract_rejects_deviations(environment, tmp_path, change):
    adapter = adapter_fixture(tmp_path / "adapter", "AUTH", environment)
    material = readout.read_material(environment["material"])
    assert readout.fit_contract(adapter, "AUTH", environment["model"], material)
    manifest = readout.base.read(adapter / "train_manifest.json")
    if change == "steps":
        manifest["steps"] = 127
    elif change == "warm_start":
        manifest["warm_start"] = dict(mode="WEIGHT_WARM_START_FRESH_OPTIMIZER")
    elif change == "corpus":
        manifest["corpus"]["sha256"] = material["inventory"]["DERANGED.json"]
    elif change == "tokens":
        manifest["train_tokens_seen"] -= 1
    elif change == "recipe":
        manifest["config"]["lr"] = 3e-5
    elif change == "truncation":
        manifest["truncation"]["items_truncated"] = 1
    else:
        config = readout.base.read(adapter / "adapter_config.json")
        config["r"] = 16
        write(adapter / "adapter_config.json", config)
    write(adapter / "train_manifest.json", manifest)
    with pytest.raises(ValueError):
        readout.fit_contract(adapter, "AUTH", environment["model"], material)


def test_off_rejects_adapter_and_bad_model_pins(environment, tmp_path):
    material = readout.read_material(environment["material"])
    with pytest.raises(ValueError, match="OFF"):
        readout.fit_contract(tmp_path, "OFF", environment["model"], material)
    with pytest.raises(ValueError, match="model file pins"):
        readout.prepare(environment["material"], tmp_path / "bad", environment["model"], {}, "OFF", "generate", None,
                        "0", time.time() + 3600, tokenizer=Tokenizer())


@pytest.mark.parametrize("phase", readout.PHASES)
def test_prepare_verify_capture_and_replay(environment, tmp_path, phase):
    root, plan = prepare_state(tmp_path, environment, phase=phase)
    verified, _, _ = readout.verify(root, tokenizer=Tokenizer())
    assert verified == plan
    capture_fixture(root, plan, environment["candidate"])
    result = readout.reduce(root, tokenizer=Tokenizer())
    assert result["complete"] is True and result["supplies_l1_verdict"] is False
    assert result["cost"]["requests"] == (224 if phase == "generate" else 64)
    if phase == "generate":
        assert result["cost"]["native_output_tokens"] < result["cost"]["output_token_ceiling"] == 14336
    else:
        assert result["cost"]["candidate_forwards"] == 192
        assert result["cost"]["native_output_tokens"] == result["cost"]["output_token_ceiling"] == 0
        assert result["cost"]["padded_forward_tokens"] >= result["cost"]["native_input_tokens"]
        assert result["cost"]["padded_forward_tokens"] == sum(
            2 * max(len(choice["input_ids"]) for choice in group)
            for request in plan["requests"] for group in readout.scoring_groups(request))
        assert result["cost"]["scored_target_tokens"] == sum(
            len(choice["response_ids"]) for request in plan["requests"] for choice in request["candidates"])
        assert result["assay_version"] == readout.ASSAY_VERSION


@pytest.mark.parametrize("failure", ["missing", "duplicate", "response", "release", "source"])
def test_missing_or_bad_capture_is_incomplete(environment, tmp_path, monkeypatch, failure):
    root, plan = prepare_state(tmp_path, environment)
    data = capture_fixture(root, plan, environment["candidate"])
    if failure == "missing":
        (data / "calls" / "0000.response.json").unlink()
    elif failure == "duplicate":
        write(data / "calls" / "9999.response.json", {})
    elif failure == "response":
        response = readout.base.read(data / "calls" / "0000.response.json")
        response["response"]["prompt_token_ids"] = [123]
        write(data / "calls" / "0000.response.json", response)
    elif failure == "release":
        path = root / "run" / "worker" / "supervision.json"
        receipt = readout.base.read(path)
        receipt["reservation_release_verified"] = False
        write(path, receipt)
    else:
        monkeypatch.setattr(readout, "sources", lambda: {})
    result = readout.reduce(root, tokenizer=Tokenizer())
    assert result["status"] == "INCOMPLETE" and result["complete"] is False
    assert "result" not in result and result["supplies_l1_verdict"] is False


def test_scoring_failure_keeps_raw_and_closes(environment, tmp_path):
    root, plan = prepare_state(tmp_path, environment, phase="score")
    data = root / "data"
    data.mkdir()
    backend = ScoreBackend(plan)
    backend.score = lambda request: dict(token_logprobs=[[float("nan")], []])
    with pytest.raises(ValueError):
        readout.capture_scores(plan, data, factory=lambda plan: backend)
    assert backend.closed
    assert (data / "failure.json").exists()
    assert not (data / "manifest.json").exists()


@pytest.mark.parametrize("operation,groups", [("PROSPECT", 2), ("REVISE", 1)])
def test_hf_wrapper_delegates_to_existing_generic_score(prepared, monkeypatch, operation, groups):
    instance = object.__new__(readout.HFScorer)
    instance.torch = object()
    instance.model = object()
    request = next(row for row in readout.scoring_requests(prepared["candidate"], "OFF", Tokenizer(), prospect_contrast=readout.PROSPECT_CONTRAST)
                   if row["operation"] == operation)
    mocked = Mock(return_value={"token_logprobs": [[-2.0], [-3.0]]})
    monkeypatch.setattr(readout.carrier, "score", mocked)
    assert instance.score(request) == {"token_logprobs": [[-2.0], [-3.0]] * groups}
    assert mocked.call_count == groups
    for index, call in enumerate(mocked.call_args_list):
        assert call.args[:2] == (instance.torch, instance.model)
        assert call.args[2] == dict(request, candidates=request["candidates"][index * 2:index * 2 + 2])


@pytest.mark.parametrize("adapter", [None, "/fixture/saved-adapter"])
def test_hf_loader_uses_saved_state_inference_only(monkeypatch, adapter):
    model = Mock()
    model.peft_config = {"default": {}}
    fake_torch = SimpleNamespace(bfloat16=object(), cuda=SimpleNamespace(empty_cache=Mock()))
    auto = SimpleNamespace(from_pretrained=Mock(return_value=model))
    peft = SimpleNamespace(from_pretrained=Mock(return_value=model))
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(sys.modules, "transformers", SimpleNamespace(AutoModelForCausalLM=auto))
    monkeypatch.setitem(sys.modules, "peft", SimpleNamespace(PeftModel=peft))
    scorer = readout.HFScorer(dict(model="/fixture/base", adapter=adapter))
    assert auto.from_pretrained.call_args.args == ("/fixture/base",)
    assert auto.from_pretrained.call_args.kwargs["local_files_only"] is True
    assert auto.from_pretrained.call_args.kwargs["trust_remote_code"] is False
    if adapter is None:
        peft.from_pretrained.assert_not_called()
    else:
        peft.from_pretrained.assert_called_once_with(model, adapter, is_trainable=False)
    model.requires_grad_.assert_called_once_with(False)
    model.eval.assert_called_once_with()
    assert model.config.use_cache is False
    assert scorer.close() is True
    fake_torch.cuda.empty_cache.assert_called_once_with()


@pytest.mark.parametrize("problem", ["short", "positive", "infinite", "mass"])
def test_candidate_score_rejects_bad_evidence(prepared, problem):
    request = readout.scoring_requests(prepared["candidate"], "OFF", Tokenizer(), prospect_contrast=readout.PROSPECT_CONTRAST)[0]
    values = [[-2.0] * len(candidate["response_ids"]) for candidate in request["candidates"]]
    if problem == "short":
        values[0].pop()
    elif problem == "positive":
        values[0][0] = .5
    elif problem == "infinite":
        values[0][0] = float("-inf")
    else:
        values = [[0.0] * len(candidate["response_ids"]) for candidate in request["candidates"]]
    with pytest.raises(ValueError):
        readout.validate_scores(request, dict(token_logprobs=values))


def test_non_swapped_prospect_candidates_are_a_real_protocol_tension(prepared):
    indexed = {row["id"]: row for row in prepared["candidate"]["dev"]}
    first, second = prepared["candidate"]["twins"]["dev"]["belief"][0]
    first_auth = readout.corpus.response_text(indexed[first], "AUTH")
    second_deranged = readout.corpus.response_text(indexed[second], "DERANGED")
    assert first_auth != second_deranged
    assert first_auth.split("ACT: ")[1] == second_deranged.split("ACT: ")[1]


def test_dual_contrast_requires_explicit_version_and_real_maps(prepared):
    with pytest.raises(ValueError, match="explicit"):
        readout.scoring_requests(prepared["candidate"], "OFF", Tokenizer(), prospect_contrast=None)
    choices = readout.contrast_candidates(prepared["candidate"], prospect_contrast=readout.PROSPECT_CONTRAST)
    indexed = {row["id"]: row for row in prepared["candidate"]["dev"]}
    for family in ("belief", "outcome"):
        for first, second in prepared["candidate"]["twins"]["dev"][family]:
            assert choices[first] == choices[second]
            assert len({row["text"] for row in choices[first]}) == (4 if family == "belief" else 2)
            pair_ids = readout.candidate_pairs(prepared["candidate"], choices[first])
            by_id = {row["candidate_id"]: row for row in choices[first]}
            for arm in readout.corpus.ARMS:
                for endpoint, case_id in enumerate((first, second)):
                    assert by_id[pair_ids[arm][endpoint]]["text"] == readout.corpus.response_text(indexed[case_id], arm)
    with pytest.raises(ValueError, match="explicit"):
        readout.contrast_candidates(prepared["candidate"], prospect_contrast="auth-belief-endpoints")


def test_missing_deranged_candidate_scores_are_not_rescued(prepared):
    requests = readout.scoring_requests(prepared["candidate"], "OFF", Tokenizer(), prospect_contrast=readout.PROSPECT_CONTRAST)
    prospect = next(row for row in requests if row["operation"] == "PROSPECT")
    response = ScoreBackend({"state": "OFF"}).score(prospect)
    response["token_logprobs"] = response["token_logprobs"][:2]
    with pytest.raises(ValueError, match="complete candidate"):
        readout.validate_scores(prospect, response)


def test_version_drift_makes_score_plan_incomplete(environment, tmp_path):
    root, plan = prepare_state(tmp_path, environment, phase="score")
    plan["assay_version"] = "obsolete-auth-subset"
    write(root / "plan.json", plan)
    write(root / "plan.sha256.json", dict(sha256=readout.base.digest(root / "plan.json")))
    result = readout.reduce(root, tokenizer=Tokenizer())
    assert result["status"] == "INCOMPLETE"
    assert "assay version" in result["error"]


def test_run_reuses_supervisor_and_requires_explicit_permission(environment, tmp_path, monkeypatch):
    root, plan = prepare_state(tmp_path, environment)
    with pytest.raises(ValueError, match="allow-gpu"):
        readout.run(root)
    monkeypatch.setattr(readout, "verify", lambda root: (plan, {}, Tokenizer()))
    supervise = Mock(return_value={"fixture": True})
    monkeypatch.setattr(readout.base, "supervise", supervise)
    assert readout.run(root, allow_gpu=True) == {"fixture": True}
    args = supervise.call_args.args
    assert args[0] == root and args[1] == plan
    assert "organism_v6.conditional_behavior_readout" in args[3]
    assert "fundamental_teaching_readout" not in " ".join(args[3])


def test_all_six_panels_and_shared_off_summary(environment, tmp_path):
    reductions = []
    for state in readout.STATES:
        directory = tmp_path / state
        directory.mkdir()
        adapter = adapter_fixture(directory / "adapter", state, environment) if state != "OFF" else None
        for phase in readout.PHASES:
            root, plan = prepare_state(directory, environment, state, phase, adapter)
            capture_fixture(root, plan, environment["candidate"])
            reductions.append(readout.reduce(root, tokenizer=Tokenizer()))
    result = readout.summarize(reductions)
    assert result["complete"] and not result["supplies_l1_verdict"]
    assert result["actual_generation_calls"] == 672 and result["candidate_forwards"] == 576
    assert result["cost"]["candidate_forwards"] == 576
    assert result["assay_version"] == readout.ASSAY_VERSION
    assert result["comparisons"]["AUTH"]["auth_minus_off_semantic"] == dict(PROSPECT=0.0, REVISE=0.0)
    assert readout.summarize(reductions[:-1])["status"] == "INCOMPLETE"
    bad = copy.deepcopy(reductions)
    bad[-1]["adapter_files"]["adapter_model.safetensors"] = "wrong"
    assert readout.summarize(bad)["status"] == "INCOMPLETE"


def test_cli_reduce_missing_is_incomplete(tmp_path, capsys):
    readout.main(["reduce", "--root", str(tmp_path / "absent")])
    assert json.loads(capsys.readouterr().out)["status"] == "INCOMPLETE"

"""TRAIN-only observation-reading prompts and exact raw-child replay admission."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tarfile


SELF = Path(__file__).resolve()
SCHEMA = "astra_own_source_observation_replay_20260913_v1"
ARCHIVE = "/data/home/rohing/dream-state/gpu_artifacts_local/level1_second_roster_20260913/node2_second_perception.tar"
ARCHIVE_PIN = "addc2e61ce05f2b622482adde82f16c2c571db6dd072b0fb7750a4d6dc559a3a"
SOURCE_ROOT = "/tmp/astra_level1_real_record_source_20260913_attempt1"
MATERIAL_PATH = "/tmp/astra_level1_perception_reflection_material_20260913.py"
MATERIAL_PIN = "4648f8542b1babb10f6ffda4bf023024d71b8c9834a32e2242a7f064a94a8941"
RUNNER_PATH = "/tmp/astra_level1_skill_run_20260913.py"
RUNNER_PIN = "6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e"
DATASET_PIN = "48c52b25ceb3edb719d2e5f958b63c58301fee90dd9df27277f54cabdc2b9cdb"
PLAN_PINS = ("3f4fd56868d2c42fe776c72ad4c5c93b15284ad16cd87c06849ba50419f67900",
             "563d6799cd4b4030844f9dc037b931856132771e8e66e005b139e3f9dae96b47",
             "bd4c5c4ec37da0a3e6611d430441d786beee2f338200f64ff64d2c40a8875910")
WEIGHT_PINS = ("8bfe8b9d647b58b064733ed24d8aaa97cd79d7012795232305838a23ac415432",
               "c9700a2f46b36e64ce9e1845cd4601d3d0da086afbaba9efbc93012af936e0e2",
               "5d198acfc7bf2f2c552b6b180688bce5d7fe00b1afd2eea7d056fc44a2e505da")
SUPPORTED = ("agreement", "contradicted_prediction", "absent_prediction")
SELECTION = "supported24_v1: four skins x three admissible cases x two outcomes; earlier_same iff (skin+case+int(outcome))%2==0"
BOUNDARY = ("Own-source observation-reading replay CANDIDATES from supplied child outputs on externally curated TRAIN observations. "
            "These contexts were in the original parent's authored training: possible relearning/rote readout, not new free action, "
            "independent experience, verified native identity, approved fit, or proven retention repair.")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def decode(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique, parse_constant=lambda value: require(False, "nonfinite JSON"))


def load(path, pin, name):
    require(digest(path) == pin, "source pin differs: " + name)
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("own_source_replay_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dependencies(source_root=SOURCE_ROOT):
    material = load(MATERIAL_PATH, MATERIAL_PIN, "material")
    require(digest(RUNNER_PATH) == RUNNER_PIN, "original skill runner pin differs")
    root = Path(source_root).resolve()
    for relative, pin in material.PINS.items():
        require(digest(root / relative) == pin, "frozen source differs: " + relative)
    corpus = load(root / "organism_v6/birth_skill_corpus.py", material.PINS["organism_v6/birth_skill_corpus.py"], "corpus")
    return material, corpus


def original_inputs(seed, archive_path=ARCHIVE):
    require(type(seed) is int and seed in (0, 1, 2), "original perception seed0/1/2 required")
    require(digest(archive_path) == ARCHIVE_PIN, "original perception archive pin differs")
    prefix = f"localhome/local-rohing/astra_diagnostics/level1_perception_seed{seed}_20260913_attempt1/"
    with tarfile.open(archive_path, "r:") as archive:
        members = archive.getmembers()
        require(len({member.name for member in members}) == len(members), "duplicate archive members")
        def member_bytes(name):
            member = archive.getmember(prefix + name)
            require(member.isfile() and 0 <= member.size <= 128 * 1024 * 1024, "bounded regular source member required")
            return archive.extractfile(member).read()
        plan_raw = member_bytes("plan.json")
        material_raw = member_bytes("material.json")
        require(sha(plan_raw) == PLAN_PINS[seed] and sha(material_raw) == DATASET_PIN, "original plan/material binding differs")
        plan, dataset = decode(plan_raw), decode(material_raw)
        require(plan["skill"] == "perception" and plan["learner_seed"] == seed and plan["material_seed"] == 0 and
                plan["self_sha256"] == RUNNER_PIN and plan["input_hashes"]["material.json"] == DATASET_PIN and
                plan["specification"]["material"]["sha256"] == MATERIAL_PIN, "original training identity differs")
        files = {member.name[len(prefix + "run/fit/adapter/"):]: sha(archive.extractfile(member).read()) for member in members
                 if member.isfile() and member.name.startswith(prefix + "run/fit/adapter/")}
        require(files["adapter_model.safetensors"] == WEIGHT_PINS[seed], "original parent adapter differs")
        manifest = decode(member_bytes("run/fit/adapter/train_manifest.json"))
        require(manifest["config"] == plan["config"] and manifest["config"]["seed"] == seed and manifest["steps"] == 320,
                "original authored parent fit differs")
    producer = dict(learner_seed=seed, adapter=plan["root"] + "/run/fit/adapter", adapter_files=files,
                    model=plan["model"], model_files=plan["model_files"], parent_plan_sha256=PLAN_PINS[seed])
    return dataset, producer, dict(archive=dict(path=str(Path(archive_path).resolve()), sha256=ARCHIVE_PIN),
        plan_member=prefix + "plan.json", plan_sha256=PLAN_PINS[seed], material_member=prefix + "material.json", material_sha256=DATASET_PIN,
        original_source_root=plan["source"], original_source_files=plan["specification"]["source_files"])


def observation_row(row):
    return {key: copy.deepcopy(row[key]) for key in ("row_id", "input_messages", "source")}


def inventory(dataset, material, corpus):
    require(dataset["schema"] == material.SCHEMA and dataset["provenance"]["generator_sha256"] == MATERIAL_PIN and
            dataset["provenance"]["skill"] == "perception", "canonical perception inventory required")
    partitions = dict(training=dataset["training"], **dataset["evaluation"])
    require(set(partitions) == {"training", "held", "canary"}, "closed partitions required")
    exclusions, all_ids, all_sources, all_prompts, triples, records = {}, set(), set(), set(), set(), []
    for split, count in (("training", 96), ("held", 48), ("canary", 12)):
        rows = partitions[split]
        require(type(rows) is list and len(rows) == count, "fixed source denominator differs")
        exclusions[split] = []
        for supplied in rows:
            row = observation_row(supplied)
            source = row["source"]
            source_id, row_id = source["source_id"], row["row_id"]
            prompt_hash = sha(encoded(row["input_messages"]))
            require(row_id not in all_ids and source_id not in all_sources and prompt_hash not in all_prompts, "cross-split or duplicate row/source/prompt")
            all_ids.add(row_id)
            all_sources.add(source_id)
            all_prompts.add(prompt_hash)
            exclusions[split].append(dict(row_id=row_id, source_id=source_id, input_sha256=prompt_hash))
            if split != "canary":
                require(source["split"] == ("train" if split == "training" else "held"), "literal TRAIN-only split violated")
                fields, diagnosis = material.evidence(source, corpus)
                triple = tuple(fields["try"])
                require(triple not in triples, "selected train/held triple overlap")
                triples.add(triple)
            if split != "training":
                continue
            skin = source["template_id"]
            require(skin in tuple(f"train_{index}" for index in range(4)), "TRAIN skin required")
            skin_index = int(skin[-1])
            events = "\n\n".join("Event " + event["event_id"] + "\n" + event["raw_response"] + "\n[OUTCOME] " +
                ("[No public outcome supplied]" if event["raw_outcome"] is None else event["raw_outcome"]) for event in source["events"])
            messages = [dict(role="user", content=material.TRAIN_SKINS[skin_index].format(events=events) + "\n\n" + material.PERCEPTION_TASK)]
            require(row["input_messages"] == messages, "original TRAIN prompt bytes differ")
            assessment = corpus.assess_source(source)
            require(assessment["admissible"] == (diagnosis in SUPPORTED), "source judge/category disagreement")
            earlier = copy.deepcopy(source)
            earlier["events"] = earlier["events"][:1]
            earlier["selected_event_id"] = earlier["events"][0]["event_id"]
            corpus._identify(earlier)
            earlier_assessment = corpus.assess_source(earlier)
            require(earlier_assessment["admissible"], "earlier supplied source invalid")
            selected = False
            if assessment["admissible"]:
                earlier_same = earlier_assessment["execution"]["observed"] == fields["observed"]
                selected = earlier_same == ((skin_index + SUPPORTED.index(diagnosis) + int(fields["observed"])) % 2 == 0)
            records.append(dict(row, source_id=source_id, input_sha256=prompt_hash, diagnosis=diagnosis,
                                public_fields=fields, source_admissible=assessment["admissible"], source_errors=assessment["reasons"],
                                earlier_observed=earlier_assessment["execution"]["observed"], selected=selected))
    require(Counter(row["diagnosis"] for row in records) == {case: 16 for case in material.CASES} and
            Counter(row["source"]["template_id"] for row in records) == {f"train_{index}": 24 for index in range(4)}, "original96 factorial differs")
    strata = Counter((row["source"]["template_id"], row["diagnosis"], row["public_fields"]["observed"]) for row in records if row["source_admissible"])
    require(strata == {(f"train_{skin}", case, outcome): 2 for skin in range(4) for case in SUPPORTED for outcome in (False, True)}, "supported48 factorial differs")
    selected = [row for row in records if row["selected"]]
    require(len(selected) == 24 and Counter((row["source"]["template_id"], row["diagnosis"], row["public_fields"]["observed"]) for row in selected) ==
            {key: 1 for key in strata}, "fixed24 source selection differs")
    return sorted(records, key=lambda row: row["row_id"]), {key: sorted(exclusions[key], key=lambda row: row["row_id"]) for key in ("held", "canary")}


def build(seed=0, *, archive_path=ARCHIVE, source_root=SOURCE_ROOT):
    material, corpus = dependencies(source_root)
    dataset, producer, provenance = original_inputs(seed, archive_path)
    records, excluded = inventory(dataset, material, corpus)
    producer_hash = sha(encoded(producer))
    requests = []
    for row in records:
        if row["selected"]:
            request = dict(schema=SCHEMA, row_id=row["row_id"], source_id=row["source_id"], input_messages=row["input_messages"],
                           input_sha256=row["input_sha256"], producer_sha256=producer_hash, source_split="train")
            request["request_id"] = sha(encoded(request))
            requests.append(request)
    provenance.update(core_sha256=digest(SELF), runner_sha256=RUNNER_PIN, material_generator_sha256=MATERIAL_PIN,
                      source_root=str(Path(source_root).resolve()), source_files=copy.deepcopy(material.PINS),
                      parser_interface=copy.deepcopy(corpus._interface().source_manifest))
    return dict(schema=SCHEMA, boundary=BOUNDARY, producer=producer, producer_sha256=producer_hash, provenance=provenance,
                selection=SELECTION, source_population_denominator=96, source_admissible=48, requested=24,
                training_observations=records, excluded=excluded, requests=requests, selection_sha256=sha(encoded([request["row_id"] for request in requests])),
                prompt_manifest_sha256=sha(encoded(requests)), native_identity_verified=False, training_export_ready=False,
                binding_decisions=["Use ORIGINAL perception post-fit parent only; do not substitute HIGH/LOWER_LR descendants.",
                    "Default24 is a supported-source subset, not the full96-case abstention distribution or a balanced judgement corpus.",
                    "Original public prompt bytes retained, including generic schema/abstention instructions; no case/proof labels appended.",
                    "Native caller must verify actual adapter/model identity and bind each response; hashes here are declarations plus archived identities.",
                    "Main freezes recipient, sampling/call budgets, replay/control dose and fitting separately; no fit or retry decision here."])


def admit(bundle, responses):
    """One batch, no retries; every supplied response is retained in the audit."""
    require(type(bundle) is dict and bundle.get("schema") == SCHEMA, "replay bundle schema differs")
    rebuilt = build(bundle["producer"]["learner_seed"], archive_path=bundle["provenance"]["archive"]["path"],
                    source_root=bundle["provenance"]["source_root"])
    require(encoded(bundle) == encoded(rebuilt), "bundle differs from fixed original TRAIN build")
    require(type(responses) is list and len(responses) <= 96 and all(type(response) is dict for response in responses), "bounded response objects required")
    _, corpus = dependencies(bundle["provenance"]["source_root"])
    requests = {request["request_id"]: request for request in bundle["requests"]}
    observations = {row["row_id"]: row for row in bundle["training_observations"]}
    counts = Counter(response.get("request_id") for response in responses if type(response.get("request_id")) is str)
    accepted, audits = [], []
    required = {"request_id", "input_sha256", "producer_sha256", "raw", "finish_reason"}
    for index, response in enumerate(responses):
        errors, judge = [], None
        request_id = response.get("request_id")
        request = requests.get(request_id) if type(request_id) is str else None
        raw = response.get("raw")
        if set(response) != required:
            errors.append("closed_response_schema_required")
        if request is None:
            errors.append("unknown_or_nonselected_train_request")
        elif counts[request_id] != 1:
            errors.append("duplicate_response_no_retry_selection")
        if type(raw) is not str:
            errors.append("raw_child_text_required")
        if response.get("finish_reason") != "stop":
            errors.append("stop_completion_required")
        if request is not None:
            if response.get("input_sha256") != request["input_sha256"]:
                errors.append("input_prompt_binding_mismatch")
            if response.get("producer_sha256") != request["producer_sha256"]:
                errors.append("original_parent_model_adapter_binding_mismatch")
            source = observations[request["row_id"]]["source"]
            assessment = corpus.assess_source(source)
            if not assessment["admissible"]:
                errors.extend(assessment["reasons"])
            elif type(raw) is str:
                judge = corpus._interface().judge_record(raw, assessment["execution"])
                if not judge["eligible"]:
                    errors.extend(judge["failures"])
        eligible = not errors
        response_hash = sha(encoded(response))
        audit = dict(submission_index=index, response=copy.deepcopy(response), response_sha256=response_hash,
                     raw_sha256=sha(raw.encode()) if type(raw) is str else None, eligible=eligible, errors=errors, source_judge=judge)
        audits.append(audit)
        if eligible:
            accepted.append(dict(row_id=request["row_id"], request_id=request_id, input_messages=copy.deepcopy(request["input_messages"]),
                raw_target=raw, target_sha256=sha(raw.encode()), source=copy.deepcopy(source), producer_sha256=bundle["producer_sha256"],
                source_proof=dict(original_train_row_id=request["row_id"], original_source_id=request["source_id"],
                    input_sha256=request["input_sha256"], supplied_response_sha256=response_hash, target_origin="SUPPLIED_RAW_CHILD_RESPONSE_ONLY")))
    accepted.sort(key=lambda row: row["row_id"])
    ledger = []
    accepted_ids = {row["row_id"] for row in accepted}
    row_requests = {request["row_id"]: request["request_id"] for request in requests.values()}
    for row in bundle["training_observations"]:
        if not row["source_admissible"]:
            status = "source_unsupported_not_requested"
        elif not row["selected"]:
            status = "source_supported_not_selected"
        elif row["row_id"] in accepted_ids:
            status = "admitted"
        elif counts[row_requests[row["row_id"]]]:
            status = "response_rejected"
        else:
            status = "response_missing"
        ledger.append(dict(row_id=row["row_id"], source_id=row["source_id"], status=status, source_errors=row["source_errors"]))
    return dict(schema=SCHEMA, boundary=BOUNDARY, bundle_sha256=sha(encoded(bundle)), producer=copy.deepcopy(bundle["producer"]),
                provenance=copy.deepcopy(bundle["provenance"]), source_population_denominator=96, source_admissible_denominator=48,
                requested_denominator=24, submitted=len(responses), admitted_count=len(accepted), admission_ledger=ledger,
                status_counts=dict(Counter(row["status"] for row in ledger)), admitted=accepted, responses=audits,
                rejected=[audit for audit in audits if not audit["eligible"]], missing_request_ids=sorted(set(requests) - set(counts)),
                native_identity_verified=False, training_export_ready=False, fit_decision=None)

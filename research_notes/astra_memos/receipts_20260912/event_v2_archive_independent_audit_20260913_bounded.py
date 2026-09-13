"""Read-only, standard-library archive audit; never imports experiment code."""

import argparse
import collections
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile


EXPECTED = "fdc22c730206c5c9e6486099fc908b5daaaad78916c106eeb4f738fa86446879"
ARCHIVE = "gpu_artifacts_local/pcfl_v2_acquisition_20260913_attempt1/evidence.tar"
ROOT = "localhome/local-rohing/astra_diagnostics/pcfl_sequence_v2_acquisition_20260913_attempt5/"
SOURCE = "tmp/astra_pcfl_sequence_v2_source_20260913_attempt2.tar"
ORIGINAL = "tmp/astra_pcfl_event_only_original_archive_20260913_attempt1.tar"
SOURCE_PREFIX = "/tmp/astra_pcfl_sequence_v2_source_20260913_attempt2/"
ORIGINAL_ROOT = "pcfl_own_write_format_20260913_attempt1/"
SYSTEM = "You are the child's local personal-memory reader. You receive one opaque address request and no task. Return only the exact stored memory block associated with that address. Do not explain, infer, repair, or invent. If nothing usable is remembered, return exactly MISS."


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value):
    return sha(canonical(value))


def strict_stop(text, target, finish, truncated):
    return text.encode("utf-8") == target.encode("utf-8") and finish == "stop" and truncated is False


class MemberMap:
    def __init__(self, archive):
        self.archive = archive
        members = archive.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)):
            raise ValueError("duplicate tar member names")
        if any(member.name.startswith("/") or ".." in PurePosixPath(member.name).parts
               or not (member.isfile() or member.isdir()) for member in members):
            raise ValueError("unsafe or non-regular tar members")
        self.total = len(members)
        self.files = {member.name: member for member in members if member.isfile()}
        self.hashes = {}

    def read(self, name):
        return self.archive.extractfile(self.files[name]).read()

    def json(self, name):
        return json.loads(self.read(name))

    def hash(self, name):
        if name not in self.hashes:
            with self.archive.extractfile(self.files[name]) as stream:
                hasher = hashlib.sha256()
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    hasher.update(chunk)
                self.hashes[name] = hasher.hexdigest()
        return self.hashes[name]

    def inventory(self):
        return {name: {"sha256": self.hash(name), "size": member.size}
                for name, member in sorted(self.files.items())}


def audit(path, detail):
    failures, unavailable, checks = [], set(), collections.Counter()

    def check(condition, label, category="assertions"):
        checks[category] += 1
        if not condition:
            failures.append(label)

    with path.open("rb") as stream:
        hasher = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    archive_hash = hasher.hexdigest()
    if archive_hash != EXPECTED:
        raise ValueError("archive SHA256 mismatch: " + archive_hash)
    with tarfile.open(path, "r:") as outer:
        members = MemberMap(outer)
        with tarfile.open(fileobj=io.BytesIO(members.read(SOURCE)), mode="r:") as source_tar, \
                tarfile.open(fileobj=io.BytesIO(members.read(ORIGINAL)), mode="r:") as original_tar:
            source, original = MemberMap(source_tar), MemberMap(original_tar)
            old_source_name = "astra_pcfl_own_write_format_source_20260913_attempt1.tar"
            with tarfile.open(fileobj=io.BytesIO(original.read(old_source_name)), mode="r:") as old_source_tar:
                old_source = MemberMap(old_source_tar)
                old_inventory = old_source.inventory()
                old_counts = {"total": old_source.total, "files": len(old_source.files)}
            inventories = {"outer": members.inventory(), "source": source.inventory(), "original": original.inventory(), "original_source": old_inventory}
            check(original.hash(old_source_name) == "698ad6278f69131fdc7721d173753732631b7485b2d420ac293a2ef0e4e50280", "original source tar pin")

            def resolve(name):
                if name.startswith(SOURCE_PREFIX):
                    return source, name[len(SOURCE_PREFIX):]
                return members, name.lstrip("/")

            def pin(value, label):
                mapping, name = resolve(value["path"])
                if name not in mapping.files:
                    unavailable.add(value["path"])
                    return
                check(mapping.hash(name) == value["sha256"], label + " file pin", "file_pins")

            def walk(value, label):
                if isinstance(value, dict):
                    if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
                        pin(value, label)
                    for key, item in value.items():
                        if key in ("source_files", "sources") and isinstance(item, dict):
                            for name, expected in item.items():
                                if name.startswith("/") and isinstance(expected, str) and len(expected) == 64:
                                    pin({"path": name, "sha256": expected}, label + "/" + key)
                        walk(item, label + "/" + key)
                elif isinstance(value, list):
                    for index, item in enumerate(value):
                        walk(item, label + "/" + str(index))

            def seal(value, label):
                check(value["sha256"] == digest({key: item for key, item in value.items() if key != "sha256"}),
                      label + " canonical seal", "seals")

            def inventory_check(base, declared, label, sized=False, exclude=(), mapping=members):
                actual = {name[len(base):] for name in mapping.files if name.startswith(base)} - set(exclude)
                check(actual == set(declared), label + " exact member set", "inventory_sets")
                for name, expected in declared.items():
                    full = base + name
                    check(full in mapping.files, label + "/" + name + " present", "inventory_presence")
                    if full in mapping.files:
                        expected_hash = expected["sha256"] if sized else expected
                        check(mapping.hash(full) == expected_hash, label + "/" + name + " hash", "inventory_hashes")
                        if sized:
                            check(mapping.files[full].size == expected["size"], label + "/" + name + " size", "inventory_sizes")

            original_report = original.json(ORIGINAL_ROOT + "formation/records/formation.json")
            original_outer_base = "pcfl_own_write_format_20260913_attempt1.formation.outer/"
            original_collection = original.json(original_outer_base + "collection.json")
            inventory_check(original_outer_base, original_collection["files"], "original outer inventory", sized=True, exclude=("collection.json",), mapping=original)
            inventory_check(ORIGINAL_ROOT + "formation/", original_collection["stage_inventory"], "original stage inventory", sized=True, mapping=original)
            seal(original_report, "original formation report")
            check(original_report["status"] == "FORMATION_FAILED" and original_collection["status"] == "FAILED"
                  and original_collection["returncode"] == 1, "original failed formation preserved")
            old_source_joins = set()
            for name in original.files:
                if not name.endswith(".json"):
                    continue
                document = original.json(name)
                pending = [document]
                while pending:
                    value = pending.pop()
                    if isinstance(value, dict):
                        for key, expected in value.items():
                            if key.startswith("/tmp/astra_pcfl_own_write_format_source_20260913_attempt1/") and isinstance(expected, str) and len(expected) == 64:
                                relative = key.removeprefix("/tmp/astra_pcfl_own_write_format_source_20260913_attempt1/")
                                check(relative in old_inventory and old_inventory[relative]["sha256"] == expected, "original source join " + relative, "historical_source_pins")
                                old_source_joins.add(relative)
                        pending.extend(value.values())
                    elif isinstance(value, list):
                        pending.extend(value)

            documents = {name: members.json(name) for name in members.files if name.endswith(".json")}
            for name, document in documents.items():
                walk(document, name)
            manifest, completed = documents[ROOT + "manifest.json"], documents[ROOT + "completed.json"]
            check([entry["seed"] for entry in manifest["entries"]] == [0, 1, 2], "unique manifest seeds")
            result_keys = [(item["seed"], item["stage"], item["state"]) for item in completed["results"]]
            expected_keys = [(seed, stage, state) for seed in range(3)
                             for stage, state in [("fit", None), ("readout", "NO_WRITE"), ("readout", "A200")]]
            check(collections.Counter(result_keys) == collections.Counter(expected_keys), "exact nine campaign stages")
            collections_found = sorted(name for name in members.files if name.startswith(ROOT + "runs/") and name.endswith("/collection.json"))
            check(set(collections_found) == {item["collection"]["path"].lstrip("/") for item in completed["results"]}, "campaign-to-collection bijection")
            fit_paths = sorted(name for name in members.files if name.startswith(ROOT + "runs/") and name.endswith("/fit/completed.json"))
            check(fit_paths == [ROOT + f"runs/seed{seed}/fit_outer/fit/completed.json" for seed in range(3)], "only three archived A200 fits")
            check(not any("b200" in name.lower() for name in members.files if name.startswith(ROOT + "runs/")), "no B200 run members")
            stages, calls, material_hashes, record_digests, adapter_hashes, worker_ids = [], [], [], [], [], []
            total_updates, total_presentations = 0, 0
            exceptions, text_classes, source_joins = set(), collections.Counter(), set()
            for source_map in [manifest["source_files"]] + [document.get("source_files", {}) for document in documents.values() if isinstance(document, dict)]:
                source_joins.update(name for name in source_map if name.startswith(SOURCE_PREFIX))
            for seed in range(3):
                material_path = ROOT + f"inputs/seed{seed}/material.json"
                material = documents[material_path]
                spec, phase = material["spec"], material["phases"]["A200"]
                material_hashes.append(members.hash(material_path))
                record_digests.append(digest(spec["records"]))
                check(spec["learner_seed"] == seed, f"material seed {seed}")
                for label, value in [("material", material), ("spec", spec), ("A200 phase", phase), ("tokenizer receipt", material["tokenizer_receipt"])]:
                    seal(value, f"seed{seed} {label}")
                check(spec["roster_sha256"] == digest(spec["roster"]), "roster digest")
                records = spec["records"]
                check([record["index"] for record in records] == list(range(8)), "record indices")
                check([record["call_index"] for record in records] == list(range(1, 16, 2)), "chronological EVENT source calls")
                check([record["bank"] for record in records] == ["A"] * 4 + ["B"] * 4, "A4/B4 banks")
                check(len({record["request"] for record in records}) == 8, "eight distinct addresses")
                for record in records:
                    capture = ORIGINAL_ROOT + f"formation/actor/call_{record['call_index']:04d}.raw.json"
                    raw = original.json(capture)["raw"]
                    response = original.json(capture.replace(".raw.json", ".response.json"))
                    target = record["target"]
                    attempt = original.json(ORIGINAL_ROOT + f"formation/records/call_{record['call_index']:02d}.attempt.json")
                    check(digest(attempt["capture"]) == record["generation"]["capture_sha256"], "original capture envelope hash", "source_record_joins")
                    for name, stored in attempt["capture"]["files"].items():
                        capture_member = ORIGINAL_ROOT + "formation/actor/" + name
                        check(original.read(capture_member) == stored["utf8"].encode() and original.hash(capture_member) == stored["sha256"], "original capture envelope member " + name, "source_record_joins")
                    check(raw["text"] == target == record["generation"]["raw"] == record["row"]["raw"] == response["decoded"] == response["response"]["text"], "source target exact bytes", "source_record_joins")
                    check(sha(target.encode()) == record["generation"]["sha256"] == record["row"]["sha256"] == response["raw_utf8_sha256"], "source target SHA", "source_record_joins")
                    check(response["raw_hex"] == target.encode().hex() and raw["finish_reason"] == "stop", "source bytes and termination", "source_record_joins")
                for outer_name, state, stage in [("fit_outer", None, "fit"), ("no_write_outer", "NO_WRITE", "readout"), ("a200_outer", "A200", "readout")]:
                    base = ROOT + f"runs/seed{seed}/{outer_name}/"
                    label = f"seed{seed}/{outer_name}"
                    collection = documents[base + "collection.json"]
                    receipt = documents[base + stage + "/completed.json"]
                    inputs = documents[base + "inputs.input.json"]
                    seal(collection, label)
                    seal(receipt, label + " completed")
                    check(collection["status"] == "COMPLETED" and collection["errors"] == [] and collection["returncode"] == 0 and collection["gpu_released"] is True, label + " successful release")
                    check((collection.get("phase") == "A200" if stage == "fit" else collection.get("stage") == stage)
                          and collection.get("state") == state, label + " stage state")
                    check(receipt["learner_seed"] == inputs["learner_seed"] == seed, label + " seed join")
                    check(receipt["material_sha256"] == members.hash(material_path) and receipt["spec_sha256"] == spec["sha256"], label + " material join")
                    check(receipt["import_sha256"] == spec["import_sha256"], label + " import join")
                    check(receipt["full_contract_released"] is False and receipt["automatic_promotion"] is False
                          and collection["automatic_promotion"] is False, label + " no claim promotion")
                    check(receipt["inputs"] == collection["inputs"], label + " input receipt join")
                    check(inputs == documents[collection["inputs"]["path"].lstrip("/")] == documents[base + stage + "/inputs.json"], label + " input copies")
                    check(members.read(base + stage + "_completed.json") == members.read(base + stage + "/completed.json"), label + " byte identical completion snapshot")
                    check(collection["completed_sha256"] == receipt["sha256"], label + " completion seal join")
                    inventory_check(base, collection["files"], label + " outer inventory", sized=True, exclude=("collection.json",))
                    inventory_check(base + stage + "/", collection["stage_inventory"], label + " stage inventory", sized=True)
                    inventory_check(base + stage + "/", receipt["files"], label + " receipt inventory", exclude=("completed.json",))
                    binding, context = documents[base + "binding.json"], documents[base + "context.json"]
                    check(binding["argv"][binding["argv"].index("--inputs") + 1] == collection["inputs"]["path"], label + " argv input")
                    check(binding["argv"][binding["argv"].index("--inputs-sha256") + 1] == collection["inputs"]["sha256"], label + " argv pin")
                    check(context["inputs"] == collection["inputs"], label + " context pin")
                    worker = collection["worker_identity"]
                    worker_ids.append((worker["boot_id"], worker["pid"], worker["start_ticks"]))
                    release = documents[base + "worker_release.json"]["value"]
                    check(release["identity"] == worker and release["owned_group_released"] is True, label + " worker release identity")
                    for when in ["pre", "post"]:
                        gpu, cvd, queue = [documents[base + f"{when}_{kind}.json"]["value"] for kind in ["gpu", "cvd", "queue"]]
                        check(gpu["empty"] and not gpu["processes"] and gpu["gpu_uuid"] == inputs["gpu_uuid"], label + " archived " + when + " GPU vacancy")
                        check(cvd["clear"] and not cvd["unexpected"] and not cvd["unresolved"] and queue["matched"], label + " archived " + when + " CVD/queue")
                        for entry in cvd.get("approved_unreadable_services", []):
                            exceptions.add((entry["pid"], entry["exception_scope"]))
                    stage_summary = {"seed": seed, "stage": stage, "state": state, "collection_sha256": members.hash(base + "collection.json"), "completed_file_sha256": members.hash(base + stage + "/completed.json"), "stage_members": len(collection["stage_inventory"]), "outer_members": len(collection["files"])}
                    if stage == "fit":
                        corpus = documents[base + "fit/corpus.json"]
                        config = documents[base + "fit/config.json"]
                        base_identity = documents[base + "fit/base.json"]["reference"]
                        model_binding = documents[inputs["model_binding"]["path"].lstrip("/")]
                        check(base_identity["repository"] == "Qwen/Qwen2.5-7B-Instruct" and base_identity["revision"] == "a09a35458c702b33eeacc393d103063234e8bc28"
                              and base_identity["mount"] == "C0" and base_identity["lora_request"] is None, label + " frozen base identity")
                        check(base_identity["model_binding_sha256"] == inputs["model_binding"]["sha256"], label + " model binding pin")
                        check(base_identity["model_files"] == {name: item["sha256"] for name, item in model_binding["files"].items()}, label + " base file inventory declaration")
                        train = documents[base + "fit/checkpoint/train_manifest.json"]
                        meta = documents[base + "fit/checkpoint/train_meta.json"]
                        check(receipt["phase"] == "A200" and receipt["predecessor"] is None and receipt["warm_start"] is None and receipt["parent_phase"] is None, label + " C0-only initialization")
                        check(binding["argv"][binding["argv"].index("--phase") + 1] == "A200", label + " launched phase")
                        check(corpus == phase["items"] and len(corpus) == 800 and digest(corpus) == phase["items_sha256"] == receipt["items_sha256"], label + " exact material corpus")
                        check(train["corpus"]["sha256"] == members.hash(base + "fit/corpus.json"), label + " training corpus pin")
                        check(config == train["config"] and config["seed"] == meta["seed"] == seed, label + " optimizer seeds")
                        check(all(config[key] == value for key, value in {"rank": 8, "alpha": 16, "dropout": 0.05, "lr": 3e-5, "batch_size": 4, "max_steps": 200, "epochs": 1, "optimizer": "adamw", "pack": False, "shuffle_groups": False}.items()), label + " frozen fit recipe")
                        check(train["steps"] == meta["steps"] == receipt["updates"] == phase["updates"] == 200, label + " 200 updates")
                        check(train["corpus"]["n_items"] == train["corpus"]["n_encoded"] == meta["n_texts"] == 800, label + " 800 encoded presentations")
                        check(train["truncation"]["target_tokens_dropped"] == train["truncation"]["items_truncated"] == train["corpus"]["n_skipped_no_target"] == phase["target_dropped"] == phase["skipped_targets"] == 0, label + " no dropped training targets")
                        counts = collections.Counter()
                        for index, item in enumerate(corpus):
                            record = records[item["meta"]["record"]]
                            counts[(record["index"], item["view"])] += 1
                            check(item["meta"]["bank"] == record["bank"] == "A" and record["index"] == index % 4 and item["order"] == index % 4 and item["group"] == f"batch/{index // 4:04d}" and item["view"] == f"W{(index // 4) % 8}", label + f" corpus order {index}", "training_items")
                            check([span[0] for span in item["spans"] if span[1]] == [record["target"]] and item["meta"]["capture_sha256"] == record["generation"]["capture_sha256"], label + f" literal target {index}", "training_items")
                        check(counts == collections.Counter({(record, f"W{view}"): 25 for record in range(4) for view in range(8)}), label + " 25 views per A fact")
                        total_updates += train["steps"]
                        total_presentations += len(corpus)
                        adapter_hashes.append(members.hash(base + "fit/checkpoint/adapter_model.safetensors"))
                    else:
                        readbase = base + "readout/"
                        settings, scores, close, load = [documents[readbase + name] for name in ["readout_config.json", "scores.json", "actor_close.json", "actor/load.json"]]
                        identity = documents[readbase + "actor/identity.json"]
                        check(identity["pid"] == worker["pid"] and identity["identity"]["route"] == receipt["route"], label + " actor worker and route identity")
                        read_base = identity["identity"]["base_identity"]
                        check(read_base["model_files"] == base_identity["model_files"] and read_base["repository"] == base_identity["repository"]
                              and read_base["revision"] == base_identity["revision"] and read_base["model_binding_sha256"] == inputs["model_binding"]["sha256"], label + " readout frozen base declarations")
                        check(receipt["state"] == scores["state"] == state and receipt["fits"] == receipt["updates"] == 0, label + " readout-only state")
                        check(settings["roster"] == spec["roster"] and settings["roster_sha256"] == spec["roster_sha256"], label + " exact roster")
                        check(receipt["calls"] == scores["denominator"] == len(scores["results"]) == close["calls_consumed"] == close["planned_calls"] == 16, label + " call denominator")
                        check(close["error_type"] is None and close["failed"] is False and close["budget_exceeded"] is False and close["shutdown"]["shutdown_returned"] is True, label + " actor clean close")
                        expected_raw = {readbase + f"actor/call_{index:04d}.raw.json" for index in range(16)}
                        actual_raw = {name for name in members.files if name.startswith(readbase + "actor/") and name.endswith(".raw.json")}
                        check(expected_raw == actual_raw, label + " all raw indices")
                        route = receipt["route"]
                        if state == "NO_WRITE":
                            check(receipt["fit_receipt"] is None and route == {"adapter_files_sha256": None, "arm": "NO_WRITE_C0", "lora_request": None}, label + " no hidden adapter")
                        else:
                            expected_fit = ROOT + f"runs/seed{seed}/fit_outer/fit/completed.json"
                            check(receipt["fit_receipt"] == {"path": "/" + expected_fit, "sha256": members.hash(expected_fit)}, label + " same-seed fit pin")
                            projection = documents[readbase + "adapter_projection.json"]
                            check(projection["source_checkpoint"] == "/" + ROOT + f"runs/seed{seed}/fit_outer/fit/checkpoint", label + " same-seed checkpoint")
                            for name, expected in projection["adapter"]["files"].items():
                                check(members.hash(readbase + "adapter/" + name) == expected["sha256"] == members.hash(ROOT + f"runs/seed{seed}/fit_outer/fit/checkpoint/" + name), label + " adapter mount " + name)
                            check(route["adapter_files_sha256"] == digest(projection["adapter"]["files"]), label + " adapter route digest")
                        panels = {f"W{view}": {bank: {"correct": 0, "denominator": 4, "ids": [], "strict_stop": []} for bank in ["A", "B"]} for view in [0, 8]}
                        token_totals = {"prompt": 0, "output": 0}
                        truncations = 0
                        for index, row in enumerate(spec["roster"]):
                            callbase = readbase + f"actor/call_{index:04d}"
                            rawdoc, returned, request, render = [documents[callbase + suffix + ".json"] for suffix in [".raw", ".response", ".request", ".render"]]
                            raw, response, record = rawdoc["raw"], documents[readbase + f"response_{index:04d}.json"], records[index % 8]
                            check(row["id"] == f"event-sequence-v2/W{0 if index < 8 else 8}/{index % 8:02d}" and row["request"] == record["request"], label + " fixed call grid", "raw_call_checks")
                            check(request["row"] == row and request["request"] == {"id": row["id"]} and response["id"] == row["id"] and response["request_sha256"] == digest({"id": row["id"]}), label + " request identity", "raw_call_checks")
                            public_request = (f"Retrieve the exact stored memory for this request.\n{row['request']}\nReply with only the stored memory block." if row["view"] == 0 else f"Provide the exact stored personal-memory block at this address.\n{row['request']}\nOutput only the block.")
                            messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": public_request}]
                            check(request["messages"] == messages, label + " no answer-bearing request", "raw_call_checks")
                            expected_render = "".join(f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n" for message in messages) + "<|im_start|>assistant\n"
                            check(render["rendered_prompt"] == expected_render, label + " exact answer-free rendered prompt", "raw_call_checks")
                            check(all(item == route for item in [rawdoc["route"], raw["route"], response["route"], request["route"], render["route"]]), label + " raw route", "raw_call_checks")
                            check(returned["response"] == response and returned["raw_hex"] == raw["text"].encode().hex() and returned["raw_utf8_sha256"] == sha(raw["text"].encode()), label + " response bytes", "raw_call_checks")
                            check(all(raw[key] == response[key] for key in ["text", "finish_reason", "stop_reason"]), label + " raw termination join", "raw_call_checks")
                            check(response["truncated"] == (raw["finish_reason"] == "length"), label + " truncation flag", "raw_call_checks")
                            check(raw["prompt_token_ids"] == render["prompt_token_ids"] and render["sampling"]["max_tokens"] == 2048 and render["sampling"]["seed"] == row["seed"], label + " token render and cap", "raw_call_checks")
                            check(render["sampling"] == {"frequency_penalty": 0.0, "ignore_eos": False, "max_tokens": 2048, "n": 1, "presence_penalty": 0.0, "repetition_penalty": 1.0, "seed": row["seed"], "temperature": 0.0, "top_k": -1, "top_p": 1.0}, label + " unconstrained sampling", "raw_call_checks")
                            check(load["model_load_started"] <= load["ready_at"] <= rawdoc["generation_started"] <= rawdoc["generation_ended"] <= settings["deadline"], label + " cold-call chronology", "raw_call_checks")
                            for kind in ["prompt", "output"]:
                                count = len(raw[kind + "_token_ids"])
                                check(count == response[kind + "_tokens"] and count <= settings["max_input_tokens" if kind == "prompt" else "max_output_tokens"], label + " token accounting " + kind, "raw_call_checks")
                                token_totals[kind] += count
                            passed = strict_stop(raw["text"], record["target"], raw["finish_reason"], response["truncated"])
                            result = scores["results"][index]
                            check(result["raw"] == raw["text"] and result["target_sha256"] == sha(record["target"].encode()) and result["strict_stop"] == passed and result["score"]["strict"] == (raw["text"].encode() == record["target"].encode()), label + " independent strict score", "raw_call_checks")
                            panel = panels[f"W{row['view']}"][record["bank"]]
                            panel["correct"] += int(passed)
                            panel["ids"].append(row["id"])
                            panel["strict_stop"].append(passed)
                            truncations += int(raw["finish_reason"] == "length")
                            text_classes["exact_target" if passed else "MISS" if raw["text"] == "MISS" else "wrong_EVENT" if raw["text"].startswith("EVENT ") else "other_failure"] += 1
                            calls.append({"seed": seed, "state": state, "id": row["id"], "bank": record["bank"], "finish": raw["finish_reason"], "output_tokens": len(raw["output_token_ids"]), "strict_stop": passed, "raw_file_sha256": members.hash(callbase + ".raw.json"), "raw_text_sha256": sha(raw["text"].encode()), "target_sha256": sha(record["target"].encode())})
                        check(panels == scores["panels"] == receipt["panels"], label + " independent panels")
                        check(token_totals == receipt["tokens"] and truncations == receipt["truncated"], label + " totals incl truncation")
                        expected_a = 0 if state == "NO_WRITE" else 4
                        check(all(panels[view]["A"]["correct"] == expected_a and panels[view]["B"]["correct"] == 0 for view in ["W0", "W8"]), label + " expected panel pattern")
                        stage_summary.update({"panels": {view: {bank: panel["correct"] for bank, panel in banks.items()} for view, banks in panels.items()}, "tokens": token_totals, "truncated": truncations})
                    stages.append(stage_summary)
                reduction_root = f"localhome/local-rohing/astra_diagnostics/pcfl_sequence_v2_acquisition_reduction_seed{seed}_20260913_attempt1/"
                reduction, request = documents[reduction_root + "receipt.json"], documents[reduction_root + "request.json"]
                seal(reduction, f"seed{seed} reduction")
                check(reduction["learner_seed"] == seed and reduction["request"] == request and reduction["observed_gate"] is True, f"seed{seed} reduction join")
                for state, outer_name in [("NO_WRITE", "no_write_outer"), ("A200", "a200_outer")]:
                    check(reduction["states"][state]["panels"] == documents[ROOT + f"runs/seed{seed}/{outer_name}/readout_completed.json"]["panels"], f"seed{seed} reduction panels")
            check(len(set(record_digests)) == 1, "one shared source bank")
            check(len(set(adapter_hashes)) == 3 and len(set(worker_ids)) == 9, "three distinct adapters and nine worker identities")
            check(len(calls) == len({(call["seed"], call["state"], call["id"]) for call in calls}) == 96, "96 unique compound call identities")
            all_raw = [name for name in members.files if name.endswith(".raw.json")]
            check(len(all_raw) == 96, "no extra outer raw calls")
            original_calls = [name for name in original.files if name.endswith(".raw.json")]
            original_finish = collections.Counter(original.json(name)["raw"]["finish_reason"] for name in original_calls)
            report = {
                "archive_sha256": archive_hash, "archive_bytes": path.stat().st_size,
                "members": {"outer": {"total": members.total, "files": len(members.files)}, "source": {"total": source.total, "files": len(source.files)}, "original": {"total": original.total, "files": len(original.files)}, "original_source": old_counts},
                "inventory_sha256": {name: digest(value) for name, value in inventories.items()},
                "checks": dict(sorted(checks.items())), "failures": failures,
                "unavailable_referenced_paths": sorted(unavailable),
                "archived_CVD_exceptions": sorted(exceptions),
                "counts": {"collections": len(collections_found), "fits": len(fit_paths), "updates": total_updates, "presentations": total_presentations, "raw_calls": len(calls), "strict_stop_passes": sum(call["strict_stop"] for call in calls), "termination": dict(collections.Counter(call["finish"] for call in calls)), "original_raw_calls": len(original_calls), "original_termination": dict(original_finish)},
                "raw_text_classes": dict(text_classes),
                "source_join_files": len(source_joins), "historical_source_join_files": len(old_source_joins),
                "historical_formation": {"status": original_report["status"], "slot_statuses": dict(collections.Counter(slot["status"] for slot in original_report["slots"])), "errors": original_collection["errors"], "original_source_archive_sha256": original.hash(old_source_name)},
                "shared_records_sha256": record_digests[0], "material_file_sha256": material_hashes,
                "adapter_model_sha256": adapter_hashes,
                "artifact_sha256": {name: members.hash(name) for name in [ROOT + "manifest.json", ROOT + "completed.json", SOURCE, ORIGINAL, "tmp/astra_pcfl_acquisition_reduce_20260913.py"]},
                "stages": stages, "call_ledger_sha256": digest(calls),
            }
            if detail == "calls":
                report["calls"] = calls
            if detail == "files":
                report["file_inventories"] = inventories
            return report


def self_test():
    target = "EVENT example\n"
    assert strict_stop(target, target, "stop", False)
    assert not strict_stop(target.rstrip(), target, "stop", False)
    assert not strict_stop(target, target, "length", True)
    assert not strict_stop(target, target, "stop", True)
    assert not strict_stop("MISS", target, "stop", False)
    for names in [["same", "same"], ["../escape"], ["/absolute"], ["symlink"]]:
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w") as archive:
            for name in names:
                member = tarfile.TarInfo(name)
                if name == "symlink":
                    member.type = tarfile.SYMTYPE
                    member.linkname = "outside"
                archive.addfile(member)
        buffer.seek(0)
        with tarfile.open(fileobj=buffer, mode="r:") as archive:
            try:
                MemberMap(archive)
            except ValueError:
                pass
            else:
                raise AssertionError("unsafe tar accepted")
    print("SELF_TEST PASS: 5 byte/termination cases; 4 duplicate/path/type cases")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path(ARCHIVE))
    parser.add_argument("--detail", choices=["summary", "calls", "files"], default="summary")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = audit(args.archive, args.detail)
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(bool(report["failures"]))


if __name__ == "__main__":
    main()

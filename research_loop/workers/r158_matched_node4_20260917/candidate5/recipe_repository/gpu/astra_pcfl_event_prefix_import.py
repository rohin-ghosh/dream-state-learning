"""Fixed SEQ171 EVENT-prefix import only; never execute or relocate old code."""

import copy
from collections.abc import Mapping
import hashlib
import io
import json
from pathlib import Path
import tarfile

from gpu import astra_pcfl_native_actor as native
from organism_v6 import pcfl_vertical_dev as core


SCHEMA = "pcfl.event_prefix_import.v1"
ORIGINAL = "pcfl_own_write_format_20260913_attempt1"
SOURCE_ROOT = "/tmp/astra_pcfl_own_write_format_source_20260913_attempt1"
ARCHIVE_SHA256 = "bd6829dfa4e6c0a63f48cf184e28091e12cf9de9a231e0f6cda6672d5133c869"
SOURCE_TAR_SHA256 = "698ad6278f69131fdc7721d173753732631b7485b2d420ac293a2ef0e4e50280"
FORMATION_SHA256 = "9c1e4099ac0ad4d4f53c55d7a35b0d26e3b7dc6da0620f5321cca416e71e4669"
CORE_SHA256 = "ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e"
QUERIES_SHA256 = "39e2d8d430e54ff3818967790cbe38eb15f41c014010f6647562b4c68ce02f8c"
EVENT_INDICES = tuple(range(1, 16, 2))
FIXED_FILES = {
    "manifest.json": "e1004bfa9f5cea0538a54f5866054285ea3ab7d7820df6f4ef77da5673d791ec",
    "formation/formation_config.json": "66704311982c8668744596b92588684b9c638252058d0f220a6effc16a2303b1",
    "formation/records/formation.json": "595c3e65b8eaa1d73e270094d78f0e3a88c66b3b6a23b44b2677cd807692bd15",
    "formation/actor/config.json": "837ca6a872e4332350d8adb1b725894ed0e17cfcad3636e3209227fe8b7dfebb",
    "formation/actor/identity.json": "593c0440495c53875c312ae1ec0bc4b408f16cbd92e6737c584b60fbc7885db3",
    "formation/actor/load.json": "5063a2f982f064a312b386a1f84dcea4d7e17ab5b689e68f3357fe0380b0abc9",
    "formation/actor_close.json": "205d43c3655a36377cb29e2b12a1a0bdfefbb24445e4b9ceb0a9884ad5ce86b7",
    "formation/shutdown.json": "22ddffc76fb8f4e6afda8a07fcdb08c9f8148f720c375919fd645b49ceeb16e1",
}
OUTER_FILES = {
    "collection.json": "e65f69eeed689b921d489b6297909111aec7562238da1a2b4e541e3fcb6302ac",
    "worker_exit.json": "8716b33c669649d0f539653ebf72a86e2118455a15e0e6f69c7a8865c025cbd0",
    "worker_release.json": "01828c50b91218d2e97cff4cc80378f01de38d3fa59a8254a0b3a0636768b634",
    "post_gpu.json": "8b159ef77663656a78581400872aab816bd756592133d01f3f0ecacd523c635c",
    "post_cvd.json": "1bc16cb958ad3db8c2715bdf56e42677c47498b5785f2aeeac7ebb6be7a6f13f",
}
require, canonical, digest = native.require, native.canonical, native.digest


def seal(value):
    return {**copy.deepcopy(value), "sha256": digest(value)}


def same(actual, expected, label):
    require(canonical(actual) == canonical(expected), label)


def unseal(value, expected):
    native.sha(expected)
    require(type(value) is dict and value.get("sha256") == expected
            and digest({key: item for key, item in value.items() if key != "sha256"}) == expected, "seal drift")


def _record(raw):
    return {"utf8": raw.decode("utf-8"), "sha256": hashlib.sha256(raw).hexdigest()}


def _json(record, expected=None):
    require(type(record) is dict and set(record) == {"utf8", "sha256"}, "file record fields")
    require(core.byte_hash(record["utf8"]) == record["sha256"], "file byte drift")
    if expected is not None:
        require(record["sha256"] == expected, "not the fixed SEQ171 file")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    result = json.loads(record["utf8"], object_pairs_hook=unique)
    canonical(result)
    return result


def _member(archive, name):
    member = archive.getmember(name)
    require(member.isfile() and member.size <= 16 * 1024 * 1024, "bounded regular archive member required")
    return archive.extractfile(member).read()


def load_evidence(archive_path):
    """Read the one fixed archive; no extraction, generation, or source execution."""
    path = Path(archive_path)
    require(path.stat().st_size <= 32 * 1024 * 1024, "bounded original archive required")
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == ARCHIVE_SHA256, "wrong original archive; no alternate attempt")
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        require(len(archive.getnames()) == len(set(archive.getnames())), "duplicate archive members")
        files = {name: _record(_member(archive, ORIGINAL + "/" + name)) for name in FIXED_FILES}
        outer = {name: _record(_member(archive, ORIGINAL + ".formation.outer/" + name)) for name in OUTER_FILES}
        config = _json(files["formation/formation_config.json"])
        source_tar = _member(archive, Path(SOURCE_ROOT).name + ".tar")
        require(hashlib.sha256(source_tar).hexdigest() == SOURCE_TAR_SHA256, "source tar drift")
        with tarfile.open(fileobj=io.BytesIO(source_tar)) as sources:
            require(len(sources.getnames()) == len(set(sources.getnames())), "duplicate source members")
            source_files = {}
            for absolute, expected in config["source_pins"].items():
                require(absolute.startswith(SOURCE_ROOT + "/"), "original source prefix differs")
                payload = _member(sources, absolute[len(SOURCE_ROOT) + 1:])
                require(hashlib.sha256(payload).hexdigest() == expected, "source member drift")
                source_files[absolute] = _record(payload)
        captures = {}
        for index in range(17):
            for suffix in ("request", "render", "raw", "response"):
                name = f"call_{index:04d}.{suffix}.json"
                captures[name] = _record(_member(archive, ORIGINAL + "/formation/actor/" + name))
    return {"archive_sha256": ARCHIVE_SHA256, "source_tar_sha256": SOURCE_TAR_SHA256,
            "files": files, "outer": outer, "sources": source_files, "captures": captures}


def _original(evidence):
    same(sorted(evidence), sorted(["archive_sha256", "source_tar_sha256", "files", "outer", "sources", "captures"]), "evidence fields")
    same([evidence["archive_sha256"], evidence["source_tar_sha256"]], [ARCHIVE_SHA256, SOURCE_TAR_SHA256], "fixed source selection")
    same(sorted(evidence["files"]), sorted(FIXED_FILES), "original file inventory")
    same(sorted(evidence["outer"]), sorted(OUTER_FILES), "outer file inventory")
    files = {name: _json(evidence["files"][name], expected) for name, expected in FIXED_FILES.items()}
    outer = {name: _json(evidence["outer"][name], expected) for name, expected in OUTER_FILES.items()}
    config, report = files["formation/formation_config.json"], files["formation/records/formation.json"]
    for value in (config, report, files["manifest.json"]):
        unseal(value, value["sha256"])
    same(sorted(evidence["sources"]), sorted(config["source_pins"]), "original source map")
    for name, expected in config["source_pins"].items():
        require(name.startswith(SOURCE_ROOT + "/") and evidence["sources"][name]["sha256"] == expected
                and core.byte_hash(evidence["sources"][name]["utf8"]) == expected, "source path/bytes differ")
    require(hashlib.sha256(Path(core.__file__).read_bytes()).hexdigest() == CORE_SHA256, "public replay core drift")
    same(config["source_pins"][SOURCE_ROOT + "/gpu/astra_pcfl_own_write_dev.py"], FORMATION_SHA256, "v3 formation pin")
    same([report["status"], report["counts"], report["writer_payload"], report["fits"], report["updates"]],
         ["FORMATION_FAILED", {"accepted_events": 8, "accepted_links": 0, "attempted_calls": 17,
          "possible_calls": 20, "possible_events": 8, "possible_links": 4}, None, 0, 0], "original failure must remain unchanged")
    same(report["failure"], {"message": "child LINK differs from pre-output choice", "slot": "old/formation/16", "type": "FormationError"}, "original failed LINK")
    same([outer["collection.json"]["status"], outer["collection.json"]["generation_retries"],
          outer["worker_exit.json"]["returncode"], outer["worker_exit.json"]["signal"]], ["FAILED", 0, 1, None], "original rc1/retry evidence")
    same([outer["worker_release.json"]["value"]["owned_group_released"], outer["post_gpu.json"]["value"]["empty"],
          outer["post_cvd.json"]["value"]["clear"], outer["post_cvd.json"]["value"]["owners"]], [True, True, True, []], "original release observations")
    same(files["formation/shutdown.json"]["shutdown_returned"], True, "explicit engine shutdown")
    close = files["formation/actor_close.json"]
    same([close[name] for name in ("kind", "failed", "error_type", "budget_exceeded", "calls_consumed", "token_count_calls")],
         ["NATIVE", False, None, False, 17, 0], "original actor close")
    expected_names = {f"call_{index:04d}.{suffix}.json" for index in range(17) for suffix in ("request", "render", "raw", "response")}
    same(sorted(evidence["captures"]), sorted(expected_names), "all original captures required, including failed LINK")
    for index in range(17):
        embedded = report["slots"][index]["attempt"]["capture"]["files"]
        for suffix in ("request", "render", "raw", "response"):
            name = f"call_{index:04d}.{suffix}.json"
            _json(evidence["captures"][name])
            same(evidence["captures"][name], embedded[name], "original actor file/capture join")
        for name in ("config.json", "identity.json"):
            same(embedded[name], evidence["files"]["formation/actor/" + name], "actor identity/config capture join")
    return files, config, report


def _replay_receipt(receipt, expected, config, report):
    unseal(receipt, expected)
    same(receipt, seal({"schema": "pcfl.event_prefix.original_v3_replay.v1", "method": "EXACT_ORIGINAL_V3_PATH",
         "source_root": SOURCE_ROOT, "source_tar_sha256": SOURCE_TAR_SHA256, "formation_source_sha256": FORMATION_SHA256,
         "config_file_sha256": FIXED_FILES["formation/formation_config.json"],
         "report_file_sha256": FIXED_FILES["formation/records/formation.json"],
         "replay_result": {"report_sha256": report["sha256"], "config_sha256": config["sha256"],
                           "status": "FORMATION_FAILED", "local_replay_valid": True,
                           "native_custody_verified": False, "full_contract_released": False},
         "model_calls": 0, "fits": 0, "updates": 0}), "independent exact-original-path replay receipt")


def build_import(evidence, replay_receipt, replay_receipt_sha256):
    files, config, report = _original(evidence)
    _replay_receipt(replay_receipt, replay_receipt_sha256, config, report)
    settings = config["actor_config"]
    same(settings, files["formation/actor/config.json"], "actor settings")
    same(report["config_sha256"], config["sha256"], "report/config seal")
    same(report["format_scaffold"], {"applies_to": ["EVENT", "LINK"], "policy": "pcfl.disposable_old.format_only_terminal_lf.v1",
         "readout": "UNCONSTRAINED", "regex": r"[^\r\n]+\n"}, "source formatting scaffold")
    session = core.WorldSession(core.from_data(config["planner"]["cell"]), "OLD")
    history = [{"role": "system", "content": core.FORMATION_SYSTEM}]
    rows, generations = [], []
    prior_end = files["formation/actor/load.json"]["ready_at"]
    latest = None
    for index in range(16):
        slot = report["slots"][index]
        same([slot["id"], slot["kind"], slot["status"]], [f"old/formation/{index:02d}", "EVENT" if index % 2 else "EXPLORE", "ACCEPTED"], "whole mandatory prefix")
        attempt = slot["attempt"]
        prefix = f"call_{index:04d}."
        asked, rendered, raw, returned = [_json(evidence["captures"][prefix + suffix + ".json"]) for suffix in ("request", "render", "raw", "response")]
        prompt = session.explore_prompt() if index % 2 == 0 else (
            latest["public"] + session.event_prompt(latest["receipt"]) + "\n"
            "End your response with exactly one LF (U+000A) after the last identifier. "
            "Emit the actual newline character, not the literal characters backslash-n (\\n). Do not add a blank line.")
        history.append({"role": "user", "content": prompt})
        same(attempt["request"], {"id": slot["id"], "messages": history, "seed": config["seed"], "mount": "C0"}, "public prefix history; no later/teacher fields")
        same([asked["request"], asked["limits"], attempt["backend_error"]], [attempt["request"], config["limits"], None], "original request/limits")
        same([asked["request_sha256"], raw["request_sha256"]], [digest(attempt["request"])] * 2, "raw request hash")
        sampling = {"temperature": 0.0, "top_p": 1.0, "top_k": -1, "n": 1, "presence_penalty": 0.0,
                    "frequency_penalty": 0.0, "repetition_penalty": 1.0, "ignore_eos": False,
                    "seed": config["seed"], "max_tokens": config["limits"]["output_tokens"]}
        if index % 2:
            sampling["structured_outputs"] = {"regex": r"[^\r\n]+\n"}
        same(rendered["sampling"], sampling, "original v3 sampling")
        output = raw["raw"]
        same([raw["kind"], raw["mount"], raw["lora_request"], output["finish_reason"]], ["NATIVE", "C0", None, "stop"], "native stop-only prefix")
        response = attempt["response"]
        same(returned["response"], response, "returned response join")
        same([response["text"], returned["decoded"], returned["raw_hex"], returned["raw_utf8_sha256"]],
             [output["text"], output["text"], output["text"].encode().hex(), core.byte_hash(output["text"])], "raw bytes unchanged")
        require(raw["generation_started"] >= files["formation/actor/load.json"]["ready_at"], "preload generation")
        require((index == 0 or prior_end <= raw["operation_started"]) and raw["operation_started"] <= raw["generation_started"] <= raw["generation_ended"], "prefix chronology")
        prior_end = raw["operation_started"] + response["device_seconds"]
        same([response["prompt_tokens"], response["output_tokens"]],
             [len(native.token_ids(output["prompt_token_ids"])), len(native.token_ids(output["output_token_ids"]))], "token counts")
        same(output["prompt_token_ids"], rendered["prompt_token_ids"], "prompt token join")
        if index % 2 == 0:
            same(output["text"], config["planner"]["actions"][index // 2], "fixed original action")
            latest = session.explore(output["text"])
            same(latest, slot["world_result"], "actual public world receipt")
        else:
            admission = core.admit_event(output["text"], latest["receipt"], session, config["planner"]["opportunities"][index // 2]["event_handle"])
            same(admission, slot["admission"], "exact original EVENT admission")
            require(admission["accepted"], "all eight EVENTs required")
            rows.append(admission["row"])
            generations.append({"raw": output["text"], "sha256": core.byte_hash(output["text"]),
                                "origin": "CHILD_NATIVE", "capture_sha256": digest(attempt["capture"])})
        history.append({"role": "assistant", "content": output["text"]})
    queries = core.materialize_queries(rows)
    require(len(rows) == 8 and len(queries) == 14 and core.digest(queries) == QUERIES_SHA256, "fixed eight EVENT/fourteen query material")
    return seal({"schema": SCHEMA, "status": "EVENT_PREFIX_IMPORTED_TOKENIZER_PENDING", "evidence": evidence,
                 "replay_receipt": replay_receipt, "replay_receipt_sha256": replay_receipt_sha256,
                 "selected_call_indices": list(range(16)), "selected_event_indices": list(EVENT_INDICES),
                 "rows": rows, "generations": generations, "queries": queries,
                 "original_status": "FORMATION_FAILED", "original_returncode": 1, "original_calls": 17,
                 "format_scaffold": report["format_scaffold"], "new_model_calls": 0, "fits": 0, "updates": 0,
                 "native_custody_verified": False, "full_contract_released": False})


def validate_import(imported, expected_sha256):
    unseal(imported, expected_sha256)
    same(imported, build_import(imported["evidence"], imported["replay_receipt"], imported["replay_receipt_sha256"]), "prefix import reconstruction differs")
    return {"status": imported["status"], "rows": 8, "queries": 14, "full_contract_released": False}


def verify_tokenizer(imported, tokenizer):
    """Actual CPU tokenizer check; does not load a tokenizer or model itself."""
    from organism_v6 import pcfl_vertical_train as writer
    validate_import(imported, imported["sha256"])
    manifest = _json(imported["evidence"]["files"]["manifest.json"])
    receipt = manifest["binding"]["tokenizer_receipt"]
    writer.verify_tokenizer_files({"contract": {"tokenizer_receipt": receipt}}, tokenizer)
    same(core.byte_hash(tokenizer.chat_template), receipt["chat_template_sha256"], "actual tokenizer template")
    for index in range(16):
        captures = imported["evidence"]["captures"]
        asked = _json(captures[f"call_{index:04d}.request.json"])
        rendered = _json(captures[f"call_{index:04d}.render.json"])
        output = _json(captures[f"call_{index:04d}.raw.json"])["raw"]
        text = tokenizer.apply_chat_template(asked["request"]["messages"], tokenize=False, add_generation_prompt=True)
        same([text, tokenizer.encode(text, add_special_tokens=False)], [rendered["rendered_prompt"], rendered["prompt_token_ids"]], "actual prefix tokenizer render")
        templated = tokenizer.apply_chat_template(asked["request"]["messages"], tokenize=True, add_generation_prompt=True)
        if isinstance(templated, Mapping):
            templated = templated.get("input_ids")
        same(native.token_ids(templated), rendered["prompt_token_ids"], "template/encode token disagreement")
        same(tokenizer.decode(output["output_token_ids"], skip_special_tokens=True), output["text"], "actual output token decode, LF unchanged")
    return seal({"schema": SCHEMA + "/tokenizer", "import_sha256": imported["sha256"],
                 "status": "EVENT_PREFIX_TOKENIZER_VERIFIED", "calls_checked": 16, "model_calls": 0,
                 "tokenizer_files": receipt["files"], "chat_template_sha256": receipt["chat_template_sha256"],
                 "full_contract_released": False})

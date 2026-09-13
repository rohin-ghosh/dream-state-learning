"""Closed root-1 Q0: CPU preparation/replay and opt-in native fresh workers.

No downloads, historical adapters, historical trainers or old reducers. Only
execute/worker with --allow-gpu can touch the reserved GPU. Main launches;
CPU fixtures are never native proof. Owned-group custody, not a C11 expansion.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import signal
import statistics
import sys
import tarfile
import time
from types import SimpleNamespace


VERSION = "astra-pairwise-q0-cpu-sidecar-v1"
ROOT = 1
ORIENTATION = (0, 1, 1, 0, 1, 0, 0, 1)
ACTIONS = ("-mem2reg", "-gvn")
ARMS = ("P_AUTH", "P_DERANGED", "V_AUTH", "P_UNARY_TOOL")
SNAPSHOTS = (32, 64, 128)
MAX_SECONDS, MAX_FITS, UPDATES = 2700, 3, 128
CLEANUP_RESERVE = 45
NATIVE_KIND = "Q0_NATIVE_RAW"
SCOPE = "root1 pair-balanced Q0; seed1 rank8; 128 quartet updates; <=3 fresh attempted fits; <=2700 seconds; C11 deferred"
_TENSOR_STORE = ContextVar("q0_tensor_store", default=None)
_FORWARD_COUNTS = ContextVar("q0_forward_counts", default=None)
PANEL_COUNTS = dict(exact=128, held=64, missing=8, unsupported=8,
                    neighbour=16, wrong_root=64, copy=8)
LOCALITY_COUNTS = {name: PANEL_COUNTS[name] for name in
                   ("missing", "unsupported", "neighbour", "wrong_root")}
RECIPE = dict(rank=8, alpha=16, dropout=.05, seed=1, lr=3e-5,
              betas=[.9, .999], eps=1e-8, weight_decay=.01,
              foreach=False, fused=False, scheduler=False, clipping=False,
              gradient_checkpointing=False, tf32=False, attention="eager",
              base_dtype="torch.bfloat16", trainable_dtype="torch.float32",
              target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                              "gate_proj", "up_proj", "down_proj"],
              updates=128, quartet_size=4, sweeps=4, snapshots=[32, 64, 128])
PUBLIC_MODEL = "Qwen/Qwen2.5-7B-Instruct"
PUBLIC_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
PUBLIC_BINDING_SHA256 = "e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019"
PUBLIC_METADATA_SHA256 = "8aebd0fc61d42917fedbf3c6dd08e39c36eac4c92478c88f2accabadae78de3b"
HELPER_PINS = {
    "gpu/astra_semantic_objective_probe.py": "98a90f33dcd5582b9e32fe21d08dd29283c82b955ff350c8c994d2903b2f0d41",
    "organism_v6/semantic_writer_diagnostic.py": "d6ea45ac6bfb5cabe6cbd1224f4cf101e96cbd0e07c029e934c2aa3e03e1ddb0",
    "organism_v6/multikey_writer_gateway_simple.py": "b9fd33c7c11b2f57395f08d609bb1df004d9663eeefd143060bb1a24a34f10c8",
    "organism_v6/writer_interface_calibration.py": "9ab582ebc935ae36b88bd412fd06d799044661612f89a0770e46b92ab1b066c7",
}
ARCHIVE = "research_notes/astra_memos/receipts_20260912/astra_semantic_writer_terminal_20260912.tgz"
ARCHIVE_SHA256 = "422b27e55f794cd14670f049ad09fd31b95887aa615c4d59bc0a03687e83dcf0"
ARCHIVE_ROOT = "astra_semantic_writer_Q0_20260912_attempt1"
ARCHIVE_PINS = {
    "manifest.json": "f6fa9060e9ea794309839a8651adc728989c283663070b348c3200acca57a830",
    "material.json": "769ee38ab444c9e56b6ce7dbf93be95f49e113ca7a60e02322349a53c3ef4336",
    "fits.json": "8946700f4b94078bc6d15ffd24cfe29c364783f672e90ff36a69a5b077b78aec",
    "SEAL.json": "71f164765d1cdfeef96b881da6eac68de05f1921989f1b167f7dff7b6f088d71",
}
CONTRACTS = (
    "2026-09-12_pairwise_binding_falsifier_adjudication.md",
    "2026-09-12_q0_pairwise_falsifier_implementation_closure_v2.md",
    "2026-09-12_q0_pairwise_falsifier_mathematical_redteam.md",
    "2026-09-12_q0_claim_bearing_implementation_preflight.md",
)
UNRESOLVED = (
    "confirmation-root opaque-ID/optimizer-seed allocation remains unselected and output-blind",
)


class IntegrityError(ValueError):
    """An incomplete or inconsistent receipt is not a scientific null."""


class ContractUnresolved(IntegrityError):
    pass


def require(condition, message):
    if not condition:
        raise IntegrityError(message)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def repository():
    return Path(__file__).resolve().parents[1]


def verify_helpers(base=None):
    base = Path(base) if base is not None else repository()
    for name, expected in HELPER_PINS.items():
        require(file_hash(base / name) == expected, "allowlisted helper drift: " + name)
    return dict(HELPER_PINS)


def contract_manifest():
    base = repository() / "research_notes/analysis"
    return dict(version=VERSION, root=ROOT, recipe=RECIPE, helper_pins=verify_helpers(),
                scientific_precedence=[dict(path=name, sha256=file_hash(base / name))
                                       for name in CONTRACTS],
                public_model=PUBLIC_MODEL, public_revision=PUBLIC_REVISION,
                origin_verification="NOT_PERSONALLY_VERIFIED; prospective Main binding required",
                confirmation_allocation=None, formal_C11_guard="DEFERRED",
                numerical_policy=vars(PRODUCTION_POLICY),
                numerical_authorization="Main 2026-09-13 output-blind: safety=4; floor=1e-12; arithmetic-middle-two",
                native_launch_ready=False, launch_requires="native prepare, regression receipt, reserved A40 and explicit --allow-gpu",
                unresolved=list(UNRESOLVED))


def public_binding(path):
    """Consume Main's permitted model-only receipt, not its experimental plans."""
    return public_binding_bytes(Path(path).read_bytes())


def public_binding_bytes(content):
    require(hashlib.sha256(content).hexdigest() == PUBLIC_BINDING_SHA256, "public-binding receipt hash")
    receipt = json.loads(content)
    require(receipt["repository"] == PUBLIC_MODEL and receipt["revision"] == PUBLIC_REVISION
            and receipt["metadata_sha256"] == PUBLIC_METADATA_SHA256
            and receipt["status"] == "PUBLIC_REVISION_FILES_MATCHED_PROSPECTIVE_BINDING"
            and receipt["clean_lineage_certified"] is False and receipt["historical_receipts_changed"] is False,
            "prospective public-binding scope")
    require(receipt["file_count"] == len(receipt["files"]) == 14
            and Counter(item["public_match"] for item in receipt["files"].values()) == {
                "LFS_SHA256": 4, "GIT_BLOB_SHA1": 10}, "fourteen official matched files")
    return dict(receipt_sha256=PUBLIC_BINDING_SHA256, metadata_sha256=PUBLIC_METADATA_SHA256,
                receipt_utf8=content.decode("utf-8"),
                repository=PUBLIC_MODEL, revision=PUBLIC_REVISION, files=receipt["files"],
                checked_utc=receipt["checked_utc"], verifier="Main; receipt hash checked by CPU sidecar",
                clean_lineage_certified=False, historical_receipts_changed=False)


def read_original_capsule(path=None):
    """Validate the committed projection without opening any historical outputs."""
    path = Path(path) if path is not None else repository() / ARCHIVE
    require(file_hash(path) == ARCHIVE_SHA256, "original capsule hash mismatch")
    blobs = {}
    with tarfile.open(path, "r:gz") as archive:
        names = [member.name for member in archive.getmembers()]
        for name, expected in ARCHIVE_PINS.items():
            full = ARCHIVE_ROOT + "/" + name
            require(names.count(full) == 1, "duplicate/missing original member")
            member = archive.getmember(full)
            require(member.isfile() and member.size < 16 * 1024 * 1024, "unsafe original member")
            with archive.extractfile(member) as stream:
                content = stream.read()
            require(hashlib.sha256(content).hexdigest() == expected, "original member drift: " + name)
            if name != "fits.json":
                blobs[name] = json.loads(content)
    manifest, seal = blobs["manifest.json"], blobs["SEAL.json"]
    for name in ("material.json", "fits.json"):
        require(manifest["artifacts"][name] == seal["files"][name] == ARCHIVE_PINS[name],
                "original manifest/seal disagreement")
    material = blobs["material.json"]
    require(tuple(material["roots"][ROOT]["orientation"]) == ORIENTATION, "root1 orientations")
    return material


def target(row, arm):
    require(arm in ARMS and row["panel"] in ("exact", "held"), "target outside training/evaluation map")
    orientation = ORIENTATION[row["slot"]]
    return orientation if arm == "P_UNARY_TOOL" else orientation ^ row["mode"] ^ (arm == "P_DERANGED")


def source_rows(material):
    """Projection has no old target labels, adapters, fit outputs or random seeds."""
    root = material["roots"][ROOT]
    require(tuple(root["orientation"]) == ORIENTATION and len(root["tools"]) == 8, "root1 topology")
    rows = []
    for panel, original in (("exact", root["train"]["W+"]), ("held", root["held"]),
                            ("wrong_root", material["roots"][0]["held"]), ("spill", root["spill"])):
        for index, raw in enumerate(original):
            family = raw["family"] if panel == "spill" else panel
            probe_root = 0 if family == "wrong_root" else ROOT
            slot = raw.get("slot")
            tool = material["roots"][probe_root]["tools"][slot] if slot is not None else None
            row = dict(panel=family, index=index, root=probe_root, slot=slot, tool=tool,
                       mode=raw.get("mode"), template=raw.get("template"), prompt=raw["context"])
            if family == "copy":
                row["expected"] = raw["expected"]
            rows.append(row)
    require(Counter(row["panel"] for row in rows) == PANEL_COUNTS, "complete original panels")
    for panel, templates in (("exact", range(8)), ("held", range(8, 12))):
        coords = {(row["slot"], row["mode"], row["template"]) for row in rows if row["panel"] == panel}
        require(coords == {(slot, mode, template) for slot in range(8) for mode in range(2)
                           for template in templates}, "8-by-2 template topology")
    return rows


def encode(tokenizer, text):
    result = tokenizer(text, add_special_tokens=False, truncation=False, padding=False,
                       return_offsets_mapping=True)["input_ids"]
    require(isinstance(result, list) and result and all(type(token) is int and token >= 0 for token in result),
            "one unpadded token vector required")
    require(tokenizer.decode(result) == text, "tokenizer exact roundtrip")
    return result


def render(tokenizer, prompt):
    native = getattr(tokenizer, "tokenizer", tokenizer)
    rendered = native.apply_chat_template([dict(role="user", content=prompt)], tokenize=False,
                                          add_generation_prompt=True)
    ids = encode(tokenizer, rendered)
    require(len(ids) + 32 <= 2048, "bounded native prompt")
    start = rendered.find(prompt)
    require(start >= 0 and rendered.count(prompt) == 1, "native user span")
    return dict(rendered_prompt=rendered, prompt_input_ids=ids,
                user_char_span=[start, start + len(prompt)], assistant_boundary=len(ids))


def common_prefix(tokenizer, payload):
    text = payload["rendered_prompt"]
    candidates = [encode(tokenizer, text + "ACT: " + action + "\n") for action in ACTIONS]
    position = 0
    while position < min(map(len, candidates)) and candidates[0][position] == candidates[1][position]:
        position += 1
    require(position < min(map(len, candidates)), "two distinct continuation branches")
    prefix = candidates[0][:position]
    branch_ids = [candidate[position] for candidate in candidates]
    boundary = payload["assistant_boundary"]
    require(prefix == encode(tokenizer, text + "ACT: -"), "maximal natural common prefix")
    require(prefix[:boundary] == payload["prompt_input_ids"] and position > boundary, "assistant boundary drift")
    require(tokenizer.decode(prefix) == text + "ACT: -", "natural assistant suffix")
    require(not set(branch_ids) & set(prefix[boundary:]), "future assistant branch leakage")
    forbidden = {value for value in (getattr(tokenizer, "eos_token_id", None),
                                    getattr(tokenizer, "pad_token_id", None)) if value is not None}
    require(not forbidden & set(prefix[boundary:]), "assistant EOS/padding leakage")
    require(len(prefix) <= 2048, "prefix length cap")
    return dict(input_ids=prefix, decision_prefix_hash=digest(prefix), branch_ids=branch_ids,
                decision_position=position, assistant_span=[boundary, position],
                candidates=candidates, candidate_hashes=[digest(item) for item in candidates])


def schedule(rows):
    exact = [row for row in rows if row["panel"] == "exact"]
    require(len(exact) == 128, "128 exact rows")
    by_key = {(row["slot"], row["mode"], row["template"]): row for row in exact}
    require(len(by_key) == 128, "duplicate exact coordinate")
    tools = {row["slot"]: row["tool"] for row in exact}
    groups = [sorted((slot for slot in range(8) if ORIENTATION[slot] == bit),
                     key=lambda slot: digest(["Q0-XOR-PAIR-v1", ROOT, tools[slot]])) for bit in range(2)]
    quartets = []
    for left, right in zip(*groups):
        for template in range(8):
            quartet = [by_key[slot, mode, template] for slot in (left, right) for mode in range(2)]
            require(all(Counter(target(row, arm) for row in quartet) == {0: 2, 1: 2} for arm in ARMS),
                    "quartet pair balance")
            coords = [[row[key] for key in ("root", "tool", "mode", "template", "decision_prefix_hash")]
                      for row in quartet]
            hashes = [digest(coord) for coord in coords]
            quartets.append(dict(rows=[row["id"] for row in quartet], coordinates=coords,
                                 source_row_hashes=hashes,
                                 order_hash=digest(["Q0-XOR-SCHEDULE-v1", hashes])))
    quartets.sort(key=lambda quartet: quartet["order_hash"])
    require(len(quartets) == 32 and len({item for quartet in quartets for item in quartet["rows"]}) == 128,
            "quartet exact coverage")
    return quartets


def build_prepared(tokenizer, material=None, *, evidence_kind="CPU_FIXTURE_ONLY", public_binding_path=None):
    require(evidence_kind in ("CPU_FIXTURE_ONLY", "NATIVE_TOKENIZER_ONLY"), "preparation is not native execution")
    original = read_original_capsule()
    if material is not None:
        require(material == original, "only original sealed Q0 material")
    rows = []
    for source in source_rows(original):
        payload = render(tokenizer, source["prompt"])
        row = dict(source, **payload)
        if source["panel"] != "copy":
            row.update(common_prefix(tokenizer, payload))
        else:
            row["decision_prefix_hash"] = digest(payload["prompt_input_ids"])
        row["id"] = digest([row["panel"], row["index"], row["decision_prefix_hash"]])
        rows.append(row)
    require(len({row["decision_prefix_hash"] for row in rows}) == 296, "cross-panel prefix collision")
    branches = {tuple(row["branch_ids"]) for row in rows if row["panel"] != "copy"}
    require(branches == {(10536, 21404)}, "discovered native branch ID check")
    require(len({row["decision_position"] - row["assistant_boundary"] for row in rows
                 if row["panel"] != "copy"}) == 1, "relative decision position drift")
    for arm in ARMS:
        require(Counter(target(row, arm) for row in rows if row["panel"] == "exact") == {0: 64, 1: 64},
                "exact map balance")
    quartets = schedule(rows)
    return dict(version=VERSION, evidence_kind=evidence_kind, root=ROOT, recipe=RECIPE,
                capsule_sha256=ARCHIVE_SHA256, helpers=verify_helpers(), rows=rows, quartets=quartets,
                schedule_sha256=digest(quartets), training_order=[item["rows"] for item in quartets] * 4,
                branch_ids=list(next(iter(branches))), eos_token_id=tokenizer.eos_token_id,
                confirmation_allocation=None, native_launch_ready=False,
                public_binding=public_binding(public_binding_path) if public_binding_path is not None else None)


def validate_prepared(prepared, tokenizer):
    expected = build_prepared(tokenizer, evidence_kind=prepared["evidence_kind"])
    if prepared.get("public_binding") is not None:
        binding = prepared["public_binding"]
        require(binding == public_binding_bytes(binding["receipt_utf8"].encode("utf-8")),
                "prepared prospective public binding")
        expected["public_binding"] = binding
    require(prepared == expected,
            "reconstructed material/token projection/schedule drift")


def request_inventory(prepared, state, snapshot):
    require((state == "OFF" and snapshot == 0) or (state in ARMS and snapshot in SNAPSHOTS),
            "registered evaluation stage")
    final = snapshot in (0, 128)
    material_sha256 = digest(prepared)
    requests = []
    for row in prepared["rows"]:
        if not final and row["panel"] not in ("exact", "held"):
            continue
        operations = (["prefix"] if row["panel"] != "copy" else []) + (["generate"] if final else [])
        for operation in operations:
            request = dict(material_sha256=material_sha256, row_id=row["id"], state=state,
                           snapshot=snapshot, operation=operation, attempts=1)
            requests.append(dict(request, request_id=digest(request)))
    require(len(requests) == (584 if final else 192), "request inventory denominator")
    return requests


@dataclass(frozen=True)
class NumericalPolicy:
    """Prospective numerical-error controls; not acquisition/locality thresholds."""

    gradient_floor: float
    safety: float
    median_convention: str

    def __post_init__(self):
        require(math.isfinite(self.gradient_floor) and self.gradient_floor >= 0, "finite gradient floor")
        require(math.isfinite(self.safety) and self.safety >= 1, "finite FP64 safety multiplier")
        require(self.median_convention == "arithmetic_middle_two", "explicit median convention")


PRODUCTION_POLICY = NumericalPolicy(gradient_floor=1e-12, safety=4, median_convention="arithmetic_middle_two")


def require_native_ready(config=None):
    require(config is not None, "native preparation/config and explicit launch authorization required")
    require(config["numerical_policy"] == vars(PRODUCTION_POLICY), "frozen numerical policy; no alternatives")


def torch_module():
    import torch
    return torch


def losses(logits, branch_ids, bit):
    torch = torch_module()
    require(bit in (0, 1) and logits.ndim == 1 and len(set(branch_ids)) == 2, "one natural-prefix logit vector")
    require(bool(torch.isfinite(logits).all()), "nonfinite z_train32")
    logits = logits.float()
    require(bool(torch.isfinite(logits).all()), "nonfinite converted z_train32")
    margin = logits[branch_ids[0]] - logits[branch_ids[1]]
    pairwise = torch.nn.functional.softplus(-(1 - 2 * bit) * margin)
    vocabulary = torch.logsumexp(logits, dim=0) - logits[branch_ids[bit]]
    negative_log_mass = torch.logsumexp(logits, dim=0) - torch.logsumexp(logits[branch_ids], dim=0)
    return pairwise, vocabulary, negative_log_mass


def tensor_hash(tensor):
    torch = torch_module()
    value = tensor.detach().cpu().contiguous()
    result = hashlib.sha256(canonical([str(value.dtype), list(value.shape)]))
    raw = value.reshape(-1).view(torch.uint8)
    for start in range(0, raw.numel(), 1024 * 1024):
        result.update(tensor_bytes(raw[start:start + 1024 * 1024]))
    return result.hexdigest()


def tensor_bytes(value):
    try:
        return value.detach().cpu().contiguous().numpy().tobytes()
    except RuntimeError:
        return bytes(value.detach().cpu().contiguous().view(torch_module().uint8).reshape(-1).tolist())


@contextmanager
def tensor_store(root, writable=False):
    root = Path(root)
    token = _TENSOR_STORE.set((root, writable))
    try:
        yield
    finally:
        _TENSOR_STORE.reset(token)


def tensor_payload(tensor):
    value = tensor.detach().cpu().contiguous()
    require(str(value.dtype) in ("torch.float32", "torch.float64"), "raw canary floating dtype")
    payload = dict(shape=list(value.shape), dtype=str(value.dtype), sha256=tensor_hash(value))
    store = _TENSOR_STORE.get()
    if store is not None:
        root, writable = store
        data = tensor_bytes(value)
        relative = "tensors/" + hashlib.sha256(data).hexdigest() + ".bin"
        path = root / relative
        if writable:
            path.parent.mkdir(exist_ok=True)
        require(not path.is_symlink() and not path.parent.is_symlink(), "tensor store symlink")
        if path.exists():
            require(file_hash(path) == Path(relative).stem, "immutable deduplicated tensor drift")
        else:
            require(writable, "read-only tensor store")
            with path.open("xb") as stream:
                stream.write(data)
        return dict(payload, tensor_file=relative, file_sha256=Path(relative).stem)
    return dict(payload, values=value.reshape(-1).tolist())


def payload_tensor(payload):
    torch = torch_module()
    binary = "tensor_file" in payload
    require(set(payload) == ({"shape", "dtype", "tensor_file", "file_sha256", "sha256"} if binary
                             else {"shape", "dtype", "values", "sha256"}), "raw tensor fields")
    require(payload["dtype"] in ("torch.float32", "torch.float64")
            and all(type(size) is int and size >= 0 for size in payload["shape"]), "raw tensor metadata")
    dtype = getattr(torch, payload["dtype"].split(".")[1])
    if binary:
        store = _TENSOR_STORE.get()
        require(store is not None and re.fullmatch(r"tensors/[0-9a-f]{64}\.bin", payload["tensor_file"]), "bound raw tensor store")
        path = store[0] / payload["tensor_file"]
        require(not path.is_symlink() and not path.parent.is_symlink() and file_hash(path) == payload["file_sha256"],
                "raw tensor file digest")
        data = bytearray(path.read_bytes())
        require(len(data) == math.prod(payload["shape"]) * (4 if dtype == torch.float32 else 8), "binary tensor size")
        value = torch.frombuffer(data, dtype=dtype).clone().reshape(payload["shape"])
        require(bool(torch.isfinite(value).all()), "finite binary tensor")
    else:
        require(math.prod(payload["shape"]) == len(payload["values"])
                and all(type(value) in (float, int) and math.isfinite(value) for value in payload["values"]),
                "raw tensor finite values/count")
        value = torch.tensor(payload["values"], dtype=dtype).reshape(payload["shape"])
    require(bool(torch.isfinite(value).all()), "nonfinite converted raw tensor")
    require(tensor_hash(value) == payload["sha256"], "raw tensor digest")
    return value


def ordered_inventory(named):
    return [dict(name=name, shape=list(value.shape), dtype=str(value.dtype),
                 requires_grad=value.requires_grad, sha256=tensor_hash(value)) for name, value in named]


def finite_gradients(gradients, parameters):
    torch = torch_module()
    require(len(gradients) == len(parameters) > 0, "ordered gradient inventory")
    for gradient, parameter in zip(gradients, parameters):
        require(gradient is not None and gradient.shape == parameter.shape
                and gradient.dtype == torch.float32 and bool(torch.isfinite(gradient).all()),
                "missing/disconnected/nonfinite/wrong-inventory gradient")


def gamma(operations):
    require(type(operations) is int and operations >= 0, "summation length")
    product = operations * 2.0 ** -53
    require(product < 1, "FP64 bound undefined")
    return product / (1 - product)


def fp64_dot(left, right, safety):
    """Summation bound; directional callers require exact FP32->FP64 products."""
    torch = torch_module()
    require(len(left) == len(right) > 0 and math.isfinite(safety) and safety >= 1, "dot inventory/safety")
    total, absolute, count = 0.0, 0.0, 0
    for first, second in zip(left, right):
        require(first.shape == second.shape and bool(torch.isfinite(first).all())
                and bool(torch.isfinite(second).all()), "dot shape/finite operands")
        products = first.detach().to(device="cpu", dtype=torch.float64) * second.detach().to(device="cpu", dtype=torch.float64)
        total += products.sum().item()
        absolute += products.abs().sum().item()
        count += products.numel()
    require(count > 0 and math.isfinite(total) and math.isfinite(absolute), "finite nonempty dot")
    bound = safety * gamma(max(0, count - 1)) * absolute
    return dict(dot=total, abs_sum=absolute, count=count, bound=bound,
                ratio=total / absolute if absolute else None, passed=total > bound)


def gradient_comparison(pairwise, vocabulary, parameters, policy):
    finite_gradients(pairwise, parameters)
    finite_gradients(vocabulary, parameters)
    norm_p = math.sqrt(max(0, fp64_dot(pairwise, pairwise, policy.safety)["dot"]))
    norm_v = math.sqrt(max(0, fp64_dot(vocabulary, vocabulary, policy.safety)["dot"]))
    difference = [second.double() - first.double() for first, second in zip(pairwise, vocabulary)]
    norm_difference = math.sqrt(max(0, fp64_dot(difference, difference, policy.safety)["dot"]))
    zero_p, zero_v = norm_p <= policy.gradient_floor, norm_v <= policy.gradient_floor
    cosine = None if zero_p or zero_v else fp64_dot(pairwise, vocabulary, policy.safety)["dot"] / (norm_p * norm_v)
    return dict(norm_P=norm_p, norm_V=norm_v, norm_difference=norm_difference,
                R=norm_difference / max(norm_p, 1e-12), cosine=cosine,
                zero_P=zero_p, zero_V=zero_v,
                P_sha256=digest([tensor_hash(value) for value in pairwise]),
                V_sha256=digest([tensor_hash(value) for value in vocabulary]))


def classify_audit(rows, quartets, policy):
    require(len(rows) == 128 and len(quartets) == 32, "complete zero-update audit")
    require(len({row["row_id"] for row in rows}) == 128, "unique audit rows")
    for row in rows:
        require(math.isfinite(row["negative_log_M"]) and row["negative_log_M"] >= 0
                and math.isfinite(row["M"]) and 0 <= row["M"] <= 1
                and math.isclose(row["M"], math.exp(-row["negative_log_M"]), rel_tol=1e-14, abs_tol=1e-15),
                "audit mass")
    for item in quartets:
        for key in ("norm_P", "norm_V", "norm_difference", "R"):
            require(math.isfinite(item[key]) and item[key] >= 0, "audit finite norms")
        require(item["zero_P"] == (item["norm_P"] <= policy.gradient_floor)
                and item["zero_V"] == (item["norm_V"] <= policy.gradient_floor), "zero-gradient branch")
        if item["zero_P"] or item["zero_V"]:
            require(item["cosine"] is None, "undefined cosine must be null")
        else:
            require(item["cosine"] is not None and math.isfinite(item["cosine"]), "finite cosine")
    degenerate = (all(row["negative_log_M"] < 1e-3 for row in rows)
                  and all(not item["zero_P"] and not item["zero_V"] and item["R"] < .05
                          and item["cosine"] > .999 for item in quartets))
    return dict(contrast="OBJECTIVE_CONTRAST_" + ("DEGENERATE" if degenerate else "NONDEGENERATE") + "_AT_INIT",
                tangent="ZERO_XOR_TANGENT_AT_INIT" if any(item["zero_P"] for item in quartets) else None,
                all_both_zero=all(item["zero_P"] and item["zero_V"] for item in quartets))


def rng_receipt():
    torch = torch_module()
    cuda = []
    if torch.cuda.is_initialized():
        require(torch.cuda.device_count() == 1, "one reserved CUDA device")
        cuda = [tensor_hash(state) for state in torch.cuda.get_rng_state_all()]
    return dict(cpu=tensor_hash(torch.get_rng_state()), cuda=cuda)


def tree_state(value):
    torch = torch_module()
    if isinstance(value, torch.Tensor):
        return dict(tensor_sha256=tensor_hash(value), dtype=str(value.dtype), shape=list(value.shape))
    if isinstance(value, dict):
        return [[str(key), tree_state(item)] for key, item in value.items()]
    if isinstance(value, (tuple, list)):
        return [tree_state(item) for item in value]
    return value


def state_receipt(model, optimizer, *, full_frozen=False):
    named = list(model.named_parameters())
    return dict(parameters=ordered_inventory([(name, value) for name, value in named if value.requires_grad]),
                frozen_versions=[[name, list(value.shape), str(value.dtype), value._version, value.data_ptr()]
                                 for name, value in named if not value.requires_grad],
                frozen_sha256=digest(ordered_inventory([(name, value) for name, value in named if not value.requires_grad]))
                if full_frozen else None,
                buffers=ordered_inventory(list(model.named_buffers())),
                modes=[[name, module.training] for name, module in model.named_modules()],
                gradients=[[name, tensor_hash(parameter.grad) if parameter.grad is not None else None]
                           for name, parameter in model.named_parameters()],
                optimizer=tree_state(optimizer.state_dict()) if optimizer is not None else None,
                rng=rng_receipt())


@contextmanager
def neutral_diagnostic(model, optimizer):
    before = state_receipt(model, optimizer, full_frozen=True)
    modes = [(module, module.training) for module in model.modules()]
    model.eval()
    try:
        yield
        require(all(not module.training for module in model.modules()), "diagnostic mutated module mode")
    finally:
        for module, training in modes:
            module.training = training
        require(state_receipt(model, optimizer, full_frozen=True) == before, "diagnostic mutated RNG/tensor/buffer/gradient/optimizer")


def trainables(model):
    torch = torch_module()
    named = [(name, parameter) for name, parameter in model.named_parameters() if parameter.requires_grad]
    require(named and all(parameter.dtype == torch.float32 and parameter.device.type in ("cpu", "cuda")
                          for _, parameter in named), "FP32 trainables required")
    require(len({name for name, _ in named}) == len(named), "trainable order/name uniqueness")
    return named


def audit_optimizer(model, optimizer):
    named = trainables(model)
    require(len(optimizer.param_groups) == 1 and not optimizer.state, "one group and empty optimizer state")
    require(type(optimizer) is torch_module().optim.AdamW, "exact AdamW optimizer")
    group = optimizer.param_groups[0]
    require([id(parameter) for parameter in group["params"]] == [id(parameter) for _, parameter in named],
            "optimizer parameter order")
    for name, value in dict(lr=3e-5, betas=(.9, .999), eps=1e-8, weight_decay=.01,
                            foreach=False, fused=False, amsgrad=False, maximize=False,
                            capturable=False, differentiable=False).items():
        require(group.get(name) == value, "optimizer field drift: " + name)
    return dict(trainables=ordered_inventory(named), optimizer=tree_state(optimizer.state_dict()), rng=rng_receipt())


def adamw(model):
    return torch_module().optim.AdamW([parameter for _, parameter in trainables(model)],
                                     lr=3e-5, betas=(.9, .999), eps=1e-8, weight_decay=.01,
                                     foreach=False, fused=False)


def natural_forward(model, row, hidden=False):
    torch = torch_module()
    require(row["panel"] != "copy", "copy is generation only")
    device = next(model.parameters()).device
    ids = torch.tensor([row["input_ids"]], dtype=torch.long, device=device)
    counts = _FORWARD_COUNTS.get()
    if counts is not None:
        counts["natural_prefix_forwards"] += 1
    output = model(input_ids=ids, use_cache=False, output_hidden_states=hidden)
    if device.type == "cuda":
        require(output.logits.dtype == torch.bfloat16, "native BF16 emitted logits before z_train32")
    return output


def step_zero(model, rows, optimizer):
    hashes = []
    with neutral_diagnostic(model, optimizer), torch_module().no_grad():
        for row in rows:
            logits = natural_forward(model, row).logits[0, -1]
            hashes.append([row["id"], tensor_hash(logits)])
    return digest(hashes)


def objective_audit(model, optimizer, prepared, policy, budget):
    torch = torch_module()
    initial = audit_optimizer(model, optimizer)
    by_id = {row["id"]: row for row in prepared["rows"]}
    exact = [row for row in prepared["rows"] if row["panel"] == "exact"]
    parameters = [parameter for _, parameter in trainables(model)]
    raw_rows, raw_quartets = [], []
    with neutral_diagnostic(model, optimizer):
        for quartet in prepared["quartets"]:
            budget.check()
            pair_losses, vocab_losses = [], []
            for row_id in quartet["rows"]:
                row = by_id[row_id]
                logits = natural_forward(model, row).logits[0, -1]
                pair, vocab, negative_log_mass = losses(logits, row["branch_ids"], target(row, "P_AUTH"))
                pair_losses.append(pair)
                vocab_losses.append(vocab)
                raw_logits = logits.detach().float().cpu()
                prefix = prefix_record(raw_logits, row["branch_ids"])
                pair_normalizer = max(prefix["z0"], prefix["z1"]) + math.log1p(math.exp(-abs(prefix["d"])))
                raw_rows.append(dict(row_id=row_id, M=prefix["M"],
                                     negative_log_M=max(0., prefix["log_normalizer"] - pair_normalizer),
                                     logits_sha256=tensor_hash(logits), emitted_dtype=str(logits.dtype),
                                     raw_z_train32=tensor_payload(raw_logits), prefix=prefix))
            grad_p = torch.autograd.grad(torch.stack(pair_losses).mean(), parameters, retain_graph=True, allow_unused=True)
            grad_v = torch.autograd.grad(torch.stack(vocab_losses).mean(), parameters, allow_unused=True)
            raw_quartets.append(dict(quartet_sha256=digest(quartet),
                                     raw_P=[tensor_payload(value) for value in grad_p] if all(value is not None for value in grad_p) else [],
                                     raw_V=[tensor_payload(value) for value in grad_v] if all(value is not None for value in grad_v) else [],
                                     **gradient_comparison(grad_p, grad_v, parameters, policy)))
    logits_hashes = {row["row_id"]: row["logits_sha256"] for row in raw_rows}
    initial["step_zero_logits_sha256"] = digest([[row["id"], logits_hashes[row["id"]]] for row in exact])
    return dict(initial=initial, rows=raw_rows, quartets=raw_quartets,
                decision=classify_audit(raw_rows, raw_quartets, policy), optimizer_steps=0, raw_logits_recorded=True)


def validate_audit_raw(audit, prepared, policy):
    exact_ids = {row["id"] for row in prepared["rows"] if row["panel"] == "exact"}
    require({row["row_id"] for row in audit["rows"]} == exact_ids, "audit exact row identity")
    require([row["quartet_sha256"] for row in audit["quartets"]] == [digest(item) for item in prepared["quartets"]],
            "audit quartet order")
    by_id = {row["id"]: row for row in prepared["rows"]}
    if audit.get("raw_logits_recorded"):
        for item in audit["rows"]:
            logits = payload_tensor(item["raw_z_train32"])
            require(item["emitted_dtype"] in ("torch.float32", "torch.bfloat16") and logits.dtype == torch_module().float32,
                    "audit emitted/training dtype")
            rebuilt = prefix_record(logits, by_id[item["row_id"]]["branch_ids"])
            pair_normalizer = max(rebuilt["z0"], rebuilt["z1"]) + math.log1p(math.exp(-abs(rebuilt["d"])))
            require(item["prefix"] == rebuilt and item["M"] == rebuilt["M"]
                    and item["negative_log_M"] == max(0., rebuilt["log_normalizer"] - pair_normalizer)
                    and item["logits_sha256"] == tensor_hash(logits.to(getattr(torch_module(), item["emitted_dtype"].split(".")[1]))),
                    "raw zero-update logits/mass reconstruction")
    for item in audit["quartets"]:
        grad_p = [payload_tensor(value) for value in item["raw_P"]]
        grad_v = [payload_tensor(value) for value in item["raw_V"]]
        require([list(value.shape) for value in grad_p] == [entry["shape"] for entry in audit["initial"]["trainables"]]
                and [list(value.shape) for value in grad_v] == [entry["shape"] for entry in audit["initial"]["trainables"]],
                "audit ordered gradient/trainable inventory")
        rebuilt = gradient_comparison(grad_p, grad_v, grad_p, policy)
        require({key: item[key] for key in rebuilt} == rebuilt, "raw P/V gradient audit reconstruction")
    decision = classify_audit(audit["rows"], audit["quartets"], policy)
    require(decision == audit["decision"] and audit["optimizer_steps"] == 0, "sealed pre-fit objective selection")
    return decision


def head_margin(hidden, weights, policy):
    torch = torch_module()
    require(hidden.ndim == 1 and len(weights) == 2 and all(weight.shape == hidden.shape for weight in weights),
            "two output-head products")
    hidden = hidden.to(device="cpu", dtype=torch.float64)
    weights = [weight.to(device="cpu", dtype=torch.float64) for weight in weights]
    products = [hidden * weight for weight in weights]
    dots = [product.sum() for product in products]
    margin = dots[0] - dots[1]
    absolute = [product.detach().abs().sum().item() for product in products]
    dot_values = [value.detach().item() for value in dots]
    bound = policy.safety * (gamma(hidden.numel()) * sum(absolute)
                              + 2.0 ** -53 * sum(abs(value) for value in dot_values))
    require(math.isfinite(margin.item()) and math.isfinite(bound), "finite d_canary64")
    return margin, dict(d_canary64=margin.item(), dots=dot_values, abs_sums=absolute,
                        hidden_size=hidden.numel(), bound=bound,
                        hidden_sha256=tensor_hash(hidden), head_sha256=[tensor_hash(weight) for weight in weights],
                        hidden=tensor_payload(hidden), head=[tensor_payload(weight) for weight in weights])


def canary_surface(model, row, policy):
    torch = torch_module()
    output = natural_forward(model, row, hidden=True)
    repeated = natural_forward(model, row, hidden=True)
    require(torch.equal(output.logits, repeated.logits)
            and torch.equal(output.hidden_states[-1], repeated.hidden_states[-1]), "non-bit-identical canary forwards")
    hidden = output.hidden_states[-1][0, -1].double()
    head = model.get_output_embeddings()
    require(getattr(head, "bias", None) is None and not head.weight.requires_grad, "fixed bias-free output head")
    weights = [head.weight[branch].double() for branch in row["branch_ids"]]
    margin, record = head_margin(hidden, weights, policy)
    record["z_train32"] = [output.logits[0, -1, branch].float().item() for branch in row["branch_ids"]]
    return margin, record


def canary_before(model, optimizer, quartet, arm, policy):
    torch = torch_module()
    parameters = [parameter for _, parameter in trainables(model)]
    signed_gradients, surfaces = [], []
    with neutral_diagnostic(model, optimizer):
        for row in quartet:
            margin, surface = canary_surface(model, row, policy)
            gradients = torch.autograd.grad(margin, parameters, allow_unused=True)
            finite_gradients(gradients, parameters)
            signed_gradients.append([gradient.detach().clone() * (1 - 2 * target(row, arm)) for gradient in gradients])
            surfaces.append(surface)
    return signed_gradients, surfaces


def canary_result(signed_gradients, delta, before, after, signs, policy):
    require(len(signed_gradients) == len(before) == len(after) == len(signs) == 4, "four canary predicates")
    require(all(value.dtype == torch_module().float32 for group in signed_gradients for value in group)
            and all(value.dtype == torch_module().float32 for value in delta), "directional operands must be FP32 before FP64 products")
    projections = [fp64_dot(gradients, delta, policy.safety) for gradients in signed_gradients]
    observed = []
    for previous, current, sign in zip(before, after, signs):
        require(sign in (-1, 1) and previous["head_sha256"] == current["head_sha256"], "fixed canary output head")
        change = sign * (current["d_canary64"] - previous["d_canary64"])
        bound = previous["bound"] + current["bound"] + policy.safety * 2.0 ** -53 * (
            abs(previous["d_canary64"]) + abs(current["d_canary64"]))
        observed.append(dict(signed_change=change, bound=bound, passed=change > bound))
    gram_records = [[fp64_dot(left, right, policy.safety) for right in signed_gradients] for left in signed_gradients]
    gram = [[entry["dot"] for entry in row] for row in gram_records]
    torch = torch_module()
    eigenvalues = torch.linalg.eigvalsh(torch.tensor(gram, dtype=torch.float64))
    psd_bound = max(sum(entry["bound"] for entry in row) for row in gram_records)
    psd_bound += policy.safety * gamma(4) * max(sum(abs(entry) for entry in row) for row in gram)
    require(eigenvalues.min().item() >= -psd_bound, "signed Gram failed analytic PSD implementation check")
    return dict(passed=all(item["passed"] for item in projections + observed),
                projections=projections, observed=observed, gram=gram, gram_error_bound=psd_bound,
                delta_convention="theta_after_minus_theta_before", surface="d_canary64",
                interpretation="REGISTERED_FIRST_QUARTET_UPDATE_MISS" if not all(
                    item["passed"] for item in projections + observed) else "REGISTERED_FIRST_QUARTET_UPDATE_PASS")


def replay_canary(raw, policy):
    torch = torch_module()
    require(raw["policy_sha256"] == digest(vars(policy)), "canary numerical policy binding")
    before_parameters = [payload_tensor(value) for value in raw["parameters_before"]]
    after_parameters = [payload_tensor(value) for value in raw["parameters_after"]]
    delta = [payload_tensor(value) for value in raw["delta"]]
    require(len(before_parameters) == len(after_parameters) == len(delta) > 0, "canary parameter inventory")
    for previous, current, change in zip(before_parameters, after_parameters, delta):
        require(previous.dtype == current.dtype == change.dtype == torch.float32
                and previous.shape == current.shape == change.shape
                and torch.equal((current - previous).float(), change), "actual FP32 parameter delta convention")
    gradients = [[payload_tensor(value) for value in group] for group in raw["signed_gradients"]]
    for group in gradients:
        finite_gradients(group, before_parameters)
    for surface in raw["before"] + raw["after"]:
        _, rebuilt = head_margin(payload_tensor(surface["hidden"]),
                                 [payload_tensor(value) for value in surface["head"]], policy)
        require({key: value for key, value in surface.items() if key != "z_train32"} == rebuilt,
                "raw hidden/output-head canary reconstruction")
        require(len(surface.get("z_train32", [])) == 2
                and all(math.isfinite(value) for value in surface["z_train32"]), "finite training-surface diagnostic")
    return canary_result(gradients, delta, raw["before"], raw["after"], raw["signs"], policy)


@dataclass
class Budget:
    start: float
    lease_cutoff: float
    clock: object = time.monotonic
    attempts: int = 0
    updates: int = 0
    forwards: int = 0

    def __post_init__(self):
        require(math.isfinite(self.start) and math.isfinite(self.lease_cutoff), "finite monotonic deadline")
        self.deadline = min(self.start + MAX_SECONDS, self.lease_cutoff)
        self.check()

    def check(self):
        now = self.clock()
        require(math.isfinite(now) and self.start <= now < self.deadline, "root/lease deadline exhausted")

    def attempt(self):
        self.check()
        require(self.attempts < MAX_FITS, "three-attempt fit cap; no retry")
        self.attempts += 1

    def step(self):
        self.check()
        require(self.updates < MAX_FITS * UPDATES, "root update cap")
        self.updates += 1
        self.forwards += 4


def train_fit(model, optimizer, prepared, arm, audit_initial, policy, budget, emit, save_snapshot,
              *, diagnostic_only=False):
    """One uninterrupted CPU fit; callbacks must durably retain partial evidence."""
    torch = torch_module()
    sink = emit

    def emit(name, payload):
        before = state_receipt(model, optimizer)
        sink(name, payload)
        require(state_receipt(model, optimizer) == before, "artifact callback mutated numerical state")

    require(arm in ARMS and (not diagnostic_only or arm == "P_DERANGED"), "registered fit")
    budget.attempt()
    initial = audit_optimizer(model, optimizer)
    exact = [row for row in prepared["rows"] if row["panel"] == "exact"]
    initial["step_zero_logits_sha256"] = step_zero(model, exact, optimizer)
    require(initial == audit_initial, "audit/fit initial tensors, parameter order, RNG or logits differ")
    emit("initial", initial)
    by_id = {row["id"]: row for row in prepared["rows"]}
    named = trainables(model)
    parameters = [parameter for _, parameter in named]
    steps, snapshots, canary, canary_raw = [], {}, None, None
    for update, row_ids in enumerate(prepared["training_order"], 1):
        budget.check()
        require(budget.updates < MAX_FITS * UPDATES, "root update cap before forward/backward")
        require(update <= UPDATES and len(row_ids) == 4, "registered quartet update count")
        quartet = [by_id[row_id] for row_id in row_ids]
        if update == 1:
            gradients, before_surfaces = canary_before(model, optimizer, quartet, arm, policy)
            before_parameters = [parameter.detach().clone() for parameter in parameters]
            emit("canary_before", dict(surfaces=before_surfaces,
                                       signed_gradients=[[value.clone() for value in group] for group in gradients],
                                       parameters=before_parameters))
        model.train()
        optimizer.zero_grad(set_to_none=True)
        row_losses, random_states = [], []
        for row in quartet:
            budget.check()
            random_states.append(rng_receipt())
            pairwise, vocabulary, _ = losses(natural_forward(model, row).logits[0, -1],
                                             row["branch_ids"], target(row, arm))
            row_losses.append(vocabulary if arm == "V_AUTH" else pairwise)
        loss = torch.stack(row_losses).mean()
        require(bool(torch.isfinite(loss)), "finite quartet loss")
        loss.backward()
        finite_gradients([parameter.grad for parameter in parameters], parameters)
        optimizer.step()
        require(all(bool(torch.isfinite(parameter).all()) for parameter in parameters), "finite updated parameters")
        for state in optimizer.state.values():
            require(all(not isinstance(value, torch.Tensor) or value.dtype == torch.float32
                        and bool(torch.isfinite(value).all()) for value in state.values()), "FP32 finite AdamW state")
        budget.step()
        step = dict(update=update, row_ids=row_ids, loss=loss.item(), rng=random_states,
                    tensor_sha256=digest(ordered_inventory(named)))
        steps.append(step)
        emit("step", step)
        if update == 1:
            delta = [(parameter.detach() - previous).float() for parameter, previous in zip(parameters, before_parameters)]
            with neutral_diagnostic(model, optimizer):
                after_surfaces = [canary_surface(model, row, policy)[1] for row in quartet]
            canary = canary_result(gradients, delta, before_surfaces, after_surfaces,
                                   [1 - 2 * target(row, arm) for row in quartet], policy)
            canary_raw = dict(policy_sha256=digest(vars(policy)),
                              parameters_before=[tensor_payload(value) for value in before_parameters],
                              parameters_after=[tensor_payload(parameter) for parameter in parameters],
                              delta=[tensor_payload(value) for value in delta],
                              signed_gradients=[[tensor_payload(value) for value in group] for group in gradients],
                              before=before_surfaces, after=after_surfaces,
                              signs=[1 - 2 * target(row, arm) for row in quartet])
            require(replay_canary(canary_raw, policy) == canary, "first-update raw canary replay")
            emit("canary_after", dict(result=canary, surfaces=after_surfaces, delta=delta,
                                      parameters=[parameter.detach().clone() for parameter in parameters]))
            if not canary["passed"] or diagnostic_only:
                break
        if update in SNAPSHOTS:
            state = state_receipt(model, optimizer, full_frozen=True)
            snapshots[str(update)] = save_snapshot(update, model)
            require(state_receipt(model, optimizer, full_frozen=True) == state, "snapshot mutated optimizer/model/RNG")
            emit("snapshot", dict(update=update, receipt=snapshots[str(update)]))
    expected = 1 if diagnostic_only or not canary["passed"] else UPDATES
    budget.check()
    require(len(steps) == expected and set(snapshots) == (set() if expected == 1 else {"32", "64", "128"}),
            "exact fit/snapshot counts")
    return dict(arm=arm, initial=initial, canary=canary, canary_raw=canary_raw,
                updates=len(steps), training_forwards=4 * len(steps),
                steps=steps, snapshots=snapshots, diagnostic_only=diagnostic_only)


def prefix_record(logits, branch_ids):
    torch = torch_module()
    logits = logits.detach().float()
    require(logits.ndim == 1 and bool(torch.isfinite(logits).all()), "finite readout logits")
    legal = logits[branch_ids].double()
    log_normalizer = torch.logsumexp(logits.double(), dim=0).item()
    z0, z1 = legal.tolist()
    return canonical_prefix(dict(z0=z0, z1=z1, log_normalizer=log_normalizer))


def canonical_prefix(primitives):
    first, second, normalizer = (primitives[key] for key in ("z0", "z1", "log_normalizer"))
    require(all(type(value) in (float, int) and math.isfinite(value) for value in (first, second, normalizer)),
            "finite canonical prefix primitives")
    difference = first - second
    require(math.isfinite(difference), "finite canonical margin")
    pair_normalizer = max(first, second) + math.log1p(math.exp(-abs(difference)))
    arithmetic_floor = 4 * max(math.ulp(pair_normalizer), math.ulp(normalizer))
    require(normalizer >= pair_normalizer - arithmetic_floor, "full normalizer below legal pair mass")
    q = 1 / (1 + math.exp(-difference)) if difference >= 0 else math.exp(difference) / (1 + math.exp(difference))
    mass = math.exp(min(0., pair_normalizer - normalizer))
    return dict(z0=first, z1=second, d=difference, log_normalizer=normalizer, q=q, M=mass)


def evaluate(model, prepared, state, snapshot, tokenizer, generate, budget, emit):
    """Main must call once per fresh snapshot load; no generator is loaded here."""
    torch = torch_module()
    require(not model.training and not any(parameter.requires_grad for parameter in model.parameters()),
            "readout must be a fresh frozen eval load")
    rows = {row["id"]: row for row in prepared["rows"]}
    records = []
    for request in request_inventory(prepared, state, snapshot):
        budget.check()
        row = rows[request["row_id"]]
        with torch.inference_mode():
            output = (prefix_record(natural_forward(model, row).logits[0, -1], row["branch_ids"])
                      if request["operation"] == "prefix" else generate(model, tokenizer, row,
                                                                               max_new_tokens=32, do_sample=False))
        record = dict(request, output=output)
        validate_record(record, request, row, tokenizer)
        emit("readout", record)
        records.append(record)
    return records


def strict_identity(text, truncated, ended):
    require(type(text) is str and type(truncated) is bool and type(ended) is bool, "raw generation types")
    if text.count("ACT:") > 1:
        return "MULTIPLE"
    match = re.fullmatch(r"ACT: (-[A-Za-z0-9][A-Za-z0-9_-]*)", text.strip(" \t\r\n"))
    if not match or truncated or not ended:
        return "INVALID"
    action = match.group(1)
    return {ACTIONS[0]: "MEM2REG", ACTIONS[1]: "GVN"}.get(action, "OTHER_SINGLE(" + action + ")")


def validate_record(record, request, row, tokenizer):
    require({key: value for key, value in record.items() if key != "output"} == request, "raw request/attempt binding")
    output = record["output"]
    if request["operation"] == "prefix":
        require(set(output) == {"z0", "z1", "d", "log_normalizer", "q", "M"}
                and all(type(value) in (int, float) and math.isfinite(value) for value in output.values()),
                "finite raw prefix fields")
        rebuilt = canonical_prefix(output)
        require(output["d"] == rebuilt["d"] and 0 <= output["q"] <= 1 and 0 <= output["M"] <= 1
                and math.isclose(output["q"], rebuilt["q"], rel_tol=1e-14, abs_tol=1e-15)
                and math.isclose(output["M"], rebuilt["M"], rel_tol=1e-14, abs_tol=1e-15), "raw q/M algebra")
    else:
        require(set(output) == {"generated_ids", "text", "decoded_with_terminal_eos", "eos_terminated", "truncated"},
                "raw generation fields")
        ids = output["generated_ids"]
        require(isinstance(ids, list) and len(ids) <= 32 and all(type(token) is int and token >= 0 for token in ids),
                "generation token cap")
        ended = bool(ids) and ids[-1] == tokenizer.eos_token_id
        body = ids[:-1] if ended else ids
        require(tokenizer.eos_token_id not in body and output["eos_terminated"] is ended
                and output["truncated"] is (len(ids) == 32 and not ended)
                and tokenizer.decode(body) == output["text"]
                and tokenizer.decode(ids) == output["decoded_with_terminal_eos"], "raw generation decoding/EOS")


def indexed_readout(prepared, records, state, snapshot, tokenizer):
    requests = request_inventory(prepared, state, snapshot)
    require(len(records) == len(requests) and len({record["request_id"] for record in records}) == len(records),
            "complete unique readout denominator")
    by_request = {record["request_id"]: record for record in records}
    rows = {row["id"]: row for row in prepared["rows"]}
    result = defaultdict(dict)
    for request in requests:
        require(request["request_id"] in by_request, "missing registered request")
        record = by_request[request["request_id"]]
        row = rows[request["row_id"]]
        validate_record(record, request, row, tokenizer)
        if request["operation"] == "generate":
            output = record["output"]
            result[row["id"]]["identity"] = strict_identity(output["text"], output["truncated"], output["eos_terminated"])
            result[row["id"]]["text"] = output["text"]
        else:
            result[row["id"]].update(canonical_prefix(record["output"]))
    return dict(result)


def median(values, policy):
    require(policy.median_convention == "arithmetic_middle_two" and values
            and all(math.isfinite(value) for value in values), "explicit finite median convention")
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    lower, upper = ordered[middle - 1:middle + 1]
    result = (lower + upper) / 2 if lower <= 0 <= upper else lower + (upper - lower) / 2
    require(math.isfinite(result), "finite median output")
    return result


def acquisition_gates(rows, on, off, arm, panel, policy):
    selected = [row for row in rows if row["panel"] == panel]
    require(len(selected) == PANEL_COUNTS[panel], "acquisition denominator")
    correct, recalls, validity, multiple = 0, [0, 0], 0, 0
    key_correct, key_margins, gains, tool_correct = defaultdict(int), defaultdict(list), [[], []], defaultdict(int)
    for row in selected:
        item, baseline = on[row["id"]], off[row["id"]]
        bit = target(row, arm)
        success = item["identity"] == ("MEM2REG", "GVN")[bit]
        correct += success
        recalls[bit] += success
        validity += item["identity"] in ("MEM2REG", "GVN")
        multiple += item["identity"] == "MULTIPLE"
        key = (row["slot"], row["mode"])
        key_correct[key] += success
        tool_correct[row["slot"]] += success
        key_margins[key].append((1 - 2 * bit) * item["d"])
        gains[bit].append((1 - 2 * bit) * (item["d"] - baseline["d"]))
    exact = panel == "exact"
    coverage = sum(value >= 7 for value in key_correct.values()) if exact else sum(
        median(values, policy) > 0 for values in key_margins.values())
    medians = [median(values, policy) for values in gains]
    core = correct >= (116 if exact else 52) and min(recalls) >= (56 if exact else 24)
    interface = validity >= (122 if exact else 61) and multiple == 0
    key_gate = coverage >= (14 if exact else 12)
    gain_gate = not exact or min(medians) > 0
    return dict(total=len(selected), correct=correct, recalls=recalls, class_denominators=[len(selected) // 2] * 2,
                valid=validity, multiple=multiple, key_coverage=coverage, key_denominator=16,
                key_correct={str(key): value for key, value in sorted(key_correct.items())},
                gain_medians=medians, tools_at_14=sum(value >= 14 for value in tool_correct.values()),
                core=core, interface=interface, key_gate=key_gate, gain_gate=gain_gate,
                passed=core and interface and key_gate and gain_gate)


def locality_gates(rows, on, off, family):
    selected = [row for row in rows if row["panel"] == family]
    require(len(selected) == LOCALITY_COUNTS[family], "locality family denominator")
    changes_q, changes_mass, transitions = [], [], Counter()
    a_changes, identity_changes, valid_to_invalid, invalid_to_valid = 0, 0, 0, 0
    for row in selected:
        current, baseline = on[row["id"]], off[row["id"]]
        changes_q.append(abs(current["q"] - baseline["q"]))
        changes_mass.append(abs(current["M"] - baseline["M"]))
        previous, following = baseline["identity"], current["identity"]
        previous_a, following_a = previous in ("MEM2REG", "GVN"), following in ("MEM2REG", "GVN")
        a_changes += previous_a != following_a
        identity_changes += previous != following
        valid_to_invalid += previous_a and not following_a
        invalid_to_valid += not previous_a and following_a
        transitions[previous + "->" + following] += 1
    mean_q, mean_mass = statistics.mean(changes_q), statistics.mean(changes_mass)
    cap = 3 if family == "wrong_root" else 0
    return dict(total=len(selected), mean_abs_delta_q=mean_q, mean_abs_delta_M=mean_mass,
                max_abs_delta_q=max(changes_q), max_abs_delta_M=max(changes_mass),
                a_changes=a_changes, identity_changes=identity_changes, integer_cap=cap,
                valid_to_invalid=valid_to_invalid, invalid_to_valid=invalid_to_valid,
                transitions=dict(sorted(transitions.items())),
                passed=mean_q <= .05 and mean_mass <= .05 and max(changes_q) <= .10
                and max(changes_mass) <= .10 and a_changes <= cap and identity_changes <= cap)


def copy_count(rows, readout):
    copies = [row for row in rows if row["panel"] == "copy"]
    require(len(copies) == 8, "eight-copy denominator")
    return sum(readout[row["id"]]["identity"] not in ("INVALID", "MULTIPLE")
               and readout[row["id"]]["text"].strip(" \t\r\n") == row["expected"] for row in copies)


def cell_gates(prepared, on, off, arm, policy):
    rows = prepared["rows"]
    exact = acquisition_gates(rows, on, off, arm, "exact", policy)
    held = acquisition_gates(rows, on, off, arm, "held", policy)
    locality = {family: locality_gates(rows, on, off, family) for family in LOCALITY_COUNTS}
    copies = copy_count(rows, on)
    return dict(exact=exact, held=held, locality=locality, copy_correct=copies,
                passed=exact["passed"] and held["passed"] and copies == 8
                and all(item["passed"] for item in locality.values()))


def checkpoint_curve(prepared, readout, arm, policy):
    curve = {}
    for panel in ("exact", "held"):
        margins = [[] for _ in range(2)]
        for row in prepared["rows"]:
            if row["panel"] == panel:
                bit = target(row, arm)
                margins[bit].append((1 - 2 * bit) * readout[row["id"]]["d"])
        curve[panel] = dict(total=sum(map(len, margins)), class_denominators=list(map(len, margins)),
                            mean_signed_margin=[statistics.mean(values) for values in margins],
                            median_signed_margin=[median(values, policy) for values in margins])
    return curve


def next_fit(decision, fits, cells):
    names = [fit["arm"] for fit in fits]
    require(len(names) <= MAX_FITS and len(set(names)) == len(names), "fit attempt uniqueness/cap")
    require(names[:2] == ["P_AUTH", "P_DERANGED"][:len(names[:2])], "mandatory map ordering")
    if decision.get("all_both_zero"):
        require(not names, "both-zero audit cannot release rescue fits")
        return None
    if not fits:
        return dict(arm="P_AUTH", diagnostic_only=False)
    if len(fits) == 1:
        return dict(arm="P_DERANGED", diagnostic_only=not fits[0]["canary"]["passed"])
    if len(fits) == 3:
        return None
    if not all(fit["canary"]["passed"] for fit in fits):
        return dict(arm="P_UNARY_TOOL", diagnostic_only=False)
    if decision["contrast"] == "OBJECTIVE_CONTRAST_NONDEGENERATE_AT_INIT":
        return dict(arm="V_AUTH", diagnostic_only=False)
    require(set(cells) >= {"P_AUTH", "P_DERANGED"}, "exact evidence required before degenerate arm release")
    if not all(cells[arm]["exact"]["passed"] for arm in ("P_AUTH", "P_DERANGED")):
        return dict(arm="P_UNARY_TOOL", diagnostic_only=False)
    return None


def validate_fit(fit, prepared, expected, initial, policy):
    require(fit["arm"] == expected["arm"] and fit["diagnostic_only"] == expected["diagnostic_only"],
            "sealed dynamic release violated")
    require(fit["initial"] == initial, "unequal audit/fit initialization")
    by_id = {row["id"]: row for row in prepared["rows"]}
    require(fit["canary_raw"]["signs"] == [1 - 2 * target(by_id[row_id], fit["arm"])
                                          for row_id in prepared["training_order"][0]], "canary target-map signs")
    require(fit["canary"] == replay_canary(fit["canary_raw"], policy), "canary summary differs from raw first update")
    stopped = fit["diagnostic_only"] or not fit["canary"]["passed"]
    updates = 1 if stopped else 128
    require(fit["updates"] == updates and fit["training_forwards"] == 4 * updates and len(fit["steps"]) == updates,
            "fit exact work counts")
    require(set(fit["snapshots"]) == (set() if stopped else {"32", "64", "128"}), "snapshot inventory")
    for update, (step, row_ids) in enumerate(zip(fit["steps"], prepared["training_order"]), 1):
        require(step["update"] == update and step["row_ids"] == row_ids and len(step["rng"]) == 4
                and math.isfinite(step["loss"]), "step/order/RNG count drift")


class Lifecycle:
    """CPU state machine for Main's future serial, fresh-worker dispatcher.

    Issuing a ticket is not launching a job. A failed ticket is terminal and
    cannot be reissued. Distinct load/process identities are mandatory even
    for snapshot evaluation; adapter selection is never outcome-conditioned.
    """

    def __init__(self, prepared, tokenizer, policy, budget, *, evidence_kind="CPU_FIXTURE_ONLY"):
        self.prepared, self.tokenizer, self.policy, self.budget = prepared, tokenizer, policy, budget
        require(evidence_kind in ("CPU_FIXTURE_ONLY", NATIVE_KIND), "lifecycle evidence type")
        self.evidence = dict(evidence_kind=evidence_kind, prepared_sha256=digest(prepared),
                             fits=[], readouts={})
        self.cells, self.queue = {}, [("audit", None, None)]
        self.pending, self.processes, self.loads, self.receipts = None, set(), set(), []
        self.failed = False

    def issue(self):
        self.budget.check()
        require(not self.failed and self.pending is None, "no retry or concurrent stage")
        if not self.queue:
            return None
        kind, arm, snapshot = self.queue.pop(0)
        ticket = dict(sequence=len(self.receipts), kind=kind, arm=arm, snapshot=snapshot,
                      prepared_sha256=digest(self.prepared), deadline=self.budget.deadline,
                      evidence_kind=self.evidence["evidence_kind"])
        if kind == "fit":
            release = next_fit(self.evidence["audit"]["decision"], self.evidence["fits"], self.cells)
            require(release is not None and release["arm"] == arm, "registered next fit")
            ticket["diagnostic_only"] = release["diagnostic_only"]
        self.pending = dict(ticket, ticket_sha256=digest(ticket))
        return dict(self.pending)

    def _schedule_fit(self):
        release = next_fit(self.evidence["audit"]["decision"], self.evidence["fits"], self.cells)
        if release:
            self.queue.append(("fit", release["arm"], None))

    def accept(self, ticket, payload, receipt):
        try:
            self.budget.check()
            require(not self.failed and self.pending == ticket, "outstanding stage ticket binding")
            require(receipt["ticket_sha256"] == ticket["ticket_sha256"] and receipt["attempts"] == 1,
                    "stage receipt/attempt binding")
            require(receipt["evidence_kind"] == self.evidence["evidence_kind"], "stage evidence type")
            process = (receipt["pid"], receipt["process_start"])
            load = receipt["load_id"]
            require(process not in self.processes and load not in self.loads, "fresh lifecycle-isolated process/load required")
            require(receipt["status"] == "FINISHED" and receipt["cleanup"] == "COMPLETE"
                    and receipt["start"] <= receipt["finish"] < self.budget.deadline
                    and receipt["start"] >= self.budget.start, "worker failure/deadline/cleanup")
            if self.receipts:
                require(receipt["start"] >= self.receipts[-1]["finish"], "serial stage lifecycle")
            self.processes.add(process)
            self.loads.add(load)
            self.receipts.append(receipt)
            self.pending = None
            kind, arm, snapshot = ticket["kind"], ticket["arm"], ticket["snapshot"]
            if kind == "audit":
                require(self.evidence["evidence_kind"] != NATIVE_KIND or payload.get("raw_logits_recorded") is True,
                        "native audit requires full raw logits")
                decision = validate_audit_raw(payload, self.prepared, self.policy)
                self.evidence["audit"] = payload
                if not decision["all_both_zero"]:
                    self.queue.append(("eval", "OFF", 0))
            elif kind == "fit":
                require(self.budget.attempts < MAX_FITS, "three-attempt fit cap")
                self.budget.attempt()
                expected = dict(arm=arm, diagnostic_only=ticket["diagnostic_only"])
                validate_fit(payload, self.prepared, expected, self.evidence["audit"]["initial"], self.policy)
                self.evidence["fits"].append(payload)
                if payload["updates"] == 128:
                    self.queue.extend(("eval", arm, update) for update in SNAPSHOTS)
                else:
                    self._schedule_fit()
            else:
                result = indexed_readout(self.prepared, payload, arm, snapshot, self.tokenizer)
                self.evidence["readouts"][arm + "/" + str(snapshot)] = payload
                if arm == "OFF":
                    require(copy_count(self.prepared["rows"], result) == 8, "OFF copy before fit")
                    self.off = result
                    self._schedule_fit()
                else:
                    fit = next(item for item in self.evidence["fits"] if item["arm"] == arm)
                    require(receipt["adapter"] == fit["snapshots"][str(snapshot)], "fresh snapshot reload binding")
                    if snapshot == 128:
                        self.cells[arm] = cell_gates(self.prepared, result, self.off, arm, self.policy)
                        self._schedule_fit()
        except (IntegrityError, KeyError, ValueError, TypeError) as error:
            self.failed = True
            self.queue.clear()
            self.evidence["integrity_abort"] = ("NONREPORTABLE_PRECHECK_ABORT" if "audit" not in self.evidence
                                                  else "NONREPORTABLE_RUNTIME_ABORT")
            self.evidence["partial_failure"] = str(error)
            raise IntegrityError(str(error)) from error

    def report(self):
        require(self.failed or not self.queue and self.pending is None, "unfinished lifecycle is not a terminal")
        return reduce_evidence(self.prepared, self.evidence, self.tokenizer, self.policy)


def primary_label(fits, cells, complements, wrong_root_opposites):
    if not fits[0]["canary"]["passed"]:
        return "EARLY_XOR_QUARTET_STOP_AUTH"
    if not fits[1]["canary"]["passed"]:
        return "EARLY_XOR_QUARTET_STOP_DERANGED"
    if not all(cells[arm]["exact"]["passed"] for arm in ("P_AUTH", "P_DERANGED")):
        return "LOCAL_XOR_DIRECTIONS_NOT_PRESERVED"
    if not all(cells[arm]["held"]["passed"] for arm in ("P_AUTH", "P_DERANGED")):
        return "STORED_NOT_EXTRACTABLE"
    if (not all(cells[arm]["passed"] for arm in ("P_AUTH", "P_DERANGED"))
            or complements["exact"] < 112 or complements["held"] < 48 or wrong_root_opposites > 3):
        return "CONDITIONAL_BINDING_WITH_SPILL_OR_INTERFACE_FAILURE"
    return "SUPERVISED_ONE_ROOT_XOR_BINDING_PASS"


def reduce_evidence(prepared, evidence, tokenizer, policy):
    """CPU fixture classification only. Scientific/native promotion is unavailable."""
    try:
        validate_prepared(prepared, tokenizer)
        require(evidence["evidence_kind"] in ("CPU_FIXTURE_ONLY", NATIVE_KIND), "unknown execution evidence")
        require(evidence["prepared_sha256"] == digest(prepared), "evidence/material binding")
        if evidence.get("integrity_abort"):
            require(evidence["integrity_abort"] in ("NONREPORTABLE_PRECHECK_ABORT", "NONREPORTABLE_RUNTIME_ABORT"),
                    "integrity terminal enum")
            return dict(label=evidence["integrity_abort"], evidence_kind="CPU_FIXTURE_ONLY", scientific_claim=False)
        audit = evidence["audit"]
        decision = validate_audit_raw(audit, prepared, policy)
        fits, readouts = evidence["fits"], evidence["readouts"]
        require(len(fits) <= 3, "fit cap")
        if decision["all_both_zero"]:
            require(not fits and not readouts, "no V rescue after both-zero tangent")
            return dict(label="ZERO_XOR_TANGENT_AT_INIT", evidence_kind="CPU_FIXTURE_ONLY", scientific_claim=False)
        off = indexed_readout(prepared, readouts["OFF/0"], "OFF", 0, tokenizer)
        require(copy_count(prepared["rows"], off) == 8, "contemporary OFF copy failure before fits")
        cells, indexed, seen, required_readouts, curves = {}, {}, [], {"OFF/0"}, {}
        for fit in fits:
            release = next_fit(decision, seen, cells)
            require(release is not None, "prohibited extra fit")
            validate_fit(fit, prepared, release, audit["initial"], policy)
            for prior in seen:
                count = min(len(prior["steps"]), len(fit["steps"]))
                require([step["rng"] for step in prior["steps"][:count]] == [step["rng"] for step in fit["steps"][:count]],
                        "cross-arm pre-forward RNG mismatch")
            seen.append(fit)
            if fit["updates"] == 128:
                for snapshot in SNAPSHOTS:
                    key = fit["arm"] + "/" + str(snapshot)
                    required_readouts.add(key)
                    result = indexed_readout(prepared, readouts[key], fit["arm"], snapshot, tokenizer)
                    curves.setdefault(fit["arm"], {})[str(snapshot)] = checkpoint_curve(prepared, result, fit["arm"], policy)
                    if snapshot == 128:
                        indexed[fit["arm"]] = result
                        cells[fit["arm"]] = cell_gates(prepared, result, off, fit["arm"], policy)
        require(next_fit(decision, seen, cells) is None and set(readouts) == required_readouts, "incomplete terminal lifecycle")
        require(len(seen) >= 2, "both mandatory attempts required")
        complements = dict(exact=0, held=0)
        wrong_root_opposites = 0
        if all(arm in indexed for arm in ("P_AUTH", "P_DERANGED")):
            for row in prepared["rows"]:
                auth, deranged = (indexed[arm][row["id"]]["identity"] for arm in ("P_AUTH", "P_DERANGED"))
                opposite = {auth, deranged} == {"MEM2REG", "GVN"}
                if row["panel"] in complements:
                    correct = auth == ("MEM2REG", "GVN")[target(row, "P_AUTH")]
                    complements[row["panel"]] += opposite and correct
                elif row["panel"] == "wrong_root":
                    wrong_root_opposites += opposite
        label = primary_label(seen, cells, complements, wrong_root_opposites)
        qualifiers = []
        if decision["tangent"]:
            qualifiers.append(decision["tangent"])
        if not seen[0]["canary"]["passed"]:
            qualifiers.append("FIRST_STEP_MAP_ASYMMETRY" if seen[1]["canary"]["passed"] else "BOTH_MAP_FIRST_STEP_MISS")
        if label == "LOCAL_XOR_DIRECTIONS_NOT_PRESERVED":
            qualifiers.append("MAP_ASYMMETRY" if sum(cells[arm]["exact"]["passed"] for arm in
                                                   ("P_AUTH", "P_DERANGED")) == 1 else "BOTH_XOR_EXACT_NULL")
        if len(seen) == 3:
            optional = seen[-1]
            if optional["arm"] == "V_AUTH":
                if not optional["canary"]["passed"]:
                    qualifiers += ["EARLY_V_AUTH_QUARTET_STOP", "OBJECTIVE_CONTRAST_AMBIGUOUS"]
                else:
                    p_pass, v_pass = cells["P_AUTH"]["passed"], cells["V_AUTH"]["passed"]
                    differences = [[], []]
                    for row in prepared["rows"]:
                        if row["panel"] == "exact":
                            bit = target(row, "P_AUTH")
                            differences[bit].append((1 - 2 * bit) * (
                                indexed["P_AUTH"][row["id"]]["d"] - indexed["V_AUTH"][row["id"]]["d"]))
                    if label == "SUPERVISED_ONE_ROOT_XOR_BINDING_PASS" and p_pass and not v_pass and all(
                            statistics.mean(values) > 0 for values in differences):
                        qualifier = "PAIRWISE_NORMALIZATION_SUPPORT_AUTH_INSTANCE"
                    elif p_pass and v_pass:
                        qualifier = "COMMON_PREFIX_BOTH_OBJECTIVES_PASS_AUTH_INSTANCE"
                    elif v_pass and not p_pass:
                        qualifier = "PAIRWISE_REJECTED_AUTH_INSTANCE"
                    else:
                        qualifier = "OBJECTIVE_CONTRAST_AMBIGUOUS"
                    qualifiers.append(qualifier)
            else:
                unary = cells.get("P_UNARY_TOOL")
                passed = unary is not None and unary["exact"]["core"] and unary["held"]["core"]
                passed = passed and unary["exact"]["tools_at_14"] >= 7 and unary["exact"]["interface"] and unary["held"]["interface"]
                passed = passed and unary["copy_correct"] == 8 and all(item["passed"] for item in unary["locality"].values())
                if not optional["canary"]["passed"]:
                    qualifiers.append("EARLY_UNARY_TOOL_STOP")
                qualifiers.append("UNARY_TOOL_PASS_XOR_FAIL" if passed else "OPAQUE_TOOL_WRITE_FAILURE_THIS_RECIPE")
        return dict(label=label, qualifiers=qualifiers, cells=cells, complements=complements, checkpoint_curves=curves,
                    complement_denominators=dict(exact=128, held=64), wrong_root_opposites=wrong_root_opposites,
                    wrong_root_denominator=64, attempted_fits=len(fits),
                    updates=sum(fit["updates"] for fit in fits),
                    training_forwards=sum(fit["training_forwards"] for fit in fits),
                    generations=sum(record["operation"] == "generate" for records in readouts.values() for record in records),
                    prefix_readouts=sum(record["operation"] == "prefix" for records in readouts.values() for record in records),
                    evidence_kind="CPU_FIXTURE_ONLY", scientific_claim=False, native_launch_ready=False)
    except (IntegrityError, KeyError, TypeError, ValueError, OverflowError) as error:
        return dict(label="NONREPORTABLE_RUNTIME_ABORT", reason=str(error),
                    evidence_kind="CPU_FIXTURE_ONLY", scientific_claim=False, native_launch_ready=False)


def inventory(root):
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), "regular evidence directory")
    files = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "evidence symlink")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = file_hash(path)
        else:
            require(path.is_dir(), "nonregular evidence artifact")
    return files


def write_once(root, name, value):
    require(Path(name).name == name and name not in ("", ".", ".."), "flat write-once artifact")
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), "regular output root")
    with (root / name).open("xb") as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())


def seal_fixture(root, prepared, evidence, tokenizer, policy):
    require(not inventory(root), "fresh CPU evidence root; no resume/reseal")
    write_once(root, "prepared.json", prepared)
    write_once(root, "evidence.json", evidence)
    write_once(root, "policy.json", vars(policy))
    report = reduce_evidence(prepared, evidence, tokenizer, policy)
    write_once(root, "report.json", report)
    write_once(root, "SEAL.json", dict(version=VERSION, evidence_kind="CPU_FIXTURE_ONLY", files=inventory(root)))
    return report


def replay(root, tokenizer):
    root = Path(root)
    files = inventory(root)
    require("SEAL.json" in files, "missing evidence seal")
    seal = json.loads((root / "SEAL.json").read_bytes())
    require(seal["version"] == VERSION and seal["evidence_kind"] == "CPU_FIXTURE_ONLY", "CPU seal only")
    require({name: value for name, value in files.items() if name != "SEAL.json"} == seal["files"], "sealed inventory drift")
    prepared, evidence, policy = [json.loads((root / name).read_bytes()) for name in
                                  ("prepared.json", "evidence.json", "policy.json")]
    report = reduce_evidence(prepared, evidence, tokenizer, NumericalPolicy(**policy))
    require(canonical(report) == (root / "report.json").read_bytes(), "exact reducer replay bytes")
    return dict(report=report, report_sha256=file_hash(root / "report.json"), replay="EXACT_CPU_REPLAY",
                scientific_claim=False)


def historical_helpers():
    verify_helpers()
    dependencies = {
        "organism_v6/run_reasoning_neutral.py": "dd4f0a72cddc8226fa48ce50ab0faa6dd4e75f9db510aa89cfb5224898ee7496",
    }
    for name, expected in dependencies.items():
        require(file_hash(repository() / name) == expected, "archived transitive helper changed: " + name)
    gateway = importlib.import_module("organism_v6.multikey_writer_gateway_simple")
    interface = importlib.import_module("organism_v6.writer_interface_calibration")
    supervisor = importlib.import_module("organism_v6.run_reasoning_neutral")
    source = repository() / "organism_v6/semantic_writer_diagnostic.py"
    functions = [node for node in ast.parse(source.read_bytes()).body if isinstance(node, ast.FunctionDef) and node.name == "fit_model"]
    require(len(functions) == 1, "one pinned clean-base construction helper")
    namespace = {"w0": gateway}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), "exec"), namespace)
    diagnostic = SimpleNamespace(w0=gateway, cal=interface, fit_model=namespace["fit_model"],
                                 carrier=SimpleNamespace(process_identity=process_identity))
    return diagnostic, supervisor, dependencies


def process_identity(pid):
    fields = (Path("/proc") / str(pid) / "stat").read_text().rsplit(")", 1)[1].split()
    return dict(pid=pid, ppid=int(fields[1]), pgid=int(fields[2]), session=int(fields[3]), start_ticks=int(fields[19]))


def native_source_pins():
    _, _, dependencies = historical_helpers()
    pins = dict(HELPER_PINS, **dependencies)
    names = ["gpu/astra_pairwise_q0.py", "tests/test_astra_pairwise_q0.py", ARCHIVE]
    names += ["research_notes/analysis/" + name for name in CONTRACTS]
    names += ["tests/test_semantic_objective_probe.py", "tests/test_semantic_writer_diagnostic.py",
              "tests/test_multikey_writer_gateway_simple.py", "tests/test_writer_interface_calibration.py",
              "tests/test_run_reasoning_neutral.py"]
    pins.update({name: file_hash(repository() / name) for name in names})
    return pins


def native_config_template():
    return dict(model=PUBLIC_MODEL, revision=PUBLIC_REVISION, model_path="/absolute/clean/snapshot",
                tokenizer_path="/absolute/clean/snapshot", public_binding_path=None,
                environment={}, node="REPLACE_SHA256", gpu_uuid="GPU-REPLACE", driver_version="REPLACE",
                lease_end_unix=0, lease_cutoff_unix=0, approved_intake="REPLACE_MAIN_CLOSED_INTAKE",
                builder_preflight_reference="REPLACE_DATED_BUILDER_NOTE", requested_scope=SCOPE,
                numerical_policy=dict(vars(PRODUCTION_POLICY)))


def validate_native_config(config):
    require(set(config) == set(native_config_template()), "native configuration field allowlist")
    require(config["model"] == PUBLIC_MODEL and config["revision"] == PUBLIC_REVISION
            and config["requested_scope"] == SCOPE, "frozen root1 native model/scope")
    require_native_ready(config)
    for key in ("model_path", "tokenizer_path"):
        require(isinstance(config[key], str) and Path(config[key]).is_absolute(), "absolute local snapshot path")
    require(re.fullmatch(r"GPU-[0-9a-fA-F-]{36}", config["gpu_uuid"])
            and re.fullmatch(r"[0-9a-f]{64}", config["node"])
            and re.fullmatch(r"[0-9.]+", config["driver_version"]), "reserved A40 identity fields")
    for key in ("approved_intake", "builder_preflight_reference"):
        require(isinstance(config[key], str) and config[key] and "REPLACE" not in config[key], "explicit " + key)
    for key in ("lease_end_unix", "lease_cutoff_unix"):
        require(type(config[key]) in (int, float) and math.isfinite(config[key]) and config[key] > 0, "finite " + key)
    require(config["lease_cutoff_unix"] <= config["lease_end_unix"] - 21600, "shared lease six-hour buffer")


def native_input_pins(config, binding):
    diagnostic, _, _ = historical_helpers()
    validate_native_config(config)
    require(diagnostic.w0.environment_identity() == config["environment"], "native environment pins")
    inventories = {}
    cache = {}
    for kind in ("model", "tokenizer"):
        path = str(Path(config[kind + "_path"]).resolve(strict=True))
        if path not in cache:
            cache[path] = diagnostic.w0.snapshot_inventory(path)
        value = cache[path]
        require(not any("adapter" in Path(name).name.lower() for name, _ in value["files"]), "clean base files only")
        if binding is not None:
            expected = {name: item["sha256"] for name, item in binding["files"].items()}
            require(dict(value["files"]) == expected, "local files differ from Main's official model-only binding")
        inventories[kind] = value
    model_config = json.loads((Path(config["model_path"]) / "config.json").read_bytes())
    require(model_config.get("model_type") == "qwen2" and model_config.get("num_hidden_layers") == 28
            and model_config.get("hidden_size") == 3584, "Qwen2.5-7B architecture")
    return dict(inventories=inventories, environment=config["environment"], public_binding_sha256=(
        binding["receipt_sha256"] if binding is not None else None))


CPU_SUITES = ("tests.test_astra_pairwise_q0", "tests.test_semantic_objective_probe",
              "tests.test_semantic_writer_diagnostic", "tests.test_multikey_writer_gateway_simple",
              "tests.test_writer_interface_calibration", "tests.test_run_reasoning_neutral")


def validate_test_support(support):
    require(set(support) == {"provenance", "scope", "files"}
            and support["scope"] == "ARCHIVED_REGRESSION_SUPPORT_ONLY_NOT_Q0_INPUT"
            and isinstance(support["provenance"], str) and support["provenance"]
            and isinstance(support["files"], dict) and support["files"], "explicit historical test-support manifest")
    for name, expected in support["files"].items():
        relative = Path(name)
        require(not relative.is_absolute() and ".." not in relative.parts and relative.as_posix() == name
                and re.fullmatch(r"[0-9a-f]{64}", expected), "relative hash-pinned test support")
        path = repository() / relative
        require(path.resolve(strict=True).is_relative_to(repository()) and not path.is_symlink()
                and file_hash(path) == expected, "historical test-support drift: " + name)
    return support


def cpu_test_receipt(path, test_support):
    import unittest
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == "" and os.environ.get("HF_HUB_OFFLINE") == "1"
            and os.environ.get("TRANSFORMERS_OFFLINE") == "1", "CPU regression requires hidden CUDA and offline environment")
    support = validate_test_support(json.loads(Path(test_support).read_bytes()))
    before = native_source_pins()
    diagnostic, _, _ = historical_helpers()
    environment = diagnostic.w0.environment_identity()
    previous_path = list(sys.path)
    try:
        sys.path.insert(0, str(repository() / "tests"))
        suite = unittest.defaultTestLoader.loadTestsFromNames(CPU_SUITES)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    finally:
        sys.path[:] = previous_path
    require(before == native_source_pins() and environment == diagnostic.w0.environment_identity(), "source/environment changed during CPU tests")
    validate_test_support(support)
    receipt = dict(suites=list(CPU_SUITES), tests=result.testsRun, failures=len(result.failures),
                   errors=len(result.errors), skipped=len(result.skipped), successful=result.wasSuccessful(),
                   source_pins=before, environment=environment, python=sys.version, platform=sys.platform, timestamp=time.time(),
                   test_support=support, test_support_sha256=digest(support),
                   test_import_roots=[".", "tests"], evidence_kind="CPU_REGRESSION_ONLY", native_proof=False)
    write_once(Path(path).parent, Path(path).name, receipt)
    return receipt


def native_prepare(out, config, test_receipt):
    diagnostic, _, _ = historical_helpers()
    validate_native_config(config)
    require(not torch_module().cuda.is_initialized(), "preparation must be CPU-only")
    receipt = json.loads(Path(test_receipt).read_bytes())
    require(receipt["suites"] == list(CPU_SUITES) and receipt["successful"] is True
            and receipt["failures"] == receipt["errors"] == receipt["skipped"] == 0
            and receipt["source_pins"] == native_source_pins() and receipt["platform"] == "linux"
            and receipt["environment"] == config["environment"]
            and receipt["evidence_kind"] == "CPU_REGRESSION_ONLY", "bound complete Linux regression receipt")
    support = validate_test_support(receipt["test_support"])
    require(receipt["test_support_sha256"] == digest(support) and receipt["test_import_roots"] == [".", "tests"],
            "bound archived regression support/import roots")
    root = diagnostic.w0.checked_path(out)
    protected = [repository(), Path(config["model_path"]).resolve(), Path(config["tokenizer_path"]).resolve()]
    require(all(not root.is_relative_to(path) and not path.is_relative_to(root) for path in protected), "native output overlaps protected input")
    require(root.parent.is_dir() and not root.exists(), "fresh native preparation root")
    binding_path = config["public_binding_path"]
    binding = public_binding(binding_path) if binding_path is not None else None
    pins = native_input_pins(config, binding)
    tokenizer = diagnostic.w0.load_local_tokenizer(config)
    prepared = build_prepared(tokenizer, evidence_kind="NATIVE_TOKENIZER_ONLY", public_binding_path=binding_path)
    require(not torch_module().cuda.is_initialized(), "tokenizer preparation initialized CUDA")
    manifest = dict(version=VERSION, config=config, source_pins=native_source_pins(), inputs=pins,
                    prepared_sha256=digest(prepared), test_receipt=receipt,
                    numerical_policy=vars(PRODUCTION_POLICY), recipe=RECIPE, public_binding=binding,
                    original_capsule_sha256=ARCHIVE_SHA256, provenance_scope="MODEL_ONLY_NOT_CLEAN_ANCESTRY",
                    confirmation_allocation=None, formal_C11_guard="DEFERRED", ready=binding is not None)
    root.mkdir()
    for name, expected in manifest["source_pins"].items():
        destination = root / "source" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write((repository() / name).read_bytes())
        require(file_hash(destination) == expected, "archived source snapshot bytes")
    write_once(root, "prepared.json", prepared)
    write_once(root, "manifest.json", manifest)
    write_once(root, "PREPARED.json", dict(manifest_sha256=file_hash(root / "manifest.json"),
                                           prepared_sha256=file_hash(root / "prepared.json")))
    return manifest


def native_verify(root, *, check_files=True):
    diagnostic, _, _ = historical_helpers()
    root = diagnostic.w0.checked_path(root)
    manifest = json.loads((root / "manifest.json").read_bytes())
    seal = json.loads((root / "PREPARED.json").read_bytes())
    require(seal == dict(manifest_sha256=file_hash(root / "manifest.json"),
                         prepared_sha256=file_hash(root / "prepared.json")), "native preparation seal")
    require(manifest["source_pins"] == native_source_pins() and manifest["numerical_policy"] == vars(PRODUCTION_POLICY)
            and manifest["recipe"] == RECIPE, "native source/recipe/numerical-policy pins")
    require(all(file_hash(root / "source" / name) == expected for name, expected in manifest["source_pins"].items()),
            "archived source snapshot drift")
    config = manifest["config"]
    validate_native_config(config)
    if check_files:
        require(native_input_pins(config, manifest["public_binding"]) == manifest["inputs"], "native input drift")
    tokenizer = diagnostic.w0.load_local_tokenizer(config)
    prepared = json.loads((root / "prepared.json").read_bytes())
    validate_prepared(prepared, tokenizer)
    require(digest(prepared) == manifest["prepared_sha256"] and prepared["public_binding"] == manifest["public_binding"],
            "native material/provenance identity")
    return manifest, prepared, tokenizer


def audit_native_model(model, optimizer):
    torch = torch_module()
    diagnostic, _, _ = historical_helpers()
    named = diagnostic.w0.validate_trainables(model)
    require(len(named) == 392 and all(value.dtype == torch.float32 and value.device.type == "cuda" for _, value in named),
            "392 native FP32 LoRA tensors")
    config = model.peft_config["default"]
    require(config.r == 8 and config.lora_alpha == 16 and config.lora_dropout == .05 and config.bias == "none"
            and set(config.target_modules) == set(RECIPE["target_modules"]) and config.init_lora_weights is True,
            "closed native LoRA construction")
    require(all(torch.count_nonzero(value).item() == 0 for name, value in named if ".lora_B." in name), "fresh zero-B initialization")
    require(all(not parameter.requires_grad for name, parameter in model.named_parameters()
                if ".lora_A." not in name and ".lora_B." not in name), "frozen base weights")
    require(not getattr(model, "is_gradient_checkpointing", False)
            and torch.are_deterministic_algorithms_enabled()
            and not torch.backends.cuda.matmul.allow_tf32 and not torch.backends.cudnn.allow_tf32,
            "native determinism/no checkpointing/TF32")
    require(model.get_input_embeddings().weight.dtype == torch.bfloat16
            and model.config._attn_implementation == "eager", "BF16 base and eager attention")
    return audit_optimizer(model, optimizer)


def native_generate(model, tokenizer, row, *, max_new_tokens, do_sample):
    diagnostic, _, _ = historical_helpers()
    require(max_new_tokens == 32 and do_sample is False, "fixed greedy generation")
    request = dict(request_id=row["id"], prompt_input_ids=row["prompt_input_ids"], max_new_tokens=32)
    output = diagnostic.cal._generate(torch_module(), model, tokenizer, request)
    require(output.pop("request_id") == row["id"], "native generation identity")
    return output


def artifact_value(value):
    torch = torch_module()
    if isinstance(value, torch.Tensor):
        return tensor_payload(value)
    if isinstance(value, dict):
        return {key: artifact_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [artifact_value(item) for item in value]
    return value


def native_worker(root, stage, *, allow_gpu=False):
    require(allow_gpu is True, "worker requires explicit --allow-gpu")
    require(re.fullmatch(r"[0-9]{2}_[A-Za-z0-9_]+", stage), "registered stage name")
    root = Path(root)
    diagnostic, _, _ = historical_helpers()
    job = json.loads((root / "jobs" / (stage + ".json")).read_bytes())
    started = json.loads((root / "STARTED.json").read_bytes())
    require(job["started_sha256"] == file_hash(root / "STARTED.json")
            and job["manifest_sha256"] == file_hash(root / "manifest.json"), "native job binding")
    parent = diagnostic.carrier.process_identity(os.getppid())
    require(parent == job["controller"], "native worker requires registered live controller parent")
    require(job["deadline"] <= started["deadline"] - CLEANUP_RESERVE and time.time() < job["deadline"], "worker hard deadline")
    for name, expected in job["prior_receipts"].items():
        require(file_hash(root / "receipts" / name) == expected, "prior stage receipt drift")
    directory = root / "stages" / stage
    write_once(directory, "CLAIMED.json", dict(identity=diagnostic.carrier.process_identity(os.getpid()), timestamp=time.time()))
    manifest, prepared, tokenizer = native_verify(root)
    config, ticket = manifest["config"], job["ticket"]
    require(ticket["ticket_sha256"] == digest({key: value for key, value in ticket.items() if key != "ticket_sha256"})
            and ticket["evidence_kind"] == NATIVE_KIND and ticket["prepared_sha256"] == digest(prepared)
            and stage == native_stage_name(ticket) and ticket["sequence"] == len(job["prior_receipts"]), "native ticket identity/order")
    require(manifest["ready"] and config["gpu_uuid"] == os.environ.get("CUDA_VISIBLE_DEVICES"), "reserved prospective native run")
    hardware = diagnostic.w0.gpu_identity(config)
    diagnostic.w0.assert_gpu_idle(config)
    torch = diagnostic.w0.configure_torch(config, 1)
    budget = Budget(started["started"], job["deadline"], clock=time.time)
    budget.check()
    kind, arm, snapshot = ticket["kind"], ticket["arm"], ticket["snapshot"]
    optimizer = None
    if kind in ("audit", "fit"):
        model, optimizer, _ = diagnostic.fit_model(torch, config)
        audit_native_model(model, optimizer)
    else:
        model = diagnostic.w0.load_hf_model(config, torch)
        require(not diagnostic.w0.lora_tensors(model), "fresh evaluation base without historical adapter")
        if arm != "OFF":
            from peft import PeftModel
            binding = job["adapter"]
            path = root / binding["path"]
            require(re.fullmatch(r"stages/[0-9]{2}_fit_P_(?:AUTH|DERANGED|UNARY_TOOL)/snapshots/(?:32|64|128)|stages/[0-9]{2}_fit_V_AUTH/snapshots/(?:32|64|128)", binding["path"]),
                    "only this run's registered snapshot path")
            require(diagnostic.w0.tree_hash(path) == binding["adapter_sha256"], "saved snapshot bytes")
            model = PeftModel.from_pretrained(model, str(path), is_trainable=False, local_files_only=True)
            require(diagnostic.w0.tensor_digest(diagnostic.w0.lora_tensors(model)) == binding["lora_sha256"], "fresh snapshot LoRA reload")
        model.requires_grad_(False)
        model.eval()
    identity = diagnostic.carrier.process_identity(os.getpid())
    load = dict(identity=identity, ticket_sha256=ticket["ticket_sha256"], job_sha256=file_hash(root / "jobs" / (stage + ".json")),
                hardware=hardware, inputs=manifest["inputs"], source_pins=manifest["source_pins"],
                load_id=digest([stage, identity, time.time_ns()]), adapter=job.get("adapter"), loaded=time.time())
    write_once(directory, "LOAD.json", load)
    counts = Counter(natural_prefix_forwards=0, model_forward_calls=0)
    counter_token = _FORWARD_COUNTS.set(counts)

    def count_forward(*args):
        counts["model_forward_calls"] += 1

    forward_owner = model.get_base_model() if hasattr(model, "peft_config") else model
    hook = forward_owner.register_forward_pre_hook(count_forward)
    events = []
    event_directory = directory / "events"
    event_directory.mkdir()

    def emit(name, payload):
        budget.check()
        filename = f"{len(events):04d}_{name}.json"
        write_once(event_directory, filename, artifact_value(payload))
        events.append(dict(path=filename, sha256=file_hash(event_directory / filename)))

    def save_snapshot(update, current):
        path = directory / "snapshots" / str(update)
        path.parent.mkdir(exist_ok=True)
        path.mkdir()
        current.save_pretrained(str(path), safe_serialization=True)
        return dict(path=path.relative_to(root).as_posix(), adapter_sha256=diagnostic.w0.tree_hash(path),
                    lora_sha256=diagnostic.w0.tensor_digest(diagnostic.w0.lora_tensors(current)))

    try:
        with tensor_store(root, writable=True):
            if kind == "audit":
                result = objective_audit(model, optimizer, prepared, PRODUCTION_POLICY, budget)
            elif kind == "fit":
                audit = json.loads((root / job["audit_result"]).read_bytes())["result"]
                result = train_fit(model, optimizer, prepared, arm, audit["initial"], PRODUCTION_POLICY,
                                   budget, emit, save_snapshot, diagnostic_only=ticket["diagnostic_only"])
            else:
                result = evaluate(model, prepared, arm, snapshot, tokenizer, native_generate, budget, emit)
        budget.check()
        require(native_source_pins() == manifest["source_pins"], "source changed during worker")
        write_once(directory, "DONE.json", dict(result=result, load=load, events=events, counters=dict(counts),
                                                finished=time.time(), evidence_kind=NATIVE_KIND))
    finally:
        hook.remove()
        _FORWARD_COUNTS.reset(counter_token)


def native_stage_name(ticket):
    parts = [f"{ticket['sequence']:02d}", ticket["kind"]]
    if ticket["arm"] is not None:
        parts.append(ticket["arm"])
    if ticket["snapshot"] is not None:
        parts.append(str(ticket["snapshot"]))
    return "_".join(parts)


@contextmanager
def controller_termination():
    def interrupted(signum, frame):
        raise InterruptedError("controller termination signal " + str(signum))

    previous = {signum: signal.getsignal(signum) for signum in (signal.SIGTERM, signal.SIGHUP)}
    try:
        for signum in previous:
            signal.signal(signum, interrupted)
        yield
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


def native_execute(root, *, allow_gpu=False):
    start, mono_start = time.time(), time.monotonic()
    require(allow_gpu is True, "execute requires explicit --allow-gpu")
    with controller_termination():
        return _native_execute(root, start, mono_start)


def _native_execute(root, start, mono_start):
    diagnostic, supervisor, _ = historical_helpers()
    root = diagnostic.w0.checked_path(root)
    initial_manifest = json.loads((root / "manifest.json").read_bytes())
    expected_files = {"prepared.json", "manifest.json", "PREPARED.json"} | {
        "source/" + name for name in initial_manifest["source_pins"]}
    require(set(inventory(root)) == expected_files, "fresh prepared run; no retry/resume")
    diagnostic.w0.assert_output_fds_outside_run(root)
    config = initial_manifest["config"]
    deadline = min(start + MAX_SECONDS, config["lease_cutoff_unix"])
    controller = diagnostic.carrier.process_identity(os.getpid())
    write_once(root, "STARTED.json", dict(started=start, deadline=deadline, controller=controller,
                                          manifest_sha256=file_hash(root / "manifest.json")))
    for name in ("jobs", "logs", "stages", "receipts"):
        (root / name).mkdir()
    receipt_pins, stages = {}, []
    failures = []
    prepared = tokenizer = None

    def record_failure(error):
        failures.append(dict(error_type=type(error).__name__, reason=str(error), timestamp=time.time(), preserve_partial=True))

    try:
        budget = Budget(start, config["lease_cutoff_unix"], clock=time.time)
        manifest, prepared, tokenizer = native_verify(root)
        require(manifest["ready"], "prospective public binding required for native execution")
        require(os.environ.get("CUDA_VISIBLE_DEVICES") == config["gpu_uuid"]
                and os.environ.get("CUBLAS_WORKSPACE_CONFIG") == ":4096:8", "Main must bind reserved GPU/determinism environment")
        budget.check()
        require(MAX_SECONDS - (time.monotonic() - mono_start) > CLEANUP_RESERVE + 5
                and deadline - time.time() > CLEANUP_RESERVE + 5, "insufficient root reservation")
        diagnostic.w0.gpu_identity(config)
        diagnostic.w0.assert_gpu_idle(config)
        lifecycle = Lifecycle(prepared, tokenizer, PRODUCTION_POLICY, budget, evidence_kind=NATIVE_KIND)
        with tensor_store(root):
            while (ticket := lifecycle.issue()) is not None:
                stage = native_stage_name(ticket)
                remaining = min(budget.deadline - time.time(), MAX_SECONDS - (time.monotonic() - mono_start)) - CLEANUP_RESERVE
                require(remaining > 5, "root deadline before fresh worker")
                job = dict(ticket=ticket, deadline=min(budget.deadline - CLEANUP_RESERVE, time.time() + remaining), controller=controller,
                           started_sha256=file_hash(root / "STARTED.json"),
                           manifest_sha256=file_hash(root / "manifest.json"), prior_receipts=dict(receipt_pins))
                if ticket["kind"] == "fit":
                    job["audit_result"] = "stages/00_audit/DONE.json"
                if ticket["kind"] == "eval" and ticket["arm"] != "OFF":
                    fit = next(fit for fit in lifecycle.evidence["fits"] if fit["arm"] == ticket["arm"])
                    job["adapter"] = fit["snapshots"][str(ticket["snapshot"])]
                write_once(root / "jobs", stage + ".json", job)
                (root / "stages" / stage).mkdir()
                command = [sys.executable, "-B", "-m", "gpu.astra_pairwise_q0", "worker", "--out", str(root),
                           "--stage", stage, "--allow-gpu"]
                begin = time.time()
                pid = supervisor.run_worker(command, log_path=root / "logs" / (stage + ".log"),
                                            timeout=job["deadline"] - time.time(), device=config["gpu_uuid"])
                done = json.loads((root / "stages" / stage / "DONE.json").read_bytes())
                cleanup = json.loads((root / "logs" / (stage + ".cleanup.json")).read_bytes())
                require(cleanup["owned_group_empty"] and cleanup["gpu_processes_absent"]
                        and cleanup["reservation_release_verified"], "native owned-group/GPU cleanup")
                receipt = dict(ticket_sha256=ticket["ticket_sha256"], attempts=1, evidence_kind=NATIVE_KIND,
                               pid=pid, process_start=done["load"]["identity"]["start_ticks"], load_id=done["load"]["load_id"],
                               start=begin, finish=time.time(), status="FINISHED", cleanup="COMPLETE", command=command,
                               done_sha256=file_hash(root / "stages" / stage / "DONE.json"),
                               log_sha256=file_hash(root / "logs" / (stage + ".log")),
                               cleanup_sha256=file_hash(root / "logs" / (stage + ".cleanup.json")), adapter=job.get("adapter"))
                require(done["load"]["identity"]["pid"] == pid, "fresh worker PID/load binding")
                lifecycle.accept(ticket, done["result"], receipt)
                write_once(root / "receipts", stage + ".json", receipt)
                receipt_pins[stage + ".json"] = file_hash(root / "receipts" / (stage + ".json"))
                stages.append(stage)
            budget.check()
            report = lifecycle.report()
            require(report["label"] not in ("NONREPORTABLE_PRECHECK_ABORT", "NONREPORTABLE_RUNTIME_ABORT"),
                    "native raw reducer aborted: " + report.get("reason", "unknown"))
    except BaseException as error:
        record_failure(error)
    released = False
    try:
        released = supervisor.gpu_processes_absent(config["gpu_uuid"])
        require(released, "final GPU release not verified")
    except BaseException as error:
        record_failure(error)
    elapsed = time.monotonic() - mono_start
    if elapsed >= MAX_SECONDS or time.time() >= deadline:
        record_failure(IntegrityError("final cleanup/root deadline"))
    resource = dict(stages=stages, started=start, finished=time.time(), elapsed_seconds=elapsed,
                    deadline=deadline, selected_gpu=config["gpu_uuid"], gpu_release_verified=released,
                    fit_cap=3, seconds_cap=2700, formal_C11_guard="DEFERRED")
    if not failures:
        try:
            with tensor_store(root):
                report = native_reduce(root, prepared, tokenizer, resource=resource)
        except BaseException as error:
            record_failure(error)
    if failures:
        write_once(root, "FAILED.json", dict(failures=failures, preserve_partial=True))
        report = native_abort(root, resource)
    resource.update(finished=time.time(), elapsed_seconds=time.monotonic() - mono_start,
                    replay_is_read_only_post_terminal=True)
    if resource["finished"] >= deadline or resource["elapsed_seconds"] >= MAX_SECONDS:
        report = native_abort(root, resource)
    report["resource"] = resource
    write_once(root, "RESOURCE.json", resource)
    write_once(root, "reduction.json", provisional_reduction(report))
    sealed_files = durable_inventory(root)
    write_once(root, "SEAL.json", dict(version=VERSION, evidence_kind=NATIVE_KIND, files=sealed_files,
                                       classification="PENDING_DURABLE_FINALIZATION"))
    sync_directory(root)
    seal_hash = file_hash(root / "SEAL.json")
    write_once(root, "FINALIZED.json", dict(seal_sha256=seal_hash, evidence_durable_unix=time.time(),
                                           elapsed_seconds=time.monotonic() - mono_start,
                                           witness="post-fsync evidence completion; publication metadata only"))
    sync_directory(root)
    if time.time() >= deadline or time.monotonic() - mono_start >= MAX_SECONDS:
        write_once(root, "FINALIZATION_ABORT.json", dict(seal_sha256=seal_hash,
                   finalized_sha256=file_hash(root / "FINALIZED.json"), reason="terminal publication deadline",
                   observed_unix=time.time(), elapsed_seconds=time.monotonic() - mono_start))
        sync_directory(root)
    replayed = native_replay(root)
    return replayed


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def durable_inventory(root):
    files = inventory(root)
    for name in files:
        with (Path(root) / name).open("rb") as stream:
            os.fsync(stream.fileno())
    directories = [Path(root)] + [path for path in Path(root).rglob("*") if path.is_dir()]
    for path in sorted(directories, key=lambda item: len(item.parts), reverse=True):
        sync_directory(path)
    return files


def native_abort(root, resource, *, reason=None):
    failure_path = Path(root) / "FAILED.json"
    failures = json.loads(failure_path.read_bytes()) if failure_path.exists() else None
    return dict(label="NONREPORTABLE_RUNTIME_ABORT" if resource["stages"] else "NONREPORTABLE_PRECHECK_ABORT",
                evidence_kind=NATIVE_KIND, scientific_claim=False, resource=resource,
                partial_stages_preserved=resource["stages"], counters={},
                counters_status="UNVALIDATED_PARTIAL_EVIDENCE_NOT_SCIENTIFIC_COUNTS",
                failures=failures, reason=reason or "integrity, release or root deadline abort")


def provisional_reduction(report):
    result = dict(report)
    eligible = result.pop("scientific_claim")
    return dict(candidate=result, eligible_before_finalization=eligible, scientific_claim=False,
                classification="CANDIDATE_ONLY_NOT_A_TERMINAL_CLAIM")


def native_reduce(root, prepared, tokenizer, *, resource=None):
    root = Path(root)
    started = json.loads((root / "STARTED.json").read_bytes())
    resource = json.loads((root / "RESOURCE.json").read_bytes()) if resource is None else resource
    require(resource["deadline"] == started["deadline"] <= started["started"] + MAX_SECONDS, "native root budget binding")
    if ((root / "FAILED.json").exists() or not resource["gpu_release_verified"]
            or resource["elapsed_seconds"] >= MAX_SECONDS or resource["finished"] >= resource["deadline"]):
        return native_abort(root, resource)
    clock = [started["started"]]
    lifecycle = Lifecycle(prepared, tokenizer, PRODUCTION_POLICY,
                          Budget(started["started"], started["deadline"], clock=lambda: clock[0]), evidence_kind=NATIVE_KIND)
    totals = Counter()
    for stage in resource["stages"]:
        job = json.loads((root / "jobs" / (stage + ".json")).read_bytes())
        receipt = json.loads((root / "receipts" / (stage + ".json")).read_bytes())
        done = json.loads((root / "stages" / stage / "DONE.json").read_bytes())
        cleanup = json.loads((root / "logs" / (stage + ".cleanup.json")).read_bytes())
        ticket = lifecycle.issue()
        require(ticket == job["ticket"] and stage == native_stage_name(ticket), "replayed dynamic stage path")
        require(job["started_sha256"] == file_hash(root / "STARTED.json")
                and job["manifest_sha256"] == file_hash(root / "manifest.json")
                and done["load"]["job_sha256"] == file_hash(root / "jobs" / (stage + ".json"))
                and done["load"]["ticket_sha256"] == ticket["ticket_sha256"], "native job/load source binding")
        require(receipt["done_sha256"] == file_hash(root / "stages" / stage / "DONE.json")
                and receipt["cleanup_sha256"] == file_hash(root / "logs" / (stage + ".cleanup.json"))
                and receipt["log_sha256"] == file_hash(root / "logs" / (stage + ".log")), "native stage evidence hashes")
        require(cleanup["pid"] == receipt["pid"] == done["load"]["identity"]["pid"]
                and cleanup["owned_group_empty"] and cleanup["gpu_processes_absent"]
                and cleanup["reservation_release_verified"] and done["finished"] <= receipt["finish"]
                and done["finished"] < job["deadline"] and cleanup["device"] == resource["selected_gpu"],
                "native cleanup and load identity")
        events = []
        for event in done["events"]:
            require(Path(event["path"]).name == event["path"]
                    and file_hash(root / "stages" / stage / "events" / event["path"]) == event["sha256"], "raw event inventory")
            events.append((event["path"], json.loads((root / "stages" / stage / "events" / event["path"]).read_bytes())))
        if ticket["kind"] == "fit":
            result = done["result"]
            require([value for name, value in events if name.endswith("_step.json")] == result["steps"], "raw ordered fit steps")
            require([value for name, value in events if name.endswith("_initial.json")] == [result["initial"]], "raw initialization event")
            after_events = [value for name, value in events if name.endswith("_canary_after.json")]
            require(len(after_events) == 1 and after_events[0]["result"] == result["canary"]
                    and after_events[0]["delta"] == result["canary_raw"]["delta"], "raw first-update event")
            diagnostic, _, _ = historical_helpers()
            for binding in result["snapshots"].values():
                require(Path(binding["path"]).is_relative_to("stages") and ".." not in Path(binding["path"]).parts
                        and diagnostic.w0.tree_hash(root / binding["path"]) == binding["adapter_sha256"], "sealed snapshot artifact")
        elif ticket["kind"] == "eval":
            require([value for name, value in events if name.endswith("_readout.json")] == done["result"], "raw evaluation events")
            require(done["load"]["adapter"] == job.get("adapter") == receipt["adapter"], "native reload adapter binding")
        if ticket["kind"] == "audit":
            expected_prefix, expected_calls = 128, 128
        elif ticket["kind"] == "fit":
            expected_prefix = 128 + 4 * done["result"]["updates"] + 16
            expected_calls = expected_prefix
        else:
            expected_prefix = sum(record["operation"] == "prefix" for record in done["result"])
            expected_calls = expected_prefix + sum(len(record["output"]["generated_ids"]) for record in done["result"]
                                                   if record["operation"] == "generate")
        require(done["counters"] == dict(natural_prefix_forwards=expected_prefix, model_forward_calls=expected_calls),
                "exact native forward/token work accounting")
        clock[0] = receipt["finish"]
        lifecycle.accept(ticket, done["result"], receipt)
        totals.update(done["counters"])
    require(resource["finished"] < resource["deadline"] and lifecycle.issue() is None, "complete timely native lifecycle")
    report = lifecycle.report()
    require(not report["label"].startswith("NONREPORTABLE"), "native reducer integrity failure")
    generations = [record for records in lifecycle.evidence["readouts"].values() for record in records if record["operation"] == "generate"]
    report.update(evidence_kind=NATIVE_KIND, scientific_claim=True, native_launch_ready=False,
                  claim_scope="one supervised synthetic root1 recipe only; not clean ancestry/H1/H2/retention/robustness",
                  generated_tokens=sum(len(record["output"]["generated_ids"]) for record in generations),
                  counters=dict(totals), resource=resource, numerical_policy=vars(PRODUCTION_POLICY))
    return report


def native_replay(root):
    root = Path(root)
    seal = json.loads((root / "SEAL.json").read_bytes())
    require(seal["version"] == VERSION and seal["evidence_kind"] == NATIVE_KIND, "native terminal seal")
    require({name: value for name, value in inventory(root).items()
             if name not in ("SEAL.json", "FINALIZED.json", "FINALIZATION_ABORT.json")} == seal["files"],
            "native immutable inventory")
    require(seal["classification"] == "PENDING_DURABLE_FINALIZATION", "evidence seal is not a scientific claim")
    manifest = json.loads((root / "manifest.json").read_bytes())
    started = json.loads((root / "STARTED.json").read_bytes())
    require(started["deadline"] == min(started["started"] + MAX_SECONDS, manifest["config"]["lease_cutoff_unix"]),
            "root deadline/lease reconstruction")
    resource = json.loads((root / "RESOURCE.json").read_bytes())
    if ((root / "FAILED.json").exists() or not resource["gpu_release_verified"]
            or resource["elapsed_seconds"] >= MAX_SECONDS or resource["finished"] >= resource["deadline"]):
        report = native_reduce(root, None, None)
    else:
        manifest, prepared, tokenizer = native_verify(root)
        with tensor_store(root):
            report = native_reduce(root, prepared, tokenizer)
    require(canonical(provisional_reduction(report)) == (root / "reduction.json").read_bytes(), "native exact reduction replay")
    completion_path = root / "FINALIZED.json"
    if completion_path.exists():
        completion = json.loads(completion_path.read_bytes())
        require(completion["seal_sha256"] == file_hash(root / "SEAL.json"), "durable completion seal binding")
        require(math.isfinite(completion["evidence_durable_unix"]) and math.isfinite(completion["elapsed_seconds"])
                and completion["evidence_durable_unix"] >= resource["finished"]
                and completion["elapsed_seconds"] >= resource["elapsed_seconds"], "durable completion clock ordering")
        if completion["evidence_durable_unix"] >= started["deadline"] or completion["elapsed_seconds"] >= MAX_SECONDS:
            report = native_abort(root, resource, reason="terminal durable evidence deadline")
        report["durable_completion"] = completion
    else:
        report = native_abort(root, resource, reason="missing durable evidence completion witness")
    if (root / "FINALIZATION_ABORT.json").exists():
        publication = json.loads((root / "FINALIZATION_ABORT.json").read_bytes())
        require(publication["seal_sha256"] == file_hash(root / "SEAL.json")
                and publication["finalized_sha256"] == file_hash(completion_path), "late publication evidence binding")
        require(publication["observed_unix"] >= started["deadline"] or publication["elapsed_seconds"] >= MAX_SECONDS,
                "late publication deadline reconstruction")
        report = native_abort(root, resource, reason="terminal publication deadline")
        report.update(durable_completion=completion, late_publication=publication)
    return dict(report=report, report_sha256=digest(report), replay="EXACT_NATIVE_RAW_REPLAY")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("contract", "material", "native-readiness", "config-template", "cpu-tests",
                                           "prepare", "execute", "worker", "replay"))
    parser.add_argument("--out")
    parser.add_argument("--config")
    parser.add_argument("--test-receipt")
    parser.add_argument("--test-support")
    parser.add_argument("--stage")
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "contract":
        result = contract_manifest()
    elif args.command == "material":
        material = read_original_capsule()
        result = dict(capsule_sha256=ARCHIVE_SHA256, material_sha256=ARCHIVE_PINS["material.json"],
                      root=ROOT, orientation=list(ORIENTATION), panels=dict(Counter(row["panel"] for row in source_rows(material))),
                      scientific_claim=False, model_loaded=False, tokenizer_loaded=False)
    elif args.command == "config-template":
        result = native_config_template()
    elif args.command == "cpu-tests":
        require(args.out and args.test_support, "--out receipt file and --test-support archived manifest required")
        result = cpu_test_receipt(args.out, args.test_support)
    elif args.command == "prepare":
        require(args.out and args.config and args.test_receipt, "--out --config --test-receipt required")
        result = native_prepare(args.out, json.loads(Path(args.config).read_bytes()), args.test_receipt)
    elif args.command == "execute":
        result = native_execute(args.out, allow_gpu=args.allow_gpu)
    elif args.command == "worker":
        result = native_worker(args.out, args.stage, allow_gpu=args.allow_gpu)
    elif args.command == "replay":
        result = native_replay(args.out)
    else:
        result = dict(native_launch_ready=False, requirements="prepare and CPU/native review, then explicit Main launch",
                      confirmation_gap=list(UNRESOLVED), numerical_policy=vars(PRODUCTION_POLICY))
    print(canonical(result).decode(), end="")
    return 2 if args.command == "native-readiness" else 0


if __name__ == "__main__":
    raise SystemExit(main())

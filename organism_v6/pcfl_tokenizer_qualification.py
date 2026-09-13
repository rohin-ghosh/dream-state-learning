"""Deterministic offline qualification against a caller-supplied PCFL registry.

No tokenizer loading, world construction, template inference, or native release.
The encoder returns actual token IDs for each exact supplied text, without added
special tokens or truncation. Full training text must already include template
and EOS bytes. Receipt replay verifies the search, not the encoder's provenance.
"""

import base64
from dataclasses import dataclass
import hashlib
import json
import re


SCHEMA = "pcfl.opaque_qualification.v1"
ROOTS = tuple(f"excluded/{index}" for index in range(4)) + ("disposable/0", "dev/0", "dev/1")
PREFIXES = {"node": "N", "port": "P", "event": "E", "link": "L", "probe": "Q", "receipt": "R", "goal": "G"}
KINDS = ("grammar_row", "query", "event_twin", "link_permute", "collision_render", "reachout_order")
SOURCE_PINS = {
    "2026-09-13_pcfl_distractor_and_opaque_id_production_bindings.md": "bcdae11f3eb5c0653b842f16bbf5ba1e34cc5ffdbdc62689aca1ce2ca0f6eecf",
    "2026-09-13_pcfl_vertical_dev_v2_prospective_binding_register.md": "5d7920ea8e515794c57d19a9bd0d4793c835848727266aa0cb41ed729e5abadd",
    "2026-09-13_pcfl_vertical_dev_v2_2_writer_repair.md": "683fcba7762b69f408e5371cd9525e62c7ba6c8aa25494542f3041fec275dfca",
}
ENCODING_POLICY = "preformatted_text_no_added_special_tokens_no_truncation"


@dataclass(frozen=True)
class _Limits:
    pool_size: int = 4096
    salt_limit: int = 1000000
    lengths: tuple = tuple(range(4, 13))

    def wire(self):
        return {"pool_size": self.pool_size, "salt_limit": self.salt_limit, "lengths": list(self.lengths)}


PRODUCTION_LIMITS = _Limits()


class QualificationError(ValueError):
    """Missing, malformed, or drifted qualification input/evidence."""


class _EncodingFailure(Exception):
    pass


def _require(condition, message):
    if not condition:
        raise QualificationError(message)


def _record(value, fields, label):
    _require(type(value) is dict and set(value) == set(fields), f"{label}: missing/unknown fields")


def _name(value):
    _require(type(value) is str and re.fullmatch(r"[A-Za-z0-9_./:-]+", value) is not None, "invalid structural name")


def _hash(value):
    _require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None, "invalid SHA-256")


def canonical(value):
    def check(item):
        if item is None or type(item) in (str, int, bool):
            return
        if type(item) is list:
            for child in item:
                check(child)
            return
        if type(item) is dict and all(type(key) is str for key in item):
            for child in item.values():
                check(child)
            return
        raise QualificationError("closed JSON types required")
    check(value)
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    except UnicodeError as error:
        raise QualificationError("invalid UTF-8 wire text") from error


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def seed(label):
    _require(type(label) is str and label.isascii(), "ASCII seed label required")
    return int.from_bytes(hashlib.sha256(b"PCFL-V2.1-PREP\0" + label.encode("ascii")).digest()[:8], "big") & ((1 << 63) - 1)


def opaque_candidate(root, namespace, index, salt):
    _require(type(root) is str and type(namespace) is str and root in ROOTS and namespace in PREFIXES, "unknown root/namespace")
    _require(type(index) is int and index >= 0, "nonnegative structural index required")
    _require(type(salt) is int and 0 <= salt < 1000000, "salt outside 0..999999")
    payload = (seed("opaque/" + root).to_bytes(8, "big") + b"\0" + namespace.encode("ascii")
               + b"\0" + str(index).encode("ascii") + b"\0" + str(salt).encode("ascii"))
    return PREFIXES[namespace] + "_" + base64.b32encode(hashlib.sha256(payload).digest()).decode("ascii")[:10]


def validate_identifier(value, namespace):
    _require(type(namespace) is str and namespace in PREFIXES, "unknown identifier namespace")
    _require(type(value) is str and re.fullmatch(PREFIXES[namespace] + r"_[A-Z2-7]{10}", value) is not None, "wrong namespace/width/alphabet")
    return True


def _validate_bindings(bindings, tokenizer_pins, synthetic):
    _record(bindings, ("schema", "source_pins", "tokenizer_pins", "root_slots", "reserved_literals", "substitutions", "training_sequences", "required_training_ids", "render_registry_sha256"), "bindings")
    _require(bindings["schema"] == SCHEMA and bindings["source_pins"] == SOURCE_PINS, "schema/source-pin drift")
    _hash(bindings["render_registry_sha256"])
    _record(tokenizer_pins, ("revision", "files", "chat_template_sha256", "encoding_policy"), "tokenizer pins")
    _require(bindings["tokenizer_pins"] == tokenizer_pins, "tokenizer revision/files/template/policy drift")
    _require(type(tokenizer_pins["revision"]) is str and bool(tokenizer_pins["revision"]), "tokenizer revision required")
    _hash(tokenizer_pins["chat_template_sha256"])
    _require(tokenizer_pins["encoding_policy"] == ENCODING_POLICY, "no truncation or automatic specials permitted")
    _require(type(tokenizer_pins["files"]) is dict and bool(tokenizer_pins["files"]), "tokenizer file hashes required")
    for filename, file_hash in tokenizer_pins["files"].items():
        _require(type(filename) is str and bool(filename), "tokenizer filename")
        _hash(file_hash)
    root_slots = bindings["root_slots"]
    _require(type(root_slots) is list and bool(root_slots), "root/slot manifest required")
    roots, slots = [], []
    for root in root_slots:
        _record(root, ("root", "namespaces"), "root slots")
        _require(root["root"] in ROOTS, "unknown root label")
        roots.append(root["root"])
        _require(type(root["namespaces"]) is dict and bool(root["namespaces"]), "namespace slots required")
        _require(set(root["namespaces"]) <= set(PREFIXES) if synthetic else set(root["namespaces"]) == set(PREFIXES), "missing/unknown namespace")
        for namespace in PREFIXES:
            if namespace not in root["namespaces"]:
                continue
            names = root["namespaces"][namespace]
            _require(type(names) is list and bool(names) and len(names) == len(set(names)), "missing/duplicate structural slots")
            for index, name in enumerate(names):
                _name(name)
                slots.append((root["root"], namespace, name, index))
    _require(roots == [root for root in ROOTS if root in roots] and (synthetic or roots == list(ROOTS)), "missing/duplicate/out-of-order roots")
    reserved = bindings["reserved_literals"]
    _record(reserved, ("prompt_keywords", "canary_ids", "parser_prefixes", "other"), "reserved literals")
    for category, literals in reserved.items():
        _require(type(literals) is list and (bool(literals) or category == "other"), "missing reserved literal category")
        _require(all(type(value) is str and bool(value) for value in literals) and len(literals) == len(set(literals)), "invalid/duplicate reserved literal")
    slot_keys = {slot[:3] for slot in slots}
    covered, member_ids = set(), set()
    def member(row):
        _record(row, ("id", "parts"), "render member")
        _name(row["id"])
        _require(row["id"] not in member_ids, "duplicate member/sequence id")
        member_ids.add(row["id"])
        _require(type(row["parts"]) is list and bool(row["parts"]), "missing render parts")
        dependencies = set()
        for part in row["parts"]:
            _require(type(part) is dict and len(part) == 1, "one literal or slot per part")
            if "literal" in part:
                _require(type(part["literal"]) is str, "literal must be text")
                _require(re.search(r"\{[A-Z_]+\}", part["literal"]) is None, "unresolved template placeholder")
                _require(re.search(r"\bPAD_S[12]_", part["literal"]) is None, "obsolete loss-active PAD render")
            else:
                _record(part, ("slot",), "slot reference")
                _require(type(part["slot"]) is list and len(part["slot"]) == 3 and all(type(value) is str for value in part["slot"]), "slot reference [root, namespace, name]")
                reference = tuple(part["slot"])
                _require(reference in slot_keys, "unknown/unbound slot reference")
                dependencies.add(reference)
        covered.update(dependencies)
        return dependencies
    substitutions = bindings["substitutions"]
    _record(substitutions, ("required", "classes"), "substitution registry")
    _record(substitutions["required"], KINDS, "required substitution kinds")
    required = {}
    for kind, names in substitutions["required"].items():
        _require(type(names) is list and bool(names), "missing required substitution class")
        for name in names:
            _name(name)
            _require(name not in required, "duplicate required class")
            required[name] = kind
    _require(type(substitutions["classes"]) is list, "substitution classes must be a list")
    checks, found = [], set()
    for group in substitutions["classes"]:
        _record(group, ("id", "kind", "members"), "substitution class")
        _require(group["id"] in required and group["id"] not in found and group["kind"] == required[group["id"]], "unknown/duplicate/wrong-kind substitution class")
        found.add(group["id"])
        _require(type(group["members"]) is list and len(group["members"]) >= 2, "substitution class requires at least two mates")
        dependencies = set().union(*(member(row) for row in group["members"]))
        checks.append(("substitution", group["id"], group["members"], dependencies))
    _require(found == set(required), "missing required substitution class")
    _require(covered == slot_keys, "missing substitution coverage for required slots")
    training = bindings["training_sequences"]
    required_training = bindings["required_training_ids"]
    _require(type(required_training) is list and bool(required_training) and len(required_training) == len(set(required_training)), "required training sequence IDs")
    _require(type(training) is list and [row["id"] for row in training] == required_training, "missing/reordered/extra complete training sequences")
    for row in training:
        dependencies = member(row)
        checks.append(("training", row["id"], [row], dependencies))
    _require(covered == slot_keys, "missing substitution/render coverage for required slots")
    return slots, checks


class _Recorder:
    def __init__(self, encode, bindings_hash, pins_hash, run_hash, sink):
        self.encode = encode
        self.bindings_hash = bindings_hash
        self.pins_hash = pins_hash
        self.run_hash = run_hash
        self.sink = sink
        self.records = [] if sink is None else None
        self.count = 0
        self.head = "0" * 64

    def measure(self, text, context):
        error, tokens = None, None
        try:
            observed = self.encode(text)
            _require(type(observed) is list and bool(observed) and all(type(token) is int and token >= 0 for token in observed), "encoder must return a nonempty list of nonnegative integer token IDs")
            tokens = observed[:]
        except Exception as failure:
            error = type(failure).__name__ + ": " + str(failure)
        record = {"index": self.count, "previous_sha256": self.head, "bindings_sha256": self.bindings_hash,
                  "tokenizer_sha256": self.pins_hash, "run_sha256": self.run_hash, "context": context,
                  "text": text, "token_ids": tokens, "error": error}
        record["sha256"] = digest(record)
        self.head, self.count = record["sha256"], self.count + 1
        if self.sink is None:
            self.records.append(record)
        else:
            try:
                self.sink(json.loads(canonical(record)))
            except Exception as failure:
                raise QualificationError("receipt sink failed; search aborted without retry") from failure
        if error is not None:
            raise _EncodingFailure(error)
        return len(tokens), record["sha256"]


def _reserved(candidate, literals):
    for category, values in literals.items():
        for value in values:
            if candidate in value or (category != "parser_prefixes" and value in candidate):
                return True
    return False


def _pool(slot, length, limits, literals, recorder):
    root, namespace, name, index = slot
    pool, seen = [], set()
    for salt in range(limits.salt_limit):
        candidate = opaque_candidate(root, namespace, index, salt)
        count, receipt_hash = recorder.measure(candidate, {"kind": "candidate", "root": root, "namespace": namespace, "slot": name, "structural_index": index, "salt": salt, "length": length})
        if count == length and candidate not in seen and not _reserved(candidate, literals):
            pool.append({"value": candidate, "salt": salt, "receipt_sha256": receipt_hash})
            seen.add(candidate)
            if len(pool) == limits.pool_size:
                return pool
    return None


def _render(member, assignment):
    return "".join(part["literal"] if "literal" in part else assignment[tuple(part["slot"])]["value"] for part in member["parts"])


def _check(check, assignment, recorder):
    kind, name, members, _ = check
    observations = []
    for member in members:
        text = _render(member, assignment)
        count, receipt_hash = recorder.measure(text, {"kind": kind, "class_or_sequence": name, "member": member["id"]})
        observations.append({"member": member["id"], "token_count": count, "receipt_sha256": receipt_hash})
    valid = len({entry["token_count"] for entry in observations}) == 1 if kind == "substitution" else all(entry["token_count"] < 512 for entry in observations)
    return valid, {"kind": kind, "id": name, "members": observations}


def _search(slots, pools, checks, recorder, constant_results):
    indices = {slot[:3]: index for index, slot in enumerate(slots)}
    by_depth = {index: [] for index in range(len(slots))}
    for check in checks:
        if check[3]:
            by_depth[max(indices[reference] for reference in check[3])].append(check)
    cursor, assignment, accepted = 0, {}, dict(constant_results)
    next_candidate = [0] * len(slots)
    while cursor >= 0:
        if cursor == len(slots):
            return assignment, [accepted[(check[0], check[1])] for check in checks]
        key = slots[cursor][:3]
        if next_candidate[cursor] == len(pools[cursor]):
            next_candidate[cursor] = 0
            cursor -= 1
            if cursor >= 0:
                assignment.pop(slots[cursor][:3])
            continue
        candidate = pools[cursor][next_candidate[cursor]]
        next_candidate[cursor] += 1
        if any(candidate["value"] in previous["value"] or previous["value"] in candidate["value"] for previous in assignment.values()):
            continue
        assignment[key] = candidate
        valid = True
        for check in by_depth[cursor]:
            passed, observation = _check(check, assignment, recorder)
            if not passed:
                valid = False
                break
            accepted[(check[0], check[1])] = observation
        if valid:
            cursor += 1
        else:
            assignment.pop(key)
    return None, []


def _qualify(bindings, encode, tokenizer_pins, limits, synthetic, receipt_sink=None):
    _require(callable(encode) and (receipt_sink is None or callable(receipt_sink)), "offline encoder/receipt sink must be callable")
    _require(type(synthetic) is bool and type(limits) is _Limits, "internal search mode")
    _require(type(limits.pool_size) is int and 1 <= limits.pool_size <= 4096 and type(limits.salt_limit) is int and 1 <= limits.salt_limit <= 1000000, "invalid bounded search limits")
    _require(type(limits.lengths) is tuple and bool(limits.lengths) and all(type(length) is int and 4 <= length <= 12 for length in limits.lengths) and list(limits.lengths) == sorted(set(limits.lengths)), "invalid length order")
    _require(synthetic or limits == PRODUCTION_LIMITS, "production limits cannot be weakened")
    bindings, tokenizer_pins = json.loads(canonical(bindings)), json.loads(canonical(tokenizer_pins))
    try:
        slots, checks = _validate_bindings(bindings, tokenizer_pins, synthetic)
    except (KeyError, TypeError, IndexError) as error:
        raise QualificationError("malformed required registry") from error
    binding_hash, pins_hash = digest(bindings), digest(tokenizer_pins)
    run_hash = digest({"bindings_sha256": binding_hash, "tokenizer_sha256": pins_hash, "limits": limits.wire(), "synthetic": synthetic})
    recorder = _Recorder(encode, binding_hash, pins_hash, run_hash, receipt_sink)
    selected_length, assignment, accepted, attempts = None, None, [], []
    reason, constant_results = "fixed_pools_and_lengths_exhausted", {}
    try:
        constants_valid = True
        for check in checks:
            if not check[3]:
                valid, observation = _check(check, {}, recorder)
                constant_results[(check[0], check[1])] = observation
                if not valid:
                    constants_valid, reason = False, "constant_render_constraint_failed"
                    break
        if constants_valid:
            for length in limits.lengths:
                pools = []
                for slot in slots:
                    pool = _pool(slot, length, limits, bindings["reserved_literals"], recorder)
                    if pool is None:
                        attempts.append({"length": length, "status": "pool_exhausted", "slot": list(slot[:3])})
                        break
                    pools.append(pool)
                if len(pools) != len(slots):
                    continue
                assignment, accepted = _search(slots, pools, checks, recorder, constant_results)
                attempts.append({"length": length, "status": "selected" if assignment is not None else "joint_constraints_exhausted", "slot": None})
                if assignment is not None:
                    selected_length, reason = length, None
                    break
    except _EncodingFailure as error:
        reason = "tokenization_failed: " + str(error)
        assignment, accepted = None, []
    inventory = {}
    selected = []
    if assignment is not None:
        for root, namespace, name, index in slots:
            candidate = assignment[(root, namespace, name)]
            inventory.setdefault(root, {}).setdefault(namespace, {})[name] = candidate["value"]
            selected.append({"root": root, "namespace": namespace, "slot": name, "structural_index": index, **candidate})
    result = {"schema": SCHEMA, "status": "QUALIFIED_FOR_SUPPLIED_REGISTRY" if assignment is not None else "VS_ASSAY_INVALID",
              "qualified_for_supplied_registry": assignment is not None, "full_production_qualified": False, "ready_for_model_calls": False,
              "synthetic_test": synthetic, "bindings_sha256": binding_hash, "tokenizer_sha256": pins_hash, "run_sha256": run_hash,
              "limits": limits.wire(), "selected_length": selected_length, "inventory": inventory, "selected": selected,
              "accepted_checks": accepted, "attempts": attempts, "failure": reason,
              "receipt_count": recorder.count, "receipt_chain_sha256": recorder.head, "receipts": recorder.records,
              "pending": ["authoritative_D_and_public_probe_result_bindings", "full_production_render_registry_and_required_class_coverage", "loaded_tokenizer_file_and_template_provenance", "native_execution_release"]}
    result["sha256"] = digest(result)
    return result


def qualify_opaque_ids(bindings, encode, tokenizer_pins, *, receipt_sink=None):
    """Run the fixed production search offline; no weakened limits are exposed."""
    return _qualify(bindings, encode, tokenizer_pins, PRODUCTION_LIMITS, False, receipt_sink)


def verify_qualification(result, bindings, tokenizer_pins, receipts=None):
    """Replay exact measured token IDs to verify first-solution traversal/seals.

    This does not re-tokenize, download, or authenticate an encoder. Preserve an
    external immutable result hash to anchor the supplied transcript's custody.
    """
    _require(type(result) is dict and "sha256" in result, "sealed qualification result required")
    _require(result["sha256"] == digest({key: value for key, value in result.items() if key != "sha256"}), "result seal drift")
    records = result["receipts"] if receipts is None else receipts
    _require(type(records) is list, "complete receipt transcript required")
    limits = result["limits"]
    _record(limits, ("pool_size", "salt_limit", "lengths"), "limits")
    position = 0
    def replay(text):
        _require(position < len(records) and records[position]["text"] == text, "missing/reordered/drifted tokenization receipt")
        record = records[position]
        _require(record["error"] is None, "failed-encoder transcript requires review; cannot fabricate exception replay")
        return record["token_ids"][:]
    def compare(record):
        nonlocal position
        _require(position < len(records) and record == records[position], "receipt context/token/hash chain drift")
        position += 1
    replayed = _qualify(bindings, replay, tokenizer_pins, _Limits(limits["pool_size"], limits["salt_limit"], tuple(limits["lengths"])), result["synthetic_test"], compare)
    _require(position == len(records), "extra receipt records")
    replayed["receipts"] = result["receipts"]
    replayed["sha256"] = digest({key: value for key, value in replayed.items() if key != "sha256"})
    _require(replayed == result, "qualification/search result drift")
    return {"transcript_and_search_verified": True, "actual_encoder_provenance_verified": False,
            "full_production_qualified": False, "ready_for_model_calls": False, "qualification_sha256": result["sha256"]}

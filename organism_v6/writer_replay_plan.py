"""Prospective CPU-only W1 geometry and dose plans; never an execution permit.

Clean-base cumulative replay supports no sequential/unrehearsed retention claim.
No model loading, tokenizer loading, fitting, launching, or artifact writing.
"""

from collections import Counter
import copy
import re

from organism_v6 import multikey_writer_gateway_simple as w0


VERSION = "mwg-w1-cpu-plan-v1"
NEW_SEED = 20260912
NEW_ORIENTATIONS = ((0, 1, 0, 1, 0, 0, 1, 1), (0, 1, 0, 1, 1, 0, 0, 1))
ORIENTATION_COUNTERS = (5, 1)
BANKS = ("OLD", "NEW")
CLAIM_LIMIT = "Prospective clean-base cumulative replay; not sequential or unrehearsed retention"
SHORTCUTS = ((), ("slot",), ("mode",), ("stratum",), ("stratum", "mode"),
             ("template",), ("template", "mode"), ("tool",))
POOLED_SHORTCUTS = SHORTCUTS + (("bank",), ("bank", "mode"), ("bank", "stratum"),
                               ("bank", "stratum", "mode"), ("bank", "template"),
                               ("bank", "template", "mode"))


def build_new_bank(old_material):
    """Apply only the audit's fixed identifier/orientation substitutions to OLD."""
    w0.validate_material(old_material)
    roots = copy.deepcopy(old_material["roots"])
    excluded = {tuple(root["orientation"]) for root in roots}
    excluded |= {tuple(1 - bit for bit in orientation) for orientation in tuple(excluded)}
    for root_index, root in enumerate(roots):
        accepted = []
        for counter in range(ORIENTATION_COUNTERS[root_index] + 1):
            fingerprint = w0.digest(["mwg-w1-new-orientation-v1", NEW_SEED, root_index, counter])
            orientation = tuple(int(nibble, 16) % 2 for nibble in fingerprint[:8])
            if sum(orientation[:4]) == sum(orientation[4:]) == 2 and orientation not in excluded:
                accepted.append((counter, orientation))
        w0.require(accepted and accepted[0] == (ORIENTATION_COUNTERS[root_index], NEW_ORIENTATIONS[root_index]),
                   "prospective orientation selection changed")
        tools = ["u" + w0.digest(["mwg-w1-new-identifier-v1", NEW_SEED, root_index, slot])[:12]
                 for slot in range(8)]
        neighbours = [tool[:-1] + ("0" if tool[-1] != "0" else "1") for tool in tools]
        replacements = dict(zip(root["tools"] + root["neighbours"], tools + neighbours))
        root.update(tools=tools, neighbours=neighbours, orientation=list(NEW_ORIENTATIONS[root_index]))
        for rows in [*root["train"].values(), root["held"], root["spill"]]:
            for row in rows:
                for previous, replacement in replacements.items():
                    row["context"] = row["context"].replace(previous, replacement)
        for mapping, rows in root["train"].items():
            for row in rows:
                row["orientation"] = root["orientation"][row["slot"]]
                row["target"] = row["orientation"] ^ row["mode"] ^ (mapping == "W-")
    identifiers = [identifier for material_roots in (old_material["roots"], roots)
                   for root in material_roots for identifier in root["tools"] + root["neighbours"]]
    w0.require(len(identifiers) == len(set(identifiers)) == 64, "OLD/NEW identifier or neighbour collision")
    return dict(version=VERSION, bank="NEW", evidence="CPU_PLAN_ONLY", scientific_label=None,
                execution_ready=False, old_material_sha256=w0.digest(old_material),
                identifier_seed=NEW_SEED, orientation_counters=list(ORIENTATION_COUNTERS),
                config=copy.deepcopy(old_material["config"]), recipe=copy.deepcopy(w0.RECIPE),
                templates=copy.deepcopy(old_material["templates"]), roots=roots)


def validate_geometry(old_material, new_bank):
    """Prove exact 1/2 shortcut accuracy separately and in the pooled union."""
    w0.require(w0.canonical(new_bank) == w0.canonical(build_new_bank(old_material)),
               "NEW bank differs from prospective generator")
    checks = []
    for root_index in range(2):
        for mapping in w0.MAPS:
            for panel in ("train", "held"):
                banks = {}
                for bank, material in zip(BANKS, (old_material, new_bank)):
                    root = material["roots"][root_index]
                    rows = root["train"][mapping] if panel == "train" else root["held"]
                    banks[bank] = [dict(row, bank=bank, tool=root["tools"][row["slot"]],
                                       orientation=root["orientation"][row["slot"]],
                                       target=root["orientation"][row["slot"]] ^ row["mode"] ^ (mapping == "W-"))
                                   for row in rows]
                for bank, rows in [*banks.items(), ("POOLED", banks["OLD"] + banks["NEW"])]:
                    fields_list = POOLED_SHORTCUTS if bank == "POOLED" else SHORTCUTS
                    for fields in fields_list:
                        correct, total = w0.best_shortcut(rows, fields)
                        w0.require(2 * correct == total, "bank shortcut exceeds exactly one half")
                        checks.append(dict(root=root_index, mapping=mapping, panel=panel, bank=bank,
                                           fields=list(fields), correct=correct, total=total))
                    correct, total = w0.best_shortcut(rows, ("orientation", "mode"))
                    w0.require(correct == total, "orientation/mode positive oracle changed")
    return dict(evidence="CPU_GEOMETRY_ONLY", scientific_label=None, execution_ready=False,
                old_material_sha256=w0.digest(old_material), new_bank_sha256=w0.digest(new_bank), checks=checks)


def _schedule(old_rows, new_rows, root, mapping, seed, banks):
    occurrences = []
    for epoch in range(2):
        order = banks if epoch == 0 else tuple(reversed(banks))
        for source_index in range(128):
            for bank in order:
                row = (old_rows if bank == "OLD" else new_rows)[source_index]
                occurrences.append(dict(bank=bank, root=root, mapping=mapping, epoch=epoch,
                                        source_index=source_index, step=len(occurrences) + 1, seed=seed,
                                        source_row_sha256=w0.digest(row), context=row["context"],
                                        target=w0.CANDIDATES[row["target"]], mask="context_only"))
    return occurrences


def _plan(old_material, new_bank):
    cells = {}
    for root in range(2):
        seed = old_material["config"]["fit_seeds"][root]
        for mapping in w0.MAPS:
            old_rows = old_material["roots"][root]["train"][mapping]
            new_rows = new_bank["roots"][root]["train"][mapping]
            cells[f"{root}/{mapping}"] = {
                state: _schedule(old_rows, new_rows, root, mapping, seed, banks)
                for state, banks in (("OLD_SINGLE", ("OLD",)), ("NEW_SINGLE", ("NEW",)), ("CUM", BANKS))}
    return dict(version=VERSION, evidence="CPU_PLAN_ONLY", status="W0_PARENT_PENDING",
                execution_ready=False, scientific_label=None, claim_limit=CLAIM_LIMIT,
                training_run_replication=False, root_seed_confounded=True,
                initialization="CLEAN_BASE_FOR_EVERY_NEW_FIT", proposed_new_fits=8, reused_old_fits=4,
                old_material_sha256=w0.digest(old_material), new_bank_sha256=w0.digest(new_bank),
                inherited_recipe=copy.deepcopy(w0.EXECUTION_RECIPE),
                intended_dose=dict(NEW_SINGLE=dict(rows=128, optimizer_steps=256),
                                   CUM=dict(rows=256, optimizer_steps=512)),
                cells=cells, ordered_occurrences_sha256=w0.digest(cells),
                real_tokenizer_encodings_bound=False, parent_binding=None)


def validate_replay_plan(plan, old_material, new_bank):
    """Check full ordered bytes AND exact per-bank/per-epoch matched exposure."""
    validate_geometry(old_material, new_bank)
    w0.require(w0.canonical(plan) == w0.canonical(_plan(old_material, new_bank)),
               "replay plan changed: order, bytes, seed, dose or boundary")
    checks = []
    for cell, schedules in plan["cells"].items():
        for bank in BANKS:
            for epoch in range(2):
                single = [row for row in schedules[f"{bank}_SINGLE"] if row["epoch"] == epoch]
                cumulative = [row for row in schedules["CUM"] if row["bank"] == bank and row["epoch"] == epoch]
                def counts(rows):
                    return Counter((row["source_index"], row["source_row_sha256"], row["context"],
                                    row["target"], row["mask"], row["seed"]) for row in rows)
                w0.require(len(single) == len(cumulative) == 128 and counts(single) == counts(cumulative)
                           and len(counts(single)) == 128 and set(counts(single).values()) == {1},
                           "unmatched per-bank exposure")
                checks.append(dict(cell=cell, bank=bank, epoch=epoch, single=128, cumulative=128))
    return dict(evidence="CPU_EXPOSURE_ONLY", scientific_label=None, execution_ready=False,
                plan_sha256=w0.digest(plan), checks=checks)


def build_replay_plan(old_material, new_bank):
    """Return prospective schedules only; this API never accepts a launch flag."""
    validate_geometry(old_material, new_bank)
    plan = _plan(old_material, new_bank)
    validate_replay_plan(plan, old_material, new_bank)
    return plan


def validate_w0_parent(path, *, expected_source_hashes):
    """Read-only full W0 replay; success is parent evidence, NOT W1 readiness.

    expected_source_hashes must be independently supplied trusted W0 source pins.
    No fallback to labels in a caller-supplied report or partial stage receipts.
    """
    w0.exact_keys(expected_source_hashes, w0.SOURCE_PATHS)
    w0.require(all(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
                   for value in expected_source_hashes.values()), "trusted W0 source hashes required")
    w0.require(w0.source_hashes() == expected_source_hashes, "local W0 replay implementation differs from trusted pins")
    root = w0.checked_path(path)
    w0.require(not (root / "NONREPORTABLE_ABORT.json").exists(), "aborted W0 cannot be a parent")
    seal_path = root / "REAL_EXECUTION_SEAL.json"
    w0.require(seal_path.is_file(), "W0_PARENT_PENDING: real execution seal missing")
    seal_hash = w0.file_hash(seal_path)
    report = w0.replay_real(root)
    w0.require(report["evidence"] == "REAL_GPU_EXECUTION" and
               report["scientific_label"] == report["result"]["label"] == "MULTIKEY_BINDING_PASS",
               "W0_PARENT_PENDING: exact replayed MULTIKEY_BINDING_PASS required")
    manifest = w0.load_json(root / "manifest.json")
    w0.require(manifest["source_hashes"] == expected_source_hashes, "parent W0 source pins differ")
    seal = w0.load_json(seal_path)
    native_name = "native_build_preflight.json"
    native = w0.load_json(root / native_name)
    native_hash = w0.file_hash(root / native_name)
    w0.require(manifest["artifact_hashes"].get(native_name) == seal["files"].get(native_name) == native_hash,
               "parent native-build evidence is not sealed and manifest-bound")
    w0.require(native["kind"] == "CPU_NATIVE_BUILD_PREFLIGHT" and native["returncode"] == 0
               and native["model_loaded"] is False and native["real_GPU_executed"] is False
               and isinstance(native.get("triton_version"), str) and native["triton_version"]
               and native.get("compiler_version") and native.get("headers")
               and re.fullmatch(r"[0-9a-f]{64}", native.get("compiler_sha256", "")),
               "parent native-build/Triton prerequisite incomplete")
    adapters = w0.load_json(root / "adapter_hashes.json")
    w0.exact_keys(adapters, [f"{root_index}/{mapping}" for root_index in range(2) for mapping in w0.MAPS])
    adapter_bindings = {}
    for root_index in range(2):
        for map_index, mapping in enumerate(w0.MAPS):
            adapter_path = root / f"adapter_fit_{root_index}_{map_index}"
            key = f"{root_index}/{mapping}"
            w0.require(w0.tree_hash(adapter_path) == adapters[key], "OLD adapter tree changed")
            adapter_bindings[key] = dict(path=str(adapter_path), sha256=adapters[key])
    w0.require(w0.file_hash(seal_path) == seal_hash, "parent seal changed during replay")
    config = manifest["config"]
    return dict(evidence="REPLAYED_W0_PARENT_ONLY", parent_eligible=True, execution_ready=False,
                scientific_label=None, parent_scientific_label="MULTIKEY_BINDING_PASS", parent_root=str(root),
                seal_sha256=seal_hash, report_sha256=w0.digest(report), manifest_sha256=w0.digest(manifest),
                material_sha256=w0.file_hash(root / "material.json"),
                requests_sha256=w0.file_hash(root / "requests.json"),
                source_hashes=copy.deepcopy(expected_source_hashes), adapters=adapter_bindings,
                native_build_preflight_sha256=native_hash,
                identity={key: copy.deepcopy(config[key]) for key in
                          ("model", "model_revision", "tokenizer_revision", "model_sha256", "tokenizer_sha256",
                           "environment", "node", "gpu_uuid", "driver_version", "seeds")},
                claim_limit=CLAIM_LIMIT)

"""Immutable full-population v6 CPU qualification; never a GPU launcher."""

import argparse
from collections import Counter
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import time
import traceback


SCHEMA = "ASTRA_STAGE2A_V6_FULL_POPULATION_CPU_V1"
ROOT = Path(__file__).resolve().parents[1]
SUITES = (
    "tests.test_composition_birth_stage2a_screen_reduce",
    "tests.test_composition_birth_stage2a_canaries",
    "tests.test_composition_birth_stage2a_scoring",
    "tests.test_composition_birth_stage2a_screen",
    "tests.test_composition_birth_stage2a_primitives",
    "tests.test_composition_birth_stage2a_tape",
    "tests.test_composition_birth_stage2a_curriculum",
    "tests.test_composition_birth_stage2a_birth",
    "tests.test_composition_birth_stage2a_boundary",
    "tests.test_composition_birth_stage2a_custody",
    "tests.test_composition_birth_stage2a_allocation",
    "tests.test_composition_birth_stage2a_typed_scan",
    "tests.test_astra_stage2a_v6_cpu_oracles",
    "tests.test_astra_stage2a_v6_cpu_qualification",
)


def write_once(path, raw):
    with path.open("xb") as stream:
        stream.write(raw)


def encoded(value):
    return json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reject(call, counters, name):
    try:
        call()
    except ValueError:
        counters[name] += 1
        return
    raise AssertionError("mutation_was_accepted: " + name)


def boundary_byte_mutations(projection):
    require(type(projection) is bytes and bool(projection), "nonempty_projection_required")
    midpoint = len(projection) // 2
    changed = projection[:midpoint] + bytes((projection[midpoint] ^ 1,)) + projection[midpoint + 1:]
    mutations = {"copy": projection + projection, "delete": projection[:-1],
                 "move": projection[1:] + projection[:1], "middle": changed}
    require(all(candidate != projection for candidate in mutations.values()), "noop_byte_mutation")
    return mutations


def expected_reduced_slots():
    slots = [("CHAIN", task, 0, None, "D1_CHAIN", 29 * task + call)
             for task in (0, 4, 8, 12, 16, 20, 24, 28) for call in range(29)]
    for transition_index, transition in enumerate(("SEEK", "PROSPECT", "CHECK", "CONTINUE")):
        slots.extend(("INTERVENTION", pair, member, transition, "D1_INTERVENTION_" + transition,
                      928 + 16 * transition_index + 2 * pair + member)
                     for pair in (0, 2, 4, 6) for member in (0, 1))
    slots.extend(("CANARY", index, None, None, "D1_CANARY", 992 + index) for index in range(16))
    return tuple(slots)


def verify_reduced_pairing(master):
    expected = expected_reduced_slots()
    expected_seeds = tuple(int.from_bytes(sha256(
        master + b"\0decode\0" + slot[4].encode("ascii") + b"\0"
        + slot[5].to_bytes(4, "big")).digest()[-8:], "big") for slot in expected)
    states = {}
    for state in ("BASE", "D1_ATOM_LOCAL"):
        captured = screen.reduced_screen("D1")
        observed = tuple((entry.kind, entry.index, entry.member, entry.transition,
                          entry.slot.panel_label, entry.slot.global_ordinal) for entry in captured)
        require(observed == expected, "independent_logical_slot_mismatch:" + state)
        seeds = screen.reduced_decode_seeds("D1", master=master)
        require(seeds == expected_seeds, "independent_paired_seed_derivation_mismatch:" + state)
        states[state] = {"slots": observed, "seeds": seeds}
    require(len(expected) == 280 and states["BASE"] == states["D1_ATOM_LOCAL"], "changed_screen_pairing")
    return states


def source_pins():
    paths = [*ROOT.glob("organism_v6/composition_birth_stage2a*.py"),
             *ROOT.glob("tests/test_composition_birth_stage2a*.py"),
             *ROOT.glob("tests/test_astra_stage2a_v6_cpu*.py"),
             *ROOT.glob("gpu/astra_stage2a_v6_cpu*.py"),
             *ROOT.glob("research_notes/analysis/*stage2a*.md")]
    paths.extend(path for path in (ROOT / "organism_v6/__init__.py", ROOT / "gpu/__init__.py",
                                   ROOT / "tests/__init__.py") if path.exists())
    return {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in sorted(paths)}


def bootstrap(options):
    out = Path(options.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    snapshot = out / "source"
    snapshot.mkdir()
    pins = source_pins()
    for relative, expected_sha in pins.items():
        raw = (ROOT / relative).read_bytes()
        require(sha256(raw).hexdigest() == expected_sha, "source_changed_while_archiving")
        destination = snapshot / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        write_once(destination, raw)
        destination.chmod(0o444)
    manifest = out / "SNAPSHOT.json"
    write_once(manifest, encoded({"source_pins": pins, "created_unix": time.time(),
                                 "source_root": str(ROOT), "snapshot_root": str(snapshot)}))
    manifest.chmod(0o444)
    for directory in sorted((path for path in snapshot.rglob("*") if path.is_dir()), reverse=True):
        directory.chmod(0o555)
    snapshot.chmod(0o555)
    command = [sys.executable, "-B", str(snapshot / "gpu" / Path(__file__).name),
               "--out", str(out), "--master", options.master, "--snapshot-manifest", str(manifest)]
    return subprocess.run(command, cwd=snapshot, check=False,
                          env=dict(os.environ, PYTHONPATH=str(snapshot), PYTHONDONTWRITEBYTECODE="1",
                                   CUDA_VISIBLE_DEVICES="")).returncode


def load_implementation():
    global wire, allocation_api, boundary_api, custody_api, primitives, scanner, screen, targets, typed_scan, oracles
    from organism_v6 import composition_birth_stage2a as wire
    from organism_v6 import composition_birth_stage2a_allocation as allocation_api
    from organism_v6 import composition_birth_stage2a_boundary as boundary_api
    from organism_v6 import composition_birth_stage2a_custody as custody_api
    from organism_v6 import composition_birth_stage2a_primitives as primitives
    from organism_v6 import composition_birth_stage2a_scanner as scanner
    from organism_v6 import composition_birth_stage2a_screen as screen
    from organism_v6 import composition_birth_stage2a_targets as targets
    from organism_v6 import composition_birth_stage2a_typed_scan as typed_scan
    from gpu import astra_stage2a_v6_cpu_oracles as oracles


def expected_public(case, record):
    ordinal = int(record.unit.unit_id.rsplit("u", 1)[1])
    target = case.targets[ordinal]
    stop = target.trace_index
    if record.arm == "CLOSED":
        indices = tuple(range(stop))
        task_text = case.task_text
    else:
        phase = target.phase
        if phase == "CONTINUE":
            indices = ()
        elif phase in ("READ_CHECK", "PROSPECT"):
            indices = (stop - 1,)
        elif phase == "STEP_CHECK":
            indices = (stop - 2, stop - 1)
        elif phase == "SEEK":
            indices = ((stop - 3, stop - 2, stop - 1)
                       if case.descriptor.recovery_subtype == "STEP_OUTCOME_MISMATCH" else (0,))
        else:
            raise ValueError("unknown_phase")
        current = case.trace[indices[0]].current_before if indices else target.current_before
        task_text = f"TASK\nSTART {case.task.start}\nGOAL {case.task.goal}\nCURRENT {current}"
    messages = [targets.Message("system", wire.SYSTEM_MESSAGE), targets.Message("user", task_text)]
    for index in indices:
        turn = case.trace[index]
        messages.extend((targets.Message("assistant", turn.action), targets.Message("user", turn.response)))
    return tuple(messages), indices


def independent_inventories(source, result):
    future = result.future_inputs
    candidates = {token.encode("ascii") for role, token in source.role_tokens.items()
                  if role.rsplit("/", 1)[-1] in ("query", "event", "port")}
    for block in source.case.construction.blocks.values():
        if block.kind == "EVENTS":
            candidates.update(row.got.encode("ascii") for row in block.rows)
    candidates.update(value.encode("ascii") for value in source.case.construction.world_edges.values())
    disclosed = {}
    for observation in result.binding.observations:
        eligible = (observation.origin == "service"
                    or (observation.origin == "host" and observation.kind == "current"
                        and observation.path.endswith("/WORLD/CURRENT"))
                    or (observation.origin == "actor" and observation.kind in
                        ("issued_query", "read_index_operand", "step_operand", "think_implicated")
                        and observation.path.endswith("/action/operand")))
        if eligible and observation.value in candidates:
            disclosed.setdefault(observation.value, []).append(observation)
    require(future.candidates == candidates, "candidate_totality")
    require(future.disclosed == set(disclosed), "disclosure_totality")
    require(future.future_identifiers == candidates - set(disclosed), "future_totality")
    require(dict(future.disclosure_provenance) == {key: tuple(value) for key, value in disclosed.items()},
            "disclosure_ownership")
    require(set(future.candidate_provenance) == candidates, "candidate_ownership_totality")
    expected_routes = {}
    recovery = {}
    for request, block in source.case.construction.blocks.items():
        if block.kind == "EVENTS":
            query = wire.parse_action(request).operand
            for position, row in enumerate(block.rows):
                expected_routes[row.port] = (query, row, request, position)
                recovery[row.recover] = row.port
    require(set(result.route_inputs.transitions) == set(expected_routes), "route_totality")
    for port, (query, row, request, position) in expected_routes.items():
        edge = result.route_inputs.transitions[port]
        expected = (query, row.event, row.node, row.goal, port, row.got,
                    source.case.construction.world_edges[row.node, port], row.recover, row.receipt,
                    ("case", "construction", "blocks", request, "rows", str(position)), recovery.get(query))
        actual = (edge.query, edge.event, edge.current, edge.goal, edge.port, edge.predicted,
                  edge.actual, edge.recover, edge.receipt, edge.source_path, edge.recovery_owner_port)
        require(actual == expected, "route_effective_source_or_recovery_mismatch")


def mutation_values(source, record, result, *, route_probes=None):
    mutations = {"full_target": record.unit.target_bytes}
    if record.unit.operand is not None:
        mutations["operand"] = record.unit.operand.encode("ascii")
    for kind in (b"M2AN_", b"M2AQ_", b"M2AE_", b"M2AP_"):
        candidate = next((token for token in sorted(result.future_inputs.future_identifiers)
                          if token.startswith(kind)), None)
        if candidate is not None:
            mutations["future_" + kind.decode("ascii")] = candidate
    seen_private = set()
    for name, raw in sorted(oracles.expected_private_probes(source, record).items()):
        category = name.split(":", 1)[0]
        selection = (category, raw) if category == "private_category" else (category,)
        if selection not in seen_private:
            seen_private.add(selection)
            mutations[name] = raw
    for value in (*scanner.FORBIDDEN_CORE_LABELS, *typed_scan.FORBIDDEN_EDGE_LABELS):
        mutations["label_" + value.decode("ascii")] = value
    if route_probes is None:
        route_probes = oracles.expected_route_probes(source)
    require(set(route_probes) == {"route_actions_literal", "route_actions_spacing", "route_actions_compact",
                                 "route_ordered_ids", "route_event_rows", "route_mixed"},
            "all_source_route_families_required")
    mutations.update({name: probe["raw"] for name, probe in route_probes.items()})
    return mutations


def intended_detector(diagnostic, name, raw, offset, *, route_probe=None):
    if name.startswith("route_"):
        require(route_probe is not None and route_probe["raw"] == raw, "independent_route_probe_required")
        first_span = tuple(offset + value for value in route_probe["first_span"])
        second_span = tuple(offset + value for value in route_probe["second_span"])
        return any(issue.grammar == route_probe["grammar"]
                   and (issue.first_port, issue.second_port) == (route_probe["first_port"], route_probe["second_port"])
                   and (issue.first_span, issue.second_span) == (first_span, second_span)
                   for issue in diagnostic.route_scan.issues)
    if name.startswith("private_"):
        return any(issue.category == name.split(":")[0] and issue.value == raw and issue.start >= offset
                   for issue in diagnostic.private_issues)
    if name.startswith("label_") and raw in typed_scan.FORBIDDEN_EDGE_LABELS:
        return any(issue.category == "forbidden_edge_label" and issue.value == raw and issue.start >= offset
                   for issue in diagnostic.typed_issues)
    category = ("future_identifier" if name.startswith("future_") else
                "forbidden_core" if name.startswith("label_") else name)
    return any(issue.category == category and issue.value == raw and issue.start >= offset
               for issue in diagnostic.content_scan.issues)


def run(options):
    started = time.time()
    out = Path(options.out).resolve()
    require(Path(options.snapshot_manifest).resolve() == out / "SNAPSHOT.json"
            and ROOT == out / "source", "retained_snapshot_execution_required")
    pins = json.loads(Path(options.snapshot_manifest).read_bytes())["source_pins"]
    require(source_pins() == pins, "source_snapshot_pin_mismatch_before_import")
    load_implementation()
    master = options.master.encode("ascii")
    primitives.adapter_seed(master)
    artifacts = out / "artifacts"
    artifacts.mkdir()
    write_once(out / "manifest.json", encoded({
        "schema": SCHEMA, "started_unix": started, "master_hex": master.hex(), "source_pins": pins,
        "argv": sys.argv, "kind": "CPU_FULL_POPULATION_NOT_NATIVE_READINESS",
        "expected_cases": 64, "expected_units": 256, "expected_arm_records": 512,
    }))
    counts, commands, phases = Counter(), Counter(), Counter()
    failures, rows, category_probes = [], [], set()
    maxima = Counter()

    def keep(raw):
        digest = sha256(raw).hexdigest()
        path = artifacts / digest
        if not path.exists():
            write_once(path, raw)
        else:
            require(path.read_bytes() == raw, "content_address_collision")
        return digest

    try:
        allocation = allocation_api.allocate_stage2a(master=master)
        allocation_api.verify_stage2a(allocation, master=master)
        allocation_digest = keep(allocation.custody_bytes)
        roles = allocation.role_tokens_by_world("birth_train")
        require(tuple(roles) == tuple(f"p{index:02d}" for index in range(32)), "whole_world_roster")
        for world, role_tokens in roles.items():
            verifier = boundary_api.BirthBoundaryVerifier(world=world, role_tokens=role_tokens, display_master=master)
            shared_digest = keep(verifier.shared_bytes)
            rebuilt = custody_api.BirthSourceCustody.from_bytes(verifier.shared_bytes)
            require(rebuilt.shared_bytes == verifier.shared_bytes, "shared_roundtrip")
            reject(lambda: verifier.verify_shared(verifier.shared_bytes + b" "), counts, "shared_mutation")
            del rebuilt
            foreign_master = custody_api.BirthSourceCustody(
                world=world, role_tokens=role_tokens, display_master=master + b"-FOREIGN",
            )
            reject(lambda: verifier.verify_shared(foreign_master.shared_bytes), counts, "foreign_master_custody")
            foreign_roles = dict(role_tokens)
            keys = tuple(key for key in sorted(foreign_roles) if key.endswith("/node"))[:2]
            foreign_roles[keys[0]], foreign_roles[keys[1]] = foreign_roles[keys[1]], foreign_roles[keys[0]]
            foreign_role_custody = custody_api.BirthSourceCustody(
                world=world, role_tokens=foreign_roles, display_master=master,
            )
            reject(lambda: verifier.verify_shared(foreign_role_custody.shared_bytes), counts, "foreign_roles_custody")
            foreign_custodies = {"foreign_master": foreign_master, "foreign_roles": foreign_role_custody}
            foreign_records = {
                name: {(candidate.unit.unit_id, candidate.arm): candidate
                       for case in custody.cases
                       for paired in targets.serialize_birth_case(
                           case, role_tokens=role_tokens if name == "foreign_master" else foreign_roles)
                       for candidate in (paired.closed, paired.atom_local)}
                for name, custody in foreign_custodies.items()
            }
            foreign_shared_hashes = {name: keep(custody.shared_bytes) for name, custody in foreign_custodies.items()}
            twins = {(record.unit.unit_id, record.arm): record for record in verifier.records}
            counts["pairs"] += 1
            counts["cases"] += 2
            for record in verifier.records:
                identity = record.unit.unit_id + "/" + record.arm
                record_started = time.perf_counter()
                record_cpu_started = time.process_time()
                try:
                    source = verifier._custody.source_for(record)
                    messages, indices = expected_public(source.case, record)
                    projection = b"\n".join(message.content.encode("ascii") for message in messages)
                    result = verifier.verify(record, public_messages=messages, public_projection=projection)
                    require(result.binding.retained_trace_indices == indices, "retained_chronology_mismatch")
                    independent_inventories(source, result)
                    oracles.verify_inventory_ownership(source, result)
                    oracles.assert_private_basis_totality(source, record, result.scan.private_basis)
                    require(result.source_content_clear, "authentic_source_failed: " + repr(result.scan.issues[:8]))
                    counts["arm_records"] += 1
                    phases[record.unit.phase + "/" + record.arm] += 1
                    if record.arm == "CLOSED":
                        commands[record.unit.command] += 1
                        counts["units"] += 1
                    route_probes = oracles.expected_route_probes(source)
                    for name, raw in mutation_values(source, record, result, route_probes=route_probes).items():
                        mutated = projection + b"\n" + raw
                        reject(lambda candidate=mutated: verifier.verify(record, public_projection=candidate),
                               counts, "boundary_injection_" + name)
                        probe_key = record.unit.phase, record.arm, name.split(":", 1)[0], sha256(raw).hexdigest()
                        if probe_key not in category_probes:
                            diagnostic = typed_scan.scan_typed_birth(
                                source=source, binding=result.binding, future_inputs=result.future_inputs,
                                route_inputs=result.route_inputs, candidate_prefix=mutated,
                            )
                            require(not diagnostic.passed and intended_detector(
                                diagnostic, name, raw, len(projection) + 1, route_probe=route_probes.get(name)),
                                    "intended_category_detector_did_not_reject: " + name)
                            category_probes.add(probe_key)
                    for name, changed in boundary_byte_mutations(projection).items():
                        reject(lambda candidate=changed: verifier.verify(record, public_projection=candidate), counts, name)
                    forged = replace(record, prefix_sha256="0" * 64)
                    reject(lambda: verifier.verify(forged), counts, "forged_record")
                    reject(lambda: verifier.verify(record, candidate_boundary_bytes=result.boundary_bytes + b" "),
                           counts, "forged_boundary")
                    twin = twins[record.unit.unit_id, "ATOM_LOCAL" if record.arm == "CLOSED" else "CLOSED"]
                    reject(lambda: verifier.verify(twin, candidate_boundary_bytes=result.boundary_bytes), counts, "foreign_arm")
                    malformed = replace(record, unit=replace(record.unit, unit_id="p99/m0/u0"))
                    reject(lambda: verifier.verify(malformed), counts, "malformed_case")
                    other_member = "m1" if source.case.descriptor.member == "m0" else "m0"
                    other_unit = f"{world}/{other_member}/" + record.unit.unit_id.rsplit("/", 1)[1]
                    foreign_case = twins[other_unit, record.arm]
                    reject(lambda: verifier.verify(foreign_case, candidate_boundary_bytes=result.boundary_bytes),
                           counts, "foreign_case")
                    for name, foreign in foreign_custodies.items():
                        envelope = primitives.parse_canonical_json(result.boundary_bytes)
                        envelope["shared_custody_sha256"] = foreign.shared_sha256
                        foreign_record = foreign_records[name][record.unit.unit_id, record.arm]
                        foreign_source = foreign.source_for(foreign_record)
                        envelope.update({"source_provenance": {"bytes_hex": foreign_source.provenance_bytes.hex()},
                                         "source_provenance_sha256": foreign_source.provenance_sha256,
                                         "case_sha256": foreign_source.case_sha256,
                                         "record_sha256": foreign_source.record_sha256})
                        foreign_boundary = primitives.canonical_json(envelope)
                        reject(lambda raw=foreign_boundary, candidate=foreign_record:
                               verifier.verify(candidate, public_messages=candidate.prefix, candidate_boundary_bytes=raw),
                               counts, name)
                    envelope = primitives.parse_canonical_json(result.boundary_bytes)
                    envelope["message_spans"][0]["end"] = envelope["message_spans"][1]["end"]
                    crossing = primitives.canonical_json(envelope)
                    reject(lambda: verifier.verify(record, candidate_boundary_bytes=crossing), counts, "boundary_crossing")
                    for name in ("field_observations", "candidate_inventory", "typed_occurrence_receipts"):
                        envelope = primitives.parse_canonical_json(result.boundary_bytes)
                        if name == "field_observations":
                            envelope[name][0]["end"] = envelope["message_spans"][1]["end"]
                        else:
                            envelope[name]["count"] += 1
                        counterfeit = primitives.canonical_json(envelope)
                        reject(lambda raw=counterfeit: verifier.verify(record, candidate_boundary_bytes=raw),
                               counts, "caller_" + name)
                    artifact_hashes = {
                        "boundary": keep(result.boundary_bytes), "shared": shared_digest,
                        "candidates": keep(result.candidate_inventory_bytes),
                        "retained": keep(result.retained_inventory_bytes), "routes": keep(result.route_basis_bytes),
                        "private_static_basis": keep(result.private_static_basis_bytes),
                        "private_record_basis": keep(result.private_record_basis_bytes),
                        "typed_receipts": keep(result.typed_receipts_bytes),
                        "core": keep(result.core_inputs.core_bytes), "checker": keep(result.core_inputs.checker_payload),
                        "checker_receipt": keep(result.core_inputs.receipt_bytes),
                        **foreign_shared_hashes,
                    }
                    counts["canonical_boundary_bytes"] += len(result.boundary_bytes)
                    maxima["boundary_bytes"] = max(maxima["boundary_bytes"], len(result.boundary_bytes))
                    maxima["shared_bytes"] = max(maxima["shared_bytes"], len(verifier.shared_bytes))
                    maxima["private_values"] = max(maxima["private_values"], len(result.scan.private_basis))
                    rows.append({"identity": identity, "status": "PASS", "artifacts": artifact_hashes,
                                 "counts": dict(result.scan.counts)})
                except Exception as error:
                    failures.append({"identity": identity, "error": str(error), "traceback": traceback.format_exc()})
                    rows.append({"identity": identity, "status": "FAIL", "error": str(error)})
                    print(json.dumps(failures[-1]), flush=True)
                rows[-1].update({"elapsed_seconds": time.perf_counter() - record_started,
                                 "cpu_seconds": time.process_time() - record_cpu_started,
                                 "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
                with (out / "records.jsonl").open("ab") as stream:
                    stream.write(json.dumps(rows[-1], sort_keys=True).encode("ascii") + b"\n")
            print(json.dumps({"world": world, "processed_records": len(rows),
                              "passed_records": sum(row["status"] == "PASS" for row in rows), "failures": len(failures),
                              "elapsed_seconds": time.time() - started}), flush=True)
        require(counts["pairs"] == 32 and counts["cases"] == 64 and counts["units"] == 256
                and counts["arm_records"] == 512, "incomplete_population")
        require(commands == {"READ": 96, "STEP": 64, "THINK": 64, "STOP": 32}, "target_counts")
        expected_phases = {phase + "/" + arm for phase in
                           ("SEEK", "PROSPECT", "READ_CHECK", "STEP_CHECK", "CONTINUE")
                           for arm in ("CLOSED", "ATOM_LOCAL")}
        require(set(phases) == expected_phases, "missing_phase_arm_coverage")
        for name in ("foreign_arm", "foreign_case", "foreign_master", "foreign_roles", "boundary_crossing",
                     "caller_field_observations", "caller_candidate_inventory", "caller_typed_occurrence_receipts"):
            require(counts[name] == 512, "incomplete_population_adversary: " + name)
        for name in ("literal", "spacing", "compact"):
            require(counts["boundary_injection_route_actions_" + name] == 512, "incomplete_route_action_family:" + name)
        for name in ("ordered_ids", "event_rows", "mixed"):
            require(counts["boundary_injection_route_" + name] == 512, "incomplete_route_family:" + name)
        write_once(out / "paired_screen_slots.json", encoded(verify_reduced_pairing(master)))
        test_command = [sys.executable, "-B", "-m", "unittest", *SUITES, "-v"]
        write_once(out / "integrity_tests_command.json", encoded(test_command))
        with (out / "integrity_tests.log").open("xb") as stream:
            tested = subprocess.run(test_command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                    env=dict(os.environ, CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1"),
                                    timeout=900, check=False)
        require(tested.returncode == 0, "paired_scoring_training_integrity_tests_failed")
        test_log = (out / "integrity_tests.log").read_bytes()
        totals = re.findall(rb"^Ran ([0-9]+) tests? in ", test_log, flags=re.MULTILINE)
        require(len(totals) == 1 and int(totals[0]) > 0 and b"skipped=" not in test_log
                and b"expected failures=" not in test_log, "incomplete_integrity_test_receipt")
        counts["integrity_tests"] = int(totals[0])
        counts["paired_scoring_training_suite_exit_zero"] = 1
        require(source_pins() == pins, "source_changed_during_qualification")
    except Exception as error:
        failures.append({"identity": "population", "error": str(error), "traceback": traceback.format_exc()})
    report = {"schema": SCHEMA, "status": "PASS" if not failures else "FAIL",
              "kind": "CPU_FULL_POPULATION_NOT_NATIVE_READINESS", "started_unix": started,
              "finished_unix": time.time(), "elapsed_seconds": time.time() - started,
              "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "counts": dict(counts), "commands": dict(commands), "phases": dict(phases),
              "maxima": dict(maxima), "independent_category_probes": len(category_probes),
              "failures": failures, "records": rows, "source_pins": pins,
              "fresh_independent_review": "PENDING", "native_preparation": False,
              "native_model_tokenizer_gpu": False, "scientific_claims": False}
    write_once(out / "report.json", encoded(report))
    print(json.dumps({key: value for key, value in report.items() if key not in ("records", "source_pins", "failures")}), flush=True)
    return 0 if not failures else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--master", required=True)
    parser.add_argument("--snapshot-manifest")
    options = parser.parse_args()
    raise SystemExit(run(options) if options.snapshot_manifest else bootstrap(options))

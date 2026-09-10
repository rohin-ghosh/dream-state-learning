#!/usr/bin/env python3
"""Static/semantic validation of proposal-only PPC5r10 machine contracts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import author_machine_rfc as author
import validate_reducer_semantics as semantics

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
SOURCE_ROOT=REPO/"research_loop/changes/chg_20260905_public_pathway_consolidation_v5r9"


def load(name):return json.loads((HERE/name).read_text())


def rejected(value,schema)->bool:
    try:semantics.validate_closed_schema(value,schema)
    except (AssertionError,KeyError,TypeError):return True
    return False


def pointer_get(value,pointer):
    if pointer in ("","/"):return value
    for raw in pointer.strip("/").split("/"):
        key=raw.replace("~1","/").replace("~0","~")
        value=value[int(key)] if isinstance(value,list) else value[key]
    return value


def main():
    machine=load("REDUCER_MACHINE_RFC.json");inputs=load("REDUCER_INPUT_ROWS_RFC.json")
    programs=load("REDUCER_PROGRAMS_RFC.json");snapshots=load("REDUCER_SOURCE_SNAPSHOTS.json")
    bindings=load("REDUCER_EXACT_SOURCE_BINDINGS_RFC.json");vector=load("VECTOR_FIXTURE_RFC.json")
    assert machine["document_kind"]=="PPC5R10_CLOSED_REDUCER_MACHINE_RFC"
    assert machine["lifecycle_state"]=="PROPOSAL_ONLY" and machine["authority_conferred"] is False
    assert machine["materialization_permitted"] is False
    for row in machine["source_files"].values():
        assert hashlib.sha256((HERE/row["file"]).read_bytes()).hexdigest()==row["sha256"]
    # Preserve and re-evaluate every exact upstream pointer value.
    assert bindings["binding_count"]==110
    for row in bindings["bindings"]:
        filename,marker,pointer=row["binding"].partition("#")
        value=pointer_get(json.loads((SOURCE_ROOT/filename).read_text()),pointer if marker else "/")
        assert semantics.digest(value)==row["pointer_value_sha256"]
    for row in snapshots["snapshots"]:
        value=pointer_get(json.loads((SOURCE_ROOT/row["file"]).read_text()),row["json_pointer"])
        assert semantics.digest(value)==row["value_sha256"]
    sources=semantics.load_sources();builders={x["law_id"]:x for x in inputs["builders"]}
    program_by={x["law_id"]:x for x in programs["programs"]};laws={x["law_id"]:x for x in machine["laws"]}
    assert len(builders)==len(program_by)==len(laws)==machine["law_count"]==58
    assert set(builders)==set(program_by)==set(laws)
    expected={(test,s["suite_id"]):s["entry_count"] for test,suites in vector["suite_vectors"].items() for s in suites}
    assert {(x["test_id"],x["suite_id"]):x["entry_count"] for x in laws.values()}==expected
    total=0
    for law_id,law in laws.items():
        rows=semantics.rows_from_builder(builders[law_id],sources);total+=len(rows)
        assert semantics.digest(rows)==law["input_vector_sha256"]
        assert author.schema_for_values(rows)==law["input_row_schema"]
        for row in rows:
            assert not semantics.forbidden_keys(row,set(machine["forbidden_executor_keys"]))
            semantics.validate_closed_schema(row,law["input_row_schema"])
            extra=json.loads(semantics.canonical(row));extra["__extra__"]=0
            assert rejected(extra,law["input_row_schema"])
            missing=json.loads(semantics.canonical(row));missing.pop(next(iter(missing)))
            assert rejected(missing,law["input_row_schema"])
        params={k:builders[law_id][k] for k in ("replay_sources","final_result_source_facts") if k in builders[law_id]}
        assert author.schema_for_values([params])==law["parameter_schema"]
        semantics.validate_closed_schema(params,law["parameter_schema"])
        program=program_by[law_id]
        outputs=semantics.reduce_rows(program,rows,{sid:sources[sid] for sid in builders[law_id].get("source_ids",[])},params)
        assert law["operator"]==program["operator"] and law["output_columns"]==program["output_columns"]
        assert law["output_row_schema"]==author.output_row_schema(program,outputs)
        for output in outputs:
            semantics.validate_closed_schema(output,law["output_row_schema"])
            assert rejected(output+[None],law["output_row_schema"])
            assert rejected(output[:-1],law["output_row_schema"])
    assert total==machine["input_entry_count"]==1113
    influence=builders["T08_INFLUENCE_RELATION_V1"]
    assert influence["columns"]==["left_upstream","right_upstream"]
    assert "perturbation" not in json.dumps(influence)
    dream=builders["T04_DREAM_REDUCER_V1"]
    assert "ordinal" not in json.dumps(dream).lower()
    assert "input_ordinal" not in program_by["T04_DREAM_REDUCER_V1"]["output_columns"]
    t14=builders["T14_FULL_PREDECESSOR_REPLAY_V1"]
    assert "reconstruction_kind" not in json.dumps(t14)
    assert len(t14["rows"])==24 and len(t14["replay_sources"])==2 and len(t14["final_result_source_facts"])==6
    assert builders["T13_FULL_TECHNICAL_PASS_V1"]["op"]=="T13_TECHNICAL_GRAPH"
    schema_edges=semantics.collect_schema_edges(sources["SCHEMA_DEFS"])
    inventory_edges=semantics.inventory_edges(sources["OBJECTS"])
    assert schema_edges==inventory_edges
    cold=semantics.edges_for(inventory_edges,"COLD_REPLAY_RECEIPT")
    final=semantics.edges_for(inventory_edges,"T14_FINAL_REPLAY_RESULT")
    outbound=[e for e in inventory_edges if e["producer_type"]=="T14_FINAL_REPLAY_RESULT" and e["consumer_type"]=="PRECLAIM_AUTHORITY_RECEIPT"]
    assert (len(cold),len(final),len(outbound))==(11,6,1)
    print(json.dumps({"status":"PASS","law_count":58,"input_entry_count":total,
        "machine_sha256":hashlib.sha256((HERE/"REDUCER_MACHINE_RFC.json").read_bytes()).hexdigest()},sort_keys=True,separators=(",",":")))


if __name__=="__main__":main()

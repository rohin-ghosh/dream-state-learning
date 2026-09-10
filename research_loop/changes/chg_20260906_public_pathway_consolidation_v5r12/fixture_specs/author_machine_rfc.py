#!/usr/bin/env python3
"""Print the closed PPC5r12 reducer-machine RFC; never writes fixtures."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import validate_reducer_semantics as semantics

HERE=Path(__file__).resolve().parent


def canonical(value:Any)->str:
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))


def raw_hash(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_type(value:Any)->str:
    if value is None:return "null"
    if isinstance(value,bool):return "boolean"
    if isinstance(value,int):return "integer"
    if isinstance(value,str):return "string"
    if isinstance(value,list):return "array"
    if isinstance(value,dict):return "object"
    raise TypeError(type(value))


def schema_for_values(values:list[Any])->dict:
    groups={}
    for value in values:groups.setdefault(json_type(value),[]).append(value)
    if len(groups)>1:
        return {"oneOf":[schema_for_values(group) for _,group in sorted(groups.items())]}
    kind,group=next(iter(groups.items()))
    if kind in {"null","boolean","integer"}:return {"type":kind}
    if kind=="string":
        parsed=[]
        for value in group:
            try: decoded=json.loads(value)
            except (TypeError,json.JSONDecodeError): break
            if canonical(decoded)!=value: break
            parsed.append(decoded)
        else:
            return {"type":"string","contentMediaType":"application/json",
                    "x-canonical-json":True,"contentSchema":schema_for_values(parsed)}
        return {"type":"string"}
    if kind=="array":
        flat=[item for value in group for item in value]
        schema={"type":"array","minItems":min(map(len,group)),"maxItems":max(map(len,group))}
        schema["items"]=schema_for_values(flat) if flat else False
        return schema
    key_groups={}
    for value in group:key_groups.setdefault(tuple(sorted(value)),[]).append(value)
    variants=[]
    for keys,objects in sorted(key_groups.items()):
        variants.append({"type":"object","additionalProperties":False,
            "required":list(keys),"properties":{key:schema_for_values([x[key] for x in objects]) for key in keys}})
    return variants[0] if len(variants)==1 else {"oneOf":variants}


def output_row_schema(program:dict, output_rows:list[list[Any]]|None=None)->dict:
    scalar={
        "STRING":{"type":"string"},"INTEGER":{"type":"integer"},
        "BOOLEAN":{"type":"boolean"},"NULLABLE_STRING":{"type":["string","null"]},
        "CANONICAL_JSON":{"type":"string","contentMediaType":"application/json","x-canonical-json":True},
    }
    n=len(program["output_types"])
    prefix=[]
    for index,kind in enumerate(program["output_types"]):
        item=dict(scalar[kind])
        if output_rows is not None and kind=="CANONICAL_JSON":
            item["contentSchema"]=schema_for_values(
                [json.loads(row[index]) for row in output_rows])
        prefix.append(item)
    return {"type":"array","minItems":n,"maxItems":n,
            "prefixItems":prefix,"items":False}


def main()->None:
    inputs=json.loads((HERE/"REDUCER_INPUT_ROWS_RFC.json").read_text())
    programs=json.loads((HERE/"REDUCER_PROGRAMS_RFC.json").read_text())
    vector=json.loads((HERE/"VECTOR_FIXTURE_RFC.json").read_text())
    vendored=json.loads((HERE/"REDUCER_LAW_BINDINGS_RFC.json").read_text())
    vendored_by={x["law_id"]:x for x in vendored["laws"]}
    exact=json.loads((HERE/"REDUCER_EXACT_SOURCE_BINDINGS_RFC.json").read_text())
    exact_by={x["binding"]:x["pointer_value_sha256"] for x in exact["bindings"]}
    sources=semantics.load_sources()
    program_by={x["law_id"]:x for x in programs["programs"]}
    laws=[]
    for builder in inputs["builders"]:
        law_id=builder["law_id"];test_id="PPC5R9_"+law_id.split("_",1)[0]
        suite_id=law_id.split("_",1)[1].removesuffix("_V1")
        rows=semantics.rows_from_builder(builder,sources)
        row_schema=schema_for_values(rows)
        parameters=semantics.parameters_from_builder(builder,rows,sources)
        parameter_schema=schema_for_values([parameters])
        program=program_by[law_id]
        local_sources={sid:sources[sid] for sid in builder.get("source_ids",[])}
        output_rows=semantics.reduce_rows(program,rows,local_sources,parameters)
        laws.append({"law_id":law_id,"test_id":test_id,"suite_id":suite_id,
            "entry_count":len(rows),"input_vector_sha256":hashlib.sha256(canonical(rows).encode()).hexdigest(),
            "input_row_schema":row_schema,"parameter_schema":parameter_schema,
            "operator":program["operator"],"output_columns":program["output_columns"],
            "output_row_schema":output_row_schema(program,output_rows),
            "failure_precedence":vendored_by[law_id]["failure_precedence"],
            "source_ids":builder.get("source_ids",[]),
            "source_pointer_bindings":[{"binding":binding,
                "pointer_value_sha256":exact_by[binding]}
                for binding in [row["binding"] for row in vendored_by[law_id]["source_pointer_bindings"]]]})
    expected={(test,s["suite_id"]):s["entry_count"] for test,suites in vector["suite_vectors"].items() for s in suites}
    assert len(laws)==58
    assert {(x["test_id"],x["suite_id"]):x["entry_count"] for x in laws}==expected
    result={"document_kind":"PPC5R12_CLOSED_REDUCER_MACHINE_RFC",
        "lifecycle_state":"PROPOSAL_ONLY","authority_conferred":False,
        "materialization_permitted":False,"schema_dialect":"https://json-schema.org/draft/2020-12/schema",
        "executor_projection_ref":"VECTOR_FIXTURE_RFC.json#/executor_input_envelope",
        "case_identity":"facts-only SHA-256; expectations joined only after both executor outputs commit",
        "law_count":len(laws),"input_entry_count":sum(x["entry_count"] for x in laws),
        "source_files":{
            "input_rows":{"file":"REDUCER_INPUT_ROWS_RFC.json","sha256":raw_hash(HERE/"REDUCER_INPUT_ROWS_RFC.json")},
            "programs":{"file":"REDUCER_PROGRAMS_RFC.json","sha256":raw_hash(HERE/"REDUCER_PROGRAMS_RFC.json")},
            "source_snapshots":{"file":"REDUCER_SOURCE_SNAPSHOTS.json","sha256":raw_hash(HERE/"REDUCER_SOURCE_SNAPSHOTS.json")},
            "exact_source_bindings":{"file":"REDUCER_EXACT_SOURCE_BINDINGS_RFC.json","sha256":raw_hash(HERE/"REDUCER_EXACT_SOURCE_BINDINGS_RFC.json")},
            "vendored_law_bindings":{"file":"REDUCER_LAW_BINDINGS_RFC.json","sha256":raw_hash(HERE/"REDUCER_LAW_BINDINGS_RFC.json")},
            "local_source_inputs":{"file":"SOURCE_INPUT_MANIFEST_RFC.json","sha256":raw_hash(HERE/"SOURCE_INPUT_MANIFEST_RFC.json")},
            "executable_reducer":{"file":"validate_reducer_semantics.py","sha256":raw_hash(HERE/"validate_reducer_semantics.py")}},
        "laws":laws,
        "forbidden_executor_keys":["expected_output","expected_result","expected_first_failure","oracle_output","answer_key","branch_key","axis_values","mutation_descriptor","perturbation","reconstruction_kind"],
        "no_authority_notice":"This catalog defines proposal reducer bytes only. It is not a fixture universe, execution receipt, conformance result, architecture ratification, or run authority."}
    print(json.dumps(result,sort_keys=True,separators=(",",":"),ensure_ascii=False))


if __name__=="__main__":main()

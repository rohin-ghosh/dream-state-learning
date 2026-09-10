"""Fable-side reviewer mailbox transport (per notes/40 handoff).

This is TRANSPORT ONLY: request validation, hash verification, atomic
schema-validated response writing. The review content itself is produced
by a FRESH-context subagent spawned by the interactive Fable session
(the session itself is not fresh; per handoff clause 5 the fresh
subagent provides honest independence — this is disclosed in every
response's summary).

Usage (by the Fable session):
  python3 research_loop/fable_transport.py validate <request.json>
      -> prints a JSON contract summary (paths, hash check results,
         schema path) or exits nonzero with reasons.
  python3 research_loop/fable_transport.py respond <request.json> \
      <response-payload.json>
      -> validates payload against the request's response schema and
         writes .research_loop/handoffs/outbox/<request_id>.response.json
         atomically (tmp + rename). Never overwrites an existing response.

Hard rules encoded here (from the handoff):
  - no GPU work, no pushes, no lease operations from this path;
  - response JSON only — prose never used as a routing signal;
  - hash mismatches or missing files -> validation failure (the session
    should then respond with verdict "escalate", never guess).
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTBOX = os.path.join(ROOT, ".research_loop", "handoffs", "outbox")

REQUIRED_REQUEST_FIELDS = (
    "request_id", "run_id", "node_id", "prompt_path",
    "response_schema_path", "context_files", "autonomy_boundary",
)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_request(path):
    req = json.load(open(path))
    missing = [k for k in REQUIRED_REQUEST_FIELDS if k not in req]
    problems = [f"missing field: {k}" for k in missing]
    for p_key in ("prompt_path", "response_schema_path"):
        p = req.get(p_key)
        if p and not os.path.exists(os.path.join(ROOT, p)) \
                and not os.path.exists(p):
            problems.append(f"{p_key} not found: {p}")
    hash_results = {}
    for cf in req.get("context_files", []):
        p = cf.get("path", "")
        full = p if os.path.exists(p) else os.path.join(ROOT, p)
        if not os.path.exists(full):
            problems.append(f"context file missing: {p}")
            hash_results[p] = "MISSING"
            continue
        actual = sha256(full)
        want = cf.get("sha256", "")
        hash_results[p] = "OK" if actual == want else \
            f"MISMATCH (want {want[:12]}, got {actual[:12]})"
        if actual != want:
            problems.append(f"hash mismatch: {p}")
    return req, problems, hash_results


def validate_against_schema(payload, schema):
    """Minimal validator sufficient for review/result schemas:
    required keys, no additional properties, enum + primitive types."""
    errs = []
    props = schema.get("properties", {})
    for k in schema.get("required", []):
        if k not in payload:
            errs.append(f"missing required: {k}")
    if not schema.get("additionalProperties", True):
        for k in payload:
            if k not in props:
                errs.append(f"additional property not allowed: {k}")
    for k, v in payload.items():
        spec = props.get(k)
        if not spec:
            continue
        if "enum" in spec and v not in spec["enum"]:
            errs.append(f"{k}: {v!r} not in {spec['enum']}")
        t = spec.get("type")
        if t == "string" and not isinstance(v, str):
            errs.append(f"{k}: expected string")
        if t == "array" and not isinstance(v, list):
            errs.append(f"{k}: expected array")
        if t == "object" and not isinstance(v, dict):
            errs.append(f"{k}: expected object")
        if t == "array" and isinstance(v, list):
            item_t = spec.get("items", {}).get("type")
            if item_t == "string" and any(not isinstance(x, str) for x in v):
                errs.append(f"{k}: all items must be strings")
    return errs


def cmd_validate(req_path):
    req, problems, hashes = load_request(req_path)
    out = {"request_id": req.get("request_id"),
           "run_id": req.get("run_id"),
           "prompt_path": req.get("prompt_path"),
           "response_schema_path": req.get("response_schema_path"),
           "autonomy_boundary": req.get("autonomy_boundary"),
           "context_hash_results": hashes,
           "problems": problems,
           "ok": not problems}
    print(json.dumps(out, indent=1))
    return 0 if not problems else 2


def cmd_respond(req_path, payload_path):
    req, problems, _ = load_request(req_path)
    schema_p = req["response_schema_path"]
    schema_full = schema_p if os.path.exists(schema_p) \
        else os.path.join(ROOT, schema_p)
    schema = json.load(open(schema_full))
    payload = json.load(open(payload_path))
    errs = validate_against_schema(payload, schema)
    if errs:
        print(json.dumps({"ok": False, "schema_errors": errs}))
        return 3
    os.makedirs(OUTBOX, exist_ok=True)
    dest = os.path.join(OUTBOX, f"{req['request_id']}.response.json")
    if os.path.exists(dest):
        print(json.dumps({"ok": False,
                          "error": f"response already exists: {dest}"}))
        return 4
    fd, tmp = tempfile.mkstemp(dir=OUTBOX, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(payload, f, indent=1)
    os.rename(tmp, dest)
    print(json.dumps({"ok": True, "written": dest}))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "validate":
        sys.exit(cmd_validate(sys.argv[2]))
    if sys.argv[1] == "respond":
        sys.exit(cmd_respond(sys.argv[2], sys.argv[3]))
    print("unknown command")
    sys.exit(1)

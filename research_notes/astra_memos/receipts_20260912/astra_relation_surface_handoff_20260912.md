# EDIT-STOP — relation-surface diagnostic

Prepared for Main, 2026-09-12 17:12 UTC. Implementation is stopped.
Only repository edits: `organism_v6/relation_surface_diagnostic.py` (289 lines)
and `tests/test_relation_surface_diagnostic.py`. Original module and formation
are untouched. No Git operation, native preparation, GPU query/allocation,
GPU run, training, live world action, parent call, or child replacement performed.

## CPU results

- 9/9 new CPU fixture tests PASS; 37/37 existing RuleGame diagnostic tests PASS.
- Actual local sealed-formation `check` PASS (full deterministic provenance/world
  replay of existing evidence, not a new live rollout). Nine requests, output cap
  624, all temperature 0.0 / seed 20260912. Its stdout is preserved at
  `/tmp/astra_relation_surface_cpu_check_20260912.json`.
- Fixture tests cover exact links and prompts, no CPU-answer injection, 9/624,
  fresh roots/model pins, retained parse failures/native-like costs, generation
  and loader failures, failed cleanup, parent-loss owned-group signaling,
  signal-handler restoration, one supervisor invocation and no retry.
- Native tokenizer/model checks and all GPU execution remain Main's work.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_relation_surface_diagnostic.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_rulegame_parenting_diagnostic.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m organism_v6.relation_surface_diagnostic check --formation /tmp/astra_rulegame_v2_formation_terminal_20260912/astra_rulegame_interaction_v2_20260912_attempt1
```

## Exact fixed binding and interpretation

Record 0008 -> raw call 0007 -> P:rule0/astra-minimum-20260912/lesson0/apply#t1:
`PREDICT: F\nACT: TRY 2,3,4`, world True, prediction false.
Record 0010 -> raw call 0009 -> same episode #t2:
`PREDICT: T\nACT: TRY 1,2,3`, world True, prediction true.
Record 0012 -> raw call 0011 -> same episode #t3:
`ACT: TRY 0,1,2`, world True, prediction absent/null.

Each case runs original/fullclarified/tokenclarified, in that order, caps
100/100/8. Original prompt bytes remain unchanged. Fullclarified appends one
case-independent mapping. Tokenclarified retains the exact original prefix
(emitted text/world/observed fields) and replaces the JSON instruction with the
same mapping plus token-only instruction. No expected answer enters a prompt.
Expected answers are computed only in CPU reduction.

Original formation comparisons change temperature .7 -> .0 AND seed.
Fullclarified vs original tests explicit definition with JSON format held fixed
at .0. Token contrast also changes format and output cap. These are three
positive-observation events from one life, not a base ceiling or evidence of
general Boolean ability. No new scientific claim or formal approval gate.

## Main-only native commands

Main must first populate a **fresh immutable source snapshot** with the two
assigned files plus the existing dependencies; do not edit the old native
source snapshot or original formation. The SOURCE below is the proposed new
snapshot location, not a directory created by this worker. Main owns transfer,
Git operations, source provenance, reservation and lease checks.

Run on the native host from that new snapshot. The Python path is taken from
the sealed formation launch receipt. Lease end comes from the existing sealed
plan (2026-09-25 21:03 UTC); this is NOT authorization to lease or extend anything.
Main must confirm it still describes the actual lease before prepare/run.

```bash
set -euo pipefail
SOURCE="$HOME/astra_sources/astra_relation_surface_20260912_attempt1"
FORMATION="$HOME/astra_diagnostics/astra_rulegame_interaction_v2_20260912_attempt1"
ROOT="$HOME/astra_diagnostics/astra_relation_surface_20260912_attempt1"
PY=/localhome/local-rohing/v2/venv/bin/python
test -f "$SOURCE/organism_v6/relation_surface_diagnostic.py"
test -f "$SOURCE/tests/test_relation_surface_diagnostic.py"
cd -- "$SOURCE"
export PYTHONPATH="$SOURCE" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export V6_MODEL="$(jq -r .model "$FORMATION/plan.json")"
LEASE_END="$($PY -B -c 'from datetime import datetime,timezone; import json,sys; print(datetime.fromtimestamp(json.load(open(sys.argv[1]))["lease_end"],timezone.utc).isoformat())' "$FORMATION/plan.json")"

"$PY" -B -m unittest discover -s "$SOURCE/tests" -p 'test_relation_surface_diagnostic.py' -v
"$PY" -B -m organism_v6.relation_surface_diagnostic check --formation "$FORMATION"
test ! -e "$ROOT"
"$PY" -B -m organism_v6.relation_surface_diagnostic prepare --formation "$FORMATION" --out "$ROOT" --device 0 --lease-end "$LEASE_END"

```

Only after Main confirms vacancy and allocates GPU0, in the same shell:

```bash
"$PY" -B -m organism_v6.relation_surface_diagnostic run --root "$ROOT" --allow-gpu
"$PY" -B -m organism_v6.relation_surface_diagnostic reduce --root "$ROOT"
```

Preparation hashes local model files against formation pins, performs native
token/text audit of sealed source calls, checks all new prompt lengths, and pins
current source bytes and exact requests in a fresh root. Model origin remains
local-byte pinning, not external base authentication. Do not edit pinned source
after prepare. No stage retries or automatic extra seeds/requests.

Run reuses existing `NativeBackend`, `supervise`, and `close_backend` behavior:
one worker, maximum 600s worker window, existing 180s load / 120s pending-call
timeouts and owned cleanup reserve/grace. Cleanup time is additional to the
600s worker limit and accounted in the supervision receipt. Parent/lease/deadline
watch signals only the worker's owned group. A failed run leaves artifacts and
an unusable run directory; unverified cleanup never permits reservation release.

Reduction audits the sealed new raw capture, identity, receipt hashes, order,
native token IDs/text and output bounds; retains raw unparseable text with null
mapped answer and a flag. Full JSON record faithfulness is separately reported.
Raw sampling parameters/input/output IDs are under `run/data/calls`; cost is
actual native input/output tokens, generation seconds and supervised elapsed
seconds. Dollar cost is explicitly unavailable without billing-rate evidence.
Results: `reduction.json`; cleanup: `run/data/backend.cleanup.json` and
`run/worker/supervision.json`. Do not treat a parsed relation as full-record
faithfulness or an unparseable result as missing data.

## Byte pins at handoff

- Implementation SHA256: `497a1121e89f7214436b6a5b58a566f05f62f3af3e4225edad1e02fee44db8df`
- Tests SHA256: `8afc9e6937ad2757ad44087b803421b39ac8cee885006cc5944730dfdf4a76dd`
- Formation manifest SHA256: `4fef2770a6be151bc00fc4782575134643f8754b2cd149380b48a4aaf6dfed41`
- Formation plan SHA256: `5cc110bceb6e92186bc707fdd4369eaf53690a4fba694ac1fa5b8b8dbfcc88f7`

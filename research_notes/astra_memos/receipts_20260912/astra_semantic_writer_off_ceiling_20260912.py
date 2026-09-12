import collections
import json
import math
from pathlib import Path
import statistics

from organism_v6 import semantic_writer_diagnostic as diagnostic

prepared = Path("/tmp/astra_semantic_writer_prepared_20260912/astra_semantic_writer_Q0_20260912_attempt1")
raw = Path("/tmp/astra_semantic_writer_off_20260912/stages/off_score/raw")
material = diagnostic.read_json(prepared / "material.json")
requests = diagnostic.read_json(prepared / "requests.json")
groups = collections.defaultdict(list)
for request in requests:
    audit = request["audit"]
    if request["state"] != "OFF" or request["operation"] != "score" or audit["family"] != "primary":
        continue
    record = diagnostic.read_json(raw / (request["request_id"] + ".json"))
    assert record["request_sha256"] == diagnostic.w0.digest(request)
    scores = diagnostic.score_sums(request, record["output"])
    row = material["roots"][audit["probe_root"]]["held"][audit["index"]]
    for mapping in diagnostic.w0.MAPS:
        target = diagnostic.w0.action(audit["probe_root"], row["slot"], row["mode"], mapping)
        logq = diagnostic.w0.log_q(scores, target)
        assert math.isfinite(logq) and logq <= 0
        groups[(audit["probe_root"], mapping, row["slot"], row["mode"])].append(-logq)
cells = collections.defaultdict(list)
for (root, mapping, slot, mode), values in sorted(groups.items()):
    assert len(values) == 4
    upper = statistics.median(values)
    cells[f"{root}/{mapping}"].append(dict(slot=slot, mode=mode,
        per_template_gain_upper_bounds=values, median_gain_upper_bound=upper,
        necessary_half_nat_feasibility=upper >= .5))
result = dict(kind="POST_OFF_MATHEMATICAL_FEASIBILITY_DIAGNOSTIC_NOT_GATE_CHANGE",
    derivation="log q_ON <= 0; hence each gain <= -log q_OFF, and median preserves this order",
    recorded_threshold=.5, cells=dict(cells),
    infeasible_keys={cell:sum(not key["necessary_half_nat_feasibility"] for key in keys) for cell,keys in cells.items()},
    total_keys=len(groups), treatment_outcomes_used=False,
    interpretation="If infeasible, failure of that gain conjunction cannot identify an ineffective writer. Preserve all original outcomes and gates.")
print(json.dumps(result, indent=2, sort_keys=True))

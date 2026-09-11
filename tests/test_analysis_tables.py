import json
import os

from organism_v6.analysis_tables import same_panel_gate_replicates


def _write(path, value):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(value, fh)


def test_gate_replicates_ignore_base_and_disjoint_panels(tmp_path):
    life = str(tmp_path)
    on = {32: {"mean": 0.5, "results": {"report-a": 0.5}},
          64: {"mean": 0.4, "results": {"report-a": 0.4}}}
    _write(os.path.join(life, "probe_gate_base.json"),
           {"mean": 0.2, "results": {"gate-a": 0.2}})
    _write(os.path.join(life, "probe_gate0032.json"),
           {"mean": 0.6, "results": {"gate-a": 0.6}})
    _write(os.path.join(life, "probe_gate0064.json"),
           {"mean": 0.45, "results": {"report-a": 0.45}})
    for episode in (32, 64):
        done = os.path.join(life, f"sleep_{episode:04d}", "adapter", "DONE")
        os.makedirs(os.path.dirname(done), exist_ok=True)
        open(done, "w").close()
    assert same_panel_gate_replicates(life, on) == [0.04999999999999999]


def test_gate_replicate_requires_committed_adapter(tmp_path):
    life = str(tmp_path)
    on = {32: {"mean": 0.5, "results": {"a": 0.5}}}
    _write(os.path.join(life, "probe_gate0032.json"),
           {"mean": 0.6, "results": {"a": 0.6}})
    assert same_panel_gate_replicates(life, on) == []

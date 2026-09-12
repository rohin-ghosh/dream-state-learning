import datetime
import json
from pathlib import Path

from organism_v6 import semantic_writer_diagnostic as diagnostic

home = Path.home()
source = Path(diagnostic.__file__).resolve().parents[1]
carrier = home / "astra_diagnostics/astra_semantic_carrier_20260912_attempt1"
old = diagnostic.read_json(carrier / "manifest.json")["config"]
proof = diagnostic.proof_template()
proof.update(verified_by_main=True,
    verification_reference="SEQ080, 7a823dbe; original-source replay and independent157-file raw audit",
    model_sha256=old["model_sha256"], tokenizer_sha256=old["tokenizer_sha256"],
    output_path=str(carrier / "report.json"), output_sha256=diagnostic.w0.file_hash(carrier / "report.json"))
proof_path = Path("/tmp/astra_semantic_writer_carrier_proof_20260912.json")
with proof_path.open("x") as stream:
    json.dump(proof, stream, indent=2, sort_keys=True)
    stream.write("\n")
config = diagnostic.config_template()
config.update({key: old[key] for key in config if key in old})
protocol = source / "research_notes/astra_memos/ASTRA_SEMANTIC_WRITER_COMPARISON_2026-09-12.md"
config.update(requested_scope=diagnostic.config_template()["requested_scope"],
    approved_intake="Rohin standing authorization and simple-hygiene directive; prospective semantic Q0 protocol7a823dbe",
    builder_preflight_reference="COORDINATION 2026-09-12 13:06UTC; native preparation and Main review before launch",
    protocol_path=str(protocol), protocol_sha256=diagnostic.w0.file_hash(protocol),
    carrier_proof_path=str(proof_path), carrier_proof_sha256=diagnostic.w0.file_hash(proof_path),
    deadline_unix=datetime.datetime(2026, 9, 12, 16, 30, tzinfo=datetime.timezone.utc).timestamp())
config_path = Path("/tmp/astra_semantic_writer_config_20260912.json")
with config_path.open("x") as stream:
    json.dump(config, stream, indent=2, sort_keys=True)
    stream.write("\n")
result = diagnostic.prepare(home / "astra_diagnostics/astra_semantic_writer_Q0_20260912_attempt1", config)
print(json.dumps(result, sort_keys=True))

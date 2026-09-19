"""Reconcile existing predecessor publications without modifying their ledgers."""

from collections import Counter
import json
from pathlib import Path
import subprocess

import observe


def validate_delivery(result, delivered, result_sha):
    observe.require(delivered["result_sha256"] == result_sha, "delivered_result_hash")
    observe.require(delivered["inbox_id"] == result["inbox_publication"]["id"], "delivered_publication_id")
    observe.require(delivered["status"] == "COMPLETE", "delivery_receipt_complete")


def main():
    audit_path = observe.SPRINT / "parenting/c2_refinement/SOURCE_AUDIT.json"
    audit = json.loads(observe.read(audit_path))
    source_path = observe.SESSION / "parent/parent_000000/SOURCE.json"
    source = json.loads(observe.read(source_path))
    ledgers, targets = [], []
    for ledger in audit["ledgers"]:
        output = Path(ledger["output"])
        counts, attempts = Counter(), []
        for directory in sorted(output.glob("parent_[0-9]*")):
            result_path = directory / "RESULT.json"
            row = {"attempt": directory.name, "result": None, "delivered": None}
            counts["attempts"] += 1
            if not result_path.exists():
                counts["RESULT_ABSENT"] += 1
                attempts.append(row)
                continue
            result = json.loads(observe.read(result_path))
            row["result"] = observe.receipt(result_path)
            row["status"] = result.get("status", "UNKNOWN")
            row["error_type"] = result.get("error_type")
            counts[row["status"]] += 1
            publication = result.get("inbox_publication")
            if publication:
                row["publication"] = publication
            delivered_path = directory / "DELIVERED.json"
            if delivered_path.exists():
                delivered = json.loads(observe.read(delivered_path))
                validate_delivery(result, delivered, row["result"]["sha256"])
                row["delivered"] = observe.receipt(delivered_path)
                row["consumption"] = delivered["consumption"]
                counts["DELIVERED_RECEIPT_MATCHED"] += 1
            elif row["status"] == "PUBLISHED":
                counts["PUBLISHED_WITHOUT_DELIVERED_FILE"] += 1
            attempts.append(row)
        ledgers.append({"output": ledger["output"], "counts": dict(counts), "attempts": attempts,
                        "all_consumptions_remote_verified": False})
        for pending in ledger["pending"]:
            row = next(row for row in attempts if row["attempt"] == pending["attempt"])
            observe.require(row["result"]["sha256"] == pending["result_sha256"], "original_pending_result_hash")
            consumption = source["consumed_inbox"].get(pending["inbox_id"])
            targets.append({"attempt": row["attempt"], "output": ledger["output"], "publication": row["publication"],
                            "result": row["result"], "delivered": row["delivered"], "snapshot_consumption": consumption})
    last = ledgers[0]["attempts"][-1]
    targets.append({"attempt": last["attempt"], "output": ledgers[0]["output"], "publication": last["publication"],
                    "result": last["result"], "delivered": last["delivered"], "snapshot_consumption": last["consumption"]})
    observe.require(len(targets) <= 8 and all(row["snapshot_consumption"] for row in targets), "bounded_known_receipts_only")
    manifest = json.loads(observe.read(observe.SESSION / "MANIFEST.json"))
    config = json.loads(observe.read(observe.COLLECTOR / "private/CONFIG.json"))
    target = next(entry["binding"] for entry in config["entries"] if entry["label"] == "C2")
    local = observe.binding()
    code = "\n".join(observe.read(path).decode() for path in (observe.COLLECTOR / "contract/reader.py", observe.COLLECTOR / "remote.py"))
    code += "\nimport sys\n"
    code += "for filename, expected in " + repr(manifest["remote_helper_sha256"]) + ".items():\n"
    code += "    assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == expected, 'original_helper_hash'\n"
    code += "sys.path.insert(0, " + repr(manifest["remote_operator"]) + ")\nfrom checkpoint_tail_parent_binding import verify\n"
    code += "native = verify(" + repr(local["native_binding_path"]) + ", " + repr(local["native_binding_sha256"]) + ")\n"
    code += "target = " + repr(target) + "\nbefore = identity(target)\nverified_rows = []\n"
    code += "for item in " + repr(targets) + ":\n"
    code += "    reference = item['snapshot_consumption']\n"
    code += "    row, proof = verified(Path(target['root']) / 'stream/records' / ('%020d.json' % reference['record_index']), target['journal_id'])\n"
    code += "    document = row['document']\n"
    code += "    assert row['kind'] == 'INBOX' and row['sha256'] == reference['record_sha256'], 'original_INBOX_receipt'\n"
    code += "    assert document['message']['id'] == item['publication']['id'] and document['source_sha256'] == item['publication']['sha256'], 'original_publication_id_and_sha'\n"
    code += "    assert document['message']['actor'] == 'parent' and document['message']['speaker'] == 'Astra', 'actual_Astra_INBOX'\n"
    code += "    verified_rows.append(dict(publication=item['publication'], record=proof, document_sha256=digest(document), actor=document['message']['actor'], speaker=document['message']['speaker']))\n"
    code += "assert identity(target) == before, 'native_epoch_changed'\n"
    code += "print(json.dumps(dict(native=native, identity=before, verified_rows=verified_rows)))\n"
    result = subprocess.run(["bash", str(observe.ROOT / "gpu/ovx3_ssh.sh"), "CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B -"],
                            input=code, text=True, capture_output=True, timeout=240, check=True)
    observe.require(len(result.stdout) < observe.LIMIT, "bounded_receipts")
    remote = json.loads(result.stdout)
    document = {"schema": "c2_predecessor_read_only_reconciliation_v1", "observed_utc": observe.utc(),
                "source_audit": observe.receipt(audit_path), "published_snapshot": observe.receipt(source_path),
                "ledgers": ledgers, "targeted_pending_or_last_publications": targets, "remote": remote,
                "older_boundary": audit["older_boundary"], "whole_life_totals_known": False,
                "status": "TARGETED_ORIGINAL_INBOX_RECORDS_VERIFIED_WITHOUT_LEDGER_MUTATION",
                "replay_authorized": False, "original_ledger_writes": 0, "native_writes": 0, "signals": 0, "provider_calls": 0,
                "limitations": ["INBOX consumption is not proof of subsequent request visibility or action uptake.",
                                "Only the identified pending IDs and handoff-last publication were re-read remotely.",
                                "Two historical DELIVERED.json files remain absent; this sidecar does not create them.",
                                "PARENT13 and earlier whole-life history remain not fully audited."]}
    observe.save("PREDECESSOR_RECONCILIATION.json", document)


if __name__ == "__main__":
    main()

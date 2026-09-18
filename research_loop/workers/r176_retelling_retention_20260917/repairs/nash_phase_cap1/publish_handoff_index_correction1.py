"""Append-only correction of public receipt indexing, not candidate or proof bytes."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys


WORKER = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKER))
import preparation_io as common


def main():
    previous = WORKER / 'NASH_I1_REPAIR_READY_20260917T1748Z.json'
    raw = previous.read_bytes()
    document = json.loads(raw)
    for phase in document['phases']:
        phase['remote_receipt']['path'] = str(Path(phase['read_ledger_path']).parents[1] / 'PUBLIC_METADATA.json')
    document['public_index_correction'] = dict(
        previous=dict(path=str(previous), sha256=common.sha(raw)), observed_utc=datetime.now(timezone.utc).isoformat(),
        changed_fields_only='phases[].remote_receipt.path: correct parent depth to per-proof cell root',
        candidate_config_source_proof_and_ledger_bytes_unchanged=True,
        previous_incorrect_index_preserved=True, additional_remote_reads=0)
    target = WORKER / 'NASH_I1_REPAIR_READY_INDEX2_20260917.json'
    reference = common.write(target, document)
    markdown = (WORKER / 'NASH_I1_REPAIR_READY_20260917T1748Z.md').read_text()
    markdown = markdown.replace('NASH_I1_REPAIR_READY_20260917T1748Z.json', target.name)
    markdown += '\nAppend-only public index correction: per-proof remote receipt paths now use their cell root. '
    markdown += 'Prior index is preserved; candidate pins, actual CPU proof, per-read ledgers and budgets are unchanged.\n'
    common.write(WORKER / 'NASH_I1_REPAIR_READY_INDEX2_20260917.md', markdown.encode())
    print(json.dumps(reference, sort_keys=True))


if __name__ == '__main__':
    main()

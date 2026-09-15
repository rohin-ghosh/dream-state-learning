"""Receive bound packets on the node; no raw VM artifact output."""

import argparse
import base64
import json
from pathlib import Path
import sys
import time

from gpu import orch_combined_l1_continual_sampled as sampled
from gpu import orch_combined_l1_continual_run as run
from gpu.orch_combined_l1_continual_guard import take_batch
from organism_v6 import orch_combined_l1_continual as policy


def receive(root, envelope, native_validator=None):
    packet = envelope['packet']
    exclusions = envelope['exclusions']
    sampled.validate_packet(packet, exclusions)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(run.read(root / 'PREPARE.json')['model_dir'], local_files_only=True)
    encoded = (native_validator or sampled.native_check)(packet, exclusions, tokenizer)
    state = policy.initial_state(run.read(root / 'PACKET/ADMITTED_ROWS.json'), run.combined.MANIFEST_SHA)
    state = take_batch(root, state)
    for pending in sorted((root / 'SAMPLED_EXTRA_PENDING').glob('*/BOUND_PACKET.json')):
        state = sampled.append(state, run.read(pending), run.read(pending.parent / 'EXCLUSIONS.json'))
    expanded = sampled.append(state, packet, exclusions)
    folder = root / 'SAMPLED_EXTRA_PENDING' / packet['batch_id']
    folder.mkdir(parents=True, exist_ok=False)
    for name, key in (('MANIFEST.json', 'manifest_bytes'), ('ROWS.json', 'rows_bytes')):
        with (folder / name).open('xb') as stream:
            stream.write(base64.b64decode(envelope[key]))
    assert run.sha(folder / 'MANIFEST.json') == packet['provenance']['manifest_sha256']
    assert run.sha(folder / 'ROWS.json') == packet['provenance']['rows_file_sha256']
    run.write(folder / 'BOUND_PACKET.json', packet)
    run.write(folder / 'EXCLUSIONS.json', exclusions)
    receipt = dict(status='PASS', packet_sha256=run.sha(folder / 'BOUND_PACKET.json'),
        manifest_sha256=run.sha(folder / 'MANIFEST.json'), rows_sha256=run.sha(folder / 'ROWS.json'),
        exclusions_sha256=run.sha(folder / 'EXCLUSIONS.json'), native_calls=0, model_loaded=False,
        native_mechanical_replayed=64, accepted=len(packet['rows']), added=expanded['ingested'][-1]['added'],
        rows_after=len(expanded['rows']), maximum_sequence=max(len(row.input_ids) for row in encoded),
        native_context_limit=2048, exact_exported_inputs_labels=True,
        individual_reviewed=sum(entry['row']['review'] is not None for entry in packet['rows']),
        individual_unreviewed=sum(entry['row']['review'] is None for entry in packet['rows']),
        queued_not_training=True, finished_unix=time.time(), remote_path=str(folder))
    run.write(folder / 'CPU_BOUND.json', receipt)
    run.write(folder / 'NATIVE_ENCODER.json', receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    options = parser.parse_args()
    receive(options.root, json.load(sys.stdin))

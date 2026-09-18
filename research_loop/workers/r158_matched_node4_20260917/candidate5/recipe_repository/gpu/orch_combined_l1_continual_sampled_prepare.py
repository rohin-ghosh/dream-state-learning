"""CPU-only native-tokenizer proof before a checkpoint-preserving source upgrade."""

import argparse
from pathlib import Path
import time

from gpu import orch_combined_l1_continual_sampled as sampled
from gpu import orch_combined_l1_continual_run as run
from organism_v6 import orch_combined_l1_continual as policy


def check(root, packet_folder):
    import os
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    from transformers import AutoTokenizer
    prepared = run.read(root / 'PREPARE.json')
    tokenizer = AutoTokenizer.from_pretrained(prepared['model_dir'], local_files_only=True)
    packet = run.read(packet_folder / 'BOUND_PACKET.json')
    exclusions = run.read(packet_folder / 'EXCLUSIONS.json')
    checked = sampled.native_check(packet, exclusions, tokenizer)
    state = run.read(root / 'CORPORA/000002.json')
    expanded = sampled.append(state, packet, exclusions)
    assert len(state['rows']) == 2943 and len(expanded['rows']) == 3007
    encoded = run.encode_corpus(expanded['rows'], tokenizer, {})
    assert tuple(encoded[-64:]) == tuple(checked)
    old = run.legacy_encode(root, tokenizer)
    assert len(old) == 222
    layout = policy.ContinualLayout(len(encoded), 2)
    all_rows = run.native.assemble_replay(old, encoded, layout, legacy_reference=old,
                                         eos_token_id=tokenizer.eos_token_id)
    for update in range(1, layout.trajectory_rows + 1):
        indexes, full, reference, active, unused = run.native.training_batch(all_rows, layout, update,
            pad_id=tokenizer.pad_token_id, replay_arm='FULL_TARGET')
        off_indexes, off, off_reference, off_active, unused = run.native.training_batch(all_rows, layout, update,
            pad_id=tokenizer.pad_token_id, replay_arm='NEW_TRAJECTORY_LOSS_OFF')
        assert indexes == off_indexes and full['input_ids'] == off['input_ids']
        assert reference == off_reference and 0 < off_active <= active
        for index, before, after in zip(indexes, full['labels'], off['labels']):
            assert before == after if index < 222 else all(label == -100 for label in after)
    run.write(packet_folder / 'NATIVE_ENCODER.json', dict(status='PASS', native_calls=0,
        model_loaded=False, packet_sha256=run.sha(packet_folder / 'BOUND_PACKET.json'),
        source_policy_sha256=sampled.POLICY_SHA, wrapper_sha256=sampled.WRAPPER_SHA,
        native_mechanical_replayed=64, rows=len(encoded), legacy_rows=len(old),
        supervised_new_tokens=sum(len(row.target_ids) for row in checked),
        maximum_added_sequence=max(len(row.input_ids) for row in checked),
        native_context_limit=2048, exact_exported_inputs_labels=True, old_masks_preserved=True,
        unsampled_individual_status='UNREVIEWED', finished_unix=time.time(),
        expanded_corpus_sha256=policy.digest(expanded)))
    print('PASS: native64 source replay, whole3007 encoding, legacy222 and FULL/OFF masks')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--packet-folder', type=Path, required=True)
    options = parser.parse_args()
    check(options.root, options.packet_folder)

"""CPU-only validation of the recorded LONG boundary with the actual tokenizer."""

from dataclasses import asdict
from pathlib import Path
import tempfile

from gpu import orch_l2_shared_run as run
from gpu.orch_l2_long_hook import build_parent
from organism_v6 import orch_full_rich as rich
from organism_v6 import orch_l2_guided as guided
from organism_v6 import orch_l2_shared as shared


def check(root):
    prepared = run.source.read(root / 'PREPARE.json')
    tokenizer = run.source.native.load_local_tokenizer(prepared['model_dir'])
    identity, unused = run.input_identity(root, 'LONG', 1, 'experience')
    worlds = run.source.read(root / 'COHORT.json')['train'][0]
    output = root / 'LONG/cycle1/experience'
    records = run.continuation_records(root, 'LONG', 1, output, identity, worlds)
    originals = {str(path): run.bridge.file_sha256(path) for path in output.glob('*.json')}
    ledgers = {str(path): run.bridge.file_sha256(path) for path in root.glob('CALLS*LONG.jsonl')}
    encoded = run.legacy_encode(root, tokenizer)
    with tempfile.TemporaryDirectory(prefix='orch_l2_shared_cpu_') as directory:
        transport = run.RecordedParentTransport(root, 'LONG', 1, lambda label: None, Path(directory))
        hook = build_parent(root=root, cycle=1, tokenizer=tokenizer, transport=transport, emit=lambda event: None)
        completed = []
        for record in records:
            run.restore_parent_episode(hook, record, guided.learner_telemetry(completed, 1))
            completed.append(record)
            candidates = [capture for capture in record['captures']
                if rich.row_gate(record, capture)['eligible_for_semantic_review']]
            if candidates:
                transport(dict(kind='semantic', episode=record,
                    candidates=[dict(capture_sha256=rich.digest(capture),
                        raw_sha256=rich.digest(capture['response']['raw']), capture=capture) for capture in candidates],
                    rubric=list(rich.RUBRIC)))
        run.source.require(transport.position == 2 and hook.parent.decisions[1] == 1,
                           'restored_completed_parent_count_drift')
        task = shared.tasks(worlds[2])[0]
        transport.restoring = False
        response = hook(dict(kind='coach', turn=0, task=task,
            public_messages=[dict(role='system', content=rich.SYSTEM), dict(role='user',
                content=rich.readout.display(task['node'], task, list(task['ports'])))],
            prior_parent_messages=[], learner=guided.learner_telemetry(completed, 1)))
        run.source.require(transport.position == 3 and hook.parent.decisions[1] == 2
                           and hook.parent.exposures[1] == 1, 'pending_reserved_parent_count_drift')
        run.source.require(all(run.bridge.file_sha256(Path(path)) == digest
            for path, digest in {**originals, **ledgers}.items()), 'cpu_recovery_originals_changed')
        return dict(status='PASS', cpu_only=True, model_calls=0, provider_calls=0, updates=0,
            original_files=originals, ledgers=ledgers, completed_episodes=4, recorded_child_calls=16,
            next_episode_index=4, next_turn=0, decisions_after_pending_recovery=hook.parent.decisions[1],
            pending_parent_message_tokens=len(tokenizer.encode(response['message'], add_special_tokens=False)),
            pending_message_sha256=rich.digest(response['message']), delivered_to_child=False,
            legacy_mask_sha256=rich.digest([asdict(row) for row in encoded]), legacy_rows=len(encoded),
            frozen_interface_sha256=run.bridge.file_sha256(Path(__file__).resolve().parents[1]
                / 'research_notes/analysis/orch_l2_shared_20260914_interface.md'),
            deadline=float((root / 'DEADLINE').read_text()))


if __name__ == '__main__':
    run.write(run.ROOT / 'CPU_CONTINUATION_V5.json', check(run.ROOT))

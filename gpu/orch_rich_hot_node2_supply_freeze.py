"""Freeze the new supply queue without modifying the original native source."""

import hashlib
import json
from pathlib import Path
import shutil
import tarfile

from gpu.orch_rich_hot_node2_export import durable, wire
from organism_v6 import orch_rich_hot_node2_supply as policy


ORIGINAL = Path('research_notes/analysis/orch_rich_hot_node2_20260915_attempt1')
ROOT = ORIGINAL / 'continuation_prep'
NEW_FILES = ('gpu/orch_rich_hot_node2_continue.py', 'gpu/orch_rich_hot_node2_export.py',
             'organism_v6/orch_rich_hot_node2_supply.py', 'gpu/orch_rich_hot_node2_supply_freeze.py',
             'tests/test_orch_rich_hot_node2_supply.py', 'tests/test_orch_rich_hot_node2_export.py')
REUSED = ('organism_v6/experienced_event_two_hop.py', 'organism_v6/orch_full_rich.py',
          'organism_v6/orch_persist_code.py', 'organism_v6/orch_code_bounded.py',
          'organism_v6/orch_rich_hot_node2.py', 'gpu/orch_rich_hot_node2_run.py')


def freeze():
    ROOT.mkdir(exist_ok=False)
    shutil.copytree(ORIGINAL / 'source', ROOT / 'source')
    for name in REUSED:
        if Path(name).read_bytes() != (ROOT / 'source' / name).read_bytes():
            raise ValueError('reused_source_changed_since_original:' + name)
    for name in NEW_FILES:
        target = ROOT / 'source' / name
        target.parent.mkdir(exist_ok=True, parents=True)
        shutil.copyfile(name, target)
    prior = json.loads((ORIGINAL / 'TASKS.json').read_text())
    records = [json.loads(line) for line in (ORIGINAL / 'gsm8k_train.jsonl').read_text().splitlines()]
    document = policy.cohort(records, prior)
    for name in ('INITIAL.json', 'SERVICE_IDENTITY.json', 'gsm8k_train.jsonl'):
        shutil.copyfile(ORIGINAL / name, ROOT / name)
    shutil.copyfile(ORIGINAL / 'initial_native/LIFETIME.json', ROOT / 'LIFETIME.json')
    durable(ROOT / 'TASKS.json', wire(document))
    provenance = dict(original_root=str(ORIGINAL), original_tasks_sha256=hashlib.sha256((ORIGINAL / 'TASKS.json').read_bytes()).hexdigest(),
        original_provenance_sha256=hashlib.sha256((ORIGINAL / 'DATA_PROVENANCE.json').read_bytes()).hexdigest(),
        cached_math_source_sha256=hashlib.sha256((ROOT / 'gsm8k_train.jsonl').read_bytes()).hexdigest(),
        reused_sources={name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in REUSED},
        code_source='Existing64 L1 integer-ledger-pipelines-v1 tasks, explicit TRAIN reuse, not new unique tasks.',
        route_source='Existing four-edge two-hop generator in new isolated TRAIN namespaces; no held worlds or teacher targets.',
        math_exclusion='Original98known roster union plus all1024 initial-hot tasks; no full-census/pretraining guarantee.',
        source_repeats='Pools cycle under fixed cursor; repeated source_task_id retained, no novelty inflation.',
        no_held_access=True, parent_calls=0, fits=0, semantic_admission=False)
    durable(ROOT / 'DATA_PROVENANCE.json', wire(provenance))
    durable(ROOT / 'PROTOCOL.md', (
        '# RICH_HOT_NODE2 continuous mixed TRAIN supply — Rohin96\n\n'
        'Original source/processes/call cap remain immutable. Queue waits for original all8 terminals, '
        'AFTER states, zero unresolved reservations and privileged release before fresh privileged '
        'UUID/proc/CVD/open-device admission. No GPU while waiting. Original all8 lock reused.\n\n'
        'Inherit exact03:19:30 start /19:14:30 dispatch cutoff /19:19:30 hard end September15 '
        'and128 assigned GPU-hour ceiling. No clock or original6144call reset. Prospective additional '
        '65536calls total /8192per shard maximum (combined71680upper bound), reserved durably before '
        'dispatch; at most256 cursor batches of24common tasks,12per parity shard. No replay/retry. '
        'No dispatch after owned STOP_AFTER_CALL.json or deadline; finite exact-identity guardian.\n\n'
        'Each shard gets4math/4code/4route tasks per cursor batch.1024fresh known-excluded math tasks; '
        '64existing L1 bounded ledger tasks;256new TRAIN four-edge route worlds. Explicit repeated '
        'source identities when pools cycle, no unique-task inflation. Four styles remain paired: '
        'ORIGINAL_RICH/LIGHT_BRANCH/TWO_PASS/META_EVALUATE. Math/code two-pass conditions use only '
        'own prior response, no feedback. Route uses actual own scheduled exposures and two real '
        'goal episodes; all styles one environment action per turn, branching guidance for nonoriginal. '
        'Route TWO_PASS/META labels are style allocations, NOT matched two-call math treatments.\n\n'
        'Every native call8192max_new_tokens/16384total context, no forced minimum length, no cropping '
        'or prose-salvage. Existing strict numeric/JSON/route verifiers unchanged. Source exposures '
        'have their existing exact action/EVENT format, not claimed rich reasoning targets. Bounded '
        'code interpreter only; no arbitrary generated-code execution. Exact own messages/raw/tokens '
        'and actual verifier/episode outcomes preserved separately. No teacher/parent/API, held inputs, '
        'fit or automatic semantic admission. UNREVIEWED/not trainable; Main owns parallel sampled '
        'review, and sampled PASS does not certify unreviewed rows. No learning/transfer claim.\n\n'
        'Immutable raw manifests publish every60sec, environment evidence has separate content-hashed '
        'manifests. Per-batch mounted adapter check and terminal readonly base/state verification. '
        'Safety gates/call/window termination are operational bounds, not a one-cohort research stop.\n'
    ).encode())
    with tarfile.open(ROOT / 'source.tar', 'w') as archive:
        for path in sorted((ROOT / 'source').rglob('*.py')):
            archive.add(path, arcname=str(path.relative_to(ROOT / 'source')), recursive=False)
    durable(ROOT / 'LOCAL_FREEZE.json', wire(dict(
        source_sha256=hashlib.sha256((ROOT / 'source.tar').read_bytes()).hexdigest(),
        tasks_sha256=hashlib.sha256((ROOT / 'TASKS.json').read_bytes()).hexdigest(),
        lifetime_sha256=hashlib.sha256((ROOT / 'LIFETIME.json').read_bytes()).hexdigest(),
        math_tasks=len(document['math']['tasks']), code_tasks=len(document['code']), route_worlds=len(document['route']))))
    print((ROOT / 'LOCAL_FREEZE.json').read_text())


if __name__ == '__main__':
    freeze()

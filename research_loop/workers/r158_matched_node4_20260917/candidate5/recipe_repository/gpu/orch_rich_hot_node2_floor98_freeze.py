"""Freeze a successor to the unlaunched96 queue, retaining every earlier byte."""

import json
from pathlib import Path
import shutil
import tarfile

from gpu.orch_rich_hot_node2_export import digest, durable, wire
from organism_v6 import orch_rich_hot_node2_floor98 as policy


ORIGINAL = Path('research_notes/analysis/orch_rich_hot_node2_20260915_attempt1')
ROOT = ORIGINAL / 'floor98_prep'
NEW = ('gpu/orch_rich_hot_node2_floor98.py', 'gpu/orch_rich_hot_node2_floor98_freeze.py',
       'gpu/orch_rich_hot_node2_export.py', 'organism_v6/orch_rich_hot_node2_floor98.py',
       'tests/test_orch_rich_hot_node2_floor98.py')


def freeze():
    ROOT.mkdir(exist_ok=False)
    shutil.copytree(ORIGINAL / 'continuation_prep/source', ROOT / 'source')
    for name in NEW:
        shutil.copyfile(name, ROOT / 'source' / name)
    for name in ('INITIAL.json', 'SERVICE_IDENTITY.json', 'gsm8k_train.jsonl', 'LIFETIME.json'):
        shutil.copyfile(ORIGINAL / 'continuation_prep' / name, ROOT / name)
    records = [json.loads(line) for line in (ROOT / 'gsm8k_train.jsonl').read_text().splitlines()]
    tasks = policy.cohort(records, json.loads((ORIGINAL / 'TASKS.json').read_text()))
    durable(ROOT / 'TASKS.json', wire(tasks))
    provenance = json.loads((ORIGINAL / 'continuation_prep/DATA_PROVENANCE.json').read_text())
    provenance.update(supersedes_unlaunched_queue='orch_rich_hot_node2_continue_20260915_attempt1',
                      prior_source_sha256=digest((ORIGINAL / 'continuation_prep/source.tar').read_bytes()),
                      directive='Rohin98', prompt_version=tasks['prompt_version'], no_parenting_experience_ingestion=True)
    durable(ROOT / 'DATA_PROVENANCE.json', wire(provenance))
    durable(ROOT / 'PROTOCOL.md', (
        '# Rohin98 node2 CODE-first mixed richness successor\n\n'
        'Original hot generators/source/deadline remain unchanged. Unlaunched Rohin96 CPU queue '
        'was stopped by exact PID572111 UID2524 start67247872 with pidfd; all its preparation '
        'and zero-native evidence preserved. Only this version may launch successors.\n\n'
        'Each lane starts its CODE-first mixed stream immediately after that original lane '
        'naturally completes, has mounted AFTER unchanged, every own reservation resolved, '
        'and its old PID absent. Fresh privileged globalUUID/proc/CVD/open-device CLEAR '
        'is mandatory before each new child. Other original lanes keep running. The exclusive '
        'same-owner successor sublease is bound to original all8 claim and per-device native '
        'receipts. No original advisory lock is stolen/released; no original PID is stopped. '
        'The original guardian may later record busy successor GPUs at its whole-node release '
        'scan: preserve those real receipts; do not mislabel them as old native failure or '
        'falsify CLEAR. New guardian owns/retires only new exact PIDs.\n\n'
        'Unchanged original16h/128assignedGPUh lifetime,19:14:30.743091 dispatch cutoff, '
        '19:19:30.743091 hard end September15. Original6144call limit unchanged. Prospective '
        'additional65536total/8192per lane (combined71680upper bound); no retries/reset. '
        'Every native call8192new/16384total context; no forced minimum or crop.256 bounded '
        'cursor batches,24common tasks per batch,12per parity shard. Each shard4CODE/4math/'
        '4ROUTE with CODE first.1024fresh known-excluded math tasks,64existing L1 ledger '
        'tasks,256isolated TRAIN route worlds; repeated pool/crossworker sources explicit.\n\n'
        'New versioned prompt asks WHEN RELEVANT for the consequential alternative considered '
        'and why rejected before FINAL/final action. Never invent a branch or pad. Existing '
        'strict numeric FINAL, bounded code expressionJSON and route action/EVENT grammars '
        'unchanged. Real ROUTE exposures stay exact commands/EVENTs, followed by actual own '
        'six-turn-max episodes with branching guidance. CODE uses existing safe ledger '
        'helper interpreter, not arbitrary generated code. Math/code TWO_PASS/META use '
        'only own prior response. Route labels remain styles, not matched two-call math treatments.\n\n'
        'Branching remains UNREVIEWED until sampled semantic annotation, never keyword proof. '
        'No first-person or150–400 token eligibility gate; grounded-correct long/short raw '
        'rows remain available, not automatically admitted. All raw targets/actual outcomes '
        'and failures preserved. Immutable raw batches<=64; separate immutable environment '
        'receipts/checkpoints. Hubble owns64raw/12sample quality batches; sampled PASS cannot '
        'certify unseen rows. Main/Hubble own qualification, Laplace consumes qualified '
        'own L1 evidence only; NO parenting experiences, teacher targets or held data. '
        'No parent/API/fit calls; semantic review never blocks generation.\n'
    ).encode())
    with tarfile.open(ROOT / 'source.tar', 'w') as archive:
        for path in sorted((ROOT / 'source').rglob('*.py')):
            archive.add(path, arcname=str(path.relative_to(ROOT / 'source')), recursive=False)
    frozen = dict(source_sha256=digest((ROOT / 'source.tar').read_bytes()),
                  tasks_sha256=digest((ROOT / 'TASKS.json').read_bytes()),
                  lifetime_sha256=digest((ROOT / 'LIFETIME.json').read_bytes()),
                  protocol_sha256=digest((ROOT / 'PROTOCOL.md').read_bytes()))
    durable(ROOT / 'LOCAL_FREEZE.json', wire(frozen))
    print(json.dumps(frozen, indent=2))


if __name__ == '__main__':
    freeze()

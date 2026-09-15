"""CPU-only node5 R110 reuse plan; no SSH trust changes or native dispatch."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from organism_v6 import orch_math_feedback_uptake_r110 as policy


ROOT = '/localhome/local-rohing/orch_math_feedback_uptake_node5_20260915_attempt1'
HARD_END = datetime(2026, 9, 15, 17, 2, tzinfo=timezone.utc)
LEASE_END = datetime(2026, 9, 17, 4, 4, tzinfo=timezone.utc)
REUSE_FILES = (
    'gpu/orch_math_feedback_uptake_r110_run.py',
    'gpu/orch_math_feedback_uptake_r110_native.py',
    'gpu/orch_math_feedback_uptake_r110_broker.py',
    'organism_v6/orch_math_feedback_uptake_r110.py',
    'tests/orch_math_feedback_uptake_r110_test.py',
)
PRINCIPLES = 'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md'
READY = 'research_notes/analysis/orch_math_feedback_uptake_20260915_attempt1/R110_READY.json'
MISSING = (
    'Fable independently verified server fingerprint and normal wrapper trust',
    'Completed native environment transfer and cached base verification',
    'Fresh eight-GPU census, exact physical2/3 UUIDs and kernel minors',
    'Pinned host hash, boot, owner/service identities and privileged proc readability',
    'New node5-specific executable source and native CPU tests',
    'Fresh union exclusion registry, frozen node5 cohorts and prompt bindings',
    'Dated own native-provenance receipt and strict initial admission',
)


def make_plan(repository):
    repository = Path(repository)
    ready_path = repository / READY
    ready_bytes = ready_path.read_bytes()
    ready = json.loads(ready_bytes)
    hashes = {}
    for name in REUSE_FILES:
        digest = hashlib.sha256((repository / name).read_bytes()).hexdigest()
        policy.require(ready['family']['source_files'][ready['root'] + '/source/' + name] == digest,
            'reuse_bytes_differ_from_frozen_native_R110')
        hashes[name] = digest
    principles_sha = hashlib.sha256((repository / PRINCIPLES).read_bytes()).hexdigest()
    policy.require(principles_sha == ready['family']['principles_sha256'], 'same_shared_principles')
    hard = min(HARD_END.timestamp(), LEASE_END.timestamp() - 21600)
    lanes = []
    for physical, source_arm in ((2, 0), (3, 1)):
        budget = policy.budget(source_arm)
        lanes.append(dict(physical=physical, uuid=None, kernel_minor=None,
            prospective_cadence=budget['cadence'], reflection_generation_cap=budget['distillation_generation_cap'],
            native_cap=budget['native_calls'], parent_cap=budget['parent_calls'],
            max_cycles=budget['cycles'], sequential_episodes_per_cycle=2,
            mandatory_metacognition_dialogue=True, max_gpu_hours=8,
            source_arm_only_not_cuda_mapping=source_arm))
    return dict(schema='NODE5_R110_CPU_REUSE_PLAN_V1', status='BLOCKED_SSH_TRUST_CPU_PREPARATION_ONLY',
        launch_ready=False, native_calls=0, parent_calls=0, allocation_is_not_occupancy=True,
        root=ROOT, wrapper='gpu/ovx3_ssh.sh', transfer_wrapper='gpu/ovx3_scp.sh',
        host_sha256=None, boot_id=None, lanes=lanes,
        hard_deadline_unix=hard, native_deadline_unix=hard - 180,
        max_wall_seconds_per_card=28800, lease_end_unix=LEASE_END.timestamp(), lease_margin_seconds=21600,
        additional_native_cap=sum(lane['native_cap'] for lane in lanes),
        additional_parent_cap=sum(lane['parent_cap'] for lane in lanes), additional_gpu_hours=16,
        counters_activate_only_after_new_publication_and_admission=True,
        source_ready_path=READY, source_ready_sha256=hashlib.sha256(ready_bytes).hexdigest(),
        source_family_ready_sha256=ready['family_ready_sha256'], reused_source_hashes=hashes,
        principles_sha256=principles_sha, missing_bindings=list(MISSING),
        original_lanes_unchanged=True, original_lanes_do_not_wait_for_node5=True,
        trust_bypass=False, new_baseline_controls=0, adapter=None, optimizer=None, weight_writes=0,
        scientific_label='frozen_BASE_contextual_discovery_not_training_sleep_or_retained_weight_learning',
        raw_storage='node_only', fresh_cohorts_selected=False)


if __name__ == '__main__':
    print(json.dumps(make_plan(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))

"""Pure, fixed one-factor R186 copy configuration and frozen-adapter assembly."""

import ast
from copy import deepcopy
from pathlib import Path

from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import require


ARMS = {
    'p4': (0, 'GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0', '0000:4f:00.0', 4, 1),
    'p32': (1, 'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4', '0000:52:00.0', 32, 1),
    'lr03': (5, 'GPU-0cc84073-37a0-4f7a-e555-11671425bd03', '0000:d1:00.0', 16, 0.3),
    'lr3': (6, 'GPU-a064bca2-bddc-73ad-faf1-a4fbcb49fecf', '0000:d5:00.0', 16, 3),
}
GATE_ROOT = '/localhome/local-rohing/orch_r153_cpu_smoke_20260917t2242z/gate'
GATE_SHA = '5241727deccc099cdf93d6bde213d44df2ae52ba4b6b73103d10abbb5bfc0a89'
PACKET_SHA = 'cc7d7f07ed29c952d8f57f17f679f0fdd2084d85711a763ddebba1a2f518f91e'
BASE_PLAN_SHA = '3887bb900ea1c8f27325fcd8537a080eaff7d5e591407c9b2aef647583907448'
BASE_SOURCE_SHA = '720833444e7b045c3e3b059d89dac469764c24106725f2f8ba5040d92120b773'
BASE_ROOT = '/localhome/local-rohing/orch_r153_r184_node2_20260917/explicit1'
REMOTE_ROOT = '/localhome/local-rohing/orch_r153_r186_c2_plasticity_20260917'
OWN = 'research_loop/workers/rohin183_repo_learning_20260917'
TEST_MODULES = ('tests.test_orch_r125_continual_native', 'tests.test_orch_r184_think_act_learn',
    OWN.replace('/', '.') + '.test_r186_copy')


def make_plan(base, source, label):
    require(label in ARMS, 'fixed_assigned_arm')
    physical, device, unused_pci, presentations, multiplier = ARMS[label]
    require(base['new_presentations'] == 16 and base['rehearsal_presentations'] == 0,
        'unchanged_explicit_baseline_recipe')
    require(base['think_act_learn']['reflection_policy'] == 'explicit'
        and base['think_act_learn']['think_segments'] == 1
        and base['think_act_learn']['cpu_gate_root'] == GATE_ROOT
        and base['think_act_learn']['cpu_gate_sha256'] == GATE_SHA, 'frozen_explicit_tool_cadence')
    plan = deepcopy(base)
    plan.update(source_root=str(source), physical=physical, gpu_uuid=device,
        new_presentations=presentations, max_sleeps=44,
        plasticity=dict(schema='R186_PLASTICITY_V1', learning_rate_multiplier=multiplier))
    plan['startup_context']['path'] = str(Path(source) / 'context/R153_STARTUP.md')
    plan['think_act_learn']['trial_id'] = 'C2_explicit_R186_' + label + '_v1'
    return plan


def cpu_adapter(raw):
    text = raw.decode()
    tree = ast.parse(text)
    nodes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == '_cpu']
    require(len(nodes) == 1, 'one_exact_cpu_adapter')
    node = nodes[0]
    lines = text.splitlines(keepends=True)
    return ''.join(lines[node.lineno - 1:node.end_lineno])


def retain_bridge(canonical, frozen):
    current = cpu_adapter(canonical)
    require('from gpu.orch_r153_community_transport import cpu_once' in current,
        'expected_canonical_cpu_dispatch')
    retained = cpu_adapter(frozen)
    require('from gpu.r184_cpu_bridge import call' in retained, 'frozen_external_bridge')
    return canonical.decode().replace(current, retained, 1).encode()


def confinement(raw, label):
    require(label in ARMS, 'fixed_assigned_arm')
    physical, device, pci, unused_presentations, unused_multiplier = ARMS[label]
    text = raw.decode()
    changes = {
        'GPU-c9450d3d-0455-f034-b9bf-7f8956e44733': device,
        'MINOR=3': 'MINOR=' + str(physical),
        '/dev/nvidia3': '/dev/nvidia' + str(physical),
        '0000:57:00.0': pci,
        '[0, 1, 2, 4, 5, 6, 7]': str([minor for minor in range(8) if minor != physical]),
        "'orch-r184-c2-explicit-'": "'orch-r186-c2-" + label + "-'",
    }
    for before, after in changes.items():
        require(text.count(before) >= 1, 'exact_frozen_confinement_token:' + before)
        text = text.replace(before, after)
    return text.encode()

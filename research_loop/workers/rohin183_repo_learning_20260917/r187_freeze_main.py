"""Capture Main-ready THINK-budget bytes; no device binding, remote I/O or launch."""

import ast
from pathlib import Path
import json
import subprocess
import sys
import time

from research_loop.workers.rohin183_repo_learning_20260917.r186_copy import retain_bridge
from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import digest, write, require


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def prompt_function(raw):
    tree = ast.parse(raw)
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'stage_prompt']
    require(len(nodes) == 1, 'one_stage_prompt')
    namespace = {'require': require}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<isolated-stage-prompt>', 'exec'), namespace)
    return namespace['stage_prompt']


def main():
    original = (REPO / 'gpu/orch_r184_think_act_learn.py').read_bytes()
    frozen = (ROOT / 'r184_explicit_source/gpu/orch_r184_think_act_learn.py').read_bytes()
    candidate = retain_bridge(original, frozen)
    old_prompt, new_prompt = prompt_function(frozen), prompt_function(candidate)
    for policy in ('explicit', 'brief'):
        for stage in ('THINK', 'ACT', 'LEARN'):
            require(old_prompt(stage, policy) == new_prompt(stage, policy), 'unchanged_default_one_prompt')
    output = ROOT / 'R187_PENDING_MAIN_CODE'
    output.mkdir()
    write(output / 'CANONICAL_DRIVER.py', original)
    write(output / 'BRIDGE_ADAPTED_DRIVER.py', candidate)
    tests = ('tests/test_orch_r184_think_act_learn.py', 'tests/test_orch_r188_parent_examples.py')
    test_pins = {}
    for name in tests:
        raw = (REPO / name).read_bytes()
        write(output / Path(name).name, raw)
        test_pins[name] = digest(raw)
    command = [sys.executable, '-B', '-m', 'unittest', 'tests.test_orch_r184_think_act_learn',
        'tests.test_orch_r188_parent_examples', '-q']
    result = subprocess.run(command, cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
    write(output / 'CPU.log', result.stdout.encode())
    require(result.returncode == 0, 'Main_budget_CPU_tests')
    require((REPO / 'gpu/orch_r184_think_act_learn.py').read_bytes() == original,
        'canonical_driver_unchanged_during_tests')
    receipt = dict(status='MAIN_CODE_FROZEN_NOT_NODE4_ADMITTED', observed_unix=time.time(),
        canonical_driver_sha256=digest(original), bridge_adapted_driver_sha256=digest(candidate),
        test_pins=test_pins, test_log_sha256=digest(result.stdout.encode()), CPU_passed=True,
        default_one_prompt_bytes_unchanged=True, frozen_external_cpu_adapter_preserved=True,
        treatments=[dict(physical=5, think_segments=2), dict(physical=6, think_segments=3)],
        new_presentations=16, learning_rate_multiplier=1, episodes_per_sleep=1,
        actual_generated_rows_and_update_cost_must_be_reported=True,
        gauss_slot_lease_confirmation=None, actual_node4_CPU_gate=None, GPU_launches=0,
        live_sources_changed=False, new_parent=False)
    print(json.dumps(write(output / 'PREPARATION.json', receipt), sort_keys=True))


if __name__ == '__main__':
    main()

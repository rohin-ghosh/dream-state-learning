"""Five fresh caption forks; fixed checkpoint, compact birth and masked feedback."""

from pathlib import Path
import time

from gpu import r205_runtime as runtime


ASSIGNMENTS = {'r213_r226_caption_unparented_fork': (2, 'unparented')}
V2 = 'R225_CONTENT_BEARING_TARGETS_V2'


def caption_binding(plan):
    name = Path(plan['source_root']).parent.name
    if name not in ASSIGNMENTS or plan['physical'] != ASSIGNMENTS[name][0]:
        raise ValueError('exact_five_caption_identities_and_devices')
    config = plan['think_act_learn']
    if config.get('content_target_filter') != V2 or not config.get('learn_review_filter'):
        raise ValueError('caption_V2_and_R195_required')
    if plan['new_presentations'] != 16 or 'plasticity' in plan:
        raise ValueError('unchanged_checkpoint51_baseline_learning_recipe')
    return name, '/tmp/r226-caption-' + str(plan['physical']) + '.sock'


def bounded_runtime(argv, deadline, observed):
    result = list(argv)
    positions = [index for index, value in enumerate(result)
        if value.startswith('--property=RuntimeMaxSec=')]
    if len(positions) != 1 or deadline - observed < 30:
        raise ValueError('one_runtime_wall_with_remaining_lease_budget')
    result[positions[0]] = '--property=RuntimeMaxSec=' + str(int(deadline - observed))
    return result


def main():
    original_install, original_command = runtime.install_runtime, runtime.contained_command

    def install(plan):
        from gpu.ny_caption_life import activate
        name, socket_path = caption_binding(plan)
        runtime.receive_peer = lambda driver: None
        original_install(plan)
        activate(socket_path, max_act_attempts=3)

    def command(config_path, mode):
        from gpu.orch_r125_continual_guard import validate
        _, plan = validate(config_path)
        caption_binding(plan)
        return bounded_runtime(original_command(config_path, mode), plan['hard_end_unix'], time.time())

    runtime.MODULE = 'gpu.r226_caption_runtime'
    runtime.install_runtime, runtime.contained_command = install, command
    runtime.main()


if __name__ == '__main__':
    main()

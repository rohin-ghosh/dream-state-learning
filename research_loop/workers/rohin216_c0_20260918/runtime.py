"""New C0 lineage only; inherited snapshot, no writes to original C2."""

import hashlib
import inspect
from pathlib import Path
import time

from gpu import r205_runtime as runtime
from organism_v6.orch_r124_train_history import TrainEvent


TRIAL = 'R216_C0_SNAPSHOT51_MATH'
DEVICE = 'GPU-d304a15c-516a-16a0-a926-a560304077cc'
ORIGINAL_CONTAINED_COMMAND = runtime.contained_command


def contained_command(config_path, mode):
    from gpu import orch_r125_continual_guard as guard
    command = ORIGINAL_CONTAINED_COMMAND(config_path, mode)
    if mode == 'child':
        config, plan = guard.validate(config_path)
        remaining = int(min(plan['hard_end_unix'], plan['lease_end_unix'] - 600) - time.time() - 15)
        positions = [index for index, value in enumerate(command) if value.startswith('--property=RuntimeMaxSec=')]
        if len(positions) != 1 or not 30 < remaining <= 21600:
            raise ValueError('C0_bound_actual_operator_and_lease_deadline')
        command[positions[0]] = '--property=RuntimeMaxSec=' + str(remaining)
    return command


def preadmitted_report(config_path):
    from gpu import orch_r125_continual_guard as guard
    config, plan = guard.validate(config_path)
    admission = runtime.native.read(Path(config['attempt_dir']) / 'PRE_SERVICE_ADMISSION.json')
    if (admission['guard_sha256'] != runtime.native.sha(config_path)
            or not 0 <= time.time() - admission['verified_unix'] <= 120):
        raise ValueError('C0_fresh_source_bound_privileged_admission_required')
    report = admission['report']
    if report['scanner_euid'] != 0 or not report['clear'] or report['blocking_reasons']:
        raise ValueError('C0_actual_privileged_clear_admission_required')
    return report


def supervise_owned(config_path):
    from gpu import orch_r125_continual_guard as guard
    source = inspect.getsource(guard.supervise)
    original = 'report = json.loads(subprocess.check_output(command, text=True, timeout=100))'
    if source.count(original) != 1 or source.count("'gpu.orch_r125_continual_guard'") != 2:
        raise ValueError('C0_exact_tested_admission_and_entrypoint_seams')
    source = source.replace(original, 'report = preadmitted_report(config_path)')
    source = source.replace("'gpu.orch_r125_continual_guard'", repr('gpu.r216_c0_runtime'))
    namespace = dict(guard.supervise.__globals__, preadmitted_report=preadmitted_report)
    exec(compile(source, __file__ + ':preadmitted_entrypoint', 'exec'), namespace)
    return namespace['supervise'](config_path)


def pin_reference(stream, journal):
    path = Path(__file__).resolve().parents[1] / 'context/ROHIN_C2_TRANSCRIPT.md'
    raw = path.read_bytes()
    source = hashlib.sha256(raw).hexdigest()
    event_id = 'r216:c0:historical-transcript:' + source
    if any(event.event_id == event_id for event in stream.history.events):
        return
    event = TrainEvent(event_id=event_id, actor='parent', split='TRAIN',
        text=('Astra: Historical reference transcript, pinned verbatim below. These are earlier '
            'Rohin/C2 exchanges, not new messages to C0 or instructions to impersonate either '
            'speaker. You are C0, a new snapshot51 fork; original C2 continues separately. '
            'External reference words are context only, never imported training targets.\n\n'
            + raw.decode()), source_sha256=source, phase='feedback', episode_id='continual_stream',
        source_id=str(path), origin='TRAIN_COLLECTION')
    stream.history.append(event)
    if not stream.history.pin_parent_event(event_id):
        raise ValueError('C0_historical_reference_pin_failed')
    journal.record('CONTEXT_INPUT', dict(kind='R216_C0_PINNED_HISTORICAL_REFERENCE',
        source_sha256=source, event_id=event_id, verbatim=True, training_eligible=False,
        historical_not_new_human_message=True, state=stream.checkpoint()))


def main():
    runtime.MODULE = 'gpu.r216_c0_runtime'
    runtime.DEVICES = {4: (DEVICE, '0000:ce:00.0')}
    runtime.TRIALS = (TRIAL,)
    runtime.receive_peer = lambda driver: None
    runtime.supervise_owned = supervise_owned
    runtime.contained_command = contained_command
    compact = runtime.compact_birth

    def compact_and_pin(stream, journal):
        compact(stream, journal)
        pin_reference(stream, journal)

    runtime.compact_birth = compact_and_pin
    runtime.main()


if __name__ == '__main__':
    main()

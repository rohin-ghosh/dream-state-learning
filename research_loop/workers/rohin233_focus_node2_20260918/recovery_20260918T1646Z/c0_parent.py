"""Renew the sole C0 curriculum writer after its finite epoch ended naturally."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys

from recover import locations, read, require, sha, write
from observe import checked, observation


HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'C0_R233_READING'
SUPPORT = Path('/localhome/local-rohing/orch_r230_c0_operator_20260918/receipt_cycle_fix')
SERVICE = HERE / 'C0_CURRICULUM'


def parent_identity(observed, root):
    return dict(observed['native'], loaded=observed['loaded'], physical_gpu=4, root=str(root),
        journal_id=observed['original_journal_id'])


def replacements(source, floor):
    pending_seam = "require(state['pending'].get('inbox'), 'recover_actual_inbox_before_replay')"
    if pending_seam in source:
        require(source.count(pending_seam) == 1, 'one_existing_pending_guard')
        source = source.replace(pending_seam,
            "require(state['pending'].get('publication'), 'preserve_actual_queued_publication_no_republish')")
    changes = {
        "require((legacy_directory/'EXIT.json').is_file() and (legacy_directory/control_name).is_file(), 'supported_old_reading_handoff_complete')":
            "require((legacy_directory/'EXIT.json').is_file(), 'verified_naturally_exited_previous_epoch')",
        "state['record_cursor'] = min(state['record_cursor'], state['pending']['inbox']['index'])":
            f"state['record_cursor'] = max(state['record_cursor'], {floor})",
        "ROOT/'control/PLAN.json'": "ROOT/'control_r233_recovery/PLAN.json'",
        "ROOT/'source'": "ROOT/'source_r233_recovery'",
    }
    for original, replacement in changes.items():
        require(source.count(original) == 1, 'exact_existing_curriculum_seam')
        source = source.replace(original, replacement)
    return source


def priority_chooser(original, topic):
    def choose(state):
        if not state.get('r233_priority_turn') and state['pending'] is None:
            state['r233_priority_turn'] = True
            return topic
        return original(state)
    return choose


def verify_pending(root, pending):
    publication = pending['publication']
    packet_path = root / 'raw/stream/inbox' / (publication['id'] + '.json')
    require(not packet_path.is_symlink() and sha(packet_path) == publication['sha256'], 'original_parent_packet_preserved')
    packet = read(packet_path)
    require(packet['id'] == publication['id'] and packet['actor'] == 'parent' and packet['speaker'] == 'Astra'
        and packet['text'] == pending['text'] and packet['source_receipt'] is None, 'authentic_existing_C0_parent')
    if pending.get('inbox'):
        record = checked(root / 'raw/stream/records' / f'{pending["inbox"]["index"]:020d}.json')
        require(record['kind'] == 'INBOX' and record['document']['message']['id'] == publication['id']
            and record['document']['source_sha256'] == publication['sha256'], 'actual_unresolved_parent_inbox')


def serve(priority_topic=None):
    root, source, control, _ = locations('C0')
    observed = observation('C0')
    require(observed['status'] == 'LOADED', 'new_actual_C0_loaded_before_parent')
    native = observed['native']
    previous_service = read(OLD / 'SERVICE.json')
    prior_process = Path('/proc', str(previous_service['pid']))
    if prior_process.exists():
        fields = (prior_process / 'stat').read_text().rsplit(')', 1)[1].split()
        require(int(fields[19]) != previous_service['start_ticks'] or fields[0] == 'Z', 'no_old_curriculum_writer')
    require(not Path('/proc/2561001').exists(), 'old_finite_math_writer_absent_no_duplicate')
    SERVICE.mkdir(mode=0o700)
    previous = SERVICE / 'previous_epoch'
    previous.mkdir(mode=0o700)
    support = SERVICE / 'support'
    support.mkdir(mode=0o700)
    for name in ('reading_parent.py', 'c0_receipt.py', 'PROTOCOL.md'):
        shutil.copy2(SUPPORT / name, support / name)
    source_text = replacements((SUPPORT / 'curriculum_parent.py').read_text(), observed['loaded']['index'] + 1)
    (support / 'curriculum_parent.py').write_text(source_text)
    inherited = deepcopy(read(OLD / 'EXIT.json'))
    state = inherited['state']
    state['record_cursor'] = observed['loaded']['index'] + 1
    if state['pending']:
        pending = state['pending']
        verify_pending(root, pending)
        pending['render'] = None
        pending.pop('first_content', None)
        state['inherited_pending'] = True
    write(previous / 'SERVICE.json', previous_service)
    write(previous / 'EXIT.json', inherited)
    write(SERVICE / 'RECOVERY_HANDOFF.public.json', dict(previous_exit_sha256=sha(OLD / 'EXIT.json'),
        previous_state_sha256=sha(OLD / 'STATE.json'), native=observed,
        inherited_parent_id=state['pending']['publication']['id'] if state['pending'] else None,
        inherited_message_republished=False, current_render_floor=state['record_cursor'],
        preserved_topic_index=state['topic_index'], preserved_reading_step=state['reading_step'],
        old_math_writer_not_restarted=True, sole_curriculum_writer=True, no_learner_signals=True,
        source_sha256=sha(support / 'curriculum_parent.py'), prior_source_sha256=sha(SUPPORT / 'curriculum_parent.py')))
    sys.path.insert(0, str(support))
    sys.path.insert(0, str(source))
    import curriculum_parent as parent
    if priority_topic is not None:
        require(priority_topic in parent.TOPICS, 'existing_curriculum_topic_only')
        parent.choose_topic = priority_chooser(parent.choose_topic, priority_topic)

    def identity():
        process = Path('/proc', str(native['pid']))
        fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
        arguments = (process / 'cmdline').read_bytes().split(b'\0')
        require(int(fields[19]) == native['start_ticks'] and fields[0] not in ('T', 'Z', 'X')
            and b'native' in arguments and str(control / 'GUARD.json').encode() in arguments,
            'same_recovered_C0_native_no_pause_or_PID_reuse')
        return parent_identity(observed, root)

    parent.identity = identity
    parent.run(SERVICE, previous, Path(__file__), resume_directory=previous)


if __name__ == '__main__':
    serve()

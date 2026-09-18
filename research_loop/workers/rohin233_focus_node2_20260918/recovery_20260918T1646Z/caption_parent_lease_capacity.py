"""Bounded paid-parent continuation; preserve the outstanding publication exactly."""

import hashlib
import inspect
import json
import os
from pathlib import Path
import time

from caption_parent_renew import configure, previous, renewed_source


HERE = Path(__file__).resolve().parent
LIMIT = 640


def capacity_source(source):
    changes = {
        "epoch = remote(dict(operation='begin'))": 'epoch = preserved_epoch',
        'maximum_turns=80': 'maximum_turns=640',
        'pending, prior, number = None, [], 0': 'pending, prior, number = preserved_pending, preserved_prior, preserved_number',
        'number < 80': 'number < 640',
        "if pending:\n            observation":
            "if number >= 560 and not (PUBLIC/'CAPACITY_WARNING.json').exists():\n"
            "            focus.write(PUBLIC/'CAPACITY_WARNING.json', dict(utc=focus.utc(), used=number, ceiling=640, remaining=640-number, requires_owner_attention=True))\n"
            "        if pending:\n            observation",
        "focus.write(PUBLIC/'EXIT.json', dict(completed_utc=focus.utc(), parent_turns=number, learner_signals=0))":
            "focus.write(PUBLIC/'EXIT.json', dict(completed_utc=focus.utc(), parent_turns=number, learner_signals=0, "
            "reason='publication_budget_ceiling' if number >= 640 else 'deadline_or_owner_stop', requires_owner_attention=number >= 640))",
    }
    for original, replacement in changes.items():
        previous.focus.require(source.count(original) == 1, 'exact_existing_caption_capacity_seam')
        source = source.replace(original, replacement)
    return source


def preserved_ledger(private, public):
    published = sorted(public.glob('PUBLISHED_[0-9][0-9][0-9][0-9].json'))
    previous.focus.require(bool(published), 'existing_actual_parent_ledger')
    last = int(published[-1].stem.rsplit('_', 1)[1])
    attempt = private / f'turn_{last:04d}'
    saved = json.loads((attempt / 'PUBLISHED.private.json').read_bytes())
    request = json.loads((attempt / 'API_REQUEST.json').read_bytes())
    payload = json.loads(request['input'])
    record = json.loads(published[-1].read_bytes())
    pending = dict(text=saved['response']['message'], publication=saved['receipt']['publication'])
    previous.focus.require(pending['publication'] == record['publication']
        and hashlib.sha256(pending['text'].encode()).hexdigest() == record['parent_reply_sha256'],
        'original_parent_packet_and_text_bound_no_republish')
    previous.focus.require(payload['turn'] == last and request['max_output_tokens'] == 4096,
        'same_original_turn_and_provider_token_limit')
    return pending, payload['previous_turns'], last + 1


def main():
    configure()
    previous.focus.require(bool(os.environ.get('NVIDIA_API_KEY')), 'current_shell_credentials_present_not_persisted')
    private, public = previous.PRIVATE, previous.PUBLIC
    successor_private = HERE / 'caption_parent_lease.private'
    successor_public = HERE / 'caption_parent_lease_public'
    previous.focus.require(not successor_public.exists() and not successor_private.exists(), 'one_CPU_parent_continuation')
    owner = json.loads((public / 'SERVICE.json').read_bytes())
    process = Path('/proc', str(owner['pid']))
    fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    previous.focus.require(int(fields[19]) == owner['start_ticks']
        and process.stat().st_uid == os.getuid()
        and hashlib.sha256((process / 'cmdline').read_bytes()).hexdigest() == owner['cmdline_sha256'],
        'exact_owned_caption_CPU_parent')
    transformed = capacity_source(renewed_source(inspect.getsource(previous.serve)))
    previous.focus.write(private / 'STOP', dict(reason='Authorized finite lease-capacity renewal; no learner controls'))
    limit = time.time() + 210
    while True:
        try:
            fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
            active = int(fields[19]) == owner['start_ticks'] and fields[0] not in ('Z', 'X')
        except FileNotFoundError:
            active = False
        if (public / 'EXIT.json').exists() and not active:
            break
        previous.focus.require(time.time() < limit, 'old_CPU_parent_must_exit_without_duplicate')
        time.sleep(0.5)
    pending, prior, number = preserved_ledger(private, public)
    previous.focus.require(number < LIMIT, 'remaining_finite_parent_budget')
    epoch = json.loads((public / 'EPOCH.json').read_bytes())
    previous.PRIVATE, previous.PUBLIC = successor_private, successor_public
    successor_public.mkdir(mode=0o700)
    previous.focus.write(successor_public / 'CAPACITY_HANDOFF.json', dict(previous_pid=owner['pid'],
        previous_start_ticks=owner['start_ticks'], completed_turn_counter=number,
        pending_publication=pending['publication'], pending_republished=False, maximum_turns=LIMIT,
        maximum_output_tokens_per_call=4096, maximum_epoch_output_tokens=LIMIT * 4096,
        per_turn_instruction_unchanged=True, cadence_unchanged=True, warning_at_turn=560,
        learner_controls=0, new_treatment_epoch=False, provider_prices_or_cost_not_claimed=True))
    namespace = dict(previous.serve.__globals__, preserved_epoch=epoch, preserved_pending=pending,
        preserved_prior=prior, preserved_number=number, __file__=str(Path(__file__).resolve()))
    exec(compile(transformed, __file__ + ':bounded_capacity', 'exec'), namespace)
    namespace['serve']()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        directory = HERE / 'caption_parent_lease_public'
        directory.mkdir(mode=0o700, exist_ok=True)
        previous.focus.write(directory / 'FAILED.json', dict(error_type=type(error).__name__,
            error_code='bounded_caption_CPU_handoff_failed_no_retry', learner_controls=0))
        raise

"""Generate a public CPU readiness receipt; never activate, publish, or dispatch."""

import datetime
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

from environment import (CONTEXT_SURFACES, MemoryRound, PuzzleRound,
                         activation_status, digest)


HERE = Path(__file__).resolve().parent


def main():
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern='test_environment.py')
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (HERE / 'CPU_TESTS.log').write_text(stream.getvalue())
    if not result.wasSuccessful():
        raise SystemExit(stream.getvalue())
    bank = json.loads((HERE / 'puzzles.json').read_bytes())['items']
    answers = [[2, 2, 4, 7, 9], 2, ['amber', 'coral', 'dune', 'elm'], True]
    puzzle_receipts = [PuzzleRound(task, mode='CPU_FIXTURE').answer(answer) for task, answer in zip(bank, answers)]
    memory_receipts = []
    for condition in ('EXPLICIT_CONTEXT', 'NO_EXPLICIT_CONTEXT'):
        game = MemoryRound(condition=condition, life_id='PUBLIC_CPU_FIXTURE', mode='CPU_FIXTURE', fixture_code='K7M2Q9RX')
        study = game.study_view()
        game.mark_study_delivered(life_id='PUBLIC_CPU_FIXTURE', request_index=10, cycle=1,
                                 request_sha256=digest(study), all_history_tokens_masked=True)
        game = MemoryRound.restore_operator_state(json.loads(json.dumps(game.operator_state())))
        sleep = dict(kind='SLEEP_COMPLETE', index=20, journal_id='PUBLIC_CPU_FIXTURE',
                     document=dict(cycle=2, status='COMPLETE'), synthetic=True)
        sleep['sha256'] = digest(sleep)
        game.observe_natural_sleep(life_id='PUBLIC_CPU_FIXTURE', record=sleep, naturally_completed=True)
        view = game.recall_view()
        surfaces = {name: [] for name in CONTEXT_SURFACES}
        surfaces['rendered_prefix'] = [json.dumps(view)]
        memory_receipts.append(game.answer('K7M2Q9RX', surfaces=surfaces))
    source_names = ('environment.py', 'puzzles.json', 'test_environment.py', 'OVERVIEW.md',
                    'PARENT_GUIDANCE.md', 'README.md', 'RESERVATION.json', 'ACTIVATION.json', 'prepare_receipt.py')
    hashes = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in source_names}
    release = json.loads((HERE / 'ACTIVATION.json').read_bytes())
    receipt = dict(schema='R213_ENVIRONMENT_READY_CPU_ONLY_V1',
                   observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   status='CPU_ENVIRONMENT_READY_NOT_ATTACHED_NOT_ACTIVATED',
                   interpreter=sys.executable, tests_run=result.testsRun, tests_passed=True,
                   puzzle_receipts=puzzle_receipts, memory_receipts=memory_receipts,
                   source_sha256=hashes, activation=activation_status(release, hashes['OVERVIEW.md']),
                   original_C2_message_sent=False, live_game_started=False, receiver_bridge_deployed=False,
                   actual_child_runs=0, actual_sleep_receipts=0, synthetic_fixtures_only=True,
                   GPU_calls=0, model_calls=0, learner_signals=0, parent_publications=0,
                   runtime_or_lease_changes=0, automatic_start=False,
                   safety='No sealed/FINAL content; no pause/hold; no adapter-retention attribution.')
    (HERE / 'ENVIRONMENT_RECEIPT.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    current = json.loads((HERE / 'CURRENT_NODE2_REFRESH.json').read_bytes())
    reservation = json.loads((HERE / 'RESERVATION.json').read_bytes())
    status = dict(status=receipt['status'], prepared_utc=receipt['observed_utc'],
                  tests_run=result.testsRun, tests_passed=True, reservation=reservation,
                  activation=receipt['activation'], overview_sha256=hashes['OVERVIEW.md'],
                  current_observed_utc=current['observed_utc'], current_arms={},
                  no_pause=True, live_started=False, automatic_start=False,
                  source_receipts=['ENVIRONMENT_RECEIPT.json', 'CURRENT_NODE2_REFRESH.json'])
    for arm, observation in current['arms'].items():
        response = observation.get('RESPONSE', {})
        status['current_arms'][arm] = dict(native=observation.get('native'),
            identity_unverified=observation.get('identity_unverified'), loaded=observation['loaded'],
            head=observation['head'], response_index=response.get('index'), response_sha256=response.get('sha256'),
            response_finished_unix=response.get('document', {}).get('finished_unix'),
            last_ACT_index=observation.get('R184_ACT', {}).get('index'),
            last_ACT_status=observation.get('R184_ACT', {}).get('document', {}).get('outcome', {}).get('status'),
            natural_terminal=observation.get('TERMINAL'), filter_policy=observation['filter_policy'])
    (HERE / 'STATUS.json').write_text(json.dumps(status, indent=2, sort_keys=True) + '\n')
    print(json.dumps({key: receipt[key] for key in ('observed_utc', 'status', 'interpreter', 'tests_run',
                                                'tests_passed', 'activation', 'GPU_calls', 'model_calls', 'learner_signals')}))


if __name__ == '__main__':
    main()

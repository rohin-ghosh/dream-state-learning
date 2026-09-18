"""Defer only C2's exact old automatic parent; never stop or reset its learner."""

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path

from gpu import orch_r167_parent_takeover as takeover


HERE = Path(__file__).resolve().parent
FIXED_SHA = 'ee32ad40a7867c378ecd1f3e3b7885739c10a7f0d06f434f5308ba50dfa9ad97'
PID = 2256065
START_TICKS = '176042988'
ROOT = '/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life'
OLD_OUTPUT = Path('/data/home/rohing/dream-state-orch/research_loop/workers/r169_community_parent_status_20260917/attempt_135646/C2/parent')


def write(path, document):
    with path.open('x') as stream:
        json.dump(document, stream, indent=2, sort_keys=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    arguments = parser.parse_args()
    fixed_path = HERE / 'PILOT_CONFIG_V1.json'
    takeover.require(takeover.sha(fixed_path) == FIXED_SHA, 'fixed_pilot_unchanged')
    observed = takeover.identity(PID)
    takeover.require(observed['start_ticks'] == START_TICKS, 'exact_predecessor_start')
    config_path = Path(observed['argv'][observed['argv'].index('--config') + 1])
    source_path = Path('/proc') / str(PID) / 'cwd' / 'gpu/orch_r153_community_parents.py'
    source_path = source_path.resolve()
    binding = dict(observed, branch='C2', root=ROOT, output=str(OLD_OUTPUT),
                   config=dict(path=str(config_path), sha256=takeover.sha(config_path)),
                   source=dict(path=str(source_path), sha256=takeover.sha(source_path)))
    takeover.verify_identity(binding, observed)
    takeover.verify_files(binding)
    directory = HERE / ('guided_activation_' + datetime.now().astimezone().strftime('%Y%m%dT%H%M%S%z'))
    directory.mkdir(exist_ok=False)
    write(directory / 'BINDING.json', binding)
    write(directory / 'INTENT.json', dict(fixed_pilot_sha256=FIXED_SHA,
          action='defer_old_automatic_parent_only', execute=arguments.execute,
          new_messages=0, child_signals=0, source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    if not arguments.execute:
        print(json.dumps(dict(status='PREFLIGHT_ONLY', directory=str(directory))))
        return
    try:
        with takeover.quiesce(binding) as parent:
            manifest = takeover.settled_attempts(OLD_OUTPUT)
            write(directory / 'PRESERVED_ATTEMPTS.json', manifest)
            parent.terminate()
        result = dict(status='OLD_AUTOMATIC_PARENT_DEFERRED', observed_pdt=datetime.now().astimezone().isoformat(),
                      pid=PID, source_life=ROOT, child_signals=0, new_messages=0,
                      fixed_pilot_sha256=FIXED_SHA, guided_start='await_actual_Rohin_rendered_REQUEST',
                      resumed_parent=False, pending_publications_preserved=True)
    except Exception as error:
        result = dict(status='DEFERRED_NO_SUCCESSOR', error=str(error), child_signals=0, new_messages=0)
    write(directory / 'RESULT.json', result)
    print(json.dumps(dict(directory=str(directory), **result)))


if __name__ == '__main__':
    main()

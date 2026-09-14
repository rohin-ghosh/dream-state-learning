"""Export and exhaustively verify the installed Gym Taxi-v3 oracle on CPU."""

import argparse
import hashlib
import inspect
import json
from pathlib import Path

from organism_v6 import orch_game_screen as screen


def export():
    import gym

    if gym.__version__ != '0.21.0':
        raise ValueError('frozen_installed_gym_version_required')
    env = gym.make('Taxi-v3').unwrapped
    bank = dict(environment='Taxi-v3', gym_version=gym.__version__,
                environment_source_sha256=hashlib.sha256(Path(inspect.getfile(type(env))).read_bytes()).hexdigest(),
                map=[''.join(cell.decode() for cell in row) for row in env.desc],
                locations=[list(location) for location in env.locs],
                decoded={str(state): list(env.decode(state)) for state in range(env.observation_space.n)},
                transitions={str(state): {str(action): [[float(probability), int(next_state),
                    int(reward), bool(terminal)] for probability, next_state, reward, terminal in outcomes]
                    for action, outcomes in actions.items()} for state, actions in env.P.items()})
    checked = 0
    for state in range(env.observation_space.n):
        for action in range(env.action_space.n):
            env.s = state
            next_state, reward, terminal, info = env.step(action)
            expected = screen.transition(bank, state, action)
            if expected != dict(state=next_state, reward=reward, terminal=terminal):
                raise ValueError('native_step_replay_mismatch')
            checked += 1
    bank['native_transitions_verified'] = checked
    bank['instances'] = screen.freeze(bank)
    bank['oracle_sha256'] = screen.digest(bank['transitions'])
    bank['fit_ready'] = False
    return bank


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    options = parser.parse_args()
    bank = export()
    with Path(options.output).open('x') as stream:
        json.dump(bank, stream, sort_keys=True, indent=2)
    print(json.dumps(dict(states=len(bank['decoded']), transitions=bank['native_transitions_verified'],
                          instances=len(bank['instances']), oracle_sha256=bank['oracle_sha256'])))


if __name__ == '__main__':
    main()

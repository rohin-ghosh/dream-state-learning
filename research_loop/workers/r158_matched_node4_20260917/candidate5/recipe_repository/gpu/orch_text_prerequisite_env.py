"""CPU-only upstream TextWorld quest generation and native JSON-line interface."""

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def public(state):
    return {key: state.get(key) for key in ('feedback', 'description', 'inventory', 'won', 'lost', 'score')}


def freeze(root):
    import textworld
    from textworld.generator import make_world, make_quest, make_grammar, compile_game
    from textworld.generator.game import Game

    root.mkdir(parents=True, exist_ok=False)
    tasks = []
    for family, backward_rules in [('retrieve_closed', ['take/c', 'open/c']),
                                   ('stow_loose', ['insert', 'take'])]:
        for ordinal in range(6):
            split = 'mining' if ordinal < 4 else 'held_L1_DEV'
            seed = (31000 if family == 'retrieve_closed' else 32000) + ordinal
            options = textworld.GameOptions()
            options.seeds = seed
            options.nb_rooms = 1
            options.quest_length = 2
            options.chaining.backward = True
            options.chaining.create_variables = True
            options.chaining.restricted_types = {'r', 'd'}
            options.chaining.rng = options.rngs['quest']
            options.chaining.rules_per_depth = [[options.kb.rules[name]] for name in backward_rules]
            world = make_world(1, nb_objects=0, rngs=options.rngs)
            quests = make_quest(world, options)
            game = Game(world, make_grammar(options.grammar, rng=options.rngs['grammar']), quests)
            actions = quests[-1].win_events[0].actions
            if [action.name for action in actions] != list(reversed(backward_rules)):
                raise ValueError('unexpected_native_quest_structure')
            task_id = f'TW17_{family}_{seed}'
            options.path = str(root / (task_id + '.z8'))
            gamefile = compile_game(game, options)
            infos = textworld.EnvInfos(description=True, inventory=True, won=True, lost=True,
                                       score=True, policy_commands=True)
            environment = textworld.start(gamefile, infos)
            initial = environment.reset()
            solution = list(initial.policy_commands)
            if len(solution) != 2:
                raise ValueError('native_solution_not_two_actions')
            final_relation = next(fact for fact in actions[-1].added if fact.name == 'in')
            object_name = game.infos[final_relation.arguments[0].name].name
            goal = (f'Your goal is to be carrying the {object_name}.'
                    if family == 'retrieve_closed' else
                    f'Your goal is for the {object_name} to be inside the '
                    f'{game.infos[final_relation.arguments[1].name].name}.')
            game.objective = goal
            environment.close()
            options.force_recompile = True
            gamefile = compile_game(game, options)
            environment = textworld.start(gamefile, infos)
            initial = environment.reset()
            before = public(initial)
            failed, reward, done = environment.step(solution[-1])
            failure = public(failed)
            if done or failed.won or failed.inventory != initial.inventory:
                raise ValueError('native_missing_prerequisite_not_rejected')
            corrected = []
            for command in solution:
                state, reward, done = environment.step(command)
                corrected.append(public(state))
            if not done or not state.won:
                raise ValueError('native_oracle_replay_failed')
            environment.close()
            replay = textworld.start(gamefile, infos)
            if public(replay.reset()) != before:
                raise ValueError('nondeterministic_reset')
            for command in solution:
                state, reward, done = replay.step(command)
            if not state.won:
                raise ValueError('second_oracle_replay_failed')
            replay.close()
            tasks.append(dict(id=task_id, family=family, split=split, seed=seed,
                shard=ordinal if ordinal < 4 else None, game=Path(gamefile).name,
                game_sha256=sha(gamefile), json_sha256=sha(root / (task_id + '.json')),
                goal=goal, initial=before, oracle_commands=solution,
                prerequisite_probe=failure, correction_replay=corrected))
    result = dict(environment='upstream_textworld', version=importlib.metadata.version('textworld'),
        tasks=tasks, pairs=8, held=4, max_turns=6, max_context=2048, max_generated=512,
        maximum_calls=96, fits=0)
    (root / 'BANK.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(status='NATIVE_READY', pairs=8, held=4, bank_sha256=sha(root / 'BANK.json'))))


def serve(gamefile):
    import textworld

    environment = textworld.start(str(gamefile), textworld.EnvInfos(description=True,
        inventory=True, won=True, lost=True, score=True))
    try:
        print(json.dumps(public(environment.reset())), flush=True)
        for line in sys.stdin:
            request = json.loads(line)
            state, reward, done = environment.step(request['action'])
            print(json.dumps(dict(public(state), reward=reward, done=done)), flush=True)
    finally:
        environment.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['freeze', 'serve'])
    parser.add_argument('path', type=Path)
    arguments = parser.parse_args()
    freeze(arguments.path) if arguments.mode == 'freeze' else serve(arguments.path)

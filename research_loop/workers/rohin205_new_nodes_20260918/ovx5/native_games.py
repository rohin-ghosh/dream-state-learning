"""Native CPU game adapter; mocks are test-only, never a runtime fallback."""

import hashlib
import importlib
import json
import math
import re


PROFILES = {
    0: dict(name='GAMES-TAXI-A', environment='Taxi-v3', options={}),
    1: dict(name='GAMES-FROZENLAKE-A', environment='FrozenLake-v1', options={'is_slippery': False}),
    2: dict(name='GAMES-CLIFF-A', environment='CliffWalking-v0', options={}),
    3: dict(name='GAMES-BLACKJACK-A', environment='Blackjack-v1', options={}),
    4: dict(name='GAMES-CARTPOLE-A', environment='CartPole-v1', options={}),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def plain(value):
    if hasattr(value, 'tolist'):
        return plain(value.tolist())
    if hasattr(value, 'item'):
        return plain(value.item())
    if isinstance(value, (tuple, list)):
        return [plain(entry) for entry in value]
    if isinstance(value, dict):
        return {str(key): plain(entry) for key, entry in value.items()}
    if isinstance(value, bytes):
        return value.decode('ascii')
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError('finite_native_observation_required')
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise TypeError('unsupported_native_observation')


def parse_action(text):
    match = re.fullmatch(r'GAME_ACTION ([0-9]{1,3})', text.strip())
    if not match:
        raise ValueError('one_literal_GAME_ACTION_integer_required')
    return int(match.group(1))


class NativeGame:
    def __init__(self, environment, name, seed, provider, version):
        self.environment = environment
        self.name = name
        self.seed = seed
        self.provider = provider
        self.version = version
        self.turns = 0
        self.ended = False
        self.seen_origins = set()
        self.receipts = []

    @classmethod
    def installed(cls, physical, seed):
        if physical not in PROFILES:
            raise ValueError('caption_reserved_or_unassigned_physical')
        try:
            module = importlib.import_module('gymnasium')
        except ModuleNotFoundError as error:
            if error.name != 'gymnasium':
                raise
            module = importlib.import_module('gym')
        profile = PROFILES[physical]
        environment = module.make(profile['environment'], **profile['options'])
        return cls(environment, profile['environment'], seed, module.__name__, module.__version__)

    def observation(self, value):
        observed = dict(native=plain(value))
        native = self.environment.unwrapped
        if self.name == 'Taxi-v3':
            observed['decoded_public_state'] = plain(list(native.decode(int(value))))
            observed['decoded_fields'] = ['taxi_row', 'taxi_column', 'passenger_location', 'destination_location']
            observed['map'] = plain(native.desc)
            observed['locations'] = plain(native.locs)
            observed['actions'] = ['SOUTH', 'NORTH', 'EAST', 'WEST', 'PICKUP', 'DROPOFF']
        elif self.name == 'FrozenLake-v1':
            observed['map'] = plain(native.desc)
            observed['actions'] = ['LEFT', 'DOWN', 'RIGHT', 'UP']
        elif self.name == 'CliffWalking-v0':
            observed['grid_shape'] = plain(native.shape)
            observed['public_cliff_cells'] = plain(native._cliff)
            observed['actions'] = ['UP', 'RIGHT', 'DOWN', 'LEFT']
        elif self.name == 'Blackjack-v1':
            observed['fields'] = ['player_sum', 'dealer_showing', 'usable_ace']
            observed['actions'] = ['STICK', 'HIT']
        elif self.name == 'CartPole-v1':
            observed['fields'] = ['cart_position', 'cart_velocity', 'pole_angle', 'pole_angular_velocity']
            observed['actions'] = ['LEFT', 'RIGHT']
        return observed

    def reset(self):
        if self.receipts:
            raise ValueError('new_episode_requires_new_explicit_session')
        try:
            outcome = self.environment.reset(seed=self.seed)
        except TypeError:
            self.environment.seed(self.seed)
            outcome = self.environment.reset()
        value = outcome[0] if isinstance(outcome, tuple) and len(outcome) == 2 and isinstance(outcome[1], dict) else outcome
        receipt = dict(schema='R206_NATIVE_GAME_RESET_V1', provider=self.provider, version=self.version,
            environment=self.name, seed=self.seed, observation=self.observation(value),
            action_count=int(self.environment.action_space.n), split='TRAIN', native_call='reset', synthetic=False)
        receipt['sha256'] = digest(receipt)
        self.receipts.append(receipt)
        return receipt

    def step(self, raw_action, origin):
        if not self.receipts or self.ended or self.turns >= 64:
            raise ValueError('active_bounded_game_required')
        if origin.get('kind') != 'TRAIN_CHILD_RESPONSE' or origin.get('record_index', -1) <= 5846:
            raise ValueError('new_clone_response_origin_required')
        key = (origin['record_index'], origin['record_sha256'])
        if key in self.seen_origins:
            raise ValueError('no_redispatch_of_origin')
        action = parse_action(raw_action)
        if not self.environment.action_space.contains(action):
            raise ValueError('action_out_of_native_space')
        self.seen_origins.add(key)
        outcome = self.environment.step(action)
        if len(outcome) == 5:
            observation, reward, terminated, truncated, information = outcome
        else:
            observation, reward, done, information = outcome
            truncated = bool(information.get('TimeLimit.truncated', False))
            terminated = bool(done) and not truncated
        self.turns += 1
        self.ended = bool(terminated or truncated)
        receipt = dict(schema='R206_NATIVE_GAME_STEP_V1', environment=self.name, provider=self.provider,
            version=self.version, turn=self.turns, action=action, origin=origin,
            observation=self.observation(observation), reward=plain(reward), terminated=bool(terminated),
            truncated=bool(truncated), previous_sha256=self.receipts[-1]['sha256'], native_call='step', synthetic=False)
        receipt['sha256'] = digest(receipt)
        self.receipts.append(receipt)
        return receipt


def feedback(receipt):
    visible = {key: receipt[key] for key in ('environment', 'action', 'observation', 'reward', 'terminated', 'truncated') if key in receipt}
    return 'Tool result status: COMPLETE\nActual native game observation: ' + json.dumps(visible, sort_keys=True) + '\nReceipt: ' + receipt['sha256']

"""Role-isolated adapter of the exact original adopted runner, with new seeds."""

import argparse
from copy import deepcopy
import importlib
import os
from pathlib import Path
import sys
import time
from types import FunctionType, SimpleNamespace

import execution as common
from construct_candidate import ADOPTED_EPOCH, ADOPTED_SOURCE, ORIGINAL_SEEDS, digest, require, sha


def check_config(config, launch, expected_config_sha):
    require(config['diagnostic_epoch_sha256'] == digest(config['diagnostic_epoch'])
        and tuple(config['diagnostic_epoch']['sampling_seeds']) == common.SEEDS
        and tuple(config['seeds']) == common.SEEDS, 'new_sampling_epoch_and_seeds')
    require(config['job_id'] == digest(config['job_identity'])
        and config['job_identity']['diagnostic_epoch_sha256'] == config['diagnostic_epoch_sha256'], 'stable_new_job')
    require(config['diagnostic_epoch']['judge_epoch_sha256'] == ADOPTED_EPOCH
        and config['source_manifest_sha256'] == ADOPTED_SOURCE, 'original_science_binding')
    require(launch['block_id'] == config['block_id']
        and launch['diagnostic_epoch_sha256'] == config['diagnostic_epoch_sha256']
        and launch['job_configs'][config['job_id']] == expected_config_sha, 'bound_fresh_block_launch')
    require(launch['created_unix'] <= time.time() < launch['deadline_unix']
        <= min(launch['created_unix'] + 2400, config['hard_end_unix']), 'original_finite_wall_bound')
    require(Path(config['job_root']) == Path(config['block_root']) / 'jobs' / config['job_id']
        and Path(config['root']) == Path(config['job_root']) / 'view', 'isolated_new_job_root')
    original = config['original_config']
    for key in ('adapter_sha256', 'judge_rank', 'judge_step', 'token_budget', 'scenes',
            'parent_tokens', 'source_context_loaded', 'training_updates', 'plain_base',
            'player_physical', 'judge_physical', 'source_manifest_sha256', 'freshness_sha256',
            'primary_config', 'primary_config_sha256'):
        require(config[key] == original[key], 'unchanged_original_field:' + key)
    require(config['token_budget'] == 6144 and config['parent_tokens'] == 0
        and config['source_context_loaded'] is False and config['training_updates'] == 0, 'frozen_parent_free_budget')
    require(config['preregistration'] == common.PREREGISTRATION
        and tuple(config['expected_scene_ids']) == common.SCENE_IDS, 'preregistered_document_and_scenes')
    identity = dict(config['identity'], condition=original['identity']['condition'])
    require(identity == original['identity'], 'only_condition_label_changes')
    arm = config['job_identity']['arm']
    require(config['source_checkpoint'] == config['diagnostic_epoch']['source_checkpoints'][arm]['source_age'],
        'same_original_checkpoint_not_latest')
    if config.get('proof_only') is True:
        common.validate_cpu_repair(config['cpu_repair'], config['diagnostic_epoch_sha256'])
        require(config['execution_incarnation_sha256'] == digest(config['cpu_repair'])
            == config['job_identity']['execution_incarnation_sha256'], 'bound_cpu_incarnation')


def denial(path):
    try:
        with Path(path).open('rb') as stream:
            stream.read(1)
    except (PermissionError, FileNotFoundError, NotADirectoryError):
        return True
    except IsADirectoryError:
        return False
    return False


def custody(config, role, diagnostic_path=None):
    require(os.getuid() == config['expected_uid'], 'original_user')
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    require(boot == config['protected_policy']['receiving_boot_id'], 'same_receiving_boot')
    forbidden = config['custody_forbidden'] + (config['player_private_paths'] if role == 'player' else [])
    checks = {path: denial(path) for path in forbidden}
    if diagnostic_path is not None:
        common.write_once(diagnostic_path, dict(private_denials=checks, role=role, uid=os.getuid(),
            boot_id=boot, pid=os.getpid(), observed_unix=time.time(), model_loaded=False,
            config_sha256=config['diagnostic_config_sha256'],
            diagnostic_epoch_sha256=config['diagnostic_epoch_sha256'],
            execution_incarnation_sha256=config.get('execution_incarnation_sha256')))
    require(all(checks.values()), 'private_paths_and_host_proc_must_be_inaccessible')
    device = config['role_devices'][role]
    proof = {}
    for index in range(8):
        try:
            descriptor = os.open('/dev/nvidia' + str(index), os.O_RDWR)
        except OSError as error:
            proof[str(index)] = dict(opened=False, errno=error.errno)
        else:
            os.close(descriptor)
            proof[str(index)] = dict(opened=True)
    require(proof[str(device['physical'])]['opened'] is True
        and sum(row['opened'] for row in proof.values()) == 1
        and os.environ.get('CUDA_VISIBLE_DEVICES') == device['uuid'], 'one_assigned_gpu_seven_denied')
    return dict(private_denials=checks, device_opens=proof, boot_id=boot,
        role=role, uid=os.getuid(), pid=os.getpid())


def verify_public(config):
    root = Path(config['root'])
    common.regular(Path(config['block_root']) / 'PREREGISTRATION.md', common.PREREGISTRATION['sha256'])
    for name, expected in config['public_files'].items():
        common.regular(root / name, expected)
    for name, expected in config['original_source_closure'].items():
        common.regular(root / 'source' / name, expected)
    for name, expected in config['runtime_files'].items():
        common.regular(Path(config['block_root']) / 'runtime' / name, expected)
    if config['source_checkpoint']:
        source = config['source_checkpoint']
        for name, reference in source['copy_files'].items():
            common.regular(root / 'sources' / source['source_relative'] / name, reference['sha256'])
    require(common.read(root / 'FRESHNESS_VERIFIED.json')['eligible'] is True, 'original_exposure_eligible')
    require(tuple(sorted(scene['contest_id'] for scene in common.read(root / 'GAME_MANIFEST.json')['contests']))
        == tuple(config['expected_scene_ids']), 'pinned_manifest_scene_identity')


class TaggedRuntime:
    def __init__(self, original, diagnostic_sha, root, expected_identity=None):
        self.original = original
        self.diagnostic_sha = diagnostic_sha
        self.root = Path(root)
        self.expected_identity = expected_identity

    def __getattr__(self, name):
        return getattr(self.original, name)

    def write(self, path, value):
        require(Path(path).resolve().is_relative_to(self.root.resolve()), 'job_local_output_only')
        require(isinstance(value, dict), 'tagged_dictionary_receipt')
        value['diagnostic_epoch_sha256'] = self.diagnostic_sha
        value['sampling_replication_not_training_replication'] = True
        return self.original.write(path, value)

    def wait(self, path, deadline):
        value = self.original.wait(path, deadline)
        require(value.get('diagnostic_epoch_sha256') == self.diagnostic_sha, 'same_diagnostic_reply')
        return value

    def read(self, path):
        value = self.original.read(path)
        if Path(path).parent == self.root / 'queue':
            require(value.get('diagnostic_epoch_sha256') == self.diagnostic_sha, 'same_diagnostic_request')
        return value

    def Backend(self, source, root):
        backend = self.original.Backend(source, root)
        if self.expected_identity is not None:
            for field in ('base_sha256', 'adapter_state_sha256', 'decoder', 'tokenizer_backend_sha256',
                    'chat_template_sha256', 'library_versions', 'all_parameters_frozen', 'optimizer_created'):
                require(backend.identity[field] == self.expected_identity[field], 'original_backend_identity:' + field)
        return backend


def wrapped_role(original, config, role):
    def verify(new_config):
        require(new_config is config, 'one_bound_config_per_role')
        legacy_validation = dict(config, seeds=list(ORIGINAL_SEEDS))
        original.epoch.require_config(legacy_validation, time.time())
        verify_public(config)
        if role == 'judge':
            original.verify(legacy_validation)
        return Path(config['root']), config['identity']

    epoch = SimpleNamespace(**{name: getattr(original.epoch, name) for name in dir(original.epoch)
        if not name.startswith('__')})
    epoch.SEEDS = common.SEEDS
    runtime = TaggedRuntime(original.runtime, config['diagnostic_epoch_sha256'], config['root'],
        config.get('original_parameter_identity'))
    globals_for_role = dict(original.__dict__, verify=verify, epoch=epoch, runtime=runtime)
    original_function = getattr(original, role)
    return FunctionType(original_function.__code__, globals_for_role, original_function.__name__,
        original_function.__defaults__, original_function.__closure__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--launch-sha256', required=True)
    parser.add_argument('--review-sha256')
    parser.add_argument('--role', choices=('player', 'judge'), required=True)
    parser.add_argument('--mode', choices=('proof', 'run'), required=True)
    args = parser.parse_args()
    common.regular(args.config, args.config_sha256)
    config = common.read(args.config)
    require(not config.get('proof_only') or args.mode == 'proof', 'cpu_diagnostic_cannot_load_models')
    launch_path = Path(config['block_root']) / 'BLOCK_LAUNCH.json'
    common.regular(launch_path, args.launch_sha256)
    launch = common.read(launch_path)
    check_config(config, launch, args.config_sha256)
    if args.mode == 'run':
        require(args.review_sha256 is not None, 'explicit_model_run_review_required')
        review_path = Path(config['block_root']) / 'GPU_REVIEW.json'
        common.regular(review_path, args.review_sha256)
        review = common.read(review_path)
        common.regular(Path(config['block_root']) / 'PROOFS_COMPLETE.json', review['reviewed_proof_sha256'])
        require(review['launch_sha256'] == args.launch_sha256
            and review['diagnostic_epoch_sha256'] == config['diagnostic_epoch_sha256'], 'reviewed_exact_new_run')
    view = Path(config['root'])
    marker = view / (args.role + '_' + args.mode + '_STARTED.json')
    common.write_once(marker, dict(config_sha256=args.config_sha256, launch_sha256=args.launch_sha256,
        pid=os.getpid(), mode=args.mode, role=args.role, observed_unix=time.time(),
        diagnostic_epoch_sha256=config['diagnostic_epoch_sha256']))
    try:
        config['diagnostic_config_sha256'] = args.config_sha256
        proof = custody(config, args.role,
            view / (args.role + '_CUSTODY_PATH_DIAGNOSTIC.json') if args.mode == 'proof' else None)
        verify_public(config)
        sys.path.insert(0, str(view / 'source'))
        original = importlib.import_module('research_loop.workers.post_recovery_age_queue_20260918.runner')
        require(Path(original.__file__).resolve() == view / 'source/research_loop/workers/post_recovery_age_queue_20260918/runner.py',
            'bound_original_runner_import')
        config['deadline_unix'] = launch['deadline_unix']
        if args.mode == 'proof':
            if args.role == 'judge':
                original.verify(dict(config, seeds=list(ORIGINAL_SEEDS)))
            for module in ('torch', 'transformers', 'peft', 'safetensors', 'numpy'):
                importlib.import_module(module)
            for module, expected in config['original_parameter_identity']['library_versions'].items():
                require(importlib.import_module(module).__version__ == expected, 'original_library_version:' + module)
            common.write_once(view / (args.role + '_CUSTODY_PROOF.json'), dict(proof,
                config_sha256=args.config_sha256, launch_sha256=args.launch_sha256,
                diagnostic_epoch_sha256=config['diagnostic_epoch_sha256'],
                model_loaded=False, observed_unix=time.time(), status='PROVED_NO_MODEL_LOADED'))
            return
        prior = common.read(view / (args.role + '_CUSTODY_PROOF.json'))
        require(prior['config_sha256'] == args.config_sha256 and prior['launch_sha256'] == args.launch_sha256,
            'own_successful_cpu_proof_required')
        function = wrapped_role(original, config, args.role)
        function(config)
        verify_public(config)
    except Exception as error:
        common.write_once(view / (args.role + '_' + args.mode + '_FAILED.json'), dict(
            error_type=type(error).__name__, error=str(error), result='INCOMPLETE_NOT_ZERO_NO_RETRY',
            diagnostic_epoch_sha256=config['diagnostic_epoch_sha256'], observed_unix=time.time()))
        raise


if __name__ == '__main__':
    main()

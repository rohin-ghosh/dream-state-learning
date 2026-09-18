"""Bind only Main's public caption client and environment to reserved physical3."""

from pathlib import Path
import shutil
import time

from math_c import HOME, read, require, sha, write


CLIENT = {
    'gpu/ny_caption_life.py': '1978a3541323e7b607f5b5c66bfc70707b0af4e71d25b5b31f888f35ccd80a4a',
    'gpu/ny_caption_data.py': 'f9feb57ee6698d95fb1f88fcfe34104244ad1cfd85ca2db625cf403cfe7e184b',
    'gpu/orch_r125_continual_guard.py': '6a5968253e8fa5c1dc51e9955c836e43ff051d17e2829799e5edb85311eb184c',
}


def bind(source, plan, target):
    require(plan['physical'] == 3, 'reserved_caption_clone_only')
    packet = HOME.parent / 'caption_client'
    environment_path = Path('/localhome/local-rohing/orch_r210_caption_service_20260918/session1/CHILD_ENVIRONMENT.json')
    require(sha(environment_path) == sha(packet / 'CHILD_ENVIRONMENT.json'), 'actual_public_environment_packet')
    environment = read(environment_path)
    require(set(environment) == {'policy', 'scenes', 'help', 'scoring'}
        and environment['policy'] == 'R210_LANGUAGE_NATIVE_CAPTION_BATCH_V1', 'public_environment_only')
    require(sha(source / 'gpu/orch_r125_continual_guard.py') ==
        '1b12ff40ae7d88c06b956cf8c624aa8b010781f66a4eb0f630455f1be5e9dab6', 'same_pre_activation_guard')
    for name, digest in CLIENT.items():
        require(sha(packet / name) == digest, 'bound_client_source')
        shutil.copyfile(packet / name, source / name)
        compile((source / name).read_text(), str(source / name), 'exec')
    scenes = ['Scene ' + str(scene['number']) + ': ' + '. '.join(scene['scene'].split('. ')[:2]) + '.'
        for scene in environment['scenes']]
    facts = environment['help'] + '\nSupplied image-only scene descriptions:\n' + '\n'.join(scenes) + '\n' + environment['scoring']
    require(len(facts.encode()) <= 2048, 'existing_environment_facts_bound')
    plan['think_act_learn']['environment_facts'] = facts
    write(target / 'CAPTION_ENVIRONMENT.json', environment)
    write(target / 'CAPTION_BINDING.json', dict(client_pins=CLIENT, Main_cpu_tests_passed=23,
        socket='/tmp/r210_caption_n4.sock', life_root=plan['root'], physical=3,
        environment_sha256=sha(environment_path), observed_unix=time.time(),
        private_reference_files_read=False, scorer_loaded_into_child=False,
        CPU_ACT_disabled=True, prior_screen_unchanged=True, new_phase='R210_CAPTION_GAME'))


def publish_opening(root, target):
    environment = read(target / 'CAPTION_ENVIRONMENT.json')
    first = environment['scenes'][0]
    require(first['number'] == 1, 'actual_numbered_scene')
    description = '. '.join(first['scene'].split('. ')[:2]) + '.'
    message = ('I am Astra. This is a NEW R210 caption environment, not the previous task. '
        'Scene 1: ' + description + '\nIn ACT use separate lines:\nScene: 1\nDirection: your chosen approach\n'
        'Count: 2\nCaption: your first caption\nCaption: your second caption\n'
        'Use at most 50 words per caption. No Python executes. Actual feedback arrives before LEARN. '
        'Seek distinct accepted jokes; scoring is provisional. What two different captions will you try?')
    require(len(message.split()) <= 120, 'bounded_operator_opener')
    from gpu.orch_r127_pilot_console import publish_parent
    publication = publish_parent(str(root / 'life'), 'Astra', message)
    write(target / 'PARENT_OPENING.json', dict(publication=publication, message=message,
        published_unix=time.time(), operator_intro_not_model_response=True,
        environment_sha256=sha(target / 'CAPTION_ENVIRONMENT.json'), new_phase='R210_CAPTION_GAME'))

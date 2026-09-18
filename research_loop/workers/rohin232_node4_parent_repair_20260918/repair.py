"""NON-MATERIAL, explicitly bound R230 CPU-parent policy projection; no activation."""

import copy
import hashlib
import inspect
import json
from pathlib import Path
import types


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FLEET = REPO / 'research_loop/workers/rohin174_parenting_20260917/node4/R195_FLEET'
CURRICULUM = REPO / 'research_loop/workers/rohin230_curriculum_20260918'
ALLOWED = (2, 3, 5, 6)
MARKER = 'r230_parent_repair'
POLICY = 'R232_BOUND_R230_NODE4_PARENT_REPAIR_V1'

DECISION_EDITS = (
    ("count < 3, 'object_delivered_budget_exhausted'",
     "type(count) is int and count >= 0, 'r230_valid_delivered_count'"),
    ("rationale['disposition'] in ('continue', 'set_aside')\n"
     "        and (count < 2 or rationale['disposition'] == 'set_aside'), 'third_turn_releases_object'",
     "rationale['disposition'] in ('continue', 'set_aside'), 'r230_known_disposition'"),
    ("if count == 2 or rationale['disposition'] == 'set_aside':",
     "if rationale['disposition'] == 'set_aside':"),
)
TICK_EDITS = (("baseline + config['cadence_responses']", 'baseline + 1'),)
PROMPT_EDITS = (
    ('expiration counter. Keep its three delivered turns maximum; on turn three leave that mismatch '
     "unresolved and set the repetitive correction aside, NOT the child's project. Propose a different "
     'concrete step within the same child-chosen object, naming its exact child quote in next_task.',
     'expiration counter. Delivered-turn counts remain historical evidence, not automatic retirement. '
     'Continue when current evidence warrants it. If you judge a correction unproductive, voluntarily '
     'set it aside as unresolved and propose a concrete step within the same child-chosen object, '
     'naming its exact child quote in next_task.'),
    ('or exhausted correction budget.', 'or an automatic turn counter.'),
    ('Preserve CREDIT attribution and the existing three-turn unresolved-mismatch budget, without expiring the project.',
     'Preserve CREDIT attribution and every delivered-object count, without automatic retirement.'),
)
BRIEF = (
    '\n' + POLICY + ': only the four explicitly bound R230-enriched parents use this repair. '
    'Offer a short responsive contribution at each new committed child-response opportunity, '
    'after any pending parent publication renders. Historical SPARSE/cadence/object_turn_limit fields '
    'are retained as provenance; the bound repair uses cadence one and evidence-based retirement. '
    'Keep stable object IDs and all counts; never rename a correction to evade its history. '
    'Reconsider whether the latest actual evidence warrants continuing, changing the approach, '
    'or quitting an unproductive correction. Repetition without progress is a reason to reconsider, '
    'not an invitation to repeat forever. Voluntary set_aside must retain every existing release, '
    'unresolved, next-step, continuity and receipt check. Honest silence remains possible and recorded; '
    'do not choose silence merely because a turn count exceeded three or old sparse advice says to wait. '
    'The current R230 curriculum remains authoritative: diverse math, reading/recall, reflection and '
    'writing grounded in actual material; keep actual caption play central for the caption child. '
    'No invented observation, score, execution, peer/human voice or retention claim. '
    'Keep Astra identity, English, the assigned B walkthrough or C questions-only style, '
    'the original word/byte limits and all privacy/control/source-masking boundaries. '
    'This is not a learner, training-filter, control, lease or scientific-claim change.'
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked_file(path, expected):
    path = Path(path)
    require(path.is_absolute() and path == path.resolve() and path.is_file(), 'canonical_source_file')
    require(sha(path) == expected, 'source_pin_mismatch:' + str(path.relative_to(REPO)))


def verify_sources(physical):
    require(type(physical) is int and physical in ALLOWED, 'only_four_R230_enriched_parents')
    pins = read(HERE / 'SOURCE_PINS.json')
    for relative, checksum in pins.items():
        checked_file(REPO / relative, checksum)
    arm = 'C' if physical == 6 else 'B'
    bundle = FLEET.parents[1] / 'node3' / ('source_' + arm)
    manifest = read(bundle / 'ARM_BUNDLE.json')
    require(manifest['arm'] == arm, 'bound_bundle_arm')
    for relative, proof in manifest['files'].items():
        path = bundle / relative
        require(path.resolve().is_relative_to(bundle), 'bundle_source_scope')
        checked_file(path, proof['sha256'])
    original_dir = FLEET / f'r210_parent{physical}'
    enriched_dir = CURRICULUM / f'physical{physical}'
    original = read(original_dir / 'CONFIG.json')
    enriched = read(enriched_dir / 'CONFIG.json')
    prepared = read(enriched_dir / 'PREPARED.json')
    binding = read(original_dir / 'BINDING.json')
    require(binding['bundle'] == str(bundle), 'same_original_bundle')
    require(binding.get('physical', physical) == physical, 'same_original_physical')
    require(enriched['root'] == binding['remote'] + '/life', 'same_original_life')
    require(prepared['policy'] == 'R230_NODE4_PARENT_CURRICULUM_V1'
        and prepared['old_config_sha256'] == sha(original_dir / 'CONFIG.json')
        and prepared['config_sha256'] == sha(enriched_dir / 'CONFIG.json')
        and prepared['changed_fields'] == ['programme_path', 'programme_sha256'], 'bound_R230_preparation')
    expected = dict(original, programme_path=str(enriched_dir / 'PROGRAMME.txt'),
        programme_sha256=prepared['new_programme_sha256'])
    require(enriched == expected, 'only_existing_R230_programme_change')
    require(prepared['original_programme_sha256'] == original['programme_sha256'], 'original_programme_pin')
    for config in (original, enriched):
        for label in ('programme', 'principles'):
            checked_file(Path(config[label + '_path']), config[label + '_sha256'])
    require(enriched['r175_arm'] == arm and enriched['community_learner'] is False
        and enriched['programme'] == 'raw_parented', 'same_parented_arm_not_control')
    return enriched, bundle


def expected_config(physical):
    config, unused_bundle = verify_sources(physical)
    config[MARKER] = dict(policy=POLICY, physical=physical,
        source_pins_sha256=sha(HERE / 'SOURCE_PINS.json'),
        adapter_sha256=sha(HERE / 'repair.py'), entrypoint_sha256=sha(HERE / 'parent.py'),
        curriculum_config_sha256=sha(CURRICULUM / f'physical{physical}/CONFIG.json'),
        effective_cadence_responses=1, retirement='EVIDENCE_BASED_NOT_AUTOMATIC')
    return config


def load_config(physical):
    expected = expected_config(physical)
    config = read(HERE / f'physical{physical}/CONFIG.json')
    require(config == expected, 'exact_bound_R230_config')
    return config


def project(function, edits, namespace):
    source = inspect.getsource(function)
    for before, after in edits:
        require(source.count(before) == 1, 'exact_frozen_projection:' + function.__name__)
        source = source.replace(before, after)
    projected = dict(function.__globals__, **namespace)
    filename = str(HERE / 'repair.py') + ':' + function.__name__
    exec(compile(source, filename, 'exec'), projected)
    return projected[function.__name__]


def adapt(frozen, config):
    """Return a private function namespace; never patch the shared frozen policy."""
    if MARKER not in config:
        return frozen
    physical = config[MARKER].get('physical')
    expected = expected_config(physical)
    require(config == expected, 'exact_bound_R230_config')
    unused_config, bundle = verify_sources(physical)
    for module, filename in (
        (frozen, 'orch_r166_parent_policy.py'),
        (frozen.community, 'orch_r153_community_parents.py'),
        (frozen.parent, 'orch_r133_programme_parent.py'),
    ):
        require(Path(module.__file__).resolve() == bundle / 'gpu' / filename, 'loaded_frozen_source_identity')
    frozen.validate(config)
    approved = copy.deepcopy(config)
    community = types.SimpleNamespace(**vars(frozen.community))
    community.decision = project(frozen.community.decision, DECISION_EDITS, {})
    projected_decision = project(frozen.decision, (), dict(community=community))

    def guard(candidate):
        require(candidate == approved and config == approved, 'exact_bound_R230_config')
        return frozen.validate(candidate)

    def decision(response, state, memory_state):
        guard(config)
        return projected_decision(response, state, memory_state)

    def prompt(candidate, state, memory_state):
        if MARKER not in candidate:
            return frozen.prompt(candidate, state, memory_state)
        guard(candidate)
        instruction, payload = frozen.prompt(candidate, state, memory_state)
        cadence = 'two' if approved['r175_arm'] == 'B' else 'three'
        edits = PROMPT_EDITS + ((f'Every {cadence} responses,', 'At each new committed-response opportunity,'),)
        for before, after in edits:
            require(instruction.count(before) == 1, 'exact_frozen_prompt_projection')
            instruction = instruction.replace(before, after)
        return instruction + BRIEF, payload

    projected_tick = project(frozen.tick, TICK_EDITS, dict(validate=guard, decision=decision,
        prompt=lambda *arguments, **keywords: proxy.prompt(*arguments, **keywords)))

    def tick(repository, candidate, output, seed, state):
        if MARKER not in candidate:
            return frozen.tick(repository, candidate, output, seed, state)
        return projected_tick(repository, candidate, output, seed, state)

    def validate(candidate):
        return guard(candidate) if MARKER in candidate else frozen.validate(candidate)

    proxy = types.SimpleNamespace(**vars(frozen))
    proxy.validate, proxy.prompt, proxy.decision, proxy.tick = validate, prompt, decision, tick
    return proxy

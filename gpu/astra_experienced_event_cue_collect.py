"""DEV guided cue trajectories over child-authored external EVENT text; no fit."""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import time

from gpu import astra_experienced_event_microloop as source
from gpu import astra_experienced_event_read_route as access
from organism_v6 import experienced_event_cue_collection as cue


MASTER = "ASTRA-CUE-TRAIN-EXTERNAL-EVENT-20260914-A1"
MAX_CALLS = 40
REUSE_MAX_CALLS = 24
EXPLICIT_GUIDANCE = (
    '\n\nTeacher strategy for this training collection only: '
    'Your first decision must be READ EVENT using the first address in the public EVENTS list. '
    'After each read, compare the returned EVENT AT with the public task NODE and its GOT '
    'with the public GOAL. If both match, commit ROUTE using that EVENT\'s DID port. '
    'Otherwise READ EVENT using the unread listed address, if one remains. '
    'Never ROUTE before a read. If no returned record matches, do not invent evidence. '
    'Use only listed addresses and ports, within the public call limits. '
    'Output only the permitted command, without explanation.'
)


def training_banks():
    banks = [source.material.build_bank(MASTER + "-" + str(index)) for index in range(2)]
    seen = {value for fact in source.material.build_bank(source.MASTER)
            for key, value in fact.items() if type(value) is str}
    for bank in banks:
        identifiers = {value for fact in bank for key, value in fact.items() if type(value) is str}
        source.require(not seen.intersection(identifiers), "cue_train_identity_overlap")
        seen.update(identifiers)
    return banks


def load_reused_experiences(directory, *, expected_base_sha256):
    """Read original experience evidence only; no original cue rows or scores.

    Individual/aggregate records must agree exactly. Hashes pin this read, not
    authenticity against coherent replacement of the entire original bundle.
    """
    root, hashes = Path(directory).resolve(), {}
    source.require(not (root / 'FAILED.json').exists(), 'failed_original_collection')
    source.require(type(expected_base_sha256) is str and len(expected_base_sha256) == 64
                   and all(char in '0123456789abcdef' for char in expected_base_sha256), 'expected_base_hash_required')

    def read(relative):
        path = root / relative
        source.require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 2 * 1024 ** 2,
                       'bounded_original_file_required:' + relative)
        raw = path.read_bytes()
        hashes[relative] = sha256(raw).hexdigest()
        return json.loads(raw)

    result, request = read('RESULT.json'), read('REQUEST.json')
    source.require(result.get('schema') == request.get('schema') == 'DEV_GUIDED_EXTERNAL_EVENT_CUE_COLLECTION_V1'
                   and result.get('master') == request.get('master') == MASTER
                   and result.get('status') == 'COLLECTION_COMPLETE_NO_FIT'
                   and result.get('frozen_base_unchanged') is True, 'complete_original_collection_required')
    for name, expected in dict(banks=2, admitted_events=8, event_denominator=8, cue_task_denominator=8, fits=0).items():
        source.require(type(result.get(name)) is int and result[name] == expected, 'original_count_mismatch:' + name)
    for document in (result, request):
        options = document.get('arguments', {})
        source.require(options.get('expected_base_sha256') == expected_base_sha256
                       and options.get('phase') == 'collect' and options.get('adapter_dir') is None,
                       'original_frozen_base_binding_mismatch')
    banks = []
    for bank_index, expected_bank in enumerate(training_banks()):
        prefix = 'BANK_%02d/' % bank_index
        bank, experiences = read(prefix + 'BANK.json'), read(prefix + 'EXPERIENCES.json')
        source.require(bank == expected_bank, 'original_training_bank_mismatch')
        source.require(type(experiences) is list and len(experiences) == 4, 'four_complete_experiences_required')
        memories = {}
        for index, (fact, experience) in enumerate(zip(bank, experiences), 1):
            individual = read(prefix + 'EXPERIENCE_%02d.json' % index)
            source.require(individual == experience and experience.get('fact') == fact
                           and experience.get('admitted') is True and experience.get('error') is None,
                           'original_experience_record_mismatch')
            for kind in ('exploration', 'event'):
                response = experience.get(kind)
                source.require(type(response) is dict and type(response.get('raw')) is str
                               and response.get('terminal') is True and response.get('truncated') is False
                               and response.get('error') is None, 'terminal_original_generation_required')
                if 'token_ids' in response:
                    token_ids = response['token_ids']
                    source.require(type(token_ids) is list and bool(token_ids)
                                   and all(type(token) is int for token in token_ids)
                                   and token_ids[-1] == result.get('tokenizer', {}).get('eos_token_id'),
                                   'original_terminal_token_mismatch')
            exploration, event = experience['exploration'], experience['event']
            expected_messages = source.material.observation_messages(fact, exploration['raw'])
            for response, messages in ((exploration, source.material.exploration_messages(fact)), (event, expected_messages)):
                if 'messages' in response:
                    source.require(response['messages'] == messages, 'original_generation_messages_mismatch')
            source.require(source.material.canonical_event(event['raw']) == source.material._event(fact),
                           'original_event_grounding_mismatch')
            memories[fact['event']] = event['raw']
        cue.validate_memory(bank, memories)
        banks.append(dict(bank=bank, experiences=experiences, raw_memory_by_address=memories))
    return dict(source_directory=str(root), input_file_sha256=hashes, banks=banks,
        source_metadata={name: result[name] for name in ('schema', 'master', 'status', 'admitted_events',
                         'frozen_base_unchanged')}, expected_base_sha256=expected_base_sha256,
        source_cue_rows_used=False, source_cue_scores_used=False)


def collect(engine, output, *, reused_experiences=None, teaching_mode=cue.DEFAULT_TEACHING_MODE):
    captures, reports = [], []
    if reused_experiences is not None:
        source.require(cue.GUIDANCE == EXPLICIT_GUIDANCE, 'explicit_strategy_required_for_reuse')
        source.write(output / 'REUSED_EXPERIENCES.json', reused_experiences)
    limit = REUSE_MAX_CALLS if reused_experiences is not None else MAX_CALLS

    def generate(messages):
        source.require(len(captures) < limit, "twenty_four_cue_call_cap" if reused_experiences is not None
                       else "forty_call_collection_cap")
        record = dict(call_index=len(captures), messages=messages, response=None, error=None)
        captures.append(record)
        try:
            record["response"] = engine.generate(messages)
        except BaseException as error:
            record["error"] = repr(error)
            raise
        finally:
            source.write(output / ("CALL_%03d.json" % record["call_index"]), record)
        return record["response"]

    for bank_index, bank in enumerate(training_banks()):
        directory = output / ("BANK_%02d" % bank_index)
        directory.mkdir(exist_ok=False)
        source.write(directory / "BANK.json", bank)
        events, memories = [], {}
        if reused_experiences is not None:
            reused = reused_experiences['banks'][bank_index]
            source.require(reused['bank'] == bank, 'reused_training_bank_mismatch')
            events, memories = reused['experiences'], reused['raw_memory_by_address']
            for index, episode in enumerate(events, 1):
                source.write(directory / ('EXPERIENCE_%02d.json' % index), episode)
        for fact in bank if reused_experiences is None else ():
            exploration = generate(source.material.exploration_messages(fact))
            episode = dict(fact=fact, exploration=exploration, event=None, admitted=False, error=None)
            if not exploration["terminal"] or exploration["truncated"]:
                episode["error"] = "nonterminal_exploration"
            else:
                try:
                    messages = source.material.observation_messages(fact, exploration["raw"])
                except ValueError as error:
                    episode["error"] = str(error)
                else:
                    event = generate(messages)
                    episode["event"] = event
                    if not event["terminal"] or event["truncated"]:
                        episode["error"] = "nonterminal_event"
                    else:
                        try:
                            source.require(source.material.canonical_event(event["raw"])
                                           == source.material._event(fact), "event_grounding_mismatch")
                        except ValueError as error:
                            episode["error"] = str(error)
                        else:
                            episode["admitted"] = True
                            memories[fact["event"]] = event["raw"]
            events.append(episode)
            source.write(directory / ("EXPERIENCE_%02d.json" % len(events)), episode)
        source.write(directory / "EXPERIENCES.json", events)
        if len(memories) == 4:
            report = cue.run_collection(bank, memories, generate, teaching_mode=teaching_mode)
        else:
            report = dict(status="SOURCE_INCOMPLETE_NO_CUE_EPISODES", episodes=[], student_rows=[],
                          physical_actor_calls=0, selected_successes=0)
        source.write(directory / "CUE_COLLECTION.json", report)
        reports.append(dict(bank=bank_index, admitted_events=len(memories), collection=report))
    source.write(output / "BANK_RESULTS.json", reports)
    source.require(not any(record["error"] is not None for record in captures), "native_callback_failure")
    source.require(not any(report["collection"].get("infrastructure_failures", 0) for report in reports),
                   "cue_infrastructure_failure")
    result = dict(banks=2, event_denominator=8, cue_task_denominator=8,
        admitted_events=sum(report["admitted_events"] for report in reports),
        selected_successes=sum(report["collection"]["selected_successes"] for report in reports),
        student_rows=sum(len(report["collection"]["student_rows"]) for report in reports),
        physical_model_calls=len(captures), fits=0,
        memory_kind="EXTERNAL_ADDRESS_ONLY_RAW_CHILD_EVENT_TEXT_NOT_PARAMETRIC_READ")
    if reused_experiences is not None:
        source.require(all(source.file_hash(Path(reused_experiences['source_directory']) / name) == digest
                           for name, digest in reused_experiences['input_file_sha256'].items()),
                       'original_experiences_changed_during_reuse')
        result.update(experiences_reused=8, new_exploration_event_calls=0, physical_actor_calls=len(captures),
                      input_file_sha256=reused_experiences['input_file_sha256'])
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("model-dir", "expected-base-sha256", "output", "gpu-uuid"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument('--reuse-experiences')
    parser.add_argument('--explicit-cue-strategy', action='store_true')
    parser.add_argument('--cue-adapter-dir')
    parser.add_argument('--adapter-collection')
    parser.add_argument('--public-feedback', action='store_true')
    args = parser.parse_args(argv)
    if bool(args.reuse_experiences) != args.explicit_cue_strategy:
        parser.error('--reuse-experiences and --explicit-cue-strategy must be supplied together')
    if bool(args.cue_adapter_dir) != bool(args.adapter_collection):
        parser.error('--cue-adapter-dir and --adapter-collection must be supplied together')
    if args.cue_adapter_dir and not args.reuse_experiences:
        parser.error('the selected memory actor requires explicit reused-experience collection')
    if args.public_feedback and not args.cue_adapter_dir:
        parser.error('--public-feedback requires the selected saved memory actor')
    source.require(os.environ.get("HF_HUB_OFFLINE") == "1"
                   and os.environ.get("TRANSFORMERS_OFFLINE") == "1", "offline_required")
    source.require(os.environ.get("CUDA_VISIBLE_DEVICES") == args.gpu_uuid, "exact_gpu_required")
    args.phase = "readout" if args.cue_adapter_dir else "collect"
    args.adapter_dir = args.cue_adapter_dir
    root = Path(args.output)
    if args.reuse_experiences:
        original = Path(args.reuse_experiences).resolve()
        source.require(not root.resolve().is_relative_to(original) and not original.is_relative_to(root.resolve()),
                       'fresh_output_separate_from_original_required')
    root.mkdir(parents=True, exist_ok=False)
    started = time.time()

    def check(phase):
        source.require(time.time() < started + 1200, "collection_deadline:" + phase)

    selected_guidance = EXPLICIT_GUIDANCE if args.explicit_cue_strategy else cue.GUIDANCE
    teaching_mode = cue.PUBLIC_FEEDBACK_MODE if args.public_feedback else cue.DEFAULT_TEACHING_MODE
    result = dict(schema='DEV_GUIDED_EXTERNAL_EVENT_CUE_REUSE_V1' if args.reuse_experiences
                  else "DEV_GUIDED_EXTERNAL_EVENT_CUE_COLLECTION_V1", master=MASTER,
        started_unix=started, arguments=vars(args),
        guidance=selected_guidance, guidance_sha256=sha256(selected_guidance.encode('utf-8')).hexdigest(),
        teaching_mode=teaching_mode,
        claim="COACHED_DATA_COLLECTION_NOT_AUTONOMOUS_CUE_OR_PARENTING_SUCCESS",
        runner_sha256=source.file_hash(__file__),
        source_sha256={Path(module.__file__).name: source.file_hash(module.__file__)
                       for module in (source, cue, source.material, source.native)})
    source.write(root / "REQUEST.json", result)
    previous_guidance = cue.GUIDANCE
    try:
        reused = None
        if args.reuse_experiences:
            reused = load_reused_experiences(args.reuse_experiences, expected_base_sha256=args.expected_base_sha256)
            result['input_file_sha256'] = reused['input_file_sha256']
            cue.GUIDANCE = selected_guidance
        if args.cue_adapter_dir:
            unused_bank, unused_episodes, unused_rows, provenance = source.load_collection(
                args.adapter_collection, serialization='FINAL_LF_ONLY')
            result['actor_training_result_sha256'] = access.validate_adapter(args.cue_adapter_dir, provenance)
            result['actor_adapter_file_sha256'] = access.ADAPTER_SHA256
            result['actor_memory_collection'] = provenance
        result['actor_kind'] = 'FROZEN_SAVED_MEMORY_LEARNER' if args.cue_adapter_dir else 'FROZEN_BASE'
        tokenizer = source.native.load_local_tokenizer(args.model_dir)
        result["tokenizer"] = source.native.tokenizer_signature(tokenizer)
        engine = source.Engine(args, tokenizer, check=check)
        result["runtime"] = engine.runtime
        adapter_parameters = None
        if args.cue_adapter_dir:
            from organism_v6.pcfl_vertical_train import _state_hash

            source.require(not any(parameter.requires_grad for parameter in engine.model.parameters()),
                           'collection_actor_must_be_frozen')
            adapter_parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                                  if '.lora_A.' in name or '.lora_B.' in name}
            source.require(bool(adapter_parameters), 'loaded_memory_adapter_parameters_required')
            result['actor_adapter_state_before'] = _state_hash(adapter_parameters)
        result.update(collect(engine, root, reused_experiences=reused, teaching_mode=teaching_mode))
        engine.verify_base()
        if adapter_parameters is not None:
            result['actor_adapter_state_after'] = _state_hash(adapter_parameters)
            source.require(result['actor_adapter_state_after'] == result['actor_adapter_state_before'],
                           'collection_changed_actor_adapter')
            source.require(access.validate_adapter(args.cue_adapter_dir, provenance)
                           == result['actor_training_result_sha256'], 'original_memory_adapter_changed')
        result.update(status="COLLECTION_COMPLETE_NO_FIT", frozen_base_unchanged=True,
                      finished_unix=time.time())
        source.write(root / "RESULT.json", result)
    except BaseException as error:
        result.update(status="FAILED", error=repr(error), finished_unix=time.time())
        source.write(root / "FAILED.json", result)
        raise
    finally:
        cue.GUIDANCE = previous_guidance


if __name__ == "__main__":
    main()

"""DEV guided cue trajectories over child-authored external EVENT text; no fit."""

import argparse
import os
from pathlib import Path
import time

from gpu import astra_experienced_event_microloop as source
from organism_v6 import experienced_event_cue_collection as cue


MASTER = "ASTRA-CUE-TRAIN-EXTERNAL-EVENT-20260914-A1"
MAX_CALLS = 40


def training_banks():
    banks = [source.material.build_bank(MASTER + "-" + str(index)) for index in range(2)]
    seen = {value for fact in source.material.build_bank(source.MASTER)
            for key, value in fact.items() if type(value) is str}
    for bank in banks:
        identifiers = {value for fact in bank for key, value in fact.items() if type(value) is str}
        source.require(not seen.intersection(identifiers), "cue_train_identity_overlap")
        seen.update(identifiers)
    return banks


def collect(engine, output):
    captures, reports = [], []

    def generate(messages):
        source.require(len(captures) < MAX_CALLS, "forty_call_collection_cap")
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
        for fact in bank:
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
            report = cue.run_collection(bank, memories, generate)
        else:
            report = dict(status="SOURCE_INCOMPLETE_NO_CUE_EPISODES", episodes=[], student_rows=[],
                          physical_actor_calls=0, selected_successes=0)
        source.write(directory / "CUE_COLLECTION.json", report)
        reports.append(dict(bank=bank_index, admitted_events=len(memories), collection=report))
    source.write(output / "BANK_RESULTS.json", reports)
    source.require(not any(record["error"] is not None for record in captures), "native_callback_failure")
    source.require(not any(report["collection"].get("infrastructure_failures", 0) for report in reports),
                   "cue_infrastructure_failure")
    return dict(banks=2, event_denominator=8, cue_task_denominator=8,
        admitted_events=sum(report["admitted_events"] for report in reports),
        selected_successes=sum(report["collection"]["selected_successes"] for report in reports),
        student_rows=sum(len(report["collection"]["student_rows"]) for report in reports),
        physical_model_calls=len(captures), fits=0,
        memory_kind="EXTERNAL_ADDRESS_ONLY_RAW_CHILD_EVENT_TEXT_NOT_PARAMETRIC_READ")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("model-dir", "expected-base-sha256", "output", "gpu-uuid"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args(argv)
    source.require(os.environ.get("HF_HUB_OFFLINE") == "1"
                   and os.environ.get("TRANSFORMERS_OFFLINE") == "1", "offline_required")
    source.require(os.environ.get("CUDA_VISIBLE_DEVICES") == args.gpu_uuid, "exact_gpu_required")
    args.phase, args.adapter_dir = "collect", None
    root = Path(args.output)
    root.mkdir(parents=True, exist_ok=False)
    started = time.time()

    def check(phase):
        source.require(time.time() < started + 1200, "collection_deadline:" + phase)

    result = dict(schema="DEV_GUIDED_EXTERNAL_EVENT_CUE_COLLECTION_V1", master=MASTER,
        started_unix=started, arguments=vars(args),
        claim="COACHED_DATA_COLLECTION_NOT_AUTONOMOUS_CUE_OR_PARENTING_SUCCESS",
        runner_sha256=source.file_hash(__file__),
        source_sha256={Path(module.__file__).name: source.file_hash(module.__file__)
                       for module in (source, cue, source.material, source.native)})
    source.write(root / "REQUEST.json", result)
    try:
        tokenizer = source.native.load_local_tokenizer(args.model_dir)
        result["tokenizer"] = source.native.tokenizer_signature(tokenizer)
        engine = source.Engine(args, tokenizer, check=check)
        result["runtime"] = engine.runtime
        result.update(collect(engine, root))
        engine.verify_base()
        result.update(status="COLLECTION_COMPLETE_NO_FIT", frozen_base_unchanged=True,
                      finished_unix=time.time())
        source.write(root / "RESULT.json", result)
    except BaseException as error:
        result.update(status="FAILED", error=repr(error), finished_unix=time.time())
        source.write(root / "FAILED.json", result)
        raise


if __name__ == "__main__":
    main()

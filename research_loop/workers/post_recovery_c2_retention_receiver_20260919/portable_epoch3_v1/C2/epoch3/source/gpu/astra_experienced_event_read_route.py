"""Zero-fit DEV self-issued memory access on four previously exposed tasks."""

import argparse
from contextlib import nullcontext
import os
from pathlib import Path
import time

from gpu import astra_experienced_event_microloop as source
from organism_v6 import experienced_event_read_route as controller


ARMS = ("BASE", "FITTED", "FITTED_READER_OFF")
ADAPTER_SHA256 = "8597605e7e07b882f613e359decee0193275d4bd16eacac8cd5c45db75f25788"


def validate_adapter(adapter, provenance):
    adapter = Path(adapter)
    terminal = source.read(adapter.parent / "RESULT.json")
    source.require(terminal.get("schema") == source.SCHEMA
                   and terminal.get("status") == "COMPLETE"
                   and terminal.get("phase") == "train"
                   and terminal.get("updates") == source.UPDATES
                   and terminal.get("frozen_base_unchanged") is True
                   and terminal.get("collection") == provenance,
                   "completed_same_source_training_required")
    source.require(not (adapter.parent / "FAILED.json").exists(), "failed_training_forbidden")
    source.require(terminal["adapter_files"].get("adapter_model.safetensors") == ADAPTER_SHA256,
                   "selected_adapter_required")
    for name, digest in terminal["adapter_files"].items():
        source.require(Path(name).name == name and source.file_hash(adapter / name) == digest,
                       "adapter_file_drift")
    return source.file_hash(adapter.parent / "RESULT.json")


def evaluate(engine, bank, arm, output):
    source.require(arm in ARMS, "unknown_arm")
    source.material._check_bank(bank)
    captures, episodes = [], []

    def generate(messages, role):
        source.require(len(captures) < 20, "twenty_call_per_arm_cap")
        with engine.model.disable_adapter() if role == "reader" and arm == "FITTED_READER_OFF" else nullcontext():
            response = engine.generate(messages)
        capture = dict(role=role, adapter_enabled=arm != "BASE" and not (
            arm == "FITTED_READER_OFF" and role == "reader"), generation=response)
        captures.append(capture)
        source.write(output / ("CALL_%03d.json" % len(captures)), capture)
        return response

    def read_memory(address):
        messages = [dict(role="system", content=source.world.MEMORY_SYSTEM),
                    dict(role="user", content=source.world.WRAPPERS[8].replace(
                        "{REQUEST}", "READ EVENT " + address))]
        return generate(messages, "reader")

    for fact in bank:
        transitions = {other["port"]: other["outcome"] for other in bank
                       if other["node"] == fact["node"]}
        episode = controller.run_episode(controller.public_task(fact),
            lambda messages: generate(messages, "actor"), read_memory,
            lambda port: transitions[port])
        episodes.append(dict(event=fact["event"], episode=episode))
        source.write(output / ("EPISODE_%02d.json" % len(episodes)), episodes[-1])
    source.write(output / "EPISODES.json", episodes)
    return dict(denominator=4, reached_goal=sum(row["episode"]["reached_goal"] for row in episodes),
        episodes_with_reads=sum(row["episode"]["memory_calls"] > 0 for row in episodes),
        model_calls=len(captures), actor_calls=sum(row["role"] == "actor" for row in captures),
        reader_calls=sum(row["role"] == "reader" for row in captures),
        terminal_reasons=[row["episode"]["terminal_reason"] for row in episodes], fits=0)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=ARMS, required=True)
    for name in ("model-dir", "expected-base-sha256", "adapter-dir", "collection", "output", "gpu-uuid"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args(argv)
    source.require(os.environ.get("HF_HUB_OFFLINE") == "1"
                   and os.environ.get("TRANSFORMERS_OFFLINE") == "1", "offline_required")
    source.require(os.environ.get("CUDA_VISIBLE_DEVICES") == args.gpu_uuid, "physical_gpu_binding_required")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()

    def check(phase):
        source.require(time.time() < started + 600, "ten_minute_arm_deadline:" + phase)

    report = dict(schema="DEV_SELF_ISSUED_READ_ROUTE_V1", arm=args.arm, started_unix=started,
        arguments=vars(args).copy(), claim="CONTEXTUAL_ACCESS_DIAGNOSTIC_NOT_GENERALIZATION_OR_PARENTING",
        source_sha256={Path(module.__file__).name: source.file_hash(module.__file__)
                       for module in (source, controller, source.material, source.native)},
        runner_sha256=source.file_hash(__file__))
    source.write(output / "REQUEST.json", report)
    try:
        bank, unused_episodes, unused_rows, provenance = source.load_collection(
            args.collection, serialization="FINAL_LF_ONLY")
        report["collection"] = provenance
        report["training_result_sha256"] = validate_adapter(args.adapter_dir, provenance)
        before = source.file_hash(Path(args.adapter_dir) / "adapter_model.safetensors")
        selected_adapter = args.adapter_dir
        args.phase = "readout"
        if args.arm == "BASE":
            args.adapter_dir = None
        tokenizer = source.native.load_local_tokenizer(args.model_dir)
        report["tokenizer"] = source.native.tokenizer_signature(tokenizer)
        engine = source.Engine(args, tokenizer, check=check)
        report["runtime"] = engine.runtime
        report.update(evaluate(engine, bank, args.arm, output))
        engine.verify_base()
        source.require(source.file_hash(Path(selected_adapter) / "adapter_model.safetensors") == before,
                       "saved_adapter_changed")
        report.update(status="COMPLETE", frozen_base_unchanged=True, saved_adapter_unchanged=True,
                      finished_unix=time.time())
        source.write(output / "RESULT.json", report)
    except BaseException as error:
        report.update(status="FAILED", error=repr(error), finished_unix=time.time())
        source.write(output / "FAILED.json", report)
        raise


if __name__ == "__main__":
    main()

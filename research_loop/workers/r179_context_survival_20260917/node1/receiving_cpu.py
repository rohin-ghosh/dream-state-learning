"""CPU provenance on the actual deployed candidate; output metadata only."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import sys
import tempfile
import time
from types import SimpleNamespace


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def behavioral_cpu(source, output):
    from gpu import orch_r125_continual_native as native
    from gpu import orch_r179_context_survival as policy
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
    from organism_v6.orch_r125_continual_stream import ContinualStream, digest
    from organism_v6.orch_r125_plain_context import VERSION

    for imported, relative in ((native, "gpu/orch_r125_continual_native.py"),
                               (policy, "gpu/orch_r179_context_survival.py")):
        require(Path(imported.__file__).resolve() == source / relative, "actual_successor_module_import")
    cases = []
    for variant, token_count in (("free_distillation", 50), ("free_distillation", 15000), ("no_distillation", 50)):
        with tempfile.TemporaryDirectory(prefix="cpu_fixture_", dir=output) as directory:
            with StreamJournal(Path(directory) / "stream", create=True) as journal:
                stream = ContinualStream(TrainHistory(system_prompt="CPU fixture purpose.", birth_prompt="CPU fixture task."),
                    context_limit=16384, segment_tokens=512, segments_per_sleep=2,
                    deadline_unix=time.time() + 300, model_state_sha256="a" * 64, allow_eviction=True)
                stream.set_presentation(dict(version=VERSION, system_prompt="CPU fixture purpose.",
                                            birth_prompt="CPU fixture task."), 16384)
                prompts = []

                def generate(messages, **options):
                    prompts.append(deepcopy(messages))
                    return dict(raw="A CPU fixture summary about the unfinished bridge.",
                                token_ids=[101, 102, 2], terminal=True, truncated=False)

                child = SimpleNamespace(plan=dict(root=directory, compaction_invitation="Retell this CPU fixture.",
                    presleep_variant=variant), generate=generate, count_tokens=lambda messages: token_count)
                incoming = TrainEvent(event_id="cpu_parent", actor="parent", split="TRAIN", phase="experience",
                    episode_id="cpu", source_id="CPU_FIXTURE", source_sha256=digest(["cpu_parent"]),
                    origin="TRAIN_COLLECTION", text="CPU fixture: preserve the unresolved measurement.")
                stream.step(generate, lambda messages: 50, journal.record, incoming=[incoming])
                stream.step(generate, lambda messages: 50, journal.record)
                before = stream.checkpoint()
                native.prepare_sleep(child, stream, journal, 1)
                after = stream.checkpoint()
                if variant == "no_distillation":
                    require(before == after, "no_distillation_no_view_or_target_change")
                elif token_count < 12288:
                    require(stream.history.visible_frontier.event_count == 0
                            and stream.history.operations == (), "actual_patched_prepare_retains_below_threshold")
                else:
                    require([operation["kind"] for operation in stream.history.operations] == ["compaction"],
                            "actual_patched_prepare_compacts_only_at_threshold")
                history_before_sleep = stream.history.checkpoint()
                rows = stream.pending_rows()
                pending = stream.checkpoint()
                pending["state"]["pending"] = "sleep:" + digest([row["source_sha256"] for row in rows])
                pending["sha256"] = digest(pending["state"])
                journal.record("SLEEP_REQUEST", dict(cycle=1, resume_state=pending))
                saved = stream.commit_sleep(dict(status="COMPLETE", cycle=1, optimizer_steps=16,
                    new_row_sha256=[row["source_sha256"] for row in rows],
                    checkpoint_sha256=dict(adapter="a" * 64, optimizer="b" * 64, rng="c" * 64)), journal.record)
                require(stream.history.checkpoint() == history_before_sleep, "sleep_preserves_history_view")
                restored = ContinualStream.restore(saved, expected_sha256=saved["sha256"])
                require(restored.checkpoint() == stream.checkpoint(), "full_stream_saved_restore_identity")
                restored.step(generate, lambda messages: 50, journal.record)
                if token_count < 12288:
                    require("unresolved measurement" in str(prompts[-1]), "post_sleep_prompt_contains_prior_context")
                cases.append(dict(variant=variant, visible_tokens=token_count, passed=True))
    import torch
    require(not torch.cuda.is_initialized(), "receiving_CPU_no_CUDA_initialization")
    return dict(passed=len(cases), cases=cases, cuda_initialized=False,
        native_sha256=sha(source / "gpu/orch_r125_continual_native.py"),
        policy_sha256=sha(source / "gpu/orch_r179_context_survival.py"),
        source_root=str(source), interpreter=sys.executable, observed_unix=time.time(),
        actual_staged_native_prepare_executed=True, GPU_model_loaded=False)


def boundary_cpu(source, output, boundary_path):
    from gpu import orch_r125_continual_native as native
    import torch
    require(Path(native.__file__).resolve() == source / "gpu/orch_r125_continual_native.py", "actual_boundary_receiver_source")
    require(boundary_path.stat().st_size <= 64 * 1024 * 1024, "bounded_saved_envelope")
    record = native.read(boundary_path)
    require(record["sha256"] == native.digest({key: value for key, value in record.items() if key != "sha256"}),
            "actual_saved_record_integrity")
    envelope = record["document"]["resume_state"]
    stream = native.ContinualStream.restore(envelope, expected_sha256=envelope["sha256"])
    require(stream.checkpoint() == envelope, "exact_full_stream_history_view_roundtrip")
    require(stream.pending is None and stream.sleep_frontier == len(stream.rows), "no_pending_or_unsaved_suffix")
    checkpoint = record["document"]["checkpoint"]
    native.NativeChild.verify_checkpoint(checkpoint)
    require(native.digest(checkpoint["checkpoint_sha256"]) == stream.model_state_sha256, "full_saved_model_binding")
    payload = torch.load(checkpoint["optimizer_rng_path"], map_location="cpu", weights_only=False)
    names = payload["parameter_names"]
    require(names and len(names) == len(set(names)) and payload["optimizer_steps"] == checkpoint["optimizer_steps"] > 0,
            "saved_optimizer_order_steps")
    require(payload["optimizer"]["state"] and payload["optimizer"]["param_groups"], "saved_full_AdamW_state")
    require(payload.get("experiment") == checkpoint.get("experiment") == stream.experiment, "exact_saved_experiment")
    random.Random().setstate(payload["python_rng"])
    torch.Generator(device="cpu").set_state(payload["cpu_rng"])
    require(len(payload["cuda_rng"]) == 1 and payload["cuda_rng"][0].device.type == "cpu", "saved_single_CUDA_RNG_CPU_payload")
    require(not torch.cuda.is_initialized(), "saved_receiver_no_CUDA_initialization")
    return dict(state_sha256=envelope["sha256"], history_sha256=stream.history.checkpoint()["state_sha256"],
        state_fields_sha256={key: native.digest(value) for key, value in envelope["state"].items()},
        optimizer_steps=payload["optimizer_steps"], parameter_order_sha256=native.digest(names),
        adapter_state_sha256=checkpoint["adapter_state_sha256"], cuda_initialized=False,
        full_saved_stream_equal=True, original_journal_written=False,
        native_sha256=sha(source / "gpu/orch_r125_continual_native.py"), observed_unix=time.time())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--boundary", type=Path)
    arguments = parser.parse_args()
    sys.path.insert(0, str(arguments.source))
    result = (boundary_cpu(arguments.source, arguments.output, arguments.boundary) if arguments.boundary
              else behavioral_cpu(arguments.source, arguments.output))
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()

"""Bounded BASE-generated scaffolded data, not autonomous parenting success.

No fit, adapter, checkpoint, launch, or source qualification. Main owns native
provenance, held-isolation checks, hard wall-clock termination and later unguided
release. A fresh master makes these dose_chain-shaped worlds training-only.
Only an explicit CLI invocation loads the single frozen native model.
"""

import argparse
from collections.abc import Mapping
from dataclasses import fields, is_dataclass, replace
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import time

from gpu import astra_stage2a_native_prepare as native_prepare
from gpu import astra_stage2a_native_tokenizer_receipt as tokens
from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_actor as native_actor
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_rollout as rollout
from organism_v6 import composition_birth_stage2a_scoring as scoring
from organism_v6.pcfl_vertical_train import _state_hash


MASTER = b"ASTRA-OUTCOME-COLLECT-TRAIN-20260914-A1"
MAX_SECONDS = 900
GUIDANCE = (
    "\n\nTeacher strategy for this collection only:\n"
    "Determine CURRENT from the latest WORLD message, or from TASK before the first WORLD. "
    "Keep GOAL from TASK. Use READ INDEX at CURRENT and choose the public ROUTE row whose "
    "AT matches CURRENT and FOR matches GOAL; READ RELATION using that row's QUERY. "
    "In the public EVENT rows, match AT to CURRENT and FOR to GOAL, then STEP the observed DID port. "
    "Compare the observed WORLD CURRENT against that EVENT's GOT. If not yet at GOAL, "
    "use THINK KEEP with that event when they match, or THINK REVISE with that event when they differ. "
    "After a mismatch, READ RELATION using that event's public RECOVER query. "
    "Continue using public evidence while CURRENT differs from GOAL. STOP only at GOAL, "
    "immediately once reached. Emit exactly one legal action per call and no explanation."
)
CLAIM = "SCAFFOLDED_DATA_GENERATION_NOT_AUTONOMOUS_PARENTING_SUCCESS"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def public_teacher_prefix(prefix):
    """Fixed text transform of public messages only; no world/scorer arguments."""
    require(type(prefix) is tuple and len(prefix) >= 2
            and all(type(message) is held.Message and type(message.content) is str for message in prefix)
            and prefix[0] == held.Message("system", wire.SYSTEM_MESSAGE)
            and all(message.role in ("user", "assistant") for message in prefix[1:]),
            "original_unassisted_public_prefix_required")
    return (held.Message("system", prefix[0].content + GUIDANCE),) + prefix[1:]


def plain(value):
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if type(value) is bytes:
        return {"bytes_hex": value.hex()}
    if isinstance(value, BaseException):
        return {"error_type": type(value).__name__, "error": str(value)}
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        require(all(type(key) is str for key in value), "string_log_keys_required")
        return {key: plain(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [plain(item) for item in value]
    raise ValueError("unsupported_log_value:" + type(value).__name__)


def append_json(stream, value):
    stream.write(json.dumps(plain(value), sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def write_json(path, value):
    with Path(path).open("x") as stream:
        append_json(stream, value)


class PublicTeacher:
    """The helper holds only a native actor, public requests and logging hooks.

    The original request's context_tokens measures the guided prefix because
    rollout's allowance must reflect what is actually sent to the model.
    Both prefixes are recorded explicitly, never described as identical.
    """

    def __init__(self, actor, *, check, emit):
        self.actor, self.check, self.emit = actor, check, emit
        self.calls = []
        self.failed = False

    def count_context(self, prefix):
        self.check("guided_context")
        require(not self.failed, "teacher_failed_no_retry")
        return self.actor.count_context(public_teacher_prefix(prefix))

    def __call__(self, request):
        record = dict(call_index=len(self.calls), public_request=request, guided_request=None,
                      context_count_basis="ACTUAL_GUIDED_PREFIX", native=None, generation=None, error=None)
        self.calls.append(record)
        before = len(self.actor.calls)
        try:
            self.check("teacher_call")
            require(not self.failed, "teacher_failed_no_retry")
            require(type(request) is rollout.DecodeRequest, "decode_request_required")
            guided = replace(request, prefix=public_teacher_prefix(request.prefix))
            record["guided_request"] = guided
            require(self.actor.count_context(guided.prefix) == guided.context_tokens,
                    "guided_context_count_disagreement")
            generation = self.actor(guided)
            record["generation"] = generation
            return generation
        except BaseException as error:
            self.failed = True
            record["error"] = error
            raise
        finally:
            if len(self.actor.calls) > before:
                native = self.actor.calls[before]
                record["native"] = {key: value for key, value in native.items() if key != "native_output"}
                record["native_output_type"] = type(native.get("native_output")).__name__
                record["native_output_representation"] = "native_sequences; absent if backend did not return them"
            self.emit(record)


def training_worlds():
    allocation = native_prepare.allocate_source(master=MASTER)
    worlds = held.build_chain_panel(role_tokens_by_world=allocation.role_tokens_by_world("dose_chain"))
    require(tuple(world.world for world in worlds) == tuple(f"h{index:02d}" for index in range(16)),
            "all_16_fresh_training_worlds_required")
    require(all(tuple(member.member for member in world.members) == ("m0", "m1") for world in worlds),
            "both_training_members_required")
    return allocation.custody_sha256, worlds


def draft_rows(run, calls, score, *, episode_id):
    """Select actual outputs, never witnesses; strip guidance by source choice."""
    if not score.whole_chain_success:
        return []
    require(all((call.disposition == "UNUSED" and call.request is None and call.attempt is None)
                or (call.disposition == "EXECUTED" and call.request is not None
                    and call.attempt is not None and call.attempt.accepted)
                for call in run.calls), "rejected_or_invalid_call_cannot_be_selected")
    executed = tuple(call for call in run.calls if call.disposition == "EXECUTED")
    require(len(executed) == len(calls) == len(run.attempts)
            and tuple(call.attempt for call in executed) == run.attempts,
            "successful_call_alignment_required")
    rows = []
    for call, teacher_call in zip(executed, calls):
        generation = teacher_call["generation"]
        require(call.disposition == "EXECUTED" and call.attempt.accepted
                and call.request == teacher_call["public_request"]
                and teacher_call["guided_request"].prefix == public_teacher_prefix(call.request.prefix)
                and teacher_call["error"] is None and type(generation) is rollout.Generation
                and generation.raw.encode("utf-8") == call.raw_bytes == call.attempt.capture.raw_bytes,
                "actual_model_action_required")
        require(teacher_call["native"] is not None
                and teacher_call["native"].get("request") == teacher_call["guided_request"]
                and teacher_call["native"].get("generation") == generation
                and teacher_call["native"].get("raw_bytes") == call.raw_bytes
                and teacher_call["native"].get("raw") == generation.raw, "native_raw_generation_required")
        prefix = plain(call.request.prefix)
        require(prefix[0]["content"] == wire.SYSTEM_MESSAGE
                and all(GUIDANCE not in message["content"] for message in prefix),
                "teacher_guidance_forbidden_in_training_prefix")
        rows.append(dict(status="DRAFT_NOT_RELEASED", episode_id=episode_id,
                         source_call_index=teacher_call["call_index"], prefix=prefix,
                         assistant=generation.raw, target_eot="<|im_end|>",
                         loss_policy=dict(prefix="MASK_ALL", assistant="TRAIN", eot="TRAIN")))
    return rows


def collect(worlds, teacher, *, emit_episode, emit_row, check, summary):
    for world in worlds:
        for member in world.members:
            start = len(teacher.calls)
            episode_id = "OUTCOME-TRAIN-A1-" + world.world + "-" + member.member
            episode = dict(episode_id=episode_id, split="TRAIN_ONLY", world=world.world,
                           member=member.member, call_start=start, run=None, score=None,
                           selected=False, error=None)
            try:
                check("episode:" + episode_id)
                run = rollout.run_chain(world, member.member, actor=teacher,
                    count_context=teacher.count_context, counter_provenance="ACTUAL_GUIDED_NATIVE_PREFIX",
                    master=MASTER, stage="D1")
                episode["run"] = run
                score = scoring.score_chain(run.attempts, member)
                episode["score"] = score
                require(not teacher.failed and not any(call.disposition in ("ERROR", "NOT_CALLED") for call in run.calls),
                        "collection_halted:" + run.terminal_reason)
                rows = draft_rows(run, teacher.calls[start:], score, episode_id=episode_id)
                episode["selected"] = score.whole_chain_success
            except BaseException as error:
                episode.update(error=error, call_end=len(teacher.calls), status="ABORTED")
                emit_episode(episode)
                raise
            episode.update(call_end=len(teacher.calls), status="COMPLETED")
            emit_episode(episode)
            summary["completed_episodes"] += 1
            summary["whole_chain_successes"] += int(score.whole_chain_success)
            for row in rows:
                emit_row(row)
                summary["draft_rows"] += 1


def run(options, *, libraries=None, clock=time.time, learner_factory=None):
    root = Path(options.output)
    root.mkdir(exist_ok=False)
    started = clock()
    summary = dict(status="INCOMPLETE", claim=CLAIM, started_unix=started,
                   completed_episodes=0, whole_chain_successes=0, draft_rows=0,
                   planned_episodes=32, call_cap_per_episode=wire.CALL_CAP, max_seconds=MAX_SECONDS,
                   master=MASTER.decode("ascii"), guidance=GUIDANCE,
                   guidance_sha256=sha256(GUIDANCE.encode("ascii")).hexdigest(),
                   split="TRAIN_ONLY_FRESH_MASTER", future_release="MAIN_OWNED_UNGUIDED_CHECKS_REQUIRED")
    teacher, hook = None, None

    def check(stage):
        require(type(options.deadline_unix) in (int, float) and math.isfinite(options.deadline_unix)
                and clock() < options.deadline_unix <= started + MAX_SECONDS,
                "finite_unexpired_max_900s_deadline:" + stage)

    try:
        check("request")
        write_json(root / "REQUEST.json", vars(options))
        require(type(options.gpu_uuid) is str and options.gpu_uuid.startswith("GPU-")
                and "," not in options.gpu_uuid
                and os.environ.get("CUDA_VISIBLE_DEVICES") == options.gpu_uuid, "single_gpu_binding_required")
        require(type(options.expected_base_sha256) is str and len(options.expected_base_sha256) == 64
                and all(character in "0123456789abcdef" for character in options.expected_base_sha256),
                "expected_base_sha256_required")
        if libraries is None:
            import torch
            import transformers
        else:
            torch, transformers = libraries
        require(str(torch.__version__) == tokens.RUNTIME_VERSIONS["torch"]
                and transformers.__version__ == tokens.RUNTIME_VERSIONS["transformers"], "native_runtime_changed")
        require(not torch.cuda.is_initialized(), "fresh_exclusive_process_required")
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        summary["allocation_sha256"], worlds = training_worlds()
        check("tokenizer")
        official_path = Path(tokens.__file__).resolve().parents[1] / (
            "research_notes/astra_memos/receipts_20260912/astra_qwen_public_binding_receipt_20260913_attempt1.json")
        official_raw = official_path.read_bytes()
        require(sha256(official_raw).hexdigest() == tokens.OFFICIAL_RECEIPT_SHA256, "official_tokenizer_receipt_changed")
        official = json.loads(official_raw)
        tokenizer = transformers.AutoTokenizer.from_pretrained(options.model_dir,
            local_files_only=True, trust_remote_code=False, use_fast=True, padding_side="right")
        summary["tokenizer"] = tokens.restore_official_backend(
            tokenizer, options.model_dir, official["files"], root / "backend")
        check("frozen_base_load")
        model = transformers.AutoModelForCausalLM.from_pretrained(options.model_dir,
            local_files_only=True, trust_remote_code=False, torch_dtype=torch.bfloat16,
            device_map=None, attn_implementation="sdpa", use_safetensors=True)
        require(not hasattr(model, "peft_config"), "unwrapped_base_only")
        model.requires_grad_(False)
        model.eval()
        require(not any(parameter.requires_grad for parameter in model.parameters()), "frozen_base_required")
        summary["base_pre"] = _state_hash(dict(model.state_dict()))
        require(summary["base_pre"] == options.expected_base_sha256, "base_state_mismatch")
        verify_learner = None
        if learner_factory is not None:
            model, summary["learner"], verify_learner = learner_factory(model, root, check)
            model.requires_grad_(False)
            model.eval()
            require(not any(parameter.requires_grad for parameter in model.parameters()), "frozen_collector_required")
            require(verify_learner() == summary["base_pre"], "collector_learner_base_mismatch")
        check("single_gpu_placement")
        torch.cuda.init()
        require(torch.cuda.device_count() == 1, "exactly_one_visible_gpu_required")
        model.to("cuda:0")
        hook = model.register_forward_pre_hook(lambda module, inputs: check("forward"))
        actor = native_actor.ReadoutActor(model=model, tokenizer=tokenizer, torch=torch,
            device="cuda:0", count_basis=native_prepare.COUNT_BASIS)
        with (root / "CALLS.jsonl").open("x") as calls, (root / "EPISODES.jsonl").open("x") as episodes, (
                root / "DRAFT_TRAINING_ROWS.jsonl").open("x") as rows:
            teacher = PublicTeacher(actor, check=check, emit=lambda record: append_json(calls, record))
            collect(worlds, teacher, emit_episode=lambda record: append_json(episodes, record),
                    emit_row=lambda row: append_json(rows, row), check=check, summary=summary)
        check("base_post")
        summary["base_post"] = (_state_hash(dict(model.state_dict())) if verify_learner is None
                                else verify_learner())
        require(summary["base_post"] == options.expected_base_sha256, "collection_changed_base")
        require(summary["completed_episodes"] == 32, "all_32_training_episodes_required")
        check("result")
        summary.update(status="COLLECTION_COMPLETE_DRAFT_ONLY", physical_calls=len(teacher.calls), finished_unix=clock())
        write_json(root / "RESULT.json", summary)
        return summary
    except BaseException as error:
        summary.update(status="FAILED", failure=error, finished_unix=clock(),
                       physical_calls=len(teacher.calls) if teacher is not None else 0)
        write_json(root / "FAILED.json", summary)
        raise
    finally:
        if hook is not None:
            hook.remove()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("model-dir", "output", "gpu-uuid", "expected-base-sha256"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--deadline-unix", type=float, required=True)
    return parser.parse_args(argv)


if __name__ == "__main__":
    run(parse_args())

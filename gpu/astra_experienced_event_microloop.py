"""Bounded DEV own-EVENT collection, one sleep, and separate-process readout.

The exposure schedule and memory addresses are supplied, not learned selection.
No training on action readouts, no birth qualification, and no H1/H2 promotion.
"""

import argparse
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import time

from gpu import astra_pchain2_native as native
from organism_v6 import experienced_event_microloop as material
from organism_v6 import pcfl_vertical_dev as world


SCHEMA = "DEV_EXPERIENCED_EVENT_MICROLOOP_V1"
MASTER = "ASTRA-EXPERIENCED-EVENT-MICROLOOP-20260914-A1"
UPDATES = 200
MAX_CONTEXT = 2048
MAX_NEW_TOKENS = 160
SEED = 0


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write(path, value):
    native._write(path, value)


def read(path):
    return native._read(path)


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def encode_rows(rows, tokenizer):
    require(len(rows) == 32, "four_facts_times_eight_views_required")
    encoded = tuple(encode_row(row["messages"], tokenizer) for row in rows)
    require(all(any(label != -100 for label in row.labels) for row in encoded), "supervised_actual_event_required")
    return encoded


def encode_row(messages, tokenizer):
    require([message.get("role") for message in messages] == ["system", "user", "assistant"]
            and messages[0]["content"] == world.MEMORY_SYSTEM, "exact_memory_training_roles_required")
    target = messages[-1]["content"]
    world.parse_event_line(target)
    require(target not in messages[1]["content"], "answer_must_not_be_in_question")
    context = tokenizer.apply_chat_template(messages[:2], tokenize=False, add_generation_prompt=True, return_dict=False)
    full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False, return_dict=False)
    require(full == context + target + tokenizer.eos_token + "\n", "exact_template_boundary_required")
    prefix_ids, target_ids = native._encode(tokenizer, context), native._encode(tokenizer, target)
    suffix_ids = native._encode(tokenizer, "\n")
    require(not set(tokenizer.all_special_ids).intersection(target_ids), "target_special_token_injection")
    require(native._encode(tokenizer, tokenizer.eos_token) == (tokenizer.eos_token_id,), "eot_token_mismatch")
    supervised = target_ids + (tokenizer.eos_token_id,)
    sequence = native._encode(tokenizer, full)
    require(sequence == prefix_ids + supervised + suffix_ids, "token_boundary_mismatch")
    require(native._decode(tokenizer, sequence) == full and len(sequence) <= MAX_CONTEXT, "roundtrip_or_length_failure")
    require(tuple(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False,
                return_dict=False, truncation=False, padding=False)) == sequence, "tokenized_template_mismatch")
    return native.EncodedRow(sequence, (-100,) * len(prefix_ids) + supervised + (-100,) * len(suffix_ids), supervised)


def batch_indexes(update):
    require(type(update) is int and 1 <= update <= UPDATES, "fixed_200_update_range")
    return tuple(((update - 1) * 4 + offset) % 32 for offset in range(4))


def validate_runtime(imported, distributions):
    for name, expected in native.NUMERICAL_BINDING["runtime"].items():
        require(imported.get(name) == expected, "native_runtime_drift:" + name)
        expected_distribution = expected.split("+", 1)[0] if name == "torch" else expected
        require(distributions.get(name) == expected_distribution, "native_distribution_drift:" + name)


def load_collection(directory, *, serialization="EXACT"):
    root = Path(directory)
    result = read(root / "RESULT.json")
    require(result.get("schema") == SCHEMA and result.get("phase") == "collect"
            and result.get("status") == "COMPLETE", "complete_actual_collection_required")
    require(serialization in ("EXACT", "FINAL_LF_ONLY"), "unknown_serialization")
    if serialization == "EXACT":
        require(result.get("accepted_events") == 4, "complete_four_actual_events_required")
    else:
        require(result.get("event_denominator") == 4 and result.get("frozen_base_unchanged") is True,
                "complete_frozen_four_event_source_required")
    require(not (root / "FAILED.json").exists(), "failed_collection_not_trainable")
    for name, expected in result["files"].items():
        require(Path(name).name == name and file_hash(root / name) == expected, "collection_file_drift")
    bank, episodes = read(root / "BANK.json"), read(root / "EPISODES.json")
    require(bank == material.build_bank(MASTER), "prospective_world_master_mismatch")
    rows = material.compile_rows(bank, episodes, serialization=serialization)
    require(len(rows) == 32, "four_grounded_terminal_events_required_before_fit")
    if serialization == "EXACT":
        require(rows == read(root / "ROWS.json"), "compiled_rows_must_replay_actual_events")
    return bank, episodes, rows, dict(path=str(root.resolve()), result_sha256=file_hash(root / "RESULT.json"),
        serialization=serialization, original_strict_accepted_events=result["accepted_events"],
        compiled_rows_sha256=native._digest(rows))


class Engine:
    def __init__(self, options, tokenizer, *, check):
        import torch
        import peft
        import transformers
        import tokenizers

        self.torch, self.check, self.tokenizer = torch, check, tokenizer
        torch.set_num_threads(1)
        if torch.get_num_interop_threads() != 1:
            torch.set_num_interop_threads(1)
        versions = dict(torch=torch.__version__, transformers=transformers.__version__,
                        peft=peft.__version__, tokenizers=tokenizers.__version__)
        distributions = {name: importlib.metadata.version(name) for name in versions}
        validate_runtime(versions, distributions)
        self.runtime = dict(imported=versions, distributions=distributions)
        base = transformers.AutoModelForCausalLM.from_pretrained(options.model_dir,
            local_files_only=True, trust_remote_code=False, use_safetensors=True,
            torch_dtype=torch.bfloat16, attn_implementation="sdpa", device_map=None)
        require(base.config.model_type == "qwen2", "frozen_qwen2_base_required")
        self.base_references = dict(base.state_dict(keep_vars=True))
        self.expected_base = options.expected_base_sha256
        self.verify_base()
        base.requires_grad_(False)
        if options.phase == "train":
            torch.manual_seed(SEED)
            config = peft.LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05,
                target_modules=list(native.TARGET_MODULES), bias="none", task_type="CAUSAL_LM",
                init_lora_weights=True, use_rslora=False, use_dora=False)
            model = peft.get_peft_model(base, config, autocast_adapter_dtype=True)
            model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
            model.enable_input_require_grads()
            model.config.use_cache = False
        elif options.adapter_dir:
            config = peft.LoraConfig.from_pretrained(options.adapter_dir, local_files_only=True)
            require(config.r == 8 and config.lora_alpha == 16 and config.lora_dropout == 0.05
                    and set(config.target_modules) == set(native.TARGET_MODULES), "adapter_recipe_drift")
            model = peft.PeftModel.from_pretrained(base, options.adapter_dir,
                local_files_only=True, is_trainable=False, autocast_adapter_dtype=True)
        else:
            model = base
        self.model = model.to(options.device)
        require(torch.cuda.device_count() == 1, "exactly_one_visible_gpu_required")
        self.device = options.device
        self.transformers = transformers
        self.hook = model.register_forward_pre_hook(lambda module, inputs: check("forward"))
        self.model.eval()

    def verify_base(self):
        from organism_v6.pcfl_vertical_train import _state_hash

        self.check("base_hash")
        require(_state_hash(self.base_references) == self.expected_base, "frozen_base_changed")

    def generate(self, messages, *, max_new_tokens=MAX_NEW_TOKENS):
        require(type(max_new_tokens) is int and 0 < max_new_tokens <= 768, 'bounded_generation_tokens_required')
        self.check("generation")
        tokens = self.tokenizer.apply_chat_template(messages, tokenize=True,
            add_generation_prompt=True, return_dict=False)
        require(0 < len(tokens) <= MAX_CONTEXT, "context_bound_exceeded_no_truncation")
        inputs = self.torch.tensor([tokens], dtype=self.torch.long, device=self.device)
        config = self.transformers.GenerationConfig(do_sample=False, num_beams=1,
            use_cache=True, max_new_tokens=max_new_tokens, repetition_penalty=1.0,
            eos_token_id=self.tokenizer.eos_token_id, pad_token_id=self.tokenizer.pad_token_id)
        with self.torch.inference_mode():
            generated = self.model.generate(input_ids=inputs, attention_mask=self.torch.ones_like(inputs),
                                            generation_config=config)
        require(generated[0, :len(tokens)].tolist() == tokens, "generated_prefix_changed")
        tail = generated[0, len(tokens):].tolist()
        terminal = bool(tail) and tail[-1] == self.tokenizer.eos_token_id
        text = self.tokenizer.decode(tail[:-1] if terminal else tail,
            skip_special_tokens=False, clean_up_tokenization_spaces=False)
        return dict(messages=messages, prompt_tokens=len(tokens), token_ids=tail,
                    raw=text, terminal=terminal, truncated=not terminal and len(tail) == max_new_tokens)


def collect(engine, output):
    bank = material.build_bank(MASTER)
    write(output / "BANK.json", bank)
    episodes = []
    for fact in bank:
        exploration = engine.generate(material.exploration_messages(fact))
        event = None
        accepted = False
        error = None
        try:
            require(exploration["terminal"] and not exploration["truncated"], "unterminated_exploration")
            messages = material.observation_messages(fact, exploration["raw"])
            event = engine.generate(messages)
            require(event["terminal"] and not event["truncated"], "unterminated_event")
            material.validate_episode(fact, exploration["raw"], event["raw"])
            accepted = True
        except ValueError as failure:
            error = str(failure)
        episodes.append(dict(fact=fact, exploration=exploration, event=event,
                             accepted=accepted, error=error))
        write(output / ("EPISODE_%02d.json" % (len(episodes) - 1)), episodes[-1])
    write(output / "EPISODES.json", episodes)
    accepted_count = sum(episode["accepted"] for episode in episodes)
    rows = material.compile_rows(bank, episodes) if accepted_count == 4 else []
    write(output / "ROWS.json", rows)
    return dict(accepted_events=accepted_count, event_denominator=4, rows=len(rows),
                fits=0, model_calls=sum(1 + (episode["event"] is not None) for episode in episodes),
                files={name: file_hash(output / name) for name in ("BANK.json", "EPISODES.json", "ROWS.json")})


def train(engine, rows, output):
    torch = engine.torch
    encoded = encode_rows(rows, engine.tokenizer)
    write(output / "MASKS.json", [asdict(row) for row in encoded])
    parameters = [parameter for name, parameter in engine.model.named_parameters() if parameter.requires_grad]
    require(parameters and all(parameter.dtype == torch.float32 for parameter in parameters), "fp32_lora_required")
    require(all(".lora_A." in name or ".lora_B." in name
                for name, parameter in engine.model.named_parameters() if parameter.requires_grad), "lora_only_learning")
    optimizer = torch.optim.AdamW(parameters, lr=3e-5, **native.OPTIMIZER)
    torch.manual_seed(SEED)
    engine.model.train()
    with (output / "LOSSES.jsonl").open("x") as stream:
        for update in range(1, UPDATES + 1):
            engine.check("update")
            indexes = batch_indexes(update)
            batch = native.collate([encoded[index] for index in indexes], pad_id=engine.tokenizer.pad_token_id)
            tensors = {name: torch.tensor(value, dtype=torch.long, device=engine.device) for name, value in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=torch.device(engine.device).type, dtype=torch.bfloat16):
                loss = engine.model(**tensors, use_cache=False).loss
            require(bool(torch.isfinite(loss)) and loss.requires_grad, "nonfinite_or_disconnected_loss")
            loss.backward()
            require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
                        for parameter in parameters), "nonfinite_or_missing_gradient")
            optimizer.step()
            stream.write(json.dumps(dict(update=update, loss=loss.item(), row_indexes=indexes)) + "\n")
            stream.flush()
    require(all(bool(torch.isfinite(parameter).all()) for parameter in parameters), "nonfinite_adapter")
    engine.model.save_pretrained(output / "adapter", safe_serialization=True, save_embedding_layers=False)
    return dict(updates=UPDATES, presentations=UPDATES * 4, presentations_per_event=200,
        supervised_tokens=sum(sum(label != -100 for label in encoded[index].labels)
            for update in range(1, UPDATES + 1) for index in batch_indexes(update)),
        checkpoint_kind="PEFT_ADAPTER_ONLY_NOT_OPTIMIZER_RESUME",
        adapter_files={path.name: file_hash(path) for path in (output / "adapter").iterdir() if path.is_file()})


def evaluate(engine, bank, episodes, output, *, serialization="EXACT"):
    rows, memory = [], {}

    def call(panel, fact, messages, expected):
        result = engine.generate(messages)
        item = dict(panel=panel, event=fact["event"], expected=expected, generation=result,
                    correct=result["terminal"] and not result["truncated"] and result["raw"] == expected)
        rows.append(item)
        write(output / ("CALL_%03d.json" % (len(rows) - 1)), item)
        return result["raw"]

    for fact, episode in zip(bank, episodes):
        for view in (0, 8):
            request = "READ EVENT " + fact["event"]
            messages = [dict(role="system", content=world.MEMORY_SYSTEM),
                dict(role="user", content=world.WRAPPERS[view].replace("{REQUEST}", request))]
            expected = episode["event"]["raw"]
            if serialization == "FINAL_LF_ONLY":
                expected = material.canonical_event(expected)
            raw = call("recall_W" + str(view), fact, messages, expected)
            if view == 8:
                memory[fact["event"]] = raw
    for fact in bank:
        expected = material.expected_action(fact)
        call("native_action", fact, material.action_messages(fact), expected)
        observed = "\n".join(memory[address] for address in fact["public_events"])
        call("supplied_addresses_own_read_action", fact,
             material.action_messages(fact, memory_text=observed), expected)
        ceiling = "".join((material.canonical_event(episode["event"]["raw"])
                            if serialization == "FINAL_LF_ONLY" else episode["event"]["raw"])
                           for other, episode in zip(bank, episodes) if other["world"] == fact["world"])
        call("exact_facts_ceiling", fact, material.action_messages(fact, memory_text=ceiling, ceiling=True), expected)
    for fact in material.build_bank(MASTER + "-UNSEEN-MISS"):
        request = "READ EVENT " + fact["event"]
        call("unseen_miss", fact, [dict(role="system", content=world.MEMORY_SYSTEM),
            dict(role="user", content=world.WRAPPERS[8].replace("{REQUEST}", request))], "MISS")
    panels = {panel: dict(correct=sum(row["correct"] for row in rows if row["panel"] == panel),
                         denominator=sum(row["panel"] == panel for row in rows)) for panel in sorted({row["panel"] for row in rows})}
    write(output / "READOUT.json", rows)
    return dict(panels=panels, model_calls=len(rows), fresh_process=True, fits=0,
                note="Supplied addresses are external scheduling; native action gets no memory text. W8 is wrapper transfer, not new facts.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("collect", "train", "readout"))
    for name in ("model-dir", "expected-base-sha256", "output", "gpu-uuid"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--collection")
    parser.add_argument("--adapter-dir")
    parser.add_argument("--serialization", choices=("EXACT", "FINAL_LF_ONLY"), default="EXACT")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--deadline-seconds", type=float, default=1800)
    args = parser.parse_args(argv)
    require(math.isfinite(args.deadline_seconds) and 0 < args.deadline_seconds <= 3600, "bounded_native_deadline_required")
    require(os.environ.get("HF_HUB_OFFLINE") == "1" and os.environ.get("TRANSFORMERS_OFFLINE") == "1", "offline_required")
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == args.gpu_uuid, "exact_physical_gpu_binding_required")
    require(args.phase == "readout" or args.adapter_dir is None, "no_warm_start_or_collection_adapter_in_v1")
    require(args.phase != "collect" or args.serialization == "EXACT", "collection_keeps_original_strict_rule")
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()

    def check(phase):
        require(time.time() < started + args.deadline_seconds, "native_deadline:" + phase)

    summary = dict(schema=SCHEMA, phase=args.phase, started_unix=started, master=MASTER,
                   claim="SINGLE_DEV_EXOGENOUS_SCHEDULE_OWN_EVENT_WRITE_NOT_PARENTING", arguments=vars(args),
                   source_sha256={str(Path(module.__file__).name): file_hash(module.__file__)
                       for module in (material, native)}, runner_sha256=file_hash(__file__))
    write(output / "REQUEST.json", summary)
    try:
        if args.phase != "collect":
            require(args.collection, "source_collection_required")
            bank, episodes, rows, provenance = load_collection(args.collection, serialization=args.serialization)
            summary["collection"] = provenance
            write(output / "COMPILED_ROWS.json", rows)
        if args.adapter_dir:
            parent = Path(args.adapter_dir).resolve().parent
            terminal = read(parent / "RESULT.json")
            require(terminal["schema"] == SCHEMA and terminal["status"] == "COMPLETE"
                    and terminal["phase"] == "train" and terminal["updates"] == UPDATES
                    and terminal["collection"] == summary["collection"], "completed_same_collection_training_required")
            require(not (parent / "FAILED.json").exists(), "failed_adapter_forbidden")
            for name, digest in terminal["adapter_files"].items():
                require(Path(name).name == name and file_hash(Path(args.adapter_dir) / name) == digest, "adapter_file_drift")
            summary["training_result_sha256"] = file_hash(parent / "RESULT.json")
        tokenizer = native.load_local_tokenizer(args.model_dir)
        summary["tokenizer"] = native.tokenizer_signature(tokenizer)
        engine = Engine(args, tokenizer, check=check)
        summary["runtime"] = engine.runtime
        if args.phase == "collect":
            summary.update(collect(engine, output))
        elif args.phase == "train":
            summary.update(train(engine, rows, output))
        else:
            summary.update(evaluate(engine, bank, episodes, output, serialization=args.serialization))
        engine.verify_base()
        summary.update(status="COMPLETE", finished_unix=time.time(), frozen_base_unchanged=True)
        write(output / "RESULT.json", summary)
    except BaseException as failure:
        summary.update(status="FAILED", error=repr(failure), finished_unix=time.time())
        write(output / "FAILED.json", summary)
        raise


if __name__ == "__main__":
    main()

"""Original seed0 teach HF parity against existing SEQ100; no training/generation."""
import argparse
import gc
import json
import math
import os
from pathlib import Path
import signal
import struct
import sys
import threading
import time

SEED0_SHA = "d5a3d0297290184061b5cfcc3bf7fa5ba36a5995fbaedb021df464be7879ec5e"
LABEL = "IN_SAMPLE_HF_VLLM_PARITY_NOT_NEW_EVALUATION"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bind(source):
    global base, trainer, diagnostic
    source = Path(source).resolve(strict=True)
    sys.path.insert(0, str(source))
    from organism_v6 import rulegame_parenting_diagnostic as base
    from organism_v6 import train_adapter_v3 as trainer
    from organism_v6 import fundamental_memory_diagnostic as diagnostic
    require(all(Path(module.__file__).resolve().parent.parent == source for module in
        (base, trainer, diagnostic)), "wrong immutable source root")


def sources():
    return dict(diagnostic.sources(), trainer=base.digest(trainer.__file__), sidecar=base.digest(__file__))


def write(path, obj):
    with Path(path).open("x") as stream:
        json.dump(obj, stream, sort_keys=True, allow_nan=False, indent=2)


def sealed(root):
    require(base.digest(root / "plan.json") == base.read(root / "plan.sha256.json")["sha256"], "plan seal changed")
    return base.read(root / "plan.json")


def build_rows(seq, cases, items, captures, tokenizer):
    indexed = {item["group"]: item for item in items if item["view"] == "memory"}
    require(len(indexed) == 16 and len(captures) == len(cases) == 16 and
        [case["id"] for case in cases] == list(diagnostic.CASE_IDS), "exact16 original memory cases required")
    colors = {}
    for color in diagnostic.corpus.COLORS:
        ids = tokenizer.encode(color, add_special_tokens=False)
        require(len(ids) == 1, "color must be one native token")
        colors[color] = ids[0]
    require(len(set(colors.values())) == 4 and tokenizer.eos_token_id not in colors.values(), "color/EOS collision")
    rows = []
    for case, request, native, capture in zip(cases, seq["requests"], seq["native_inputs"], captures, strict=True):
        sent, received = capture
        response = received["response"]
        item = indexed[case["id"]]
        rendered, prefix = native["rendered_prompt"], native["prompt_token_ids"]
        require(item["spans"] == [[rendered, False, "context"], [case["expected"], True, "authored_birth_target"]],
            "original training context/target/mask mismatch")
        require(sent["request"] == request and sent["identity"] == seq["identity"] and
            request["case_id"] == case["id"] and request["prompt"] == case["context"], "SEQ100 request/identity mismatch")
        require(received["response_sha256"] == base.value_hash(response) and
            sent["prompt_sha256"] == base.value_hash(request["prompt"]), "raw response/prompt seal changed")
        require(response["rendered_prompt"] == rendered and response["prompt_token_ids"] == prefix and
            tokenizer.encode(rendered, add_special_tokens=False) == prefix and bool(prefix), "exact native prefix mismatch")
        base.validate_response(request, response)
        require(response["output_token_ids"], "missing actual vLLM first token")
        target = [colors[case["expected"]], tokenizer.eos_token_id]
        encoded = trainer.encode_item_segments(trainer.normalize_items([item])[0], tokenizer, 512, False, True)
        require(len(encoded) == 1 and encoded[0].ids == prefix + target and
            encoded[0].labels == [-100] * len(prefix) + target, "native training token/label shift mismatch")
        rows.append(dict(case_id=case["id"], source_event_ids=case["source_event_ids"], expected=case["expected"],
            rendered_prompt=rendered, prefix_ids=prefix, input_ids=prefix + target,
            labels=[-100] * len(prefix) + target, colors=colors, gold_id=target[0], eos_id=target[1],
            color_position=len(prefix), eos_position=len(prefix)+1, vllm_request=sent, vllm_response=received))
    return rows


def prepare(out, seed0_root, seq100_root, lease_end):
    out = Path(out).expanduser().absolute()
    require(not out.exists() and not any(path.is_symlink() for path in (out, *out.parents)), "fresh unaliased output required")
    seedroot, seqroot = Path(seed0_root).resolve(strict=True), Path(seq100_root).resolve(strict=True)
    seed = sealed(seedroot)
    require(base.digest(seedroot / "plan.json") == SEED0_SHA, "not pinned original seed0 plan")
    seq, cases = diagnostic.verify(seqroot)
    adapter = seedroot / "fit_teach" / "adapter"
    fit = base.read(adapter.parent / "result.json")
    require(seq["adapter"] == fit["adapter"] == str(adapter) and fit["arm"] == "teach" and
        seq["adapter_files"] == fit["adapter_files"] == trainer._warm_inventory(adapter), "seed0 teach adapter mismatch")
    require(seq["model"] == seed["model"] and seq["model_files"] == seed["model_files"], "base model mismatch")
    require((adapter / "DONE").is_file() and base.read(adapter / "train_manifest.json") == fit["manifest"] and
        fit["manifest"]["config"] == seed["config"], "incomplete/changed seed0 fit")
    require(fit["manifest"]["steps"] == 80 and fit["manifest"]["nonfinite_batches"] == 0 and
        math.isfinite(fit["manifest"]["final_loss"]) and base.digest(seedroot / "teach.json") ==
        seed["corpus_sha256"]["teach"] == fit["manifest"]["corpus"]["sha256"], "seed0 fit/material provenance differs")
    require(math.isfinite(lease_end) and lease_end > time.time()+750 and base.WORKER_SECONDS == 600 and
        base.CLEANUP_RESERVE == 140, "insufficient lease or changed native bounds")
    for protected in (seedroot, seqroot, Path(seed["model"]), base.REPO):
        require(out.resolve() != protected and protected not in out.resolve().parents and
            out.resolve() not in protected.parents, "output overlaps immutable inputs")
    data = seqroot / "run" / "data"
    require(base.read(data / "manifest.json")["files"] == base.tree_hashes(data, ("manifest.json",)), "SEQ100 capture changed")
    supervision = base.read(seqroot / "run" / "worker" / "supervision.json")
    require(all(supervision[key] is True for key in ("ok", "reservation_release_verified", "owned_group_empty",
        "gpu_processes_absent")), "SEQ100 cleanup incomplete")
    reduction = base.read(seqroot / "reduction.json")
    require(reduction["complete"] is True and reduction["counts"]["total"] == 16 and
        reduction["native_token_text_audit"] is True and reduction["plan_sha256"] == base.digest(seqroot / "plan.json"),
        "SEQ100 reduction incomplete/unbound")
    require(reduction["capture_sha256"] == base.digest(data / "manifest.json") and
        base.read(data / "identity.json") == dict(backend=seq["identity"], model_files=seq["model_files"],
            adapter_files=seq["adapter_files"]), "SEQ100 capture identity mismatch")
    expected = {f"{index:04d}.{kind}.json" for index in range(16) for kind in ("request", "response")}
    require({path.name for path in (data / "calls").iterdir()} == expected, "SEQ100 call cardinality differs")
    tokenizer = base.native_tokenizer(seed["model"])
    base.audit_native_calls(tokenizer, data)
    captures = [(base.read(data / "calls" / f"{index:04d}.request.json"),
        base.read(data / "calls" / f"{index:04d}.response.json")) for index in range(16)]
    rows = build_rows(seq, cases, base.read(seedroot / "teach.json")["corpus"], captures, tokenizer)
    plan = dict(schema=1, label=LABEL, model=seed["model"], model_files=seed["model_files"], adapter=str(adapter),
        adapter_files=seq["adapter_files"], device="0", lease_end=float(lease_end), source_root=str(base.REPO),
        source_hashes=sources(), seq100_root=str(seqroot), seq100_files=base.tree_hashes(seqroot),
        seed0_inputs={str(path):base.digest(path) for path in (seedroot / "plan.json", seedroot / "teach.json",
            adapter.parent / "result.json")}, rows=rows, worker_seconds=600, cleanup_reserve=140,
        forwards=32, new_vllm_calls=0, optimizer_steps=0, dtype="bf16", seed=20260912)
    root = base.fresh_directory(out, plan["model"])
    write(root / "plan.json", plan)
    write(root / "plan.sha256.json", dict(sha256=base.digest(root / "plan.json")))
    verify(root)
    return dict(root=str(root), status="PREPARED_NOT_LAUNCHED", forwards=32, new_vllm_calls=0)


def verify(root):
    plan = sealed(root)
    require(plan["source_root"] == str(base.REPO) and plan["source_hashes"] == sources(), "source changed")
    require(plan["model_files"] == base.model_hashes(plan["model"]) and
        plan["adapter_files"] == trainer._warm_inventory(plan["adapter"]), "model/adapter changed")
    require(plan["seq100_files"] == base.tree_hashes(plan["seq100_root"]) and
        all(base.digest(path) == value for path,value in plan["seed0_inputs"].items()), "inherited evidence changed")
    require(plan["label"] == LABEL and plan["device"] == "0" and plan["forwards"] == 32 and
        plan["new_vllm_calls"] == plan["optimizer_steps"] == 0 and plan["dtype"] == "bf16" and
        plan["worker_seconds"] == base.WORKER_SECONDS == 600 and plan["cleanup_reserve"] == 140 and
        [row["case_id"] for row in plan["rows"]] == list(diagnostic.CASE_IDS), "fixed scope changed")
    for row in plan["rows"]:
        positions(row)
    return plan


def positions(row):
    length = len(row["prefix_ids"])
    require(length > 0 and row["color_position"] == length and row["eos_position"] == length+1 and
        row["input_ids"] == row["prefix_ids"] + [row["gold_id"], row["eos_id"]] and
        row["labels"] == [-100]*length + [row["gold_id"], row["eos_id"]], "wrong causal color/EOS shift")
    return length-1, length


def metrics(row, vectors):
    positions(row)
    require(len(vectors) == 3 and len({len(vector) for vector in vectors}) == 1 and
        all(vector and all(math.isfinite(value) for value in vector) for vector in vectors), "invalid/nonfinite logits")
    prefix, full, eos = vectors
    require(all(type(token) is int and 0 <= token < len(prefix) for token in
        [*row["colors"].values(), row["gold_id"], row["eos_id"], row["vllm_response"]["response"]["output_token_ids"][0]]), "token out of vocabulary")
    def summarize(vector, gold):
        maximum = max(vector)
        normalizer = maximum + math.log(math.fsum(math.exp(value-maximum) for value in vector))
        top = max(range(len(vector)), key=vector.__getitem__)
        return dict(top1_id=top, top1_logit=vector[top], gold_logprob=vector[gold]-normalizer,
            color_logits={color:vector[token] for color,token in row["colors"].items()},
            color_logprobs={color:vector[token]-normalizer for color,token in row["colors"].items()},
            gold_minus_red=vector[gold]-vector[row["colors"]["red"]])
    first, teacher, terminal = summarize(prefix,row["gold_id"]), summarize(full,row["gold_id"]), summarize(eos,row["eos_id"])
    actual = row["vllm_response"]["response"]["output_token_ids"][0]
    return dict(prefix=first, teacher_color=teacher, color_nll=-teacher["gold_logprob"], eos_nll=-terminal["gold_logprob"],
        full_response_mean_nll=-(teacher["gold_logprob"]+terminal["gold_logprob"])/2,
        prefix_full_max_abs_logit_difference=max(abs(left-right) for left,right in zip(prefix,full)),
        prefix_full_gold_logprob_difference=first["gold_logprob"]-teacher["gold_logprob"],
        vllm_first_id=actual, top1_matches_vllm=first["top1_id"] == actual,
        hf_gold_minus_vllm_logit=prefix[row["gold_id"]]-prefix[actual],
        logprob_calculation="float64 stable logsumexp of stored float32 logits; no discrepancy threshold")


def loaded_state(source, loaded):
    source_inventory = trainer._warm_validate_state(source, loaded)
    converted = {name:tensor.to(device="cpu", dtype=loaded[name].dtype) for name,tensor in source.items()}
    expected, actual = trainer._warm_state_inventory(converted), trainer._warm_state_inventory(loaded)
    require(expected == actual, "full loaded PEFT state mismatch")
    return dict(source=source_inventory, expected_after_dtype_conversion=expected, loaded=actual,
        exact_loaded_check=True, dtype_conversions={name:dict(source=str(source[name].dtype), loaded=str(loaded[name].dtype))
        for name in source if source[name].dtype != loaded[name].dtype})


def worker_command(root):
    return [sys.executable,"-B",str(Path(__file__).resolve()),"_worker","--source-root",str(base.REPO),"--root",str(root),"--allow-gpu"]


def worker(root):
    parent, started = os.getppid(), time.monotonic()
    initial = sealed(root)
    require(parent > 1 and os.environ.get("CUDA_VISIBLE_DEVICES") == "0", "owning GPU0 supervisor required")
    until = started+5
    receipt = root / "run" / "worker" / "process.json"
    while not receipt.exists() and time.monotonic() < until:
        time.sleep(.05)
    process = base.read(receipt)
    require(process["pid"] == process["pgid"] == os.getpid() == os.getpgrp() and
        process["argv"] == worker_command(root) and process["device"] == "0", "worker process ownership differs")
    stop = threading.Event()
    def interrupted(number, frame):
        raise RuntimeError(f"worker interrupted {number}")
    handlers = {number:signal.signal(number,interrupted) for number in (signal.SIGTERM,signal.SIGINT)}
    def watch():
        while not stop.wait(.2):
            if os.getppid() != parent or time.monotonic()-started >= 600 or time.time() >= initial["lease_end"]-10:
                os.killpg(os.getpgrp(),signal.SIGTERM)
                return
    watcher = threading.Thread(target=watch,daemon=True)
    watcher.start()
    data = root / "run" / "data"
    data.mkdir()
    model, torch, error = None, None, None
    try:
        plan = verify(root)
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel, get_peft_model_state_dict
        torch.manual_seed(plan["seed"])
        tokenizer = AutoTokenizer.from_pretrained(plan["model"],local_files_only=True)
        model = AutoModelForCausalLM.from_pretrained(plan["model"],torch_dtype=torch.bfloat16,
            device_map="cuda:0",local_files_only=True)
        require(not hasattr(model,"peft_config"), "base already adapted")
        config = base.read(Path(plan["adapter"]) / "adapter_config.json")
        prior = base.read(Path(plan["adapter"]) / "train_manifest.json")["config"]
        trainer._warm_validate_config(config, trainer.lora_config(trainer.TrainConfig(**prior),model.config.num_hidden_layers).to_dict())
        paths = [Path(plan["adapter"])/name for name in ("adapter_model.safetensors","adapter_model.bin")
            if (Path(plan["adapter"])/name).is_file()]
        require(len(paths)==1,"missing/ambiguous weights")
        if paths[0].suffix == ".safetensors":
            from safetensors.torch import load_file
            source = load_file(str(paths[0]),device="cpu")
        else:
            source = torch.load(paths[0],map_location="cpu",weights_only=True)
        model = PeftModel.from_pretrained(model,plan["adapter"],is_trainable=False,local_files_only=True)
        model.requires_grad_(False)
        model.eval()
        require(not model.training and not any(parameter.requires_grad for parameter in model.parameters()) and
            list(model.peft_config)==["default"], "model must be frozen single-adapter eval")
        state = get_peft_model_state_dict(model,save_embedding_layers=False)
        load = loaded_state(source,state)
        load.update(base_frozen=True,eval=True,base_dtype="bf16",versions=trainer._versions(),optimizer_steps=0)
        write(data / "load.json",load)
        del source,state
        for row in plan["rows"]:
            require(time.monotonic()-started < 595 and time.time()<plan["lease_end"]-10,"forward deadline")
            require(tokenizer.encode(row["rendered_prompt"],add_special_tokens=False)==row["prefix_ids"],"HF tokenizer prefix mismatch")
            color_index,eos_index = positions(row)
            vectors = []
            with torch.inference_mode():
                ids = torch.tensor([row["prefix_ids"]],device="cuda:0")
                output = model(input_ids=ids,attention_mask=torch.ones_like(ids),use_cache=False)
                require(output.logits.shape[1]==len(row["prefix_ids"]),"prefix output length mismatch")
                vectors.append(output.logits[0,color_index].float().cpu().tolist())
                del output,ids
                ids = torch.tensor([row["input_ids"]],device="cuda:0")
                labels = torch.tensor([row["labels"]],device="cuda:0")
                output = model(input_ids=ids,attention_mask=torch.ones_like(ids),labels=labels,use_cache=False)
                require(output.logits.shape[1]==len(row["input_ids"]),"teacher output length mismatch")
                vectors.extend(output.logits[0,index].float().cpu().tolist() for index in (color_index,eos_index))
                hf_loss = float(output.loss.cpu())
                del output,ids,labels
            result = metrics(row,vectors)
            require(math.isfinite(hf_loss),"nonfinite HF item loss")
            result.update(case_id=row["case_id"],hf_reported_loss=hf_loss,
                hf_loss_minus_recomputed=hf_loss-result["full_response_mean_nll"],vocab_size=len(vectors[0]),
                top1_text=tokenizer.decode([result["prefix"]["top1_id"]],skip_special_tokens=False))
            with (data / (row["case_id"]+".f32")).open("xb") as stream:
                for vector in vectors:
                    stream.write(struct.pack("<"+"f"*len(vector),*vector))
            write(data / (row["case_id"]+".json"),result)
        after = trainer._warm_state_inventory(get_peft_model_state_dict(model,save_embedding_layers=False))
        require(after==load["loaded"],
            "loaded parameters changed during evaluation")
        write(data / "state_after.json",after)
        verify(root)
    except BaseException as failure:
        error = dict(type=type(failure).__name__,message=str(failure))
        raise
    finally:
        model = None
        gc.collect()
        try:
            if torch is not None:
                torch.cuda.empty_cache()
            write(data / "cleanup.json",dict(handle_released=True,error=error,owned_scope="HF handle; supervisor verifies group/GPU release"))
            if error is None:
                write(data / "manifest.json",dict(files=base.tree_hashes(data),forwards=32))
        finally:
            stop.set()
            watcher.join()
            for number,handler in handlers.items():
                signal.signal(number,handler)


def run(root, allow_gpu=False):
    require(allow_gpu and os.environ.get("CUDA_VISIBLE_DEVICES")=="0","Main GPU0 allocation and --allow-gpu required")
    plan = verify(root)
    stage = base.fresh_directory(root / "run",plan["model"])
    return base.supervise(root,plan,stage / "worker",worker_command(root))


def reduce(root):
    plan = verify(root)
    supervision = base.read(root / "run" / "worker" / "supervision.json")
    require(supervision["returncode"]==0 and all(supervision[key] is True for key in
        ("ok","owned_group_empty","gpu_processes_absent","reservation_release_verified")),"worker/cleanup incomplete")
    data = root / "run" / "data"
    require(base.read(data / "manifest.json")["files"]==base.tree_hashes(data,("manifest.json",)),"output bytes changed")
    expected={"load.json","cleanup.json","state_after.json","manifest.json"}|{row["case_id"]+suffix for row in plan["rows"] for suffix in (".json",".f32")}
    require({path.name for path in data.iterdir()}==expected,"full16 artifacts required, missing is not zero")
    require(base.read(data / "cleanup.json")["error"] is None,"HF worker failed")
    load = base.read(data / "load.json")
    require(load["exact_loaded_check"] is True and load["loaded"]==load["expected_after_dtype_conversion"] and
        load["base_frozen"] is True and load["eval"] is True,"loaded state audit failed")
    require(load["loaded"] == base.read(data / "state_after.json") and
        base.read(data / "manifest.json")["forwards"] == 32, "post-evaluation state/count mismatch")
    rows = []
    for row in plan["rows"]:
        saved = base.read(data / (row["case_id"]+".json"))
        values = [value[0] for value in struct.iter_unpack("<f",(data / (row["case_id"]+".f32")).read_bytes())]
        width = saved["vocab_size"]
        require(len(values)==3*width,"raw logit shape mismatch")
        audited = metrics(row,[values[index*width:(index+1)*width] for index in range(3)])
        require(all(saved[key]==value for key,value in audited.items()),"logit metrics differ from raw evidence")
        require(saved["case_id"]==row["case_id"] and math.isfinite(saved["hf_reported_loss"]) and
            saved["hf_loss_minus_recomputed"]==saved["hf_reported_loss"]-audited["full_response_mean_nll"],
            "case/HF loss receipt mismatch")
        rows.append(saved)
    result=dict(label=LABEL,complete=True,total=16,forwards=32,new_vllm_calls=0,optimizer_steps=0,rows=rows,
        hf_vllm_top1_agreements=sum(row["top1_matches_vllm"] for row in rows),
        plan_sha256=base.digest(root / "plan.json"),capture_sha256=base.digest(data / "manifest.json"),
        reserved_seconds=supervision["reserved_seconds"],comparison_threshold=None,
        limits="In-sample parity only; no automatic verdict from numeric differences, no dose/rank changes or scientific claim change.")
    write(root / "reduction.json",result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage",choices=("prepare","run","reduce","_worker"))
    parser.add_argument("--source-root",required=True)
    parser.add_argument("--root",required=True)
    parser.add_argument("--seed0-root")
    parser.add_argument("--seq100-root")
    parser.add_argument("--lease-end",type=float)
    parser.add_argument("--allow-gpu",action="store_true")
    args=parser.parse_args()
    bind(args.source_root)
    root=Path(args.root).expanduser().absolute()
    if args.stage=="prepare":
        require(args.seed0_root and args.seq100_root and args.lease_end is not None,"prepare inputs required")
        result=prepare(root,args.seed0_root,args.seq100_root,args.lease_end)
    elif args.stage=="_worker":
        require(args.allow_gpu,"explicit worker allowance required")
        result=worker(root)
    else:
        result=run(root,args.allow_gpu) if args.stage=="run" else reduce(root)
    print(json.dumps(result,allow_nan=False,indent=2))


if __name__=="__main__":
    main()

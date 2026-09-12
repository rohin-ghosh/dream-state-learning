import argparse
import gc
import json
import os
from pathlib import Path
import sys
import time

from organism_v6 import semantic_writer_diagnostic as diagnostic
from organism_v6 import run_reasoning_neutral as supervisor


def inspect(model, torch, request, aligned=False):
    candidates = request['candidates']
    common = 0
    for left, right in zip(candidates[0]['input_ids'], candidates[1]['input_ids']):
        if left != right:
            break
        common += 1
    assert common >= len(request['payload']['prompt_input_ids'])
    masks = []

    def hook(module, args, kwargs):
        mask = kwargs.get('attention_mask')
        masks.append(None if mask is None else dict(shape=list(mask.shape), dtype=str(mask.dtype),
            row_future_max=float(mask[0, 0, common - 1, common:].max().cpu()) if mask.ndim == 4 and mask.shape[-1] > common else None))

    attention = next(module for module in model.modules() if type(module).__name__ == 'Qwen2Attention')
    handle = attention.register_forward_pre_hook(hook, with_kwargs=True)
    vectors, totals = [], []
    maximum_length = max(len(candidate['input_ids']) for candidate in candidates)
    for candidate in candidates:
        sequence = candidate['input_ids']
        if aligned:
            sequence = sequence + [0] * (maximum_length - len(sequence))
        ids = torch.tensor([sequence], device='cuda:0')
        with torch.inference_mode():
            logits = model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False).logits
            logp = torch.log_softmax(logits[0].float(), dim=-1)
        vectors.append(logp[common - 1].cpu())
        totals.append(sum(float(logp[index - 1, token].cpu()) for index, (token, label) in
            enumerate(zip(candidate['input_ids'], candidate['labels'])) if label != -100))
    prefix_sequence = candidates[0]['input_ids'][:common]
    if aligned:
        prefix_sequence += [0] * (maximum_length - common)
    prefix = torch.tensor([prefix_sequence], device='cuda:0')
    with torch.inference_mode():
        logits = model(input_ids=prefix, attention_mask=torch.ones_like(prefix), use_cache=False).logits
        vectors.append(torch.log_softmax(logits[0, common - 1].float(), dim=-1).cpu())
    handle.remove()
    next_tokens = [candidate['input_ids'][common] for candidate in candidates]
    return dict(aligned_future_padding=aligned, dtype=str(next(model.parameters()).dtype), full_candidate_logprob=totals, full_candidate_mass=sum(__import__('math').exp(value) for value in totals),
        common_prefix_length=common, next_tokens=next_tokens,
        next_token_probabilities=[[float(vector[token].exp()) for token in next_tokens] for vector in vectors],
        max_logprob_delta_full_candidates=float((vectors[0] - vectors[1]).abs().max()),
        max_logprob_delta_full_vs_prefix=float((vectors[0] - vectors[2]).abs().max()), masks=masks,
        attention_implementation=model.config._attn_implementation,
        is_causal=getattr(model.config, 'is_causal', 'ABSENT_DEFAULT_TRUE'))


def worker(out):
    import torch
    source = Path.home() / 'astra_diagnostics/astra_semantic_writer_Q0_20260912_attempt1'
    manifest = diagnostic.read_json(source / 'manifest.json')
    assert diagnostic.sources() == manifest['sources']
    request = next(row for row in diagnostic.read_json(source / 'requests.json')
        if row['state'] == 'r0_plus' and row['operation'] == 'score'
        and row['audit']['family'] == 'neighbour' and row['audit']['index'] == 12)
    config = manifest['config']
    torch = diagnostic.w0.configure_torch(config, 0)
    records = []
    for state in ['r0_plus']:
        fit = diagnostic.read_json(source / 'stages/fit_r0_plus/DONE.json')['result']
        model = diagnostic.load_eval_model(config, torch, source, state,
            fit['adapter_sha256'] if state != 'OFF' else 'OFF',
            fit['final_lora_sha256'] if state != 'OFF' else 'OFF')
        for precision in ['bfloat16', 'float32']:
            if precision == 'float32':
                model.float()
            for aligned in [False, True]:
                records.append(dict(state=state, **inspect(model, torch, request, aligned)))
        del model
        gc.collect()
        torch.cuda.empty_cache()
    diagnostic.w0.write_once(out, 'result.json', dict(status='DIAGNOSTIC_ONLY_NO_FIT', records=records,
        request_id=request['request_id'], source_manifest_sha256=diagnostic.w0.file_hash(source / 'manifest.json')))


parser = argparse.ArgumentParser()
parser.add_argument('--out', required=True)
parser.add_argument('--worker', action='store_true')
args = parser.parse_args()
out = Path(args.out)
if args.worker:
    worker(out)
else:
    out.mkdir(parents=True, exist_ok=False)
    diagnostic.w0.write_once(out, 'STARTED.json', dict(pid=os.getpid(), started=time.time(), device=os.environ['CUDA_VISIBLE_DEVICES']))
    supervisor.run_worker([sys.executable, '-B', __file__, '--out', str(out), '--worker'],
        log_path=out / 'worker.log', timeout=600, device=supervisor.selected_device())
    diagnostic.w0.write_once(out, 'COMPLETED.json', dict(finished=time.time(), no_training=True))

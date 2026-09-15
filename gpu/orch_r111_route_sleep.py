"""Shared route-only LoRA sleep with explicit anchor and exposure accounting."""

import json

from gpu import orch_guided_native as native
from gpu.orch_l2_shared_run import write
from gpu.orch_r111_parent_provider import require
from organism_v6 import orch_r107_parented_replay as replay

ANCHOR_SHA = '2ad09dbe9673f95cbe92cd41e70d83635702b615fb7295b8b3f850e9ee674753'


def sleep_schedule(new_rows, previous_rows, anchor_rows=42):
    require(anchor_rows == 42, 'shared42_exact')
    own = [('NEW', index) for presentation in range(16) for index in range(new_rows)]
    own += [('REHEARSAL', index) for index in range(previous_rows)]
    count = max(1, len(own))
    return [dict(own=own[step] if own else None,
                 anchors=[index % 42 for index in range(step, max(42, count), count)])
            for step in range(count)]



def train_sleep(engine, optimizer, rows, history, anchors, output, check, context_limit=16384):
    encoded, rejected = [], []
    for row in rows:
        try:
            encoded.append(replay.encode_row(row, engine.tokenizer, context_limit))
        except ValueError as error:
            rejected.append(dict(source=row['source_call_sha256'], error=str(error)))
    write(output/'ENCODING.json', dict(rows=len(rows), encoded=len(encoded), rejected=rejected,
                                      structural_only=True, outcome_selection=False))
    previous, previous_rejected = [], []
    for row in history:
        try:
            previous.append(replay.encode_row(row, engine.tokenizer, context_limit))
        except ValueError as error:
            previous_rejected.append(dict(source=row['source_call_sha256'], error=str(error)))
    require(len(anchors) == 42, 'all42_shared_anchors')
    native.development.enable_existing_adapter(engine)
    engine.model.train()
    engine.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    engine.model.enable_input_require_grads()
    engine.model.config.use_cache = False
    updates, child_token_exposure, anchor_token_exposure = 0, 0, 0
    for allocation in sleep_schedule(len(encoded), len(previous)):
            check('optimizer_update')
            selected = allocation['own']
            batch = []
            if selected:
                kind, index = selected
                item = encoded[index] if kind == 'NEW' else previous[index]
                batch.append((item, .75))
                child_token_exposure += len(item.target_ids)
            for index in allocation['anchors']:
                item = anchors[index]['encoded']
                batch.append((item, .25/len(allocation['anchors'])))
                anchor_token_exposure += len(item.target_ids)
            optimizer.zero_grad(set_to_none=True)
            losses = []
            for item, weight in batch:
                inputs = engine.torch.tensor([item.input_ids], dtype=engine.torch.long, device=engine.device)
                labels = engine.torch.tensor([item.labels], dtype=engine.torch.long, device=engine.device)
                with engine.torch.autocast(device_type='cuda', dtype=engine.torch.bfloat16):
                    loss = engine.model(input_ids=inputs, attention_mask=engine.torch.ones_like(inputs), labels=labels).loss*weight
                require(bool(engine.torch.isfinite(loss)), 'nonfinite_optimizer_loss_crash')
                loss.backward()
                losses.append(float(loss.detach().cpu()))
            optimizer.step()
            updates += 1
            with (output/'UPDATES.jsonl').open('a') as stream:
                stream.write(json.dumps(dict(update=updates, allocation=allocation, losses=losses,
                    anchor_lambda=.25, child_token_exposure_including_eos=child_token_exposure,
                    anchor_token_exposure_including_eos=anchor_token_exposure))+'\n')
                stream.flush()
    engine.model.requires_grad_(False)
    engine.model.eval()
    engine.model.gradient_checkpointing_disable()
    engine.model.config.use_cache = True
    engine.verify_base()
    return dict(updates=updates, presentations_per_encoded_row=16, encoded_rows=len(encoded),
                rehearsal_presentations_per_row=1, previous_encoded_rows=len(previous),
                previous_structural_rejections=previous_rejected,
                rejected_structural_rows=len(rejected), optimizer_reset=False, outcome_selection=False,
                anchor_lambda=.25, anchor_inventory_count=42, anchor_manifest_sha256=ANCHOR_SHA,
                child_token_exposure_including_eos=child_token_exposure,
                anchor_token_exposure_including_eos=anchor_token_exposure)


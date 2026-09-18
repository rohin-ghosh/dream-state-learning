"""Bounded source-bound frozen probes and independent development-only scoring."""

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import time

from gpu import ny_caption_data as data
from research_loop.workers.rohin232_age_probe_20260918.contract import DECODER, POLICY, SEEDS, digest, run_cell
from research_loop.workers.rohin209_first_game_20260918.generate_c2 import BASE_SHA256, is_lora, tensor_state_hash
from research_loop.workers.rohin221_continuous_caption_20260918.run_base_cohort import BASE_ROOT, device_proof
from research_loop.workers.rohin221_continuous_caption_20260918.freeform import extract_batches


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + f'.{os.getpid()}.{time.time_ns()}.tmp')
    data.private_write(temporary, value)
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink()
    return data.file_ref(path)


def wait(path, deadline):
    while not path.exists():
        if time.time() >= deadline:
            raise TimeoutError('probe_deadline_before_receipt')
        time.sleep(0.1)
    return read(path)


class Backend:
    def __init__(self, source, root):
        import torch
        import tokenizers
        import transformers
        data.require(torch.cuda.device_count() == 1, 'one_visible_GPU')
        torch.set_num_threads(1)
        base_root = Path(BASE_ROOT)
        tokenizer = transformers.AutoTokenizer.from_pretrained(BASE_ROOT, local_files_only=True,
            trust_remote_code=False, use_fast=True, padding_side='right')
        tokenizer._tokenizer = tokenizers.Tokenizer.from_str((base_root/'tokenizer.json').read_text())
        base = transformers.AutoModelForCausalLM.from_pretrained(BASE_ROOT, local_files_only=True,
            trust_remote_code=False, use_safetensors=True, torch_dtype=torch.bfloat16,
            attn_implementation='sdpa', device_map=None)
        data.require(tensor_state_hash(dict(base.state_dict(keep_vars=True)), torch) == BASE_SHA256,
            'exact_frozen_base_tensor_hash')
        self.base_keys = set(base.state_dict())
        self.source = source
        if source is None:
            model = base
        else:
            import peft
            checkpoint = root/'sources'/source['source_relative']
            commit = read(checkpoint/'COMMIT.json')
            for relative, expected in source['copy_files'].items():
                data.require(data.file_ref(checkpoint/relative)['sha256'] == expected['sha256'], 'durable_checkpoint_file_hash')
            data.require(commit['base_sha256'] == BASE_SHA256 and
                commit['adapter_state_sha256'] == source['adapter_state_sha256'], 'source_commit_identity')
            for name, checksum in commit['adapter_files'].items():
                data.require(data.file_ref(checkpoint/'adapter'/name)['sha256'] == checksum, 'commit_adapter_binding')
            model = peft.PeftModel.from_pretrained(base, str(checkpoint/'adapter'), local_files_only=True,
                is_trainable=False, autocast_adapter_dtype=True)
            data.require(list(model.active_adapters) == ['default'] and
                not any(getattr(module, 'disable_adapters', False) is True for module in model.modules()),
                'one_active_adapter_not_disabled')
        self.model = model.requires_grad_(False).eval().to('cuda:0')
        self.tokenizer, self.torch, self.transformers = tokenizer, torch, transformers
        self.identity = self.verify()
        self.identity.update(decoder=DECODER, optimizer_created=False,
            tokenizer_backend_sha256=hashlib.sha256(tokenizer.backend_tokenizer.to_str().encode()).hexdigest(),
            chat_template_sha256=hashlib.sha256(tokenizer.chat_template.encode()).hexdigest(),
            library_versions=dict(torch=torch.__version__, transformers=transformers.__version__))

    def verify(self):
        data.require(not any(parameter.requires_grad for parameter in self.model.parameters()), 'frozen_parameters')
        state = dict(self.model.state_dict(keep_vars=True))
        if self.source is None:
            data.require(not any(is_lora(name) for name in state), 'plain_base_no_adapter')
            base, adapter_sha = state, None
        else:
            adapter = {name: value for name, value in self.model.named_parameters() if is_lora(name)}
            data.require(adapter and all(value.dtype == self.torch.float32 for value in adapter.values()), 'native_FP32_adapter')
            adapter_sha = tensor_state_hash(adapter, self.torch)
            data.require(adapter_sha == self.source['adapter_state_sha256'], 'actual_mounted_adapter_hash')
            base = {}
            for name, value in state.items():
                if not is_lora(name):
                    data.require(name.startswith('base_model.model.'), 'native_base_namespace')
                    original = name.removeprefix('base_model.model.').replace('.base_layer.', '.')
                    data.require(original not in base, 'unique_base_parameter')
                    base[original] = value
        data.require(set(base) == self.base_keys and tensor_state_hash(base, self.torch) == BASE_SHA256,
            'mounted_base_unchanged')
        return dict(base_sha256=BASE_SHA256, adapter_state_sha256=adapter_sha, all_parameters_frozen=True)

    def seed(self, seed):
        self.torch.manual_seed(seed)
        self.torch.cuda.manual_seed_all(seed)

    def generate(self, messages, max_new_tokens):
        tokens = self.tokenizer.apply_chat_template(messages, tokenize=True,
            add_generation_prompt=True, return_dict=False)
        data.require(0 < len(tokens) <= 8192 and 0 < max_new_tokens <= 256,
            'bounded_untruncated_probe_context')
        inputs = self.torch.tensor([tokens], device='cuda:0', dtype=self.torch.long)
        configuration = self.transformers.GenerationConfig(**DECODER, use_cache=True,
            max_new_tokens=max_new_tokens, eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id)
        started = time.time()
        with self.torch.inference_mode():
            output = self.model.generate(input_ids=inputs, attention_mask=self.torch.ones_like(inputs),
                generation_config=configuration)
        data.require(output[0, :len(tokens)].tolist() == tokens, 'actual_generation_prefix')
        tail = output[0, len(tokens):].tolist()
        terminal = bool(tail) and tail[-1] == self.tokenizer.eos_token_id
        return dict(messages=messages, prompt_tokens=len(tokens), token_ids=tail,
            raw=self.tokenizer.decode(tail[:-1] if terminal else tail, skip_special_tokens=False,
                clean_up_tokenization_spaces=False), terminal=terminal,
            truncated=not terminal and len(tail) == max_new_tokens,
            started_unix=started, finished_unix=time.time())


def describe(root, deadline):
    from gpu import ny_caption_vision as vision
    from PIL import Image
    import torch
    import transformers
    snapshot = root/'vision/snapshot'
    vision.verify_snapshot(snapshot)
    data.require(torch.cuda.device_count() == 1, 'one_visible_vision_device')
    backend = vision.QwenBackend()
    backend.deadline = deadline
    backend.processor = transformers.AutoProcessor.from_pretrained(str(snapshot), local_files_only=True,
        trust_remote_code=False, **vision.PROCESSOR)
    backend.model = transformers.Qwen2_5_VLForConditionalGeneration.from_pretrained(str(snapshot),
        local_files_only=True, trust_remote_code=False, use_safetensors=True, dtype=torch.bfloat16,
        device_map={'': 0}, attn_implementation='sdpa').eval().requires_grad_(False)
    backend.generation_config = transformers.GenerationConfig(**vision.DECODING)
    write(root/'VISION_LOADED.json', dict(unix=time.time(), pid=os.getpid(),
        snapshot_manifest=data.file_ref(snapshot/'SNAPSHOT_MANIFEST.json'), model=vision.MODEL_ID,
        revision=vision.REVISION, actual_visible_device=os.environ['CUDA_VISIBLE_DEVICES']))
    contests = []
    for image in read(root/'images/IMAGE_PACKET.json')['images']:
        image_path = Path(image['path'])
        data.require(data.file_ref(image_path)['sha256'] == image['sha256'], 'fresh_image_hash')
        with Image.open(image_path) as pixels:
            generation = backend.generate(pixels.convert('RGB'),
                'Describe only the visible people, objects, and spatial relationships. State what is uncertain.')
        visual, canonicalization = vision.canonical_visual(generation.text)
        scene = visual.observations + '\n' + visual.uncertainty
        write(root/'vision_receipts'/f"{image['handle']}.json", dict(image=image, generation=asdict(generation), canonicalization=canonicalization,
            scene_sha256=hashlib.sha256(scene.encode()).hexdigest(), source=data.file_ref(Path(vision.__file__)), unix=time.time()))
        contests.append(dict(contest_id=image['handle'], canonical_scene=scene,
            image=image['handle'], split='agent_development'))
    write(root/'GAME_MANIFEST.json', dict(mode='DEVELOPMENT', development_contest_ids=[row['contest_id'] for row in contests],
        reserved_final_contest_ids=[], contests=contests))
    write(root/'VISION_COMPLETE.json', dict(unix=time.time(), pid=os.getpid(), scenes=len(contests),
        manifest=data.file_ref(root/'GAME_MANIFEST.json'), captions_or_panels_accessed=False))


def judge(root, deadline):
    from gpu.ny_caption_game import DevelopmentManifest
    from gpu.ny_caption_pixels import PixelConfig
    from gpu.ny_caption_relative_game import build_game, prepare_references
    from gpu.ny_caption_scalar_judge import ScalarJudge
    from gpu.ny_caption_similarity import FrozenCPUEncoder
    manifest = DevelopmentManifest.from_mapping(read(root/'GAME_MANIFEST.json'))
    assets = root/'assets'
    rule = read(assets/'RULE.json')
    data.require(digest(rule) == '7127a82613c6c75ed561b180ad394a657acbc194cb27cca72bc3b0a686d6444a', 'same_frozen_game_rule')
    base_ref = write(root/'judge/base_manifest.json', dict(read(assets/'base_manifest.json'), root=BASE_ROOT))
    runtime = write(root/'judge/scalar_runtime.json', dict(schema='R207_SCALAR_RUNTIME_V1',
        base_model=base_ref, selected_adapter_root=str(assets/'adapter'),
        adapter={name: data.file_ref(assets/'adapter'/name) for name in rule['adapter']},
        config=dict(max_length=rule['max_length']), source_judge_config_sha256=rule['original_judge_config_sha256']))
    scalar = ScalarJudge(runtime['path'], batch_size=8)
    panels, panel_rows = prepare_references(data.file_ref(root/'private/DATA_MANIFEST.private.json'),
        manifest, scalar, read(root/'images/GAME_IMAGE_MAP.json'), panel_size=64, seed=207)
    panel_ref = write(root/'judge/REFERENCE_PANELS.private.json', panel_rows)
    encoder = FrozenCPUEncoder(data.file_ref(assets/'embedding_snapshot.json'), threads=2)
    pixels = PixelConfig(**read(assets/'pixel_config.json'))
    write(root/'JUDGE_LOADED.json', dict(pid=os.getpid(), unix=time.time(), top_k=50, reference_count=64,
        rule_sha256=digest(rule), panel_sha256=panel_ref['sha256'], scalar=scalar.reference,
        fresh_development_panels=True, raw_reference_captions_visible_to_players=False))
    games = {}
    while time.time() < deadline:
        for request_path in sorted((root/'queue').glob('*.request.json')):
            output_path = request_path.with_name(request_path.name.replace('.request.json', '.result.json'))
            if output_path.exists():
                continue
            request = read(request_path)
            identity = request['identity']
            condition, seed, contest = identity['condition'], identity['seed'], identity['contest_id']
            data.require(condition in ('source51', 'currentC2', 'base') and seed in SEEDS and
                contest in {item.contest_id for item in manifest.contests}, 'declared_probe_cell')
            data.require(request['raw_sha256'] == hashlib.sha256(request['raw'].encode()).hexdigest()
                and request['origin']['text_sha256'] == request['raw_sha256'], 'authentic_proposal_bytes')
            key = (condition, seed)
            if key not in games:
                games[key] = build_game(manifest, scalar, panels, pixels, encoder, top_k=50,
                    agent_id=f'{condition}-{seed}', lane='R232_DEVELOPMENT_EVALUATION',
                    relevance_threshold=rule['relevance_threshold'])
            scene = next(item for item in manifest.contests if item.contest_id == contest)
            actions, parsed = extract_batches(request['raw'], [dict(contest_id=contest,
                canonical_scene=scene.canonical_scene)], active_scene=contest,
                explicit_candidates_only=request['origin']['stage'] == 'THINK')
            results = []
            for action in actions:
                for caption in action['captions']:
                    outcome = games[key].submit_caption(contest, caption)
                    results.append(dict(caption_sha256=hashlib.sha256(caption.encode()).hexdigest(), result=outcome))
            feedback = []
            for number, row in enumerate(results, 1):
                result = row['result']
                feedback.append(f"Caption {number}: rank {result.get('rank')} of 65; accepted {result.get('accepted')}; "
                    f"novelty {result.get('status')}; relevance {result.get('relevance_score')}; cached {result.get('cached', False)}.")
            if not feedback:
                feedback.append('No caption was scored in this output. Offer the captions themselves for the active scene; no fixed format is required.')
            receipt = dict(request_sha256=digest(request), unix=time.time(), results=results,
                parsed=parsed, feedback='\n'.join(feedback), new_pixels=sum(row['result'].get('status') == 'new_pixel'
                    and not row['result'].get('cached', False) for row in results))
            write(output_path, receipt)
        time.sleep(0.1)
        if all((root/'players'/condition/'COMPLETE.json').exists() for condition in ('source51', 'currentC2', 'base')):
            break
    write(root/'JUDGE_EXIT.json', dict(unix=time.time(), pid=os.getpid(), independent_games=len(games)))


def player(root, condition, deadline):
    manifest = wait(root/'GAME_MANIFEST.json', deadline)
    evidence = wait(root/'FRESHNESS_VERIFIED.json', deadline)
    data.require(evidence['eligible'] is True, 'both_source_exposure_checked')
    capture = read(root/'sources/CAPTURE.json')
    source = None if condition == 'base' else capture['sources'][0 if condition == 'source51' else 1]
    output = root/'players'/condition
    started = time.time()
    backend = Backend(source, root)
    write(output/'LOADED.json', dict(unix=time.time(), pid=os.getpid(), model_load_seconds=time.time()-started,
        condition=condition, source_age=source, identity=backend.identity, policy=POLICY,
        snapshot_context_used=False, actual_visible_device=os.environ['CUDA_VISIBLE_DEVICES']))
    wait(root/'JUDGE_LOADED.json', deadline)
    results = []
    for contest in manifest['contests']:
        scene = {key: contest[key] for key in ('contest_id', 'canonical_scene')}
        for seed in SEEDS:
            cell = output/f"{scene['contest_id']}_{seed}"
            counter = 0
            def score(raw, stage, origin):
                nonlocal counter
                counter += 1
                key = f"{condition}-{scene['contest_id']}-{seed}-{counter:04d}"
                request = dict(identity=dict(condition=condition, seed=seed, contest_id=scene['contest_id']),
                    raw=raw, raw_sha256=hashlib.sha256(raw.encode()).hexdigest(), origin=origin)
                write(root/'queue'/f'{key}.request.json', request)
                receipt = wait(root/'queue'/f'{key}.result.json', deadline)
                data.require(receipt['request_sha256'] == digest(request), 'scorer_bound_actual_request')
                return receipt
            def emit(value):
                write(cell/f'{counter:04d}.json', value)
                elapsed = time.time()-started
                event = value['event']
                progress = dict(condition=condition, unix=time.time(), cell=cell.name,
                    actual_generated_tokens=sum(item['generated_tokens'] for item in results)+event['origin']['generated_tokens_after'],
                    elapsed_seconds=elapsed, current_event=event)
                temporary = output/'PROGRESS.tmp'
                temporary.write_text(json.dumps(progress, sort_keys=True))
                temporary.replace(output/'PROGRESS.json')
            result = run_cell(backend, scene, seed, score, emit)
            result.update(contest_id=scene['contest_id'], seed=seed)
            write(cell/'RESULT.json', result)
            results.append(result)
    final_identity = backend.verify()
    write(output/'COMPLETE.json', dict(unix=time.time(), condition=condition, cells=results,
        actual_generated_tokens=sum(item['generated_tokens'] for item in results),
        unchanged_identity=final_identity, elapsed_seconds=time.time()-started,
        raw_acceptance_not_certified_literal_jokes=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--mode', choices=['vision', 'judge', 'source51', 'currentC2', 'base'], required=True)
    parser.add_argument('--physical', type=int, required=True)
    parser.add_argument('--deadline', type=float, required=True)
    args = parser.parse_args()
    data.require(0 < args.deadline-time.time() <= 7200, 'bounded_probe_runtime')
    write(args.root/f'{args.mode}_DEVICE_PROOF.json', device_proof(args.physical))
    try:
        if args.mode == 'vision':
            describe(args.root, args.deadline)
        elif args.mode == 'judge':
            judge(args.root, args.deadline)
        else:
            player(args.root, args.mode, args.deadline)
    except Exception as error:
        write(args.root/f'{args.mode}_FAILED.json', dict(unix=time.time(), error_type=type(error).__name__,
            error=str(error), no_live_life_mutations=True))
        raise


if __name__ == '__main__':
    main()

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from gpu.ny_caption_life_service import LifeSession
from research_loop.workers.rohin221_continuous_caption_20260918.controller import (
    Controller, Plan, PendingExternalResult, file_ref,
)
from research_loop.workers.rohin221_continuous_caption_20260918.freeform import extract_batches
from research_loop.workers.rohin221_continuous_caption_20260918.collect import hourly
from research_loop.workers.rohin221_continuous_caption_20260918.generation_origin import (
    KIND, generation_origin, validate_generation_origin, process_generation,
)


SCENES = [dict(contest_id='opaque-a', canonical_scene='Two adults beside a crib.')]


class Backend:
    kind = 'SYNTHETIC_CPU_TEST_ONLY'

    def state_receipt(self):
        return dict(kind=self.kind, optimizer_created=False)

    def count_tokens(self, messages):
        return 100

    def generate(self, messages, *, max_new_tokens):
        if messages[-1]['content'].startswith('THINK:'):
            raw = 'For the crib:\nCaption: Own THINK joke.'
        else:
            repaired = any('Actual environment feedback' in message['content'] for message in messages)
            raw = 'Captions for Scene1:\nCaption: Own ACT joke.\nThese captions are ready.' if repaired else 'Question: how?'
        return dict(messages=messages, raw=raw, token_ids=[1, 2], prompt_tokens=100, terminal=True, truncated=False)


class Game:
    def __init__(self):
        self.received = []

    def snapshot(self):
        return dict(received=list(self.received))

    def restore(self, state):
        self.received = [tuple(item) for item in state['received']]

    def submit_caption(self, contest, caption):
        repeated = (contest, caption) in self.received
        self.received.append((contest, caption))
        return dict(ok=True, accepted=True, status='repeat' if repeated else 'new_pixel',
                    rank=3, reference_count=64, top_k=50)


class Scorer:
    def __init__(self, root, plan):
        self.root, self.plan, self.session = root, plan, None
        self.binding = dict(rule_sha256=plan.rule_sha256, top_k=50, reference_count=64,
                            relevance=True, novelty=True, condition=plan.condition)

    def attach(self, controller):
        self.expected, self.backend = controller.binding, controller.backend.state_receipt()
        self.session = LifeSession(Game(), self.root / 'private/generations', self.root / 'service', SCENES,
            source_mode=KIND, session_binding=dict(controller=self.expected, backend=self.backend))

    def submit(self, request):
        return process_generation(self.session, dict(origin=generation_origin(request['source'], request['think_source']),
            metrics=request['metrics']), receipt_root=self.root / 'private/generations',
            expected_binding=self.expected, expected_backend_state=self.backend)

    def lookup(self, identifier):
        return None


def setup(tmp_path):
    plan = Plan(condition='cpu-test', rule_sha256='a'*64)
    scorer = Scorer(tmp_path, plan)
    controller = Controller(tmp_path, plan, Backend(), scorer, SCENES, extract_batches)
    scorer.attach(controller)
    return controller, scorer


def test_continuous_24_plus_freeform_repair_think_source_and_hourly(tmp_path):
    controller, scorer = setup(tmp_path)
    with controller:
        events = controller.run()
        assert controller.state['completed_opportunities'] == 24
        assert len(events) == 25
        assert events[0]['opportunity'] == events[1]['opportunity'] == 1
        assert events[0]['fault'] and events[0]['salvaged_THINK'] == 1
        assert not events[1]['fault'] and events[1]['parsed'] == 1
        assert events[0]['novel'] == events[1]['novel'] == 1
        assert any('"rank": 3' in message['content'] for message in controller.state['history'])
        assert 'actual' not in controller.state.get('LOADED', {})
        counts = hourly(json.loads((tmp_path / 'ATTEMPTS.public.json').read_text()))
        assert sum(bucket['attempts'] for bucket in counts['buckets'].values()) == 25
        assert sum(bucket['THINK_generated_tokens'] for bucket in counts['buckets'].values()) == 48
        assert sum(bucket['ACT_generated_tokens'] for bucket in counts['buckets'].values()) == 50
        assert counts['total_generated_tokens_including_THINK'] == 98
        assert counts['pending'] is None and not counts['live_GPU_claim']
        for stage in ['THINK', 'ACT']:
            prompt = json.dumps(controller.messages(stage))
            assert 'Then give Scene, Direction, Count' not in prompt
            assert 'one scene and one to ten' not in prompt


def test_standalone_origin_request_response_tamper_and_path_confined(tmp_path):
    controller, scorer = setup(tmp_path)
    with controller:
        controller.step()
        controller.step()
        source = controller.state['events'][0]['source']
        origin = generation_origin(source, controller.state['think_source'])
        kwargs = dict(receipt_root=tmp_path / 'private/generations', expected_binding=controller.binding,
                      expected_backend_state=controller.backend.state_receipt())
        verified = validate_generation_origin(origin, **kwargs)
        assert verified['stage'] == 'ACT' and verified['think']['stage'] == 'THINK'
        with pytest.raises(ValueError, match='generation_request_response_hashes'):
            validate_generation_origin(dict(origin, response_sha256='b'*64), **kwargs)
        outside = tmp_path / 'outside.json'
        outside.write_bytes(Path(source['generation']['path']).read_bytes())
        with pytest.raises(ValueError, match='confined_bounded'):
            validate_generation_origin(dict(origin, generation=file_ref(outside)), **kwargs)
        with pytest.raises(ValueError, match='same_condition_model_source_stage'):
            validate_generation_origin(origin, **dict(kwargs, expected_backend_state={'kind':'other'}))
        with pytest.raises(ValueError, match='duplicate_ACT'):
            process_generation(scorer.session, dict(origin=origin, metrics=dict(THINK=2, ACT=2, LEARN=0)), **kwargs)


def test_resume_keeps_opportunity_history_and_pending_no_redispatch(tmp_path):
    controller, scorer = setup(tmp_path)
    with controller:
        controller.run(opportunity_limit=1)
        before = list(controller.state['history'])
        binding = controller.binding
    with Controller(tmp_path, scorer.plan, Backend(), scorer, SCENES, extract_batches) as resumed:
        assert resumed.binding == binding and resumed.state['history'] == before
        assert resumed.state['completed_opportunities'] == 1
        resumed.state['pending'] = dict(kind='GENERATION', request_id='b'*64)
        resumed.save()
        with pytest.raises(PendingExternalResult):
            resumed.step()
        public = json.loads((tmp_path / 'ATTEMPTS.public.json').read_text())
        assert public['pending']['kind'] == 'GENERATION'


def test_counts_optional_and_real_result_schema():
    from research_loop.workers.rohin221_continuous_caption_20260918.controller import observed_counts
    totals, child = observed_counts(dict(feedback=[dict(result=dict(ok=True, accepted=False, rank=55,
        status='rejected', reference_count=64, top_k=50))]), 1)
    assert totals['scored'] == 1 and totals['accepted'] == 0 and child[0]['rank'] == 55


def test_generation_service_is_distinct_from_native_and_clarifies(tmp_path):
    from gpu.ny_caption_generation_service import GenerationSession
    controller, scorer = setup(tmp_path)
    with controller:
        scorer.session = GenerationSession(Game(), tmp_path / 'private/generations', tmp_path / 'generation-service',
            SCENES, source_mode=KIND, session_binding=dict(controller=controller.binding, backend=scorer.backend))
        controller.step()
        generated, source = controller.generate('ACT')
        origin = generation_origin(source, controller.state['think_source'])
        result = scorer.session.process(dict(origin=origin, metrics=dict(THINK=0, ACT=2, LEARN=0)))
        assert result['origin']['kind'] == KIND and result['report']['next_stage'] == 'ACT'
        assert result['report']['format_metrics']['salvaged_THINK_count'] == 1
        assert result['condition'] == 'cpu-test' and result['request_id'] == source['request_id']


def test_legacy_direct_policy_count_guard_still_preserved():
    from gpu.ny_caption_action_policy import CaptionActionPolicy
    action = dict(tool='caption_batch', contest_id='opaque-a', direction='legacy', count=11,
                  captions=[str(ordinal) for ordinal in range(11)])
    assert CaptionActionPolicy(Game()).submit(action)['error'] == 'batch_growth_too_large'

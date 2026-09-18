"""Real frozen-base inference and owner-local scorer adapters; no native forgery."""

from copy import deepcopy
import json
from pathlib import Path

from gpu import ny_caption_data as data
from gpu.ny_caption_life import request as socket_request
from research_loop.workers.rohin221_continuous_caption_20260918.controller import file_ref
from research_loop.workers.rohin221_continuous_caption_20260918.generation_origin import generation_origin


class BaseBackend:
    kind = 'FROZEN_BASE_NO_LORA_NO_LEARNING'

    def __init__(self, base_root, device='cuda:0'):
        from research_loop.workers.rohin209_first_game_20260918 import matched_players, generate_c2
        self.backend = matched_players.FrozenBase(base_root, device)
        self.source = dict(adapter=file_ref(__file__), loader=file_ref(matched_players.__file__),
                           generation=file_ref(generate_c2.__file__))

    def count_tokens(self, messages):
        return len(self.backend.tokenizer.apply_chat_template(messages, tokenize=True,
            add_generation_prompt=True, return_dict=False))

    def generate(self, messages, *, max_new_tokens):
        return self.backend.generate(messages, max_new_tokens)

    def state_receipt(self):
        data.require(not any(parameter.requires_grad for parameter in self.backend.model.parameters()),
                     'frozen_base_no_training')
        return dict(kind=self.kind, identity=deepcopy(self.backend.identity), source=self.source)


class SocketScorer:
    def __init__(self, socket_path, binding, *, output=None):
        self.socket_path, self.binding = str(socket_path), binding
        self.output = Path(output).resolve() if output else None

    def submit(self, request):
        origin = generation_origin(request['source'], request['think_source'])
        reply = socket_request(self.socket_path, origin, request['metrics'])
        data.require(reply.get('condition') == self.binding['condition']
            and reply.get('rule_sha256') == self.binding['rule_sha256']
            and reply.get('request_id') == request['request_id'], 'same_standalone_scoring_binding')
        return reply

    def lookup(self, identifier):
        if self.output is None:
            return None
        data.require(len(identifier) == 64 and all(character in '0123456789abcdef' for character in identifier),
                     'bounded_lookup_identifier')
        target = self.output / 'attempts' / identifier
        result, after = target / 'RESULT.json', target / 'AFTER.json'
        if not result.is_file() or not after.is_file():
            return None
        document = data.bound(data.file_ref(result))
        data.require(document['origin']['request_id'] == identifier
            and document.get('condition') == self.binding['condition']
            and document.get('rule_sha256') == self.binding['rule_sha256'], 'same_completed_score_receipt')
        return dict(policy=document['policy'], origin=document['origin'], report=document['report'],
            request_id=identifier, condition=self.binding['condition'], rule_sha256=self.binding['rule_sha256'],
            receipt_sha256=data.file_ref(result)['sha256'])


def base_factory(args):
    return BaseBackend(args.base_root, args.device)


def scorer_factory(args):
    return SocketScorer(args.socket, json.loads(Path(args.scorer_binding).read_text()), output=args.scorer_output)

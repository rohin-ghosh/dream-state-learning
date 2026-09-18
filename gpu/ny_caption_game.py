"""CPU-only DEVELOPMENT tool core with explicit, injected scoring and vision."""

from __future__ import annotations

from copy import deepcopy
from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import re
from threading import RLock
from typing import Callable, Mapping

from gpu.ny_caption_pixels import (
    ArchiveFullError, Embed, PixelArchive, PixelConfig, SameJokeVerifier, SnapshotError,
    _require_snapshot, _same_json, _snapshot_copy,
)


@dataclass(frozen=True)
class Contest:
    contest_id: str
    canonical_scene: str
    image: str | bytes
    split: str = 'agent_development'

    def __post_init__(self) -> None:
        for name in ('contest_id', 'canonical_scene'):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f'{name} must be nonempty text')
        if self.split != 'agent_development':
            raise ValueError('only agent_development contests may enter Stage 1')
        if not isinstance(self.image, (str, bytes)) or not self.image:
            raise ValueError('image must be nonempty bytes or an opaque image handle')


@dataclass(frozen=True)
class DevelopmentManifest:
    contests: tuple[Contest, ...]
    reserved_final_contest_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.contests, (tuple, list)) or not isinstance(self.reserved_final_contest_ids, (tuple, list)):
            raise ValueError('contests and reserved_final_contest_ids must be sequences, not text')
        object.__setattr__(self, 'contests', tuple(self.contests))
        object.__setattr__(self, 'reserved_final_contest_ids', tuple(self.reserved_final_contest_ids))
        if len(self.contests) != 3 or any(not isinstance(contest, Contest) for contest in self.contests):
            raise ValueError('Stage 1 requires exactly three development cartoons')
        identifiers = [contest.contest_id for contest in self.contests]
        if len(set(identifiers)) != 3:
            raise ValueError('development contest IDs must be distinct')
        if any(not isinstance(identifier, str) or not identifier.strip()
               for identifier in self.reserved_final_contest_ids):
            raise ValueError('reserved contest IDs must be nonempty text')
        if set(identifiers).intersection(self.reserved_final_contest_ids):
            raise ValueError('reserved final contests cannot enter development')

    @classmethod
    def from_mapping(cls, manifest: Mapping) -> DevelopmentManifest:
        allowed = {'mode', 'development_contest_ids', 'reserved_final_contest_ids', 'contests'}
        if not isinstance(manifest, Mapping) or set(manifest) - allowed:
            raise ValueError('project the data manifest to the documented game-only fields')
        if manifest.get('mode') != 'DEVELOPMENT':
            raise ValueError('only DEVELOPMENT mode is supported')
        contests = manifest.get('contests')
        allowlist = manifest.get('development_contest_ids')
        if not isinstance(contests, (tuple, list)) or not isinstance(allowlist, (tuple, list)):
            raise ValueError('contests and development_contest_ids must be lists')
        if len(allowlist) != 3 or any(not isinstance(identifier, str) for identifier in allowlist):
            raise ValueError('development allowlist must contain three contest IDs')
        if any(not isinstance(contest, Mapping) or set(contest) !=
               {'contest_id', 'canonical_scene', 'image', 'split'} for contest in contests):
            raise ValueError('contest entries require exactly contest_id, canonical_scene, image and split')
        result = cls(tuple(Contest(**contest) for contest in contests),
                     manifest.get('reserved_final_contest_ids', ()))
        if len(set(allowlist)) != 3 or set(allowlist) != {contest.contest_id for contest in result.contests}:
            raise ValueError('contest rows must match the development allowlist exactly')
        return result


@dataclass(frozen=True)
class GameConfig:
    tau: float
    visual_call_limit: int = 100
    caption_word_limit: int = 50
    question_token_limit: int = 128
    visual_response_token_limit: int = 256
    transport_retries: int = 2
    max_submissions_per_contest: int = 10000

    def __post_init__(self) -> None:
        if isinstance(self.tau, bool) or not isinstance(self.tau, (float, int)):
            raise ValueError('tau must be an explicit numeric threshold')
        if not math.isfinite(self.tau) or not 0 <= self.tau <= 1:
            raise ValueError('tau must be finite and in [0, 1]')
        for name, minimum, maximum in (
                ('visual_call_limit', 0, 10000), ('caption_word_limit', 1, 50),
                ('question_token_limit', 1, 128), ('visual_response_token_limit', 1, 256),
                ('transport_retries', 0, 2), ('max_submissions_per_contest', 1, 10000)):
            value = getattr(self, name)
            if type(value) is not int or not minimum <= value <= maximum:
                raise ValueError(f'{name} must be an integer in [{minimum}, {maximum}]')


@dataclass(frozen=True)
class JudgeResult:
    scene_fit: bool
    q: float

    def __post_init__(self) -> None:
        if type(self.scene_fit) is not bool:
            raise ValueError('scene_fit must be a bool')
        if isinstance(self.q, bool) or not isinstance(self.q, (float, int)):
            raise ValueError('q must be an actual numeric probability estimate')
        if not math.isfinite(self.q) or not 0 <= self.q <= 1:
            raise ValueError('q must be finite and in [0, 1]')


@dataclass(frozen=True)
class VisualResult:
    observations: str
    uncertainty: str

    def __post_init__(self) -> None:
        if any(not isinstance(value, str) or not value.strip()
               for value in (self.observations, self.uncertainty)):
            raise ValueError('visual observations and explicit uncertainty must be nonempty text')


class TransportError(RuntimeError):
    """The adapter explicitly identifies a retryable transport fault."""


_INJECTION = re.compile(
    r'ignore\s+(?:(?:all|any|the)\s+)?(?:previous|prior|system|scoring|above)\s+(?:instructions?|rules?|prompts?)'
    r'|(?:<\|(?:im_start|system|assistant|endoftext)\|>|</?(?:system|developer)\b)'
    r'|\b(?:scene_fit|acceptance_score)\s*[:=]'
    r'|\b(?:return|set|output)\s+(?:the\s+)?(?:score|q|accepted)\s*(?:to\s+|[=:]\s*)?(?:1|true|100)\b'
    r'|\b(?:execute|run)\s+(?:this|the|following)\s+(?:following\s+)?(?:code|command|script)\b',
    re.IGNORECASE)


class CaptionGame:
    def __init__(self, agent_id: str, lane: str, manifest: DevelopmentManifest,
                 config: GameConfig, pixel_config: PixelConfig, *, embed: Embed,
                 judge: Callable[[str, str], JudgeResult],
                 inspect_provider: Callable[[str | bytes, str], VisualResult],
                 count_tokens: Callable[[str], int],
                 same_joke_verifier: SameJokeVerifier | None = None):
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError('agent_id must be nonempty text')
        if not isinstance(lane, str) or not lane.strip():
            raise ValueError('lane must be a nonempty lineage identifier')
        if not isinstance(manifest, DevelopmentManifest) or not isinstance(config, GameConfig):
            raise ValueError('explicit DevelopmentManifest and GameConfig are required')
        if any(not callable(callback) for callback in (embed, judge, inspect_provider, count_tokens)):
            raise ValueError('embedding, judge, visual provider and tokenizer callables are required')
        self.agent_id, self.lane, self.manifest, self.config = agent_id, lane, manifest, config
        self._judge, self._inspect_provider, self._count_tokens = judge, inspect_provider, count_tokens
        self._contests = {contest.contest_id: contest for contest in manifest.contests}
        self._archives = {contest.contest_id: PixelArchive(
            agent_id, contest.contest_id, contest.canonical_scene, pixel_config, embed,
            max_submissions=config.max_submissions_per_contest, same_joke_verifier=same_joke_verifier)
            for contest in manifest.contests}
        self._submissions: dict[tuple[str, str], dict] = {}
        self._visual_cache: dict[tuple[str, str], VisualResult] = {}
        self._events: list[dict] = []
        self._event_limit = config.max_submissions_per_contest * 3 + config.visual_call_limit * 4 + 128
        self._counters = dict(visual_calls=0, visual_transport_attempts=0, judge_attempts=0,
                              question_tokens=0, visual_context_tokens=0, external_visual_tokens=0,
                              failed_visual_attempts=0)
        self._accounting: list[dict] = []
        self._accounting_base = None
        self._lock = RLock()

    @property
    def remaining_visual_calls(self) -> int:
        with self._lock:
            return self.config.visual_call_limit - self._counters['visual_calls']

    def _failure(self, code: str, message: str, *, pause_required: bool = False) -> dict:
        result = dict(ok=False, status='error', error=dict(code=code, message=message),
                      pause_required=pause_required, remaining_budget=self.remaining_visual_calls)
        if len(self._events) < self._event_limit:
            self._events.append(deepcopy(result))
        return result

    def _validate_contest(self, contest_id: str) -> dict | None:
        if len(self._events) + self.config.transport_retries + 2 > self._event_limit:
            return self._failure('history_full', 'Development event allowance exhausted; preserve state and pause.',
                                 pause_required=True)
        if not isinstance(contest_id, str) or contest_id not in self._contests:
            return self._failure('contest_not_allowed', 'Contest is not in the three-cartoon development allowlist.')
        return None

    def _tokens(self, text: str) -> int:
        count = self._count_tokens(text)
        if type(count) is not int or count <= 0:
            raise ValueError('token counter must return a positive integer for nonempty text')
        return count

    def _invoke(self, operation: str, callback: Callable, *args) -> tuple[object, dict | None]:
        counter = 'visual_transport_attempts' if operation == 'inspect_image' else 'judge_attempts'
        for attempt in range(self.config.transport_retries + 1):
            self._counters[counter] += 1
            try:
                return callback(*args), None
            except TransportError:
                if operation == 'inspect_image':
                    self._counters['failed_visual_attempts'] += 1
                self._events.append(dict(operation=operation, error='transport_fault', attempt=attempt + 1))
                if attempt == self.config.transport_retries:
                    return None, self._failure('transport_exhausted',
                                               f'{operation} transport retries exhausted; pause this operation.',
                                               pause_required=True)
            except Exception:
                if operation == 'inspect_image':
                    self._counters['failed_visual_attempts'] += 1
                return None, self._failure('provider_error', f'{operation} provider failed without a usable result.',
                                           pause_required=True)
        raise RuntimeError('unreachable transport state')

    def _record_accounting(self, tool: str, contest_id: str, text: str, before: dict, result: dict) -> None:
        delta = {name: value - before[name] for name, value in self._counters.items()}
        if any(delta.values()):
            self._accounting.append(dict(tool=tool, contest_id=contest_id, input=text,
                                         counter_delta=delta, result=deepcopy(result)))

    def inspect_image(self, contest_id: str, question: str) -> dict:
        with self._lock:
            before = dict(self._counters)
            result = self._inspect_image(contest_id, question)
            self._record_accounting('inspect_image', contest_id, question, before, result)
            return result

    def _inspect_image(self, contest_id: str, question: str) -> dict:
        with self._lock:
            error = self._validate_contest(contest_id)
            if error is not None:
                return error
            if not isinstance(question, str) or not question.strip():
                return self._failure('invalid_question', 'Supply one nonempty factual question.')
            try:
                question_tokens = self._tokens(question)
            except Exception:
                return self._failure('tokenizer_error', 'Question token count is unavailable.', pause_required=True)
            if question_tokens > self.config.question_token_limit:
                return self._failure('question_too_long', f'Question exceeds {self.config.question_token_limit} tokens.')
            if _INJECTION.search(question):
                return self._failure('injection_rejected', 'Tool-control instructions are not factual image questions.')
            if self.remaining_visual_calls == 0:
                return self._failure('visual_budget_exhausted', 'Visual call allowance exhausted; continue from existing notes.')
            self._counters['visual_calls'] += 1
            self._counters['question_tokens'] += question_tokens
            key = (contest_id, question)
            cached = key in self._visual_cache
            if cached:
                visual = self._visual_cache[key]
            else:
                visual, error = self._invoke('inspect_image', self._inspect_provider,
                                              self._contests[contest_id].image, question)
                if error is not None:
                    return error
            if isinstance(visual, Mapping):
                try:
                    visual = VisualResult(**visual)
                except (TypeError, ValueError):
                    visual = None
            if not isinstance(visual, VisualResult):
                return self._failure('invalid_visual_result', 'Provider must return observations and uncertainty only.',
                                     pause_required=True)
            try:
                response_tokens = self._tokens(visual.observations + '\n' + visual.uncertainty)
            except Exception:
                return self._failure('tokenizer_error', 'Visual response token count is unavailable.', pause_required=True)
            if not cached:
                self._counters['external_visual_tokens'] += response_tokens
            if response_tokens > self.config.visual_response_token_limit:
                return self._failure('visual_response_too_long',
                                     f'Provider response exceeds {self.config.visual_response_token_limit} tokens; no observation delivered.',
                                     pause_required=True)
            if _INJECTION.search(visual.observations + '\n' + visual.uncertainty):
                return self._failure('injection_rejected', 'Visual response contains tool-control instructions; no observation delivered.',
                                     pause_required=True)
            self._visual_cache[key] = visual
            self._counters['visual_context_tokens'] += response_tokens
            result = dict(ok=True, status='ok', contest_id=contest_id, observations=visual.observations,
                          uncertainty=visual.uncertainty, remaining_budget=self.remaining_visual_calls,
                          question_tokens=question_tokens, response_tokens=response_tokens, cached=cached)
            self._events.append(dict(operation='inspect_image', question=question, result=deepcopy(result)))
            return result

    def submit_caption(self, contest_id: str, text: str) -> dict:
        with self._lock:
            before = dict(self._counters)
            result = self._submit_caption(contest_id, text)
            self._record_accounting('submit_caption', contest_id, text, before, result)
            return result

    def _submit_caption(self, contest_id: str, text: str) -> dict:
        with self._lock:
            if isinstance(contest_id, str) and isinstance(text, str) and (contest_id, text) in self._submissions:
                return dict(deepcopy(self._submissions[(contest_id, text)]), replayed=True)
            error = self._validate_contest(contest_id)
            if error is not None:
                return error
            if not isinstance(text, str) or not text.strip():
                return self._failure('invalid_caption', 'Supply one nonempty caption; split batches into separate calls.')
            if len(text.split()) > self.config.caption_word_limit:
                return self._failure('caption_too_long', f'Caption exceeds {self.config.caption_word_limit} words.')
            key = (contest_id, text)
            archive = self._archives[contest_id]
            if len(archive.history) >= self.config.max_submissions_per_contest:
                return self._failure('submission_budget_exhausted', 'Unique caption allowance exhausted for this cartoon.')
            injection = bool(_INJECTION.search(text))
            judgement = None
            if not injection:
                judgement, error = self._invoke('submit_caption', self._judge,
                                                 self._contests[contest_id].canonical_scene, text)
                if error is not None:
                    return error
                if isinstance(judgement, Mapping):
                    try:
                        judgement = JudgeResult(**judgement)
                    except (TypeError, ValueError):
                        judgement = None
                if not isinstance(judgement, JudgeResult):
                    return self._failure('invalid_judge_result', 'Judge must return scene_fit and a finite q probability only.',
                                         pause_required=True)
            accepted = not injection and judgement.scene_fit and judgement.q >= self.config.tau
            try:
                trace = archive.submit(text, accepted=accepted, q=judgement.q if judgement else None)
            except ArchiveFullError:
                return self._failure('submission_budget_exhausted', 'Unique caption allowance exhausted for this cartoon.')
            except Exception:
                return self._failure('pixel_error', 'Pixel encoder or verifier failed; no submission committed.', pause_required=True)
            result = dict(ok=True, contest_id=contest_id, accepted=trace.accepted,
                          q=trace.q, scene_fit=judgement.scene_fit if judgement else None,
                          status=trace.status, pixel_id=trace.pixel_id, pixel_count=archive.pixel_count,
                          matching_caption=trace.matching_caption, nearest_similarity=trace.nearest_similarity,
                          submission_id=trace.submission_id, replayed=False,
                          rejection_reason='injection_detected' if injection else
                          None if accepted else 'scene_fit' if not judgement.scene_fit else 'below_tau',
                          scoring_status='provisional_development')
            self._submissions[key] = deepcopy(result)
            self._events.append(dict(operation='submit_caption', caption=text, result=deepcopy(result)))
            return result

    @classmethod
    def from_snapshot(cls, snapshot: Mapping, agent_id: str, lane: str, manifest: DevelopmentManifest,
                      config: GameConfig, pixel_config: PixelConfig, *, embed: Embed,
                      judge: Callable[[str, str], JudgeResult],
                      inspect_provider: Callable[[str | bytes, str], VisualResult],
                      count_tokens: Callable[[str], int],
                      same_joke_verifier: SameJokeVerifier | None = None) -> CaptionGame:
        game = cls(agent_id, lane, manifest, config, pixel_config, embed=embed, judge=judge,
                   inspect_provider=inspect_provider, count_tokens=count_tokens,
                   same_joke_verifier=same_joke_verifier)
        game.restore(snapshot)
        return game

    def _validate_counters(self, counters: dict, events: list[dict]) -> None:
        _require_snapshot(isinstance(counters, dict) and set(counters) == set(self._counters), 'invalid counter fields')
        _require_snapshot(all(type(value) is int and value >= 0 for value in counters.values()), 'counters must be nonnegative integers')
        remaining = self.config.visual_call_limit
        successful_questions = context_tokens = external_tokens = successful_visuals = 0
        visual_bases = judge_bases = visual_faults = judge_faults = visual_provider_faults = 0
        unknown_visual_attempts = measured_visual_errors = 0
        for event in events:
            if event.get('error') == 'transport_fault':
                visual_faults += int(event['operation'] == 'inspect_image')
                judge_faults += int(event['operation'] == 'submit_caption')
            elif event.get('operation') == 'inspect_image':
                result = event['result']
                _require_snapshot(result['remaining_budget'] == remaining - 1, 'visual access did not consume one logical call')
                remaining = result['remaining_budget']
                successful_visuals += 1
                successful_questions += result['question_tokens']
                context_tokens += result['response_tokens']
                if not result['cached']:
                    external_tokens += result['response_tokens']
                    visual_bases += 1
            elif event.get('operation') == 'submit_caption':
                judge_bases += int(event['result']['q'] is not None)
            elif event.get('ok') is False:
                next_remaining = event['remaining_budget']
                _require_snapshot(next_remaining in (remaining, remaining - 1) and next_remaining >= 0,
                                  'error history resets or overcharges visual budget')
                charged = next_remaining != remaining
                remaining = next_remaining
                code = event['error']['code']
                if charged:
                    _require_snapshot(code in ('transport_exhausted', 'provider_error', 'invalid_visual_result',
                                               'tokenizer_error', 'visual_response_too_long', 'injection_rejected'),
                                      'nonvisual error consumed visual budget')
                    if code in ('tokenizer_error', 'visual_response_too_long', 'injection_rejected'):
                        unknown_visual_attempts += 1
                    elif code != 'transport_exhausted':
                        visual_bases += 1
                    visual_provider_faults += int(code == 'provider_error')
                    measured_visual_errors += int(code in ('visual_response_too_long', 'injection_rejected'))
                elif code in ('provider_error', 'invalid_judge_result', 'pixel_error'):
                    judge_bases += 1
        calls = self.config.visual_call_limit - remaining
        failed_calls = calls - successful_visuals
        _require_snapshot(counters['visual_calls'] == calls, 'visual call counter does not close over events')
        _require_snapshot(successful_questions + failed_calls <= counters['question_tokens'] <=
                          successful_questions + failed_calls * self.config.question_token_limit,
                          'question-token counter contradicts recorded accesses')
        _require_snapshot(counters['visual_context_tokens'] == context_tokens, 'visual context tokens do not close over responses')
        _require_snapshot(counters['external_visual_tokens'] >= external_tokens and
                          (measured_visual_errors > 0 or counters['external_visual_tokens'] == external_tokens),
                          'provider-token counter contradicts recorded responses')
        _require_snapshot(visual_bases + visual_faults <= counters['visual_transport_attempts'] <=
                          visual_bases + visual_faults + unknown_visual_attempts,
                          'visual transport attempts do not close over faults and responses')
        _require_snapshot(counters['failed_visual_attempts'] == visual_faults + visual_provider_faults,
                          'failed visual attempts do not close over faults')
        _require_snapshot(counters['judge_attempts'] == judge_bases + judge_faults, 'judge attempts do not close over submissions and faults')

    def restore(self, snapshot: Mapping) -> None:
        with self._lock:
            _require_snapshot(not self._events and not self._submissions and not self._visual_cache and
                              not self._accounting and not any(self._counters.values()) and
                              all(not archive.history for archive in self._archives.values()),
                              'restore requires an empty game; live evidence will not be replaced')
            state = _snapshot_copy(snapshot)
            try:
                decoded = self._decode_snapshot(state)
            except SnapshotError:
                raise
            except (KeyError, TypeError, ValueError, IndexError) as error:
                raise SnapshotError('malformed game snapshot') from error
            self._archives, self._submissions, self._visual_cache = decoded
            self._counters, self._events = state['counters'], state['events']
            if state['schema_version'] == 1:
                self._accounting_base = dict(counters=dict(self._counters), event_count=len(self._events), source_schema_version=1)
                self._accounting = []
            else:
                self._accounting_base, self._accounting = state['accounting_base'], state['accounting']

    def _decode_snapshot(self, state: dict) -> tuple[dict, dict, dict]:
        _require_snapshot(type(state.get('schema_version')) is int and state['schema_version'] in (1, 2), 'unsupported game snapshot version')
        expected = self.snapshot()
        required = set(expected) - ({'accounting', 'accounting_base'} if state['schema_version'] == 1 else set())
        _require_snapshot(set(state) == required, 'unexpected game snapshot fields')
        for name in ('mode', 'agent_id', 'lane', 'config', 'manifest_bindings'):
            _require_snapshot(_same_json(state[name], expected[name]), f'game binding mismatch: {name}')
        _require_snapshot(isinstance(state['archives'], dict) and set(state['archives']) == set(self._archives),
                          'archive contest set does not match the development allowlist')
        archives = {}
        for identifier, empty in self._archives.items():
            archives[identifier] = PixelArchive.from_snapshot(
                state['archives'][identifier], self.agent_id, identifier, empty.scene, empty.config, empty._embed,
                max_submissions=empty.max_submissions, same_joke_verifier=empty._verifier)
        submissions, counts_at_submission = {}, {}
        for identifier, archive in archives.items():
            count = 0
            for trace in archive.history:
                count += int(trace.status == 'new_pixel')
                counts_at_submission[(identifier, trace.caption)] = count
        _require_snapshot(isinstance(state['submissions'], list) and len(state['submissions']) == len(counts_at_submission),
                          'response cache is not closed over submission history')
        for entry in state['submissions']:
            _require_snapshot(isinstance(entry, dict) and set(entry) == {'contest_id', 'caption', 'result'}, 'invalid submission cache entry')
            identifier, caption, result = entry['contest_id'], entry['caption'], entry['result']
            _require_snapshot(isinstance(identifier, str) and identifier in archives and isinstance(caption, str),
                              'submission cache contains an unbound contest or caption')
            key = (identifier, caption)
            trace = archives[identifier].lookup(caption)
            _require_snapshot(key not in submissions and trace is not None and isinstance(result, dict), 'duplicate or orphaned cached submission')
            _require_snapshot(len(caption.split()) <= self.config.caption_word_limit, 'cached caption exceeds configured word cap')
            scene_fit = result.get('scene_fit')
            if trace.q is None:
                _require_snapshot(scene_fit is None and not trace.accepted, 'unscored rejection claims a scene decision')
                reason = 'injection_detected'
            else:
                _require_snapshot(type(scene_fit) is bool and trace.accepted == (scene_fit and trace.q >= self.config.tau),
                                  'cached acceptance contradicts scene_fit AND q >= tau')
                reason = None if trace.accepted else 'scene_fit' if not scene_fit else 'below_tau'
            expected_result = dict(ok=True, contest_id=identifier, accepted=trace.accepted, q=trace.q, scene_fit=scene_fit,
                                   status=trace.status, pixel_id=trace.pixel_id, pixel_count=counts_at_submission[key],
                                   matching_caption=trace.matching_caption, nearest_similarity=trace.nearest_similarity,
                                   submission_id=trace.submission_id, replayed=False, rejection_reason=reason,
                                   scoring_status='provisional_development')
            _require_snapshot(_same_json(result, expected_result), 'cached response disagrees with its immutable trace')
            submissions[key] = result
        _require_snapshot(isinstance(state['visual_cache'], list), 'visual cache must be a list')
        cache = {}
        for entry in state['visual_cache']:
            _require_snapshot(isinstance(entry, dict) and set(entry) == {'contest_id', 'question', 'result'}, 'invalid visual cache entry')
            identifier, question = entry['contest_id'], entry['question']
            _require_snapshot(isinstance(identifier, str) and identifier in archives and
                              isinstance(question, str) and bool(question.strip()), 'unbound visual cache key')
            key = (identifier, question)
            _require_snapshot(key not in cache, 'duplicate visual cache key')
            cache[key] = VisualResult(**entry['result'])
        events = state['events']
        _require_snapshot(isinstance(events, list) and len(events) <= self._event_limit, 'invalid or oversized event history')
        seen_submissions, seen_visuals = set(), set()
        error_fields = {'ok', 'status', 'error', 'pause_required', 'remaining_budget'}
        visual_fields = {'ok', 'status', 'contest_id', 'observations', 'uncertainty', 'remaining_budget',
                         'question_tokens', 'response_tokens', 'cached'}
        pending_tool = None
        pending_faults = 0
        for event in events:
            _require_snapshot(isinstance(event, dict), 'event must be an object')
            if event.get('ok') is False:
                _require_snapshot(set(event) == error_fields and event['status'] == 'error' and
                                  type(event['pause_required']) is bool and type(event['remaining_budget']) is int and
                                  isinstance(event['error'], dict) and set(event['error']) == {'code', 'message'} and
                                  all(isinstance(value, str) for value in event['error'].values()), 'invalid error event')
                if event['error']['code'] == 'transport_exhausted':
                    _require_snapshot(pending_faults == self.config.transport_retries + 1, 'transport exhaustion lacks its bounded attempts')
                pending_tool, pending_faults = None, 0
            elif event.get('error') == 'transport_fault':
                _require_snapshot(set(event) == {'operation', 'error', 'attempt'} and
                                  event['operation'] in ('inspect_image', 'submit_caption') and
                                  type(event['attempt']) is int and 1 <= event['attempt'] <= self.config.transport_retries + 1,
                                  'invalid transport-fault event')
                _require_snapshot(pending_tool in (None, event['operation']) and event['attempt'] == pending_faults + 1,
                                  'transport fault attempts are not contiguous')
                pending_tool, pending_faults = event['operation'], event['attempt']
            elif event.get('operation') == 'submit_caption':
                _require_snapshot(set(event) == {'operation', 'caption', 'result'}, 'invalid submission event')
                result = event['result']
                key = (result['contest_id'], event['caption'])
                _require_snapshot(key not in seen_submissions and key in submissions and _same_json(result, submissions[key]),
                                  'submission event/response cache closure failed')
                _require_snapshot(pending_tool in (None, 'submit_caption') and pending_faults <= self.config.transport_retries,
                                  'submission succeeds after exhausted or foreign transport attempts')
                pending_tool, pending_faults = None, 0
                seen_submissions.add(key)
            elif event.get('operation') == 'inspect_image':
                _require_snapshot(set(event) == {'operation', 'question', 'result'}, 'invalid visual event')
                result = event['result']
                _require_snapshot(isinstance(result, dict) and set(result) == visual_fields and result['ok'] is True and
                                  result['status'] == 'ok' and type(result['cached']) is bool and
                                  type(result['remaining_budget']) is int, 'invalid visual response event')
                for name, cap in (('question_tokens', self.config.question_token_limit), ('response_tokens', self.config.visual_response_token_limit)):
                    _require_snapshot(type(result[name]) is int and 1 <= result[name] <= cap, 'visual event exceeds token bounds')
                key = (result['contest_id'], event['question'])
                _require_snapshot(key in cache and result['cached'] == (key in seen_visuals) and
                                  _same_json(asdict(cache[key]), dict(observations=result['observations'], uncertainty=result['uncertainty'])),
                                  'visual cache/observation/history closure failed')
                _require_snapshot(pending_tool in (None, 'inspect_image') and pending_faults <= self.config.transport_retries and
                                  (not result['cached'] or pending_faults == 0), 'visual response contradicts transport attempts')
                pending_tool, pending_faults = None, 0
                seen_visuals.add(key)
            else:
                raise SnapshotError('unknown event type')
        _require_snapshot(pending_tool is None, 'snapshot ends with an unfinished transport operation')
        _require_snapshot(seen_submissions == set(submissions) and seen_visuals == set(cache), 'orphaned cache entry or history event')
        self._validate_counters(state['counters'], events)
        _require_snapshot(type(state['remaining_visual_calls']) is int and
                          state['remaining_visual_calls'] == self.config.visual_call_limit - state['counters']['visual_calls'],
                          'remaining visual allowance does not match counters')
        if state['schema_version'] == 2:
            self._validate_accounting(state, submissions)
        return archives, submissions, cache

    def _validate_accounting(self, state: dict, submissions: dict) -> None:
        baseline, ledger = state['accounting_base'], state['accounting']
        _require_snapshot(isinstance(ledger, list) and len(ledger) <= self._event_limit, 'invalid accounting ledger')
        running = {name: 0 for name in self._counters}
        base_event_count = 0
        if baseline is not None:
            _require_snapshot(isinstance(baseline, dict) and set(baseline) == {'counters', 'event_count', 'source_schema_version'} and
                              type(baseline['source_schema_version']) is int and baseline['source_schema_version'] == 1 and
                              type(baseline['event_count']) is int and
                              0 <= baseline['event_count'] <= len(state['events']), 'invalid legacy accounting baseline')
            base_event_count = baseline['event_count']
            self._validate_counters(baseline['counters'], state['events'][:base_event_count])
            running = dict(baseline['counters'])
        event_responses = Counter(json.dumps(event.get('result', event), sort_keys=True) for event in state['events'][base_event_count:]
                                  if event.get('ok') is False or 'result' in event)
        seen_judged = set()
        seen_inspections = Counter()
        for row in ledger:
            _require_snapshot(isinstance(row, dict) and set(row) == {'tool', 'contest_id', 'input', 'counter_delta', 'result'}, 'invalid accounting row')
            delta, result = row['counter_delta'], row['result']
            _require_snapshot(isinstance(row['contest_id'], str) and row['contest_id'] in self._contests and
                              isinstance(row['input'], str) and bool(row['input'].strip()), 'unbound accounting row')
            _require_snapshot(isinstance(delta, dict) and set(delta) == set(running) and
                              all(type(value) is int and value >= 0 for value in delta.values()) and any(delta.values()), 'invalid accounting delta')
            response_key = json.dumps(result, sort_keys=True)
            _require_snapshot(event_responses[response_key] > 0, 'accounting response is absent from event history')
            event_responses[response_key] -= 1
            if row['tool'] == 'submit_caption':
                _require_snapshot(1 <= delta['judge_attempts'] <= self.config.transport_retries + 1 and
                                  all(value == 0 for name, value in delta.items() if name != 'judge_attempts'), 'invalid judge accounting delta')
                if result['ok']:
                    key = (row['contest_id'], row['input'])
                    _require_snapshot(key not in seen_judged and key in submissions and
                                      _same_json(result, submissions[key]) and result['q'] is not None, 'judge ledger is not closed over responses')
                    seen_judged.add(key)
            elif row['tool'] == 'inspect_image':
                _require_snapshot(delta['visual_calls'] == 1 and delta['judge_attempts'] == 0 and
                                  1 <= delta['question_tokens'] <= self.config.question_token_limit and
                                  0 <= delta['failed_visual_attempts'] <= delta['visual_transport_attempts'] <= self.config.transport_retries + 1,
                                  'invalid visual accounting delta')
                if result['ok']:
                    _require_snapshot(result['contest_id'] == row['contest_id'] and
                                      delta['question_tokens'] == result['question_tokens'] and
                                      delta['visual_context_tokens'] == result['response_tokens'] and
                                      delta['external_visual_tokens'] == (0 if result['cached'] else result['response_tokens']) and
                                      (delta['visual_transport_attempts'] == 0 if result['cached'] else delta['visual_transport_attempts'] >= 1) and
                                      (delta['failed_visual_attempts'] == 0 if result['cached'] else
                                       delta['failed_visual_attempts'] < delta['visual_transport_attempts']), 'visual success accounting contradicts response')
                    seen_inspections[(row['contest_id'], row['input'], response_key)] += 1
                else:
                    _require_snapshot(delta['visual_context_tokens'] == 0, 'failed visual call delivered context tokens')
            else:
                raise SnapshotError('unknown accounting tool')
            running = {name: value + delta[name] for name, value in running.items()}
            if 'remaining_budget' in result:
                _require_snapshot(result['remaining_budget'] == self.config.visual_call_limit - running['visual_calls'],
                                  'accounting row resets visual allowance')
        _require_snapshot(_same_json(running, state['counters']), 'accounting deltas do not sum to persisted counters')
        expected_judged = set()
        expected_inspections = Counter()
        for event in state['events'][base_event_count:]:
            if event.get('operation') == 'submit_caption' and 'result' in event and event['result']['q'] is not None:
                expected_judged.add((event['result']['contest_id'], event['caption']))
            elif event.get('operation') == 'inspect_image' and 'result' in event:
                expected_inspections[(event['result']['contest_id'], event['question'], json.dumps(event['result'], sort_keys=True))] += 1
        _require_snapshot(seen_judged == expected_judged and seen_inspections == expected_inspections, 'accounting is not closed over successful tool calls')

    def snapshot(self) -> dict:
        with self._lock:
            manifest = [dict(contest_id=contest.contest_id, canonical_scene=contest.canonical_scene,
                             image_binding_sha256=hashlib.sha256(contest.image.encode('utf-8')
                             if isinstance(contest.image, str) else contest.image).hexdigest())
                        for contest in self.manifest.contests]
            return dict(schema_version=2, mode='DEVELOPMENT', agent_id=self.agent_id, lane=self.lane,
                        config=asdict(self.config), manifest_bindings=manifest,
                        counters=dict(self._counters), remaining_visual_calls=self.remaining_visual_calls,
                        archives={identifier: archive.snapshot() for identifier, archive in self._archives.items()},
                        submissions=[dict(contest_id=identifier, caption=caption, result=deepcopy(result))
                                     for (identifier, caption), result in self._submissions.items()],
                        visual_cache=[dict(contest_id=identifier, question=question, result=asdict(result))
                                      for (identifier, question), result in self._visual_cache.items()],
                        accounting=deepcopy(self._accounting), accounting_base=deepcopy(self._accounting_base),
                        events=deepcopy(self._events))

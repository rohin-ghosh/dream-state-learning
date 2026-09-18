"""Bounded DEVELOPMENT idea archives and evaluator-only pair calibration."""

from __future__ import annotations

import argparse
from bisect import bisect_left
from dataclasses import asdict, dataclass, fields, replace
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
from threading import RLock
from typing import Callable, Mapping, Sequence


RESOLUTIONS = ('coarse', 'primary', 'fine')
Embed = Callable[[str], Sequence[float]]
SameJokeVerifier = Callable[[str, str, str], bool]


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name} must be nonempty text')


def _number(value: float, name: str, minimum: float, maximum: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{name} must be numeric')
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f'{name} must be finite and in [{minimum}, {maximum}]')


@dataclass(frozen=True)
class PixelConfig:
    embedding_model_id: str
    embedding_revision: str
    rho_coarse: float
    rho_primary: float
    rho_fine: float
    resolution: str = 'primary'
    input_format: str = 'scene_caption_v1'
    calibration_status: str = 'provisional'

    def __post_init__(self) -> None:
        _text(self.embedding_model_id, 'embedding_model_id')
        _text(self.embedding_revision, 'embedding_revision')
        for resolution in RESOLUTIONS:
            _number(getattr(self, f'rho_{resolution}'), f'rho_{resolution}', -1, 1)
        if not self.rho_coarse <= self.rho_primary <= self.rho_fine:
            raise ValueError('thresholds must satisfy coarse <= primary <= fine')
        if self.resolution not in RESOLUTIONS or self.input_format != 'scene_caption_v1':
            raise ValueError('unsupported resolution or embedding input format')
        if self.calibration_status not in ('provisional', 'development_human_labeled'):
            raise ValueError('Stage 1 supports development calibration status only')

    @property
    def rho(self) -> float:
        return getattr(self, f'rho_{self.resolution}')


def embedding_text(scene: str, caption: str) -> str:
    _text(scene, 'scene')
    _text(caption, 'caption')
    return json.dumps({'scene': scene, 'caption': caption}, ensure_ascii=False,
                      sort_keys=True, separators=(',', ':'))


def embedding_key(scene: str, caption: str) -> str:
    return hashlib.sha256(embedding_text(scene, caption).encode('utf-8')).hexdigest()


def normalized_vector(vector: Sequence[float]) -> tuple[float, ...]:
    if isinstance(vector, (str, bytes, Mapping)):
        raise ValueError('embedding must be a numeric vector')
    try:
        values = tuple(float(component) for component in vector)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError('embedding must be a numeric vector') from error
    if not values or not all(math.isfinite(component) for component in values):
        raise ValueError('embedding must be nonempty and finite')
    scale = max(abs(component) for component in values)
    if not scale:
        raise ValueError('embedding must have nonzero norm')
    scaled = tuple(component / scale for component in values)
    norm = math.sqrt(math.fsum(component * component for component in scaled))
    return tuple(component / norm for component in scaled)


def cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError('embedding dimensions changed')
    return max(-1.0, min(1.0, math.fsum(first * second
                                       for first, second in zip(left, right))))


@dataclass(frozen=True)
class SubmissionTrace:
    submission_id: str
    sequence: int
    caption: str
    accepted: bool
    q: float | None
    status: str
    pixel_id: str | None
    matching_caption: str | None
    nearest_pixel_id: str | None
    nearest_similarity: float | None
    similarities: tuple[tuple[str, float], ...]
    verifier_same_joke: bool | None
    vector: tuple[float, ...] | None
    created_at: str


@dataclass(frozen=True)
class Pixel:
    pixel_id: str
    representative_caption: str
    representative_vector: tuple[float, ...]
    discovered_sequence: int
    members: tuple[SubmissionTrace, ...]


class ArchiveFullError(RuntimeError):
    """A bounded archive cannot accept another unique submission."""


class SnapshotError(ValueError):
    """Persisted state is malformed, unbound, or not closed under its history."""


def _snapshot_copy(snapshot: Mapping) -> dict:
    if not isinstance(snapshot, Mapping):
        raise SnapshotError('snapshot must be a JSON object')
    try:
        return json.loads(json.dumps(dict(snapshot), sort_keys=True, allow_nan=False))
    except (TypeError, ValueError) as error:
        raise SnapshotError('snapshot must contain only finite JSON values') from error


def _same_json(left: object, right: object) -> bool:
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)


def _require_snapshot(condition: bool, message: str) -> None:
    if not condition:
        raise SnapshotError(message)


def _submission_identity(agent_id: str, contest_id: str, caption: str) -> str:
    identity = json.dumps([agent_id, contest_id, caption], ensure_ascii=False)
    return hashlib.sha256(identity.encode('utf-8')).hexdigest()


class PixelArchive:
    def __init__(self, agent_id: str, contest_id: str, scene: str,
                 config: PixelConfig, embed: Embed, *, max_submissions: int = 10000,
                 same_joke_verifier: SameJokeVerifier | None = None):
        for name, value in (('agent_id', agent_id), ('contest_id', contest_id), ('scene', scene)):
            _text(value, name)
        if type(max_submissions) is not int or not 1 <= max_submissions <= 10000:
            raise ValueError('max_submissions must be an integer from 1 to 10000')
        if not isinstance(config, PixelConfig) or not callable(embed):
            raise ValueError('PixelConfig and injected embedding callable are required')
        if same_joke_verifier is not None and not callable(same_joke_verifier):
            raise ValueError('same_joke_verifier must be callable')
        self.agent_id, self.contest_id, self.scene = agent_id, contest_id, scene
        self.config, self.max_submissions = config, max_submissions
        self._embed, self._verifier = embed, same_joke_verifier
        self._history: list[SubmissionTrace] = []
        self._by_caption: dict[str, SubmissionTrace] = {}
        self._pixels: list[Pixel] = []
        self._trace_policy = 'nearest_only_all_immutable_representatives_searched'
        self._lock = RLock()

    @property
    def history(self) -> tuple[SubmissionTrace, ...]:
        with self._lock:
            return tuple(self._history)

    @property
    def pixels(self) -> tuple[Pixel, ...]:
        with self._lock:
            return tuple(self._pixels)

    @property
    def pixel_count(self) -> int:
        with self._lock:
            return len(self._pixels)

    def lookup(self, caption: str) -> SubmissionTrace | None:
        with self._lock:
            return self._by_caption.get(caption)

    def submit(self, caption: str, *, accepted: bool, q: float | None) -> SubmissionTrace:
        _text(caption, 'caption')
        if type(accepted) is not bool:
            raise ValueError('accepted must be a bool')
        if q is not None:
            _number(q, 'q', 0, 1)
        elif accepted:
            raise ValueError('accepted captions require an actual q score')
        with self._lock:
            previous = self._by_caption.get(caption)
            if previous is not None:
                if previous.accepted != accepted or previous.q != q:
                    raise ValueError('conflicting exact submission; use a new archive for rescoring')
                return previous
            if len(self._history) >= self.max_submissions:
                raise ArchiveFullError('unique submission allowance exhausted')
            sequence = len(self._history) + 1
            vector = None
            nearest = None
            similarities: tuple[tuple[str, float], ...] = ()
            verifier_decision = None
            repeat = False
            nearest_similarity = None
            if accepted:
                vector = normalized_vector(self._embed(embedding_text(self.scene, caption)))
                similarities = tuple((pixel.pixel_id, cosine(vector, pixel.representative_vector))
                                     for pixel in self._pixels)
                if similarities:
                    nearest_index = max(range(len(similarities)), key=lambda index: similarities[index][1])
                    nearest = self._pixels[nearest_index]
                    nearest_similarity = similarities[nearest_index][1]
                    if self._trace_policy is not None:
                        similarities = ((nearest.pixel_id, nearest_similarity),)
                    repeat = nearest_similarity >= self.config.rho
                    if repeat and self._verifier is not None:
                        verifier_decision = self._verifier(self.scene, caption, nearest.representative_caption)
                        if type(verifier_decision) is not bool:
                            raise ValueError('same-joke verifier must return a bool')
                        repeat = verifier_decision
            pixel_id = None
            matching_caption = None
            status = 'rejected'
            if accepted:
                pixel_id = nearest.pixel_id if repeat else f'pixel-{len(self._pixels) + 1:06d}'
                matching_caption = nearest.representative_caption if repeat else None
                status = 'repeat' if repeat else 'new_pixel'
            trace = SubmissionTrace(
                _submission_identity(self.agent_id, self.contest_id, caption), sequence, caption,
                accepted, q, status, pixel_id, matching_caption,
                nearest.pixel_id if nearest else None, nearest_similarity, similarities,
                verifier_decision, vector, datetime.now(timezone.utc).isoformat())
            if accepted:
                if repeat:
                    self._pixels[nearest_index] = replace(nearest, members=nearest.members + (trace,))
                else:
                    self._pixels.append(Pixel(pixel_id, caption, vector, sequence, (trace,)))
            self._history.append(trace)
            self._by_caption[caption] = trace
            return trace

    @classmethod
    def from_snapshot(cls, snapshot: Mapping, agent_id: str, contest_id: str, scene: str,
                      config: PixelConfig, embed: Embed, *, max_submissions: int = 10000,
                      same_joke_verifier: SameJokeVerifier | None = None) -> PixelArchive:
        archive = cls(agent_id, contest_id, scene, config, embed, max_submissions=max_submissions,
                      same_joke_verifier=same_joke_verifier)
        archive.restore(snapshot)
        return archive

    def restore(self, snapshot: Mapping) -> None:
        with self._lock:
            _require_snapshot(not self._history and not self._pixels and not self._by_caption,
                              'restore requires an empty archive; live evidence will not be replaced')
            state = _snapshot_copy(snapshot)
            expected = self.snapshot()
            _require_snapshot(not (set(state) - set(expected)) and
                              not (set(expected) - set(state) - {'similarity_trace'}), 'unexpected archive snapshot fields')
            for name in ('schema_version', 'mode', 'agent_id', 'contest_id', 'scene', 'config',
                         'max_submissions', 'implementation'):
                _require_snapshot(_same_json(state.get(name), expected[name]), f'archive binding mismatch: {name}')
            if 'similarity_trace' in state:
                _require_snapshot(state['similarity_trace'] == expected['similarity_trace'], 'unknown similarity trace policy')
            _require_snapshot(isinstance(state['history'], list) and len(state['history']) <= self.max_submissions,
                              'archive history exceeds its bound or is not a list')
            _require_snapshot(isinstance(state['pixels'], list), 'archive pixels must be a list')
            history, pixels, by_caption = [], [], {}
            trace_fields = {field.name for field in fields(SubmissionTrace)}
            for sequence, raw in enumerate(state['history'], start=1):
                _require_snapshot(isinstance(raw, dict) and set(raw) == trace_fields, 'invalid submission trace fields')
                _require_snapshot(type(raw['sequence']) is int and raw['sequence'] == sequence, 'noncontiguous submission sequence')
                _require_snapshot(isinstance(raw['caption'], str) and bool(raw['caption'].strip()), 'invalid archived caption')
                _require_snapshot(raw['caption'] not in by_caption, 'duplicate exact caption in archive history')
                _require_snapshot(raw['submission_id'] == _submission_identity(self.agent_id, self.contest_id, raw['caption']),
                                  'submission identity does not bind agent, contest and exact caption')
                _require_snapshot(type(raw['accepted']) is bool, 'invalid archived acceptance flag')
                try:
                    if raw['q'] is not None:
                        _number(raw['q'], 'q', 0, 1)
                    recorded_at = datetime.fromisoformat(raw['created_at'])
                    _require_snapshot(recorded_at.tzinfo is not None, 'submission timestamp must have a timezone')
                except (TypeError, ValueError) as error:
                    raise SnapshotError('invalid archived score or timestamp') from error
                _require_snapshot(isinstance(raw['similarities'], list), 'invalid similarity trace')
                _require_snapshot(all(isinstance(pair, list) and len(pair) == 2 for pair in raw['similarities']),
                                  'invalid similarity trace entries')
                try:
                    if raw['nearest_similarity'] is not None:
                        _number(raw['nearest_similarity'], 'nearest similarity', -1, 1)
                    for identifier, similarity in raw['similarities']:
                        _require_snapshot(isinstance(identifier, str), 'invalid nearest-neighbor identity')
                        _number(similarity, 'stored similarity', -1, 1)
                except ValueError as error:
                    raise SnapshotError('invalid stored similarities') from error
                similarities = tuple(tuple(pair) for pair in raw['similarities'])
                vector = None
                nearest = None
                nearest_index = None
                nearest_similarity = None
                expected_similarities = ()
                repeat = False
                if raw['accepted']:
                    _require_snapshot(raw['q'] is not None, 'accepted trace lacks its actual score')
                    _require_snapshot(isinstance(raw['vector'], list) and bool(raw['vector']), 'accepted trace lacks its vector')
                    vector = tuple(raw['vector'])
                    try:
                        for component in vector:
                            _number(component, 'vector component', -1, 1)
                    except ValueError as error:
                        raise SnapshotError('invalid stored vector') from error
                    _require_snapshot(math.isclose(math.fsum(component * component for component in vector), 1,
                                                   rel_tol=1e-12, abs_tol=1e-12), 'stored vector is not normalized')
                    if pixels:
                        _require_snapshot(len(vector) == len(pixels[0].representative_vector), 'stored embedding dimensions changed')
                        all_similarities = tuple((pixel.pixel_id, cosine(vector, pixel.representative_vector)) for pixel in pixels)
                        nearest_index = max(range(len(all_similarities)), key=lambda index: all_similarities[index][1])
                        nearest = pixels[nearest_index]
                        nearest_similarity = all_similarities[nearest_index][1]
                        expected_similarities = ((nearest.pixel_id, nearest_similarity),)
                        if 'similarity_trace' not in state:
                            expected_similarities = all_similarities
                        repeat = nearest_similarity >= self.config.rho
                    if repeat and self._verifier is not None:
                        _require_snapshot(type(raw['verifier_same_joke']) is bool, 'required verifier decision is absent')
                        repeat = raw['verifier_same_joke']
                    else:
                        _require_snapshot(raw['verifier_same_joke'] is None, 'unexpected verifier decision')
                else:
                    _require_snapshot(raw['vector'] is None and raw['verifier_same_joke'] is None,
                                      'rejected caption cannot carry an accepted vector or verifier decision')
                expected_status = ('repeat' if repeat else 'new_pixel') if raw['accepted'] else 'rejected'
                expected_pixel_id = (nearest.pixel_id if repeat else f'pixel-{len(pixels) + 1:06d}') if raw['accepted'] else None
                _require_snapshot(raw['status'] == expected_status and raw['pixel_id'] == expected_pixel_id,
                                  'pixel assignment contradicts immutable-representative history')
                _require_snapshot(raw['matching_caption'] == (nearest.representative_caption if repeat else None),
                                  'matching caption is not the same archive representative')
                _require_snapshot(raw['nearest_pixel_id'] == (nearest.pixel_id if nearest else None) and
                                  raw['nearest_similarity'] == nearest_similarity and similarities == expected_similarities,
                                  'nearest-neighbor trace does not close over immutable representatives')
                trace = SubmissionTrace(**dict(raw, vector=vector, similarities=similarities))
                if raw['accepted']:
                    if repeat:
                        pixels[nearest_index] = replace(nearest, members=nearest.members + (trace,))
                    else:
                        pixels.append(Pixel(expected_pixel_id, trace.caption, vector, sequence, (trace,)))
                history.append(trace)
                by_caption[trace.caption] = trace
            _require_snapshot(_same_json(state['pixels'], [asdict(pixel) for pixel in pixels]),
                              'pixel representatives or membership do not close over history')
            self._history, self._pixels, self._by_caption = history, pixels, by_caption
            self._trace_policy = state.get('similarity_trace')

    def snapshot(self) -> dict:
        with self._lock:
            result = dict(schema_version=1, mode='DEVELOPMENT', agent_id=self.agent_id,
                        contest_id=self.contest_id, scene=self.scene, config=asdict(self.config),
                        max_submissions=self.max_submissions,
                        similarity_trace=self._trace_policy,
                        implementation='embedding_plus_verifier' if self._verifier else 'embedding_only',
                        history=[asdict(trace) for trace in self._history],
                        pixels=[asdict(pixel) for pixel in self._pixels])
            if self._trace_policy is None:
                result.pop('similarity_trace')
            return result


@dataclass(frozen=True)
class LabeledPair:
    pair_id: str
    contest_id: str
    scene: str
    caption_a: str
    caption_b: str
    labels: Mapping[str, bool | None]
    label_source: str = 'missing'
    group_id: str | None = None
    spotcheck_labels: Mapping[str, bool | None] | None = None
    labeler_id: str | None = None
    labeler_revision: str | None = None


def _metric_counts(true_positive: int, false_positive: int, true_negative: int,
                   false_negative: int, errors: list) -> dict:
    same_count, different_count = true_positive + false_negative, true_negative + false_positive
    false_merge_rate = false_positive / different_count if different_count else None
    false_split_rate = false_negative / same_count if same_count else None
    return dict(n=same_count + different_count, same_joke_count=same_count, different_joke_count=different_count,
                tp_same=true_positive, tn_different=true_negative, fp_merge=false_positive,
                fn_split=false_negative, false_merge_rate=false_merge_rate,
                false_split_rate=false_split_rate,
                balanced_error=(false_merge_rate + false_split_rate) / 2
                if same_count and different_count else None, errors=errors)


def _metrics(rows: list[tuple[LabeledPair, float]], resolution: str, rho: float) -> dict:
    labeled = [(pair, similarity) for pair, similarity in rows if pair.labels.get(resolution) is not None]
    true_positive = false_positive = true_negative = false_negative = 0
    errors = []
    for pair, similarity in labeled:
        actual, predicted = pair.labels[resolution], similarity >= rho
        true_positive += int(actual and predicted)
        false_positive += int(not actual and predicted)
        true_negative += int(not actual and not predicted)
        false_negative += int(actual and not predicted)
        if actual != predicted:
            errors.append(dict(pair_id=pair.pair_id, contest_id=pair.contest_id,
                               error='FPmerge' if predicted else 'FNsplit', similarity=similarity))
    return _metric_counts(true_positive, false_positive, true_negative, false_negative, errors)


def _threshold_table(rows: list[tuple[LabeledPair, float]], resolution: str, candidates: list[float]) -> list[dict]:
    same = sorted(similarity for pair, similarity in rows if pair.labels.get(resolution) is True)
    different = sorted(similarity for pair, similarity in rows if pair.labels.get(resolution) is False)
    table = []
    for rho in candidates:
        false_negative, true_negative = bisect_left(same, rho), bisect_left(different, rho)
        table.append(_metric_counts(len(same) - false_negative, len(different) - true_negative,
                                    true_negative, false_negative, []))
    return table


def calibrate_pairs(pairs: Sequence[LabeledPair], config: PixelConfig, embed: Embed, *,
                    heldout_fraction: float = 1 / 3, seed: int = 177) -> dict:
    _number(heldout_fraction, 'heldout_fraction', 0, 1)
    if not 0 < heldout_fraction < 1 or type(seed) is not int:
        raise ValueError('heldout fraction must be strictly between zero and one; seed must be an int')
    pairs = tuple(pairs)
    if len(pairs) > 10000:
        raise ValueError('calibration is bounded to 10000 pairs')
    identifiers = set()
    contest_groups = {}
    for pair in pairs:
        for name in ('pair_id', 'contest_id', 'scene', 'caption_a', 'caption_b'):
            _text(getattr(pair, name), name)
        if pair.pair_id in identifiers:
            raise ValueError('duplicate pair_id')
        identifiers.add(pair.pair_id)
        if pair.label_source not in ('human', 'synthetic', 'automatic', 'llm', 'missing'):
            raise ValueError('label_source must be human, synthetic, automatic, llm or missing')
        for labels in (pair.labels, pair.spotcheck_labels if pair.spotcheck_labels is not None else {}):
            if not isinstance(labels, Mapping) or set(labels) - set(RESOLUTIONS):
                raise ValueError('labels must be keyed by coarse, primary and fine')
            if any(value is not None and type(value) is not bool for value in labels.values()):
                raise ValueError('pair labels must be bool or null')
        group = pair.group_id or pair.contest_id
        _text(group, 'group_id')
        if pair.contest_id in contest_groups and contest_groups[pair.contest_id] != group:
            raise ValueError('one contest cannot straddle calibration and holdout groups')
        contest_groups[pair.contest_id] = group
    groups = sorted(set(contest_groups.values()))
    random.Random(seed).shuffle(groups)
    holdout_count = min(len(groups) - 1, max(1, round(len(groups) * heldout_fraction))) if len(groups) > 1 else 0
    heldout_groups = set(groups[:holdout_count])
    cache = {}
    dimension = None
    rows = []
    for pair in pairs:
        for caption in (pair.caption_a, pair.caption_b):
            text = embedding_text(pair.scene, caption)
            if text not in cache:
                vector = normalized_vector(embed(text))
                if dimension is not None and dimension != len(vector):
                    raise ValueError('embedding dimensions changed')
                dimension = len(vector)
                cache[text] = vector
        rows.append((pair, cosine(cache[embedding_text(pair.scene, pair.caption_a)],
                                  cache[embedding_text(pair.scene, pair.caption_b)])))
    training = [row for row in rows if contest_groups[row[0].contest_id] not in heldout_groups]
    heldout = [row for row in rows if contest_groups[row[0].contest_id] in heldout_groups]
    human_count = sum((pair.label_source == 'human' and any(value is not None for value in pair.labels.values()))
                      or any(value is not None for value in (pair.spotcheck_labels or {}).values()) for pair in pairs)
    spotcheck_count = sum(any(value is not None for value in (pair.spotcheck_labels or {}).values()) for pair in pairs)
    source_counts = {source: sum(pair.label_source == source for pair in pairs)
                     for source in ('human', 'llm', 'automatic', 'synthetic', 'missing')}
    has_nonsynthetic = any(pair.label_source in ('human', 'llm', 'automatic') for pair in pairs)

    def effective_labels(original: list[tuple[LabeledPair, float]]) -> list[tuple[LabeledPair, float]]:
        effective = []
        for pair, similarity in original:
            labels = dict(pair.labels) if pair.label_source != 'missing' else {}
            if has_nonsynthetic and pair.label_source == 'synthetic':
                labels = {}
            labels.update({name: value for name, value in (pair.spotcheck_labels or {}).items() if value is not None})
            effective.append((replace(pair, labels=labels), similarity))
        return effective

    if human_count:
        selection_source = 'human_and_automatic' if source_counts['llm'] or source_counts['automatic'] else 'human'
    else:
        selection_source = 'automatic_only' if has_nonsynthetic else 'nonhuman_diagnostic'
    training_labels = effective_labels(training)
    heldout_labels = effective_labels(heldout)
    similarities = sorted(set(similarity for pair, similarity in training_labels
                              if any(value is not None for value in pair.labels.values())))
    candidates = sorted(set([-1.0, 1.0] + similarities +
                            [(left + right) / 2 for left, right in zip(similarities, similarities[1:])]))
    tables = {resolution: _threshold_table(training_labels, resolution, candidates) for resolution in RESOLUTIONS}
    available = [resolution for resolution in RESOLUTIONS
                 if tables[resolution][0]['balanced_error'] is not None]
    selected = {resolution: None for resolution in RESOLUTIONS}

    def cost(resolution: str, index: int) -> tuple:
        metrics = tables[resolution][index]
        return metrics['balanced_error'], metrics['false_merge_rate'], metrics['false_split_rate'], -candidates[index]

    if len(available) == 3:
        coarse_best = []
        best = 0
        for index in range(len(candidates)):
            if cost('coarse', index) < cost('coarse', best):
                best = index
            coarse_best.append(best)
        fine_best = [0] * len(candidates)
        best = len(candidates) - 1
        for index in reversed(range(len(candidates))):
            if cost('fine', index) < cost('fine', best):
                best = index
            fine_best[index] = best

        def joint_cost(primary: int) -> tuple:
            indices = (coarse_best[primary], primary, fine_best[primary])
            costs = [cost(resolution, index) for resolution, index in zip(RESOLUTIONS, indices)]
            return tuple(sum(item[column] for item in costs) for column in range(3)) + tuple(-candidates[index] for index in indices)

        primary = min(range(len(candidates)), key=joint_cost)
        for resolution, index in zip(RESOLUTIONS, (coarse_best[primary], primary, fine_best[primary])):
            selected[resolution] = candidates[index]
    else:
        for resolution in available:
            selected[resolution] = candidates[min(range(len(candidates)), key=lambda index: cost(resolution, index))]
    warnings = []
    if len(pairs) < 300:
        warnings.append('fewer_than_approximately_300_pairs')
    if not human_count:
        warnings.append('missing_human_labels')
    elif human_count < len(pairs):
        warnings.append('incomplete_human_labels')
    if not heldout:
        warnings.append('insufficient_independent_groups_for_holdout')
    if len(available) < 3:
        warnings.append('missing_both_training_label_classes_at_some_resolutions')
    resolution_reports = {}
    for resolution, rho in selected.items():
        if rho is None:
            resolution_reports[resolution] = dict(rho=None, training=None, heldout=None)
        else:
            checked = _metrics(heldout_labels, resolution, rho)
            resolution_reports[resolution] = dict(rho=rho, training=_metrics(training_labels, resolution, rho),
                                                   heldout=checked,
                                                   heldout_human_spotcheck=_metrics(
                                                       [(replace(pair, labels=pair.labels if pair.label_source == 'human'
                                                                 else pair.spotcheck_labels or {}), similarity)
                                                        for pair, similarity in heldout], resolution, rho))
            if checked['balanced_error'] is None:
                warnings.append(f'{resolution}_holdout_missing_both_label_classes')
    result_config = None
    if len(available) == 3:
        result_config = asdict(replace(config, rho_coarse=selected['coarse'], rho_primary=selected['primary'],
                                       rho_fine=selected['fine'], calibration_status='provisional'))
    return dict(schema_version=1, mode='DEVELOPMENT', validation_status='provisional',
                validated_scoring=False, pair_count=len(pairs), human_labeled_pair_count=human_count,
                human_spotchecked_pair_count=spotcheck_count, label_source_counts=source_counts,
                stage1_human_panel_required=False,
                labeler_provenance=[dict(pair_id=pair.pair_id, label_source=pair.label_source,
                                        labeler_id=pair.labeler_id, labeler_revision=pair.labeler_revision)
                                   for pair in pairs],
                label_selection_source=selection_source, seed=seed, heldout_fraction=heldout_fraction,
                split_unit='contest_or_declared_scene_group',
                training_pair_ids=[pair.pair_id for pair, similarity in training],
                heldout_pair_ids=[pair.pair_id for pair, similarity in heldout],
                heldout_group_ids=sorted(heldout_groups),
                selection_objective='minimum summed balanced FPmerge/FNsplit error with coarse <= primary <= fine',
                selection_uses='training pair labels only; no heldout labels, arm outcomes or top-N distances',
                resolutions=resolution_reports, pixel_config=result_config, warnings=warnings,
                encoder=dict(embedding_model_id=config.embedding_model_id, embedding_revision=config.embedding_revision,
                             input_format=config.input_format, frozen_pretrained_required=True,
                             model_execution_verified=False),
                limitations=['Pair errors are not archive coverage corrections.',
                             'Retrieval misses and sequential order sensitivity require separate archive audits.',
                             'No human acceptance validation or scientific outcome is established here.'])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    calibrate = commands.add_parser('calibrate', help='CPU-only labeled pairs plus precomputed frozen vectors')
    calibrate.add_argument('--pairs', type=Path, required=True)
    calibrate.add_argument('--vectors', type=Path, required=True)
    calibrate.add_argument('--config', type=Path, required=True)
    calibrate.add_argument('--output-dir', type=Path, required=True)
    calibrate.add_argument('--heldout-fraction', type=float, default=1 / 3)
    calibrate.add_argument('--seed', type=int, default=177)
    args = parser.parse_args(argv)
    try:
        config = PixelConfig(**json.loads(args.config.read_text()))
        payload = json.loads(args.pairs.read_text())
        pairs = [LabeledPair(**row) for row in (payload['pairs'] if isinstance(payload, dict) else payload)]
        vector_payload = json.loads(args.vectors.read_text())
        for field in ('embedding_model_id', 'embedding_revision', 'input_format'):
            if vector_payload[field] != getattr(config, field):
                raise ValueError(f'vector provenance mismatch: {field}')
        if vector_payload.get('source_kind') not in ('frozen_pretrained', 'synthetic_fixture'):
            raise ValueError('vectors require declared frozen_pretrained or synthetic_fixture source_kind')
        if vector_payload['source_kind'] == 'synthetic_fixture' and any(
                pair.label_source == 'human' or any(value is not None for value in (pair.spotcheck_labels or {}).values())
                for pair in pairs):
            raise ValueError('synthetic vectors cannot be presented as human embedding validation')

        def embed(text: str) -> Sequence[float]:
            key = hashlib.sha256(text.encode('utf-8')).hexdigest()
            return vector_payload['vectors'][key]

        report = calibrate_pairs(pairs, config, embed, heldout_fraction=args.heldout_fraction, seed=args.seed)
        report['encoder']['source_kind'] = vector_payload['source_kind']
        report['implementation_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        report['input_sha256'] = {name: hashlib.sha256(path.read_bytes()).hexdigest()
                                  for name, path in (('pairs', args.pairs), ('vectors', args.vectors), ('config', args.config))}
        artifacts = {'pixel_calibration_report.json': report}
        if report['pixel_config'] is not None:
            artifacts['pixel_config.json'] = report['pixel_config']
        if args.output_dir.exists():
            raise ValueError('output-dir must be new; existing artifacts are never overwritten')
        args.output_dir.mkdir(parents=True, exist_ok=False)
        for filename, content in artifacts.items():
            with (args.output_dir / filename).open('x') as stream:
                json.dump(content, stream, indent=2, sort_keys=True, allow_nan=False)
                stream.write('\n')
        print(json.dumps(dict(output_dir=str(args.output_dir), validation_status='provisional',
                              warnings=report['warnings']), sort_keys=True))
        return 0
    except (OSError, KeyError, TypeError, ValueError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    raise SystemExit(main())

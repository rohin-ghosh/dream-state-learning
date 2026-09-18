"""One-life local caption judge, with private panels outside the learner source."""

import argparse
import json
import os
from pathlib import Path
import socketserver
import tempfile
import time

from gpu import ny_caption_data as data
from gpu.ny_caption_action_policy import CaptionActionPolicy
from gpu.ny_caption_game import DevelopmentManifest
from gpu.ny_caption_life import HELP, LIMIT, POLICY, FORMAT_POLICY, child_act, extract_batches, latest_own_think
from gpu.ny_caption_pixels import PixelConfig
from gpu.ny_caption_relative_game import build_game, prepare_references
from gpu.ny_caption_scalar_judge import ScalarJudge
from gpu.orch_r125_stream_journal import _decode
from gpu.orch_r189_outcome_allocation import SCHEMA as OUTCOME_POLICY, validate_tokens


DEFAULT_TOP_K = 50


def save_state(path, state):
    path = Path(path)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.session-', delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data.canonical(state))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def scoring_rule(top_k):
    data.require(type(top_k) is int and 1 <= top_k <= 65, 'rank_bar_between_one_and_65')
    return (f'Provisional acceptance: rank <= {top_k} of 65 (your caption plus 64 human captions), '
            'AND weak scene relevance AND new-pixel novelty. Every rank is retained for later analysis.')


class LifeSession:
    def __init__(self, game, life_root, output, scene_ids, *, resume_state=None,
                 source_mode='NATIVE_JOURNAL', session_binding=None):
        self.game, self.life_root, self.output = game, Path(life_root).resolve(), Path(output).resolve()
        self.scene_ids = scene_ids
        self.source_mode, self.session_binding = source_mode, session_binding
        self.policy = CaptionActionPolicy(game, outcome_policy=OUTCOME_POLICY)
        self.seen = set()
        if resume_state is not None:
            data.require(resume_state['schema'] == 'R223_CAPTION_SESSION_STATE_V1'
                and resume_state['life_root'] == str(self.life_root)
                and resume_state['scene_ids'] == scene_ids
                and resume_state.get('source_mode', 'NATIVE_JOURNAL') == source_mode
                and resume_state.get('session_binding') == session_binding
                and resume_state['phase'] == 'COMPLETE', 'same_complete_session_resume')
            game.restore(resume_state['game'])
            self.policy = CaptionActionPolicy(game, state=resume_state['policy'], outcome_policy=OUTCOME_POLICY)
            self.seen = set(resume_state['seen'])

    def snapshot(self, phase='COMPLETE'):
        return dict(schema='R223_CAPTION_SESSION_STATE_V1', life_root=str(self.life_root),
            scene_ids=self.scene_ids, phase=phase, game=self.game.snapshot(), policy=self.policy.snapshot(),
            seen=sorted(self.seen), format_policy=FORMAT_POLICY,
            source_mode=self.source_mode, session_binding=self.session_binding)

    def process(self, request):
        data.require(type(request) is dict and set(request) == {'origin', 'metrics'}, 'exact_local_request')
        validate_tokens(request['metrics'])
        origin = request['origin']
        raw = child_act(self.life_root, origin)
        return self.process_verified(request, raw, identifier=origin['record_sha256'],
            think_resolver=lambda: latest_own_think(self.life_root, origin))

    def process_verified(self, request, raw, *, identifier, think_resolver=None, active_scene=None):
        """Internal callback ONLY after source validation, never a raw-text wire endpoint."""
        validate_tokens(request['metrics'])
        data.require(isinstance(identifier, str) and len(identifier) == 64
            and all(character in '0123456789abcdef' for character in identifier), 'bounded_source_identifier')
        origin = request['origin']
        data.require(identifier not in self.seen, 'duplicate_ACT_no_automatic_resubmit')
        target = self.output / 'attempts' / identifier
        target.mkdir(parents=True, mode=0o700, exist_ok=False)
        self.seen.add(identifier)
        data.private_write(target / 'REQUEST.json', dict(request=request, raw_act=raw, unix=time.time()))
        data.private_write(target / 'BEFORE.json', dict(game=self.game.snapshot(), policy=self.policy.snapshot()))
        save_state(self.output / 'SESSION_STATE.private.json', self.snapshot('PENDING'))
        actions, caption_sources, source_groups, salvaged = [], [], [], None
        try:
            actions, format_metrics = extract_batches(raw, self.scene_ids, active_scene=active_scene)
            caption_sources = [dict(item, stage='ACT', origin=origin) for item in format_metrics['caption_sources']]
            source_groups = [[item for item in caption_sources if item['contest_id'] == action['contest_id']]
                             for action in actions]
        except ValueError as error:
            format_metrics = dict(format_fault=True, clarification_needed=True,
                                  unscored_reason=str(error), recovered_count=0, unparsed_lines=[])
        if format_metrics['clarification_needed']:
            try:
                salvaged = think_resolver() if think_resolver else None
                if salvaged:
                    recovered, salvage_metrics = extract_batches(salvaged['raw'], self.scene_ids,
                        explicit_candidates_only=True, active_scene=active_scene)
                    existing = {(action['contest_id'], caption) for action in actions for caption in action['captions']}
                    for action in recovered:
                        kept, kept_sources = [], []
                        for ordinal, caption in enumerate(action['captions'], 1):
                            if (action['contest_id'], caption) in existing:
                                continue
                            source = next(item for item in salvage_metrics['caption_sources']
                                if item['contest_id'] == action['contest_id'] and item['caption_ordinal'] == ordinal)
                            kept.append(caption)
                            kept_sources.append(dict(source, stage='THINK', origin=salvaged['origin'],
                                source_sha256=salvaged['source_sha256'], actual_trigger_ACT=origin))
                            existing.add((action['contest_id'], caption))
                        if kept:
                            actions.append(dict(action, captions=kept, count=len(kept)))
                            caption_sources.extend(kept_sources)
                            source_groups.append(kept_sources)
                    format_metrics['salvaged_THINK_count'] = sum(item['stage']=='THINK' for item in caption_sources)
            except (ValueError, OSError, KeyError) as error:
                format_metrics['THINK_salvage_unavailable'] = type(error).__name__
        feedback, batch_reports = [], []
        for position, action in enumerate(actions):
            offset = 0
            while offset < action['count']:
                previous = self.policy.previous.get(action['contest_id'])
                maximum = min(100, 2 * previous['count']) if previous else 10
                captions = action['captions'][offset:offset + maximum]
                metrics = request['metrics'] if not batch_reports else {key:0 for key in request['metrics']}
                batch_report = self.policy.submit(dict(action, captions=captions, count=len(captions)),
                                                  cycle_metrics=metrics)
                batch_report['extracted_caption_start'] = offset + 1
                batch_report['extracted_caption_end'] = offset + len(captions)
                batch_reports.append(batch_report)
                feedback.extend(dict(item, contest_id=action['contest_id'],
                    caption_source_index=caption_sources.index(source_groups[position][offset + item['ordinal']-1]))
                    for item in batch_report.get('feedback', []))
                offset += len(captions)
                if not batch_report['ok']:
                    break
            if batch_reports and not batch_reports[-1]['ok']:
                break
        clarification = format_metrics['clarification_needed'] or any(not item['ok'] for item in batch_reports)
        report = dict(ok=bool(actions) and all(item['ok'] for item in batch_reports), feedback=feedback,
            requested_count=sum(action['count'] for action in actions),
            batch_reports=[{key:value for key,value in item.items() if key not in ('feedback', 'outcome_allocation')}
                           for item in batch_reports],
            dispatch_policy='R224_ALL_EXTRACTED_CAPTIONS_LEGACY_SAFE_CHUNKS_V1',
            not_dispatched_count=sum(action['count'] for action in actions) - len(feedback),
            caption_sources=caption_sources, help=HELP, format_policy=FORMAT_POLICY,
            next_stage='ACT' if clarification else 'THINK',
            instruction=('Please clarify the unparsed lines or their scene names/numbers in your next input; '
                         'no fixed format or count is required. Already-scored captions retain their actual results.'
                         if clarification else 'Use the actual ranks, acceptance and novelty feedback.'))
        if not actions:
            report['error'] = format_metrics['unscored_reason']
        if format_metrics.get('no_caption_act'):
            report['instruction'] = ('No caption found in your output—write the captions themselves, '
                'one per line, for the scene you choose. One per line is a suggestion, not a required '
                'format. Any actual recovered THINK captions keep their separately attributed results.')
        format_metrics.pop('caption_sources', None)
        report['format_metrics'] = format_metrics
        document = dict(policy=POLICY, origin=origin, raw_act=raw, action=actions[0] if len(actions)==1 else None,
                        actions=actions, salvaged_THINK=salvaged, report=report, internal_batch_reports=batch_reports,
                        child_training_target=False, unix=time.time(), no_tau_gate=True)
        if self.source_mode == 'STANDALONE_GENERATION':
            document.update(condition=self.session_binding['controller']['plan']['condition'],
                rule_sha256=self.session_binding['controller']['plan']['rule_sha256'])
        data.private_write(target / 'RESULT.json', document)
        data.private_write(target / 'AFTER.json', dict(game=self.game.snapshot(), policy=self.policy.snapshot()))
        save_state(self.output / 'SESSION_STATE.private.json', self.snapshot())
        reference = data.file_ref(target / 'RESULT.json')
        return dict(policy=POLICY, origin=origin, report=report, receipt_sha256=reference['sha256'])


def restoration_evidence(session, resume_reference):
    return dict(resume_state_input=resume_reference,
        resume_state_input_sha256=resume_reference['sha256'] if resume_reference else None,
        resumed_complete_state=resume_reference is not None,
        restored_seen_count=len(session.seen),
        restored_game_snapshot_sha256=data.digest(session.game.snapshot()),
        restored_policy_snapshot_sha256=data.digest(session.policy.snapshot()),
        private_caption_payload_included=False)


def load_session(args, *, session_class=LifeSession, source_mode='NATIVE_JOURNAL', session_binding=None):
    from gpu.ny_caption_similarity import FrozenCPUEncoder
    scoring = scoring_rule(args.top_k)
    output = Path(args.output).resolve()
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    manifest_ref = data.file_ref(Path(args.game_manifest).resolve())
    manifest = DevelopmentManifest.from_mapping(data.bound(manifest_ref))
    scalar = ScalarJudge(args.judge_config, batch_size=8)
    panels, private = prepare_references(data.file_ref(Path(args.data_manifest).resolve()), manifest,
        scalar, data.bound(data.file_ref(Path(args.image_map).resolve())), panel_size=64, seed=207)
    data.private_write(output / 'REFERENCE_PANELS.private.json', private)
    encoder_ref = data.file_ref(Path(args.encoder_manifest).resolve())
    encoder = FrozenCPUEncoder(encoder_ref, threads=2)
    pixels = PixelConfig(**json.loads(Path(args.pixel_config).read_text()))
    relevance = data.bound(data.file_ref(Path(args.relevance_config).resolve()))
    data.require(relevance['policy'] == 'R209_MINILM_SCENE_CAPTION_COSINE_V1'
                 and relevance['encoder']['sha256'] == encoder_ref['sha256'], 'same_measured_relevance_gate')
    game = build_game(manifest, scalar, panels, pixels, encoder, top_k=args.top_k,
                      agent_id=args.agent_id, lane='R210_LIVE_DEVELOPMENT',
                      relevance_threshold=relevance['threshold'])
    scenes = [dict(number=index, scene=contest.canonical_scene)
              for index, contest in enumerate(manifest.contests, 1)]
    data.private_write(output / 'CHILD_ENVIRONMENT.json', dict(policy=POLICY, scenes=scenes, help=HELP,
        scoring=scoring))
    resume, resume_reference = None, None
    if getattr(args, 'resume_state', None):
        data.require(getattr(args, 'resume_state_sha256', None), 'bound_resume_state_sha256_required')
        resume_reference = dict(path=str(Path(args.resume_state).resolve()), sha256=args.resume_state_sha256)
        resume = data.bound(resume_reference)
    descriptors = [dict(contest_id=contest.contest_id, canonical_scene=contest.canonical_scene) for contest in manifest.contests]
    session = session_class(game, args.life_root, output, descriptors, resume_state=resume,
        source_mode=source_mode, session_binding=session_binding)
    data.private_write(output / 'LOADED.json', dict(policy=POLICY, pid=os.getpid(), unix=time.time(),
        life_root=str(session.life_root), game_manifest=manifest_ref, scalar=scalar.reference,
        source=data.file_ref(Path(__file__).resolve()), panel_size=64, top_k=args.top_k, tau=None,
        service_kind='CAPTION_SCORER_NOT_LEARNER', source_mode=source_mode,
        FINAL_read=False, locked_validation_read=False, parent_private_panel_access=False,
        **restoration_evidence(session, resume_reference)))
    return session


def serve(session, socket_path, seconds):
    path = Path(socket_path)
    data.require(not path.exists() and path.is_absolute(), 'new_absolute_local_socket')

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(125)
            raw = self.rfile.readline(LIMIT + 1)
            data.require(raw.endswith(b'\n') and len(raw) <= LIMIT, 'bounded_request_line')
            request = _decode(raw)
            try:
                result = session.process(request)
            except Exception as error:
                result = dict(policy=POLICY, origin=request.get('origin'), report=dict(ok=False,
                    error='REQUEST_FAILED_NO_RETRY', error_type=type(error).__name__, feedback=[]))
            encoded = data.canonical(result) + b'\n'
            data.require(len(encoded) <= LIMIT, 'bounded_feedback')
            self.wfile.write(encoded)

    with socketserver.UnixStreamServer(str(path), Handler) as server:
        os.chmod(path, 0o600)
        server.timeout = 1
        data.private_write(session.output / 'LISTENING.json', dict(socket=str(path), pid=os.getpid(),
            unix=time.time(), deadline_unix=time.time() + seconds))
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            server.handle_request()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('game-manifest', 'data-manifest', 'image-map', 'judge-config', 'encoder-manifest',
                 'pixel-config', 'relevance-config', 'life-root', 'agent-id', 'output', 'socket'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--seconds', type=int, default=5400)
    parser.add_argument('--top-k', type=int, default=DEFAULT_TOP_K)
    parser.add_argument('--resume-state')
    parser.add_argument('--resume-state-sha256')
    args = parser.parse_args()
    data.require(0 < args.seconds <= 21600, 'bounded_service_lifetime')
    serve(load_session(args), args.socket, args.seconds)


if __name__ == '__main__':
    main()

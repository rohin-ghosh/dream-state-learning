"""Read pinned local evidence and report the unresolved legacy drain boundary."""

import argparse
import ast
import hashlib
import json
from pathlib import Path


WORKER = Path('research_loop/workers/post_reboot_node3_parents_20260919')
CUT = WORKER / 'INTEGRATION_CUT_1789785379507492424.json'
CUT_SHA256 = '639a423c18551e44c5feba769693a116aadf666104f7493d0e61503a5189be08'
SEALED = WORKER / 'transactional_ingress/MANIFEST.json'
SEALED_SHA256 = 'e00ed71d18f9dfd4cb7e41f020927fe4e292a5fa529ea885ca5968df82b762dc'
BRIDGE = 'research_loop/workers/rohin233_ovx4_recovery_20260918/lease_bridge.py'
PROXY = 'research_loop/workers/rohin233_ovx4_recovery_20260918/transport_proxy.py'
SCORER = 'research_loop/workers/rohin221_continuous_caption_20260918/shared_scorer.py'
SOURCE_PINS = {
    BRIDGE: '84d5016b2ce0d254bb4d2d55a574f56ed8c58c3c36459d24124189052ed0e3ab',
    PROXY: '115e611cc386d0709d9eab685a1b7201abb116d5a3afd1aa588c4cd44d10dedd',
    SCORER: '9d9702c494ead1f4fb04ac94a39f2167551d0ceebccc69abd89e26341cb87a36',
}


def pinned(path, expected):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('source_or_artifact_changed_no_reuse_of_prior_reasoning:' + str(path))
    return raw


def source_evidence(repo):
    result = {}
    for relative, expected in SOURCE_PINS.items():
        raw = pinned(repo / relative, expected)
        tree = ast.parse(raw)
        methods = [{'name': node.name, 'line': node.lineno, 'end_line': node.end_lineno}
            for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef))]
        result[relative] = dict(sha256=expected, definitions=methods)
    return result


def analyze(repo):
    sources = source_evidence(repo)
    cut = json.loads(pinned(repo / CUT, CUT_SHA256))
    seal = json.loads(pinned(repo / SEALED, SEALED_SHA256))
    for name, expected in seal['files'].items():
        pinned(repo / SEALED.parent / name, expected)
    routes = [dict(endpoint=row['endpoint']['path'], routing_file=row['target_reference']['path'],
        routing_file_sha256_at_old_cut=row['target_reference']['sha256'], target=row['target']['path'],
        endpoint_is_not_queue_proof=True) for row in cut['scorer']['routes']]
    return dict(schema='R233_SOURCE_ONLY_INGRESS_FENCE_ASSESSMENT_V1',
        decision='BLOCKED_NO_LEGACY_FENCE_ACK_OR_PERMITTED_DRAIN_PROOF', ready=False,
        assessment_type='OFFLINE_SOURCE_SUPPORTED_BEHAVIOR_NOT_FRESH_LIVE_STATE',
        source_evidence=sources, sealed_candidate_sha256=SEALED_SHA256,
        evidence_cut=dict(path=str(CUT), sha256=CUT_SHA256, unix=cut['unix'],
            admission_closed=cut['scorer']['admission_closed'],
            kernel_backlog_observed=cut['scorer']['kernel_backlog_observed'],
            explicitly_not_a_fresh_drain=True),
        recorded_retained_routes=routes,
        supported_route_control=dict(kind='EXISTING_BRIDGE_TARGET_JSON_READ_PER_HANDLER',
            source=BRIDGE, read_line=57, connect_line=60,
            changes_only='Handlers whose TARGET read occurs after an owner replacement select the replacement.',
            not_an_admission_fence=True, not_a_drain_ack=True,
            already_captured_target_not_revoked=True,
            all_five_source_aliases_and_direct_native_base_routes_still_require_accounting=True),
        rejected_shortcuts=[
            dict(proposal='Replace TARGET.json then wait 108/110/115 seconds',
                reason='Handler retains target before connect; max(.1, stop-now) still permits connect/send after stop.'),
            dict(proposal='Remove TARGET.json to revoke old handlers',
                reason='Only readers that have not captured a target wait; captured targets and upstream calls survive.'),
            dict(proposal='Edit running VM proxy config',
                reason='Config is loaded once in main; no per-request reload or administrative close exists.'),
            dict(proposal='Point bridge TARGET directly at sealed transactional relay native socket',
                reason='Bridge forwards trusted session/request/records envelope; relay native ingress requires origin/metrics.'),
            dict(proposal='Five source alias switches prove old route closed',
                reason='Retained private socket paths, accepted frames and established SSH channels are not revoked.'),
            dict(proposal='Quiet sessions, stable COMPLETE or 52/26 logged origins prove drain',
                reason='Old proxy logs only after outcome; unlogged accepted or queued work remains unenumerated.'),
            dict(proposal='Client disconnect proves callback finished',
                reason='Original synchronous scorer retains accepted socket through callback and response write.'),
            dict(proposal='CPU bridge exit alone proves original scorer quiescent',
                reason='An upstream scorer callback can outlive the bridge connection; no callback completion acknowledgment follows from process exit.'),
        ],
        precise_blocker=dict(
            missing_in_live_source='No acknowledged fence generation/admission ledger covering every old handler and queue.',
            missing_permitted_evidence='No permitted complete observation of retained accepted/queued/SSH lifetimes.',
            consequence='Cannot exclude a handler that captured the old target and can still dispatch or a live scorer callback.',
            no_finite_quiet_interval_suffices=True,
            platform_denied_kernel_information_will_not_be_retrieved_by_other_tools=True,
            no_alternative_procfs_netlink_socket_or_packet_probe=True),
        owner_decision='KEEP_CONTINUATION_BLOCKED; no executable live mutation plan is justified by this evidence.',
        necessary_release_condition='An independently authorized evidence or lifecycle-control capability that actually closes the unobserved legacy work; not a new assertion of zero.',
        live_observations=[], live_actions=[], executable_live_actions=[],
        scorer_restarts=[], native_signals=[], aliases_changed=[], historical_replay=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[4])
    args = parser.parse_args()
    try:
        result = analyze(args.repo.resolve())
    except (OSError, KeyError, ValueError) as error:
        result = dict(ready=False, decision='BLOCKED_SOURCE_OR_EVIDENCE_MISMATCH', reason=str(error),
            live_actions=[], executable_live_actions=[])
    print(json.dumps(result, sort_keys=True, indent=2))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())

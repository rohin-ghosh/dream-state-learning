"""Adapter for the original serialized Hub and existing NativeEpoch sessions."""

from copy import deepcopy
import threading
import time

from .contract import WIRE_SCHEMA, canonical, digest, require, validate_binding, validate_receipt


def envelope(binding, request, token):
    return dict(schema=WIRE_SCHEMA, session_id=binding['session_id'], transport_epoch=binding['transport_epoch'],
        request=request, attestation_sha256=token)


class ProjectedHub:
    def __init__(self, original, store, bindings):
        self.original, self.store, self.bindings = original, store, deepcopy(bindings)
        self.root, self.sessions, self.registry = original.root, original.sessions, original.registry
        self.lock = threading.RLock()
        for identifier, binding in self.bindings.items():
            validate_binding(binding)
            require(identifier == binding['session_id'] and identifier in self.sessions, 'existing_registered_session')
            self.check_session(binding)

    def check_session(self, binding):
        identifier = binding['session_id']
        session = self.sessions[identifier]
        require(self.registry[identifier] == binding['registry'] and session.session_binding == binding['registry']
            and session.source_mode == 'NATIVE_JOURNAL' and str(session.life_root) == binding['mirror_root'],
            'unchanged_native_session_binding')
        require(session.epoch_ledger.epoch_sha256 == binding['judge_epoch_sha256'], 'unchanged_original_judge_epoch')
        return session

    def native(self, incoming):
        with self.lock:
            if type(incoming) is dict and set(incoming) == {'session_id', 'request', 'records'}:
                if incoming['session_id'] in self.bindings:
                    validate_binding(self.bindings[incoming['session_id']])
                return self.original.native(incoming)
            keys = {'schema', 'session_id', 'transport_epoch', 'request', 'attestation_sha256'}
            require(type(incoming) is dict and set(incoming) == keys and incoming['schema'] == WIRE_SCHEMA,
                'owner_custody_reference_only_wire')
            require(incoming['session_id'] in self.bindings, 'owner_registered_projected_session')
            binding = self.bindings[incoming['session_id']]
            validate_binding(binding)
            require(incoming['transport_epoch'] == binding['transport_epoch'], 'same_explicit_transport_epoch')
            receipt = validate_receipt(self.store.receipt(incoming['attestation_sha256']), binding)
            require(incoming['request'] == receipt['request'], 'exact_attested_request_and_metrics')
            session = self.check_session(binding)
            request = deepcopy(receipt['request'])
            identifier = request['origin']['record_sha256']
            require(identifier not in session.seen, 'duplicate_ACT_no_automatic_resubmit')
            key = digest(dict(session_id=binding['session_id'], origin_sha256=identifier))
            claim = dict(schema='R233_PROJECTED_DISPATCH_INTENT_V1', request=request,
                attestation_sha256=incoming['attestation_sha256'], binding_sha256=digest(binding),
                transport_epoch=binding['transport_epoch'], unix=time.time())
            self.store.put('claim-' + key + '.json', canonical(claim))
            result = session.process_verified(request, receipt['raw_act'], identifier=identifier,
                think_resolver=lambda: deepcopy(receipt['think']))
            result['source_transport'] = dict(session_id=binding['session_id'], journal_id=binding['registry']['journal']['journal_id'],
                source_life_root=binding['registry']['life_root'], authenticated_operator_transport=True,
                child_network_access=False, mirror_method=WIRE_SCHEMA, transport_epoch=binding['transport_epoch'],
                attestation_sha256=incoming['attestation_sha256'], records_sha256=digest(receipt['records']),
                original_bytes=receipt['locally_validated_original_bytes'], projected_bytes=len(canonical(receipt)),
                complete_THINK_ancestry=receipt['think'] is not None)
            self.store.put('complete-' + key + '.json', canonical(dict(claim_sha256=digest(claim), response=result)))
            return result

    def generation(self, request):
        with self.lock:
            return self.original.generation(request)

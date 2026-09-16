"""Synthetic CPU-only tests: source remains inert data throughout validation."""

import builtins
from copy import deepcopy
import hashlib
import json
import os
import subprocess

import pytest

from organism_v6 import orch_r125_experiment_request as request_api


def origin():
    return dict(kind='BUILDER_TEST', record_index=0, record_sha256='a' * 64)


def encode(document):
    return json.dumps(document, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def rebind(document):
    payload = {key: value for key, value in document.items() if key != 'request_id'}
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'),
                           ensure_ascii=True, allow_nan=False).encode('utf-8')
    document['request_id'] = hashlib.sha256(canonical).hexdigest()
    return document


@pytest.mark.parametrize('kind', ['BUILDER_TEST', 'TRAIN_CHILD_RESPONSE'])
@pytest.mark.parametrize('source', ['print(1)\n', 'é😀\r\n', ' ', '# shell\necho "$HOME"',
                                   'this is not valid Python !!!'])
def test_roundtrip_and_independent_canonical_hash(kind, source):
    provenance = dict(origin(), kind=kind, record_index=42)
    request = request_api.make_request(source, provenance)
    assert request_api.parse_request(encode(request)) == request
    assert request['source'] == source
    assert request['source_sha256'] == hashlib.sha256(source.encode('utf-8')).hexdigest()
    assert rebind(deepcopy(request)) == request
    assert request_api.parse_request(json.dumps(request, indent=2).encode()) == request
    reordered = dict(reversed(list(request.items())))
    reordered['origin'] = dict(reversed(list(provenance.items())))
    assert request_api.parse_request(encode(reordered)) == request
    provenance['record_index'] = 99
    assert request['origin']['record_index'] == 42


def test_source_is_data_without_execution_import_or_compilation(monkeypatch):
    source = 'import os\nos.system("false")\nraise RuntimeError("must not run")\n'
    provenance = origin()

    def forbidden(*args, **kwargs):
        raise AssertionError('validator attempted execution or file access')

    with monkeypatch.context() as guards:
        for name in ('exec', 'eval', 'compile', 'open'):
            guards.setattr(builtins, name, forbidden)
        guards.setattr(os, 'system', forbidden)
        guards.setattr(subprocess, 'Popen', forbidden)
        guards.setattr(builtins, '__import__', forbidden)
        request = request_api.make_request(source, provenance)
        result = request_api.parse_request(encode(request))
    assert result['source'] == source


@pytest.mark.parametrize('field', sorted(request_api.REQUEST_KEYS))
def test_missing_top_level_field(field):
    request = request_api.make_request('pass', origin())
    del request[field]
    with pytest.raises(ValueError):
        request_api.parse_request(encode(request))


@pytest.mark.parametrize('field', ['path', 'args', 'command', 'environment', 'devices',
                                  'executable', 'timeout', 'extra'])
def test_forbidden_extra_fields_even_with_recomputed_id(field):
    request = request_api.make_request('pass', origin())
    request[field] = 'untrusted'
    with pytest.raises(ValueError):
        request_api.parse_request(encode(rebind(request)))


@pytest.mark.parametrize('change', [dict(kind='HELD'), dict(kind=[]), dict(record_index=True),
                                   dict(record_index=False), dict(record_index=-1),
                                   dict(record_index=1.0), dict(record_index='0'),
                                   dict(record_sha256='A' * 64), dict(extra=1)])
def test_invalid_origin_in_both_interfaces(change):
    provenance = dict(origin(), **change)
    request = request_api.make_request('pass', origin())
    request['origin'] = provenance
    with pytest.raises(ValueError):
        request_api.parse_request(encode(rebind(request)))
    with pytest.raises(ValueError):
        request_api.make_request('pass', provenance)


@pytest.mark.parametrize('field', sorted(request_api.ORIGIN_KEYS))
def test_missing_origin_fields(field):
    provenance = origin()
    del provenance[field]
    with pytest.raises(ValueError):
        request_api.make_request('pass', provenance)


@pytest.mark.parametrize('provenance', [None, [], 'origin', 1, True])
def test_origin_requires_object(provenance):
    with pytest.raises(ValueError):
        request_api.make_request('pass', provenance)


@pytest.mark.parametrize('field', ['request_id', 'source_sha256', 'record_sha256'])
@pytest.mark.parametrize('value', ['', 'a' * 63, 'a' * 65, 'A' * 64, 'g' * 64,
                                  'a' * 63 + '\n', 0, None, []])
def test_malformed_hashes(field, value):
    request = request_api.make_request('pass', origin())
    target = request['origin'] if field == 'record_sha256' else request
    target[field] = value
    if field != 'request_id':
        rebind(request)
    with pytest.raises(ValueError):
        request_api.parse_request(encode(request))


@pytest.mark.parametrize('field,value', [('source', 'changed'), ('source_sha256', 'b' * 64),
                                       ('request_id', 'b' * 64), ('schema', 'OTHER')])
def test_tampering(field, value):
    request = request_api.make_request('pass', origin())
    request[field] = value
    with pytest.raises(ValueError):
        request_api.parse_request(encode(request))


def test_source_hash_and_origin_binding_checked_independently():
    request = request_api.make_request('pass', origin())
    request['source'] = 'different'
    with pytest.raises(ValueError, match='source_sha256 mismatch'):
        request_api.parse_request(encode(rebind(request)))
    request = request_api.make_request('pass', origin())
    request['origin']['record_index'] = 1
    with pytest.raises(ValueError, match='request_id mismatch'):
        request_api.parse_request(encode(request))


@pytest.mark.parametrize('source', ['', '\0', 'x\0y', '\ud800', None, 1, [],
                                   'a' * 65537, 'é' * 32769])
def test_invalid_source_in_both_interfaces(source):
    with pytest.raises(ValueError):
        request_api.make_request(source, origin())
    request = request_api.make_request('pass', origin())
    request['source'] = source
    with pytest.raises(ValueError):
        request_api.parse_request(json.dumps(rebind(request)).encode())


@pytest.mark.parametrize('source', ['a' * 65536, 'é' * 32768, '😀' * 16384])
def test_exact_source_byte_limit(source):
    request = request_api.make_request(source, origin())
    assert request_api.parse_request(encode(request))['source'] == source


def test_exact_encoded_limit_and_early_oversize_rejection(monkeypatch):
    request = request_api.make_request('pass', origin())
    raw = encode(request)
    exact = raw + b' ' * (100_000 - len(raw))
    assert request_api.parse_request(exact) == request

    def forbidden(*args, **kwargs):
        raise AssertionError('oversized input reached JSON parser')

    monkeypatch.setattr(request_api.json, 'loads', forbidden)
    with pytest.raises(ValueError, match='byte limit'):
        request_api.parse_request(exact + b' ')


def test_make_request_checks_encoded_size_too():
    with pytest.raises(ValueError, match='byte limit'):
        request_api.make_request('\x01' * 65536, origin())


@pytest.mark.parametrize('raw', [b'{"schema":1,"schema":1}',
                                b'{"origin":{"kind":1,"kind":2}}',
                                b'{"source":1,"sour\\u0063e":2}'])
def test_duplicate_keys_at_every_depth(raw):
    with pytest.raises(ValueError, match='duplicate'):
        request_api.parse_request(raw)


@pytest.mark.parametrize('number', ['NaN', 'Infinity', '-Infinity', '1e999', '-1e999'])
def test_nonfinite_numbers(number):
    with pytest.raises(ValueError, match='nonfinite'):
        request_api.parse_request(('{"unused":' + number + '}').encode())


@pytest.mark.parametrize('raw', [b'', b'null', b'[]', b'true', b'1', b'"text"',
                                b'{} trailing', b'{}{}', b'{', b'\xff',
                                b'\xff\xfe{\x00}\x00', b'\xef\xbb\xbf{}',
                                b'[' * 2000 + b']' * 2000,
                                '{}', bytearray(b'{}'), None])
def test_malformed_or_nonbytes_input(raw):
    with pytest.raises(ValueError):
        request_api.parse_request(raw)

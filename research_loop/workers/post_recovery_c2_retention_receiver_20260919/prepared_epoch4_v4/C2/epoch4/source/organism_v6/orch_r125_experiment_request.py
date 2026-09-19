"""Pure request validation; submitted source is never executed or compiled.

Request IDs hash UTF-8 JSON with sorted keys, compact separators, ASCII escaping
(`ensure_ascii=True`), and no nonfinite numbers, excluding only request_id.
Origin hashes bind declarations; validation does not authenticate their records.
"""

import hashlib
import json
import math


SCHEMA = 'R125_CPU_EXPERIMENT_REQUEST_V1'
MAX_INPUT_BYTES = 100_000
MAX_SOURCE_BYTES = 65_536
REQUEST_KEYS = {'schema', 'request_id', 'source', 'source_sha256', 'origin'}
ORIGIN_KEYS = {'kind', 'record_index', 'record_sha256'}


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _valid_hash(value):
    return type(value) is str and len(value) == 64 and all(
        character in '0123456789abcdef' for character in value)


def _source_bytes(source):
    _require(type(source) is str, 'source must be a string')
    _require(0 < len(source) <= MAX_SOURCE_BYTES and '\0' not in source,
             'source must be nonempty, bounded and NUL-free')
    encoded = source.encode('utf-8')
    _require(len(encoded) <= MAX_SOURCE_BYTES, 'source exceeds UTF-8 byte limit')
    return encoded


def _canonical(document):
    return json.dumps(document, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('utf-8')


def _request_id(request):
    return hashlib.sha256(_canonical({key: value for key, value in request.items()
                                     if key != 'request_id'})).hexdigest()


def _unique_object(pairs):
    document = {}
    for key, value in pairs:
        _require(key not in document, 'duplicate JSON key')
        document[key] = value
    return document


def _reject_constant(value):
    raise ValueError('nonfinite JSON number')


def _finite_float(value):
    number = float(value)
    _require(math.isfinite(number), 'nonfinite JSON number')
    return number


def _validate(request):
    _require(type(request) is dict and set(request) == REQUEST_KEYS,
             'request requires exact fields')
    _require(request['schema'] == SCHEMA, 'unsupported schema')
    _require(_valid_hash(request['request_id']), 'invalid request_id')
    _require(_valid_hash(request['source_sha256']), 'invalid source_sha256')
    encoded = _source_bytes(request['source'])
    _require(hashlib.sha256(encoded).hexdigest() == request['source_sha256'],
             'source_sha256 mismatch')
    origin = request['origin']
    _require(type(origin) is dict and set(origin) == ORIGIN_KEYS,
             'origin requires exact fields')
    _require(type(origin['kind']) is str and origin['kind'] in (
        'BUILDER_TEST', 'TRAIN_CHILD_RESPONSE'), 'invalid origin kind')
    _require(type(origin['record_index']) is int and origin['record_index'] >= 0,
             'record_index must be a nonnegative integer')
    _require(_valid_hash(origin['record_sha256']), 'invalid record_sha256')
    _require(request['request_id'] == _request_id(request), 'request_id mismatch')
    return request


def parse_request(raw: bytes) -> dict:
    """Validate one bounded UTF-8 JSON object; invalid requests raise ValueError."""
    _require(type(raw) is bytes, 'raw must be bytes')
    _require(len(raw) <= MAX_INPUT_BYTES, 'encoded request exceeds byte limit')
    try:
        request = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object,
                             parse_constant=_reject_constant, parse_float=_finite_float)
        return _validate(request)
    except (UnicodeError, RecursionError) as error:
        raise ValueError('invalid UTF-8 or excessive JSON nesting') from error


def make_request(source: str, origin: dict) -> dict:
    """Build and validate a request, returning a detached JSON-compatible dict."""
    request = dict(schema=SCHEMA, source=source,
                   source_sha256=hashlib.sha256(_source_bytes(source)).hexdigest(),
                   origin=origin)
    try:
        request['request_id'] = _request_id(request)
        raw = json.dumps(request, ensure_ascii=False, allow_nan=False,
                         separators=(',', ':')).encode('utf-8')
    except (TypeError, UnicodeError, RecursionError) as error:
        raise ValueError('request must contain valid JSON data') from error
    return parse_request(raw)

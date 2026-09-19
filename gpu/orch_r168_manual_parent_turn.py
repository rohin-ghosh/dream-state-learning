"""Single Main-authored console turn during exclusive, settled parent custody."""

import hashlib
import json
from pathlib import Path

from gpu import orch_r167_parent_takeover as takeover


MESSAGE = ('Your last pre-sleep reply was {}. Earlier you were making a text game with a '
    'forest and a left-or-right choice. Return to that game: what is one specific '
    'difference between those choices, and why should it matter to the player? Decide '
    'which detail deserves closer attention and how you would examine it. Keep '
    'developing the same game in your own words, without a template; a proposed '
    'action is not an executed result.')


def settled_and_rendered(output):
    manifest = takeover.settled_attempts(output)
    for entry in manifest['attempts']:
        if entry['status'] != 'PUBLISHED':
            continue
        directory = Path(output)/entry['attempt']
        delivered = json.loads(takeover.read_file(directory/'DELIVERED.json'))
        result = json.loads(takeover.read_file(directory/'RESULT.json'))
        takeover.require(delivered['status'] == 'RENDERED'
            and delivered['publication'] == result['publication']
            and delivered['result_sha256'] == takeover.sha(directory/'RESULT.json')
            and delivered['rendered']['inbox_sha256'] == result['publication']['sha256']
            and delivered['rendered']['speaker'] == 'Astra'
            and delivered['rendered']['text_sha256'] == hashlib.sha256(result['message'].encode()).hexdigest(),
            'pending_or_unbound_publication_defer')
    return manifest


def execute_once(operations):
    """Injected lifecycle; actual implementation must prove exit before lock ownership."""
    operations.preflight()
    handle = None
    try:
        with operations.quiesce() as handle:
            manifest = operations.settled()
            operations.preserve(manifest)
            handle.terminate()
        with operations.exclusive_lock():
            operations.confirm_exit(manifest)
            operations.write_intent(MESSAGE)
            publication = operations.publish(MESSAGE)
            operations.record_publication(publication)
            return publication
    finally:
        if handle is not None and handle.terminated:
            operations.restart_unchanged()

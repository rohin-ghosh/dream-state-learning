"""Queue one attributed public HUMOUR goal; never pause or wait for a scorer."""

import sys
import time

from math_c import HOME, host, read, require, sha, write
from r206_handoff import root_for


def main():
    host()
    root = root_for(3)
    target = root / 'r210'
    binding = read(target / 'CAPTION_BINDING.json')
    require(binding['physical'] == 3 and binding['life_root'] == str(root / 'life'), 'one_exact_caption_life')
    require(not (target / 'R212_HUMOUR_GOAL.json').exists(), 'one_public_goal_delivery')
    source = target / 'source'
    message_path = HOME.parent / 'R212_HUMOUR_PARENT.txt'
    message = message_path.read_text().strip()
    require(len(message.split()) <= 160 and len(message.encode()) <= 4096, 'bounded_style_B_goal')
    sys.path.insert(0, str(source))
    from gpu.orch_r127_pilot_console import publish_parent
    publication = publish_parent(str(root / 'life'), 'Astra', message)
    write(target / 'R212_HUMOUR_GOAL.json', dict(publication=publication, published_unix=time.time(),
        message_sha256=sha(message_path), operator_authored_public_goal=True, child_rendered=False,
        child_signals=[], private_references_read=False, no_scorer_switch_wait=True))
    print(publication, flush=True)


if __name__ == '__main__':
    main()

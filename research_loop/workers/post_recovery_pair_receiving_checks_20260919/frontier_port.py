"""Exact-source performance overlay; serialized history and receipts are unchanged."""

from pathlib import Path


EDITS = (
    ("        self._events = []\n        self._by_id = {}\n",
     "        self._events = []\n        self._frontier_hasher = hashlib.sha256(b'[')\n"
     "        self._frontier_digests = [_digest([])]\n        self._by_id = {}\n"),
    ("    @property\n    def events(self):\n",
     "    def __deepcopy__(self, memo):\n"
     "        copied = type(self).__new__(type(self))\n"
     "        memo[id(self)] = copied\n"
     "        for name, value in vars(self).items():\n"
     "            setattr(copied, name, value.copy() if name == '_frontier_hasher' else deepcopy(value, memo))\n"
     "        return copied\n\n    @property\n    def events(self):\n"),
    ("        self._events.append(event)\n        self._by_id[event.event_id] = event\n",
     "        encoded = _json(asdict(event)).encode()\n"
     "        if self._events:\n            self._frontier_hasher.update(b',')\n"
     "        self._frontier_hasher.update(encoded)\n"
     "        closed = self._frontier_hasher.copy()\n        closed.update(b']')\n"
     "        self._frontier_digests.append(closed.hexdigest())\n"
     "        self._events.append(event)\n        self._by_id[event.event_id] = event\n"),
    ("        return Frontier(count, _digest([asdict(event) for event in self._events[:count]]))\n",
     "        return Frontier(count, self._frontier_digests[count])\n"),
)


def port(original):
    if b'_frontier_hasher' in original or b'def __deepcopy__' in original:
        raise ValueError('frontier_port_requires_unmodified_target')
    proposed = original
    for before, after in EDITS:
        if proposed.count(before.encode()) != 1:
            raise ValueError('frontier_port_requires_one_exact_seam')
        proposed = proposed.replace(before.encode(), after.encode(), 1)
    compile(proposed, '<frontier_performance_overlay>', 'exec')
    return proposed


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('output', type=Path)
    arguments = parser.parse_args()
    proposed = port(arguments.original.read_bytes())
    with arguments.output.open('xb') as output:
        output.write(proposed)

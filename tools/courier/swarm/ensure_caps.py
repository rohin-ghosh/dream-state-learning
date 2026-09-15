#!/usr/bin/env python3
"""Append the broker's lane word-cap note to NEXT_GUIDANCE of every Fable branch field file in a prompts directory.

Usage: python3 ensure_caps.py PROMPTS_DIR
The rendered prompt and its sha256 are untouched (NEXT_GUIDANCE is metadata the broker appends to the parent policy).
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_prompts import with_lane_caps  # noqa: E402


def main():
    prompts = sys.argv[1]
    changed = []
    for path in sorted(glob.glob(os.path.join(prompts, 'F[1-4].fields.json'))):
        doc = json.load(open(path))
        fields = doc['fields']
        new = with_lane_caps(fields.get('NEXT_GUIDANCE', ''), fields['GAME'])
        if new != fields.get('NEXT_GUIDANCE', ''):
            fields['NEXT_GUIDANCE'] = new
            tmp = path + '.tmp'
            json.dump(doc, open(tmp, 'w'), indent=1, sort_keys=True)
            os.replace(tmp, path)
            changed.append(os.path.basename(path))
    print('caps ensured; changed:', changed or 'none')


if __name__ == '__main__':
    main()

import argparse
import json

from prepare import CANON, OWN, act_pairs, event_key


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('label')
    parser.add_argument('--parents-only', action='store_true')
    parser.add_argument('--limit', type=int, default=1800)
    parser.add_argument('--max-events', type=int, default=5)
    arguments = parser.parse_args()
    evidence = json.loads((OWN / 'private' / arguments.label / 'EVIDENCE.json').read_bytes())
    acts = act_pairs(evidence)
    first = acts[0]['request']['index']
    seen = {}
    for frame in CANON.frames(evidence):
        for event in frame['request']['external']:
            if event['actor'] != 'parent' and not event['text'].startswith('Tool:'):
                continue
            if arguments.parents_only and event['actor'] != 'parent':
                continue
            key = event_key(event)
            if key not in seen:
                seen[key] = dict(event, first_request=frame['request']['index'], last_request=frame['request']['index'])
            else:
                seen[key]['last_request'] = frame['request']['index']
    eligible = []
    for event in seen.values():
        if event['last_request'] < first:
            continue
        if event['first_request'] < first - 40 and event['actor'] != 'parent':
            continue
        eligible.append(event)
    for event in sorted(eligible, key=lambda item: item['first_request'])[-arguments.max_events:]:
        print(json.dumps({key: value for key, value in event.items() if key != 'text'}, ensure_ascii=False))
        print(event['text'][:arguments.limit])


if __name__ == '__main__':
    main()

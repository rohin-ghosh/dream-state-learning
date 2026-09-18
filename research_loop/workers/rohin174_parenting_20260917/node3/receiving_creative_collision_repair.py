"""Apply the tested A/1 response-clock naming repair at a quiet parent boundary."""

import argparse
import json
import receiving_parent as receiver
from receiving_collision_repair import install


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preflight', 'serve'))
    arguments = parser.parse_args()
    receiver.STATE = receiver.STATE / 'creative_collision_repair_v1'
    receiver.effort.runtime = install(receiver.effort.runtime)
    result = receiver.serve(4, preflight=arguments.action == 'preflight')
    if result is not None:
        print(json.dumps(result, sort_keys=True))

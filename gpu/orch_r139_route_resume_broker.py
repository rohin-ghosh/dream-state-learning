"""Bind unchanged prospective F1 broker to actual attempt3/R139B readiness."""

import hashlib
from pathlib import Path


ORIGINAL_SHA = 'dba180f089c909bbdd653efc8782b33353780e39254c7f0215de3de487be3763'


def broker_source(source):
    changes = {
        'orch_r139_F1_astra_handoff_20260916_attempt2':('orch_r139_F1_astra_handoff_20260916_attempt3',1),
        'R139_INDEPENDENT_ACTOR_READY.json':('R139B_INDEPENDENT_ACTOR_READY.json',2),
    }
    for before,(after,count) in changes.items():
        if source.count(before)!=count:
            raise ValueError('exact_attempt3_broker_binding_seam')
        source = source.replace(before,after)
    return source


def main():
    original = Path(__file__).with_name('orch_r139_route_astra_broker.py')
    if hashlib.sha256(original.read_bytes()).hexdigest()!=ORIGINAL_SHA:
        raise ValueError('frozen_existing_F1_broker')
    values = dict(__file__=__file__,__name__='r139b_bound_existing_broker')
    exec(compile(broker_source(original.read_text()),__file__+':actual_attempt3_actor','exec'),values)
    old_pins = values['ORIGINAL_PINS']
    def pins():
        result = old_pins()
        root = values['prior'].transport.ROOT
        result[str(original.relative_to(root))] = ORIGINAL_SHA
        return result
    values['ORIGINAL_PINS'] = pins
    values['main']()


if __name__=='__main__':
    main()

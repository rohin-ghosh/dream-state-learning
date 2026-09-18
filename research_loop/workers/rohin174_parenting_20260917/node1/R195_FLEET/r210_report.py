"""Write a current receipt; publication, rendering, LOADED and /proc are distinct."""

import datetime
import importlib.util
import json
import os
from pathlib import Path


OWN = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('r210_parent_report', OWN/'r210_parent.py')
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)


def main():
    observed = parent.observe()
    report = dict(observed_unix=observed['observed_unix'], phase='R210_PARENTED_ENRICHMENT', arms=[],
                  prior_phase='COMPLETE57_SCREEN_ENDED_PRESERVED', no_withdrawn_suffix_claim=True,
                  hard_end_utc='2026-09-26T17:05:00Z', physical_lease_end_utc='2026-09-26T23:05:00Z',
                  peer_groups=[[2,3,4],[5,7]], caption_followup_handoff='research_loop/workers/rohin209_first_game_20260918/followup_c2.py')
    for physical, arm in observed['arms'].items():
        saved = json.loads((OWN/'R204_LIVE_VERIFIED_20260918T050117Z.json').read_bytes())
        prior = next(row for row in saved['arms'] if row['physical']==int(physical))
        if arm['loaded']:
            loaded = arm['loaded']['document']
            checkpoint = prior['terminal_checkpoint']['metadata']
            assert loaded['adapter_sha256']==checkpoint['adapter_state_sha256']
            assert loaded['optimizer_steps']==checkpoint['optimizer_steps']
            assert loaded['base_sha256']==checkpoint['base_sha256'] and loaded['resume'] is True
        rows = []
        for publication in arm['publications']:
            rows.append(dict(kind=publication['kind'], id=publication['publication']['id'],
                             published_unix=publication['published_unix'], inbox=publication['inbox'], render=publication['render']))
        receipt_root = OWN/('R210_PARENT_'+physical)
        judgment = None
        if (receipt_root/'V_TURN2.json').exists():
            judgment = json.loads((receipt_root/'V_TURN2.json').read_bytes())['parent_judgment']
        repairs = 1 if (receipt_root/'OPENING.json').exists() and json.loads((receipt_root/'OPENING.json').read_bytes())['V_repair_turn'] else 0
        repairs += any(row['kind']=='V_TURN2' for row in rows)
        report['arms'].append(dict(physical=int(physical), name=arm['name'], environment_object=arm['task'],
             status='LIVE' if arm['native'] else 'LOADED_NOT_CURRENTLY_ALIVE' if arm['loaded'] else 'DISPATCHED_NOT_LOADED',
             native=arm['native'], loaded=arm['loaded'], first_request=arm['requests'][0] if arm['requests'] else None,
             preserved=arm['phase1_preserved'], restore_pass=arm['restore_pass'], latest_complete=arm['complete'],
             loaded_matches_preserved_adapter_optimizer=bool(arm['loaded']),
             filter_sha256=arm['filter_sha256'], filter_live=bool(arm['native']), parent_turns=rows,
             V_repair_publications=repairs, V_parent_judgment=judgment,
             move_on_published=any(row['kind']=='MOVE_ON' for row in rows),
             move_on_rendered=any(row['kind']=='MOVE_ON' and row['render'] for row in rows),
             peer_publications=sum(row['kind'].startswith('PEER_') for row in rows),
             peer_first_renders=sum(row['kind'].startswith('PEER_') and row['render'] is not None for row in rows),
             own_current_state_entries=len(arm['own_state']), exit=arm['exit'], dispatch_failure=arm['dispatch_failure']))
    stamp = datetime.datetime.fromtimestamp(observed['observed_unix'], datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    path = OWN/('R210_CURRENT_'+stamp+'.json')
    path.write_text(json.dumps(report, sort_keys=True, indent=2))
    temporary = OWN/'R210_CURRENT.partial'
    temporary.write_text(json.dumps(report, sort_keys=True, indent=2))
    os.replace(temporary, OWN/'R210_CURRENT.json')
    print(path.relative_to(OWN.parents[4]))
    for arm in report['arms']:
        opening = next((row for row in arm['parent_turns'] if row['kind']=='OPENING'), {})
        print(json.dumps(dict(physical=arm['physical'], name=arm['name'], status=arm['status'], native=arm['native'],
              opening_id=opening.get('id'), first_render=opening.get('render'), V_turns=arm['V_repair_publications'],
              move_on=arm['move_on_rendered'], peers=arm['peer_first_renders'])))


if __name__ == '__main__':
    main()

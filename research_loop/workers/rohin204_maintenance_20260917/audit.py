"""R204 local scheduler for finite, read-only, CPU-only fleet observations."""

import argparse
import concurrent.futures
import datetime
import fcntl
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
import unicodedata


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCANNER_SOURCE = (REPO / 'organism_v6/orch_r203_prose_target_filter.py').read_bytes()
SCANNER = {}
exec(compile(SCANNER_SOURCE, 'orch_r203_prose_target_filter.py', 'exec'), SCANNER)
scan_target = SCANNER['scan_target']

WRAPPERS = dict(node1='gpu/a100_ssh.sh', node2='gpu/ovx_ssh.sh',
                node4='gpu/a40r_ssh.sh', node5='gpu/ovx3_ssh.sh')
INTERVAL = 1200
OWNER = dict(node1='NODE1 sole operator', node2='Leibniz/NODE2', node4='Turing/NODE4', node5='Descartes/NODE5')
SECRET = re.compile(r'-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----|\b(?:sk-ant-|sk-proj-|ghp_|github_pat_|glpat-)[\w-]{16,}|\bBearer\s+[A-Za-z0-9._-]{20,}')


def save(path, value):
    content = json.dumps(value, indent=2, ensure_ascii=False) + '\n'
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(content)
    os.replace(temporary, path)


def glyphs(raw):
    letters = [character for character in raw if character.isalpha()]
    words = re.findall(r'[^\W\d_]+', raw)
    scripts = ('LATIN', 'CYRILLIC', 'GREEK', 'CJK', 'HIRAGANA', 'KATAKANA', 'HANGUL')
    mixed = 0
    for word in words:
        found = {script for character in word for script in scripts if script in unicodedata.name(character, '')}
        mixed += int(len(found) > 1)
    capital = scan_target(raw)
    return dict(chars=len(raw), letters=len(letters), words=len(words),
        fullwidth=sum('\uff01' <= character <= '\uff5e' for character in raw),
        cjk=sum(any(script in unicodedata.name(character, '') for script in scripts[3:]) for character in letters),
        mixed_script_words=mixed,
        whitespace=sum(character.isspace() for character in raw),
        non_ascii_whitespace=sum(character.isspace() and ord(character) > 127 for character in raw),
        zero_width=sum(character in '\u200b\u200c\u200d\ufeff' for character in raw),
        internal_multispace_runs=len(re.findall(r'\S[ \t]{2,}(?=\S)', raw)),
        lowercase_uppercase_joins=len(re.findall(r'[a-z][A-Z]', raw)), capitalization=capital)


def collect_node(node, bundle, inventory):
    leases = [life.get('wall', {}).get('lease_end_unix') for life in inventory['lives'] if life['node'] == node]
    leases = [value for value in leases if isinstance(value, (int, float))]
    if not leases or time.time() >= min(leases) - 300:
        return dict(status='LEASE_UNVERIFIED_OR_EXPIRED_SKIPPED', lives=[], native_count=None)
    program = bundle['census'] + '\ncensus=rows\n' + bundle['journal_helpers'] + '\n' + (HERE / 'remote.py').read_text()
    try:
        result = subprocess.run(['bash', str(REPO / WRAPPERS[node]), 'python3 -B -c ' + shlex.quote(program)],
            capture_output=True, text=True, timeout=125)
        if result.returncode:
            return dict(status='SSH_READOUT_FAILED', returncode=result.returncode, lives=[], native_count=None)
        payload = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, ValueError, OSError) as error:
        return dict(status='READOUT_UNVERIFIED', error_type=type(error).__name__, lives=[], native_count=None)
    for life in payload['lives']:
        prior = next((row for row in inventory['lives'] if row['node'] == node
            and row['configured_root'] == life.get('configured_root')), {})
        life['life'] = life.get('trial_id') or prior.get('life') or life.get('configured_root', 'unknown').split('/')[-2]
        life['owner'] = OWNER[node]
        for raw in life.get('raw_last10', []):
            raw['metrics'] = glyphs(raw['raw'])
            if SECRET.search(raw['raw']):
                raw.pop('raw')
                raw['raw_withheld_possible_credential'] = True
    return payload


def table(nodes):
    lines = ['| Node/slot/life | PID/state; head age | REQUEST /12288 | Compaction | THINK sequence | Raw10 FW; capitals; CJK; mixed; spaces | Sleep rows new/replay; updates new/replay (total); seconds | Parent INBOX/hr; REQUEST opportunities | State rejects/edits |',
        '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for node, payload in nodes.items():
        if payload.get('status'):
            lines.append(f"| {node} | {payload['status']} | ? | ? | ? | ? | ? | ? | ? |")
        for life in sorted(payload.get('lives', []), key=lambda row: (row.get('physical') is None, row.get('physical') or 0)):
            if life.get('status'):
                lines.append(f"| {node}/{life.get('physical')}/{life.get('life')} | {life['pid']}: UNVERIFIED {life.get('failure_reason', '')} | ? | ? | ? | ? | ? | ? | ? |")
                continue
            samples = life.get('raw_last10', [])
            metrics = [sample['metrics'] for sample in samples]
            chars = sum(metric['chars'] for metric in metrics)
            letters = sum(metric['letters'] for metric in metrics)
            capitals = sum(metric['capitalization']['capitalized_common_words'] for metric in metrics)
            opportunities = sum(metric['capitalization']['eligible_common_word_opportunities'] for metric in metrics)
            text = f"{len(samples)}/10: {sum(metric['fullwidth'] for metric in metrics)}/{chars}; {capitals}/{opportunities}; {sum(metric['cjk'] for metric in metrics)}/{letters}; {sum(metric['mixed_script_words'] for metric in metrics)}/{sum(metric['words'] for metric in metrics)}; {sum(metric['non_ascii_whitespace'] for metric in metrics)}/{sum(metric['whitespace'] for metric in metrics)}"
            last_sleep = (life.get('sleeps') or [{}])[-1]
            recipe = last_sleep.get('recipe') or {}
            sleep = f"{last_sleep.get('new_rows', '?')}/{recipe.get('selected_old_rows', '?')}; {last_sleep.get('new_updates', '?')}/{last_sleep.get('replay_updates', '?')} ({last_sleep.get('optimizer_steps', '?')}); {last_sleep.get('duration_mtime_seconds', '?')}"
            if life.get('sleep_in_progress'):
                sleep += ' (+active)'
            stages = life.get('stages', [])
            sequence = ','.join(str(stage['stage']) for stage in stages[-6:]) or 'none observed'
            compaction = (life.get('compactions') or [{}])[-1].get('reference', {})
            counts = life.get('working_state_statuses', {})
            head = life.get('head', {})
            request = life.get('latest_request') or {}
            prefix = '' if life.get('hour_window_complete') else '>='
            age = round(head['age_seconds']) if head.get('age_seconds') is not None else '?'
            request_label = '' if life.get('current_loaded') else ' (await matching LOADED)'
            lines.append(f"| {node}/{life.get('physical')}/{life['life']} | {life['pid']}/{life.get('state_at_end', life.get('state'))}; {age}s | {request.get('prompt_tokens', '?')}/12288{request_label} | {compaction.get('kind', 'none')}:{compaction.get('index', '-')} | {sequence} | {text} | {sleep} | {prefix}{life.get('parent_inbox_hour', 0)}; {prefix}{life.get('requests_hour', 0)} | {counts.get('REJECTED_PRIOR_STATE_RETAINED', 0)}/{life.get('working_state_edit_opportunities', 0)} |")
    return '\n'.join(lines)


def prepend(entry):
    path = REPO / 'research_loop/COORDINATION.md'
    for attempt in range(5):
        before = path.read_bytes()
        heading, separator, body = before.partition(b'\n')
        candidate = heading + separator + b'\n' + entry.encode() + b'\n' + body
        temporary = HERE / 'coordination_prepend.tmp'
        temporary.write_bytes(candidate)
        if path.read_bytes() == before:
            os.replace(temporary, path)
            return True
        time.sleep(0.1)
    temporary.unlink(missing_ok=True)
    return False


def one_pass():
    inventory_path = REPO / 'research_notes/analysis/R195_FLEET_GLYPH_AUDIT_2026-09-17.json'
    inventory = json.loads(inventory_path.read_text())
    bundle = json.loads((HERE / 'R195_HELPERS.json').read_text())
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda node: collect_node(node, bundle, inventory), WRAPPERS))
    nodes = dict(zip(WRAPPERS, results))
    output = dict(schema='R204_MAINTENANCE_PASS_V1', started_utc=timestamp.isoformat(),
        finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), nodes=nodes,
        helper_sources=bundle['sources'], inventory_sha256=hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
        scanner_sha256=hashlib.sha256(SCANNER_SOURCE).hexdigest(),
        observed_native_count=sum(payload.get('native_count') or 0 for payload in nodes.values()),
        observed_state_counts=dict((state, sum(life.get('state_at_end') == state for payload in nodes.values()
            for life in payload.get('lives', []))) for state in ('R', 'S', 'T', 'D', 'Z')),
        gpu_model_calls=0, remote_writes=0, child_signals=0, node3_contacted=False)
    if len(json.dumps(output, ensure_ascii=False).encode()) > 16 * 1024 * 1024:
        for payload in nodes.values():
            for life in payload.get('lives', []):
                for sample in life.get('raw_last10', []):
                    if 'raw' in sample:
                        sample.pop('raw')
                        sample['raw_withheld_local_log_bound'] = True
        output['raw_copy_limit_reached'] = True
    name = timestamp.strftime('PASS_%Y%m%dT%H%M%SZ')
    save(HERE / (name + '.json'), output)
    markdown = table(nodes)
    notes = ('Counts are descriptive opportunities, not degradation, causal, or quality claims. '
        'Raw columns: fullwidth/chars; internal common-word capitals/opportunities (existing R203 scanner); '
        'CJK+Kana+Hangul/letters; mixed-script words/words; non-ASCII whitespace/all whitespace. '
        'Zero-width, internal multispace and case-join counts are in JSON. Original raw TRAIN strings and SHA receipts are retained unchanged; possible credentials are withheld. '
        'Parent counts are accepted TRAIN parent INBOX records, not a claim of attention or actual REQUEST visibility; denominator is TRAIN REQUESTs in up to one hour of this incarnation, not an extrapolated hourly rate. '
        '>= means the 2,000-record bound did not cover the full hour. Sleep rows are raw-new/selected-replay; actual new/replay updates join presentation hashes to new-row hashes. Duration uses SLEEP_REQUEST-to-COMPLETE file mtimes, including checkpoint time; last completed sleep is shown, not an update-rate claim. '
        'State edits deduplicate consolidation source_event_id and exclude NO_EXPLICIT_STATE_DELTA. T means stopped/held, not diagnosed broken. '
        'Current metrics begin at a hash-verified LOADED matching PID and process-start time, under the observed trial/root/plan; no current REQUEST or raw sample is reported before that boundary. Inherited source head/REQUEST are separate JSON fields. Document started/finished/loaded timestamps are preferred when present; zero mtimes are unknown, never multi-decade staleness. '
        'Missing evidence is unverified. No launch gate, child/operator intervention, or sealed/FINAL access.\n')
    faults = []
    for node, payload in nodes.items():
        if payload.get('status'):
            faults.append(f"{OWNER[node]}: {payload['status']} (audit connectivity/lease status, not child failure).")
        for life in payload.get('lives', []):
            request = life.get('latest_request') or {}
            reasons = list(life.get('errors', []))
            if not life.get('native_identity_verified'):
                reasons.append('identity/readout unverified: ' + life.get('failure_reason', 'IDENTITY_CHANGED'))
            if (request.get('prompt_tokens') or 0) >= 12288 and request.get('after_current_process_start'):
                reasons.append('last REQUEST at/above 12288')
            if (life.get('head', {}).get('age_seconds') or 0) > INTERVAL:
                reasons.append('record age >20min; hold/sleep/operator intent not inferred')
            if reasons:
                faults.append(f"{OWNER[node]} {life.get('life')} PID {life['pid']}: {', '.join(reasons[:3])}.")
    notice = '\n'.join('- ' + fault for fault in faults) or 'No bounded readout fault flagged; this does not establish overall runtime health.'
    entry = f"## [Builder/Jason — R204 maintenance read-only pass] {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n{output['observed_native_count']} native processes observed on nodes1/2/4/5 (includes T/held, not a live-learning count); node3 excluded. State counts: {output['observed_state_counts']}. Receipts: `research_loop/workers/rohin204_maintenance_20260917/{name}.json`.\n\n{markdown}\n\n{notes}\nOwner routing (report only; no signals/restarts/reconfiguration):\n{notice}\n"
    (HERE / (name + '.md')).write_text(entry)
    output['coordination_prepended'] = prepend(entry)
    save(HERE / 'STATUS.json', output)
    (HERE / 'STATUS.md').write_text(entry)
    for suffix in ('.json', '.md'):
        for old in sorted(HERE.glob('PASS_*' + suffix))[:-36]:
            old.unlink()
    logging.info('%s observed=%d coordination=%s', name, output['observed_native_count'], output['coordination_prepended'])
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('once', 'serve', 'status', 'stop'))
    args = parser.parse_args()
    if args.mode == 'stop':
        (HERE / 'STOP').touch()
        print('Audit-only stop requested; child processes untouched.')
        return
    if args.mode == 'status':
        state = json.loads((HERE / 'SERVICE.json').read_text()) if (HERE / 'SERVICE.json').exists() else {}
        try:
            fields = Path('/proc', str(state['pid']), 'stat').read_text().rsplit(')', 1)[1].split()
            process = Path('/proc', str(state['pid']))
            state['identity_alive'] = (fields[19] == state['start_ticks'] and process.stat().st_uid == state['uid']
                and hashlib.sha256(process.joinpath('cmdline').read_bytes()).hexdigest() == state['cmdline_sha256'])
        except (KeyError, OSError):
            state['identity_alive'] = False
        print(json.dumps(state))
        return
    with (HERE / 'SERVICE.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        handler = RotatingFileHandler(HERE / 'service.log', maxBytes=65536, backupCount=2)
        logging.basicConfig(level=logging.INFO, handlers=[handler])
        if args.mode == 'once':
            result = one_pass()
            print(json.dumps(dict(observed=result['observed_native_count'], coordination=result['coordination_prepended'])))
            return
        if (HERE / 'STOP').exists():
            raise RuntimeError('STOP_PRESENT')
        fields = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
        save(HERE / 'SERVICE.json', dict(pid=os.getpid(), uid=os.getuid(), start_ticks=fields[19],
            cmdline_sha256=hashlib.sha256(Path('/proc/self/cmdline').read_bytes()).hexdigest(),
            interval_seconds=INTERVAL, control=str(HERE / 'STOP'),
            stop_command=f'python3 -B {HERE.relative_to(REPO)}/audit.py stop'))
        while not (HERE / 'STOP').exists():
            began = time.monotonic()
            try:
                one_pass()
            except Exception as error:
                logging.error('pass_error_type=%s', type(error).__name__)
                save(HERE / 'LAST_ERROR.json', dict(error_type=type(error).__name__, observed_unix=time.time()))
            while time.monotonic() - began < INTERVAL and not (HERE / 'STOP').exists():
                time.sleep(5)


if __name__ == '__main__':
    main()

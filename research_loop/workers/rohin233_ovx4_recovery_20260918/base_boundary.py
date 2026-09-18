"""Capture a real score boundary; never regenerate or rescore a pending ACT."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import socket
import socketserver
import time

from research_loop.workers.rohin233_ovx4_recovery_20260918.lease_bridge import exchange, put


def finalize_pending(root, state, response, clock=time.time):
    from research_loop.workers.rohin221_continuous_caption_20260918.controller import Controller, Plan
    pending = state['pending']
    if not pending or pending['kind'] != 'SCORE' or pending['request']['request_id'] != response.get('request_id'):
        raise ValueError('exact_pending_real_score_required')
    controller = Controller.__new__(Controller)
    controller.root = Path(root)
    controller.state_path = controller.root / 'private/state.json'
    controller.plan = Plan(**state['binding']['plan'])
    controller.state = deepcopy(state)
    controller.clock = clock
    controller.backend = type('NoGenerationDuringFinalization', (), {'kind':state['backend_state']['kind']})()
    controller.finish_attempt(deepcopy(pending['attempt']), deepcopy(pending['request']), deepcopy(response))
    return controller.state


def main(config):
    root = Path(config['root'])
    original = Path(config['original_root'])
    endpoint = Path(config['endpoint'])
    parked = endpoint.with_name('base.prelease.sock')
    pid = config['player_pid']
    assert not parked.exists()
    assert Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19] == config['player_start_ticks']

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(115)
            raw = self.rfile.readline(262145)
            assert raw.endswith(b'\n') and len(raw) <= 262144
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as upstream:
                upstream.settimeout(110)
                upstream.connect(str(parked))
                upstream.sendall(raw)
                with upstream.makefile('rb') as stream:
                    received = stream.readline(262145)
            assert received.endswith(b'\n') and len(received) <= 262144
            request,response = json.loads(raw),json.loads(received)
            state_path = original / 'player/private/state.json'
            saved = state_path.read_bytes()
            state = json.loads(saved)
            assert state['pending']['kind'] == 'SCORE'
            identifier = state['pending']['request']['request_id']
            assert request['origin']['request_id'] == response['request_id'] == identifier
            result_path = original / 'scorer/attempts' / identifier / 'RESULT.json'
            assert hashlib.sha256(result_path.read_bytes()).hexdigest() == response['receipt_sha256']
            result = json.loads(result_path.read_bytes())
            assert result['origin'] == request['origin']
            put(root / 'BOUNDARY_RESPONSE.private.json', dict(request=request,response=response,
                request_wire_sha256=hashlib.sha256(raw).hexdigest(), response_wire_sha256=hashlib.sha256(received).hexdigest()))
            put(root / 'BOUNDARY_CAPTURED.json',dict(unix=time.time(),player_pid=pid,
                ACT_request_id=identifier,actual_result_sha256=response['receipt_sha256'],
                controller_state_sha256=hashlib.sha256(saved).hexdigest(),operator_handoff_required=True,
                privileged_actions_attempted=False,native_signals=[]))
            while not (root / 'BOUNDARY_READY.json').exists() and time.time()<config['deadline_unix']:
                time.sleep(.1)

    with socketserver.UnixStreamServer(str(parked),Handler) as server:
        os.chmod(parked,0o600)
        exchange(endpoint,parked)
        put(root / 'BOUNDARY_ARMED.json',dict(unix=time.time(),pid=os.getpid(),player_pid=pid,
            mechanism='forward_next_authentic_score_then_exact_saved_pending_SCORE_handoff',native_signals=[]))
        server.timeout=.5
        while time.time()<config['deadline_unix'] and not (root/'BOUNDARY_READY.json').exists():
            server.handle_request()


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,required=True)
    main(json.loads(parser.parse_args().config.read_bytes()))

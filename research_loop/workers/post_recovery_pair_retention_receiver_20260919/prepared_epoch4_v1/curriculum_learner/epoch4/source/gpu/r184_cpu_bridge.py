"""Fixed-origin C2 CPU dispatcher outside the non-escalating GPU service."""
import argparse,json,os,socket,time
from pathlib import Path


def call(config,origin):
    path=Path(config['bridge_config'])
    binding=json.loads(path.read_bytes())
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as channel:
        channel.settimeout(150)
        channel.connect(binding['socket'])
        channel.sendall(json.dumps(origin).encode()+b'\n')
        stream=channel.makefile('rb')
        return json.loads(stream.readline(262145))


def serve(path):
    from gpu.orch_r153_community_transport import cpu_once
    from gpu.orch_r125_cpu_experiment import digest,verify_gate
    config=json.loads(Path(path).read_bytes())
    if digest(verify_gate(config['gate_root']))!=config['gate_sha256']:
        raise ValueError('actual_node2_CPU_gate')
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as server:
        server.bind(config['socket'])
        os.chmod(config['socket'],0o600)
        server.listen(1)
        server.settimeout(5)
        while time.time()<config['stop_unix']:
            try:
                channel,unused=server.accept()
            except TimeoutError:
                continue
            with channel:
                channel.settimeout(160)
                try:
                    origin=json.loads(channel.makefile('rb').readline(4097))
                    if set(origin)!={'kind','record_index','record_sha256'} or origin['kind']!='TRAIN_CHILD_RESPONSE' or origin['record_index']<5129:
                        raise ValueError('new_copy_child_origin_only')
                    outcome=cpu_once(config['raw_root'],config['journal_id'],origin,config['gate_sha256'],gate_root=config['gate_root'],start=True)
                    outcome={key:value for key,value in outcome.items() if key!='result'}
                except Exception as error:
                    outcome=dict(status='TOOL_OUTCOME_UNKNOWN_NO_RETRY',executed=None,error_type=type(error).__name__)
                channel.sendall(json.dumps(outcome).encode()+b'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',required=True)
    serve(parser.parse_args().config)

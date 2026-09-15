import inspect
import pytest
from gpu import orch_r118_route_astra_custody as custody


def control():
    return dict(root=custody.ROOT, terminal=custody.TERMINAL,
        plan=dict(path=custody.ROOT+'/R118_PARALLEL_PLAN.json',sha256='a'*64),
        parent_wait_seconds=120,deadline_unix=1789491720,
        native_source=dict(path=custody.__file__,sha256=custody.sha(custody.__file__)),
        control_sha256='b'*64,config_sha256='c'*64)


def heartbeat(config):
    return dict(control_sha256=config['control_sha256'],config_sha256=config['config_sha256'],
        plan=config['plan'],exclusive_queue_lock_acquired=True,time_unix=100,
        identity_role='VM_HTTP_PROVIDER_WORKER',identity=dict(pid=12),host_binding_sha256='d'*64)


def test_exact_A1_control():
    custody.verify_control(control())


@pytest.mark.parametrize('field,value', [('root','/foreign'),('terminal','TERMINAL.json'),
    ('parent_wait_seconds',600),('deadline_unix',1789591720)])
def test_foreign_or_changed_control_rejected(field,value):
    config=control();config[field]=value
    with pytest.raises(ValueError):custody.verify_control(config)


@pytest.mark.parametrize('field,value', [('time_unix',69),('time_unix',101),
    ('exclusive_queue_lock_acquired',False),('identity_role','NODE_PROVIDER'),
    ('control_sha256','e'*64),('config_sha256','f'*64)])
def test_stale_or_unbound_worker_rejected(field,value):
    config=control();document=heartbeat(config);document[field]=value
    with pytest.raises(ValueError):custody.validate_heartbeat(document,config,100)


def test_current_worker_and_real_http_evaluator_preserved():
    config=control();custody.validate_heartbeat(heartbeat(config),config,100)
    source=inspect.getsource(custody.serve)
    assert 'evaluate=astra.evaluate' in source and 'transport.process_request.__code__' in source
    assert 'self.owned_lock = True' in source
    assert 'threading.Thread(target=self.heartbeat_loop, daemon=True).start()' in source
    assert 'self.heartbeat_lock = threading.Lock()' in source
    assert 'NVIDIA_API_KEY' not in inspect.getsource(custody)

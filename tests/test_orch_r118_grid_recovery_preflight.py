import hashlib
import os

import pytest

from gpu import orch_r118_grid_recovery_preflight as preflight


def test_native_code_compiles_without_model_dispatch():
    for branch in ('F4','A4'):
        code = preflight.native_code(branch)
        compile(code, '<native-readonly-preflight>', 'exec')
        assert 'runner.guard(' not in code and 'runner.native(' not in code


def test_live_identity_ignores_reparenting_but_checks_stable_fields(tmp_path):
    directory=tmp_path/'123'
    directory.mkdir()
    fields=['S','999']+['0']*17+['42']
    (directory/'stat').write_text('123 (python3) '+' '.join(fields))
    (directory/'cmdline').write_bytes(b'python3\0owned.py\0')
    boot=tmp_path/'sys/kernel/random/boot_id'
    boot.parent.mkdir(parents=True)
    boot.write_text('fixture')
    identity=dict(pid=123,start_ticks='42',boot_id='fixture',uid=os.getuid(),ppid=1,
        command_sha256=hashlib.sha256((directory/'cmdline').read_bytes()).hexdigest())
    preflight.checked_identity(identity,proc=tmp_path)
    for change in (dict(start_ticks=43),dict(boot_id='other'),dict(uid=os.getuid()+1),dict(command_sha256='wrong')):
        with pytest.raises(ValueError):
            preflight.checked_identity(dict(identity,**change),proc=tmp_path)

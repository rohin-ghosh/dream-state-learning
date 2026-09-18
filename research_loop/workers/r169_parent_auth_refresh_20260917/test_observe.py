import importlib.util
import json
from pathlib import Path


spec = importlib.util.spec_from_file_location('observer', Path(__file__).with_name('observe.py'))
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)


def test_process_read_denial_is_unknown_not_dead(tmp_path, monkeypatch):
    config = tmp_path/'CONFIG.json'
    config.write_text('{}')
    (tmp_path/'BINDING.json').write_text(json.dumps(dict(config=str(config), branch='test',
        original=dict(pid=1), cursor=5)))
    (tmp_path/'parent').mkdir()
    (tmp_path/'parent/STARTED.json').write_text(json.dumps(dict(pid=123, started_unix=10)))

    class DeniedProc:
        def __truediv__(self, value):
            raise PermissionError(13, 'denied')

    def path_factory(value):
        return DeniedProc() if str(value) == '/proc' else Path(value)

    monkeypatch.setattr(observer, 'Path', path_factory)
    result = observer.observe(tmp_path)
    assert result['alive'] is None
    assert result['health_read_error'] == dict(error_type='PermissionError', errno=13)
    assert result['started'] is True

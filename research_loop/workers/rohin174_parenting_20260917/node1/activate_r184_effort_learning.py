"""Use the existing takeover with the learning receipt's actual label binding."""

from pathlib import Path

from inventory_node1 import HERE, Reader, digest, require


if __name__ == '__main__':
    raw = Reader().raw(HERE / 'activate_r184_effort.py')
    require(digest(raw) == 'fba9c24e191ce9c82a034c0b484a634750e3ed4c87cf8b4c8a26f6631aec98a7',
            'unchanged_consumed_parent_takeover')
    before = "require(old_spec['root'] == activation['root'], 'same_actual_parented_root')"
    after = ("require(physical in range(2, 8) and old_spec['root'] == "
             "'/localhome/local-rohing/orch_r136_a100_' + activation['label'] + "
             "'_20260916_attempt1/run1', 'same_actual_learning_parented_root')")
    source = raw.decode()
    require(source.count(before) == 1, 'single_receipt_schema_adaptation')
    exec(compile(source.replace(before, after), str(Path(__file__)), 'exec'),
         dict(__name__='__main__', __file__=str(Path(__file__).resolve())))

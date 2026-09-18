"""Transfer only the existing CPU parent to a reconciled completed-cycle clock."""

from pathlib import Path
import time

from c0_continuation_parent import main
from recover import HERE, read, require, write


if __name__ == '__main__':
    previous = HERE / 'C0_CURRICULUM_AFTER_CONTINUATION'
    successor = HERE / 'C0_CURRICULUM_CYCLE_RECONCILED'
    require(not successor.exists(), 'one_supported_CPU_writer_handoff')
    owner = read(previous / 'SERVICE.json')
    process = Path('/proc', str(owner['pid']))
    fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    require(int(fields[19]) == owner['start_ticks'] and process.stat().st_uid == 2524
        and b'c0_continuation_parent.py' in (process / 'cmdline').read_bytes(), 'exact_owned_CPU_parent')
    write(previous / 'CANCEL_CURRICULUM_SERVICE', dict(reason='Reconcile actual completed handoff cycle; no learner controls'))
    limit = time.time() + 30
    while not (previous / 'EXIT.json').exists() or process.exists():
        require(time.time() < limit, 'previous_CPU_writer_must_exit')
        time.sleep(0.2)
    main(previous, successor)

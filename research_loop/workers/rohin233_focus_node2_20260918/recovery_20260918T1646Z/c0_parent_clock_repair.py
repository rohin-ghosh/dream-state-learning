"""Transfer only the existing CPU parent to a reconciled completed-cycle clock."""

from pathlib import Path
import time

from c0_continuation_parent import main
from recover import HERE, read, require, write


def transfer(previous, successor, *, lease_capacity=False):
    require(not successor.exists(), 'one_supported_CPU_writer_handoff')
    owner = read(previous / 'SERVICE.json')
    process = Path('/proc', str(owner['pid']))
    fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    arguments = (process / 'cmdline').read_bytes().split(b'\0')
    require(int(fields[19]) == owner['start_ticks'] and process.stat().st_uid == 2524
        and any(name in arguments for name in (b'c0_continuation_parent.py', b'c0_parent_clock_repair.py'))
        and (process / 'cwd').resolve() == HERE, 'exact_owned_CPU_parent')
    write(previous / 'CANCEL_CURRICULUM_SERVICE', dict(reason='Authorized CPU parent ledger/capacity handoff; no learner controls'))
    limit = time.time() + 30
    while not (previous / 'EXIT.json').exists() or process.exists():
        require(time.time() < limit, 'previous_CPU_writer_must_exit')
        time.sleep(0.2)
    main(previous, successor, lease_capacity=lease_capacity)


if __name__ == '__main__':
    transfer(HERE / 'C0_CURRICULUM_AFTER_CONTINUATION', HERE / 'C0_CURRICULUM_CYCLE_RECONCILED')

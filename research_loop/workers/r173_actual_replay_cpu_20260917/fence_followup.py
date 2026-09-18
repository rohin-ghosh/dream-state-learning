"""Local-only non-material CPU harness repair; no launcher or receiving approval."""

import hashlib
import importlib.util
import os
from pathlib import Path
import stat


ATTEMPTED_RUNNER_SHA256 = '79f68ba20697d63aa8a80cb52956855bd5886660489dffe190c088b45e4c8637'
runner_path = Path(__file__).resolve().with_name('receiving_cpu.py')
if hashlib.sha256(runner_path.read_bytes()).hexdigest() != ATTEMPTED_RUNNER_SHA256:
    raise ValueError('preserve_exact_attempted_runner')
specification = importlib.util.spec_from_file_location('r173_attempted_runner', runner_path)
attempted = importlib.util.module_from_spec(specification)
specification.loader.exec_module(attempted)


class CpuFixtureFence(attempted.RuntimeFence):
    def __init__(self, scratch, pins):
        super().__init__(scratch, pins)
        self.special_reads.update(str(Path('/proc/self', name).resolve())
                                  for name in ('maps', 'status', 'stat'))

    def audit(self, event, arguments):
        if event == 'open':
            filename, mode, flags = arguments
            path = self.open_context[-1] if self.open_context else self.path_for(filename)
            writing = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            if flags & os.O_DIRECTORY and not writing:
                if any(root == path or path in root.parents for root in self.read_roots):
                    return
            if path == Path('/dev/null') and not flags & os.O_DIRECTORY:
                metadata = os.stat(path)
                if stat.S_ISCHR(metadata.st_mode) and os.major(metadata.st_rdev) == 1 and os.minor(metadata.st_rdev) == 3:
                    return
        if event in ('os.listdir', 'os.scandir'):
            path = self.path_for(arguments[0]) if arguments[0] is not None else Path.cwd()
            self.check_file(path, False)
        return super().audit(event, arguments)

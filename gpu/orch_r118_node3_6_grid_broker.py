"""Scoped node3 queue transport; unchanged fixed-v4 F4 Astra parent."""

import argparse
from pathlib import Path
import subprocess
from types import FunctionType

from gpu import orch_r118_a1004_grid_broker as template
from gpu import orch_r118_node3_6_grid_run as run


class Store(template.Store):
    def shell(self, script, check=True):
        return subprocess.run(['bash', str(self.repository / 'gpu/ovx2_ssh.sh'), script],
            text=True, capture_output=True, timeout=20, check=check)

    def copy(self, source, destination):
        subprocess.run(['bash', str(self.repository / 'gpu/ovx2_scp.sh'), str(source), str(destination)],
            capture_output=True, timeout=20, check=True)


serve = FunctionType(template.serve.__code__, dict(template.serve.__globals__,
                    run=run, Store=Store), 'serve', template.serve.__defaults__)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--launch-receipt', type=Path, required=True)
    parser.add_argument('--prompt-root', type=Path, required=True)
    parser.add_argument('--principles', type=Path, required=True)
    args = parser.parse_args()
    serve(args.config, args.launch_receipt, args.prompt_root, args.principles)

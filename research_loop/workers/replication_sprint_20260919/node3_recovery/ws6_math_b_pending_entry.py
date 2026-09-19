"""Original confined entry chain with a source-bound interrupted-sleep seam."""

import json
from pathlib import Path
import sys


def main():
    from gpu import orch_r125_continual_native as native
    from gpu import orch_r125_stream_journal as journal_module
    from gpu import r205_runtime as runtime
    from gpu import r226_math_runtime
    from gpu.r213_recovery_runtime import RecoveryJournal
    from gpu.r233_recovery_runtime import entrypoint
    import math_b_startup as startup

    config_path = Path(sys.argv[sys.argv.index('--config') + 1])
    config = json.loads(config_path.read_bytes())
    startup.require(config['resume'] is True, 'only_original_resume_guard')
    manifest = json.loads(startup.bound_bytes(config['pending_sleep_recovery']))
    plan_bytes = Path(config['plan_path']).read_bytes()
    unused, plan, envelope, selection = startup.validate_manifest(manifest, plan_bytes)
    startup.require(entrypoint(plan) == 'gpu.r226_math_runtime', 'same_math_entry_chain')
    original_main, original_install = runtime.main, runtime.install_runtime

    def recovered_main():
        runtime.MODULE = 'gpu.ws6_math_b_pending_entry'
        runtime.ControlJournal = RecoveryJournal
        return original_main()

    def install(execution_plan):
        original_install(execution_plan)
        from gpu.orch_r107_base_anchors_inventory import build_inventory
        from gpu import orch_r184_think_act_learn as driver
        journal_class = startup.make_journal_class(journal_module.StreamJournal, selection)
        journal_module.StreamJournal = journal_class

        def recover(plan_path, *, resume=False):
            return startup.resume(plan_path, resume=resume, manifest=manifest, native=native,
                journal_class=journal_class, build_inventory=build_inventory, run_loop=driver.run_loop)

        native.run = recover

    runtime.main, runtime.install_runtime = recovered_main, install
    r226_math_runtime.main()


if __name__ == '__main__':
    main()

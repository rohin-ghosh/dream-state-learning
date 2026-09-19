"""C0-only addition: original node2 confinement, guard, admission and driver."""

import json
from pathlib import Path
import sys


def main():
    import c0_startup as startup
    from gpu import orch_r125_continual_native as native
    from gpu import orch_r125_stream_journal as journal_module
    from gpu import r205_runtime as runtime
    from gpu import r233_node2_recovery as original_wrapper

    config_path = Path(sys.argv[sys.argv.index('--config') + 1])
    config = json.loads(config_path.read_bytes())
    manifest = json.loads(startup.bound_bytes(config['pending_sleep_recovery']))
    plan_bytes = Path(config['plan_path']).read_bytes()
    startup.validate_guard_binding(config, manifest, plan_bytes)
    unused, plan, envelope, selection = startup.validate_manifest(manifest, plan_bytes)
    original_main, original_install = runtime.main, runtime.install_runtime

    def install(execution_plan):
        original_install(execution_plan)
        from gpu import orch_r184_think_act_learn as driver
        from gpu.orch_r107_base_anchors_inventory import build_inventory
        journal_class = startup.make_journal_class(journal_module.StreamJournal, selection)
        journal_module.StreamJournal = journal_class

        def recover(plan_path, *, resume=False):
            return startup.resume(plan_path, resume=resume, manifest=manifest, native=native,
                journal_class=journal_class, build_inventory=build_inventory, run_loop=driver.run_loop)

        native.run = recover

    def recovered_main():
        startup.require(runtime.MODULE == startup.MODULE, 'same_entry_in_all_wrapper_modes')
        return original_main()

    original_wrapper.MODULE = startup.MODULE
    runtime.main, runtime.install_runtime = recovered_main, install
    original_wrapper.main()


if __name__ == '__main__':
    main()

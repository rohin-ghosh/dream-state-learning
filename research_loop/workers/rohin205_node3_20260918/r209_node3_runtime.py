"""Same-life R209 resume, retaining the tested node3 containment and treatments."""

from gpu import r205_runtime as runtime


def main():
    original_install = runtime.install_runtime

    def install_resume(plan):
        from gpu import orch_r184_think_act_learn as driver
        original_loop = driver.run_loop
        original_install(plan)
        driver.run_loop = original_loop

    runtime.MODULE = 'gpu.r209_node3_runtime'
    runtime.install_runtime = install_resume
    runtime.main()


if __name__ == '__main__':
    main()

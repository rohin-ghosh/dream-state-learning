"""Run every CPU test script with the current interpreter and print counts.

  /opt/homebrew/bin/python3.12 tests/run_all.py
  <venv with reasoning-gym>/bin/python tests/run_all.py     (for the rg tests)

Plain scripts (pytest optional): each test file prints "N/M passed".
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = [
    "test_compiler_golden.py",
    "test_gym_protocol.py",
    "test_reasoning_gym_gym.py",
    "test_clone_coordinator.py",
    "test_reflection.py",
    "test_curriculum.py",
    "test_agentic_parent_mock.py",
    # 2026-09-11 write pretest build: v3 compiler, v3 trainer (torch path
    # skips without torch/peft), SVD init, rg band, write A/B report
    "test_sleep_compile_v3.py",
    "test_train_adapter_v3.py",
    "test_lora_svd_init.py",
    "test_rg_band.py",
    "test_write_ab_report.py",
    # memory dose-response (car) test: mock model, CPU (Astra memo 2 section 2)
    "test_memory_dose.py",
    # Astra autonomous tool loop: policy allow/deny list, budgets, key masking,
    # timeouts, truncation, python guard, loopback HTTP client (no network)
    "test_astra_agent.py",
]


def main():
    total_p = total_n = 0
    rows = []
    for f in FILES:
        t0 = time.time()
        p = subprocess.run([sys.executable, os.path.join(HERE, f)],
                           capture_output=True, text=True, cwd=os.path.dirname(HERE))
        out = p.stdout + p.stderr
        m = re.findall(r"(\d+)/(\d+) passed", out)
        passed, n = (int(m[-1][0]), int(m[-1][1])) if m else (0, 0)
        skipped = "SKIP" in out
        total_p += passed
        total_n += n
        status = "OK" if p.returncode == 0 else "FAIL"
        rows.append((f, passed, n, status, round(time.time() - t0, 1), skipped))
        if p.returncode != 0:
            print(f"----- {f} output (tail) -----")
            print(out[-4000:])
    print(f"{'file':34s} {'passed':>8s} {'status':>7s} {'sec':>7s}")
    for f, passed, n, status, dt, sk in rows:
        print(f"{f:34s} {passed:>3d}/{n:<4d} {status:>7s} {dt:>7.1f}"
              + ("  (skips)" if sk else ""))
    print(f"TOTAL {total_p}/{total_n} passed; interpreter {sys.executable}")
    sys.exit(0 if all(r[3] == "OK" for r in rows) else 1)


if __name__ == "__main__":
    main()

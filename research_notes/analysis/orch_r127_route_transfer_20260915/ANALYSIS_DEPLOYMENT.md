# R127 offline verification deployment — September 15, 2026

Analysis lives separately at `/localhome/local-rohing/orch_r127_route_transfer_20260915/analysis_source` on `gpu/ovx_ssh.sh`. The running producer's frozen source, model inputs and checkpoint selection were not changed.

Pinned analysis modules:

- `gpu/orch_r127_route_transfer_results.py`: `ce308a0b9d63430e0db7cd1bd4efe0bb258a91a09875e8b709f6db11d8145ba4`
- `gpu/orch_r127_route_transfer_reduce.py`: `e39320143f9d19d4c30806e642a88dfbd202661aa95c01e60a553c79984ceea1`
- IO tests: `9f110910ad81cf23d8def998a3b2f70eb6de7b002875c661e1a12643e9b43494`

The analysis-only `gpu/__init__.py` uses `pkgutil.extend_path` to allow CPU tests to import the unchanged producer and environment from the frozen source. Its SHA256 is `a8415eab7cae7f7950295b1e00b98bf1a3ccf1fa424b9e01ff9a6bcb4d0cde19`; its complete contents are:

```python
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
```

Main independently passed 26 IO tests locally and **49 native unittest tests** (IO plus pure reducer). The initial local 10-second test command timed out, then passed with a 120-second command budget. Native pytest was absent; two following import-path attempts failed before the analysis package overlay was installed. Those failures are not counted as passing tests. No dependency installation, GPU, provider or training call occurred.

Native successful command, with `ROOT=/localhome/local-rohing/orch_r127_route_transfer_20260915`:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT/analysis_source:$ROOT/source" python3 -B -m unittest discover -s "$ROOT/analysis_source/tests" -p 'test_orch_r127_route_transfer*.py' -q
```

The first real-artifact reduction verified SOURCE and SEED/GUIDED C2/C4/C6, including 2,845 file checks, and withheld every comparison because UNPARENTED was still running. It confirms **64 accepted of 64 offered events across all 16 worlds**. `PARTIAL_2020.json` is an immutable snapshot label, not a claim about its wall-clock creation time. All raw call/episode data remains node-local.

Run the same reducer after all seven conditions exit; never filter an incomplete condition or retry an old logical inference merely to obtain a complete comparison.

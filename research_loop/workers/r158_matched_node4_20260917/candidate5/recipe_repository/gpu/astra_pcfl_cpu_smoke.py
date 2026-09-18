"""Capture one offline CPU test execution; never release scientific work."""

import argparse
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import sys
import time
import unittest


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_dependency_skip(test, reason):
    return (test.id() == "test_pcfl_vertical_train.WriterTests.test_missing_torch_preserves_failed_attempt_no_retry"
            and reason == "explicit missing-dependency path on this VM")


def run(source, output, expected_manifest):
    for name, expected in (("CUDA_VISIBLE_DEVICES", ""), ("HF_HUB_OFFLINE", "1"),
                           ("TRANSFORMERS_OFFLINE", "1"), ("ASTRA_PCFL_TINY_CPU", "1")):
        if os.environ.get(name) != expected:
            raise ValueError(f"CPU/offline environment required: {name}")
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    manifest_path = source / "cpu_source_manifest.json"
    if file_hash(manifest_path) != expected_manifest:
        raise ValueError("source manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text())
    if not isinstance(manifest, dict) or not manifest:
        raise ValueError("nonempty source manifest required")
    for relative, expected in manifest.items():
        path = (source / relative).resolve()
        if not path.is_relative_to(source.resolve()) or file_hash(path) != expected:
            raise ValueError(f"source mismatch: {relative}")
    if file_hash(Path(__file__).resolve()) != manifest["gpu/astra_pcfl_cpu_smoke.py"]:
        raise ValueError("runner not bound by source manifest")
    output.mkdir(parents=False, exist_ok=False)
    log = io.StringIO()
    started = time.time()
    sys.path.insert(0, str(source))
    try:
        import torch

        if torch.cuda.is_available():
            raise ValueError("CUDA must not be available to CPU tests")
        torch.set_num_threads(1)
        suite = unittest.defaultTestLoader.discover(
            str(source / "tests"), pattern="test_pcfl_vertical_train.py")
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
        unchanged = all(file_hash(source / relative) == expected
                        for relative, expected in manifest.items())
        unexpected_skips = [(test, reason) for test, reason in result.skipped
                            if not expected_dependency_skip(test, reason)]
        passed = result.wasSuccessful() and not unexpected_skips and unchanged and result.testsRun > len(result.skipped)
        receipt = {
            "status": "PASS" if passed else "FAIL",
            "tests_run": result.testsRun,
            "failures": len(result.failures), "errors": len(result.errors),
            "skips": [(str(test), reason) for test, reason in result.skipped],
            "unexpected_skips": [(str(test), reason) for test, reason in unexpected_skips],
            "source_unchanged": unchanged,
            "versions": {name: importlib.metadata.version(name)
                         for name in ("torch", "transformers", "peft")},
            "python": platform.python_version(),
            "cuda_available": False, "torch_threads": torch.get_num_threads(),
        }
    except Exception as error:
        receipt = {"status": "ERROR", "error_type": type(error).__name__, "error": str(error)}
    receipt.update({"started_unix": started, "elapsed_seconds": time.time() - started,
                    "source_manifest_sha256": expected_manifest,
                    "source_files": manifest,
                    "fixture_only": True, "scientific_readiness": False,
                    "pretrained_models_loaded": 0})
    (output / "tests.log").write_text(log.getvalue())
    receipt["tests_log_sha256"] = file_hash(output / "tests.log")
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": receipt["status"], "output": str(output),
                      "elapsed_seconds": receipt["elapsed_seconds"]}))
    return 0 if receipt["status"] == "PASS" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    return run(args.source, args.out, args.manifest_sha256)


if __name__ == "__main__":
    raise SystemExit(main())

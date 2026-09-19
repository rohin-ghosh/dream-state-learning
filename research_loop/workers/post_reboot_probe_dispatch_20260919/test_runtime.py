import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

import dispatch_once
import probe_runtime as runtime


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        source = dict(absolute_sleep=12, journal_id="038f85cbde5c4abfb749ea4d59da6897",
            sleep_complete_sha256="complete", adapter_state_sha256="adapter", optimizer_steps=576)
        identity = dict(journal_id=source["journal_id"], sleep_complete_sha256="complete",
            adapter_state_sha256="adapter", battery=runtime.EXPECTED_BATTERY)
        identifier = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        self.config = dict(job_id=identifier, battery=copy.deepcopy(runtime.EXPECTED_BATTERY),
            source_identity=source, root="/job/" + identifier, expected_uid=1352,
            lease_end_unix=runtime.HARD_END, lease_boundary_unix=runtime.BOUNDARY,
            max_runtime_seconds=2400, scheduled_physical=[2, 7], protected_physical=[0, 1, 3, 4, 5, 6],
            role_devices=dict(player=dict(physical=2, uuid="GPU-player"), judge=dict(physical=7, uuid="GPU-judge")))
        self.inventory = [dict(physical=2, uuid="GPU-player", memory_used_mib=0, compute_pids=[]),
            dict(physical=7, uuid="GPU-judge", memory_used_mib=0, compute_pids=[])]

    def test_parameterized_uuid_bound_two_seven_allowed_without_new_ratification(self):
        runtime.validate_config(self.config, 100)
        runtime.validate_admission(self.config, self.inventory)

    def test_overlapping_physical_or_uuid_rejected(self):
        for field in ("physical", "uuid"):
            changed = copy.deepcopy(self.config)
            changed["role_devices"]["judge"][field] = changed["role_devices"]["player"][field]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "overlapping"):
                runtime.validate_config(changed, 100)

    def test_protected_device_or_arbitrary_fallback_rejected(self):
        self.config["role_devices"]["player"]["physical"] = 4
        with self.assertRaises(ValueError):
            runtime.validate_config(self.config, 100)
        self.config["scheduled_physical"] = [4, 7]
        with self.assertRaisesRegex(ValueError, "protected"):
            runtime.validate_config(self.config, 100)

    def test_live_compute_and_nonempty_memory_rejected(self):
        for change in ({"compute_pids": [499900]}, {"memory_used_mib": 100}):
            inventory = copy.deepcopy(self.inventory)
            inventory[0].update(change)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "occupied"):
                runtime.validate_admission(self.config, inventory)

    def test_uuid_remapping_rejected(self):
        self.inventory[0]["uuid"] = "GPU-other"
        with self.assertRaisesRegex(ValueError, "uuid_mapping"):
            runtime.validate_admission(self.config, self.inventory)

    def test_other_gpu_exposure_and_cuda_mask_mismatch_rejected(self):
        proof = {str(index): dict(opened=index == 2) for index in range(8)}
        runtime.validate_confinement(2, proof, "GPU-player", "GPU-player")
        with self.assertRaises(ValueError):
            runtime.validate_confinement(2, proof, "2", "GPU-player")
        proof["4"]["opened"] = True
        with self.assertRaisesRegex(ValueError, "seven_denied"):
            runtime.validate_confinement(2, proof, "GPU-player", "GPU-player")

    def test_expired_lease_extension_and_unbounded_job_rejected(self):
        with self.assertRaises(ValueError):
            runtime.validate_config(self.config, runtime.HARD_END)
        for field in ("lease_end_unix", "max_runtime_seconds"):
            changed = copy.deepcopy(self.config)
            changed[field] += 1
            with self.subTest(field=field), self.assertRaises(ValueError):
                runtime.validate_config(changed, 100)

    def test_changed_battery_is_rejected(self):
        for field, replacement in (("total_generated_tokens", 7000), ("seeds", [1, 2]),
                                    ("game_sha256", "changed"), ("rule_digest", "changed")):
            changed = copy.deepcopy(self.config)
            changed["battery"][field] = replacement
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "battery"):
                runtime.validate_config(changed, 100)

    def test_job_id_cannot_be_changed_to_repeat_the_same_source(self):
        self.config["job_id"] = "another"
        with self.assertRaisesRegex(ValueError, "idempotent"):
            runtime.validate_config(self.config, 100)

    def test_complete_source_closure_detects_changed_and_extra_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source").mkdir()
            source = root / "source/module.py"
            source.write_text("value = 1\n")
            (root / "SOURCE_MANIFEST.json").write_text(json.dumps({"module.py": runtime.sha(source)}))
            runtime.verify_source_closure(root)
            (root / "source/unbound.py").write_text("extra\n")
            with self.assertRaisesRegex(ValueError, "closure"):
                runtime.verify_source_closure(root)
            (root / "source/unbound.py").unlink()
            source.write_text("changed\n")
            with self.assertRaisesRegex(ValueError, "source_changed"):
                runtime.verify_source_closure(root)

    def test_exact_cgroup_route_has_one_gpu_allow_and_uuid_mask(self):
        commands = dispatch_once.commands(self.config, Path("/config"), "configsha", Path("/launch"), "launchsha", 2500, 100)
        for spec in commands:
            assigned = self.config["role_devices"][spec["role"]]
            argv = spec["argv"]
            self.assertEqual(argv[:3], ["sudo", "-n", "systemd-run"])
            self.assertIn("--property=DevicePolicy=closed", argv)
            self.assertIn("--property=RuntimeMaxSec=2400", argv)
            self.assertIn("--setenv=CUDA_VISIBLE_DEVICES=" + assigned["uuid"], argv)
            physical_rules = [value for value in argv if value.startswith("--property=DeviceAllow=/dev/nvidia")
                and value.removeprefix("--property=DeviceAllow=/dev/nvidia").split()[0].isdigit()]
            self.assertEqual(physical_rules, ["--property=DeviceAllow=/dev/nvidia" + str(assigned["physical"]) + " rw"])

    def test_platform_denial_is_terminal_no_alternate_or_retry(self):
        runner = Mock(return_value=Mock(returncode=1))
        with self.assertRaisesRegex(RuntimeError, "TERMINAL_NO_FALLBACK"):
            dispatch_once.submit(["sudo", "-n", "systemd-run"], runner=runner)
        runner.assert_called_once()

    def test_existing_launch_or_player_state_never_replayed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "runtime").mkdir()
            config = dict(self.config, condition="R233_TEST")
            runtime.verify_no_attempt(root, config)
            (root / "runtime/LAUNCH.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "never_replayed"):
                runtime.verify_no_attempt(root, config)


if __name__ == "__main__":
    unittest.main()

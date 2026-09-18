import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from gpu.replay_q1_map_dynamics import branch_choice_counts, collect_prefixes, load_archive


class ArchiveReplayTests(unittest.TestCase):
    def test_tie_conventions_are_explicit_and_not_generation(self):
        result = branch_choice_counts([0., -1., -1., 1.], [-1., 0., 1., 0.])
        self.assertEqual(result["strict_positive_signed_margin_both"], 1)
        self.assertEqual(result["argmax_tie_to_mem2reg_both"], 3)
        self.assertEqual(result["argmax_tie_to_gvn_both"], 2)
        self.assertEqual(result["either_arm_zero_margin"], 3)
        self.assertEqual(result["total"], 4)
        self.assertIn("not a new gate", result["interpretation"])

    def make_archive(self, directory, extra=None):
        values = {"manifest.json": {}, "prepared.json": {}, "reduction.json": {}}
        files = {name: json.dumps(value).encode() for name, value in values.items()}
        files["SEAL.json"] = json.dumps({"files": {
            name: hashlib.sha256(content).hexdigest() for name, content in files.items()
        }}).encode()
        files["FINALIZED.json"] = json.dumps({
            "seal_sha256": hashlib.sha256(files["SEAL.json"]).hexdigest()
        }).encode()
        path = Path(directory) / "source.tar"
        prefix = "q0_fulldose_R0_20260913_attempt1/"
        with tarfile.open(path, "w") as archive:
            root = tarfile.TarInfo(prefix)
            root.type = tarfile.DIRTYPE
            archive.addfile(root)
            for name, content in files.items():
                member = tarfile.TarInfo(prefix + name)
                member.size = len(content)
                archive.addfile(member, io.BytesIO(content))
            if extra is not None:
                archive.addfile(extra)
        stream = "".join(f"{hashlib.sha256(files[name]).hexdigest()}  ./{name}\n"
                         for name in sorted(files)).encode()
        return path, len(files), hashlib.sha256(stream).hexdigest()

    def test_readonly_regular_archive_and_pinned_stream(self):
        with tempfile.TemporaryDirectory() as directory:
            path, count, digest = self.make_archive(directory)
            before = path.read_bytes()
            selected, hashes = load_archive(path, "R0", count, digest)
            self.assertEqual(set(selected), set(hashes))
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(Path(directory).iterdir()), [path])
            with self.assertRaisesRegex(ValueError, "digest differs"):
                load_archive(path, "R0", count, "0" * 64)
            with self.assertRaisesRegex(ValueError, "count differs"):
                load_archive(path, "R0", count + 1, digest)

    def test_links_rejected_without_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            extra = tarfile.TarInfo("q0_fulldose_R0_20260913_attempt1/link")
            extra.type = tarfile.SYMTYPE
            extra.linkname = "/outside"
            path, count, digest = self.make_archive(directory, extra)
            with self.assertRaisesRegex(ValueError, "non-regular"):
                load_archive(path, "R0", count, digest)

    def test_prefix_integrity_and_missing_not_zero(self):
        event = dict(state="OFF", snapshot=0, material_sha256="bound", attempts=1,
                     operation="prefix", row_id="row", output=dict(d=2., z0=3., z1=1., q=.8, M=.9))
        selected = {"stages/stage/events/0000_readout.json": event}
        self.assertEqual(collect_prefixes(selected, "stage", ["row"], "OFF", 0, "bound"),
                         [event["output"]])
        with self.assertRaisesRegex(ValueError, "incomplete"):
            collect_prefixes({}, "stage", ["row"], "OFF", 0, "bound")
        with self.assertRaisesRegex(ValueError, "state/checkpoint"):
            collect_prefixes(selected, "stage", ["row"], "OFF", 1, "bound")
        with self.assertRaisesRegex(ValueError, "material/attempt"):
            collect_prefixes(selected, "stage", ["row"], "OFF", 0, "other")
        event["output"]["d"] = 1.
        with self.assertRaisesRegex(ValueError, "primitives"):
            collect_prefixes(selected, "stage", ["row"], "OFF", 0, "bound")


if __name__ == "__main__":
    unittest.main()

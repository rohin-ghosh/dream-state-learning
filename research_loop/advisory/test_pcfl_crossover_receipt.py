from __future__ import annotations

import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pcfl_crossover_receipt as receipt  # noqa: E402


def write_container(path: Path, header: dict, data_bytes: int) -> None:
    raw = json.dumps(header, separators=(",", ":")).encode("utf-8")
    path.write_bytes(struct.pack("<Q", len(raw)) + raw + bytes(data_bytes))


def valid_header(layers: int = 1, rank: int = 1) -> tuple[dict, int]:
    header: dict = {"__metadata__": {"format": "pt"}}
    offset = 0
    for layer in range(layers):
        for module in sorted(receipt.EXPECTED_MODULES):
            input_size = 18_944 if module == "down_proj" else 3_584
            if module in {"k_proj", "v_proj"}:
                output_size = 512
            elif module in {"gate_proj", "up_proj"}:
                output_size = 18_944
            else:
                output_size = 3_584
            branch = receipt.MODULE_BRANCH[module]
            for side, shape in (
                ("A", [rank, input_size]),
                ("B", [output_size, rank]),
            ):
                size = receipt.product(shape) * 4
                name = (
                    "base_model.model.model.layers."
                    f"{layer}.{branch}.{module}.lora_{side}.weight"
                )
                header[name] = {
                    "dtype": "F32",
                    "shape": shape,
                    "data_offsets": [offset, offset + size],
                }
                offset += size
    return header, offset


class ExactRateTests(unittest.TestCase):
    def test_strict_half_boundary(self) -> None:
        self.assertEqual(receipt.strict_denominator_min(80_792_096, 1, 2), 161_584_193)

    def test_strict_seven_twentieths_boundary(self) -> None:
        self.assertEqual(receipt.strict_denominator_min(80_792_096, 7, 20), 230_834_561)


class SafetensorsValidationTests(unittest.TestCase):
    def inspect(self, path: Path, rank: int = 1) -> dict:
        return receipt.inspect_adapter(
            path, 16_384, False, 1, rank, "F32", 3_584, 512, 18_944
        )

    def test_valid_complete_partition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "adapter_model.safetensors"
            header, data_bytes = valid_header()
            write_container(path, header, data_bytes)
            result = self.inspect(path)
            self.assertEqual(result["tensor_count"], 14)
            self.assertEqual(result["tensor_payload_bytes"], data_bytes)
            self.assertEqual(result["rank_candidates"], [1])

    def test_rejects_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "adapter_model.safetensors"
            header, data_bytes = valid_header()
            names = [name for name in header if name != "__metadata__"]
            header[names[1]]["data_offsets"] = [
                value - 4 for value in header[names[1]]["data_offsets"]
            ]
            write_container(path, header, data_bytes)
            with self.assertRaisesRegex(ValueError, "overlap"):
                self.inspect(path)

    def test_rejects_leading_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "adapter_model.safetensors"
            header, data_bytes = valid_header()
            for name, spec in header.items():
                if name != "__metadata__":
                    spec["data_offsets"] = [value + 4 for value in spec["data_offsets"]]
            write_container(path, header, data_bytes + 4)
            with self.assertRaisesRegex(ValueError, "gap"):
                self.inspect(path)

    def test_rejects_negative_interval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "adapter_model.safetensors"
            header, data_bytes = valid_header()
            name = next(name for name in header if name != "__metadata__")
            header[name]["data_offsets"] = [-4, 0]
            write_container(path, header, data_bytes)
            with self.assertRaisesRegex(ValueError, "negative"):
                self.inspect(path)

    def test_rejects_unexpected_tensor_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "adapter_model.safetensors"
            header, data_bytes = valid_header()
            name = next(name for name in header if name != "__metadata__")
            header["unexpected.weight"] = header.pop(name)
            write_container(path, header, data_bytes)
            with self.assertRaisesRegex(ValueError, "unexpected tensor namespace"):
                self.inspect(path)

    def test_rejects_wrong_expected_rank(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "adapter_model.safetensors"
            header, data_bytes = valid_header(rank=2)
            write_container(path, header, data_bytes)
            with self.assertRaisesRegex(ValueError, "expected rank 1"):
                self.inspect(path, rank=1)

    def test_rejects_tiny_dimensionally_fake_carrier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "adapter_model.safetensors"
            header, _ = valid_header()
            offset = 0
            for name, spec in header.items():
                if name == "__metadata__":
                    continue
                spec["shape"] = [1, 1]
                spec["data_offsets"] = [offset, offset + 4]
                offset += 4
            write_container(path, header, offset)
            with self.assertRaisesRegex(ValueError, "wrong Qwen projection shape"):
                self.inspect(path)

    def test_rejects_near_miss_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "adapter_model.safetensors"
            header, data_bytes = valid_header()
            name = next(name for name in header if name != "__metadata__")
            header[name.replace("base_model.model.model", "alien")] = header.pop(name)
            write_container(path, header, data_bytes)
            with self.assertRaisesRegex(ValueError, "unexpected tensor namespace"):
                self.inspect(path)

    def test_rejects_zero_padded_layer_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "adapter_model.safetensors"
            header, data_bytes = valid_header()
            renamed = {}
            for name, spec in header.items():
                renamed[name.replace(".layers.0.", ".layers.00.")] = spec
            write_container(path, renamed, data_bytes)
            with self.assertRaisesRegex(ValueError, "unexpected tensor namespace"):
                self.inspect(path)

    def test_rejects_wrong_projection_dimension(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "adapter_model.safetensors"
            header, data_bytes = valid_header()
            name = next(name for name in header if ".q_proj.lora_A." in name)
            old_start, old_end = header[name]["data_offsets"]
            header[name]["shape"] = [1, 3_583]
            header[name]["data_offsets"] = [old_start, old_end - 4]
            for other, spec in header.items():
                if other != "__metadata__" and spec["data_offsets"][0] >= old_end:
                    spec["data_offsets"] = [value - 4 for value in spec["data_offsets"]]
            write_container(path, header, data_bytes - 4)
            with self.assertRaisesRegex(ValueError, "wrong Qwen projection shape"):
                self.inspect(path)

    def test_rejects_duplicate_json_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "adapter_model.safetensors"
            raw = b'{"duplicate":{},"duplicate":{}}'
            path.write_bytes(struct.pack("<Q", len(raw)) + raw)
            with self.assertRaisesRegex(ValueError, "duplicate JSON object key"):
                self.inspect(path)


if __name__ == "__main__":
    unittest.main()

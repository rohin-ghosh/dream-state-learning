"""Prospective disposable OLD formatting scaffold; not learned serialization."""

from pathlib import Path

from gpu import astra_pcfl_native_actor as native


POLICY = "pcfl.disposable_old.format_only_terminal_lf.v1"
REGEX = r"[^\r\n]+\n"
COMMITMENT_IDS = frozenset(f"old/formation/{index:02d}"
                           for index in (*range(1, 16, 2), *range(16, 20)))


def sampling_for(request, limits):
    sampling = {**native.SAMPLING, "seed": request["seed"], "max_tokens": limits["output_tokens"]}
    if request["id"] in COMMITMENT_IDS:
        sampling["structured_outputs"] = {"regex": REGEX}
    return sampling


class LFNativeActor(native.NativeActor):
    def _validate_config(self):
        super()._validate_config()
        native.require(str(Path(__file__).resolve()) in self._config["source_files"],
                       "pin actually imported LF actor source")

    def _sampling(self, request, limits):
        return sampling_for(request, limits)

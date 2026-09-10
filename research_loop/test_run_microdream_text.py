"""CPU-only tests for the model-facing recurrent microdream text CLI."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from research_loop.microdream_world import export_rows
from research_loop.microdream_runner import run_recurrent_life
from research_loop.microdream_contract import audit_trace
from research_loop.run_microdream_text import (
    DEFAULT_MODEL,
    DEFAULT_REVISION,
    TextRunConfig,
    _backend_generate,
    _reconcile_backend_calls,
    _sha256_canonical,
    _verify_bundle_binding,
    run_text_dev,
)


class FakeBackend:
    def __init__(self, outputs, usages):
        self.outputs = iter(outputs)
        self.usages = iter(usages)
        self.last_usage = []
        self.calls = []

    def generate(self, prompts, *, max_tokens, temperature, seed):
        assert len(prompts) == 1
        self.calls.append({
            "prompt": prompts[0],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "seed": seed,
        })
        self.last_usage = [next(self.usages)]
        return [next(self.outputs)]


def _public_export(seed: int, skin: str):
    return export_rows(
        (
            "[obs_0 | episode_0] During episode zero, state-token crimson.",
            "[obs_1 | episode_1] During episode one, state-token azure.",
        ),
        world_seed=seed,
        skin=skin,
        life_tag=f"test-life-{seed}-{skin}",
    )


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_sha(value):
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def _exact_usage(prompt_ids, output_ids, output, *, source="model"):
    return {
        "prompt_tokens": len(prompt_ids),
        "output_tokens": len(output_ids),
        "original_prompt_tokens": len(prompt_ids),
        "prompt_truncated": False,
        "source": source,
        "prompt_token_ids_sha256": _canonical_sha(prompt_ids),
        "supplied_prompt_token_ids_sha256": _canonical_sha(prompt_ids),
        "output_token_ids": output_ids,
        "output_token_ids_sha256": _canonical_sha(output_ids),
        "decoded_output": output,
        "decoded_output_sha256": _canonical_sha(output),
        "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
    }


def _self_check_revision_trace():
    public = _public_export(19, "aligned")
    add = (
        "ADD | KIND=similarity | LEFT=crimson | RELATION=shows | RIGHT=pattern | "
        "CLAIM=one local public connection | CITES=episode_0 | "
        "PREDICTION=NONE | CONFIDENCE=0.8"
    )
    revise = (
        "REVISE | KIND=causal | LEFT=crimson | RELATION=shows | RIGHT=pattern | "
        "CLAIM=one corrected local public connection | CITES=episode_1,node_00000 | "
        "PREDICTION=NONE | CONFIDENCE=0.8 | SUPERSEDES=node_00000"
    )
    supported_first = (
        "VERDICT=SUPPORTED | REASON=public material supports it | CITES=episode_0"
    )
    supported_revision = (
        "VERDICT=SUPPORTED | REASON=cited material supports revision | "
        "CITES=episode_1,node_00000"
    )
    outputs = [add, supported_first, revise, supported_revision]
    backend = FakeBackend(
        outputs,
        [_exact_usage([index], [index + 10], output)
         for index, output in enumerate(outputs, start=1)],
    )
    result = run_recurrent_life(
        public, _backend_generate(backend), condition="self_check_no_drift",
        split="dev", split_id="self-check-binding", max_tokens=9,
        temperature=0.0, seed=19, retrieval_limit=2, reactivate_every=2,
    )
    trace = result["trace"]
    digest = _sha256_canonical(public)
    trace["public_export_sha256"] = digest
    _verify_bundle_binding(public, trace, digest)
    return public, trace, digest


def _rewrite_self_check_prompt(event, replacement):
    old_prompt = event["self_check_call"]["prompt"]
    assert old_prompt != replacement
    event["self_check_call"]["prompt"] = replacement
    event["self_check_call"]["prompt_sha256"] = hashlib.sha256(
        replacement.encode("utf-8")
    ).hexdigest()
    event["self_check_prompt"] = replacement
    event["self_check_prompt_sha256"] = hashlib.sha256(
        replacement.encode("utf-8")
    ).hexdigest()


def _rehash_public_lifetime(public):
    rows = []
    for episode in public["episodes"]:
        for row in episode["rows"]:
            row["row_sha256"] = hashlib.sha256(row["row"].encode("utf-8")).hexdigest()
            rows.append(row)
        episode["episode_sha256"] = _canonical_sha(episode["rows"])
    public["life"]["row_hashes"] = [row["row_sha256"] for row in rows]
    public["life"]["life_sha256"] = _canonical_sha([
        {key: row[key] for key in ("row_id", "episode_id", "row", "row_sha256")}
        for row in rows
    ])


def _rewrite_proposal_prompt(cycle, replacement):
    cycle["model_prompt"] = replacement
    cycle["model_prompt_sha256"] = hashlib.sha256(replacement.encode("utf-8")).hexdigest()
    cycle["proposal_call"]["prompt"] = replacement
    cycle["proposal_call"]["prompt_sha256"] = hashlib.sha256(
        replacement.encode("utf-8")
    ).hexdigest()


def test_exactly_one_prompt_returns_exact_backend_usage():
    exact = _exact_usage([1, 2, 3], [9], "PASS")
    backend = FakeBackend(["PASS"], [exact])
    generate = _backend_generate(backend)
    text, usage = generate("public prompt", 19, 0.2, 37)
    assert text == "PASS"
    assert usage == exact
    assert backend.calls == [{
        "prompt": "public prompt",
        "max_tokens": 19,
        "temperature": 0.2,
        "seed": 37,
    }]


def test_missing_truncated_or_fallback_usage_is_refused():
    class BadUsageBackend:
        last_usage = []

        def generate(self, prompts, *, max_tokens, temperature, seed):
            return ["PASS"]

    try:
        _backend_generate(BadUsageBackend())("p", 1, 0.0, 0)
    except RuntimeError as exc:
        assert "exactly one exact usage" in str(exc)
    else:
        raise AssertionError("backend without exact usage was accepted")

    for invalid in (
        {"prompt_tokens": 1},
        {**_exact_usage([1], [2], "PASS"), "prompt_truncated": True},
        {**_exact_usage([1], [2], "PASS"), "source": "fallback"},
    ):
        try:
            _backend_generate(FakeBackend(["PASS"], [invalid]))("p", 1, 0.0, 0)
        except RuntimeError as exc:
            assert "exact usage" in str(exc)
        else:
            raise AssertionError("non-exact usage was accepted")


def test_text_run_uses_only_public_export_and_writes_atomic_audit_bundle():
    with TemporaryDirectory() as temporary:
        output = Path(temporary) / "text-dev-artifact"
        backend = FakeBackend(
            ["PASS", "PASS"],
            [
                _exact_usage(list(range(10)), [1], "PASS"),
                _exact_usage(list(range(11)), [1], "PASS"),
            ],
        )
        config = TextRunConfig(
            output_dir=output,
            backend="vllm",
            model=DEFAULT_MODEL,
            revision=DEFAULT_REVISION,
            condition="no_gate_no_drift",
            seed=13,
            skin="aligned",
            split="dev",
            split_id="text-cli-test",
            max_output_tokens=73,
            temperature=0.0,
            retrieval_limit=2,
            reactivate_every=1,
            max_model_len=4096,
            gpu_util=0.5,
        )
        published = run_text_dev(config, backend=backend, exporter=_public_export)
        assert published == output.resolve()
        assert sorted(path.name for path in output.iterdir()) == [
            "contract_audit.json",
            "corpus_manifest.json",
            "episodes.jsonl",
            "microdreams.jsonl",
            "public_episodes.json",
            "public_export.json",
            "run_manifest.json",
            "sha256s.json",
            "trace.json",
        ]

        public = _load(output / "public_export.json")
        episodes = _load(output / "public_episodes.json")
        trace = _load(output / "trace.json")
        contract_audit = _load(output / "contract_audit.json")
        manifest = _load(output / "run_manifest.json")
        hashes = _load(output / "sha256s.json")
        assert episodes["episodes"] == public["episodes"]
        assert trace["memory_mode"] == "none"
        assert trace["memory_adapter_id"] is None
        assert trace["world_id"] == public["world_id"]
        assert trace["skin_id"] == public["skin_id"]
        assert len(backend.calls) == len(public["episodes"]) == 2
        assert all(call["max_tokens"] == 73 for call in backend.calls)
        assert backend.calls[0]["seed"] == 13
        assert backend.calls[1]["seed"] == 14
        assert "crimson" in backend.calls[0]["prompt"]
        assert "azure" in backend.calls[1]["prompt"]

        assert manifest["model"] == {
            "backend": "vllm",
            "name": DEFAULT_MODEL,
            "revision": DEFAULT_REVISION,
            "pinned": True,
        }
        assert manifest["offline_scoring"] is False
        assert trace["public_export_sha256"] == manifest["public_export_sha256"]
        assert trace["public_export_sha256"] == _canonical_sha(public)
        assert contract_audit["valid"] is True
        assert manifest["public_export_only"] is True
        assert manifest["memory_mode"] == "text_only_no_lora"
        assert manifest["budgets"]["max_output_tokens_per_call"] == 73
        assert manifest["arguments"]["condition"] == "no_gate_no_drift"

        assert hashes["algorithm"] == "sha256"
        assert set(hashes["files"]) == {
            "contract_audit.json", "corpus_manifest.json", "episodes.jsonl", "microdreams.jsonl",
            "public_episodes.json", "public_export.json",
            "run_manifest.json", "trace.json",
        }
        for name, expected in hashes["files"].items():
            assert hashlib.sha256((output / name).read_bytes()).hexdigest() == expected

        episode_rows = (output / "episodes.jsonl").read_text(encoding="utf-8").splitlines()
        assert len(episode_rows) == 2
        assert all(json.loads(row)["episode"] == public["episodes"][index]
                   for index, row in enumerate(episode_rows))
        microdream_rows = (output / "microdreams.jsonl").read_text(encoding="utf-8").splitlines()
        assert len(microdream_rows) == len(trace["cycles"])
        microdreams = [json.loads(row) for row in microdream_rows]
        assert all(row["events"] is not None for row in microdreams)
        assert [
            generation["call_id"]
            for row in microdreams for generation in row["generations"]
        ] == [
            call_id for cycle in trace["cycles"] for call_id in cycle["model_call_ids"]
        ]
        assert microdreams[0]["generations"][0]["usage"] == _exact_usage(
            list(range(10)), [1], "PASS"
        )
        assert microdream_rows[0] == json.dumps(
            microdreams[0], ensure_ascii=True, sort_keys=True, separators=(",", ":")
        )
        corpus_manifest = _load(output / "corpus_manifest.json")
        assert corpus_manifest["corpus"] is None
        assert corpus_manifest["lines"] == []

        assert not list(Path(temporary).glob(".text-dev-artifact.staging-*"))


def test_backend_call_reconciliation_rejects_missing_reordered_or_rewritten_calls():
    public = _public_export(17, "aligned")
    outputs = ["PASS", "PASS"]
    backend = FakeBackend(outputs, [
        _exact_usage([1], [11], outputs[0]),
        _exact_usage([2], [12], outputs[1]),
    ])
    generate = _backend_generate(backend)
    result = run_recurrent_life(
        public, generate, condition="no_gate_no_drift", split="dev",
        split_id="backend-reconcile", seed=17,
    )
    exact_calls = generate.exact_calls
    reconciled = _reconcile_backend_calls(result["trace"], exact_calls)
    assert list(reconciled) == ["call_00000", "call_00001"]

    try:
        _reconcile_backend_calls(result["trace"], exact_calls[:-1])
    except RuntimeError as exc:
        assert "call count" in str(exc)
    else:
        raise AssertionError("missing backend call was accepted")

    reordered = list(reversed(exact_calls))
    try:
        _reconcile_backend_calls(result["trace"], reordered)
    except RuntimeError as exc:
        assert "execution index" in str(exc) or "differs" in str(exc)
    else:
        raise AssertionError("reordered backend calls were accepted")

    rewritten = deepcopy(result["trace"])
    rewritten["model_calls"][0]["output"] = "different output"
    try:
        _reconcile_backend_calls(rewritten, exact_calls)
    except RuntimeError as exc:
        assert "output differs" in str(exc)
    else:
        raise AssertionError("rewritten trace call was accepted")


def test_publisher_rejects_result_corpus_different_from_audited_trace_corpus():
    with TemporaryDirectory() as temporary:
        add = (
            "ADD | KIND=similarity | LEFT=crimson | RELATION=shows | RIGHT=pattern | "
            "CLAIM=one local public connection | CITES=episode_0 | "
            "PREDICTION=NONE | CONFIDENCE=0.8"
        )
        backend = FakeBackend(
            [add, "PASS"], [
                _exact_usage([1], [10], add),
                _exact_usage([2], [11], "PASS"),
            ],
        )

        def mismatched_runner(world, generate, **kwargs):
            result = run_recurrent_life(world, generate, **kwargs)
            result["corpus"] = deepcopy(result["corpus"])
            result["corpus"]["lines"][0]["text"] = "rewritten corpus line"
            return result

        try:
            run_text_dev(
                TextRunConfig(
                    output_dir=Path(temporary) / "mismatched-corpus",
                    condition="no_gate_no_drift", seed=3, skin="aligned",
                ),
                backend=backend, exporter=_public_export, runner=mismatched_runner,
            )
        except RuntimeError as exc:
            assert "result corpus differs" in str(exc)
        else:
            raise AssertionError("result/trace corpus mismatch was published")


def test_status_reassignment_attack_fails_audit_and_atomic_publication():
    """A later self-check cannot be reassigned to an earlier unresolved node.

    This is the exact locked-review attack: cycle 0 creates node_00000 and
    labels it UNRESOLVED; cycle 1 creates node_00001 and labels it SUPPORTED.
    Repointing only cycle 1's STATUS_CHANGE (plus its append predecessor
    status) at node_00000 used to leave all calls untouched while the corpus
    still serialized node_00001. Both the deterministic audit and publisher
    must now fail closed.
    """
    add_first = (
        "ADD | KIND=similarity | LEFT=crimson | RELATION=shows | RIGHT=pattern | "
        "CLAIM=one local public connection | CITES=episode_0 | "
        "PREDICTION=NONE | CONFIDENCE=0.8"
    )
    unresolved_first = (
        "VERDICT=UNRESOLVED | REASON=one row is insufficient | CITES=episode_0"
    )
    add_second = (
        "ADD | KIND=difference | LEFT=azure | RELATION=marks | RIGHT=clue | "
        "CLAIM=a second local public connection | CITES=episode_1 | "
        "PREDICTION=NONE | CONFIDENCE=0.8"
    )
    supported_second = (
        "VERDICT=SUPPORTED | REASON=the public row states this | CITES=episode_1"
    )
    outputs = [add_first, unresolved_first, add_second, supported_second]
    observed = {}

    def attacked_runner(world, generate, **kwargs):
        result = run_recurrent_life(world, generate, **kwargs)
        assert result["corpus"]["lines"][0]["node_ids"] == ["node_00001"]
        later_status = next(
            event for event in result["trace"]["events"]
            if event["cycle_index"] == 1 and event["type"] == "STATUS_CHANGE"
        )
        later_status["node_id"] = "node_00000"
        later_status["previous_status"] = "unresolved"
        audit = audit_trace(result["trace"])
        observed["audit"] = audit
        assert audit["valid"] is False
        assert any(
            "STATUS_CHANGE node_id must equal the sole node" in error
            for error in audit["errors"]
        )
        assert any(
            "not condition-eligible" in error or "canonical node-creation/status" in error
            for error in audit["errors"]
        )
        return result

    with TemporaryDirectory() as temporary:
        output = Path(temporary) / "status-reassignment"
        backend = FakeBackend(
            outputs,
            [_exact_usage([index], [index + 20], value)
             for index, value in enumerate(outputs, start=1)],
        )
        try:
            run_text_dev(
                TextRunConfig(
                    output_dir=output, condition="self_check_no_drift",
                    seed=3, skin="aligned",
                ),
                backend=backend, exporter=_public_export, runner=attacked_runner,
            )
        except RuntimeError as exc:
            assert "contract audit" in str(exc)
        else:
            raise AssertionError("status-reassigned corpus was published")
        assert observed["audit"]["valid"] is False
        assert not output.exists()


def test_invalid_self_check_cannot_be_rewritten_into_status_and_corpus():
    """The exact invalid verdict bytes cannot be promoted after the runner."""
    add = (
        "ADD | KIND=similarity | LEFT=crimson | RELATION=shows | RIGHT=pattern | "
        "CLAIM=one local public connection | CITES=episode_0 | "
        "PREDICTION=NONE | CONFIDENCE=0.8"
    )
    # ghost_node was neither cited by the proposal nor present in the rendered
    # self-check material. The live runner correctly leaves the node provisional.
    invalid_check = (
        "VERDICT=SUPPORTED | REASON=the absent memory supports it | CITES=ghost_node"
    )
    outputs = [add, invalid_check, "PASS"]
    observed = {}

    def attacked_runner(world, generate, **kwargs):
        result = run_recurrent_life(world, generate, **kwargs)
        trace = result["trace"]
        cycle = trace["cycles"][0]
        operation = cycle["operation"]
        assert operation["self_check_parse_error"]
        assert trace["corpus"] is None
        check_call = operation.pop("self_check_call")
        check_prompt = operation.pop("self_check_prompt")
        check_prompt_hash = operation.pop("self_check_prompt_sha256")
        check_raw = operation.pop("self_check_raw_completion")
        operation.pop("self_check_parse_error")
        creation = trace["events"][0]
        status = {
            "world_id": trace["world_id"], "skin_id": trace["skin_id"],
            "life_id": trace["life_id"], "event_id": "event_00001",
            "event_index": 1, "prev_event_id": creation["event_id"],
            "cycle_index": 0, "microdream_index": 0,
            "trigger": deepcopy(cycle["trigger"]), "type": "STATUS_CHANGE",
            "operation": "SELF_CHECK", "node_id": creation["node_id"],
            "previous_status": "provisional", "status": "supported",
            "reason": "the absent memory supports it",
            "self_check_raw_completion": check_raw,
            "self_check_call": check_call, "self_check_prompt": check_prompt,
            "self_check_prompt_sha256": check_prompt_hash,
            "prompt_tokens": check_call["usage"]["prompt_tokens"],
            "output_tokens": check_call["usage"]["output_tokens"],
            "cited_episode_ids": [], "cited_experience_ids": [],
            "cited_node_ids": ["ghost_node"], "retrieved_node_ids": [],
            "model_visible": True,
        }
        trace["events"].append(status)
        cycle["event_ids"].append(status["event_id"])
        line = {
            "world_id": trace["world_id"], "skin_id": trace["skin_id"],
            "life_id": trace["life_id"], "line_id": "line_00000",
            "text": "crimson shows pattern.",
            "edge": ["similarity", "crimson", "shows", "pattern"],
            "claim_kind": "similarity", "rendering": "canonical_atomic_v0",
            "paraphrase_index": 0, "exposure_count": 1,
            "node_ids": [creation["node_id"]], "model_visible": True,
            "provenance": {
                "world_id": trace["world_id"], "skin_id": trace["skin_id"],
                "life_id": trace["life_id"],
                "event_ids": [creation["event_id"], status["event_id"]],
            },
        }
        corpus = {
            "schema_version": trace["schema_version"],
            "world_id": trace["world_id"], "skin_id": trace["skin_id"],
            "life_id": trace["life_id"], "lines": [line],
        }
        trace["corpus"] = corpus
        result["corpus"] = corpus
        observed["audit"] = audit_trace(trace)
        assert observed["audit"]["valid"] is False
        assert any(
            "absent from its bound evidence prompt" in error
            for error in observed["audit"]["errors"]
        )
        return result

    with TemporaryDirectory() as temporary:
        output = Path(temporary) / "forged-self-check"
        backend = FakeBackend(
            outputs,
            [_exact_usage([index], [index + 30], value)
             for index, value in enumerate(outputs, start=1)],
        )
        try:
            run_text_dev(
                TextRunConfig(
                    output_dir=output, condition="self_check_no_drift",
                    seed=3, skin="aligned",
                ),
                backend=backend, exporter=_public_export, runner=attacked_runner,
            )
        except RuntimeError as exc:
            assert "invalid self-check" in str(exc) or "contract audit" in str(exc)
        else:
            raise AssertionError("invalid self-check was promoted and published")
        assert observed["audit"]["valid"] is False
        assert not output.exists()


def test_runner_malformed_public_bundle_cannot_be_rewritten_as_add():
    """Syntax parsing cannot override the runner's full semantic classifier."""
    packed = (
        "ADD | KIND=similarity | LEFT=crimsonazure | RELATION=shows | RIGHT=pattern | "
        "CLAIM=two public atoms are packed into one endpoint | CITES=episode_1 | "
        "PREDICTION=NONE | CONFIDENCE=0.8"
    )
    outputs = ["PASS", packed]
    observed = {}

    def attacked_runner(world, generate, **kwargs):
        result = run_recurrent_life(world, generate, **kwargs)
        trace = result["trace"]
        cycle = trace["cycles"][1]
        operation = cycle["operation"]
        assert operation["kind"] == "MALFORMED"
        operation.clear()
        operation.update({
            "op_id": "op_00001", "model_visible": True, "kind": "ADD",
            "raw_completion": packed, "claim_kind": "similarity",
            "left": "crimsonazure", "relation": "shows", "right": "pattern",
            "edge": ["similarity", "crimsonazure", "shows", "pattern"],
            "claim": "two public atoms are packed into one endpoint",
            "prediction": "NONE", "confidence": 0.8,
            "cited_episode_ids": ["episode_1"], "cited_experience_ids": [],
            "cited_node_ids": [], "supersedes": [],
        })
        event = {
            "world_id": trace["world_id"], "skin_id": trace["skin_id"],
            "life_id": trace["life_id"], "event_id": "event_00000",
            "event_index": 0, "prev_event_id": None,
            "cycle_index": 1, "microdream_index": 1,
            "trigger": deepcopy(cycle["trigger"]), "type": "ADD_NODE",
            "operation": "ADD", "node_id": "node_00000",
            "claim": operation["claim"], "claim_kind": "similarity",
            "left": "crimsonazure", "relation": "shows", "right": "pattern",
            "edge": ["similarity", "crimsonazure", "shows", "pattern"],
            "prediction": "NONE", "raw_completion": packed,
            "prompt_tokens": cycle["proposal_call"]["usage"]["prompt_tokens"],
            "output_tokens": cycle["proposal_call"]["usage"]["output_tokens"],
            "confidence": 0.8, "status": "provisional", "supersedes": [],
            "cited_episode_ids": ["episode_1"], "cited_experience_ids": [],
            "cited_node_ids": [], "retrieved_node_ids": [], "depth": 1,
            "model_visible": True,
        }
        trace["events"] = [event]
        cycle["event_ids"] = [event["event_id"]]
        line = {
            "world_id": trace["world_id"], "skin_id": trace["skin_id"],
            "life_id": trace["life_id"], "line_id": "line_00000",
            "text": "crimsonazure shows pattern.",
            "edge": list(event["edge"]), "claim_kind": "similarity",
            "rendering": "canonical_atomic_v0", "paraphrase_index": 0,
            "exposure_count": 1, "node_ids": [event["node_id"]],
            "model_visible": True,
            "provenance": {
                "world_id": trace["world_id"], "skin_id": trace["skin_id"],
                "life_id": trace["life_id"], "event_ids": [event["event_id"]],
            },
        }
        corpus = {
            "schema_version": trace["schema_version"],
            "world_id": trace["world_id"], "skin_id": trace["skin_id"],
            "life_id": trace["life_id"], "lines": [line],
        }
        trace["corpus"] = corpus
        result["corpus"] = corpus
        observed["audit"] = audit_trace(trace)
        assert observed["audit"]["valid"] is False
        assert any(
            "complete runner classification is MALFORMED" in error
            for error in observed["audit"]["errors"]
        )
        return result

    with TemporaryDirectory() as temporary:
        output = Path(temporary) / "forged-packed-add"
        backend = FakeBackend(
            outputs,
            [_exact_usage([index], [index + 40], value)
             for index, value in enumerate(outputs, start=1)],
        )
        try:
            run_text_dev(
                TextRunConfig(
                    output_dir=output, condition="no_gate_no_drift",
                    seed=3, skin="aligned",
                ),
                backend=backend, exporter=_public_export, runner=attacked_runner,
            )
        except RuntimeError as exc:
            assert "complete runner classification" in str(exc) or "contract audit" in str(exc)
        else:
            raise AssertionError("runner-malformed packed ADD was published")
        assert observed["audit"]["valid"] is False
        assert not output.exists()


def test_corpus_is_published_only_when_runner_returns_one_and_receives_no_memory_adapter():
    with TemporaryDirectory() as temporary:
        output = Path(temporary) / "bundle"
        public = _public_export(3, "aligned")
        observed = {}

        def exporter(seed, skin):
            assert (seed, skin) == (3, "aligned")
            return public

        def runner(world, generate, **kwargs):
            observed["same_public_object"] = world is public
            observed["kwargs"] = kwargs
            return run_recurrent_life(world, generate, **kwargs)

        add = (
            "ADD | KIND=similarity | LEFT=crimson | RELATION=shows | RIGHT=pattern | "
            "CLAIM=one local public connection | CITES=episode_0 | "
            "PREDICTION=NONE | CONFIDENCE=0.8"
        )
        backend = FakeBackend(
            [add, "PASS"], [
                _exact_usage([1, 2, 3, 4], [1], add),
                _exact_usage([5, 6, 7, 8], [1], "PASS"),
            ],
        )
        run_text_dev(
            TextRunConfig(
                output_dir=output,
                condition="no_gate_no_drift",
                seed=3,
                skin="aligned",
                max_output_tokens=5,
            ),
            backend=backend,
            exporter=exporter,
            runner=runner,
        )
        assert observed["same_public_object"] is True
        assert observed["kwargs"]["memory_adapter_id"] is None
        assert observed["kwargs"]["max_tokens"] == 5
        corpus = _load(output / "corpus.json")
        assert corpus["lines"][0]["node_ids"] == ["node_00000"]
        assert _load(output / "corpus_manifest.json")["corpus"] == corpus
        hashes = _load(output / "sha256s.json")
        assert "corpus.json" in hashes["files"]


def test_public_row_hash_mutation_is_refused_before_generation():
    with TemporaryDirectory() as temporary:
        public = _public_export(8, "aligned")
        public["episodes"][0]["rows"][0]["row"] = "tampered public row"
        backend = FakeBackend([], [])
        try:
            run_text_dev(
                TextRunConfig(output_dir=Path(temporary) / "mutated-public"),
                backend=backend, exporter=lambda *_: public,
            )
        except RuntimeError as exc:
            assert "row_sha256" in str(exc)
        else:
            raise AssertionError("mutated public row was accepted")
        assert backend.calls == []


def test_retrieved_node_state_mutation_is_refused_by_prompt_replay():
    public = _public_export(9, "aligned")
    add = (
        "ADD | KIND=similarity | LEFT=crimson | RELATION=shows | RIGHT=pattern | "
        "CLAIM=one local public connection | CITES=episode_0 | "
        "PREDICTION=NONE | CONFIDENCE=0.8"
    )
    backend = FakeBackend(
        [add, "PASS"], [
            _exact_usage([1, 2, 3], [4], add),
            _exact_usage([5, 6, 7], [8], "PASS"),
        ],
    )
    generate = _backend_generate(backend)
    result = run_recurrent_life(
        public, generate, condition="no_gate_no_drift", split="dev",
        split_id="binding-test", max_tokens=7, temperature=0.0, seed=9,
        retrieval_limit=2, reactivate_every=2,
    )
    trace = result["trace"]
    public_digest = _sha256_canonical(public)
    trace["public_export_sha256"] = public_digest
    _verify_bundle_binding(public, trace, public_digest)
    assert trace["cycles"][1]["retrieved_node_ids"] == ["node_00000"]

    trace["events"][0]["depth"] = 99
    try:
        _verify_bundle_binding(public, trace, public_digest)
    except RuntimeError as exc:
        assert "model_prompt" in str(exc)
    else:
        raise AssertionError("mutated retrieved-node state was accepted")


def test_self_check_prompt_replay_rejects_mutated_cited_material_and_prior_edge():
    for target, replacement, expected in (
        (
            "state-token azure.",
            "state-token tampered.",
            "cited public row",
        ),
        (
            "status=supported depth=1",
            "status=contradicted depth=1",
            "cited prior node",
        ),
        (
            "KIND=similarity | LEFT=crimson | RELATION=shows | RIGHT=pattern",
            "KIND=operator | LEFT=crimson | RELATION=shows | RIGHT=pattern",
            "revision prior edge",
        ),
    ):
        public, trace, digest = _self_check_revision_trace()
        revision_status = next(
            event for event in trace["events"]
            if event["cycle_index"] == 1 and event["type"] == "STATUS_CHANGE"
        )
        prompt = revision_status["self_check_call"]["prompt"]
        assert target in prompt, expected
        _rewrite_self_check_prompt(revision_status, prompt.replace(target, replacement))
        try:
            _verify_bundle_binding(public, trace, digest)
        except RuntimeError as exc:
            assert "self-check" in str(exc)
        else:
            raise AssertionError(f"mutated {expected} was accepted")


def test_self_check_replay_rejects_rehashed_mutated_public_row_and_node_source():
    public, trace, _ = _self_check_revision_trace()
    public["episodes"][1]["rows"][0]["row"] = (
        "[obs_1 | episode_1] During episode one, state-token violet."
    )
    _rehash_public_lifetime(public)
    digest = _sha256_canonical(public)
    trace["public_export_sha256"] = digest
    proposal = trace["cycles"][1]["model_prompt"]
    _rewrite_proposal_prompt(trace["cycles"][1], proposal.replace("azure.", "violet."))
    try:
        _verify_bundle_binding(public, trace, digest)
    except RuntimeError as exc:
        assert "self-check" in str(exc)
    else:
        raise AssertionError("rehashed cited public row was accepted by self-check replay")

    public, trace, digest = _self_check_revision_trace()
    first_status = next(
        event for event in trace["events"]
        if event["cycle_index"] == 0 and event["type"] == "STATUS_CHANGE"
    )
    first_status["status"] = "contradicted"
    proposal = trace["cycles"][1]["model_prompt"]
    _rewrite_proposal_prompt(
        trace["cycles"][1],
        proposal.replace("status=supported depth=1", "status=contradicted depth=1"),
    )
    try:
        _verify_bundle_binding(public, trace, digest)
    except RuntimeError as exc:
        assert "self-check" in str(exc)
    else:
        raise AssertionError("rehashed cited node was accepted by self-check replay")


def test_holdout_split_and_wrong_public_world_family_are_refused():
    with TemporaryDirectory() as temporary:
        output = Path(temporary) / "holdout"
        try:
            run_text_dev(
                TextRunConfig(output_dir=output, split="holdout"),
                backend=FakeBackend([], []), exporter=_public_export,
            )
        except ValueError as exc:
            assert "split must be 'dev'" in str(exc)
        else:
            raise AssertionError("holdout artifact was accepted")

        wrong_family = _public_export(0, "aligned")
        wrong_family["world_family"] = "other_world"
        try:
            run_text_dev(
                TextRunConfig(output_dir=Path(temporary) / "wrong-family"),
                backend=FakeBackend([], []), exporter=lambda *_: wrong_family,
            )
        except ValueError as exc:
            assert "world_family" in str(exc)
        else:
            raise AssertionError("wrong world family was accepted")


def test_existing_output_is_refused_before_export_or_generation():
    with TemporaryDirectory() as temporary:
        output = Path(temporary) / "exists"
        output.mkdir()
        called = False

        def exporter(seed, skin):
            nonlocal called
            called = True
            return _public_export(seed, skin)

        try:
            run_text_dev(
                TextRunConfig(output_dir=output),
                backend=FakeBackend([], []),
                exporter=exporter,
            )
        except FileExistsError as exc:
            assert "refusing to overwrite" in str(exc)
        else:
            raise AssertionError("existing artifact directory was overwritten")
        assert called is False


def test_failure_leaves_no_partial_or_staging_directory():
    with TemporaryDirectory() as temporary:
        output = Path(temporary) / "failed-bundle"

        def runner(world, generate, **kwargs):
            raise RuntimeError("scripted failure")

        try:
            run_text_dev(
                TextRunConfig(output_dir=output),
                backend=FakeBackend([], []),
                exporter=_public_export,
                runner=runner,
            )
        except RuntimeError as exc:
            assert "scripted failure" in str(exc)
        else:
            raise AssertionError("scripted failure did not propagate")
        assert not output.exists()
        assert not list(Path(temporary).glob(".failed-bundle.staging-*"))

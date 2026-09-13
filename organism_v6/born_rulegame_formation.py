"""Source-bound birth-adapter participation; no fit, runner, or launch interface.

The caller supplies a checked, normalized completed-birth pin, not merely an
adapter directory. Its receipt/plan hashes are custody references: this module
does not interpret the birth runner's terminal artifacts or authenticate origin.
Default capture/replay use the unchanged interaction_v3 formation schedule.
An explicit exploratory binding selects the separate action-projection schedule
and AUTH or OFF child; native routing uses one engine and never switches adapters.
Backend injection supports CPU fixtures. Loader receipts are not semantic proofs.
"""
from __future__ import annotations

from collections import Counter
import copy
import math
from pathlib import Path
import re
import time

from . import model_backend, rulegame_parenting_diagnostic as diagnostic
from . import rulegame_action_projection as projection


SCHEMA = "born_rulegame_formation_v1"
PROJECTION_SCHEMA = "born_rulegame_formation_action_projection_v1"
BIRTH_PIN_SCHEMA = "completed_birth_adapter_pin_v1"
PROTOCOL = "interaction_v3"
ROLES = ("wake", "restate", "record", "parent")
ORIGIN = "SOURCE_AUTHORED_BIRTH_NOT_CLEAN"
MODEL_ORIGIN = "UNRESOLVED_LOCAL_HASHES_ONLY"
CLAIM_BOUNDARY = "Participation/in-context interaction only; no write, retained learning, P1/G3/G5/H1/H2 claim"
require = diagnostic.require


def _sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _hashes(value):
    return (isinstance(value, dict) and bool(value) and
            all(isinstance(name, str) and name and not Path(name).is_absolute()
                and ".." not in Path(name).parts and _sha(pin) for name, pin in value.items()))


def source_hashes(interface=None):
    sources = dict(diagnostic.sources(), **{
        "born_rulegame_formation.py": diagnostic.digest(Path(__file__)),
        "reasoning_neutral_probe.py": diagnostic.digest(Path(__file__).with_name("reasoning_neutral_probe.py")),
    })
    if interface is not None:
        require(interface == projection.INTERFACE, "unknown formation interface")
        sources["rulegame_action_projection.py"] = diagnostic.digest(Path(projection.__file__))
    return sources


def _birth_pin(pin):
    require(set(pin) == {"schema", "status", "birth_arm", "birth_plan_sha256",
                        "completion_receipt_sha256", "child_identity", "model_files", "origin", "model_origin"},
            "completed birth pin fields mismatch")
    require(pin["schema"] == BIRTH_PIN_SCHEMA and pin["status"] == "COMPLETE", "birth is not pinned COMPLETE")
    require(pin["birth_arm"] in ("AUTH", "DERANGED"), "unknown birth arm")
    require(pin["origin"] == ORIGIN and pin["model_origin"] == MODEL_ORIGIN, "birth origin boundary mismatch")
    require(_sha(pin["birth_plan_sha256"]) and _sha(pin["completion_receipt_sha256"]), "missing birth custody hashes")
    require(_hashes(pin["model_files"]), "missing base file pins")
    child = pin["child_identity"]
    require(isinstance(child, dict) and set(child) == {"backend", "model_input", "adapter_input", "adapter_files",
            "default_max_tokens", "default_temperature", "scope"}, "child loader identity fields mismatch")
    require(child["backend"] == "vllm" and child["default_max_tokens"] == 400
            and child["default_temperature"] == .7
            and child["scope"] == "configured loader inputs; base authentication requires lineage pins",
            "child loader identity contract mismatch")
    for field in ("model_input", "adapter_input"):
        require(isinstance(child[field], str) and Path(child[field]).is_absolute(), "local absolute loader paths required")
    require(child["adapter_input"] != child["model_input"], "adapter overlaps model")
    files = child["adapter_files"]
    require(_hashes(files) and set(files) in ({"adapter_config.json", "adapter_model.safetensors"},
            {"adapter_config.json", "adapter_model.bin"}), "missing or ambiguous birth adapter pins")


def make_binding(birth_pin, *, expected_birth_pin_sha256, interface=None, child_mode=None):
    """Bind a caller-verified completion summary (hash uses diagnostic.value_hash).

    Main/the birth runner must derive child_identity and model_files from its
    verified completed fit and bind the real plan and completion-receipt hashes.
    No birth scores or material are accepted here or sent to any generation role.
    interface=None preserves the original binding exactly. Projection requires
    interface=projection.INTERFACE and child_mode='AUTH' or 'OFF'; OFF references
    the genuine AUTH completion for matching base custody but loads no adapter.
    """
    require(diagnostic.value_hash(birth_pin) == expected_birth_pin_sha256, "birth pin hash mismatch")
    _birth_pin(birth_pin)
    child = copy.deepcopy(birth_pin["child_identity"])
    parent = dict(child, adapter_input=None, adapter_files={})
    if interface is None:
        require(child_mode is None, "child comparator requires explicit projection interface")
        return dict(schema=SCHEMA, protocol=PROTOCOL, birth=copy.deepcopy(birth_pin),
                    role_identities={role: copy.deepcopy(parent if role == "parent" else child) for role in ROLES},
                    sources=source_hashes())
    require(interface == projection.INTERFACE and child_mode in ("AUTH", "OFF"), "explicit projection AUTH/OFF required")
    require(birth_pin["birth_arm"] == "AUTH", "projection comparison requires the genuine completed AUTH reference")
    return dict(schema=PROJECTION_SCHEMA, protocol=PROTOCOL, birth=copy.deepcopy(birth_pin),
                role_identities={role: copy.deepcopy(parent if role == "parent" or child_mode == "OFF" else child) for role in ROLES},
                sources=source_hashes(interface), interface=interface, child_mode=child_mode,
                task_schedule=projection.schedule(), wake_slots=projection.WAKE_SLOTS)


def _binding(binding, expected_binding_sha256):
    require(diagnostic.value_hash(binding) == expected_binding_sha256, "formation binding hash mismatch")
    fields = {"schema", "protocol", "birth", "role_identities", "sources"}
    if binding.get("schema") == PROJECTION_SCHEMA:
        require(set(binding) == fields | {"interface", "child_mode", "task_schedule", "wake_slots"}
                and binding["protocol"] == PROTOCOL, "projection formation version mismatch")
        expected = make_binding(binding["birth"], expected_birth_pin_sha256=diagnostic.value_hash(binding["birth"]),
                                interface=binding["interface"], child_mode=binding["child_mode"])
    else:
        require(set(binding) == fields and binding["schema"] == SCHEMA and binding["protocol"] == PROTOCOL, "formation version mismatch")
        expected = make_binding(binding["birth"], expected_birth_pin_sha256=diagnostic.value_hash(binding["birth"]))
    require(binding == expected, "source or per-role identity mismatch")


def _route(binding, role):
    require(role in ROLES, "unknown generation role")
    adapter = binding["role_identities"][role]["adapter_input"]
    return None if adapter is None else dict(name="born_child", id=1, path=adapter)


def _formation_interface(binding):
    if binding["schema"] == PROJECTION_SCHEMA:
        return projection.run_formation, projection.CLAIM_BOUNDARY
    return diagnostic.run_formation, CLAIM_BOUNDARY


def _request(count, role, arm, eid, tick, prompt):
    require(role in ROLES and arm in diagnostic.ARMS, "unknown formation role/arm")
    salt = {"wake": 0, "record": 0x5A5A, "parent": 0x1010, "restate": 0x2020}[role]
    return dict(call_id=f"{count:04d}", role=role, arm=arm, eid=eid, tick=tick, prompt=prompt,
                seed=diagnostic._seed_for(eid, tick, diagnostic.GEN_SEED ^ salt),
                max_tokens=diagnostic.TOKENS[role], temperature=.5 if role in ("parent", "restate") else .7,
                **diagnostic.interaction_settings(PROTOCOL, role))


def _loader(binding, role, envelope):
    identity = binding["role_identities"][role]
    require(envelope["loader_identity"] == identity
            and envelope["loader_identity_sha256"] == diagnostic.value_hash(identity), "actual loader identity mismatch")
    require(envelope["lora_request"] == _route(binding, role), "actual LoRA request mismatch")


class RoleCalls:
    """In-memory capture; failed/partial requests remain in rows for the caller."""

    protocol = PROTOCOL

    def __init__(self, backend, binding, *, expected_binding_sha256, cutoff, clock=time.monotonic):
        _binding(binding, expected_binding_sha256)
        require(isinstance(cutoff, (int, float)) and math.isfinite(cutoff), "finite monotonic cutoff required")
        self.backend, self.binding = backend, copy.deepcopy(binding)
        self.cutoff, self.clock = cutoff, clock
        self.rows, self.counts, self.count = [], Counter(), 0
        self.failed, self.last_ended = False, 0

    def ask(self, role, arm, eid, tick, prompt):
        require(not self.failed, "failed capture cannot continue")
        try:
            require(role in ROLES and self.counts[role] < diagnostic.LIMITS["formation"][role], "response budget exhausted")
            if self.binding["schema"] == PROJECTION_SCHEMA:
                require(eid in self.binding["task_schedule"]["formation"], "projection development source required")
            started = self.clock()
            require(math.isfinite(started) and self.last_ended <= started < self.cutoff, "formation cutoff/order exceeded")
            identity = self.binding["role_identities"][role]
            require(self.backend.identity(role) == identity, "backend role identity changed")
            request = _request(self.count, role, arm, eid, tick, prompt)
            row = dict(request=request, identity=copy.deepcopy(identity), identity_sha256=diagnostic.value_hash(identity),
                       prompt_sha256=diagnostic.value_hash(prompt), started=started)
            self.rows.append(row)
            self.count += 1
            self.counts[role] += 1
            envelope = copy.deepcopy(self.backend.generate(copy.deepcopy(request)))
            row.update(envelope=envelope, ended=self.clock(), envelope_sha256=diagnostic.value_hash(envelope))
            _loader(self.binding, role, envelope)
            require(self.backend.identity(role) == identity, "backend role identity changed during call")
            require(math.isfinite(row["ended"]) and started <= row["ended"] < self.cutoff, "formation cutoff/order exceeded")
            diagnostic.validate_response(request, envelope["response"])
            self.last_ended = row["ended"]
            return request["call_id"], envelope["response"]["text"]
        except Exception:
            self.failed = True
            raise


class RoleReplay:
    protocol = PROTOCOL

    def __init__(self, rows, binding, *, expected_binding_sha256, cutoff):
        _binding(binding, expected_binding_sha256)
        require(isinstance(cutoff, (int, float)) and math.isfinite(cutoff), "finite monotonic cutoff required")
        self.rows, self.binding = copy.deepcopy(rows), copy.deepcopy(binding)
        self.counts, self.count, self.last_ended = Counter(), 0, 0
        self.cutoff = cutoff

    def ask(self, role, arm, eid, tick, prompt):
        require(role in ROLES and self.counts[role] < diagnostic.LIMITS["formation"][role], "response budget exhausted")
        if self.binding["schema"] == PROJECTION_SCHEMA:
            require(eid in self.binding["task_schedule"]["formation"], "projection development source required")
        require(self.count < len(self.rows), "missing raw call")
        row = self.rows[self.count]
        expected = _request(self.count, role, arm, eid, tick, prompt)
        require(row["request"] == expected, "source request/seed/context mismatch")
        identity = self.binding["role_identities"][role]
        require(row["identity"] == identity and row["identity_sha256"] == diagnostic.value_hash(identity), "source role identity mismatch")
        require(row["prompt_sha256"] == diagnostic.value_hash(prompt), "prompt hash mismatch")
        require(row["envelope_sha256"] == diagnostic.value_hash(row["envelope"]), "raw response hash mismatch")
        require(math.isfinite(row["started"]) and math.isfinite(row["ended"])
                and self.last_ended <= row["started"] <= row["ended"] < self.cutoff, "call cutoff/order invalid")
        _loader(self.binding, role, row["envelope"])
        diagnostic.validate_response(expected, row["envelope"]["response"])
        self.last_ended = row["ended"]
        self.count += 1
        self.counts[role] += 1
        return expected["call_id"], row["envelope"]["response"]["text"]


class FormationFailure(ValueError):
    def __init__(self, message, partial):
        super().__init__(message)
        self.partial = partial


def capture_formation(backend, binding, *, expected_binding_sha256, cutoff, clock=time.monotonic):
    """Return source-bound raw capture, or raise FormationFailure with partial.

    cutoff is monotonic and checked around calls; an external supervisor must
    interrupt blocked generation and own GPU cleanup. This function writes no
    files, retries nothing, and never selects or exports sleep material.
    """
    calls = RoleCalls(backend, binding, expected_binding_sha256=expected_binding_sha256, cutoff=cutoff, clock=clock)
    events = diagnostic.Events()
    run_formation, claim = _formation_interface(binding)
    capture = dict(schema=binding["schema"], protocol=PROTOCOL, binding=copy.deepcopy(binding),
                   binding_sha256=expected_binding_sha256, cutoff=cutoff,
                   claim_boundary=claim, status="FAILED_PARTIAL", result=None,
                   calls=calls.rows, events=events.rows)
    try:
        backend.verify()
        result = run_formation(calls, events)
        backend.verify()
        _binding(binding, expected_binding_sha256)
        require(clock() < cutoff, "formation cutoff exceeded")
        capture.update(status="AWAITING_MAIN_AUDIT", result=result)
        replay_formation(capture, binding, expected_binding_sha256=expected_binding_sha256, cutoff=cutoff)
        return copy.deepcopy(capture)
    except Exception as error:
        capture.update(status="FAILED_PARTIAL", result=None)
        raise FormationFailure(str(error), copy.deepcopy(capture)) from error


def replay_formation(capture, binding, *, expected_binding_sha256, cutoff):
    """Recompute every public prompt/world join; no backend or model calls."""
    _binding(binding, expected_binding_sha256)
    run_formation, claim = _formation_interface(binding)
    require(capture["schema"] == binding["schema"] and capture["protocol"] == PROTOCOL, "capture version mismatch")
    require(capture["binding"] == binding and capture["binding_sha256"] == expected_binding_sha256,
            "capture binding mismatch")
    require(capture["cutoff"] == cutoff, "capture cutoff mismatch")
    require(capture["status"] == "AWAITING_MAIN_AUDIT" and capture["claim_boundary"] == claim,
            "incomplete capture or claim boundary mismatch")
    calls = RoleReplay(capture["calls"], binding, expected_binding_sha256=expected_binding_sha256, cutoff=capture["cutoff"])
    events = diagnostic.Events()
    result = run_formation(calls, events)
    require(calls.count == len(capture["calls"]), "extra raw calls")
    require(result == capture["result"], "recomputed formation result mismatch")
    require(events.rows == capture["events"], "execution/record provenance mismatch")
    return dict(ok=True, result=result, events=events.rows, calls=calls.count, roles=dict(calls.counts))


class NativeRoleBackend:
    """One existing engine; explicit OFF/child request routing, never a switch.

    Construction is opt-in model work, not performed by capture/replay. External
    Main-owned supervision, deadlines, release and terminal custody are required.
    """

    def __init__(self, binding, *, expected_binding_sha256, allow_gpu=False):
        require(allow_gpu, "Main-owned native integration requires allow_gpu")
        _binding(binding, expected_binding_sha256)
        self.binding = copy.deepcopy(binding)
        self.child = self.binding["role_identities"]["wake"]
        require(Path(model_backend.MODEL).resolve() == Path(self.child["model_input"]).resolve(), "V6_MODEL differs from pin")
        self._files()
        native = diagnostic.NativeBackend(self.child["model_input"], self.child["adapter_input"])
        self.backend = native.backend
        self.child_lora = (self.backend._LoRARequest("born_child", 1, self.child["adapter_input"])
                           if self.child["adapter_input"] is not None else None)
        self.verify()

    def _files(self):
        require(diagnostic.model_hashes(self.child["model_input"]) == self.binding["birth"]["model_files"], "base files changed")
        require(model_backend.configured_generation_identity(self.child["model_input"], self.child["adapter_input"])
                == self.child, "birth adapter files changed")

    def verify(self):
        self._files()
        require(self.backend.generation_identity() == self.child, "engine child loader changed")
        require(self.backend.adapter_path == self.child["adapter_input"], "engine adapter path changed")
        if self.child["adapter_input"] is None:
            require(self.child_lora is None, "OFF must not create a synthetic child LoRA")
        else:
            require(self.child_lora is not None and self.child_lora.lora_name == "born_child" and self.child_lora.lora_int_id == 1
                    and self.child_lora.lora_path == self.child["adapter_input"], "child LoRA request changed")

    def identity(self, role):
        require(role in ROLES, "unknown generation role")
        require(model_backend.configured_generation_identity(self.child["model_input"], self.child["adapter_input"])
                == self.child, "birth adapter files changed")
        require(self.backend.generation_identity() == self.child and self.backend.adapter_path == self.child["adapter_input"],
                "engine child loader changed")
        return copy.deepcopy(self.binding["role_identities"][role])

    def generate(self, request):
        from vllm import SamplingParams
        role = request["role"]
        if self.binding["schema"] == PROJECTION_SCHEMA:
            require(request["eid"] in self.binding["task_schedule"]["formation"], "projection development source required")
        identity = self.identity(role)
        require(request == _request(int(request["call_id"]), role, request["arm"], request["eid"], request["tick"], request["prompt"]),
                "native request settings/version mismatch")
        backend = self.backend
        rendered = backend.tok.apply_chat_template([{"role": "user", "content": request["prompt"]}],
                                                   tokenize=False, add_generation_prompt=True)
        require(len(backend.tok.encode(rendered)) + request["max_tokens"] <= diagnostic.MAX_MODEL_LEN, "prompt exceeds model limit")
        sampling = SamplingParams(max_tokens=request["max_tokens"], temperature=request["temperature"], seed=request["seed"],
                                  stop=request["stop"], include_stop_str_in_output=request["include_stop_str_in_output"])
        route = _route(self.binding, role)
        lora = None if route is None else self.child_lora
        require((lora is None) == (route is None), "native role LoRA route mismatch")
        require(self.child["adapter_input"] is not None or self.child_lora is None, "OFF must not create a synthetic child LoRA")
        require(lora is None or (lora.lora_name == "born_child" and lora.lora_int_id == 1
                and lora.lora_path == self.child["adapter_input"]), "child LoRA request changed")
        outputs = backend.llm.generate([rendered], sampling, lora_request=lora, use_tqdm=False)
        require(len(outputs) == 1 and len(outputs[0].outputs) == 1, "native generation cardinality mismatch")
        output = outputs[0].outputs[0]
        response = dict(text=output.text, prompt_token_ids=list(outputs[0].prompt_token_ids),
                        output_token_ids=list(output.token_ids), rendered_prompt=rendered,
                        finish_reason=output.finish_reason, stop_reason=output.stop_reason)
        diagnostic.validate_response(request, response)
        require(response["prompt_token_ids"] == backend.tok.encode(rendered), "native source input token mismatch")
        decoded = backend.tok.decode(response["output_token_ids"], skip_special_tokens=True, clean_up_tokenization_spaces=False)
        if response["stop_reason"] in request["stop"]:
            require(response["finish_reason"] == "stop", "native stop finish mismatch")
            decoded = decoded.split(response["stop_reason"], 1)[0]
        require(decoded == response["text"], "native source output token mismatch")
        require(self.identity(role) == identity, "loader changed during generation")
        return dict(response=response, loader_identity=identity, loader_identity_sha256=diagnostic.value_hash(identity),
                    lora_request=None if lora is None else dict(name=lora.lora_name, id=lora.lora_int_id, path=lora.lora_path))

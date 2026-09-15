"""Additional micro/critical and creative/critical BASE treatments on node3 0/3."""

from types import SimpleNamespace

from organism_v6 import orch_math_feedback_uptake_node3 as prior


base = prior.base
HOST_SHA = prior.HOST_SHA
add_declared_question_hashes = prior.add_declared_question_hashes
DEVICES = {0: 'GPU-0ee6f753-c61e-e18a-8aea-acccd3042939', 3: 'GPU-e1277146-04f2-c38f-d1ae-1a98132f907e'}
STYLES = {
    0: ('micro', 'Use concise, sharply critical coaching about the reasoning, not the child. Identify one consequential unsupported assumption or unperformed check and ask the child to investigate it. Do not supply the answer or require decorative introspection.'),
    3: ('creative', 'Use critical creative inquiry: challenge unsupported certainty and ask the child to explore a genuinely different interpretation tied to actual evidence. Demand clear distinctions between facts and hypotheses, without prescribing a solution or branch quota.')}


def configured(index):
    base.require(index in DEVICES, 'only_allocated_node3_0_3')
    style, instruction = STYLES[index]
    namespace = SimpleNamespace(**vars(base))
    namespace.UUID = DEVICES[index]
    namespace.PHYSICAL = index
    namespace.NATIVE_CAP = 28
    namespace.PARENT_CAP = 4
    namespace.PARENT_INSTRUCTION = base.PARENT_INSTRUCTION + '\n' + instruction
    parenting = dict(style=style, horizon='short' if index == 0 else 'long', tone='harsh-critical', strength=base.STRONG)
    def validate(payload):
        base.require(payload['parenting'] == parenting and payload['instruction'] == namespace.PARENT_INSTRUCTION, 'exact_node3_extra_style')
        normalized = dict(payload, instruction=base.PARENT_INSTRUCTION,
            parenting=dict(style='persistent-curious', horizon='long', tone='supportive', strength=base.STRONG))
        base.validate_parent_payload(normalized)
    def payload(tasks, records, cycle, round_number, previous=()):
        result = base.parent_payload(tasks, records, cycle, round_number, previous)
        result['parenting'] = dict(parenting)
        result['instruction'] = namespace.PARENT_INSTRUCTION
        validate(result)
        return result
    namespace.validate_parent_payload = validate
    namespace.parent_payload = payload
    namespace.options = lambda model_dir: SimpleNamespace(model_dir=model_dir, adapter_dir=None, phase='readout',
        device='cuda:0', gpu_uuid=DEVICES[index], expected_base_sha256=base.BASE_SHA)
    return namespace

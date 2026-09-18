"""Two prospective BASE parenting treatments, not additional controls."""

from types import SimpleNamespace

from organism_v6 import orch_math_feedback_uptake_base as base


HOST_SHA = '3e10ebcb89f013079c1e088fa82820188b1a805b879ebb85a7ffeb689e7b86e9'
DEVICES = {1: 'GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821', 2: 'GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1'}
STYLES = {
    1: ('training-wheels', 'Use supportive training wheels: help the child allocate effort to consequential uncertainty, check what evidence is missing, and return to an unresolved thread when useful. Do not dictate a solution or prescribe a branch count.'),
    2: ('creative', 'Use supportive creative inquiry: help the child ask relevant questions, connect actual observations, and consider a different interpretation when its current account fails. Keep speculation distinct from facts and avoid ceremonial alternatives.')}


def add_declared_question_hashes(documents, hashes):
    def visit(value):
        if isinstance(value, dict):
            for name in ('excluded_question_sha256', 'excluded_question_hashes'):
                hashes.update(value.get(name, []))
            if isinstance(value.get('question_sha256'), str):
                hashes.add(value['question_sha256'])
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    for document in documents:
        visit(document)
    return hashes


def configured(index):
    base.require(index in DEVICES, 'only_allocated_node3_1_2')
    style, instruction = STYLES[index]
    namespace = SimpleNamespace(**vars(base))
    namespace.UUID = DEVICES[index]
    namespace.PHYSICAL = index
    namespace.NATIVE_CAP = 28
    namespace.PARENT_CAP = 4
    namespace.PARENT_INSTRUCTION = base.PARENT_INSTRUCTION + '\n' + instruction
    parenting = dict(style=style, horizon='long', tone='supportive', strength=base.STRONG)
    def validate(payload):
        base.require(payload['parenting'] == parenting and payload['instruction'] == namespace.PARENT_INSTRUCTION, 'exact_node3_parent_style')
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

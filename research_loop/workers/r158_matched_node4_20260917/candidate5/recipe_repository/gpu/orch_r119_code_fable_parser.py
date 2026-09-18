"""CODE-only native turn accounting; one provider attempt is not one utility turn."""

from gpu import orch_r110_claude_broker as original


def parse_output(raw, family, task_id):
    original.require(family == 'code', 'CODE_only_parser_override')
    envelope = original.loads(raw)
    original.require(isinstance(envelope, dict) and envelope.get('type') == 'result'
        and not envelope.get('is_error') and envelope.get('subtype') in (None, 'success')
        and type(envelope.get('num_turns')) is int and envelope['num_turns'] >= 1,
        'provider_error_or_invalid_native_turn_accounting')
    models = envelope.get('modelUsage')
    original.require(isinstance(models, dict) and 0 < len(models) <= 2, 'actual_model_usage_required')
    observed = [name for name, usage in models.items()
        if name == original.MODEL or isinstance(usage, dict) and usage.get('canonicalModel') == original.MODEL]
    original.require(len(observed) == 1, 'actual_fable_model_required_no_substitute')
    result = envelope.get('result')
    original.require(isinstance(result, str), 'parent_result_text')
    text = result.strip()
    if text.startswith('```json\n') and text.endswith('\n```'):
        text = text[8:-4]
    reply = '[SILENT]' if text == '[SILENT]' else original.loads(text)
    plan, metadata = original.adapt_plan(reply, family, task_id)
    return dict(status='SILENT' if metadata['silent'] else 'COMPLETE', plan=plan,
        parent_metadata=metadata, actual_model=observed[0], usage=dict(
            usage=envelope.get('usage'), model_usage=models,
            total_cost_usd=envelope.get('total_cost_usd'), duration_ms=envelope.get('duration_ms'),
            native_num_turns=envelope['num_turns'], provider_attempts=1,
            main_vs_utility_turn_split='NOT_INFERRED'))

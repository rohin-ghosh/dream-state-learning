"""Non-material recipe comparison: only explicit target-module ordering is inert."""

from copy import deepcopy


def canonical_recipe(document):
    if not isinstance(document, dict):
        raise ValueError('adapter_recipe_object_required')
    result = deepcopy(document)
    targets = result.get('target_modules')
    if isinstance(targets, list):
        if not targets or any(not isinstance(name, str) or not name for name in targets):
            raise ValueError('nonempty_explicit_target_names_required')
        if len(set(targets)) != len(targets):
            raise ValueError('duplicate_target_module_not_normalized')
        result['target_modules'] = sorted(targets)
    elif not isinstance(targets, str) or not targets:
        raise ValueError('explicit_target_list_or_unchanged_regex_required')
    return result


def require_same_recipe(prior, following):
    if canonical_recipe(prior) != canonical_recipe(following):
        raise ValueError('unchanged_adapter_recipe_except_target_order')
    return dict(equivalent=True, ignored_difference='explicit_target_modules_order_only',
        original_documents_unchanged=True, tensor_keys_shapes_hashes_still_required=True)

"""Pure, oracle-blind FeltCraft V7 symbolic candidate surfaces."""

from fractions import Fraction
from itertools import permutations


DESCRIPTORS = ("DR0", "DR1", "DR2", "DR3", "DI0", "DI1", "DT0", "DT1")
RAW_DESCRIPTORS = DESCRIPTORS[:4]
INTERMEDIATE_DESCRIPTORS = DESCRIPTORS[4:6]
TOP_DESCRIPTORS = DESCRIPTORS[6:8]
ROLES = ("R0", "R1", "R2", "R3", "I0", "I1", "T0", "T1")
RAW_ROLES = ROLES[:4]
INTERMEDIATE_ROLES = ROLES[4:6]
TOP_ROLES = ROLES[6:8]

_ROLE_RECIPES = (
    ("I0", "R0", "R1"),
    ("I1", "R2", "R3"),
    ("T0", "I0", "R2"),
    ("T1", "I1", "R0"),
)


class DomainError(Exception):
    """Exact closed-domain exception surface."""

    def __init__(self, code):
        self.code = code
        Exception.__init__(self, code)


def _raise(code):
    raise DomainError(code)


def _enumerate_alignments():
    return tuple(
        raw + intermediate + top
        for raw in permutations(RAW_ROLES)
        for intermediate in permutations(INTERMEDIATE_ROLES)
        for top in permutations(TOP_ROLES)
    )


def _render_graph(alignment):
    inverse = {role: descriptor for descriptor, role in zip(DESCRIPTORS, alignment)}
    recipe_by_output = {triple[0]: triple[1:] for triple in _ROLE_RECIPES}
    rendered = []
    descriptor_index = {descriptor: index for index, descriptor in enumerate(DESCRIPTORS)}
    for output_descriptor in INTERMEDIATE_DESCRIPTORS + TOP_DESCRIPTORS:
        output_role = alignment[DESCRIPTORS.index(output_descriptor)]
        ingredient_roles = recipe_by_output[output_role]
        pair = tuple(sorted(
            (inverse[ingredient_roles[0]], inverse[ingredient_roles[1]]),
            key=descriptor_index.__getitem__,
        ))
        rendered.append((output_descriptor,) + pair)
    return tuple(rendered)


def _unique_first(values):
    result = ()
    for value in values:
        if value not in result:
            result += (value,)
    return result


_ALIGNMENT_REGISTRY = _enumerate_alignments()
_GRAPH_REGISTRY = _unique_first(tuple(_render_graph(alignment) for alignment in _ALIGNMENT_REGISTRY))
_CALIBRATION_REGISTRY = _unique_first(tuple(graph[:2] for graph in _GRAPH_REGISTRY))


def _alignments():
    return _ALIGNMENT_REGISTRY


def _graphs():
    return _GRAPH_REGISTRY


def _calibrations():
    return _CALIBRATION_REGISTRY


def _require_alignment(alignment):
    if type(alignment) is not tuple:
        _raise("SK08_E_TYPE")
    if len(alignment) != 8:
        _raise("SK08_E_ARITY")
    if any(type(atom) is not str for atom in alignment):
        _raise("SK08_E_TYPE")
    if any(atom not in ROLES for atom in alignment):
        _raise("SK08_E_ATOM")
    if alignment not in _alignments():
        _raise("SK08_E_ALIGNMENT")


def _require_triple_shape(value, length):
    if type(value) is not tuple:
        _raise("SK08_E_TYPE")
    if len(value) != length:
        _raise("SK08_E_ARITY")
    for triple in value:
        if type(triple) is not tuple:
            _raise("SK08_E_TYPE")
        if len(triple) != 3:
            _raise("SK08_E_ARITY")
        if any(type(atom) is not str for atom in triple):
            _raise("SK08_E_TYPE")


def _require_atoms(value):
    if any(atom not in DESCRIPTORS for triple in value for atom in triple):
        _raise("SK08_E_ATOM")


def _require_order(value, outputs):
    descriptor_index = {descriptor: index for index, descriptor in enumerate(DESCRIPTORS)}
    if tuple(triple[0] for triple in value) != outputs:
        _raise("SK08_E_ORDER")
    if any(descriptor_index[triple[1]] >= descriptor_index[triple[2]] for triple in value):
        _raise("SK08_E_ORDER")


def _support(calibration, goal):
    counts = {}
    for alignment in _alignments():
        graph = _render_graph(alignment)
        if graph[:2] == calibration:
            pair = graph[TOP_DESCRIPTORS.index(goal) + 2][1:]
            counts[pair] = counts.get(pair, 0) + 1
    descriptor_index = {descriptor: index for index, descriptor in enumerate(DESCRIPTORS)}
    support = tuple(sorted(
        counts.items(),
        key=lambda item: tuple(descriptor_index[atom] for atom in item[0]),
    ))
    best = max(count for pair, count in support)
    chosen = next(pair for pair, count in support if count == best)
    value = Fraction(best, sum(count for pair, count in support))
    return (value.numerator, value.denominator, chosen, support)


def enumerator_call(surface, args):
    """Single addressed enumerator invocation surface."""
    if type(surface) is not str or type(args) is not tuple:
        _raise("SK08_E_TYPE")
    if surface == "ALIGNMENTS" and len(args) == 0:
        return _alignments()
    if surface == "GRAPHS" and len(args) == 0:
        return _graphs()
    if surface == "CALIBRATIONS" and len(args) == 0:
        return _calibrations()
    if surface == "ALIGNMENT_AT" and len(args) == 1 and type(args[0]) is int:
        if 0 <= args[0] < 96:
            return _alignments()[args[0]]
        _raise("SK08_E_ALIGNMENT")
    if surface in ("GRAPH", "CAL") and len(args) == 1:
        _require_alignment(args[0])
        graph = _render_graph(args[0])
        return graph if surface == "GRAPH" else graph[:2]
    if surface == "TOP" and len(args) == 2:
        _require_alignment(args[0])
        if type(args[1]) is not str:
            _raise("SK08_E_TYPE")
        if args[1] not in TOP_DESCRIPTORS:
            _raise("SK08_E_GOAL")
        return _render_graph(args[0])[TOP_DESCRIPTORS.index(args[1]) + 2][1:]
    _raise("SK08_E_ARITY")


def projection_call(projection_id, args):
    """Sole fail-closed public constructor for all four projections."""
    if type(projection_id) is not str or type(args) is not tuple:
        _raise("SK08_E_TYPE")
    arities = (("LOCAL", 2), ("MOTIF_SCHEMA", 3), ("RANDOM_SOURCE", 4), ("ORACLE", 2))
    expected = next((arity for name, arity in arities if name == projection_id), None)
    if expected is None:
        _raise("SK08_E_ATOM")
    if len(args) != expected:
        _raise("SK08_E_ARITY")

    compounds = args[:-1]
    if projection_id == "ORACLE":
        alignment = compounds[0]
        if type(alignment) is not tuple:
            _raise("SK08_E_TYPE")
        if len(alignment) != 8:
            _raise("SK08_E_ARITY")
        if any(type(atom) is not str for atom in alignment):
            _raise("SK08_E_TYPE")
    else:
        triple_lengths = (2,) if projection_id == "LOCAL" else ((4, 2) if projection_id == "MOTIF_SCHEMA" else (4, 4, 2))
        for value, length in zip(compounds, triple_lengths):
            _require_triple_shape(value, length)

    goal = args[-1]
    if type(goal) is not str:
        _raise("SK08_E_TYPE")
    if goal not in TOP_DESCRIPTORS:
        _raise("SK08_E_GOAL")

    if projection_id == "ORACLE":
        if any(atom not in ROLES for atom in alignment):
            _raise("SK08_E_ATOM")
        if alignment not in _alignments():
            _raise("SK08_E_ALIGNMENT")
        pair = _render_graph(alignment)[TOP_DESCRIPTORS.index(goal) + 2][1:]
        return (1, 1, pair, ((pair, 1),))

    for value in compounds:
        _require_atoms(value)
    if projection_id == "LOCAL":
        calibration = compounds[0]
        _require_order(calibration, INTERMEDIATE_DESCRIPTORS)
        if calibration not in _calibrations():
            _raise("SK08_E_ALIGNMENT")
        return _support(calibration, goal)

    graph = compounds[0]
    calibration = compounds[-1]
    _require_order(graph, INTERMEDIATE_DESCRIPTORS + TOP_DESCRIPTORS)
    _require_order(calibration, INTERMEDIATE_DESCRIPTORS)
    if projection_id == "RANDOM_SOURCE":
        second_graph = compounds[1]
        _require_order(second_graph, INTERMEDIATE_DESCRIPTORS + TOP_DESCRIPTORS)
        if graph not in _graphs() or second_graph not in _graphs():
            _raise("SK08_E_SOURCE_GRAPH")
        if calibration not in _calibrations():
            _raise("SK08_E_ALIGNMENT")
        return _support(calibration, goal)

    if graph not in _graphs():
        _raise("SK08_E_SOURCE_GRAPH")
    if calibration not in _calibrations():
        _raise("SK08_E_ALIGNMENT")
    if calibration != graph[:2]:
        _raise("SK08_E_MOTIF_INCOMPATIBLE")
    pair = graph[TOP_DESCRIPTORS.index(goal) + 2][1:]
    return (1, 1, pair, ((pair, 1),))


def _twin(alignment):
    swaps = (("R0", "R2"), ("R2", "R0"), ("R1", "R3"), ("R3", "R1"))
    return tuple(next((right for left, right in swaps if left == role), role) for role in alignment)


def _require_goal(goal):
    if type(goal) is not str:
        _raise("SK08_E_TYPE")
    if goal not in TOP_DESCRIPTORS:
        _raise("SK08_E_GOAL")


def checker_call(surface, args):
    """Single addressed twin/cost/bridge/deletion checker invocation."""
    if type(surface) is not str or type(args) is not tuple:
        _raise("SK08_E_TYPE")
    if surface == "TWIN" and len(args) == 1:
        _require_alignment(args[0])
        return _twin(args[0])
    if surface == "INTERMEDIATE_COST" and len(args) == 2:
        _require_alignment(args[0])
        if args[1] not in INTERMEDIATE_DESCRIPTORS:
            _raise("SK08_E_ATOM")
        return 2 + 2 + 1
    if surface == "TOP_COST" and len(args) == 2:
        _require_alignment(args[0])
        _require_goal(args[1])
        return (2 + 2 + 1) + 2 + 1
    if surface in ("CONJ_COST", "BRIDGE_COST") and len(args) == 4:
        _require_alignment(args[0])
        _require_goal(args[1])
        _require_alignment(args[2])
        _require_goal(args[3])
        two_tops = ((2 + 2 + 1) + 2 + 1) * 2
        return two_tops if surface == "CONJ_COST" else two_tops + 1
    if surface == "BRIDGE_DELETION" and len(args) == 5:
        _require_alignment(args[0])
        _require_goal(args[1])
        _require_alignment(args[2])
        _require_goal(args[3])
        if args[4] not in ("OLD", "NEW"):
            _raise("SK08_E_ATOM")
        old_product = "OLD::" + args[1]
        new_product = "NEW::" + args[3]
        inventory = (old_product, new_product)
        deleted_product = old_product if args[4] == "OLD" else new_product
        remaining = tuple(product for product in inventory if product != deleted_product)
        final_craft_enabled = old_product in remaining and new_product in remaining
        remaining_budget = 17 - 16
        return (final_craft_enabled, remaining_budget)
    _raise("SK08_E_ARITY")

"""Exhaustive SK01--SK09 comparator for the FeltCraft V7 candidate surfaces."""

from collections import Counter
from itertools import product

from .kernel import DomainError, checker_call, enumerator_call, projection_call
from .report import validate_and_return


_ALIGNMENT_GRAPH_VECTORS = (
    (0,("R0","R1","R2","R3","I0","I1","T0","T1"),(("DI0","DR0","DR1"),("DI1","DR2","DR3"),("DT0","DR2","DI0"),("DT1","DR0","DI1"))),
    (1,("R0","R1","R2","R3","I0","I1","T1","T0"),(("DI0","DR0","DR1"),("DI1","DR2","DR3"),("DT0","DR0","DI1"),("DT1","DR2","DI0"))),
    (2,("R0","R1","R2","R3","I1","I0","T0","T1"),(("DI0","DR2","DR3"),("DI1","DR0","DR1"),("DT0","DR2","DI1"),("DT1","DR0","DI0"))),
    (3,("R0","R1","R2","R3","I1","I0","T1","T0"),(("DI0","DR2","DR3"),("DI1","DR0","DR1"),("DT0","DR0","DI0"),("DT1","DR2","DI1"))),
    (8,("R0","R2","R1","R3","I0","I1","T0","T1"),(("DI0","DR0","DR2"),("DI1","DR1","DR3"),("DT0","DR1","DI0"),("DT1","DR0","DI1"))),
    (10,("R0","R2","R1","R3","I1","I0","T0","T1"),(("DI0","DR1","DR3"),("DI1","DR0","DR2"),("DT0","DR1","DI1"),("DT1","DR0","DI0"))),
    (12,("R0","R2","R3","R1","I0","I1","T0","T1"),(("DI0","DR0","DR3"),("DI1","DR1","DR2"),("DT0","DR1","DI0"),("DT1","DR0","DI1"))),
    (14,("R0","R2","R3","R1","I1","I0","T0","T1"),(("DI0","DR1","DR2"),("DI1","DR0","DR3"),("DT0","DR1","DI1"),("DT1","DR0","DI0"))),
    (16,("R0","R3","R1","R2","I0","I1","T0","T1"),(("DI0","DR0","DR2"),("DI1","DR1","DR3"),("DT0","DR3","DI0"),("DT1","DR0","DI1"))),
    (48,("R2","R0","R1","R3","I0","I1","T0","T1"),(("DI0","DR1","DR2"),("DI1","DR0","DR3"),("DT0","DR0","DI0"),("DT1","DR1","DI1"))),
)

_CAL_EXPECTATIONS = (
    ((("DI0","DR0","DR1"),("DI1","DR2","DR3")),(("DR0","DI1"),("DR1","DI1"),("DR2","DI0"),("DR3","DI0"))),
    ((("DI0","DR2","DR3"),("DI1","DR0","DR1")),(("DR0","DI0"),("DR1","DI0"),("DR2","DI1"),("DR3","DI1"))),
    ((("DI0","DR0","DR2"),("DI1","DR1","DR3")),(("DR0","DI1"),("DR1","DI0"),("DR2","DI1"),("DR3","DI0"))),
    ((("DI0","DR1","DR3"),("DI1","DR0","DR2")),(("DR0","DI0"),("DR1","DI1"),("DR2","DI0"),("DR3","DI1"))),
    ((("DI0","DR0","DR3"),("DI1","DR1","DR2")),(("DR0","DI1"),("DR1","DI0"),("DR2","DI0"),("DR3","DI1"))),
    ((("DI0","DR1","DR2"),("DI1","DR0","DR3")),(("DR0","DI0"),("DR1","DI1"),("DR2","DI1"),("DR3","DI0"))),
)


def _invoke(function, call_edge, observation_edge, args):
    if call_edge not in ("SKE07", "SKE09", "SKE11"):
        raise AssertionError("call edge")
    try:
        value = function(*args)
    except BaseException as exception:
        observation = ("exception", exception)
    else:
        observation = ("return", value)
    if observation_edge not in ("SKE08", "SKE10", "SKE12"):
        raise AssertionError("observation edge")
    return observation


def _enumerator(surface, args):
    observation = _invoke(enumerator_call, "SKE07", "SKE08", (surface, args))
    if observation[0] != "return":
        raise observation[1]
    return observation[1]


def _projection(projection, args):
    return _invoke(projection_call, "SKE09", "SKE10", (projection, args))


def _projection_value(projection, args):
    observation = _projection(projection, args)
    if observation[0] != "return":
        raise observation[1]
    return observation[1]


def _checker(surface, args):
    observation = _invoke(checker_call, "SKE11", "SKE12", (surface, args))
    if observation[0] != "return":
        raise observation[1]
    return observation[1]


def _receipt(test_id, counts):
    return (test_id, tuple(counts), True)


def _expected_support(calibration):
    return next(pairs for cal, pairs in _CAL_EXPECTATIONS if cal == calibration)


def test_sk01():
    alignments = _enumerator("ALIGNMENTS", ())
    graphs = _enumerator("GRAPHS", ())
    mismatches = 0
    for index, alignment, graph in _ALIGNMENT_GRAPH_VECTORS:
        mismatches += _enumerator("ALIGNMENT_AT", (index,)) != alignment
        mismatches += _enumerator("GRAPH", (alignment,)) != graph
    mismatches += _ALIGNMENT_GRAPH_VECTORS[6][2] == _ALIGNMENT_GRAPH_VECTORS[8][2]
    assert len(alignments) == 96 and len(graphs) == 48
    assert all(len(graph) == 4 for graph in graphs) and mismatches == 0
    return _receipt("SK01_DOMAIN_INVERSE_V7", (96,48,4,10,10,0))


def test_sk02():
    alignments = _enumerator("ALIGNMENTS", ())
    calibrations = _enumerator("CALIBRATIONS", ())
    histogram = Counter(_enumerator("CAL", (alignment,)) for alignment in alignments)
    mismatches = sum(calibration != expected[0] for calibration, expected in zip(calibrations, _CAL_EXPECTATIONS))
    assert len(calibrations) == 6 and set(histogram.values()) == {16} and mismatches == 0
    return _receipt("SK02_CALIBRATION_VECTORS_V7", (6,16,6,0))


def test_sk03():
    checks = 0
    chosen_checks = 0
    source_factor = len(_enumerator("GRAPHS", ())) ** 2
    for calibration, pairs in _CAL_EXPECTATIONS:
        expected_table = tuple((pair, 4) for pair in pairs)
        for goal in ("DT0", "DT1"):
            result = _projection_value("LOCAL", (calibration, goal))
            assert result == (1,4,pairs[0],expected_table)
            assert tuple(count * source_factor for pair, count in expected_table) == (9216,9216,9216,9216)
            assert sum(count * source_factor for pair, count in expected_table) == 36864
            checks += 1
            chosen_checks += 1
    assert checks == 12 and chosen_checks == 12
    return _receipt("SK03_RANDOM_WITNESSES_V7", (12,4,4,1,4,12,12,0))


def test_sk04():
    graphs = _enumerator("GRAPHS", ())
    cases = 0
    for graph, goal in product(graphs, ("DT0", "DT1")):
        result = _projection_value("MOTIF_SCHEMA", (graph, graph[:2], goal))
        pair = graph[2 + (goal == "DT1")][1:]
        assert result == (1,1,pair,((pair,1),))
        cases += 1
    top_checks = 0
    for index, alignment, graph in _ALIGNMENT_GRAPH_VECTORS:
        for goal in ("DT0", "DT1"):
            assert _enumerator("TOP", (alignment, goal)) == graph[2 + (goal == "DT1")][1:]
            top_checks += 1
    assert cases == 96 and top_checks == 20
    return _receipt("SK04_MOTIF_WITNESSES_V7", (96,1,1,20,0))


def test_sk05():
    alignments = _enumerator("ALIGNMENTS", ())
    roundtrip = edge_failures = top_failures = 0
    for alignment in alignments:
        twin = _checker("TWIN", (alignment,))
        roundtrip += _checker("TWIN", (twin,)) != alignment
        graph = _enumerator("GRAPH", (alignment,))
        twin_graph = _enumerator("GRAPH", (twin,))
        edge_failures += any(left == right for left, right in zip(graph, twin_graph))
        top_failures += any(
            _enumerator("TOP", (alignment, goal)) == _enumerator("TOP", (twin, goal))
            for goal in ("DT0", "DT1")
        )
    fixed = ((12,48),(48,12))
    for source, target in fixed:
        assert _checker("TWIN", (_enumerator("ALIGNMENT_AT", (source,)),)) == _enumerator("ALIGNMENT_AT", (target,))
    assert roundtrip == edge_failures == top_failures == 0
    return _receipt("SK05_TWIN_WITNESSES_V7", (96,2,0,0,0))


def test_sk06():
    alignments = _enumerator("ALIGNMENTS", ())
    intermediate = tuple(_checker("INTERMEDIATE_COST", (alignment, output)) for alignment, output in product(alignments, ("DI0","DI1")))
    top = tuple(_checker("TOP_COST", (alignment, goal)) for alignment, goal in product(alignments, ("DT0","DT1")))
    conj = _checker("CONJ_COST", (alignments[0],"DT0",alignments[-1],"DT1"))
    bridge = _checker("BRIDGE_COST", (alignments[0],"DT0",alignments[-1],"DT1"))
    failures = sum(value != 5 for value in intermediate) + sum(value != 8 for value in top) + (conj != 16) + (bridge != 17)
    assert len(intermediate) == len(top) == 192 and failures == 0
    return _receipt("SK06_COSTS", (192,5,192,8,16,17,0))


def test_sk07():
    alignments = _enumerator("ALIGNMENTS", ())
    cases = deletions = failures = 0
    for old_alignment, new_alignment, old_goal, new_goal in product(alignments, alignments, ("DT0","DT1"), ("DT0","DT1")):
        cases += 1
        for deleted in ("OLD", "NEW"):
            enabled, remaining_budget = _checker("BRIDGE_DELETION", (old_alignment,old_goal,new_alignment,new_goal,deleted))
            deletions += 1
            failures += enabled or remaining_budget >= 8
    assert cases == 36864 and deletions == 73728 and failures == 0
    return _receipt("SK07_BRIDGE_DELETION", (36864,73728,0))


def _negative_fixtures():
    pi0 = _ALIGNMENT_GRAPH_VECTORS[0][1]
    graph0 = _ALIGNMENT_GRAPH_VECTORS[0][2]
    graph12 = _ALIGNMENT_GRAPH_VECTORS[6][2]
    cal0 = graph0[:2]
    cal12 = graph12[:2]
    return (
        ("LOCAL",(cal0,),"SK08_E_ARITY"),("MOTIF_SCHEMA",(graph0,cal0),"SK08_E_ARITY"),("RANDOM_SOURCE",(graph0,graph0,cal0),"SK08_E_ARITY"),("ORACLE",(pi0,),"SK08_E_ARITY"),
        ("LOCAL",((("DI0","DR0","DR1"),),"DT0"),"SK08_E_ARITY"),("MOTIF_SCHEMA",((("DI0","DR0","DR1"),("DI1","DR2","DR3"),("DT0","DR2","DI0")),cal0,"DT0"),"SK08_E_ARITY"),("ORACLE",(("R0","R1","R2","R3","I0","I1","T0"),"DT0"),"SK08_E_ARITY"),
        ("LOCAL",(0,"DT0"),"SK08_E_TYPE"),("MOTIF_SCHEMA",(graph0,"CAL_000","DT0"),"SK08_E_TYPE"),("RANDOM_SOURCE",(graph0,graph0,None,"DT0"),"SK08_E_TYPE"),("ORACLE",({"not":"an immutable tuple"},"DT0"),"SK08_E_TYPE"),
        ("LOCAL",((("DI0","DR4","DR1"),("DI1","DR2","DR3")),"DT0"),"SK08_E_ATOM"),("MOTIF_SCHEMA",((("DI0","DR0","DR1"),("DI1","DR2","DR3"),("DT0","DR2","DI0"),("DT1","DR0","DX")),cal0,"DT0"),"SK08_E_ATOM"),
        ("LOCAL",((("DI0","DR1","DR0"),("DI1","DR2","DR3")),"DT0"),"SK08_E_ORDER"),("MOTIF_SCHEMA",((("DI1","DR2","DR3"),("DI0","DR0","DR1"),("DT0","DR2","DI0"),("DT1","DR0","DI1")),cal0,"DT0"),"SK08_E_ORDER"),
        ("LOCAL",(cal0,"DT2"),"SK08_E_GOAL"),("MOTIF_SCHEMA",(graph0,cal0,"DT2"),"SK08_E_GOAL"),("RANDOM_SOURCE",(graph0,graph0,cal0,"DT2"),"SK08_E_GOAL"),("ORACLE",(pi0,"DT2"),"SK08_E_GOAL"),
        ("ORACLE",(("R0","R0","R2","R3","I0","I1","T0","T1"),"DT0"),"SK08_E_ALIGNMENT"),("ORACLE",(("I0","R1","R2","R3","R0","I1","T0","T1"),"DT0"),"SK08_E_ALIGNMENT"),
        ("MOTIF_SCHEMA",(graph0,cal12,"DT0"),"SK08_E_MOTIF_INCOMPATIBLE"),("MOTIF_SCHEMA",(graph12,cal0,"DT1"),"SK08_E_MOTIF_INCOMPATIBLE"),
        ("RANDOM_SOURCE",((("DI0","DR0","DR1"),("DI1","DR2","DR3"),("DT0","DR0","DI0"),("DT1","DR0","DI1")),graph0,cal0,"DT0"),"SK08_E_SOURCE_GRAPH"),("RANDOM_SOURCE",(graph0,(("DI0","DR0","DR1"),("DI1","DR2","DR3"),("DT0","DR2","DI0"),("DT1","DR2","DI1")),cal0,"DT1"),"SK08_E_SOURCE_GRAPH"),
    )


def test_sk08():
    alignments = _enumerator("ALIGNMENTS", ())
    graphs = _enumerator("GRAPHS", ())
    calibrations = _enumerator("CALIBRATIONS", ())
    local = motif = random_count = oracle = 0
    for calibration, goal in product(calibrations, ("DT0","DT1")):
        assert _projection_value("LOCAL", (calibration,goal))[:2] == (1,4)
        local += 1
    for graph, goal in product(graphs, ("DT0","DT1")):
        assert _projection_value("MOTIF_SCHEMA", (graph,graph[:2],goal))[:2] == (1,1)
        motif += 1
    for graph0, graph1, calibration, goal in product(graphs, graphs, calibrations, ("DT0","DT1")):
        expected_pairs = _expected_support(calibration)
        assert _projection_value("RANDOM_SOURCE", (graph0,graph1,calibration,goal)) == (1,4,expected_pairs[0],tuple((pair,4) for pair in expected_pairs))
        random_count += 1
    for alignment, goal in product(alignments, ("DT0","DT1")):
        assert _projection_value("ORACLE", (alignment,goal))[:2] == (1,1)
        oracle += 1
    histogram = Counter()
    rejected = mismatches = 0
    fixtures = _negative_fixtures()
    for projection, args, expected_code in fixtures:
        observation = _projection(projection, args)
        if observation[0] == "exception" and type(observation[1]) is DomainError and observation[1].code == expected_code and observation[1].args == (expected_code,):
            rejected += 1
            histogram[expected_code] += 1
        else:
            mismatches += 1
    assert (local,motif,random_count,oracle) == (12,96,27648,192)
    assert len(fixtures) == rejected == 25 and mismatches == 0
    expected_histogram = (("SK08_E_ALIGNMENT",2),("SK08_E_ARITY",7),("SK08_E_ATOM",2),("SK08_E_GOAL",4),("SK08_E_MOTIF_INCOMPATIBLE",2),("SK08_E_ORDER",2),("SK08_E_SOURCE_GRAPH",2),("SK08_E_TYPE",4))
    assert tuple(sorted(histogram.items())) == expected_histogram
    return _receipt("SK08_PROJECTIONS_CLOSED_BOUNDARY_V7", (12,96,27648,192,72,25,25,0)), expected_histogram


def run_all():
    receipts = (test_sk01(),test_sk02(),test_sk03(),test_sk04(),test_sk05(),test_sk06(),test_sk07())
    sk08, histogram = test_sk08()
    return validate_and_return(receipts + (sk08,), histogram)

HEADER = '''# DEMO CONTENT — public repository, therefore NOT secret (ADR-009).
# Design record: docs/content-design/pivot-index.md (bank expansion batch A4, 2026-10-25).

slug = "pivot-index"
title = "Balance point of an array"
family = "prefix-sums"
statement = "statement.md"
harness = "harness.cpp"
reference = "reference.cpp"
solution_file = "solution.cpp" # name the student's code is compiled under
interface = "int pivot_index(const std::vector<int>& a);"
# Bank expansion (2026-10-25): new problems are not recommendable (CE1 decision E2 applied to
# every new problem). They stay in the problem list and their attempts produce skill evidence.
recommendable = false

[skills]
index_range = "Visiting exactly the valid positions: the loop's start and end cover every element once."
tie_resolution = "Handling equal values as the specification says: which of several equal candidates wins, and whether duplicates count separately."
update_rule = "Updating every piece of tracked state on each step (running candidates, pointers, window edges) so no candidate is lost."
output_contract = "Returning exactly what the specification asks for: an index or a value, a sentinel when there is no answer."

[probes]
pivot_excluded = ["index_range", "update_rule"]
several_pivots = ["tie_resolution"]
no_pivot = ["output_contract"]
pivot_at_edge = ["index_range"]
negatives = ["update_rule"]
large_input = ["update_rule"]

[curriculum]
assumes = ["a running sum while scanning"]
'''

TESTS = [
    dict(key="sample_typical", sample=True, input="L 6 1 7 3 6 5 6", probes=["pivot_excluded"], desc="A typical array.", purpose="Visible typical case."),
    dict(key="sample_none", sample=True, input="L 3 1 2 3", probes=["no_pivot"], desc="No balance point.", purpose="Visible case with answer -1."),
    dict(key="pivot_first", input="L 3 2 1 -1", probes=["pivot_at_edge", "negatives"], desc="The first index balances.", purpose="Left side is empty."),
    dict(key="pivot_last", input="L 3 -1 1 5", probes=["pivot_at_edge", "negatives"], desc="The last index balances.", purpose="Right side is empty."),
    dict(key="zeros", input="L 4 0 0 0 0", probes=["several_pivots"], desc="Every value zero.", purpose="Every index balances; the first wins."),
    dict(key="two_pivots", input="L 5 1 -1 0 1 -1", probes=["several_pivots", "negatives"], desc="More than one balance point.", purpose="The first of several pivots."),
    dict(key="two_pivots_mixed", input="L 5 3 0 -1 2 2", probes=["several_pivots", "negatives"], desc="Two balance points with mixed signs.", purpose="Indices 1 and 3 both balance; the first wins."),
    dict(key="single", input="L 1 5", probes=["pivot_at_edge"], desc="One element.", purpose="Both sides empty: index 0."),
    dict(key="pivot_value_matters", input="L 5 3 3 9 4 2", probes=["pivot_excluded"], desc="A large middle value.", purpose="Counting the pivot on one side gives a different index."),
    dict(key="left_heavy_trap", input="L 4 2 3 1 4", probes=["pivot_excluded"], desc="A pivot only if it is counted on the left.", purpose="No pivot; counting the pivot on the left finds one."),
    dict(key="right_heavy_trap", input="L 4 4 1 3 2", probes=["pivot_excluded", "no_pivot"], desc="A pivot only if it is counted on the right.", purpose="No pivot; counting the pivot on the right finds one."),
    dict(key="negative_sum", input="L 6 -3 -2 -4 1 -6 1", probes=["negatives", "pivot_excluded"], desc="Mostly negative values.", purpose="Balance with negative sums."),
    dict(key="large_symmetric", input="R 99999 0 3 4 0", probes=["large_input"], desc="A long array of equal values.", purpose="Large input; the middle index balances."),
    dict(key="large_zeros", input="R 100000 0 0 1 0", probes=["large_input", "several_pivots"], desc="A long array of zeros.", purpose="Large input; every index balances."),
    dict(key="large_none", input="R 100000 1 0 7 1", probes=["large_input", "no_pivot"], desc="A long array with no balance point.", purpose="Large input; answer -1."),
]


def parse(inp):
    t = inp.split()
    n = int(t[1])
    if t[0] == "L":
        return [int(x) for x in t[2:2 + n]]
    mult, add, mod, base = map(int, t[2:6])
    return [(i * mult + add) % mod + base for i in range(n)]


def check(inp):
    a = parse(inp)
    total, left = sum(a), 0
    for i, x in enumerate(a):
        if left == total - left - x:
            return str(i)
        left += x
    return "-1"


def RANDOM(rng):
    n = rng.randint(1, 8)
    a = [rng.randint(-3, 3) for _ in range(n)]
    return "L %d %s" % (n, " ".join(map(str, a)))


MODELS = '''
[[error_models]]
key = "pivot_counted_left"
file = "error_models/pivot_counted_left.cpp"
skill = "update_rule"
description = "Adds a[i] to the left sum before comparing, so the pivot itself is counted on the left side."
student_hint = "Is the element at the balance point part of the left side, the right side, or neither? Check when you add it to your running sum."

[[error_models]]
key = "pivot_counted_right"
file = "error_models/pivot_counted_right.cpp"
skill = "update_rule"
description = "Computes the right side as total - left, so the pivot itself is counted on the right side."
student_hint = "Does your right-hand sum leave out the element at the balance point?"

[[error_models]]
key = "last_pivot"
file = "error_models/last_pivot.cpp"
skill = "tie_resolution"
description = "Returns the last balancing index instead of the first."
student_hint = "If several indices balance, which one must you return?"

[[error_models]]
key = "size_when_none"
file = "error_models/size_when_none.cpp"
skill = "output_contract"
description = "When no index balances, returns n (the loop index after the loop) instead of -1."
student_hint = "What must you return when no index balances the array?"
'''

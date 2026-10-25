HEADER = '''# DEMO CONTENT — public repository, therefore NOT secret (ADR-009).
# Design record: docs/content-design/closest-pair-sum.md (bank expansion batch A2, 2026-10-25).

slug = "closest-pair-sum"
title = "Closest pair sum"
family = "two-pointers"
statement = "statement.md"
harness = "harness.cpp"
reference = "reference.cpp"
solution_file = "solution.cpp" # name the student's code is compiled under
interface = "int closest_pair_gap(const std::vector<int>& a, int target);"
# Bank expansion (2026-10-25): new problems are not recommendable (CE1 decision E2 applied to
# every new problem). They stay in the problem list and their attempts produce skill evidence.
recommendable = false

[skills]
index_range = "Visiting exactly the valid positions: the loop's start and end cover every element once."
update_rule = "Updating every piece of tracked state on each step (running candidates, pointers, window edges) so no candidate is lost."
output_contract = "Returning exactly what the specification asks for: an index or a value, a sentinel when there is no answer."

[probes]
self_pair_tempting = ["index_range"]
first_element_needed = ["index_range"]
pointer_direction = ["update_rule"]
gap_below_target = ["output_contract"]
exact_hit = ["update_rule"]
large_input = ["update_rule"]

[curriculum]
assumes = ["a sorted array", "two indices moving towards each other"]
'''

TESTS = [
    dict(key="sample_typical", sample=True, input="L 5 1 3 5 8 12 14", probes=["pointer_direction", "gap_below_target"], desc="A small sorted array.", purpose="Visible typical case."),
    dict(key="sample_exact", sample=True, input="L 4 2 4 7 11 11", probes=["exact_hit", "pointer_direction"], desc="Some pair hits the target exactly.", purpose="Visible exact case."),
    dict(key="self_pair_middle", input="L 5 1 4 10 30 40 20", probes=["self_pair_tempting"], desc="One element doubled would hit the target.", purpose="Only a self-pair hits the target."),
    dict(key="self_pair_two", input="L 2 5 9 10", probes=["self_pair_tempting", "first_element_needed"], desc="Two elements; doubling the first is closest.", purpose="Smallest self-pair case."),
    dict(key="first_needed", input="L 4 -5 6 7 9 1", probes=["first_element_needed"], desc="The best pair uses the first element.", purpose="The answer needs a[0]."),
    dict(key="two_elements", input="L 2 3 4 10", probes=["first_element_needed", "gap_below_target"], desc="Exactly two elements, sum below the target.", purpose="Only one pair exists."),
    dict(key="all_above", input="L 4 10 20 30 40 5", probes=["gap_below_target", "first_element_needed"], desc="Every sum is above the target.", purpose="The closest sum is the smallest one."),
    dict(key="all_below", input="L 4 1 2 3 4 100", probes=["gap_below_target"], desc="Every sum is below the target.", purpose="The closest sum is the largest one."),
    dict(key="negatives", input="L 6 -9 -7 -2 3 8 12 -10", probes=["pointer_direction", "first_element_needed"], desc="Negative values and a negative target.", purpose="Pointer moves with negative sums."),
    dict(key="duplicates", input="L 6 2 2 2 5 5 9 7", probes=["exact_hit"], desc="Repeated values.", purpose="Exact hit among duplicates."),
    dict(key="direction_matters", input="L 6 1 2 3 50 60 70 52", probes=["pointer_direction"], desc="Small and large values far apart.", purpose="Moving the wrong pointer skips the best pair."),
    dict(key="large_steps", input="S 100000 3 -150000 1000001", probes=["large_input", "pointer_direction"], desc="A long arithmetic sequence.", purpose="Large input; target not reachable exactly."),
    dict(key="large_exact", input="S 100000 2 0 199996", probes=["large_input", "exact_hit"], desc="A long arithmetic sequence with an exact pair.", purpose="Large input; exact pair at the far end."),
]


def parse(inp):
    t = inp.split()
    n = int(t[1])
    if t[0] == "L":
        return [int(x) for x in t[2:2 + n]], int(t[2 + n])
    step, start, target = map(int, t[2:5])
    return [start + i * step for i in range(n)], target


def check(inp):
    a, target = parse(inp)
    lo, hi, best = 0, len(a) - 1, None
    while lo < hi:
        s = a[lo] + a[hi]
        g = abs(s - target)
        best = g if best is None else min(best, g)
        if s < target:
            lo += 1
        elif s > target:
            hi -= 1
        else:
            return "0"
    return str(best)


def RANDOM(rng):
    n = rng.randint(2, 8)
    a = sorted(rng.randint(-15, 15) for _ in range(n))
    return "L %d %s %d" % (n, " ".join(map(str, a)), rng.randint(-30, 30))


MODELS = '''
[[error_models]]
key = "allows_same_element"
file = "error_models/allows_same_element.cpp"
skill = "index_range"
description = "Loops while lo <= hi, so an element can be paired with itself."
student_hint = "Can the two numbers of a pair be the same element of the array? Check when your loop stops."

[[error_models]]
key = "moves_wrong_pointer"
file = "error_models/moves_wrong_pointer.cpp"
skill = "update_rule"
description = "Moves hi when the sum is too small and lo when it is too large, so the sum moves away from the target."
student_hint = "If the current sum is too small, which pointer must move to make it larger?"

[[error_models]]
key = "skips_first"
file = "error_models/skips_first.cpp"
skill = "index_range"
description = "The left pointer starts at index 1, so pairs using the first element are never considered."
student_hint = "Where does your left pointer start? Can the first element be part of the best pair?"

[[error_models]]
key = "signed_gap"
file = "error_models/signed_gap.cpp"
skill = "output_contract"
description = "Returns the signed difference (sum - target) of the closest pair instead of its absolute value."
student_hint = "Can the answer be negative? Re-read what distance the function must return."
'''

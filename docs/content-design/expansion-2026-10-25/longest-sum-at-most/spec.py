HEADER = '''# DEMO CONTENT — public repository, therefore NOT secret (ADR-009).
# Design record: docs/content-design/longest-sum-at-most.md (bank expansion batch A3, 2026-10-25).

slug = "longest-sum-at-most"
title = "Longest stretch within a budget"
family = "sliding-window"
statement = "statement.md"
harness = "harness.cpp"
reference = "reference.cpp"
solution_file = "solution.cpp" # name the student's code is compiled under
interface = "int longest_at_most(const std::vector<int>& a, int s);"
# Bank expansion (2026-10-25): new problems are not recommendable (CE1 decision E2 applied to
# every new problem). They stay in the problem list and their attempts produce skill evidence.
recommendable = false

[skills]
index_range = "Visiting exactly the valid positions: the loop's start and end cover every element once."
update_rule = "Updating every piece of tracked state on each step (running candidates, pointers, window edges) so no candidate is lost."
output_contract = "Returning exactly what the specification asks for: an index or a value, a sentinel when there is no answer."

[probes]
multi_shrink = ["update_rule"]
partial_overlap = ["update_rule"]
exact_budget = ["output_contract"]
length_counted = ["index_range"]
nothing_fits = ["output_contract", "update_rule"]
large_input = ["update_rule"]

[curriculum]
assumes = ["a window with a left and a right edge"]
prerequisites = ["max-window-sum"]
'''

TESTS = [
    dict(key="sample_typical", sample=True, input="L 6 3 1 2 1 4 2 5", probes=["partial_overlap", "length_counted"], desc="A small array with budget 5.", purpose="Visible typical case."),
    dict(key="sample_exact", sample=True, input="L 4 2 2 2 2 6", probes=["exact_budget", "length_counted"], desc="Equal values; the budget fits three exactly.", purpose="Visible case with an exact fit."),
    dict(key="big_then_small", input="L 6 9 1 1 1 1 1 5", probes=["multi_shrink"], desc="One large value then small ones.", purpose="Removing one element at a time is needed after the large value."),
    dict(key="many_to_drop", input="L 6 1 1 1 1 8 1 9", probes=["multi_shrink", "partial_overlap"], desc="Many small values then a large one.", purpose="Several elements must leave the window at once."),
    dict(key="keep_tail", input="L 4 5 1 1 3 6", probes=["partial_overlap"], desc="The best window keeps part of an earlier one.", purpose="Restarting the window loses the answer."),
    dict(key="drop_one_keep_rest", input="L 5 6 1 1 1 1 7", probes=["partial_overlap", "multi_shrink"], desc="A large first value, then small ones.", purpose="Only the first element must leave; restarting loses one."),
    dict(key="exact_after_overlap", input="L 6 5 2 5 2 2 1 12", probes=["partial_overlap", "exact_budget"], desc="The best stretch sums exactly to the budget and overlaps an earlier one.", purpose="Separates the strict limit from restarting the window."),
    dict(key="whole_array", input="L 4 1 2 3 4 10", probes=["exact_budget", "length_counted"], desc="Everything fits exactly.", purpose="The whole array sums to the budget."),
    dict(key="nothing_fits", input="L 3 7 8 9 5", probes=["nothing_fits"], desc="Every value is above the budget.", purpose="The answer is 0."),
    dict(key="one_fits", input="L 3 7 3 9 5", probes=["nothing_fits", "length_counted"], desc="Only one value fits.", purpose="The answer is 1."),
    dict(key="single_exact", input="L 1 5 5", probes=["exact_budget"], desc="One element equal to the budget.", purpose="Minimal exact case."),
    dict(key="loose_budget", input="L 5 1 2 3 4 5 100", probes=["length_counted"], desc="A budget larger than the total.", purpose="Nothing ever leaves the window."),
    dict(key="large_ramp", input="R 100000 1 0 100 1 5000", probes=["large_input", "multi_shrink"], desc="A long array of repeated ramps.", purpose="Large input."),
    dict(key="large_exact", input="R 100000 0 0 1 3 30000", probes=["large_input", "exact_budget"], desc="A long array of equal values.", purpose="Large input; windows fit the budget exactly."),
]


def parse(inp):
    t = inp.split()
    n = int(t[1])
    if t[0] == "L":
        return [int(x) for x in t[2:2 + n]], int(t[2 + n])
    mult, add, mod, base, s = map(int, t[2:7])
    return [(i * mult + add) % mod + base for i in range(n)], s


def check(inp):
    a, s = parse(inp)
    tot, left, best = 0, 0, 0
    for right, x in enumerate(a):
        tot += x
        while tot > s:
            tot -= a[left]
            left += 1
        best = max(best, right - left + 1)
    return str(best)


def RANDOM(rng):
    n = rng.randint(1, 9)
    a = [rng.randint(1, 6) for _ in range(n)]
    return "L %d %s %d" % (n, " ".join(map(str, a)), rng.randint(1, 15))


MODELS = '''
[[error_models]]
key = "length_without_plus_one"
file = "error_models/length_without_plus_one.cpp"
skill = "index_range"
description = "Measures the window as right - left, one less than its number of elements."
student_hint = "How many elements are there between positions left and right, both included?"

[[error_models]]
key = "strict_limit"
file = "error_models/strict_limit.cpp"
skill = "output_contract"
description = "Treats 'at most s' as 'less than s', so a window whose sum equals s is rejected."
student_hint = "Is a stretch whose sum is exactly the budget allowed?"

[[error_models]]
key = "restarts_window"
file = "error_models/restarts_window.cpp"
skill = "update_rule"
description = "When the sum goes over s, starts a new window at the current element instead of shrinking from the left."
student_hint = "When the sum goes over the budget, do you need to drop the whole window, or only some elements from its left end?"
'''

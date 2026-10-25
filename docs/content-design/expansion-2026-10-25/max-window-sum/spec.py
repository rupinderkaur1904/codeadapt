HEADER = '''# DEMO CONTENT — public repository, therefore NOT secret (ADR-009).
# Design record: docs/content-design/max-window-sum.md (bank expansion batch A3, 2026-10-25).

slug = "max-window-sum"
title = "Largest sum of k consecutive values"
family = "sliding-window"
statement = "statement.md"
harness = "harness.cpp"
reference = "reference.cpp"
solution_file = "solution.cpp" # name the student's code is compiled under
interface = "int max_window_sum(const std::vector<int>& a, int k);"
# Bank expansion (2026-10-25): new problems are not recommendable (CE1 decision E2 applied to
# every new problem). They stay in the problem list and their attempts produce skill evidence.
recommendable = false

[skills]
index_range = "Visiting exactly the valid positions: the loop's start and end cover every element once."
accumulator_init = "Initialising (and re-initialising) a running best, minimum, maximum, count or sum to the value the first real element requires."
update_rule = "Updating every piece of tracked state on each step (running candidates, pointers, window edges) so no candidate is lost."

[probes]
best_window_last = ["index_range"]
all_negative = ["accumulator_init"]
leaving_element_matters = ["update_rule"]
k_equals_n = ["index_range", "update_rule"]
k_one = ["update_rule"]
large_input = ["update_rule"]

[curriculum]
assumes = ["summing a range of a std::vector"]
'''

TESTS = [
    dict(key="sample_typical", sample=True, input="L 7 2 1 5 1 3 2 4 3", probes=["leaving_element_matters"], desc="A small array, windows of 3.", purpose="Visible typical case."),
    dict(key="sample_negative", sample=True, input="L 5 -4 -2 -7 -1 -3 2", probes=["all_negative"], desc="Every value negative.", purpose="Visible case where every window sum is negative."),
    dict(key="best_last", input="L 6 1 2 1 2 9 9 2", probes=["best_window_last", "leaving_element_matters"], desc="The best window is at the end.", purpose="The answer is the last window."),
    dict(key="best_first", input="L 6 9 9 1 1 1 1 2", probes=["leaving_element_matters"], desc="The best window is at the start.", purpose="The first window is the answer."),
    dict(key="k_equals_n", input="L 4 3 -1 4 1 4", probes=["k_equals_n"], desc="The window is the whole array.", purpose="Only one window exists."),
    dict(key="k_one", input="L 5 -3 8 -1 6 2 1", probes=["k_one"], desc="Windows of one element.", purpose="The answer is the largest element."),
    dict(key="negative_k_one", input="L 4 -5 -2 -9 -4 1", probes=["k_one", "all_negative"], desc="Negative values, windows of one.", purpose="All negative with k = 1."),
    dict(key="mixed_signs", input="L 8 4 -6 3 3 -2 5 -8 1 3", probes=["leaving_element_matters", "best_window_last"], desc="Positive and negative values.", purpose="Large positives early must leave the window."),
    dict(key="dip_then_rise", input="L 7 5 5 -9 -9 1 6 6 2", probes=["best_window_last", "leaving_element_matters"], desc="A dip in the middle, rising at the end.", purpose="Two windows compete; the later one wins."),
    dict(key="single", input="L 1 -7 1", probes=["k_equals_n", "all_negative"], desc="One element.", purpose="Minimal input."),
    dict(key="large_negative", input="R 100000 7 3 1000 -5000 50", probes=["large_input", "all_negative"], desc="A long array of negative values.", purpose="Large input; every window negative."),
    dict(key="large_ramp", input="R 100000 1 0 10000 -5000 100", probes=["large_input", "best_window_last"], desc="A long array of repeated ramps.", purpose="Large input."),
]


def parse(inp):
    t = inp.split()
    n = int(t[1])
    if t[0] == "L":
        return [int(x) for x in t[2:2 + n]], int(t[2 + n])
    mult, add, mod, base, k = map(int, t[2:7])
    return [(i * mult + add) % mod + base for i in range(n)], k


def check(inp):
    a, k = parse(inp)
    s = sum(a[:k])
    best = s
    for i in range(k, len(a)):
        s += a[i] - a[i - k]
        best = max(best, s)
    return str(best)


def RANDOM(rng):
    n = rng.randint(1, 9)
    a = [rng.randint(rng.choice([-9, -3]), rng.choice([-1, 9])) for _ in range(n)]
    return "L %d %s %d" % (n, " ".join(map(str, a)), rng.randint(1, n))


MODELS = '''
[[error_models]]
key = "best_starts_zero"
file = "error_models/best_starts_zero.cpp"
skill = "accumulator_init"
description = "Starts the best sum at 0, so 0 is returned when every window sum is negative."
student_hint = "What should you return if every window has a negative sum? Check the starting value of your best sum."

[[error_models]]
key = "misses_last_window"
file = "error_models/misses_last_window.cpp"
skill = "index_range"
description = "The sliding loop stops one step early, so the last window is never summed."
student_hint = "Does your loop reach the window that ends at the last element?"

[[error_models]]
key = "never_subtracts"
file = "error_models/never_subtracts.cpp"
skill = "update_rule"
description = "Adds each entering element but never subtracts the leaving one, so the window keeps growing."
student_hint = "When the window moves one step right, which element leaves it?"

[[error_models]]
key = "subtracts_wrong_element"
file = "error_models/subtracts_wrong_element.cpp"
skill = "update_rule"
description = "Subtracts a[i - k + 1] instead of a[i - k], so the wrong element leaves the window."
student_hint = "When element i enters a window of size k, which index leaves? Check it on a small example."
'''

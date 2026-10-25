HEADER = '''# DEMO CONTENT — public repository, therefore NOT secret (ADR-009).
# Design record: docs/content-design/distinct-in-windows.md (bank expansion batch A3, 2026-10-25).

slug = "distinct-in-windows"
title = "Distinct values in every window"
family = "sliding-window"
statement = "statement.md"
harness = "harness.cpp"
reference = "reference.cpp"
solution_file = "solution.cpp" # name the student's code is compiled under
interface = "std::vector<int> distinct_in_windows(const std::vector<int>& a, int k);"
# Bank expansion (2026-10-25): new problems are not recommendable (CE1 decision E2 applied to
# every new problem). They stay in the problem list and their attempts produce skill evidence.
recommendable = false

[skills]
index_range = "Visiting exactly the valid positions: the loop's start and end cover every element once."
tie_resolution = "Handling equal values as the specification says: which of several equal candidates wins, and whether duplicates count separately."
update_rule = "Updating every piece of tracked state on each step (running candidates, pointers, window edges) so no candidate is lost."

[probes]
value_leaves = ["update_rule"]
value_leaves_fully = ["update_rule"]
duplicates_in_window = ["tie_resolution"]
last_window = ["index_range"]
k_equals_n = ["index_range"]
large_input = ["update_rule"]

[curriculum]
assumes = ["std::unordered_map or std::map counts"]
prerequisites = ["max-window-sum"]
'''

TESTS = [
    dict(key="sample_typical", sample=True, input="L 7 1 2 1 3 4 2 3 4", probes=["value_leaves", "duplicates_in_window", "last_window"], desc="Windows of four.", purpose="Visible typical case."),
    dict(key="sample_all_same", sample=True, input="L 5 7 7 7 7 7 2", probes=["duplicates_in_window"], desc="Every value equal.", purpose="Visible case: one distinct value per window."),
    dict(key="all_distinct", input="L 6 1 2 3 4 5 6 3", probes=["value_leaves_fully", "last_window"], desc="No repeated values.", purpose="Every window has k distinct values."),
    dict(key="value_returns", input="L 6 5 6 5 6 5 6 2", probes=["value_leaves", "duplicates_in_window"], desc="Two values alternate.", purpose="A leaving value is still present in the window."),
    dict(key="leaves_for_good", input="L 6 9 9 1 2 3 4 3", probes=["value_leaves_fully"], desc="A repeated value at the start that never returns.", purpose="Values leave the window completely."),
    dict(key="k_equals_n", input="L 4 3 1 3 2 4", probes=["k_equals_n", "duplicates_in_window", "last_window"], desc="The window is the whole array.", purpose="Only one window."),
    dict(key="k_one", input="L 4 8 8 2 8 1", probes=["last_window"], desc="Windows of one element.", purpose="Every count is 1."),
    dict(key="pairs_in_window", input="L 6 1 1 2 2 3 3 4", probes=["duplicates_in_window", "value_leaves"], desc="Each value appears twice in a row.", purpose="Duplicates inside each window."),
    dict(key="new_at_end", input="L 5 4 4 4 4 9 2", probes=["last_window", "value_leaves_fully"], desc="A new value only in the last position.", purpose="The last window differs from the others."),
    dict(key="single", input="L 1 0 1", probes=["k_equals_n", "last_window"], desc="One element.", purpose="Minimal input."),
    dict(key="large_cycle", input="R 100000 1 0 50 0 100", probes=["large_input", "value_leaves", "duplicates_in_window"], desc="A long array cycling through 50 values.", purpose="Large input; every window holds all 50 values."),
    dict(key="large_distinct", input="R 100000 1 0 100000 0 1000", probes=["large_input", "value_leaves_fully"], desc="A long array without repeats.", purpose="Large input; every value leaves for good."),
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
    from collections import Counter
    c = Counter(a[:k])
    out = [len(c)]
    for i in range(k, len(a)):
        c[a[i]] += 1
        c[a[i - k]] -= 1
        if c[a[i - k]] == 0:
            del c[a[i - k]]
        out.append(len(c))
    if len(out) <= 40:
        return " ".join(map(str, out))
    h = 1469598103934665603
    for x in out:
        h = (h * 1000003 + x + 1000) % (1 << 64)
    return "len=%d first=%d last=%d hash=%d" % (len(out), out[0], out[-1], h)


def RANDOM(rng):
    n = rng.randint(1, 9)
    a = [rng.randint(0, rng.choice([1, 3, 6])) for _ in range(n)]
    return "L %d %s %d" % (n, " ".join(map(str, a)), rng.randint(1, n))


MODELS = '''
[[error_models]]
key = "keeps_zero_counts"
file = "error_models/keeps_zero_counts.cpp"
skill = "update_rule"
description = "Counts values that have left the window: the count is decremented but the key is never erased at zero (never removing the leaving element at all, or a set that only grows, gives identical output)."
student_hint = "When a value's count drops to 0, is it still in the window? Does your container still count it?"

[[error_models]]
key = "misses_last_window"
file = "error_models/misses_last_window.cpp"
skill = "index_range"
description = "The loop stops one element early, so the last window gets no count."
student_hint = "How many windows of size k does an array of n elements have? Count yours."

[[error_models]]
key = "counts_unique_only"
file = "error_models/counts_unique_only.cpp"
skill = "tie_resolution"
description = "Counts the values that occur exactly once in the window instead of the distinct values."
student_hint = "If a value appears twice in a window, does it count as one distinct value or as none?"
'''

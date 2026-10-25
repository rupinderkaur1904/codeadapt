HEADER = '''# DEMO CONTENT — public repository, therefore NOT secret (ADR-009).
# Design record: docs/content-design/range-sum-queries.md (bank expansion batch A4, 2026-10-25).

slug = "range-sum-queries"
title = "Range sums with prefix sums"
family = "prefix-sums"
statement = "statement.md"
harness = "harness.cpp"
reference = "reference.cpp"
solution_file = "solution.cpp" # name the student's code is compiled under
interface = "std::vector<long long> range_sums(const std::vector<int>& a, const std::vector<std::pair<int, int>>& queries);"
# Bank expansion (2026-10-25): new problems are not recommendable (CE1 decision E2 applied to
# every new problem). They stay in the problem list and their attempts produce skill evidence.
recommendable = false

[skills]
index_range = "Visiting exactly the valid positions: the loop's start and end cover every element once."
update_rule = "Updating every piece of tracked state on each step (running candidates, pointers, window edges) so no candidate is lost."
output_contract = "Returning exactly what the specification asks for: an index or a value, a sentinel when there is no answer."

[probes]
right_end_counts = ["index_range"]
long_range = ["update_rule"]
left_not_zero = ["output_contract"]
single_element_range = ["index_range", "update_rule"]
large_input = ["update_rule"]

[curriculum]
assumes = ["building an array of running totals"]
prerequisites = ["pivot-index"]
'''

TESTS = [
    dict(key="sample_typical", sample=True, input="L 6 3 -1 4 1 5 -9 3 0 2 1 4 2 5", probes=["right_end_counts", "long_range", "left_not_zero"], desc="Three queries on a small array.", purpose="Visible typical case."),
    dict(key="sample_whole", sample=True, input="L 4 1 2 3 4 1 0 3", probes=["right_end_counts", "long_range"], desc="One query over the whole array.", purpose="Visible case starting at index 0."),
    dict(key="single_elements", input="L 5 7 -2 9 0 4 3 0 0 2 2 4 4", probes=["single_element_range", "left_not_zero"], desc="Queries of one element each.", purpose="l = r."),
    dict(key="from_start", input="L 5 2 4 6 8 10 2 0 1 0 4", probes=["long_range", "right_end_counts"], desc="Queries starting at index 0.", purpose="Prefix queries."),
    dict(key="middle_ranges", input="L 7 5 1 -3 2 2 8 -1 3 1 3 2 5 4 6", probes=["left_not_zero", "long_range", "right_end_counts"], desc="Queries in the middle of the array.", purpose="l > 0 for every query."),
    dict(key="zero_right_end", input="L 5 4 4 4 0 9 2 1 3 0 3", probes=["right_end_counts"], desc="Queries ending at a zero.", purpose="Excluding a[r] changes nothing here; other tests carry the evidence."),
    dict(key="negatives", input="L 5 -4 -6 -1 -8 -2 2 1 3 0 4", probes=["long_range", "left_not_zero"], desc="Negative values.", purpose="Negative range sums."),
    dict(key="single_value_array", input="L 1 -7 1 0 0", probes=["single_element_range"], desc="One element, one query.", purpose="Minimal input."),
    dict(key="repeated_query", input="L 4 1 1 1 1 3 1 2 1 2 1 2", probes=["left_not_zero", "single_element_range"], desc="The same query three times.", purpose="Answers do not depend on earlier queries."),
    dict(key="large_many_queries", input="G 100000 37 11 20001 -10000 100000", probes=["large_input", "long_range"], desc="A long array with many queries.", purpose="Large input; O(n + q) needed."),
]


def parse(inp):
    t = inp.split()
    n = int(t[1])
    if t[0] == "L":
        a = [int(x) for x in t[2:2 + n]]
        q = int(t[2 + n])
        qs = [(int(t[3 + n + 2 * j]), int(t[4 + n + 2 * j])) for j in range(q)]
        return a, qs
    mult, add, mod, base, q = map(int, t[2:7])
    a = [(i * mult + add) % mod + base for i in range(n)]
    qs = []
    for j in range(q):
        l = (j * 7919) % n
        qs.append((l, l + (j * 104729) % (n - l)))
    return a, qs


def check(inp):
    a, qs = parse(inp)
    p = [0]
    for x in a:
        p.append(p[-1] + x)
    out = [p[r + 1] - p[l] for l, r in qs]
    if len(out) <= 40:
        return " ".join(map(str, out))
    h = 1469598103934665603
    for x in out:
        h = (h * 1000003 + x + 2000000000) % (1 << 64)
    return "len=%d first=%d last=%d hash=%d" % (len(out), out[0], out[-1], h)


def RANDOM(rng):
    n = rng.randint(1, 8)
    a = [rng.randint(-5, 5) for _ in range(n)]
    q = rng.randint(1, 4)
    qs = []
    for _ in range(q):
        l = rng.randint(0, n - 1)
        qs += [l, rng.randint(l, n - 1)]
    return "L %d %s %d %s" % (n, " ".join(map(str, a)), q, " ".join(map(str, qs)))


MODELS = '''
[[error_models]]
key = "excludes_right_end"
file = "error_models/excludes_right_end.cpp"
skill = "index_range"
description = "Uses prefix[r] - prefix[l], so a[r] is left out of every range."
student_hint = "Is a[r] part of the range from l to r? Check which prefix entries you subtract."

[[error_models]]
key = "prefix_not_accumulated"
file = "error_models/prefix_not_accumulated.cpp"
skill = "update_rule"
description = "Stores each element instead of the running total, so the prefix array is just a shifted copy of a."
student_hint = "What should prefix[i + 1] contain: a[i] alone, or everything up to a[i]?"

[[error_models]]
key = "ignores_left_end"
file = "error_models/ignores_left_end.cpp"
skill = "output_contract"
description = "Returns prefix[r + 1], the sum from the start of the array, ignoring l."
student_hint = "Does your answer change when l changes? Try a query that does not start at index 0."
'''

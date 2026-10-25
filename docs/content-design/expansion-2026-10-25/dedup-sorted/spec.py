HEADER = '''# DEMO CONTENT — public repository, therefore NOT secret (ADR-009).
# Design record: docs/content-design/dedup-sorted.md (bank expansion batch A2, 2026-10-25).

slug = "dedup-sorted"
title = "Remove duplicates in place"
family = "two-pointers"
statement = "statement.md"
harness = "harness.cpp"
reference = "reference.cpp"
solution_file = "solution.cpp" # name the student's code is compiled under
interface = "int remove_duplicates(std::vector<int>& a);"
# Bank expansion (2026-10-25): new problems are not recommendable (CE1 decision E2 applied to
# every new problem). They stay in the problem list and their attempts produce skill evidence.
recommendable = false

[skills]
index_range = "Visiting exactly the valid positions: the loop's start and end cover every element once."
update_rule = "Updating every piece of tracked state on each step (running candidates, pointers, window edges) so no candidate is lost."
output_contract = "Returning exactly what the specification asks for: an index or a value, a sentinel when there is no answer."

[probes]
new_value_last = ["index_range"]
repeat_after_change = ["update_rule"]
values_must_move = ["update_rule"]
count_returned = ["output_contract"]
single = ["output_contract", "index_range"]
large_input = ["update_rule"]

[curriculum]
assumes = ["a sorted array", "a read index and a write index"]
'''

TESTS = [
    dict(key="sample_typical", sample=True, input="L 7 1 1 2 3 3 3 4", probes=["repeat_after_change", "values_must_move", "count_returned"], desc="Some repeated values.", purpose="Visible typical case."),
    dict(key="sample_distinct", sample=True, input="L 3 4 5 6", probes=["new_value_last", "count_returned"], desc="No duplicates.", purpose="Visible case where nothing is removed."),
    dict(key="all_equal", input="L 5 7 7 7 7 7", probes=["count_returned"], desc="Every value equal.", purpose="One value kept."),
    dict(key="single", input="L 1 -3", probes=["single"], desc="One element.", purpose="Minimal input."),
    dict(key="pair_new_last", input="L 2 1 2", probes=["new_value_last"], desc="Two different values.", purpose="The last element is new."),
    dict(key="dups_at_start", input="L 5 0 0 0 1 2", probes=["values_must_move", "new_value_last"], desc="Duplicates only at the start.", purpose="Later values must move forward."),
    dict(key="dups_at_end", input="L 5 1 2 3 3 3", probes=["repeat_after_change"], desc="Duplicates only at the end.", purpose="Repeats after the first value."),
    dict(key="negatives", input="L 6 -5 -5 -2 -2 0 9", probes=["repeat_after_change", "values_must_move", "new_value_last"], desc="Negative values with repeats.", purpose="Mixed signs; last element new."),
    dict(key="first_repeats_only", input="L 4 2 2 2 2", probes=["count_returned"], desc="Four copies of one value.", purpose="All duplicates of the first value."),
    dict(key="alternating_blocks", input="L 8 1 1 2 2 3 3 4 4", probes=["repeat_after_change", "values_must_move"], desc="Every value twice.", purpose="Each value repeated once."),
    dict(key="large_blocks", input="B 100000 3", probes=["large_input", "repeat_after_change"], desc="A long array where each value repeats three times.", purpose="Large input with many duplicates."),
    dict(key="large_distinct", input="B 100000 1", probes=["large_input", "new_value_last"], desc="A long array with no repeats.", purpose="Large input where nothing is removed."),
]


def parse(inp):
    t = inp.split()
    n = int(t[1])
    if t[0] == "L":
        return [int(x) for x in t[2:2 + n]]
    block = int(t[2])
    return [i // block for i in range(n)]


def check(inp):
    a = parse(inp)
    r = [a[0]]
    for x in a[1:]:
        if x != r[-1]:
            r.append(x)
    k = len(r)
    if k <= 40:
        return " ".join(map(str, [k] + r))
    h = 1469598103934665603
    for x in r:
        h = (h * 1000003 + x + 2000000000) % (1 << 64)
    return "%d %d %d %d" % (k, r[0], r[-1], h)


def RANDOM(rng):
    n = rng.randint(1, 10)
    a = sorted(rng.randint(-3, 3) for _ in range(n))
    return "L %d %s" % (n, " ".join(map(str, a)))


MODELS = '''
[[error_models]]
key = "returns_last_index"
file = "error_models/returns_last_index.cpp"
skill = "output_contract"
description = "Returns one less than the number of distinct values, with the kept prefix one element short (for example by returning the index of the last kept element)."
student_hint = "Is the value you return the number of kept elements, or the position of the last one?"
known_limitation = "Attribution not unique (L20): keeping a value when it differs from the next one and forgetting the final element (a loop-range error) gives identical output on every valid input. Diagnoses are reported as qualified and add no skill evidence (docs/content-design/dedup-sorted.md)."

[[error_models]]
key = "skips_last"
file = "error_models/skips_last.cpp"
skill = "index_range"
description = "The read loop stops one element early, so a new value in the last position is lost."
student_hint = "Does your read pointer reach the last element? Try an array whose last value appears only once."

[[error_models]]
key = "compares_to_first"
file = "error_models/compares_to_first.cpp"
skill = "update_rule"
description = "Compares each element with a[0] instead of the last kept value, so duplicates of later values are kept."
student_hint = "Which value should each element be compared with to know whether it is new?"

[[error_models]]
key = "counts_without_writing"
file = "error_models/counts_without_writing.cpp"
skill = "update_rule"
description = "Counts the distinct values correctly but never moves them, so the first k elements are not the distinct values."
student_hint = "After your function returns k, do the first k elements of the array hold the distinct values?"
'''

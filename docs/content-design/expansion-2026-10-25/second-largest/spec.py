HEADER = '''# DEMO CONTENT — public repository, therefore NOT secret (ADR-009).
# Design record: docs/content-design/second-largest.md (bank expansion batch A1, 2026-10-25).

slug = "second-largest"
title = "Second largest distinct value"
family = "arrays"
statement = "statement.md"
harness = "harness.cpp"
reference = "reference.cpp"
solution_file = "solution.cpp" # name the student's code is compiled under
interface = "int second_largest(const std::vector<int>& a);"
# Bank expansion (2026-10-25): new problems are not recommendable (CE1 decision E2 applied to
# every new problem). They stay in the problem list and their attempts produce skill evidence.
recommendable = false

[skills]
index_range = "Visiting exactly the valid positions: the loop's start and end cover every element once."
tie_resolution = "Handling equal values as the specification says: which of several equal candidates wins, and whether duplicates count separately."
update_rule = "Updating every piece of tracked state on each step (running candidates, pointers, window edges) so no candidate is lost."
output_contract = "Returning exactly what the specification asks for: an index or a value, a sentinel when there is no answer."

[probes]
duplicate_max = ["tie_resolution"]
increasing = ["update_rule"]
max_first = ["index_range"]
answer_first = ["index_range"]
no_second = ["output_contract"]
single = ["output_contract", "index_range"]
large_input = ["update_rule"]

[curriculum]
assumes = ["iterating over a std::vector", "tracking a running maximum"]
prerequisites = ["first-max-index"]
'''

TESTS = [
    dict(key="sample_mixed", sample=True, input="L 6 4 9 2 9 7 1", probes=["duplicate_max"], desc="The maximum appears twice.", purpose="Visible typical case with a duplicated maximum."),
    dict(key="sample_none", sample=True, input="L 3 5 5 5", probes=["no_second", "duplicate_max"], desc="Every value equal.", purpose="Visible case with no second distinct value."),
    dict(key="increasing", input="L 5 1 3 5 7 9", probes=["increasing"], desc="Increasing values.", purpose="Each new value is a new maximum; the old one must move to second."),
    dict(key="decreasing", input="L 5 9 7 5 3 1", probes=["max_first"], desc="Decreasing values.", purpose="The maximum is first; the answer is the second element."),
    dict(key="answer_first", input="L 4 8 2 10 3", probes=["answer_first", "increasing"], desc="The answer is the first element.", purpose="The second largest value is at index 0."),
    dict(key="max_first_dups", input="L 5 10 10 4 6 10", probes=["max_first", "duplicate_max"], desc="The maximum first and repeated.", purpose="Repeated maximum including position 0."),
    dict(key="answer_before_max", input="L 3 5 3 9", probes=["answer_first", "increasing"], desc="The answer comes before the maximum, with a smaller value between them.", purpose="Added after the held-out evaluation (2026-10-25): separates no_demotion from a program that only looks after the maximum's position."),
    dict(key="two_distinct", input="L 2 3 8", probes=["increasing", "answer_first"], desc="Two different values.", purpose="Smallest case with an answer; answer first."),
    dict(key="two_equal", input="L 2 6 6", probes=["no_second", "duplicate_max"], desc="Two equal values.", purpose="Smallest case without an answer."),
    dict(key="single", input="L 1 4", probes=["single", "no_second"], desc="One element.", purpose="Minimal input; no answer."),
    dict(key="zero_is_answer", input="L 4 0 5 0 5", probes=["answer_first", "duplicate_max"], desc="The answer is zero.", purpose="0 is a genuine answer, not a sentinel."),
    dict(key="second_dups", input="L 6 2 7 7 9 1 9", probes=["duplicate_max", "increasing"], desc="Both top values repeated.", purpose="Duplicates of the maximum and of the answer."),
    dict(key="large_increasing", input="R 100000 1 0 100000 0", probes=["large_input", "increasing"], desc="A long increasing array.", purpose="Large input; every value a new maximum."),
    dict(key="large_periodic", input="R 100000 7 3 1000 5", probes=["large_input", "duplicate_max"], desc="A long array with repeating values.", purpose="Large input with many duplicates of the maximum."),
]


def parse(inp):
    t = inp.split()
    n = int(t[1])
    if t[0] == "L":
        return [int(x) for x in t[2:2 + n]]
    mult, add, mod, base = map(int, t[2:6])
    return [(i * mult + add) % mod + base for i in range(n)]


def check(inp):
    a = sorted(set(parse(inp)))
    return str(a[-2] if len(a) >= 2 else -1)


def RANDOM(rng):
    n = rng.randint(1, 10)
    hi = rng.choice([1, 3, 9, 30])
    a = [rng.randint(0, hi) for _ in range(n)]
    return "L %d %s" % (n, " ".join(map(str, a)))


MODELS = '''
[[error_models]]
key = "counts_duplicates"
file = "error_models/counts_duplicates.cpp"
skill = "tie_resolution"
description = "Lets a copy of the maximum become the second largest, so a repeated maximum is returned (also the output of sorting and taking the second element)."
student_hint = "If the largest value appears twice, is the second copy a 'second largest distinct value'?"

[[error_models]]
key = "no_demotion"
file = "error_models/no_demotion.cpp"
skill = "update_rule"
description = "When a new maximum appears, the old maximum is not moved to second place."
student_hint = "When you find a new largest value, what should happen to the previous largest value?"

[[error_models]]
key = "skips_first"
file = "error_models/skips_first.cpp"
skill = "index_range"
description = "The loop starts at index 1 without using a[0], so the first element is never considered."
student_hint = "Does your loop consider the first element of the array?"

[[error_models]]
key = "zero_when_none"
file = "error_models/zero_when_none.cpp"
skill = "output_contract"
description = "The second largest starts at 0, so 'no second value' is reported as 0 instead of -1."
student_hint = "What must you return when there is no second distinct value? Check the starting value of your answer."
'''

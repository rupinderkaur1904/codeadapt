HEADER = '''# DEMO CONTENT — public repository, therefore NOT secret (ADR-009).
# Design record: docs/content-design/plus-one.md (bank expansion batch A2, 2026-10-25).

slug = "plus-one"
title = "Add one to a digit array"
family = "arrays"
statement = "statement.md"
harness = "harness.cpp"
reference = "reference.cpp"
solution_file = "solution.cpp" # name the student's code is compiled under
interface = "std::vector<int> plus_one(const std::vector<int>& digits);"
# Bank expansion (2026-10-25): new problems are not recommendable (CE1 decision E2 applied to
# every new problem). They stay in the problem list and their attempts produce skill evidence.
recommendable = false

[skills]
index_range = "Visiting exactly the valid positions: the loop's start and end cover every element once."
update_rule = "Updating every piece of tracked state on each step (running candidates, pointers, window edges) so no candidate is lost."
output_contract = "Returning exactly what the specification asks for: an index or a value, a sentinel when there is no answer."

[probes]
no_carry = ["index_range"]
one_carry = ["index_range", "update_rule"]
carry_chain = ["update_rule"]
all_nines = ["output_contract"]
front_digit_small = ["index_range"]
large_input = ["update_rule"]

[curriculum]
assumes = ["iterating over a std::vector from the back"]
prerequisites = ["first-max-index"]
'''

TESTS = [
    dict(key="sample_simple", sample=True, input="L 3 1 2 3", probes=["no_carry", "front_digit_small"], desc="No carry needed.", purpose="Visible typical case."),
    dict(key="sample_chain", sample=True, input="L 4 1 2 9 9", probes=["carry_chain"], desc="Two trailing nines.", purpose="Visible carry chain."),
    dict(key="one_carry", input="L 3 4 5 9", probes=["one_carry"], desc="One trailing nine.", purpose="A single carry."),
    dict(key="long_chain", input="L 6 3 9 9 9 9 9", probes=["carry_chain"], desc="Many trailing nines.", purpose="A carry through five digits."),
    dict(key="all_nines", input="L 3 9 9 9", probes=["all_nines", "carry_chain"], desc="Every digit is nine.", purpose="The result gains a digit."),
    dict(key="single_nine", input="L 1 9", probes=["all_nines"], desc="The number 9.", purpose="Smallest case that gains a digit."),
    dict(key="single_zero", input="L 1 0", probes=["no_carry"], desc="The number 0.", purpose="Minimal input."),
    dict(key="nine_front", input="L 3 9 0 0", probes=["no_carry"], desc="A leading nine, no carry.", purpose="A nine that must not change."),
    dict(key="nines_front_eight_end", input="L 4 9 9 9 8", probes=["no_carry"], desc="Leading nines, last digit eight.", purpose="Front nines that must not change."),
    dict(key="middle_zero", input="L 4 2 0 9 9", probes=["carry_chain", "front_digit_small"], desc="A zero before the trailing nines.", purpose="The carry stops at a zero."),
    dict(key="ten", input="L 2 1 9", probes=["one_carry", "front_digit_small"], desc="The number 19.", purpose="Two digits with one carry."),
    dict(key="large_all_nines", input="N 100000", probes=["large_input", "all_nines"], desc="A very long run of nines.", purpose="Large input; the result gains a digit."),
    dict(key="large_pattern", input="P 99999", probes=["large_input", "carry_chain"], desc="A very long number ending in 9.", purpose="Large input with a carry."),
]


def parse(inp):
    t = inp.split()
    n = int(t[1])
    if t[0] == "L":
        return [int(x) for x in t[2:2 + n]]
    if t[0] == "N":
        return [9] * n
    return [i % 10 for i in range(1, n + 1)]


def fmt(r):
    if len(r) <= 40:
        return " ".join(map(str, r))
    h = 1469598103934665603
    for x in r:
        h = (h * 1000003 + x + 1000) % (1 << 64)
    return "len=%d first=%d last=%d hash=%d" % (len(r), r[0], r[-1], h)


def check(inp):
    d = parse(inp)
    r = d[:]
    i = len(r) - 1
    while i >= 0 and r[i] == 9:
        r[i] = 0
        i -= 1
    if i < 0:
        r.insert(0, 1)
    else:
        r[i] += 1
    return fmt(r)


def RANDOM(rng):
    n = rng.randint(1, 8)
    d = [rng.choice([9, 9, 9, rng.randint(0, 9)]) for _ in range(n)]
    if n > 1 and d[0] == 0:
        d[0] = rng.randint(1, 9)
    return "L %d %s" % (n, " ".join(map(str, d)))


MODELS = '''
[[error_models]]
key = "single_carry"
file = "error_models/single_carry.cpp"
skill = "update_rule"
description = "Propagates a carry into the next digit only once, so a second 9 becomes 10."
student_hint = "What happens when the digit that receives the carry is also a 9? Try a number ending in 99."

[[error_models]]
key = "no_new_digit"
file = "error_models/no_new_digit.cpp"
skill = "output_contract"
description = "Drops the carry out of the most significant digit, so 999 becomes 000."
student_hint = "What is 999 + 1? Check what you return when every digit is 9."

[[error_models]]
key = "adds_at_front"
file = "error_models/adds_at_front.cpp"
skill = "index_range"
description = "Adds at digits[0] and carries towards the end, treating the first digit as the least significant."
student_hint = "Which digit is the least significant one? The first element is the most significant digit."

[[error_models]]
key = "carry_never_cleared"
file = "error_models/carry_never_cleared.cpp"
skill = "update_rule"
description = "The carry starts at 1 but is never cleared, so 1 is added to every digit."
student_hint = "After a digit absorbs the carry without overflowing, should later digits still receive it?"
'''

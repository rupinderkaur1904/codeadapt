HEADER = '''# DEMO CONTENT — public repository, therefore NOT secret (ADR-009).
# Design record: docs/content-design/first-max-index.md (bank expansion batch A1, 2026-10-25).

slug = "first-max-index"
title = "Index of the first maximum"
family = "arrays"
statement = "statement.md"
harness = "harness.cpp"
reference = "reference.cpp"
solution_file = "solution.cpp" # name the student's code is compiled under
interface = "int first_max_index(const std::vector<int>& a);"
# Bank expansion (2026-10-25): new problems are not recommendable (CE1 decision E2 applied to
# every new problem). They stay in the problem list and their attempts produce skill evidence.
recommendable = false

[skills]
index_range = "Visiting exactly the valid positions: the loop's start and end cover every element once."
accumulator_init = "Initialising (and re-initialising) a running best, minimum, maximum, count or sum to the value the first real element requires."
tie_resolution = "Handling equal values as the specification says: which of several equal candidates wins, and whether duplicates count separately."
output_contract = "Returning exactly what the specification asks for: an index or a value, a sentinel when there is no answer."

[probes]
max_first = ["index_range"]
max_last = ["index_range"]
all_negative = ["accumulator_init"]
zero_max_later = ["accumulator_init"]
tied_max = ["tie_resolution"]
index_not_value = ["output_contract"]
single = ["index_range", "accumulator_init"]
large_input = ["index_range"]

[curriculum]
assumes = ["iterating over a std::vector by index"]
'''

TESTS = [
    dict(key="sample_mixed", sample=True, input="L 6 3 9 2 9 5 1", probes=["tied_max", "index_not_value"], desc="Mixed values with the maximum twice.", purpose="Visible typical case with a tie."),
    dict(key="sample_last", sample=True, input="L 4 1 2 3 7", probes=["max_last", "index_not_value"], desc="Increasing values.", purpose="Visible case: maximum in the last position."),
    dict(key="max_at_start", input="L 5 8 1 2 3 4", probes=["max_first"], desc="Maximum first.", purpose="The answer is index 0."),
    dict(key="max_at_end_neg", input="L 4 -9 -8 -7 -3", probes=["max_last", "all_negative"], desc="Negative values, maximum last.", purpose="All negative; maximum in the last position."),
    dict(key="all_negative_mid", input="L 5 -5 -4 -1 -6 -2", probes=["all_negative", "index_not_value"], desc="All values negative.", purpose="All negative; maximum in the middle."),
    dict(key="all_negative_tie", input="L 5 -7 -2 -9 -2 -3", probes=["all_negative", "tied_max"], desc="Negative values with a tie for the maximum.", purpose="All negative with a tied maximum."),
    dict(key="zero_max_later", input="L 4 -3 0 -1 0", probes=["zero_max_later", "tied_max"], desc="The maximum is zero.", purpose="Maximum 0 after position 0, tied."),
    dict(key="all_equal", input="L 5 4 4 4 4 4", probes=["tied_max"], desc="Every value equal.", purpose="Every element ties."),
    dict(key="tie_at_ends", input="L 5 6 1 2 3 6", probes=["tied_max", "max_last", "max_first"], desc="The maximum appears first and last.", purpose="Tie between the first and last position."),
    dict(key="small_values", input="L 5 0 1 0 2 1", probes=["index_not_value"], desc="Small non-negative values.", purpose="Index and value differ."),
    dict(key="single", input="L 1 -5", probes=["single", "all_negative"], desc="One element.", purpose="Minimal input."),
    dict(key="two_elements", input="L 2 -1 -1", probes=["tied_max", "all_negative"], desc="Two equal negative values.", purpose="Smallest tie."),
    dict(key="large_last", input="R 100000 1 0 100000 -50000", probes=["large_input", "max_last"], desc="A long increasing array.", purpose="Large input; maximum last."),
    dict(key="large_periodic", input="R 100000 7 3 1000 -2000", probes=["large_input", "tied_max", "all_negative"], desc="A long array with repeating negative values.", purpose="Large input with many ties, all negative."),
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
    return str(a.index(max(a)))


def RANDOM(rng):
    n = rng.randint(1, 12)
    lo = rng.choice([-20, -10, 0])
    hi = rng.choice([-1, 5, 20])
    a = [rng.randint(lo, max(lo, hi)) for _ in range(n)]
    return "L %d %s" % (n, " ".join(map(str, a)))


MODELS = '''
[[error_models]]
key = "max_starts_at_zero"
file = "error_models/max_starts_at_zero.cpp"
skill = "accumulator_init"
description = "Starts the running maximum at 0, so an all-negative array (or a maximum of 0 after position 0) keeps index 0."
student_hint = "What is your running maximum before you have looked at any element? Try an array whose values are all negative."

[[error_models]]
key = "last_of_ties"
file = "error_models/last_of_ties.cpp"
skill = "tie_resolution"
description = "Returns the last of several equal maxima, for example by replacing the best index on >= (or, with identical output, by scanning from the end with >)."
student_hint = "When the maximum appears more than once, which position should you return? Check how your loop decides which of two equal values to keep."

[[error_models]]
key = "skips_last"
file = "error_models/skips_last.cpp"
skill = "index_range"
description = "The loop stops one element early, so a maximum in the last position is missed."
student_hint = "Does your loop look at the last element? Try an array whose largest value is at the end."

[[error_models]]
key = "returns_value"
file = "error_models/returns_value.cpp"
skill = "output_contract"
description = "Returns the maximum value instead of its index."
student_hint = "Re-read what the function must return: a position in the array, or a value from it?"
'''

HEADER = '''# DEMO CONTENT — public repository, therefore NOT secret (ADR-009).
# Design record: docs/content-design/longest-run.md (bank expansion batch A1, 2026-10-25).

slug = "longest-run"
title = "Longest run of equal values"
family = "arrays"
statement = "statement.md"
harness = "harness.cpp"
reference = "reference.cpp"
solution_file = "solution.cpp" # name the student's code is compiled under
interface = "int longest_run(const std::vector<int>& a);"
# Bank expansion (2026-10-25): new problems are not recommendable (CE1 decision E2 applied to
# every new problem). They stay in the problem list and their attempts produce skill evidence.
recommendable = false

[skills]
accumulator_init = "Initialising (and re-initialising) a running best, minimum, maximum, count or sum to the value the first real element requires."
update_rule = "Updating every piece of tracked state on each step (running candidates, pointers, window edges) so no candidate is lost."
output_contract = "Returning exactly what the specification asks for: an index or a value, a sentinel when there is no answer."

[probes]
longest_not_first = ["accumulator_init"]
longest_last = ["update_rule"]
run_not_first_value = ["update_rule"]
length_not_value = ["output_contract"]
single = ["accumulator_init", "update_rule"]
large_input = ["update_rule"]

[curriculum]
assumes = ["comparing neighbouring elements of a std::vector"]
prerequisites = ["first-max-index"]
'''

TESTS = [
    dict(key="sample_middle", sample=True, input="L 8 1 1 2 2 2 3 1 1", probes=["longest_not_first", "run_not_first_value", "length_not_value"], desc="The longest run is in the middle.", purpose="Visible typical case."),
    dict(key="sample_end", sample=True, input="L 6 4 5 5 7 7 7", probes=["longest_last", "longest_not_first", "run_not_first_value"], desc="The longest run is at the end.", purpose="Visible case: final run is the longest."),
    dict(key="first_run_longest", input="L 6 9 9 9 2 2 5", probes=["length_not_value"], desc="The first run is the longest.", purpose="The answer comes from the first run."),
    dict(key="all_equal", input="L 5 6 6 6 6 6", probes=["longest_last", "length_not_value"], desc="Every value equal.", purpose="One run covering the whole array."),
    dict(key="all_distinct", input="L 5 3 1 4 1 5", probes=["length_not_value"], desc="No two neighbours equal.", purpose="Every run has length 1."),
    dict(key="single", input="L 1 8", probes=["single"], desc="One element.", purpose="Minimal input."),
    dict(key="two_equal", input="L 2 -4 -4", probes=["longest_last"], desc="Two equal values.", purpose="Smallest run of 2; it is the final run."),
    dict(key="nonadjacent_repeat", input="L 7 2 5 2 2 5 5 5", probes=["run_not_first_value", "longest_last", "longest_not_first"], desc="Values reappear after a gap.", purpose="Runs equal to a[0] but not adjacent to it."),
    dict(key="first_value_returns", input="L 7 0 0 3 0 0 0 1", probes=["run_not_first_value", "longest_not_first"], desc="The first value comes back later in a longer run.", purpose="A later run of a[0]'s value is the longest."),
    dict(key="two_longest", input="L 7 1 1 1 2 3 3 3", probes=["longest_last", "length_not_value"], desc="Two runs tie for the longest.", purpose="Tie between the first and last run."),
    dict(key="negatives", input="L 6 -1 -1 -2 -2 -2 0", probes=["longest_not_first", "run_not_first_value"], desc="Negative values.", purpose="The longest run is negative and not first."),
    dict(key="large_one_run", input="R 100000 0 7 100 0", probes=["large_input", "longest_last"], desc="A long array of one value.", purpose="Large input that is a single run."),
    dict(key="large_blocks", input="R 100000 1 0 100000 0", probes=["large_input"], desc="A long array with no repeats.", purpose="Large input where every run has length 1."),
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
    best = run = 1
    for i in range(1, len(a)):
        run = run + 1 if a[i] == a[i - 1] else 1
        best = max(best, run)
    return str(best)


def RANDOM(rng):
    n = rng.randint(1, 12)
    k = rng.choice([1, 2, 3])
    a = [rng.randint(0, k) for _ in range(n)]
    return "L %d %s" % (n, " ".join(map(str, a)))


MODELS = '''
[[error_models]]
key = "reset_to_zero"
file = "error_models/reset_to_zero.cpp"
skill = "accumulator_init"
description = "Restarts a new run's length at 0 instead of 1, so every run after the first is counted one too short."
student_hint = "When a new run starts, how long is it already? Check the value you reset your counter to."

[[error_models]]
key = "last_run_unchecked"
file = "error_models/last_run_unchecked.cpp"
skill = "update_rule"
description = "Updates the best length only when a run ends, so the final run is never compared."
student_hint = "What happens to the run that is still going when the loop ends? Try an array whose longest run is at the end."

[[error_models]]
key = "returns_value"
file = "error_models/returns_value.cpp"
skill = "output_contract"
description = "Returns the value that forms the longest run instead of the run's length."
student_hint = "Re-read what the function must return: the length of a run, or the value repeated in it?"

[[error_models]]
key = "compares_to_first"
file = "error_models/compares_to_first.cpp"
skill = "update_rule"
description = "Compares each element with a[0] instead of with its neighbour, so only runs of a[0]'s value are extended."
student_hint = "Which element should each element be compared with to decide whether the run continues?"
'''

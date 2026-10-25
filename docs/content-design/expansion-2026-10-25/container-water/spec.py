HEADER = '''# DEMO CONTENT — public repository, therefore NOT secret (ADR-009).
# Design record: docs/content-design/container-water.md (bank expansion batch A2, 2026-10-25).

slug = "container-water"
title = "Container with most water"
family = "two-pointers"
statement = "statement.md"
harness = "harness.cpp"
reference = "reference.cpp"
solution_file = "solution.cpp" # name the student's code is compiled under
interface = "int max_water(const std::vector<int>& height);"
# Bank expansion (2026-10-25): new problems are not recommendable (CE1 decision E2 applied to
# every new problem). They stay in the problem list and their attempts produce skill evidence.
recommendable = false

[skills]
index_range = "Visiting exactly the valid positions: the loop's start and end cover every element once."
update_rule = "Updating every piece of tracked state on each step (running candidates, pointers, window edges) so no candidate is lost."
output_contract = "Returning exactly what the specification asks for: an index or a value, a sentinel when there is no answer."

[probes]
inner_pair_best = ["update_rule"]
adjacent_best = ["index_range"]
width_counts = ["index_range"]
shorter_limits = ["output_contract"]
large_input = ["update_rule"]

[curriculum]
assumes = ["two indices moving towards each other"]
prerequisites = ["closest-pair-sum"]
'''

TESTS = [
    dict(key="sample_classic", sample=True, input="L 9 1 8 6 2 5 4 8 3 7", probes=["inner_pair_best", "shorter_limits", "width_counts"], desc="The classic example.", purpose="Visible typical case."),
    dict(key="sample_two", sample=True, input="L 2 1 1", probes=["adjacent_best", "width_counts"], desc="Two lines of height 1.", purpose="Visible minimal case."),
    dict(key="outer_best", input="L 5 6 1 1 1 6", probes=["width_counts", "shorter_limits"], desc="The outermost lines are tallest.", purpose="The answer is the outer pair."),
    dict(key="inner_tall_pair", input="L 6 1 9 2 2 9 1", probes=["inner_pair_best"], desc="Two tall lines inside short ones.", purpose="Moving the taller pointer loses the inner pair."),
    dict(key="adjacent_tallest", input="L 5 1 0 0 9 9", probes=["adjacent_best", "inner_pair_best"], desc="The two tallest lines are neighbours.", purpose="The best container has width 1."),
    dict(key="neighbours_last", input="L 3 1 5 5", probes=["adjacent_best"], desc="Two equal tall lines at the end.", purpose="The best pair is the last pair the pointers reach."),
    dict(key="uneven_ends", input="L 4 2 3 4 10", probes=["shorter_limits"], desc="A very tall last line.", purpose="The shorter line decides the level."),
    dict(key="with_zeros", input="L 5 0 5 0 5 0", probes=["shorter_limits", "inner_pair_best"], desc="Some lines have height 0.", purpose="Zero-height ends hold no water."),
    dict(key="increasing", input="L 6 1 2 3 4 5 6", probes=["inner_pair_best", "width_counts"], desc="Increasing heights.", purpose="The best pair is not the outer pair."),
    dict(key="decreasing", input="L 5 9 7 5 3 1", probes=["inner_pair_best"], desc="Decreasing heights.", purpose="Mirror of the increasing case."),
    dict(key="equal_heights", input="L 4 3 3 3 3", probes=["width_counts", "shorter_limits"], desc="Every line equal.", purpose="Ties between the ends."),
    dict(key="large_sawtooth", input="R 100000 37 11 10000 0", probes=["large_input", "width_counts"], desc="A long, jagged skyline.", purpose="Large input."),
    dict(key="large_blocks", input="R 100000 1 0 10000 1", probes=["large_input", "inner_pair_best"], desc="A long skyline of repeated ramps.", purpose="Large input; the best pair is not the outer pair."),
]


def parse(inp):
    t = inp.split()
    n = int(t[1])
    if t[0] == "L":
        return [int(x) for x in t[2:2 + n]]
    mult, add, mod, base = map(int, t[2:6])
    return [(i * mult + add) % mod + base for i in range(n)]


def check(inp):
    h = parse(inp)
    lo, hi, best = 0, len(h) - 1, 0
    while lo < hi:
        best = max(best, min(h[lo], h[hi]) * (hi - lo))
        if h[lo] < h[hi]:
            lo += 1
        else:
            hi -= 1
    return str(best)


def RANDOM(rng):
    n = rng.randint(2, 9)
    return "L %d %s" % (n, " ".join(str(rng.randint(0, 9)) for _ in range(n)))


MODELS = '''
[[error_models]]
key = "moves_taller"
file = "error_models/moves_taller.cpp"
skill = "update_rule"
description = "Moves the pointer at the taller line, discarding a line that could still form a larger container."
student_hint = "Which of the two lines limits every container that uses it? That is the one you can safely discard."
known_limitation = "Attribution not unique (L20): moving the taller line never finds a larger container than the outermost pair, so this model is output-identical on every valid input to a program that only measures the outermost pair (a misread specification). Diagnoses are reported as qualified and add no skill evidence (docs/content-design/container-water.md)."

[[error_models]]
key = "width_plus_one"
file = "error_models/width_plus_one.cpp"
skill = "index_range"
description = "Counts the width as hi - lo + 1 (the number of lines) instead of the distance between them."
student_hint = "How wide is a container between positions 2 and 5? Count the gaps, not the lines."

[[error_models]]
key = "uses_taller_height"
file = "error_models/uses_taller_height.cpp"
skill = "output_contract"
description = "Uses the taller line as the water level instead of the shorter one."
student_hint = "Which of the two lines decides how high the water can rise before it spills?"

[[error_models]]
key = "stops_before_adjacent"
file = "error_models/stops_before_adjacent.cpp"
skill = "index_range"
description = "Loops while lo + 1 < hi, so the last pair of neighbouring lines is never checked."
student_hint = "Does your loop check a pair of neighbouring lines? Try two tall lines next to each other."
'''

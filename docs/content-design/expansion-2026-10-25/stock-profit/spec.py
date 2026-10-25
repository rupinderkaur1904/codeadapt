HEADER = '''# DEMO CONTENT — public repository, therefore NOT secret (ADR-009).
# Design record: docs/content-design/stock-profit.md (bank expansion batch A1, 2026-10-25).

slug = "stock-profit"
title = "Best single trade"
family = "arrays"
statement = "statement.md"
harness = "harness.cpp"
reference = "reference.cpp"
solution_file = "solution.cpp" # name the student's code is compiled under
interface = "int max_profit(const std::vector<int>& prices);"
# Bank expansion (2026-10-25): new problems are not recommendable (CE1 decision E2 applied to
# every new problem). They stay in the problem list and their attempts produce skill evidence.
recommendable = false

[skills]
index_range = "Visiting exactly the valid positions: the loop's start and end cover every element once."
output_contract = "Returning exactly what the specification asks for: an index or a value, a sentinel when there is no answer."

[probes]
min_after_max = ["output_contract"]
best_sale_last = ["index_range"]
falling = ["output_contract"]
single_day = ["output_contract"]
large_input = ["index_range"]

[curriculum]
assumes = ["tracking a running minimum while scanning"]
prerequisites = ["first-max-index"]
'''

TESTS = [
    dict(key="sample_typical", sample=True, input="L 6 7 1 5 3 6 4", probes=["best_sale_last"], desc="A typical week of prices.", purpose="Visible typical case."),
    dict(key="sample_falling", sample=True, input="L 5 7 6 4 3 1", probes=["falling", "min_after_max"], desc="Prices only fall.", purpose="Visible case with no profitable trade."),
    dict(key="rise_last_day", input="L 5 3 4 2 5 9", probes=["best_sale_last"], desc="The best sale is on the last day.", purpose="The answer needs the last day."),
    dict(key="peak_then_dip", input="L 6 2 9 4 8 1 3", probes=["min_after_max"], desc="A high price early, the lowest price late.", purpose="The global minimum comes after the global maximum."),
    dict(key="min_after_max_flat", input="L 4 5 8 6 1", probes=["min_after_max"], desc="Rise, then a deep fall.", purpose="Global spread is not achievable."),
    dict(key="flat", input="L 4 5 5 5 5", probes=["falling"], desc="Constant prices.", purpose="Zero profit without a loss."),
    dict(key="single_day", input="L 1 4", probes=["single_day"], desc="One day only.", purpose="Minimal input: no trade possible."),
    dict(key="two_days_up", input="L 2 1 10", probes=["best_sale_last"], desc="Two days, rising.", purpose="Smallest profitable case; sale on the last day."),
    dict(key="two_days_down", input="L 2 10 1", probes=["falling", "min_after_max"], desc="Two days, falling.", purpose="Smallest losing case."),
    dict(key="late_low_late_high", input="L 7 8 6 9 2 3 7 1", probes=["min_after_max"], desc="Several rises and falls.", purpose="The best trade is in the middle; the last day is the lowest."),
    dict(key="large_rising", input="R 10000 1 0 10000 1", probes=["large_input", "best_sale_last"], desc="A long rising market.", purpose="Large input; best sale on the last day."),
    dict(key="dip_then_last_rise", input="L 5 9 3 5 2 8", probes=["best_sale_last", "min_after_max"], desc="An early high, a late low, then a rise on the last day.", purpose="The best sale is last and the global spread is not achievable."),
    dict(key="large_sawtooth", input="R 100000 37 5 10000 1", probes=["large_input", "min_after_max"], desc="A long market that rises and falls repeatedly.", purpose="Large input with many local trades."),
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
    best, lo = 0, a[0]
    for x in a[1:]:
        best = max(best, x - lo)
        lo = min(lo, x)
    return str(best)


def RANDOM(rng):
    n = rng.randint(1, 10)
    a = [rng.randint(1, rng.choice([3, 10, 50])) for _ in range(n)]
    return "L %d %s" % (n, " ".join(map(str, a)))


MODELS = '''
[[error_models]]
key = "ignores_order"
file = "error_models/ignores_order.cpp"
skill = "output_contract"
description = "Returns the overall maximum minus the overall minimum, ignoring that the purchase must come before the sale (sorting the prices gives the same output)."
student_hint = "Can you sell on a day before the day you buy? Try prices whose lowest value comes after their highest."
known_limitation = "Attribution not unique (L20): sorting the prices (a misread specification) and tracking the overall minimum and maximum separately (an update error) give identical output on every valid input. Diagnoses are reported as qualified and add no skill evidence (design record docs/content-design/stock-profit.md)."

[[error_models]]
key = "allows_loss"
file = "error_models/allows_loss.cpp"
skill = "output_contract"
description = "Insists on one trade, so a falling market gives a negative profit (and a single day gives INT_MIN) instead of 0."
student_hint = "What should you return when no trade makes money? Check the starting value of your answer."

[[error_models]]
key = "misses_last_day"
file = "error_models/misses_last_day.cpp"
skill = "index_range"
description = "The loop stops one day early, so selling on the last day is never considered."
student_hint = "Does your loop consider selling on the very last day?"
'''

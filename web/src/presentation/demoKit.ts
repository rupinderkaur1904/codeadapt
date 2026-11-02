// Prepared test data for the live demo: four lower-bound programs copied verbatim from
// eval/heldout/lower-bound/. They were written by the project author, not by students. The
// expected outcomes are the recorded method v1.3 results in
// docs/evaluation/l20-original-s1-2026-10-26/heldout/lower-bound.md; rehearse before presenting.

export type DemoProgram = {
  file: string;
  intent: string;
  expect: string;
  shows: string;
  source: string;
};

export const DEMO_PROGRAMS: DemoProgram[] = [
  {
    file: "correct_iterative.cpp",
    intent: "correct, different style",
    expect: "no_failure_observed",
    shows: "All 17 tests pass. The message still says tests cannot prove correctness.",
    source: `#include <vector>

// A correct solution in a different style (step-halving), not derived from the reference.
int lower_bound_index(const std::vector<int>& a, int target) {
    int pos = 0;
    int n = static_cast<int>(a.size());
    int step = 1;
    while (step * 2 <= n) step *= 2;
    for (; step > 0; step /= 2) {
        if (pos + step <= n && a[pos + step - 1] < target) pos += step;
    }
    return pos;
}
`,
  },
  {
    file: "recursive_early_equal.cpp",
    intent: "returns on the first equal element",
    expect: "hypothesis_supported: stops_at_first_match",
    shows: "One known mistake fits every failing test, so the student gets a hint.",
    source: `#include <vector>

namespace {
int search(const std::vector<int>& v, int x, int from, int to) {
    if (from >= to) return from;
    int m = (from + to) / 2;
    if (v[m] == x) return m;  // found it
    return v[m] < x ? search(v, x, m + 1, to) : search(v, x, from, m);
}
}  // namespace

int lower_bound_index(const std::vector<int>& a, int target) {
    return search(a, target, 0, static_cast<int>(a.size()));
}
`,
  },
  {
    file: "double_bug.cpp",
    intent: "two mistakes at once",
    expect: "unmodelled_behaviour",
    shows:
      "No single known mistake explains it, so the system shows failing cases and does not guess.",
    source: `#include <vector>

// Two modelled bugs at once (hi = n - 1 and <=): outside the single-error model space.
int lower_bound_index(const std::vector<int>& a, int target) {
    int lo = 0;
    int hi = static_cast<int>(a.size()) - 1;
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;
        if (a[mid] <= target) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo;
}
`,
  },
  {
    file: "size_t_stuck_left.cpp",
    intent: "loop never makes progress",
    expect: "non_termination_observed",
    shows: "A time limit is reported as a symptom. No mistake is named.",
    source: `#include <cstddef>
#include <vector>

// Unsigned half-open search written with an explicit break; the left update keeps \`half\`
// instead of moving past it.
int lower_bound_index(const std::vector<int>& a, int target) {
    std::size_t first = 0;
    std::size_t last = a.size();
    for (;;) {
        if (first >= last) break;
        std::size_t half = first + (last - first) / 2;
        if (a[half] < target)
            first = half;
        else
            last = half;
    }
    return static_cast<int>(first);
}
`,
  },
];

#include <vector>

// cause: reads "find the peak" as "return the peak value" (specification), via a linear scan.
// cause-skill: problem_specification (same skill as the model)
// compare-with: returns_value
int peak_index(const std::vector<int>& a) {
    int best = a[0];
    for (int x : a) if (x > best) best = x;
    return best;
}

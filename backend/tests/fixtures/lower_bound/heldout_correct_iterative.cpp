#include <vector>

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

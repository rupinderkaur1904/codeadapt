#include <vector>

// Alternative cause for last_of_ties: scanning from the end with `>` (direction, not comparison).
int first_max_index(const std::vector<int>& a) {
    int best = static_cast<int>(a.size()) - 1;
    for (int i = best - 1; i >= 0; --i) {
        if (a[i] > a[best]) best = i;
    }
    return best;
}

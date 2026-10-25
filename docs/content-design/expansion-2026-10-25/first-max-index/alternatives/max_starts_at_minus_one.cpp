#include <vector>

// Alternative cause for max_starts_at_zero: an initial value of -1 (still a fixed sentinel).
int first_max_index(const std::vector<int>& a) {
    int best_value = -1, best = 0;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        if (a[i] > best_value) { best_value = a[i]; best = i; }
    }
    return best;
}

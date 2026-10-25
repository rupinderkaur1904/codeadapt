#include <vector>

// Error model: `>=` replaces the best index on equal values, so the last maximum is returned.
int first_max_index(const std::vector<int>& a) {
    int best = 0;
    for (int i = 1; i < static_cast<int>(a.size()); ++i) {
        if (a[i] >= a[best]) best = i;
    }
    return best;
}

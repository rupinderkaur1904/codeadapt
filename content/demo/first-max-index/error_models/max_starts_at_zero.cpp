#include <vector>

// Error model: the running maximum starts at 0 instead of the first element, so an array whose
// values are all negative (or whose maximum is 0 after position 0) keeps index 0.
int first_max_index(const std::vector<int>& a) {
    int best_value = 0, best = 0;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        if (a[i] > best_value) { best_value = a[i]; best = i; }
    }
    return best;
}

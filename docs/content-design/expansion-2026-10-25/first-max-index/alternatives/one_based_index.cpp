#include <vector>

// Alternative (unmodelled) error: returns a 1-based position.
int first_max_index(const std::vector<int>& a) {
    int best = 0;
    for (int i = 1; i < static_cast<int>(a.size()); ++i) {
        if (a[i] > a[best]) best = i;
    }
    return best + 1;
}

#include <vector>

// Error model: returns the maximum value instead of its index.
int first_max_index(const std::vector<int>& a) {
    int best = 0;
    for (int i = 1; i < static_cast<int>(a.size()); ++i) {
        if (a[i] > a[best]) best = i;
    }
    return a[best];
}

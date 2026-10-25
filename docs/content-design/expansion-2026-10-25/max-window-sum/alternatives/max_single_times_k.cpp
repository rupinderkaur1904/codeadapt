#include <algorithm>
#include <vector>

// Alternative (unmodelled) error: k times the largest element.
int max_window_sum(const std::vector<int>& a, int k) {
    return *std::max_element(a.begin(), a.end()) * k;
}

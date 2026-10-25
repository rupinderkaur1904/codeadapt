#include <algorithm>
#include <climits>
#include <cstdlib>
#include <vector>

// For each i, binary-searches the best partner among positions after i.
int closest_pair_gap(const std::vector<int>& a, int target) {
    int best = INT_MAX;
    for (std::size_t i = 0; i + 1 < a.size(); ++i) {
        const long long want = static_cast<long long>(target) - a[i];
        auto it = std::lower_bound(a.begin() + static_cast<long>(i) + 1, a.end(), want);
        if (it != a.end()) best = std::min(best, std::abs(a[i] + *it - target));
        if (it != a.begin() + static_cast<long>(i) + 1) best = std::min(best, std::abs(a[i] + *(it - 1) - target));
    }
    return best;
}

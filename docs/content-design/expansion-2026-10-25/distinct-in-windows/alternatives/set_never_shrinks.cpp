#include <set>
#include <vector>

// Alternative cause for keeps_zero_counts: a std::set that only grows.
std::vector<int> distinct_in_windows(const std::vector<int>& a, int k) {
    std::set<int> seen;
    std::vector<int> out;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        seen.insert(a[i]);
        if (i >= k - 1) out.push_back(static_cast<int>(seen.size()));
    }
    return out;
}

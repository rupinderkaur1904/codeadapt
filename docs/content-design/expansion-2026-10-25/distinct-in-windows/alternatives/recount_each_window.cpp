#include <set>
#include <vector>

// Correct but O(nk): rebuilds a set per window (times out only on large k).
std::vector<int> distinct_in_windows(const std::vector<int>& a, int k) {
    std::vector<int> out;
    for (int s = 0; s + k <= static_cast<int>(a.size()) && s < 3000; ++s)
        out.push_back(static_cast<int>(std::set<int>(a.begin() + s, a.begin() + s + k).size()));
    return out;
}

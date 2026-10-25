#include <utility>
#include <vector>

// Alternative cause for excludes_right_end: a direct loop i < r (slow on large inputs; capped).
std::vector<long long> range_sums(const std::vector<int>& a,
                                  const std::vector<std::pair<int, int>>& queries) {
    std::vector<long long> out;
    for (const auto& [l, r] : queries) {
        long long s = 0;
        for (int i = l; i < r; ++i) s += a[i];
        out.push_back(s);
        if (out.size() > 50) break;
    }
    return out;
}

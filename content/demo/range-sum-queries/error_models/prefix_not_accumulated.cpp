#include <utility>
#include <vector>

// Error model: stores each element instead of the running total, so "prefix" differences are
// a[r] - a[l - 1].
std::vector<long long> range_sums(const std::vector<int>& a,
                                  const std::vector<std::pair<int, int>>& queries) {
    std::vector<long long> prefix(a.size() + 1, 0);
    for (std::size_t i = 0; i < a.size(); ++i) prefix[i + 1] = a[i];
    std::vector<long long> out;
    for (const auto& [l, r] : queries) out.push_back(prefix[r + 1] - prefix[l]);
    return out;
}

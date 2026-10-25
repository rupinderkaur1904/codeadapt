#include <utility>
#include <vector>

// Error model: uses prefix[r] - prefix[l], so a[r] is left out of every sum.
std::vector<long long> range_sums(const std::vector<int>& a,
                                  const std::vector<std::pair<int, int>>& queries) {
    std::vector<long long> prefix(a.size() + 1, 0);
    for (std::size_t i = 0; i < a.size(); ++i) prefix[i + 1] = prefix[i] + a[i];
    std::vector<long long> out;
    for (const auto& [l, r] : queries) out.push_back(prefix[r] - prefix[l]);
    return out;
}

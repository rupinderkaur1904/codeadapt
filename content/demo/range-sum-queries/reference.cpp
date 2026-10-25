#include <utility>
#include <vector>

// prefix[i] is the sum of the first i elements, so a[l..r] sums to prefix[r + 1] - prefix[l].
std::vector<long long> range_sums(const std::vector<int>& a,
                                  const std::vector<std::pair<int, int>>& queries) {
    std::vector<long long> prefix(a.size() + 1, 0);
    for (std::size_t i = 0; i < a.size(); ++i) prefix[i + 1] = prefix[i] + a[i];
    std::vector<long long> out;
    out.reserve(queries.size());
    for (const auto& [l, r] : queries) out.push_back(prefix[r + 1] - prefix[l]);
    return out;
}

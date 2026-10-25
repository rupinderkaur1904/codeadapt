#include <utility>
#include <vector>

// Error model: returns prefix[r + 1], the sum from the start of the array, ignoring l.
std::vector<long long> range_sums(const std::vector<int>& a,
                                  const std::vector<std::pair<int, int>>& queries) {
    std::vector<long long> prefix(a.size() + 1, 0);
    for (std::size_t i = 0; i < a.size(); ++i) prefix[i + 1] = prefix[i] + a[i];
    std::vector<long long> out;
    for (const auto& [l, r] : queries) out.push_back(prefix[r + 1]);
    return out;
}

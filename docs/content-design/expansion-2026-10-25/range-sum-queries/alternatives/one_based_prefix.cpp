#include <utility>
#include <vector>

// Alternative (unmodelled) error: prefix[i] includes a[i] and the query uses prefix[r] - prefix[l].
std::vector<long long> range_sums(const std::vector<int>& a,
                                  const std::vector<std::pair<int, int>>& queries) {
    std::vector<long long> prefix(a.size(), 0);
    long long run = 0;
    for (std::size_t i = 0; i < a.size(); ++i) { run += a[i]; prefix[i] = run; }
    std::vector<long long> out;
    for (const auto& [l, r] : queries) out.push_back(prefix[r] - prefix[l]);
    return out;
}

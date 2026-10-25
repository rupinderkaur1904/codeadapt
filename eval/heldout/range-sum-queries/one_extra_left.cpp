#include <utility>
#include <vector>

std::vector<long long> range_sums(const std::vector<int>& a,
                                  const std::vector<std::pair<int, int>>& queries) {
    std::vector<long long> p(a.size());
    long long run = 0;
    for (size_t i = 0; i < a.size(); i++) p[i] = run += a[i];
    std::vector<long long> ans;
    for (auto [l, r] : queries) ans.push_back(p[r] - (l > 1 ? p[l - 2] : 0));
    return ans;
}

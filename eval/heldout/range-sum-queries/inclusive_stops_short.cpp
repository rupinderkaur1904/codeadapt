#include <utility>
#include <vector>

std::vector<long long> range_sums(const std::vector<int>& a,
                                  const std::vector<std::pair<int, int>>& queries) {
    std::vector<long long> p(a.size());
    long long run = 0;
    for (size_t i = 0; i < a.size(); i++) p[i] = run += a[i];
    auto upto = [&](int i) { return i >= 0 ? p[i] : 0LL; };
    std::vector<long long> ans;
    for (auto [l, r] : queries) ans.push_back(upto(r - 1) - upto(l - 1));
    return ans;
}

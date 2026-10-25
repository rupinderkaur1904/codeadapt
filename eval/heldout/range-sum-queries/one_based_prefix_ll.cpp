#include <utility>
#include <vector>

std::vector<long long> range_sums(const std::vector<int>& a,
                                  const std::vector<std::pair<int, int>>& queries) {
    int n = a.size();
    std::vector<long long> s(n + 1);
    for (int i = 1; i <= n; i++) s[i] = s[i - 1] + a[i - 1];
    std::vector<long long> ans;
    for (auto q : queries) {
        int l = q.first + 1, r = q.second + 1;
        ans.push_back(s[r] - s[l - 1]);
    }
    return ans;
}

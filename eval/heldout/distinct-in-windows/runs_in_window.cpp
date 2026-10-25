#include <vector>

std::vector<int> distinct_in_windows(const std::vector<int>& a, int k) {
    int n = a.size();
    std::vector<int> change(n, 0);
    for (int i = 1; i < n; i++) change[i] = change[i - 1] + (a[i] != a[i - 1]);
    std::vector<int> res;
    for (int s = 0; s + k <= n; s++) res.push_back(1 + change[s + k - 1] - change[s]);
    return res;
}

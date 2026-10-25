#include <vector>

int pivot_index(const std::vector<int>& a) {
    int n = a.size();
    std::vector<long long> pre(n + 1, 0), suf(n + 2, 0);
    for (int i = 0; i < n; i++) pre[i + 1] = pre[i] + a[i];
    for (int i = n - 1; i >= 0; i--) suf[i] = suf[i + 1] + a[i];
    for (int i = 0; i < n; i++)
        if (pre[i] == suf[i + 1]) return i;
    return -1;
}

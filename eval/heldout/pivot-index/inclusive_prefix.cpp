#include <vector>

int pivot_index(const std::vector<int>& a) {
    int n = a.size();
    std::vector<long long> pre(n);
    long long run = 0;
    for (int i = 0; i < n; i++) { run += a[i]; pre[i] = run; }
    long long total = run;
    for (int i = 0; i < n; i++)
        if (pre[i] == total - pre[i]) return i;
    return -1;
}

#include <numeric>
#include <vector>

int pivot_index(const std::vector<int>& a) {
    long long left = std::accumulate(a.begin(), a.end(), 0LL);
    long long right = 0;
    for (int i = (int)a.size() - 1; i >= 0; i--) {
        left -= a[i];
        if (left == right) return i;
        right += a[i];
    }
    return -1;
}

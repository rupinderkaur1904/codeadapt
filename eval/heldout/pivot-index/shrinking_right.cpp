#include <numeric>
#include <vector>

int pivot_index(const std::vector<int>& a) {
    long long right = std::accumulate(a.begin(), a.end(), 0LL);
    long long left = 0;
    for (size_t i = 0; i < a.size(); i++) {
        right -= a[i];
        if (left == right) return i;
        left += a[i];
    }
    return -1;
}

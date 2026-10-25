#include <numeric>
#include <vector>

int pivot_index(const std::vector<int>& a) {
    long long total = std::accumulate(a.begin(), a.end(), 0LL);
    long long left = 0;
    for (size_t i = 0; i < a.size(); i++) {
        if (left == (total - a[i]) / 2) return i;
        left += a[i];
    }
    return -1;
}

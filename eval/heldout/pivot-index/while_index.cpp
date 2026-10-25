#include <numeric>
#include <vector>

int pivot_index(const std::vector<int>& a) {
    long long total = std::accumulate(a.begin(), a.end(), 0LL);
    long long left = 0;
    size_t i = 0;
    while (i < a.size() && 2 * left + a[i] != total) {
        left += a[i];
        i++;
    }
    return i;
}

#include <algorithm>
#include <vector>

// Alternative cause for strict_limit: uses s - 1 as the limit (an off-by-one constant).
int longest_at_most(const std::vector<int>& a, int s) {
    long long sum = 0;
    int left = 0, best = 0;
    for (int right = 0; right < static_cast<int>(a.size()); ++right) {
        sum += a[right];
        while (sum > s - 1) sum -= a[left++];
        best = std::max(best, right - left + 1);
    }
    return best;
}
